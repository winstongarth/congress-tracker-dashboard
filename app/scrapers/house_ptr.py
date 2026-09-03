"""House half of the ingestion pipeline: Periodic Transaction Report (PTR) scraping.

Source of truth: disclosures-clerk.house.gov publishes a bulk per-year ZIP
(financial-pdfs/<year>FD.zip) containing an XML index of every filing (Last,
First, FilingType, StateDst, Year, FilingDate, DocID). FilingType "P" = PTR.
This is preferred over driving the site's search form per-member: it's the
same official data, fetched in one request instead of N, which is friendlier
to the site as a well-behaved client.

PTR PDFs live at:
  https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf

PDF layout note: these are the post-~2023 "eFiled" templated PTRs. The
embedded font has no usable glyphs for some lowercase letters in the "Filing
Status:" / "Description:" labels (pdfplumber extracts them as literal NUL
bytes) -- the parser below works around this and does not depend on exact
label text. Pre-2023 / scanned PTRs use a different (often image-based)
layout and are NOT handled by this parser yet; such filings should fail
loudly (logged, skipped) rather than silently produce wrong rows.
"""

from __future__ import annotations

import datetime as dt
import io
import re
import zipfile
from dataclasses import dataclass

from app.cache.http_cache import CachedFetcher

INDEX_ZIP_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
PTR_PDF_URL = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf"

# fd.house.gov/reference/asset-type-codes.aspx, mapped down to the
# trades.asset_type enum (stock|option|bond|fund|crypto|other).
ASSET_TYPE_CODE_MAP = {
    "ST": "stock",
    "OP": "option",
    "CS": "bond", "GS": "bond", "AB": "bond", "ET": "bond",
    "MF": "fund", "EF": "fund",
    "CT": "crypto",
}

OWNER_CODE_MAP = {None: "self", "SP": "spouse", "DC": "dependent_child", "JT": "joint"}

TXN_TYPE_MAP = {"P": "buy", "S": "sell", "E": "exchange"}

HEADER_NOISE_RE = re.compile(
    r"ID Owner Asset Transaction Date Notification Amount Cap\.\s*"
    r"Type Date Gains >\s*\$200\?\s*"
)
FOOTER_RE = re.compile(r"\*\s*For the complete list")
STATUS_RE = re.compile(r"F\W*S\W*:\s*(New|Amended)\s*")
TAIL_RE = re.compile(
    r"(?P<txn_type>S \(partial\)|[PSE])\s+"
    r"(?P<txn_date>\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(?P<notif_date>\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"\$(?P<amt_low>[\d,]+(?:\.\d+)?)\s*"
)
TICKER_RE = re.compile(r"\(([A-Z][A-Z.]{0,5})\)")
TYPE_CODE_RE = re.compile(r"\[([A-Z0-9]{2,3})\]")
DOLLAR_RE = re.compile(r"\$(?P<amt>[\d,]+(?:\.\d+)?)")


@dataclass
class FilingIndexEntry:
    last: str
    first: str
    filing_type: str
    state_dst: str
    year: int
    filing_date: dt.date
    doc_id: str


def fetch_filing_index(year: int) -> list[FilingIndexEntry]:
    with CachedFetcher("house_ptr_index", check_robots=False) as fetcher:
        raw_zip = fetcher.get(INDEX_ZIP_URL.format(year=year), cache_key=f"house_fd_index_{year}")

    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        xml_bytes = zf.read(f"{year}FD.xml")

    from xml.etree import ElementTree as ET

    root = ET.fromstring(xml_bytes)
    entries = []
    for member_el in root.findall("./Member"):
        try:
            filing_date = dt.datetime.strptime(
                member_el.findtext("FilingDate", default=""), "%m/%d/%Y"
            ).date()
        except ValueError:
            continue
        entries.append(
            FilingIndexEntry(
                last=member_el.findtext("Last", default="").strip(),
                first=member_el.findtext("First", default="").strip(),
                filing_type=member_el.findtext("FilingType", default="").strip(),
                state_dst=member_el.findtext("StateDst", default="").strip(),
                year=year,
                filing_date=filing_date,
                doc_id=member_el.findtext("DocID", default="").strip(),
            )
        )
    return entries


def match_tracked_members(
    entries: list[FilingIndexEntry], tracked: dict[str, tuple[str, str]]
) -> dict[str, list[FilingIndexEntry]]:
    """tracked: member_id -> (full_name, state_abbr). Returns member_id -> PTR entries.

    Matched by last-name token + state, since the index has no bioguide_id.
    Pre-indexed by state so this stays fast with hundreds of tracked members
    (all of them, by default) against thousands of filing-index entries --
    each entry only needs to check candidates from its own state, not every
    tracked member.
    """
    candidates_by_state: dict[str, list[tuple[str, set[str]]]] = {}
    for member_id, (full_name, state) in tracked.items():
        candidates_by_state.setdefault(state, []).append((member_id, {w.lower() for w in full_name.split()}))

    by_member: dict[str, list[FilingIndexEntry]] = {mid: [] for mid in tracked}
    for entry in entries:
        if entry.filing_type != "P" or not entry.doc_id:
            continue
        last_lower = entry.last.lower()
        for member_id, name_words in candidates_by_state.get(entry.state_dst[:2], []):
            if last_lower in name_words:
                by_member[member_id].append(entry)
                break
    return by_member


def fetch_ptr_pdf(entry: FilingIndexEntry) -> bytes:
    with CachedFetcher("house_ptr_pdfs", check_robots=False) as fetcher:
        return fetcher.get(
            PTR_PDF_URL.format(year=entry.year, doc_id=entry.doc_id),
            cache_key=f"house_ptr_{entry.year}_{entry.doc_id}",
        )


def extract_pdf_text(raw_pdf: bytes) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(raw_pdf)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _parse_amount(s: str) -> float:
    return float(s.replace(",", ""))


def parse_ptr_text(text: str) -> list[dict]:
    """Parses the transaction table out of a PTR's extracted text. See module
    docstring for the layout this targets. Returns raw dicts (not yet mapped
    to DB enum values) -- one per transaction line item.
    """
    text = HEADER_NOISE_RE.sub("\n", text)
    end = FOOTER_RE.search(text)
    body = text[: end.start()] if end else text

    status_matches = list(STATUS_RE.finditer(body))

    # Pass 1: pull owner/name/txn/dates/amount_low/rest + filing_status per record.
    prelim = []
    prev_end = 0
    for s in status_matches:
        chunk = body[prev_end : s.start()]
        tails = list(TAIL_RE.finditer(chunk))
        if not tails:
            prev_end = s.end()
            continue
        tail = tails[-1]
        nl = chunk.rfind("\n", 0, tail.start())
        name_and_owner = chunk[nl + 1 : tail.start()].strip()
        rest = chunk[tail.end() :].strip()

        owner_m = re.match(r"^(SP|DC|JT)\s+(.*)$", name_and_owner, re.DOTALL)
        owner, name_part1 = (owner_m.group(1), owner_m.group(2)) if owner_m else (None, name_and_owner)

        prelim.append(
            {
                "owner": owner,
                "name_part1": name_part1,
                "rest": rest,
                "txn_type": tail.group("txn_type"),
                "txn_date": tail.group("txn_date"),
                "notif_date": tail.group("notif_date"),
                "amt_low": tail.group("amt_low"),
                "filing_status": s.group(1),
            }
        )
        prev_end = s.end()

    # Pass 2: descriptions are offset by one -- the text between status_k and
    # status_(k+1) starts with description_k (see module's design notes /
    # commit history for why this two-pass split was needed).
    tail_chunk_bounds = [s.end() for s in status_matches] + [len(body)]
    for i, record in enumerate(prelim):
        chunk = body[tail_chunk_bounds[i] : tail_chunk_bounds[i + 1]]
        tails = list(TAIL_RE.finditer(chunk))
        desc_end = tails[-1].start() if tails else len(chunk)
        nl = chunk.rfind("\n", 0, desc_end)
        description = (chunk[:nl] if nl != -1 else chunk[:desc_end]).strip()
        description = re.sub(r"^D\W*:\s*", "", description).strip()
        record["description"] = description

    results = []
    for r in prelim:
        combined_name = f"{r['name_part1']} {r['rest']}"
        # Ticker and asset-type code don't reliably sit next to each other --
        # sometimes "(TICKER) [CODE]" are adjacent, sometimes the ticker trails
        # the line-1 name and the code sits alone after the line wrap (e.g.
        # "Apple Inc. - Common Stock (AAPL) -\n[ST] $25,000,000"). Find each
        # independently and truncate the name at whichever starts first.
        ticker_matches = list(TICKER_RE.finditer(combined_name))
        type_matches = list(TYPE_CODE_RE.finditer(combined_name))
        ticker = ticker_matches[-1].group(1) if ticker_matches else None
        type_code = type_matches[-1].group(1) if type_matches else None

        cut_positions = [m.start() for m in (ticker_matches[-1:] + type_matches[-1:])]
        asset_name_raw = combined_name[: min(cut_positions)] if cut_positions else combined_name
        asset_name_raw = re.sub(r"\s+", " ", asset_name_raw).strip(" -")

        dollar_amounts = DOLLAR_RE.findall(r["rest"])
        amt_low = _parse_amount(r["amt_low"])
        amt_high = _parse_amount(dollar_amounts[-1]) if dollar_amounts else amt_low

        results.append(
            {
                "owner_code": r["owner"],
                "asset_name_raw": asset_name_raw,
                "ticker_guess": ticker,
                "asset_type_code": type_code,
                "txn_type_code": r["txn_type"].split()[0],  # "S (partial)" -> "S"
                "txn_date": dt.datetime.strptime(r["txn_date"], "%m/%d/%Y").date(),
                "amount_min": min(amt_low, amt_high),
                "amount_max": max(amt_low, amt_high),
                "description": r["description"],
                "filing_status": r["filing_status"],
            }
        )
    return results


def build_trade_rows(
    member_id: str, entry: FilingIndexEntry, parsed_items: list[dict]
) -> list[dict]:
    """Maps parsed PTR line items onto trades-table-shaped dicts."""
    source_url = PTR_PDF_URL.format(year=entry.year, doc_id=entry.doc_id)
    rows = []
    for item in parsed_items:
        asset_type = ASSET_TYPE_CODE_MAP.get(item["asset_type_code"], "other")
        amount_min, amount_max = item["amount_min"], item["amount_max"]
        rows.append(
            {
                "member_id": member_id,
                "filing_id": entry.doc_id,
                "asset_name_raw": item["asset_name_raw"],
                "ticker": None,  # resolved later by app/normalization
                "ticker_match_confidence": None,
                "asset_type": asset_type,
                "owner": OWNER_CODE_MAP.get(item["owner_code"], "self"),
                "transaction_type": TXN_TYPE_MAP.get(item["txn_type_code"], "exchange"),
                "transaction_date": item["txn_date"],
                "disclosure_date": entry.filing_date,
                "filing_lag_days": (entry.filing_date - item["txn_date"]).days,
                "amount_min": amount_min,
                "amount_max": amount_max,
                "amount_mid": (amount_min + amount_max) / 2,
                "source_url": source_url,
                "_raw_ticker_guess": item["ticker_guess"],  # consumed by normalization, not stored as-is
            }
        )
    return rows
