from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import MemberDetail, MemberListEntry
from app.db.models import Member, PortfolioReturn, Score, TickerMetadata, Trade

router = APIRouter(prefix="/members", tags=["members"])

LIST_SORT_KEYS = {
    "full_name": lambda e: e.full_name,
    "trade_count": lambda e: e.trade_count,
    "realized_pnl": lambda e: e.realized_pnl if e.realized_pnl is not None else float("-inf"),
    "unrealized_pnl": lambda e: e.unrealized_pnl if e.unrealized_pnl is not None else float("-inf"),
    "realized_pnl_pct": lambda e: e.realized_pnl_pct if e.realized_pnl_pct is not None else float("-inf"),
    "unrealized_pnl_pct": lambda e: e.unrealized_pnl_pct if e.unrealized_pnl_pct is not None else float("-inf"),
}


def _portfolio_fields(pr: PortfolioReturn | None) -> dict:
    if pr is None:
        return {
            "realized_pnl": None,
            "realized_cost_basis": None,
            "realized_pnl_pct": None,
            "unrealized_pnl": None,
            "unrealized_cost_basis": None,
            "unrealized_pnl_pct": None,
        }
    return {
        "realized_pnl": float(pr.realized_pnl),
        "realized_cost_basis": float(pr.realized_cost_basis),
        "realized_pnl_pct": pr.realized_pnl_pct,
        "unrealized_pnl": float(pr.unrealized_pnl),
        "unrealized_cost_basis": float(pr.unrealized_cost_basis),
        "unrealized_pnl_pct": pr.unrealized_pnl_pct,
    }


@router.get("", response_model=list[MemberListEntry])
def list_members(
    db: Session = Depends(get_db),
    chamber: str | None = None,
    party: str | None = None,
    sort_by: str = Query("full_name"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
) -> list[MemberListEntry]:
    stmt = select(Member).where(Member.active.is_(True))
    if chamber:
        stmt = stmt.where(Member.chamber == chamber)
    if party:
        stmt = stmt.where(Member.party == party)
    members = list(db.scalars(stmt))

    trade_counts = dict(db.execute(select(Trade.member_id, func.count(Trade.trade_id)).group_by(Trade.member_id)).all())
    returns_by_member = {pr.member_id: pr for pr in db.scalars(select(PortfolioReturn))}

    entries = [
        MemberListEntry(
            member_id=m.member_id,
            full_name=m.full_name,
            chamber=m.chamber,
            party=m.party,
            state=m.state,
            district=m.district,
            photo_url=m.photo_url,
            trade_count=trade_counts.get(m.member_id, 0),
            **_portfolio_fields(returns_by_member.get(m.member_id)),
        )
        for m in members
    ]

    key_fn = LIST_SORT_KEYS.get(sort_by, LIST_SORT_KEYS["full_name"])
    entries.sort(key=key_fn, reverse=(sort_dir == "desc"))
    return entries


@router.get("/{member_id}", response_model=MemberDetail)
def get_member(member_id: str, db: Session = Depends(get_db)) -> MemberDetail:
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    trades = list(db.scalars(select(Trade).where(Trade.member_id == member_id)))

    rollup = db.scalar(
        select(Score.value).where(
            Score.member_id == member_id, Score.score_type == "performance", Score.trade_id.is_(None)
        )
    )
    portfolio_return = db.get(PortfolioReturn, member_id)

    tickers = {t.ticker for t in trades if t.ticker}
    metadata_by_ticker = {
        tm.ticker: tm for tm in db.scalars(select(TickerMetadata).where(TickerMetadata.ticker.in_(tickers)))
    } if tickers else {}

    sector_totals: dict[str, float] = defaultdict(float)
    for t in trades:
        meta = metadata_by_ticker.get(t.ticker)
        sector = meta.sector if meta and meta.sector else "Unknown"
        sector_totals[sector] += float(t.amount_mid)

    return MemberDetail(
        member_id=member.member_id,
        full_name=member.full_name,
        chamber=member.chamber,
        party=member.party,
        state=member.state,
        district=member.district,
        photo_url=member.photo_url,
        committees=member.committees or [],
        performance_rollup=rollup,
        trade_count=len(trades),
        sector_breakdown=dict(sector_totals),
        **_portfolio_fields(portfolio_return),
    )
