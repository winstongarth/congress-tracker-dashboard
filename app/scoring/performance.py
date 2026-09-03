"""7.1 Performance score (per trade, rolls up to per-member).

% price change of the ticker from transaction_date to today, or to the sale
date if a matching sell was later disclosed. Buys score on raw upside; sells
invert the framing -- a sell followed by a price drop is a "good" sell, so a
sell's score is how much the price fell *after* the sale.

'exchange' transactions (spinoffs, distributions, etc.) aren't discretionary
buy/sell decisions, so they're skipped here rather than forced into a
buy/sell framing that wouldn't mean anything.
"""

from __future__ import annotations

import bisect
import datetime as dt
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PriceHistory, Trade


class PriceSeries:
    """ticker -> sorted (date, close) pairs, with nearest-available lookup."""

    def __init__(self, session: Session, tickers: set[str]) -> None:
        self._series: dict[str, list[tuple[dt.date, float]]] = defaultdict(list)
        if not tickers:
            return
        rows = session.execute(
            select(PriceHistory.ticker, PriceHistory.date, PriceHistory.close_price).where(
                PriceHistory.ticker.in_(tickers)
            )
        ).all()
        for ticker, date, close in rows:
            self._series[ticker].append((date, float(close)))
        for ticker in self._series:
            self._series[ticker].sort()

    def price_near(self, ticker: str, target: dt.date) -> float | None:
        series = self._series.get(ticker)
        if not series:
            return None
        dates = [d for d, _ in series]
        idx = bisect.bisect_right(dates, target)
        if idx > 0:
            return series[idx - 1][1]  # most recent close on/before target
        return series[0][1]  # fall back to earliest available close


def match_exit_dates(trades: list[Trade]) -> dict[int, dt.date]:
    """FIFO-matches each buy to the earliest later sell of the same ticker for
    that member+owner. Returns trade_id -> exit_date for buys with a match.
    """
    groups: dict[tuple[str, str, str], list[Trade]] = defaultdict(list)
    for t in trades:
        groups[(t.member_id, t.ticker, t.owner)].append(t)

    exit_dates: dict[int, dt.date] = {}
    for group in groups.values():
        group.sort(key=lambda t: t.transaction_date)
        sells = [t for t in group if t.transaction_type == "sell"]
        sell_idx = 0
        for t in group:
            if t.transaction_type != "buy":
                continue
            while sell_idx < len(sells) and sells[sell_idx].transaction_date <= t.transaction_date:
                sell_idx += 1
            if sell_idx < len(sells):
                exit_dates[t.trade_id] = sells[sell_idx].transaction_date
                sell_idx += 1
    return exit_dates


def compute_performance(session: Session, trades: list[Trade]) -> dict[int, float]:
    """trade_id -> raw (unnormalized) performance percentage for every
    buy/sell stock trade with a resolved ticker. Caller normalizes: every
    sub-score is percentile-ranked within its population before combining.
    """
    scoreable = [t for t in trades if t.ticker and t.asset_type == "stock" and t.transaction_type in ("buy", "sell")]
    tickers = {t.ticker for t in scoreable}
    prices = PriceSeries(session, tickers)
    today = dt.date.today()
    exit_dates = match_exit_dates(scoreable)

    results: dict[int, float] = {}
    for t in scoreable:
        entry_price = prices.price_near(t.ticker, t.transaction_date)
        if entry_price is None or entry_price == 0:
            continue

        if t.transaction_type == "buy":
            exit_date = exit_dates.get(t.trade_id, today)
            exit_price = prices.price_near(t.ticker, exit_date)
            if exit_price is None:
                continue
            results[t.trade_id] = (exit_price - entry_price) / entry_price * 100
        else:  # sell: inverted framing -- reward price drops after the sale
            current_price = prices.price_near(t.ticker, today)
            if current_price is None:
                continue
            results[t.trade_id] = (entry_price - current_price) / entry_price * 100

    return results
