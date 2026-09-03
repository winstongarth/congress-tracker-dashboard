"""Top 30 member selection strategies. Named and swappable via
settings.selection_method, not a hardcoded list.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Member
from config.settings import settings
from config.tracked_members import MANUAL_TRACKED_MEMBERS


def resolve_manual_list(session: Session) -> list[str]:
    """Resolves config/tracked_members.py entries to member_id (bioguide_id) by
    name + state + chamber, against the already-scraped `members` table.
    Logs (does not raise) on unmatched entries so one bad name doesn't break
    the run -- run the roster scraper first if everything fails to resolve.
    """
    resolved: list[str] = []
    for entry in MANUAL_TRACKED_MEMBERS:
        stmt = select(Member).where(
            Member.full_name == entry["name"],
            Member.state == entry["state"],
            Member.chamber == entry["chamber"],
        )
        member = session.scalars(stmt).first()
        if member is None:
            print(f"WARNING: could not resolve tracked member {entry!r} against roster")
            continue
        resolved.append(member.member_id)
    return resolved


def select_all(session: Session) -> list[str]:
    """Every active member, both chambers -- no filtering at all. Default as
    of the move away from a curated subset; the "Top 30" framing still
    applies if you switch back to "manual" or a ranked method later.
    """
    return list(session.scalars(select(Member.member_id).where(Member.active.is_(True))))


def select_top30(session: Session, method: str | None = None) -> list[str]:
    method = method or settings.selection_method
    if method == "all":
        return select_all(session)
    if method == "manual":
        return resolve_manual_list(session)
    raise NotImplementedError(
        f"selection_method={method!r} needs at least one full trade-scrape cycle "
        "of history before it's meaningful -- not available yet on a fresh "
        "database with no ingested trades."
    )
