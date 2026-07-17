"""7.5 Committee relevance flag (per trade).

Cross-references the member's committees against the ticker's sector/industry
via config/committee_sector_map.py. Qualitative badge/filter, not part of the
numeric composite by design (CLAUDE.md Sec 7.5) -- surfaced as a boolean on
the trade itself (Trade.committee_relevant) for direct dashboard filtering.
"""

from __future__ import annotations

from app.db.models import Member, Trade, TickerMetadata
from config.committee_sector_map import relevant_sector_keywords


def compute_committee_relevance(
    trades: list[Trade],
    members_by_id: dict[str, Member],
    ticker_metadata: dict[str, TickerMetadata],
) -> dict[int, bool]:
    flags: dict[int, bool] = {}
    for t in trades:
        member = members_by_id.get(t.member_id)
        if member is None or not member.committees or not t.ticker:
            flags[t.trade_id] = False
            continue
        keywords = relevant_sector_keywords(member.committees)
        if not keywords:
            flags[t.trade_id] = False
            continue
        meta = ticker_metadata.get(t.ticker)
        haystack = f"{(meta.sector or '')} {(meta.industry or '')}".lower() if meta else ""
        flags[t.trade_id] = any(kw in haystack for kw in keywords)
    return flags
