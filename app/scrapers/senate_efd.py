"""Step 3 (Senate half): Senate eFD Periodic Transaction Report scraping.

efdsearch.senate.gov requires accepting a click-wrap agreement before search
becomes available (CLAUDE.md Sec 2), and its bot protection (Akamai) blocks
every plain HTTP client -- confirmed directly: httpx, PowerShell
Invoke-WebRequest, and even headless Chromium (both legacy headless and the
newer `--headless=new` mode) all get a 403. Only a real, non-headless browser
window gets through. That means this scraper:
  - requires Playwright with headless=False -- a visible browser window will
    appear while it runs.
  - requires a machine with an active desktop session. It will NOT work on a
    headless server/CI box or over a typical SSH-only session without a
    virtual display (e.g. Xvfb).
This is a hard constraint from the site's bot protection, not a design
choice -- there is no known headless path through it.

Given that, this module drives the real search form via Playwright (fill
the last-name field, check the "Periodic Transactions" checkbox, click
search) rather than hand-building the DataTables AJAX payload -- whatever
hidden fields the JS adds get filled in correctly because it's the same code
path a real user's click takes.

efdsearch.senate.gov's terms restrict commercial redistribution of this
data. CLAUDE.md positions this project as personal/educational; read the
site's terms yourself before relying on this for anything else.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

BASE_URL = "https://efdsearch.senate.gov"
HOME_URL = f"{BASE_URL}/search/home/"
SEARCH_URL = f"{BASE_URL}/search/"
PTR_REPORT_TYPE_VALUE = "11"  # confirmed live: checkbox labeled "Periodic Transactions"


@dataclass
class SenateFiling:
    first_name: str
    last_name: str
    filing_date: dt.date
    detail_url: str


class SenateEfdSession:
    """Owns one Playwright browser across a whole scrape run (accepting the
    agreement once, then reusing the same page for every tracked senator's
    search) rather than relaunching per search.
    """

    def __init__(self) -> None:
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()

    def __enter__(self) -> "SenateEfdSession":
        self.page.goto(HOME_URL)
        self.page.click("#agree_statement")
        self.page.wait_for_load_state("networkidle", timeout=15000)
        if "/search/" not in self.page.url:
            raise RuntimeError(
                f"Agreement acceptance didn't land on /search/ (got {self.page.url}) "
                "-- the site's form may have changed."
            )
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self.browser.close()
        self._playwright.stop()

    def search_ptrs(self, last_name: str, *, since: dt.date | None = None) -> list[SenateFiling]:
        # fetch_filing_detail_html() navigates away to a filing's detail page,
        # so getting back here for the next senator/filing needs a fresh nav.
        if not self.page.url.rstrip("/").endswith("/search"):
            self.page.goto(SEARCH_URL)

        # After a search, the site hides the form behind a results view; a
        # "Modify Search" control (#re-search) brings it back. Only present
        # from the second search onward in a given session.
        re_search = self.page.locator("#re-search")
        if re_search.count() and re_search.is_visible():
            re_search.click()

        self.page.fill("#lastName", last_name)
        checkbox = self.page.locator(f'#reportTypes[value="{PTR_REPORT_TYPE_VALUE}"]')
        if not checkbox.is_checked():
            checkbox.check()

        with self.page.expect_response(lambda r: "/search/report/data/" in r.url) as resp_info:
            self.page.click('button[type="submit"]')
        payload = resp_info.value.json()

        filings = [self._parse_row(row) for row in payload.get("data", [])]
        if since:
            filings = [f for f in filings if f.filing_date >= since]
        return filings

    def _parse_row(self, row: list[str]) -> SenateFiling:
        # [first_name, last_name, filer_label, report_type_html, date_str]
        first_name, last_name, _filer_label, report_type_html, date_str = row[:5]
        link_match = re.search(r'href="([^"]+)"', report_type_html)
        if not link_match:
            raise ValueError(f"No detail link found in report_type cell: {report_type_html!r}")
        href = link_match.group(1)
        detail_url = href if href.startswith("http") else BASE_URL + href
        filing_date = dt.datetime.strptime(date_str.strip(), "%m/%d/%Y").date()
        return SenateFiling(first_name=first_name, last_name=last_name, filing_date=filing_date, detail_url=detail_url)

    def fetch_filing_detail_html(self, filing: SenateFiling) -> str:
        self.page.goto(filing.detail_url)
        return self.page.content()


# Confirmed live against a real PTR detail page. "type" alone would also
# match the "Asset Type" header, so transaction_type requires an exact
# header match rather than a substring -- the real column is just "Type".
COLUMN_EXACT = {
    "transaction_date": ["transaction date"],
    "owner": ["owner"],
    "ticker": ["ticker"],
    "asset_name": ["asset name"],
    "asset_type": ["asset type"],
    "transaction_type": ["type"],
    "amount": ["amount"],
}

OWNER_MAP = {"self": "self", "spouse": "spouse", "dependent child": "dependent_child", "joint": "joint"}

AMOUNT_RANGE_RE = re.compile(r"\$([\d,]+(?:\.\d+)?)\s*-\s*\$([\d,]+(?:\.\d+)?)")
AMOUNT_SINGLE_RE = re.compile(r"\$([\d,]+(?:\.\d+)?)")


def _asset_type_from_label(label: str) -> str:
    label_lower = label.lower()
    if "option" in label_lower:
        return "option"
    if "bond" in label_lower or "note" in label_lower:
        return "bond"
    if "fund" in label_lower:
        return "fund"
    if "crypto" in label_lower:
        return "crypto"
    if "stock" in label_lower:
        return "stock"
    return "other"


def _transaction_type_from_label(label: str) -> str:
    label_lower = label.lower()
    if label_lower.startswith("purchase"):
        return "buy"
    if label_lower.startswith("sale"):
        return "sell"
    return "exchange"


def parse_ptr_detail_html(html: str) -> list[dict]:
    """Parses an e-filed Senate PTR's HTML transaction table into raw dicts.
    Returns [] for paper/scanned filings (no table present) -- caller should
    log those for manual review, not treat them as "no transactions"
    (CLAUDE.md Sec 9: scanned filings need OCR, not silent skipping).
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        return []

    header_cells = [th.get_text(strip=True).lower() for th in table.find_all("th")]
    col_index_for_field: dict[str, int] = {}
    for field, exact_labels in COLUMN_EXACT.items():
        for idx, header in enumerate(header_cells):
            if header in exact_labels:
                col_index_for_field[field] = idx
                break

    missing = set(COLUMN_EXACT) - set(col_index_for_field)
    if missing:
        raise RuntimeError(
            f"Senate PTR table is missing expected columns {missing} given headers "
            f"{header_cells!r} -- the page layout has likely changed."
        )

    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < len(COLUMN_EXACT):
            continue
        raw = {field: cells[idx].get_text(strip=True) for field, idx in col_index_for_field.items()}

        amount_text = raw["amount"]
        range_match = AMOUNT_RANGE_RE.search(amount_text)
        if range_match:
            amount_min = float(range_match.group(1).replace(",", ""))
            amount_max = float(range_match.group(2).replace(",", ""))
        else:
            single_match = AMOUNT_SINGLE_RE.search(amount_text)
            amount_min = amount_max = float(single_match.group(1).replace(",", "")) if single_match else 0.0

        rows.append(
            {
                "transaction_date": dt.datetime.strptime(raw["transaction_date"], "%m/%d/%Y").date(),
                "owner": OWNER_MAP.get(raw["owner"].lower(), "self"),
                "ticker": raw["ticker"] or None,
                "asset_name_raw": raw["asset_name"],
                "asset_type": _asset_type_from_label(raw["asset_type"]),
                "transaction_type": _transaction_type_from_label(raw["transaction_type"]),
                "amount_min": amount_min,
                "amount_max": amount_max,
            }
        )
    return rows


def build_trade_rows(member_id: str, filing: SenateFiling, parsed_items: list[dict]) -> list[dict]:
    """Maps parsed Senate PTR line items onto trades-table-shaped dicts (CLAUDE.md Sec 4)."""
    rows = []
    for item in parsed_items:
        amount_min, amount_max = item["amount_min"], item["amount_max"]
        rows.append(
            {
                "member_id": member_id,
                "filing_id": filing.detail_url.rstrip("/").rsplit("/", 1)[-1],
                "asset_name_raw": item["asset_name_raw"],
                "ticker": None,  # resolved later by app/normalization
                "ticker_match_confidence": None,
                "asset_type": item["asset_type"],
                "owner": item["owner"],
                "transaction_type": item["transaction_type"],
                "transaction_date": item["transaction_date"],
                "disclosure_date": filing.filing_date,
                "filing_lag_days": (filing.filing_date - item["transaction_date"]).days,
                "amount_min": amount_min,
                "amount_max": amount_max,
                "amount_mid": (amount_min + amount_max) / 2,
                "source_url": filing.detail_url,
                "_raw_ticker_guess": item["ticker"],
            }
        )
    return rows
