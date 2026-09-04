from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.api.main import app
from app.db.models import Base, Member, PortfolioReturn, Score, TickerMetadata, Trade


@pytest.fixture()
def engine():
    # A single shared in-memory SQLite connection (StaticPool) so every
    # Session opened during a test -- REST routes and the test's own setup
    # session -- sees the same data.
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def db_session(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def make_member(db_session):
    def _make(member_id="M1", full_name="Jane Doe", chamber="house", party="D", state="CA", **kwargs):
        m = Member(
            member_id=member_id,
            full_name=full_name,
            chamber=chamber,
            party=party,
            state=state,
            district=kwargs.get("district"),
            committees=kwargs.get("committees", []),
            photo_url=kwargs.get("photo_url"),
            active=kwargs.get("active", True),
        )
        db_session.add(m)
        db_session.commit()
        return m

    return _make


@pytest.fixture()
def make_trade(db_session):
    def _make(member_id, ticker="AAPL", transaction_type="buy", transaction_date=None, **kwargs):
        transaction_date = transaction_date or dt.date(2026, 1, 1)
        t = Trade(
            member_id=member_id,
            filing_id=kwargs.get("filing_id", "F1"),
            asset_name_raw=kwargs.get("asset_name_raw", "Apple Inc"),
            ticker=ticker,
            ticker_match_confidence=kwargs.get("ticker_match_confidence", 0.99),
            asset_type=kwargs.get("asset_type", "stock"),
            owner=kwargs.get("owner", "self"),
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            disclosure_date=kwargs.get("disclosure_date", transaction_date + dt.timedelta(days=10)),
            filing_lag_days=kwargs.get("filing_lag_days", 10),
            amount_min=kwargs.get("amount_min", 1000),
            amount_max=kwargs.get("amount_max", 15000),
            amount_mid=kwargs.get("amount_mid", 8000),
            source_url=kwargs.get("source_url", "https://example.com"),
            committee_relevant=kwargs.get("committee_relevant", False),
            bipartisan_overlap=kwargs.get("bipartisan_overlap", False),
        )
        db_session.add(t)
        db_session.commit()
        return t

    return _make


@pytest.fixture()
def make_score(db_session):
    def _make(member_id, score_type, value, trade_id=None):
        s = Score(member_id=member_id, ticker=None, trade_id=trade_id, score_type=score_type, value=value)
        db_session.add(s)
        db_session.commit()
        return s

    return _make


@pytest.fixture()
def make_ticker_metadata(db_session):
    def _make(ticker, company_name="Apple Inc.", sector="Technology", industry="Consumer Electronics"):
        tm = TickerMetadata(ticker=ticker, company_name=company_name, sector=sector, industry=industry)
        db_session.add(tm)
        db_session.commit()
        return tm

    return _make


@pytest.fixture()
def make_portfolio_return(db_session):
    def _make(member_id, **kwargs):
        pr = PortfolioReturn(
            member_id=member_id,
            realized_pnl=kwargs.get("realized_pnl", 100.0),
            realized_cost_basis=kwargs.get("realized_cost_basis", 1000.0),
            realized_pnl_pct=kwargs.get("realized_pnl_pct", 10.0),
            unrealized_pnl=kwargs.get("unrealized_pnl", 50.0),
            unrealized_cost_basis=kwargs.get("unrealized_cost_basis", 500.0),
            unrealized_pnl_pct=kwargs.get("unrealized_pnl_pct", 10.0),
        )
        db_session.add(pr)
        db_session.commit()
        return pr

    return _make
