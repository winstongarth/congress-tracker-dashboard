from __future__ import annotations

import datetime as dt
from typing import Annotated

import strawberry
from sqlalchemy import func, select

from app.db.models import Member
from app.db.models import Trade as TradeModel
from app.graphql.types import (
    Chamber,
    Politician,
    PoliticianConnection,
    Trade,
    TradeConnection,
    build_politician,
    build_trade,
)


@strawberry.type
class Query:
    @strawberry.field(description="Search/browse tracked members of Congress.")
    def politicians(
        self,
        info: strawberry.Info,
        search: str | None = None,
        chamber: Chamber | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PoliticianConnection:
        db = info.context["db"]
        stmt = select(Member).where(Member.active.is_(True))
        if chamber is not None:
            stmt = stmt.where(Member.chamber == chamber.value)
        if search:
            stmt = stmt.where(Member.full_name.ilike(f"%{search}%"))

        total = db.scalar(select(func.count()).select_from(stmt.subquery()))
        rows = db.scalars(stmt.order_by(Member.full_name).offset(offset).limit(limit)).all()
        return PoliticianConnection(total_count=total or 0, results=[build_politician(m) for m in rows])

    @strawberry.field(description="A single member of Congress by id (bioguide id).")
    def politician(self, info: strawberry.Info, id: strawberry.ID) -> Politician | None:
        member = info.context["db"].get(Member, str(id))
        return build_politician(member) if member is not None else None

    @strawberry.field(description="Search/browse tracked trades.")
    def trades(
        self,
        info: strawberry.Info,
        ticker: str | None = None,
        politician_id: strawberry.ID | None = None,
        from_: Annotated[dt.date | None, strawberry.argument(name="from")] = None,
        to: dt.date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TradeConnection:
        db = info.context["db"]
        stmt = select(TradeModel)
        if ticker:
            stmt = stmt.where(TradeModel.ticker == ticker.upper())
        if politician_id is not None:
            stmt = stmt.where(TradeModel.member_id == str(politician_id))
        if from_ is not None:
            stmt = stmt.where(TradeModel.transaction_date >= from_)
        if to is not None:
            stmt = stmt.where(TradeModel.transaction_date <= to)

        total = db.scalar(select(func.count()).select_from(stmt.subquery()))
        rows = db.scalars(stmt.order_by(TradeModel.transaction_date.desc()).offset(offset).limit(limit)).all()
        return TradeConnection(total_count=total or 0, results=[build_trade(t) for t in rows])
