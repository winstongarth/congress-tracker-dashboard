from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class MemberSummary(BaseModel):
    member_id: str
    full_name: str
    chamber: str
    party: str
    state: str
    district: str | None
    photo_url: str | None


class TradeOut(BaseModel):
    trade_id: int
    member: MemberSummary
    filing_id: str
    asset_name_raw: str
    ticker: str | None
    ticker_match_confidence: float | None
    asset_type: str
    sector: str | None
    industry: str | None
    owner: str
    transaction_type: str
    transaction_date: dt.date
    disclosure_date: dt.date
    filing_lag_days: int
    amount_min: float
    amount_max: float
    amount_mid: float
    source_url: str
    committee_relevant: bool
    performance: float | None
    overlap: float | None
    conviction: float | None
    composite: float | None
    bipartisan_overlap: bool


class TradePage(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[TradeOut]


class PortfolioReturnFields(BaseModel):
    realized_pnl: float | None
    realized_cost_basis: float | None
    realized_pnl_pct: float | None
    unrealized_pnl: float | None
    unrealized_cost_basis: float | None
    unrealized_pnl_pct: float | None


class MemberListEntry(MemberSummary, PortfolioReturnFields):
    trade_count: int


class MemberDetail(MemberSummary, PortfolioReturnFields):
    committees: list[str]
    performance_rollup: float | None
    trade_count: int
    sector_breakdown: dict[str, float]  # sector -> total amount_mid


class TickerTradeEntry(BaseModel):
    member: MemberSummary
    transaction_type: str
    transaction_date: dt.date
    amount_min: float
    amount_max: float
    bipartisan_overlap: bool


class TickerDetail(BaseModel):
    ticker: str
    company_name: str | None
    sector: str | None
    industry: str | None
    trades: list[TickerTradeEntry]
    distinct_members: int
    has_bipartisan_overlap: bool
