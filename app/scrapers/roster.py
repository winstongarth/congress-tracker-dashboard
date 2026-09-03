"""First stage of the pipeline: member roster + committee assignments. Bio
data comes from api.congress.gov; committees come from clerk.house.gov /
senate.gov directly (see committees.py for why).

Re-run weekly: rosters change rarely, but committee assignments shift
between sessions.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Member
from app.scrapers.committees import (
    fetch_house_committee_assignments,
    fetch_senate_committee_assignments,
)
from app.scrapers.congress_api import CongressApiClient

_STATE_NAME_TO_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI",
    "Wyoming": "WY", "American Samoa": "AS", "District of Columbia": "DC", "Guam": "GU",
    "Northern Mariana Islands": "MP", "Puerto Rico": "PR", "U.S. Virgin Islands": "VI",
}

_PARTY_NAME_TO_CODE = {
    "Democratic": "D",
    "Republican": "R",
    "Independent": "I",
    "Independent Democrat": "I",
    "Libertarian": "I",
}


def _full_name(raw: dict) -> str:
    if raw.get("directOrderName"):
        return raw["directOrderName"]
    name = raw.get("name", "")
    if "," in name:
        last, first = name.split(",", 1)
        return f"{first.strip()} {last.strip()}"
    return name


def _chamber(raw: dict) -> str:
    terms = raw.get("terms", {}).get("item", [])
    if terms and "senate" in terms[-1].get("chamber", "").lower():
        return "senate"
    return "house"


def fetch_roster() -> list[dict]:
    """Returns normalized member dicts, ready to upsert into `members`."""
    client = CongressApiClient()
    try:
        raw_members = list(client.iter_current_members())
    finally:
        client.close()

    house_committees = fetch_house_committee_assignments()
    try:
        senate_committees = fetch_senate_committee_assignments()
    except Exception as exc:  # senate.gov scraper is untested live (see committees.py)
        print(f"WARNING: Senate committee scrape failed ({exc}); senate members will have committees=[]")
        senate_committees = {}

    roster: list[dict] = []
    for raw in raw_members:
        bioguide_id = raw.get("bioguideId")
        if not bioguide_id:
            continue

        chamber = _chamber(raw)
        state_name = raw.get("state", "")
        state_abbr = _STATE_NAME_TO_ABBR.get(state_name, state_name)
        full_name = _full_name(raw)

        if chamber == "house":
            committees = house_committees.get(bioguide_id, [])
            district = str(raw["district"]) if raw.get("district") is not None else None
        else:
            last_name = full_name.split()[-1]
            committees = senate_committees.get((last_name, state_abbr), [])
            district = None

        roster.append(
            {
                "member_id": bioguide_id,
                "full_name": full_name,
                "chamber": chamber,
                "party": _PARTY_NAME_TO_CODE.get(raw.get("partyName", ""), "I"),
                "state": state_abbr,
                "district": district,
                "committees": committees,
                "photo_url": raw.get("depiction", {}).get("imageUrl"),
                "active": True,
            }
        )
    return roster


def upsert_roster(session: Session, roster: list[dict]) -> None:
    existing = {m.member_id: m for m in session.scalars(select(Member))}
    seen_ids = set()

    for entry in roster:
        seen_ids.add(entry["member_id"])
        member = existing.get(entry["member_id"])
        if member is None:
            session.add(Member(**entry))
        else:
            for key, value in entry.items():
                setattr(member, key, value)

    # Members no longer in the current roster are not deleted (history matters
    # for past trades) -- just marked inactive.
    for member_id, member in existing.items():
        if member_id not in seen_ids:
            member.active = False
