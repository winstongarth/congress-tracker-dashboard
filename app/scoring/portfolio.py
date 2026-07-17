"""Member-level realized/unrealized portfolio return.

Not part of CLAUDE.md's original §7 scoring spec -- added later as its own
feature. Distinct from the §7.1 Performance score: that's a 0-100
percentile rank for ranking trades against each other; this is an actual
dollar P&L estimate for a member's whole portfolio.

Methodology: STOCK Act disclosures only give amount RANGES, never share
counts, so exact P&L isn't recoverable. Implied shares = amount_mid / entry
price approximates a position size from the disclosed range -- the same
approximation CLAUDE.md already endorses for "all volume calculations" via
amount_mid. These are estimates, not exact figures, same as everywhere else
in this app.

Position matching reuses §7.1's FIFO buy->sell pairing (same member +
ticker + owner), so a buy counted as "closed" here is the same buy counted
as closed for the performance score -- one consistent notion of what's
still open vs. already sold.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy.orm import Session

from app.db.models import Trade
from app.scoring.performance import PriceSeries, match_exit_dates


def compute_portfolio_returns(session: Session, trades: list[Trade]) -> dict[str, dict[str, float]]:
    """member_id -> {realized_pnl, realized_cost_basis, unrealized_pnl,
    unrealized_cost_basis}, in dollars. Only stock buy/sell trades with a
    resolved ticker are scoreable -- same scope as the performance score.
    """
    scoreable = [t for t in trades if t.ticker and t.asset_type == "stock" and t.transaction_type in ("buy", "sell")]
    buys = [t for t in scoreable if t.transaction_type == "buy"]
    tickers = {t.ticker for t in scoreable}
    prices = PriceSeries(session, tickers)
    today = dt.date.today()
    exit_dates = match_exit_dates(scoreable)

    returns: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "realized_pnl": 0.0,
            "realized_cost_basis": 0.0,
            "unrealized_pnl": 0.0,
            "unrealized_cost_basis": 0.0,
        }
    )

    for t in buys:
        entry_price = prices.price_near(t.ticker, t.transaction_date)
        if entry_price is None or entry_price == 0:
            continue
        invested = float(t.amount_mid)
        implied_shares = invested / entry_price

        exit_date = exit_dates.get(t.trade_id)
        if exit_date is not None:
            exit_price = prices.price_near(t.ticker, exit_date)
            if exit_price is None:
                continue
            returns[t.member_id]["realized_pnl"] += implied_shares * (exit_price - entry_price)
            returns[t.member_id]["realized_cost_basis"] += invested
        else:
            current_price = prices.price_near(t.ticker, today)
            if current_price is None:
                continue
            returns[t.member_id]["unrealized_pnl"] += implied_shares * (current_price - entry_price)
            returns[t.member_id]["unrealized_cost_basis"] += invested

    return dict(returns)
