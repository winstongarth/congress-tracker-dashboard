"""7.3 Recency weighting (per trade).

Exponential decay based on days since transaction_date, half-life
[CONFIG: default 90 days]. Already bounded in (0, 100] by construction --
unlike performance/overlap/conviction (raw percentages and counts in very
different units), this doesn't need percentile-rank normalization to be
comparable; today's trades score 100, a trade one half-life old scores 50.
"""

from __future__ import annotations

import datetime as dt

from app.db.models import Trade
from config.settings import settings


def compute_recency_weight(trades: list[Trade], *, as_of: dt.date | None = None, half_life_days: int | None = None) -> dict[int, float]:
    as_of = as_of or dt.date.today()
    half_life_days = half_life_days or settings.recency_half_life_days

    weights: dict[int, float] = {}
    for t in trades:
        days_since = (as_of - t.transaction_date).days
        weights[t.trade_id] = 100.0 * (0.5 ** (days_since / half_life_days))
    return weights
