"""SQLAlchemy models mirroring the application's data model field-for-field."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = "members"

    member_id: Mapped[str] = mapped_column(String, primary_key=True)  # = bioguide_id
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    chamber: Mapped[str] = mapped_column(String, nullable=False)  # 'house' | 'senate'
    party: Mapped[str] = mapped_column(String, nullable=False)  # 'D' | 'R' | 'I'
    state: Mapped[str] = mapped_column(String, nullable=False)
    district: Mapped[str | None] = mapped_column(String, nullable=True)  # null for senators
    committees: Mapped[list] = mapped_column(JSON, default=list)  # json array of committee names
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Trade(Base):
    __tablename__ = "trades"

    trade_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.member_id"), nullable=False)
    member: Mapped[Member] = relationship(lazy="joined")
    filing_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    asset_name_raw: Mapped[str] = mapped_column(String, nullable=False)
    ticker: Mapped[str | None] = mapped_column(String, nullable=True)
    ticker_match_confidence: Mapped[float | None] = mapped_column(nullable=True)  # 0-1
    asset_type: Mapped[str] = mapped_column(String, nullable=False)  # stock|option|bond|fund|crypto|other
    owner: Mapped[str] = mapped_column(String, nullable=False)  # self|spouse|joint|dependent_child
    transaction_type: Mapped[str] = mapped_column(String, nullable=False)  # buy|sell|exchange
    transaction_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    disclosure_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    filing_lag_days: Mapped[int] = mapped_column(nullable=False)  # disclosure_date - transaction_date
    amount_min: Mapped[float] = mapped_column(Numeric, nullable=False)
    amount_max: Mapped[float] = mapped_column(Numeric, nullable=False)
    amount_mid: Mapped[float] = mapped_column(Numeric, nullable=False)  # computed midpoint
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    # Qualitative badge/filter, deliberately not folded into the numeric
    # composite score -- lives on the row itself since the dashboard filters
    # trades by it directly, not via a scores-table join.
    committee_relevant: Mapped[bool] = mapped_column(Boolean, default=False)
    # Worth surfacing distinctly in the UI -- same reasoning as
    # committee_relevant, denormalized here for direct dashboard filtering.
    bipartisan_overlap: Mapped[bool] = mapped_column(Boolean, default=False)


class TickerMetadata(Base):
    __tablename__ = "ticker_metadata"

    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    sector: Mapped[str | None] = mapped_column(String, nullable=True)  # GICS sector
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    last_refreshed: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class PriceHistory(Base):
    __tablename__ = "price_history"

    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    close_price: Mapped[float] = mapped_column(Numeric, nullable=False)


class Score(Base):
    """Recomputed on each scoring run, not derived live in the UI."""

    __tablename__ = "scores"

    score_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.member_id"), nullable=False)
    ticker: Mapped[str | None] = mapped_column(String, nullable=True)  # nullable for member-level-only scores
    # performance/recency/composite scores are scoped "per trade" rather than
    # per member+ticker -- nullable FK so those can attach to one specific
    # trade, while member-level rollups and ticker-level aggregates
    # (conviction, ticker overlap) leave this null and use member_id/ticker alone.
    # CASCADE: scores are recomputed wholesale on every `score` run anyway, so
    # a deleted trade (re-scraping a filing, an amendment superseding rows)
    # should take its scores with it rather than blocking the delete or
    # leaving orphaned rows pointing at a trade_id that no longer exists.
    trade_id: Mapped[int | None] = mapped_column(ForeignKey("trades.trade_id", ondelete="CASCADE"), nullable=True)
    score_type: Mapped[str] = mapped_column(String, nullable=False)
    # 'performance' | 'overlap' | 'conviction' | 'composite'
    value: Mapped[float] = mapped_column(nullable=False)
    computed_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class PortfolioReturn(Base):
    """Member-level realized/unrealized P&L. Kept out of `scores` deliberately:
    everything in that table is a 0-100 percentile-ranked sub-score, while
    these are real dollar amounts and percentages -- a different kind of
    number with its own table, recomputed wholesale on each `score` run same
    as everything else (not derived live in the UI).
    """

    __tablename__ = "portfolio_returns"

    member_id: Mapped[str] = mapped_column(ForeignKey("members.member_id"), primary_key=True)
    realized_pnl: Mapped[float] = mapped_column(Numeric, nullable=False)
    realized_cost_basis: Mapped[float] = mapped_column(Numeric, nullable=False)
    realized_pnl_pct: Mapped[float | None] = mapped_column(nullable=True)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric, nullable=False)
    unrealized_cost_basis: Mapped[float] = mapped_column(Numeric, nullable=False)
    unrealized_pnl_pct: Mapped[float | None] = mapped_column(nullable=True)
    computed_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
