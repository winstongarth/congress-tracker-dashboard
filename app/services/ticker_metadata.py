"""Shared ticker -> TickerMetadata lookup, used by the REST /trades route and
the GraphQL ticker DataLoader (trade -> ticker)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TickerMetadata


def fetch_ticker_metadata(db: Session, tickers: set[str]) -> dict[str, TickerMetadata]:
    """ticker -> TickerMetadata for every ticker in `tickers` that has a row."""
    if not tickers:
        return {}
    return {tm.ticker: tm for tm in db.scalars(select(TickerMetadata).where(TickerMetadata.ticker.in_(tickers)))}
