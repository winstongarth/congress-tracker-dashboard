"""Price backfill: for every ticker with at least one trade, backfill
price_history from the earliest trade date to today. Re-running only
fetches the gap since the last stored date, not the whole history again --
"never re-fetch something you already have" applies to price data the same
as to filing pages.

yfinance is the documented single-point-of-failure here -- kept behind this
one function so the data source can be swapped later.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import PriceHistory, Trade


def tickers_needing_backfill(session: Session) -> dict[str, dt.date]:
    """ticker -> earliest transaction_date across all trades in that ticker."""
    rows = session.execute(
        select(Trade.ticker, func.min(Trade.transaction_date))
        .where(Trade.ticker.is_not(None))
        .group_by(Trade.ticker)
    ).all()
    return {ticker: earliest for ticker, earliest in rows}


def _existing_max_date(session: Session, ticker: str) -> dt.date | None:
    return session.scalar(select(func.max(PriceHistory.date)).where(PriceHistory.ticker == ticker))


def _yfinance_symbol(ticker: str) -> str:
    """NASDAQ's symbol directory uses dots for share classes (BRK.B), but
    Yahoo Finance expects dashes (BRK-B). The dot form is kept as the
    canonical stored ticker (it's what trades.ticker and ticker_metadata
    already use), this translation is only for the yfinance call itself.
    """
    return ticker.replace(".", "-")


def backfill_ticker(session: Session, ticker: str, earliest_needed: dt.date) -> int:
    """Returns number of price rows inserted."""
    import yfinance as yf

    existing_max = _existing_max_date(session, ticker)
    start = (existing_max + dt.timedelta(days=1)) if existing_max else earliest_needed
    today = dt.date.today()
    if start > today:
        return 0  # already fully backfilled, including today

    history = yf.Ticker(_yfinance_symbol(ticker)).history(
        start=start.isoformat(), end=(today + dt.timedelta(days=1)).isoformat()
    )
    if history.empty:
        return 0

    # Defensive: Yahoo's history endpoint has been observed returning a row
    # at or before the requested start date despite the explicit range --
    # without this filter, that collides with the unique (ticker, date) row
    # already on file and aborts the whole transaction.
    rows = [
        PriceHistory(ticker=ticker, date=ts.date(), close_price=float(close))
        for ts, close in history["Close"].items()
        if ts.date() >= start
    ]
    session.add_all(rows)
    return len(rows)


def backfill_all(session: Session) -> dict[str, int]:
    """Backfills every ticker that has at least one trade. Returns ticker -> rows inserted.

    Each ticker runs in its own savepoint: Postgres aborts an entire
    transaction on any single failed statement, so without this, one bad
    ticker would silently zero out every other ticker's backfill too.
    """
    results: dict[str, int] = {}
    for ticker, earliest in tickers_needing_backfill(session).items():
        try:
            with session.begin_nested():
                results[ticker] = backfill_ticker(session, ticker, earliest)
        except Exception as exc:
            print(f"WARNING: price backfill failed for {ticker}: {exc}")
            results[ticker] = 0
    return results
