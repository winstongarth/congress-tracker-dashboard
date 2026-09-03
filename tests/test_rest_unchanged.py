"""Regression coverage ensuring zero changes to existing REST response
shapes, even though the underlying score/metric lookups were extracted
into app/services/* so GraphQL could reuse them."""

from __future__ import annotations

import datetime as dt


def test_rest_trades_response_shape_unchanged(client, make_member, make_trade, make_ticker_metadata, make_score):
    make_member(member_id="M1", full_name="Jane Doe", chamber="house", party="D", state="CA")
    make_ticker_metadata("AAPL", sector="Technology", industry="Consumer Electronics")
    t = make_trade("M1", ticker="AAPL", transaction_date=dt.date(2026, 1, 1))
    make_score("M1", "performance", 55.0, trade_id=t.trade_id)
    make_score("M1", "composite", 61.0, trade_id=t.trade_id)

    resp = client.get("/trades", params={"page": 1, "page_size": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["page_size"] == 10

    row = body["results"][0]
    assert row["ticker"] == "AAPL"
    assert row["sector"] == "Technology"
    assert row["industry"] == "Consumer Electronics"
    assert row["performance"] == 55.0
    assert row["composite"] == 61.0
    assert row["overlap"] is None
    assert row["conviction"] is None
    assert set(row.keys()) == {
        "trade_id", "member", "filing_id", "asset_name_raw", "ticker", "ticker_match_confidence",
        "asset_type", "sector", "industry", "owner", "transaction_type", "transaction_date",
        "disclosure_date", "filing_lag_days", "amount_min", "amount_max", "amount_mid", "source_url",
        "committee_relevant", "performance", "overlap", "conviction", "composite", "bipartisan_overlap",
    }


def test_rest_member_detail_response_shape_unchanged(
    client, make_member, make_trade, make_ticker_metadata, make_portfolio_return
):
    make_member(member_id="M1", full_name="Jane Doe")
    make_ticker_metadata("AAPL", sector="Technology")
    make_trade("M1", ticker="AAPL", amount_mid=5000)
    make_portfolio_return("M1", realized_pnl=100.0)

    resp = client.get("/members/M1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["trade_count"] == 1
    assert body["sector_breakdown"] == {"Technology": 5000.0}
    assert body["realized_pnl"] == 100.0


def test_rest_member_not_found_unchanged(client):
    resp = client.get("/members/does-not-exist")
    assert resp.status_code == 404
