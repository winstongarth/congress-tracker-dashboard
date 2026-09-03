"""Orchestrates the scoring stage: runs every sub-score against whatever's
currently in `trades`, normalizes each to 0-100 within its own population,
computes the composite, and writes everything to `scores` (trade-level rows)
plus `trades.committee_relevant` (the one flag that lives directly on the
trade row -- see committee_relevance.py for why).

Scores are recomputed wholesale on each run, not incrementally -- the table
is documented as "recomputed on each scoring run, not derived live", so
stale rows for trade_ids no longer scoreable would otherwise accumulate.
"""

from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.db.models import Member, PortfolioReturn, Score, TickerMetadata, Trade
from app.scoring import composite as composite_mod
from app.scoring import overlap as overlap_mod
from app.scoring.committee_relevance import compute_committee_relevance
from app.scoring.conviction import compute_conviction
from app.scoring.normalize import percentile_rank
from app.scoring.performance import compute_performance
from app.scoring.portfolio import compute_portfolio_returns
from app.scoring.price_backfill import backfill_all
from app.scoring.recency import compute_recency_weight


def run_scoring(session: Session) -> dict[str, int]:
    print("Backfilling price history...")
    backfill_results = backfill_all(session)
    session.flush()
    print(f"  ...{sum(backfill_results.values())} new price rows across {len(backfill_results)} tickers")

    trades = list(session.scalars(select(Trade)))
    members_by_id = {m.member_id: m for m in session.scalars(select(Member))}
    member_party = {mid: m.party for mid, m in members_by_id.items()}
    ticker_metadata = {tm.ticker: tm for tm in session.scalars(select(TickerMetadata))}

    print("Computing performance scores...")
    performance_raw = compute_performance(session, trades)
    performance_pct = percentile_rank(performance_raw)

    print("Computing conviction scores...")
    conviction_raw = compute_conviction(trades)
    conviction_pct_by_pair = percentile_rank(
        {f"{mid}|{ticker}": v for (mid, ticker), v in conviction_raw.items()}
    )
    conviction_pct_by_trade = {
        t.trade_id: conviction_pct_by_pair[f"{t.member_id}|{t.ticker}"]
        for t in trades
        if t.ticker and f"{t.member_id}|{t.ticker}" in conviction_pct_by_pair
    }

    print("Computing overlap scores...")
    overlap_raw, bipartisan_flags = overlap_mod.compute_overlap(trades, member_party)
    overlap_pct = percentile_rank(overlap_raw)

    print("Computing recency weights...")
    recency_weight = compute_recency_weight(trades)

    print("Computing committee relevance flags...")
    committee_relevant = compute_committee_relevance(trades, members_by_id, ticker_metadata)

    print("Computing composite scores...")
    composite_scores = composite_mod.compute_composite(performance_pct, overlap_pct, conviction_pct_by_trade, recency_weight)

    trades_by_id = {t.trade_id: t for t in trades}

    # Wholesale recompute: clear old trade-level scores before inserting fresh ones.
    session.execute(delete(Score).where(Score.trade_id.is_not(None)))

    score_rows = []
    for score_type, values in (
        ("performance", performance_pct),
        ("overlap", overlap_pct),
        ("conviction", conviction_pct_by_trade),
        ("composite", composite_scores),
    ):
        for trade_id, value in values.items():
            score_rows.append(
                Score(member_id=trades_by_id[trade_id].member_id, trade_id=trade_id, score_type=score_type, value=value)
            )
    session.add_all(score_rows)

    # Member-level performance rollup: performance also rolls up to per-member.
    session.execute(delete(Score).where(Score.trade_id.is_(None), Score.score_type == "performance"))
    member_trade_perf: dict[str, list[float]] = {}
    for trade_id, value in performance_pct.items():
        member_trade_perf.setdefault(trades_by_id[trade_id].member_id, []).append(value)
    for member_id, values in member_trade_perf.items():
        session.add(Score(member_id=member_id, ticker=None, trade_id=None, score_type="performance", value=sum(values) / len(values)))

    for trade in trades:
        trade.committee_relevant = committee_relevant.get(trade.trade_id, False)
        trade.bipartisan_overlap = bipartisan_flags.get(trade.trade_id, False)

    print("Computing portfolio returns...")
    portfolio_returns = compute_portfolio_returns(session, trades)
    session.execute(delete(PortfolioReturn))
    for member_id, r in portfolio_returns.items():
        session.add(
            PortfolioReturn(
                member_id=member_id,
                realized_pnl=r["realized_pnl"],
                realized_cost_basis=r["realized_cost_basis"],
                realized_pnl_pct=(r["realized_pnl"] / r["realized_cost_basis"] * 100) if r["realized_cost_basis"] else None,
                unrealized_pnl=r["unrealized_pnl"],
                unrealized_cost_basis=r["unrealized_cost_basis"],
                unrealized_pnl_pct=(r["unrealized_pnl"] / r["unrealized_cost_basis"] * 100) if r["unrealized_cost_basis"] else None,
            )
        )

    return {
        "trades_scored": len(performance_pct),
        "members_with_rollup": len(member_trade_perf),
        "committee_relevant_flagged": sum(committee_relevant.values()),
        "bipartisan_overlap_trades": sum(bipartisan_flags.values()),
        "members_with_portfolio_returns": len(portfolio_returns),
    }
