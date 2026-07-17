"""CLAUDE.md Sec 10 entry points: Phase 1 ingestion + Phase 2 scoring.

Usage:
    python -m app.cli init-db
    python -m app.cli roster
    python -m app.cli trades [--year 2026] [--include-senate]
    python -m app.cli normalize
    python -m app.cli score
    python -m app.cli all [--include-senate]
"""

from __future__ import annotations

import argparse
import datetime as dt

from sqlalchemy import select

from app.db.models import Member, TickerMetadata, Trade
from app.db.session import get_session, init_db
from app.normalization.ticker_match import (
    fetch_ticker_metadata,
    load_reference_table,
    match_ticker,
    normalize_trade_row,
)
from app.scoring.run import run_scoring
from app.scrapers import house_ptr
from app.scrapers.roster import fetch_roster, upsert_roster
from app.selection.top30 import select_top30


def cmd_init_db(_args: argparse.Namespace) -> None:
    init_db()
    print("Tables created.")


def cmd_roster(_args: argparse.Namespace) -> None:
    roster = fetch_roster()
    with get_session() as session:
        upsert_roster(session, roster)
    print(f"Upserted {len(roster)} members.")


def _upsert_trades(session, rows: list[dict]) -> int:
    """Deletes any existing rows for each filing_id before inserting fresh
    ones -- makes re-running the scraper idempotent and lets a re-filed
    (amended) version of the same filing_id naturally replace the old rows.
    Cross-filing amendments (a new DocID amending an old one) aren't linked
    automatically -- the House index doesn't say which DocID an amendment
    supersedes, so both stay on file (CLAUDE.md Sec 9 flags this as a known
    gotcha, not something Phase 1 needs to fully resolve).
    """
    filing_ids = {row["filing_id"] for row in rows}
    if filing_ids:
        existing = session.scalars(select(Trade).where(Trade.filing_id.in_(filing_ids)))
        for trade in existing:
            session.delete(trade)
        session.flush()
    for row in rows:
        session.add(Trade(**row))
    return len(rows)


def cmd_trades(args: argparse.Namespace) -> None:
    year = args.year or dt.date.today().year
    reference = load_reference_table()

    with get_session() as session:
        tracked_ids = select_top30(session)
        members = {m.member_id: m for m in session.scalars(select(Member).where(Member.member_id.in_(tracked_ids)))}

        house_tracked = {mid: (m.full_name, m.state) for mid, m in members.items() if m.chamber == "house"}
        total_rows = 0
        if house_tracked:
            index = house_ptr.fetch_filing_index(year)
            matches = house_ptr.match_tracked_members(index, house_tracked)
            for member_id, entries in matches.items():
                for entry in entries:
                    raw_pdf = house_ptr.fetch_ptr_pdf(entry)
                    text = house_ptr.extract_pdf_text(raw_pdf)
                    try:
                        items = house_ptr.parse_ptr_text(text)
                    except Exception as exc:
                        print(f"WARNING: failed to parse House filing {entry.doc_id} for {member_id}: {exc}")
                        continue
                    rows = house_ptr.build_trade_rows(member_id, entry, items)
                    rows = [normalize_trade_row(row, reference) for row in rows]
                    total_rows += _upsert_trades(session, rows)
        print(f"Upserted {total_rows} House trade rows for {len(house_tracked)} tracked House members.")

        if args.include_senate:
            print(
                "NOTE: Senate eFD scraping requires a visible (non-headless) browser "
                "window -- efdsearch.senate.gov's bot protection blocks every headless "
                "client, including headless Chromium. A Chrome window will open now."
            )
            from app.scrapers import senate_efd

            senate_tracked = {mid: m for mid, m in members.items() if m.chamber == "senate"}
            senate_rows = 0
            with senate_efd.SenateEfdSession() as efd:
                for member_id, member in senate_tracked.items():
                    last_name = member.full_name.split()[-1]
                    filings = efd.search_ptrs(last_name, since=dt.date(year, 1, 1))
                    for filing in filings:
                        html = efd.fetch_filing_detail_html(filing)
                        try:
                            items = senate_efd.parse_ptr_detail_html(html)
                        except Exception as exc:
                            print(f"WARNING: failed to parse Senate filing {filing.detail_url} for {member_id}: {exc}")
                            continue
                        if not items:
                            print(f"NOTE: Senate filing {filing.detail_url} has no parseable table (paper/scanned filing?) -- skipped, needs manual review")
                            continue
                        rows = senate_efd.build_trade_rows(member_id, filing, items)
                        rows = [normalize_trade_row(row, reference) for row in rows]
                        senate_rows += _upsert_trades(session, rows)
            print(f"Upserted {senate_rows} Senate trade rows for {len(senate_tracked)} tracked senators.")


def cmd_normalize(_args: argparse.Namespace) -> None:
    """Re-runs ticker matching for any trade still missing a confidence score
    (e.g. Senate rows, or after a ticker_match_confidence_threshold change),
    then backfills ticker_metadata for every resolved ticker that doesn't have
    it yet -- not just ones touched in this run, since metadata fetches can
    fail independently of ticker matching (e.g. yfinance wasn't installed the
    first time trades were scraped).
    """
    reference = load_reference_table()
    count = 0

    with get_session() as session:
        trades = session.scalars(select(Trade).where(Trade.ticker_match_confidence.is_(None)))
        for trade in trades:
            ticker, confidence = match_ticker(trade.asset_name_raw, trade.ticker, reference)
            trade.ticker, trade.ticker_match_confidence = ticker, confidence
            count += 1

        resolved_tickers = set(session.scalars(select(Trade.ticker).where(Trade.ticker.is_not(None))))
        existing_metadata = set(session.scalars(select(TickerMetadata.ticker)))
        new_tickers = resolved_tickers - existing_metadata
        for ticker in new_tickers:
            meta = fetch_ticker_metadata(ticker)
            if meta:
                session.add(TickerMetadata(ticker=ticker, **meta))

    print(f"Re-normalized {count} trades; fetched metadata for {len(new_tickers)} new tickers.")


def cmd_score(_args: argparse.Namespace) -> None:
    """Phase 2 (CLAUDE.md Sec 7): price backfill + every sub-score + composite."""
    with get_session() as session:
        summary = run_scoring(session)
    print(
        f"Scored {summary['trades_scored']} trades across {summary['members_with_rollup']} members; "
        f"{summary['committee_relevant_flagged']} flagged committee-relevant; "
        f"{summary['bipartisan_overlap_trades']} trades have bipartisan overlap; "
        f"computed portfolio returns for {summary['members_with_portfolio_returns']} members."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db").set_defaults(func=cmd_init_db)
    sub.add_parser("roster").set_defaults(func=cmd_roster)

    trades_parser = sub.add_parser("trades")
    trades_parser.add_argument("--year", type=int, default=None)
    trades_parser.add_argument("--include-senate", action="store_true")
    trades_parser.set_defaults(func=cmd_trades)

    sub.add_parser("normalize").set_defaults(func=cmd_normalize)
    sub.add_parser("score").set_defaults(func=cmd_score)

    all_parser = sub.add_parser("all")
    all_parser.add_argument("--include-senate", action="store_true")
    all_parser.add_argument("--year", type=int, default=None)

    def cmd_all(args: argparse.Namespace) -> None:
        cmd_roster(args)
        cmd_trades(args)
        cmd_normalize(args)
        cmd_score(args)

    all_parser.set_defaults(func=cmd_all)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
