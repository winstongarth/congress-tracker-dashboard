"""Trade-level score lookup used by the REST /trades route: assembles a
trade's performance/overlap/conviction/composite values."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Score


def fetch_scores_by_trade(db: Session, trade_ids: list[int]) -> dict[int, dict[str, float]]:
    """trade_id -> {score_type: value} for every Score row attached to one of
    the given trade_ids. Missing trade_ids simply have no entry."""
    if not trade_ids:
        return {}

    rows = db.execute(
        select(Score.trade_id, Score.score_type, Score.value).where(Score.trade_id.in_(trade_ids))
    ).all()

    scores_by_trade: dict[int, dict[str, float]] = {}
    for trade_id, score_type, value in rows:
        scores_by_trade.setdefault(trade_id, {})[score_type] = value
    return scores_by_trade
