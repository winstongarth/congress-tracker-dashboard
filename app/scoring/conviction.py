"""7.2 Conviction score (per member+ticker).

How repeatedly a member buys into the same name: count of buy transactions
in that ticker over the trailing 12 months. A single $50k buy and ten $5k
buys over a year are different signals -- conviction captures the latter.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter

from app.db.models import Trade


def compute_conviction(trades: list[Trade], *, as_of: dt.date | None = None) -> dict[tuple[str, str], int]:
    """(member_id, ticker) -> raw buy count in the trailing 12 months.
    Caller normalizes (percentile rank within the population).
    """
    as_of = as_of or dt.date.today()
    window_start = as_of - dt.timedelta(days=365)

    counts: Counter[tuple[str, str]] = Counter()
    for t in trades:
        if t.transaction_type != "buy" or not t.ticker:
            continue
        if not (window_start <= t.transaction_date <= as_of):
            continue
        counts[(t.member_id, t.ticker)] += 1
    return dict(counts)
