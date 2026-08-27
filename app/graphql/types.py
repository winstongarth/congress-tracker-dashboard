"""Strawberry GraphQL types, mapped field-for-field onto the real SQLAlchemy
models (app/db/models.py) and enums onto the real stored string values.
Fields that require a batched lookup against a side table (scores, ticker
metadata) are resolved lazily via the DataLoaders in app/graphql/loaders.py
-- see the comments on Trade.sector/performance/etc. below."""

from __future__ import annotations

import datetime as dt
import enum

import strawberry

from app.db.models import Member
from app.db.models import Trade as TradeModel


@strawberry.enum
class Chamber(enum.Enum):
    HOUSE = "house"
    SENATE = "senate"


@strawberry.enum
class Party(enum.Enum):
    D = "D"
    R = "R"
    I = "I"


@strawberry.enum
class AssetType(enum.Enum):
    STOCK = "stock"
    OPTION = "option"
    BOND = "bond"
    FUND = "fund"
    CRYPTO = "crypto"
    OTHER = "other"


@strawberry.enum
class Owner(enum.Enum):
    SELF = "self"
    SPOUSE = "spouse"
    JOINT = "joint"
    DEPENDENT_CHILD = "dependent_child"


@strawberry.enum
class TransactionType(enum.Enum):
    BUY = "buy"
    SELL = "sell"
    EXCHANGE = "exchange"


@strawberry.type
class PortfolioReturnType:
    realized_pnl: float | None
    realized_cost_basis: float | None
    realized_pnl_pct: float | None
    unrealized_pnl: float | None
    unrealized_cost_basis: float | None
    unrealized_pnl_pct: float | None


@strawberry.type
class SectorBreakdownEntry:
    sector: str
    amount_mid: float


@strawberry.type
class Politician:
    id: strawberry.ID
    full_name: str
    chamber: Chamber
    party: Party
    state: str
    district: str | None
    committees: list[str]
    photo_url: str | None
    active: bool

    @strawberry.field(description="Number of trades on file for this member.")
    def trade_count(self, info: strawberry.Info) -> int:
        from sqlalchemy import func, select

        db = info.context["db"]
        return db.scalar(select(func.count()).select_from(TradeModel).where(TradeModel.member_id == self.id)) or 0

    @strawberry.field(description="Member-level performance rollup (0-100 percentile), if computed.")
    def performance(self, info: strawberry.Info) -> float | None:
        from app.services.member_metrics import fetch_performance_rollup

        return fetch_performance_rollup(info.context["db"], str(self.id))

    @strawberry.field(description="Realized/unrealized P&L for this member, if computed.")
    def portfolio_return(self, info: strawberry.Info) -> PortfolioReturnType | None:
        from app.db.models import PortfolioReturn

        pr = info.context["db"].get(PortfolioReturn, str(self.id))
        if pr is None:
            return None
        return PortfolioReturnType(
            realized_pnl=float(pr.realized_pnl),
            realized_cost_basis=float(pr.realized_cost_basis),
            realized_pnl_pct=pr.realized_pnl_pct,
            unrealized_pnl=float(pr.unrealized_pnl),
            unrealized_cost_basis=float(pr.unrealized_cost_basis),
            unrealized_pnl_pct=pr.unrealized_pnl_pct,
        )

    @strawberry.field(description="Total disclosed amount_mid per sector across this member's trades.")
    def sector_breakdown(self, info: strawberry.Info) -> list[SectorBreakdownEntry]:
        from app.services.member_metrics import fetch_sector_breakdown

        breakdown = fetch_sector_breakdown(info.context["db"], str(self.id))
        return [SectorBreakdownEntry(sector=sector, amount_mid=amount) for sector, amount in breakdown.items()]

    @strawberry.field(description="This member's trades, most recent first.")
    async def trades(self, info: strawberry.Info, limit: int = 50, offset: int = 0) -> "TradeConnection":
        # Batched: every Politician.trades field resolved in the same GraphQL
        # request is collapsed into a single `WHERE member_id IN (...)` query
        # by trades_by_member_loader, instead of one query per politician.
        all_trades = await info.context["loaders"].trades_by_member.load(str(self.id))
        page = all_trades[offset : offset + limit]
        return TradeConnection(total_count=len(all_trades), results=[build_trade(t) for t in page])


def build_politician(m: Member) -> Politician:
    return Politician(
        id=strawberry.ID(m.member_id),
        full_name=m.full_name,
        chamber=Chamber(m.chamber),
        party=Party(m.party),
        state=m.state,
        district=m.district,
        committees=list(m.committees or []),
        photo_url=m.photo_url,
        active=m.active,
    )


@strawberry.type
class PoliticianConnection:
    total_count: int
    results: list[Politician]


@strawberry.type
class Trade:
    id: strawberry.ID
    filing_id: str
    asset_name_raw: str
    ticker: str | None
    ticker_match_confidence: float | None
    asset_type: AssetType
    owner: Owner
    transaction_type: TransactionType
    transaction_date: dt.date
    disclosure_date: dt.date
    filing_lag_days: int
    amount_min: float
    amount_max: float
    amount_mid: float
    source_url: str
    committee_relevant: bool
    bipartisan_overlap: bool

    # Stashed off-schema so the lazy fields below don't need a second fetch.
    _politician: strawberry.Private[Politician]
    _ticker_row: strawberry.Private[str | None]
    _trade_id_row: strawberry.Private[int]

    @strawberry.field(description="The member who filed this trade.")
    def politician(self) -> Politician:
        return self._politician

    @strawberry.field(description="GICS-ish sector for the matched ticker, if any.")
    async def sector(self, info: strawberry.Info) -> str | None:
        # Batched: every Trade.sector/industry resolved in this request is
        # collapsed into one `WHERE ticker IN (...)` query against
        # ticker_metadata via ticker_metadata_loader, instead of one query
        # per trade row.
        if not self._ticker_row:
            return None
        meta = await info.context["loaders"].ticker_metadata.load(self._ticker_row)
        return meta.sector if meta else None

    @strawberry.field(description="Industry for the matched ticker, if any.")
    async def industry(self, info: strawberry.Info) -> str | None:
        if not self._ticker_row:
            return None
        meta = await info.context["loaders"].ticker_metadata.load(self._ticker_row)
        return meta.industry if meta else None

    @strawberry.field(description="0-100 percentile performance score for this trade, if computed.")
    async def performance(self, info: strawberry.Info) -> float | None:
        # Batched via scores_by_trade_loader -- same N+1 shape as sector/
        # industry above, but against the `scores` table instead of
        # `ticker_metadata`. Reuses app.services.trade_scores.fetch_scores_by_trade,
        # the exact function the REST /trades route uses, so both API layers
        # read the same values the same way.
        scores = await info.context["loaders"].scores_by_trade.load(self._trade_id_row)
        return scores.get("performance")

    @strawberry.field(description="0-100 percentile overlap score for this trade, if computed.")
    async def overlap(self, info: strawberry.Info) -> float | None:
        scores = await info.context["loaders"].scores_by_trade.load(self._trade_id_row)
        return scores.get("overlap")

    @strawberry.field(description="0-100 percentile conviction score for this trade, if computed.")
    async def conviction(self, info: strawberry.Info) -> float | None:
        scores = await info.context["loaders"].scores_by_trade.load(self._trade_id_row)
        return scores.get("conviction")

    @strawberry.field(description="0-100 weighted composite score for this trade, if computed.")
    async def composite(self, info: strawberry.Info) -> float | None:
        scores = await info.context["loaders"].scores_by_trade.load(self._trade_id_row)
        return scores.get("composite")


def build_trade(t: TradeModel) -> "Trade":
    return Trade(
        id=strawberry.ID(str(t.trade_id)),
        filing_id=t.filing_id,
        asset_name_raw=t.asset_name_raw,
        ticker=t.ticker,
        ticker_match_confidence=t.ticker_match_confidence,
        asset_type=AssetType(t.asset_type),
        owner=Owner(t.owner),
        transaction_type=TransactionType(t.transaction_type),
        transaction_date=t.transaction_date,
        disclosure_date=t.disclosure_date,
        filing_lag_days=t.filing_lag_days,
        amount_min=float(t.amount_min),
        amount_max=float(t.amount_max),
        amount_mid=float(t.amount_mid),
        source_url=t.source_url,
        committee_relevant=t.committee_relevant,
        bipartisan_overlap=t.bipartisan_overlap,
        _politician=build_politician(t.member),
        _ticker_row=t.ticker,
        _trade_id_row=t.trade_id,
    )


@strawberry.type
class TradeConnection:
    total_count: int
    results: list[Trade]
