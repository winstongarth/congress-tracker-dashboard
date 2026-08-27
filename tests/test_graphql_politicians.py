from __future__ import annotations

import datetime as dt

from tests.conftest import gql

POLITICIANS_QUERY = """
query($search: String, $chamber: Chamber, $limit: Int, $offset: Int) {
  politicians(search: $search, chamber: $chamber, limit: $limit, offset: $offset) {
    totalCount
    results {
      id
      fullName
      chamber
      party
      tradeCount
    }
  }
}
"""

POLITICIAN_DETAIL_QUERY = """
query($id: ID!) {
  politician(id: $id) {
    id
    fullName
    performance
    portfolioReturn {
      realizedPnl
      unrealizedPnlPct
    }
    sectorBreakdown {
      sector
      amountMid
    }
    trades(limit: 10) {
      totalCount
      results {
        ticker
        transactionType
        amountMid
      }
    }
  }
}
"""


def test_politicians_search_and_chamber_filter(client, make_member):
    make_member(member_id="M1", full_name="Jane Doe", chamber="house")
    make_member(member_id="M2", full_name="John Smith", chamber="senate")
    make_member(member_id="M3", full_name="Jane Appleseed", chamber="senate")

    data = gql(client, POLITICIANS_QUERY, {"search": "Jane"})
    names = {p["fullName"] for p in data["politicians"]["results"]}
    assert names == {"Jane Doe", "Jane Appleseed"}
    assert data["politicians"]["totalCount"] == 2

    data = gql(client, POLITICIANS_QUERY, {"chamber": "SENATE"})
    names = {p["fullName"] for p in data["politicians"]["results"]}
    assert names == {"John Smith", "Jane Appleseed"}


def test_politicians_pagination(client, make_member):
    for i in range(5):
        make_member(member_id=f"M{i}", full_name=f"Member {i}")

    data = gql(client, POLITICIANS_QUERY, {"limit": 2, "offset": 2})
    assert data["politicians"]["totalCount"] == 5
    assert len(data["politicians"]["results"]) == 2


def test_politician_detail_with_nested_trades_and_performance(
    client, make_member, make_trade, make_score, make_ticker_metadata, make_portfolio_return
):
    make_member(member_id="M1", full_name="Jane Doe")
    make_ticker_metadata("AAPL", sector="Technology")
    t1 = make_trade("M1", ticker="AAPL", transaction_type="buy", transaction_date=dt.date(2026, 1, 1), amount_mid=8000)
    make_score("M1", "performance", 77.0, trade_id=t1.trade_id)
    make_score("M1", "performance", 90.0, trade_id=None)  # member-level rollup
    make_portfolio_return("M1", realized_pnl=250.0, unrealized_pnl_pct=12.5)

    data = gql(client, POLITICIAN_DETAIL_QUERY, {"id": "M1"})
    politician = data["politician"]
    assert politician["fullName"] == "Jane Doe"
    assert politician["performance"] == 90.0  # rollup, not the per-trade value
    assert politician["portfolioReturn"]["realizedPnl"] == 250.0
    assert politician["portfolioReturn"]["unrealizedPnlPct"] == 12.5
    assert politician["sectorBreakdown"] == [{"sector": "Technology", "amountMid": 8000.0}]

    trades = politician["trades"]
    assert trades["totalCount"] == 1
    assert trades["results"][0]["ticker"] == "AAPL"
    assert trades["results"][0]["transactionType"] == "BUY"


def test_politician_not_found_returns_null(client):
    data = gql(client, POLITICIAN_DETAIL_QUERY, {"id": "does-not-exist"})
    assert data["politician"] is None
