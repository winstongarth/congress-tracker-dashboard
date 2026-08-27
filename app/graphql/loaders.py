"""DataLoaders that batch the two N+1-prone lookups the brief calls out:

- politician -> trades: naively resolving `Politician.trades` per politician
  in a `politicians(...)` list would issue one `SELECT ... WHERE member_id = ?`
  per politician. trades_by_member batches all of them into a single
  `WHERE member_id IN (...)` per request tick.
- trade -> ticker: `Trade.sector`/`Trade.industry` come from `ticker_metadata`,
  a separate table with no ORM relationship. ticker_metadata batches those
  lookups the same way.

scores_by_trade extends the same pattern to the `scores` table: a trade's
performance/overlap/conviction/composite each live as a separate row keyed by
trade_id, so naively resolving all four per trade would be a 4x N+1. It
reuses app.services.trade_scores.fetch_scores_by_trade -- the same function
the REST /trades route uses -- so both API layers read scores identically.

All three loaders are created fresh per-request (see app/graphql/context.py)
so their internal caches never leak across requests.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session
from strawberry.dataloader import DataLoader

from app.db.models import TickerMetadata, Trade
from app.services.ticker_metadata import fetch_ticker_metadata
from app.services.trade_scores import fetch_scores_by_trade


@dataclass
class Loaders:
    trades_by_member: DataLoader[str, list[Trade]]
    ticker_metadata: DataLoader[str, TickerMetadata | None]
    scores_by_trade: DataLoader[int, dict[str, float]]


def make_loaders(db: Session) -> Loaders:
    async def batch_trades_by_member(member_ids: list[str]) -> list[list[Trade]]:
        rows = list(
            db.scalars(
                select(Trade).where(Trade.member_id.in_(member_ids)).order_by(Trade.transaction_date.desc())
            )
        )
        by_member: dict[str, list[Trade]] = {mid: [] for mid in member_ids}
        for t in rows:
            by_member[t.member_id].append(t)
        return [by_member[mid] for mid in member_ids]

    async def batch_ticker_metadata(tickers: list[str]) -> list[TickerMetadata | None]:
        metadata = fetch_ticker_metadata(db, set(tickers))
        return [metadata.get(ticker) for ticker in tickers]

    async def batch_scores_by_trade(trade_ids: list[int]) -> list[dict[str, float]]:
        scores = fetch_scores_by_trade(db, list(trade_ids))
        return [scores.get(trade_id, {}) for trade_id in trade_ids]

    return Loaders(
        trades_by_member=DataLoader(load_fn=batch_trades_by_member),
        ticker_metadata=DataLoader(load_fn=batch_ticker_metadata),
        scores_by_trade=DataLoader(load_fn=batch_scores_by_trade),
    )
