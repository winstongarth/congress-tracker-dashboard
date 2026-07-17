from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import MemberSummary, TradeOut, TradePage
from app.db.models import Member, Score, TickerMetadata, Trade

router = APIRouter(prefix="/trades", tags=["trades"])

SORTABLE_COLUMNS = {
    "transaction_date": Trade.transaction_date,
    "disclosure_date": Trade.disclosure_date,
    "filing_lag_days": Trade.filing_lag_days,
    "amount": Trade.amount_mid,
}

FILING_LAG_BUCKETS = {
    "within_10": (0, 10),
    "11_to_30": (11, 30),
    "31_to_45": (31, 45),
    "late": (46, None),
}


@router.get("", response_model=TradePage)
def list_trades(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("transaction_date"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    sector: str | None = None,
    party: str | None = Query(None, pattern="^[DRI]$"),
    bipartisan_only: bool = False,
    chamber: str | None = Query(None, pattern="^(house|senate)$"),
    transaction_type: str | None = None,
    asset_type: str | None = None,
    transaction_date_from: dt.date | None = None,
    transaction_date_to: dt.date | None = None,
    disclosure_date_from: dt.date | None = None,
    disclosure_date_to: dt.date | None = None,
    filing_lag_bucket: str | None = Query(None, pattern="^(within_10|11_to_30|31_to_45|late)$"),
    committee_relevant: bool | None = None,
    member_id: str | None = None,
    ticker: str | None = None,
    search: str | None = None,
) -> TradePage:
    stmt = select(Trade).join(Member, Trade.member_id == Member.member_id)

    if sector or asset_type == "stock":
        stmt = stmt.outerjoin(TickerMetadata, Trade.ticker == TickerMetadata.ticker)
    if sector:
        stmt = stmt.where(TickerMetadata.sector == sector)
    if party:
        stmt = stmt.where(Member.party == party)
    if bipartisan_only:
        stmt = stmt.where(Trade.bipartisan_overlap.is_(True))
    if chamber:
        stmt = stmt.where(Member.chamber == chamber)
    if transaction_type:
        stmt = stmt.where(Trade.transaction_type == transaction_type)
    if asset_type:
        stmt = stmt.where(Trade.asset_type == asset_type)
    if transaction_date_from:
        stmt = stmt.where(Trade.transaction_date >= transaction_date_from)
    if transaction_date_to:
        stmt = stmt.where(Trade.transaction_date <= transaction_date_to)
    if disclosure_date_from:
        stmt = stmt.where(Trade.disclosure_date >= disclosure_date_from)
    if disclosure_date_to:
        stmt = stmt.where(Trade.disclosure_date <= disclosure_date_to)
    if filing_lag_bucket:
        low, high = FILING_LAG_BUCKETS[filing_lag_bucket]
        stmt = stmt.where(Trade.filing_lag_days >= low)
        if high is not None:
            stmt = stmt.where(Trade.filing_lag_days <= high)
    if committee_relevant is not None:
        stmt = stmt.where(Trade.committee_relevant.is_(committee_relevant))
    if member_id:
        stmt = stmt.where(Trade.member_id == member_id)
    if ticker:
        stmt = stmt.where(Trade.ticker == ticker.upper())
    if search:
        like = f"%{search}%"
        stmt = stmt.where((Member.full_name.ilike(like)) | (Trade.ticker.ilike(like)) | (Trade.asset_name_raw.ilike(like)))

    total = len(db.scalars(stmt).all())

    if sort_by in SORTABLE_COLUMNS:
        col = SORTABLE_COLUMNS[sort_by]
        stmt = stmt.order_by(col.desc() if sort_dir == "desc" else col.asc())
    # composite/performance/overlap/conviction sorting happens after merging
    # in score values below, since they live in a separate table keyed by
    # trade_id rather than as columns on trades.

    all_trades = list(db.scalars(stmt))

    score_rows = db.execute(
        select(Score.trade_id, Score.score_type, Score.value).where(
            Score.trade_id.in_([t.trade_id for t in all_trades])
        )
    ).all()
    scores_by_trade: dict[int, dict[str, float]] = {}
    for trade_id, score_type, value in score_rows:
        scores_by_trade.setdefault(trade_id, {})[score_type] = value

    if sort_by in ("composite", "performance", "overlap", "conviction"):
        all_trades.sort(
            key=lambda t: scores_by_trade.get(t.trade_id, {}).get(sort_by, float("-inf")),
            reverse=(sort_dir == "desc"),
        )

    page_trades = all_trades[(page - 1) * page_size : page * page_size]

    tickers = {t.ticker for t in page_trades if t.ticker}
    metadata_by_ticker = {
        tm.ticker: tm for tm in db.scalars(select(TickerMetadata).where(TickerMetadata.ticker.in_(tickers)))
    } if tickers else {}

    results = []
    for t in page_trades:
        meta = metadata_by_ticker.get(t.ticker)
        trade_scores = scores_by_trade.get(t.trade_id, {})
        results.append(
            TradeOut(
                trade_id=t.trade_id,
                member=MemberSummary.model_validate(t.member, from_attributes=True),
                filing_id=t.filing_id,
                asset_name_raw=t.asset_name_raw,
                ticker=t.ticker,
                ticker_match_confidence=t.ticker_match_confidence,
                asset_type=t.asset_type,
                sector=meta.sector if meta else None,
                industry=meta.industry if meta else None,
                owner=t.owner,
                transaction_type=t.transaction_type,
                transaction_date=t.transaction_date,
                disclosure_date=t.disclosure_date,
                filing_lag_days=t.filing_lag_days,
                amount_min=float(t.amount_min),
                amount_max=float(t.amount_max),
                amount_mid=float(t.amount_mid),
                source_url=t.source_url,
                committee_relevant=t.committee_relevant,
                performance=trade_scores.get("performance"),
                overlap=trade_scores.get("overlap"),
                conviction=trade_scores.get("conviction"),
                composite=trade_scores.get("composite"),
                bipartisan_overlap=t.bipartisan_overlap,
            )
        )

    return TradePage(total=total, page=page, page_size=page_size, results=results)
