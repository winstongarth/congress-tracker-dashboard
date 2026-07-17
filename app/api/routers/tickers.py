from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import MemberSummary, TickerDetail, TickerTradeEntry
from app.db.models import TickerMetadata, Trade

router = APIRouter(prefix="/tickers", tags=["tickers"])


@router.get("/{ticker}", response_model=TickerDetail)
def get_ticker(ticker: str, db: Session = Depends(get_db)) -> TickerDetail:
    ticker = ticker.upper()
    trades = list(
        db.scalars(select(Trade).where(Trade.ticker == ticker).order_by(Trade.transaction_date.desc()))
    )
    if not trades:
        raise HTTPException(status_code=404, detail="No tracked trades for this ticker")

    meta = db.get(TickerMetadata, ticker)

    entries = [
        TickerTradeEntry(
            member=MemberSummary.model_validate(t.member, from_attributes=True),
            transaction_type=t.transaction_type,
            transaction_date=t.transaction_date,
            amount_min=float(t.amount_min),
            amount_max=float(t.amount_max),
            bipartisan_overlap=t.bipartisan_overlap,
        )
        for t in trades
    ]

    return TickerDetail(
        ticker=ticker,
        company_name=meta.company_name if meta else None,
        sector=meta.sector if meta else None,
        industry=meta.industry if meta else None,
        trades=entries,
        distinct_members=len({t.member_id for t in trades}),
        has_bipartisan_overlap=any(t.bipartisan_overlap for t in trades),
    )
