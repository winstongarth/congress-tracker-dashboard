"""Member-level metric lookups shared by the REST /members route and the
GraphQL Politician type, so the performance rollup and sector breakdown are
computed identically (and only once) in both API layers."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Score, TickerMetadata, Trade


def fetch_performance_rollup(db: Session, member_id: str) -> float | None:
    """The member-level performance rollup Score row (trade_id IS NULL),
    written by app/scoring/run.py -- distinct from the per-trade rows."""
    return db.scalar(
        select(Score.value).where(
            Score.member_id == member_id, Score.score_type == "performance", Score.trade_id.is_(None)
        )
    )


def fetch_sector_breakdown(db: Session, member_id: str) -> dict[str, float]:
    """sector -> total amount_mid across every trade for this member."""
    trades = list(db.scalars(select(Trade).where(Trade.member_id == member_id)))
    tickers = {t.ticker for t in trades if t.ticker}
    metadata_by_ticker = (
        {tm.ticker: tm for tm in db.scalars(select(TickerMetadata).where(TickerMetadata.ticker.in_(tickers)))}
        if tickers
        else {}
    )

    sector_totals: dict[str, float] = defaultdict(float)
    for t in trades:
        meta = metadata_by_ticker.get(t.ticker)
        sector = meta.sector if meta and meta.sector else "Unknown"
        sector_totals[sector] += float(t.amount_mid)
    return dict(sector_totals)
