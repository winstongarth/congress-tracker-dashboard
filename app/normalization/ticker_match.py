"""asset_name_raw -> ticker normalization.

Reference data: NASDAQ Trader's symbol directory (nasdaqlisted.txt +
otherlisted.txt) -- a free, no-key bulk file covering every
NASDAQ/NYSE/NYSE American/ARCA listed ticker + company name. Matching order:
  1. exact ticker match, if the scraper already pulled a ticker guess out of
     the filing itself (e.g. House PTRs annotate "(TICKER)" inline)
  2. fuzzy company-name match against the reference table otherwise
  3. below ticker_match_confidence_threshold [CONFIG]: ticker stored as None,
     confidence stored as whatever was found -- query `trades` where
     ticker IS NULL for the manual-review queue, rather than maintaining a
     separate review table.
"""

from __future__ import annotations

import csv
import io

from rapidfuzz import fuzz, process

from app.cache.http_cache import CachedFetcher
from config.settings import settings

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


def _load_pipe_delimited(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text), delimiter="|")
    return [row for row in reader if row.get("Symbol") or row.get("ACT Symbol")]


def load_reference_table() -> dict[str, str]:
    """ticker -> company name, refreshed from NASDAQ Trader's symbol directory."""
    with CachedFetcher("ticker_reference", check_robots=False) as fetcher:
        nasdaq_raw = fetcher.get(NASDAQ_LISTED_URL, cache_key="nasdaqlisted")
        other_raw = fetcher.get(OTHER_LISTED_URL, cache_key="otherlisted")

    table: dict[str, str] = {}
    for row in _load_pipe_delimited(nasdaq_raw):
        if row.get("Test Issue") == "Y" or row.get("Symbol", "").startswith("File Creation"):
            continue
        table[row["Symbol"].strip()] = row["Security Name"].strip()
    for row in _load_pipe_delimited(other_raw):
        if row.get("Test Issue") == "Y":
            continue
        symbol = (row.get("ACT Symbol") or row.get("Symbol") or "").strip()
        if symbol and not symbol.startswith("File Creation"):
            table[symbol] = row["Security Name"].strip()
    return table


def match_ticker(
    asset_name_raw: str, ticker_guess: str | None, reference: dict[str, str]
) -> tuple[str | None, float]:
    """Returns (ticker, confidence) in [0, 1]. ticker is None if confidence
    falls below settings.ticker_match_confidence_threshold."""
    if ticker_guess and ticker_guess in reference:
        return ticker_guess, 1.0

    best = process.extractOne(asset_name_raw, reference, scorer=fuzz.token_sort_ratio)
    if best is None:
        return None, 0.0
    _matched_name, score, ticker = best
    confidence = score / 100.0
    if confidence < settings.ticker_match_confidence_threshold:
        return None, confidence
    return ticker, confidence


def normalize_trade_row(row: dict, reference: dict[str, str]) -> dict:
    """Mutates and returns a trades-table-shaped row dict: resolves
    ticker/ticker_match_confidence and drops the scraper's private ticker
    guess field. No-op (ticker stays None) for non-stock asset types --
    v1 is stocks-only; fuzzy-matching a bond/option/fund description against
    an equity ticker list would just produce noise.
    """
    ticker_guess = row.pop("_raw_ticker_guess", None)
    if row.get("asset_type") != "stock":
        row["ticker"] = None
        row["ticker_match_confidence"] = None
        return row
    ticker, confidence = match_ticker(row["asset_name_raw"], ticker_guess, reference)
    row["ticker"] = ticker
    row["ticker_match_confidence"] = confidence
    return row


def fetch_ticker_metadata(ticker: str) -> dict | None:
    """Sector/industry via yfinance (a documented single-point-of-failure,
    kept behind this one function so it's easy to swap providers later).
    Returns None on any failure rather than raising -- missing metadata
    shouldn't block trade ingestion.
    """
    try:
        import yfinance as yf

        # NASDAQ's symbol directory uses dots for share classes (BRK.B);
        # Yahoo Finance expects dashes (BRK-B). Keep the dot form as the
        # canonical stored ticker, translate only for the yfinance call.
        info = yf.Ticker(ticker.replace(".", "-")).info
        if not info or not info.get("longName") and not info.get("shortName"):
            return None
        return {
            "company_name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
    except Exception as exc:
        print(f"WARNING: ticker metadata fetch failed for {ticker}: {exc}")
        return None
