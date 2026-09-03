"""7.4 Overlap score (per ticker, across members), per trade.

Count of distinct tracked members who bought the same ticker within a
rolling window [CONFIG: default 60 days] of a given trade -- the "is this a
cluster, not a coincidence" signal. Computed per buy trade (a symmetric
window around that trade's date, so it catches members who moved slightly
before or after). Sells/exchanges aren't about buying clusters, so they're
left out, same as conviction.

Bipartisan overlap flag is computed separately -- it's a distinct,
less-partisan-driven signal worth surfacing on its own, not folded into
the overlap count.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

from app.db.models import Trade
from config.settings import settings


def compute_overlap(
    trades: list[Trade], member_party: dict[str, str], *, window_days: int | None = None
) -> tuple[dict[int, int], dict[int, bool]]:
    """Returns (trade_id -> overlap count, trade_id -> bipartisan flag) for
    every buy trade with a resolved ticker. Caller normalizes the count.
    """
    window_days = window_days or settings.overlap_window_days
    window = dt.timedelta(days=window_days)

    buys_by_ticker: dict[str, list[Trade]] = defaultdict(list)
    for t in trades:
        if t.transaction_type == "buy" and t.ticker:
            buys_by_ticker[t.ticker].append(t)

    overlap_counts: dict[int, int] = {}
    bipartisan: dict[int, bool] = {}
    for ticker, ticker_trades in buys_by_ticker.items():
        for t in ticker_trades:
            window_members = {
                other.member_id
                for other in ticker_trades
                if abs((other.transaction_date - t.transaction_date).days) <= window_days
            }
            overlap_counts[t.trade_id] = len(window_members)
            parties = {member_party.get(mid) for mid in window_members} - {None}
            bipartisan[t.trade_id] = "D" in parties and "R" in parties

    return overlap_counts, bipartisan
