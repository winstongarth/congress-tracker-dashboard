from __future__ import annotations

import datetime as dt

from sqlalchemy import event

from tests.conftest import gql

N_PLUS_ONE_QUERY = """
query {
  politicians(limit: 10) {
    results {
      id
      trades(limit: 10) {
        results {
          ticker
          sector
          performance
        }
      }
    }
  }
}
"""


def test_dataloaders_prevent_n_plus_one(client, engine, make_member, make_trade, make_ticker_metadata, make_score):
    tickers = ["AAPL", "MSFT", "GOOG"]
    for ticker in tickers:
        make_ticker_metadata(ticker, sector=f"{ticker}-sector")

    for i in range(4):
        member_id = f"M{i}"
        make_member(member_id=member_id, full_name=member_id)
        for j in range(3):
            t = make_trade(member_id, ticker=tickers[j % len(tickers)], transaction_date=dt.date(2026, 1, j + 1))
            make_score(member_id, "performance", 50.0, trade_id=t.trade_id)

    query_count = 0

    def count_queries(*args, **kwargs):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "before_cursor_execute", count_queries)
    try:
        data = gql(client, N_PLUS_ONE_QUERY)
    finally:
        event.remove(engine, "before_cursor_execute", count_queries)

    # Sanity: the data is actually there -- 4 politicians x 3 trades each.
    assert len(data["politicians"]["results"]) == 4
    for politician in data["politicians"]["results"]:
        assert len(politician["trades"]["results"]) == 3

    # Without DataLoader batching this shape of query would issue:
    #   2 (politicians: count + rows)
    #   + 4 (one trades-by-member query per politician, instead of 1 batched IN(...))
    #   + 12 (one ticker_metadata query per trade, instead of 1 batched IN(...))
    #   + 12 (one scores query per trade, instead of 1 batched IN(...))
    #   = 30 queries, scaling linearly with politician/trade count.
    # With batching it stays at a small constant regardless of how many
    # politicians/trades are in the result set.
    assert query_count <= 10, f"expected DataLoader-batched queries, got {query_count}"
