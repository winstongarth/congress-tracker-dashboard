from __future__ import annotations

import datetime as dt

from tests.conftest import gql

TRADES_QUERY = """
query($search: String, $ticker: String, $chamber: Chamber, $politicianId: ID, $from: Date, $to: Date, $limit: Int, $offset: Int) {
  trades(search: $search, ticker: $ticker, chamber: $chamber, politicianId: $politicianId, from: $from, to: $to, limit: $limit, offset: $offset) {
    totalCount
    results {
      id
      ticker
      sector
      industry
      transactionType
      transactionDate
      amountMid
      performance
      overlap
      politician {
        id
        fullName
      }
    }
  }
}
"""


def _seed(make_member, make_trade, make_ticker_metadata, make_score):
    make_member(member_id="M1", full_name="Jane Doe", chamber="house")
    make_member(member_id="M2", full_name="John Smith", chamber="senate")
    make_ticker_metadata("AAPL", sector="Technology", industry="Consumer Electronics")
    t1 = make_trade("M1", ticker="AAPL", transaction_date=dt.date(2026, 1, 5))
    t2 = make_trade("M2", ticker="MSFT", transaction_date=dt.date(2026, 2, 10))
    make_score("M1", "performance", 42.0, trade_id=t1.trade_id)
    make_score("M1", "overlap", 60.0, trade_id=t1.trade_id)
    return t1, t2


def test_trades_filter_by_ticker(client, make_member, make_trade, make_ticker_metadata, make_score):
    _seed(make_member, make_trade, make_ticker_metadata, make_score)

    data = gql(client, TRADES_QUERY, {"ticker": "aapl"})  # lowercase, service should upper() it
    assert data["trades"]["totalCount"] == 1
    trade = data["trades"]["results"][0]
    assert trade["ticker"] == "AAPL"
    assert trade["sector"] == "Technology"
    assert trade["industry"] == "Consumer Electronics"
    assert trade["performance"] == 42.0
    assert trade["overlap"] == 60.0
    assert trade["politician"]["fullName"] == "Jane Doe"


def test_trades_filter_by_politician_id(client, make_member, make_trade, make_ticker_metadata, make_score):
    _seed(make_member, make_trade, make_ticker_metadata, make_score)

    data = gql(client, TRADES_QUERY, {"politicianId": "M2"})
    assert data["trades"]["totalCount"] == 1
    assert data["trades"]["results"][0]["politician"]["id"] == "M2"
    # MSFT has no ticker_metadata row and no scores -- both should resolve to null, not error.
    assert data["trades"]["results"][0]["sector"] is None
    assert data["trades"]["results"][0]["performance"] is None


def test_trades_filter_by_date_range(client, make_member, make_trade, make_ticker_metadata, make_score):
    _seed(make_member, make_trade, make_ticker_metadata, make_score)

    data = gql(client, TRADES_QUERY, {"from": "2026-02-01", "to": "2026-02-28"})
    assert data["trades"]["totalCount"] == 1
    assert data["trades"]["results"][0]["ticker"] == "MSFT"


def test_trades_search_matches_politician_name_ticker_or_asset_name(
    client, make_member, make_trade, make_ticker_metadata, make_score
):
    _seed(make_member, make_trade, make_ticker_metadata, make_score)

    by_name = gql(client, TRADES_QUERY, {"search": "jane"})
    assert [t["ticker"] for t in by_name["trades"]["results"]] == ["AAPL"]

    by_ticker = gql(client, TRADES_QUERY, {"search": "msft"})
    assert [t["ticker"] for t in by_ticker["trades"]["results"]] == ["MSFT"]

    by_nothing = gql(client, TRADES_QUERY, {"search": "no-such-match"})
    assert by_nothing["trades"]["totalCount"] == 0


def test_trades_filter_by_chamber(client, make_member, make_trade, make_ticker_metadata, make_score):
    _seed(make_member, make_trade, make_ticker_metadata, make_score)

    house_only = gql(client, TRADES_QUERY, {"chamber": "HOUSE"})
    assert [t["ticker"] for t in house_only["trades"]["results"]] == ["AAPL"]

    senate_only = gql(client, TRADES_QUERY, {"chamber": "SENATE"})
    assert [t["ticker"] for t in senate_only["trades"]["results"]] == ["MSFT"]


def test_trades_pagination(client, make_member, make_trade):
    make_member(member_id="M1")
    for day in range(1, 6):
        make_trade("M1", ticker="AAPL", transaction_date=dt.date(2026, 1, day))

    data = gql(client, TRADES_QUERY, {"limit": 2, "offset": 1})
    assert data["trades"]["totalCount"] == 5
    assert len(data["trades"]["results"]) == 2
    # default sort is transaction_date desc, so offset 1 skips Jan 5th.
    assert data["trades"]["results"][0]["transactionDate"] == "2026-01-04"
