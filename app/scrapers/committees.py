"""Committee-membership resolution.

api.congress.gov has no committee-roster endpoint (confirmed against its own
docs: /member and /committee never return who currently sits on a committee).
So this hits clerk.house.gov and senate.gov directly, per CLAUDE.md Sec 2.

House: clerk.house.gov/xml/lists/MemberData.xml carries bioguideID plus
committee/subcommittee codes for every member in one file. Codes are resolved
to names via api.congress.gov's committee list (systemCode = "hs" + code,
lowercased -- e.g. comcode "AG00" -> systemCode "hsag00").

Senate: senate.gov publishes per-committee membership as XML, discovered from
an index page listing each committee's thomas_id. NOTE: this sandbox's network
gets a 403 from senate.gov's Akamai bot protection on every request (even with
browser-like headers) -- this function is written from the documented official
approach (the same one
github.com/unitedstates/congress-legislators/scripts/committee_membership.py
uses) but has NOT been live-tested here. Verify it against the real site on
your own machine before trusting its output.
"""

from __future__ import annotations

import re
from collections import defaultdict
from xml.etree import ElementTree as ET

from app.cache.http_cache import CachedFetcher
from app.scrapers.congress_api import CongressApiClient

HOUSE_MEMBERDATA_URL = "https://clerk.house.gov/xml/lists/MemberData.xml"
SENATE_INDEX_URL = (
    "https://www.senate.gov/pagelayout/committees/b_three_sections_with_teasers/membership.htm"
)
SENATE_COMMITTEE_XML_TMPL = (
    "https://www.senate.gov/general/committee_membership/committee_memberships_{thomas_id}.xml"
)

# Hardcoded last-name normalization quirk the official source itself special-cases
# (clerk/senate XML feeds are plain ASCII; accented official names are not).
_SENATE_NAME_FIXES = {
    ("NM", "Lujan"): "Luján",
}


def _committee_name_map(chamber: str) -> dict[str, str]:
    """systemCode -> committee name, via api.congress.gov."""
    client = CongressApiClient()
    try:
        return {c["systemCode"]: c["name"] for c in client.iter_committees(chamber)}
    finally:
        client.close()


def fetch_house_committee_assignments() -> dict[str, list[str]]:
    """bioguide_id -> list of committee/subcommittee names, from clerk.house.gov."""
    with CachedFetcher("house_committees") as fetcher:
        raw = fetcher.get(HOUSE_MEMBERDATA_URL, cache_key="house_memberdata_xml")

    name_map = _committee_name_map("house")
    root = ET.fromstring(raw)

    assignments: dict[str, list[str]] = defaultdict(list)
    for member_el in root.findall(".//member"):
        bioguide_el = member_el.find("./member-info/bioguideID")
        if bioguide_el is None or not bioguide_el.text:
            continue
        bioguide_id = bioguide_el.text.strip()

        for code_el in member_el.findall("./committee-assignments/committee"):
            code = code_el.get("comcode", "")
            assignments[bioguide_id].append(name_map.get(f"hs{code.lower()}", code))
        for code_el in member_el.findall("./committee-assignments/subcommittee"):
            code = code_el.get("subcomcode", "")
            assignments[bioguide_id].append(name_map.get(f"hs{code.lower()}", code))

    return dict(assignments)


def fetch_senate_committee_assignments() -> dict[tuple[str, str], list[str]]:
    """(last_name, state) -> list of committee names, from senate.gov.

    Keyed by (last_name, state) rather than bioguide_id because the
    per-committee XML this scrapes does not carry bioguide IDs -- the caller
    must match against the members table the same way the official
    congress-legislators scraper does.
    """
    with CachedFetcher("senate_committees") as fetcher:
        index_html = fetcher.get(
            SENATE_INDEX_URL, cache_key="senate_membership_index"
        ).decode("utf-8", errors="replace")

        thomas_ids = re.findall(
            r'value="/general/committee_membership/committee_memberships_(.{4})\.htm">(.*?)</option>',
            index_html,
        )

        assignments: dict[tuple[str, str], list[str]] = defaultdict(list)
        for thomas_id, committee_name in thomas_ids:
            url = SENATE_COMMITTEE_XML_TMPL.format(thomas_id=thomas_id)
            raw = fetcher.get(url, cache_key=f"senate_committee_{thomas_id}")
            root = ET.fromstring(raw)
            for member_el in root.findall(".//member"):
                last = member_el.findtext("name/last", default="").strip()
                state = member_el.findtext("state", default="").strip()
                if not last or not state:
                    continue
                last = _SENATE_NAME_FIXES.get((state, last), last)
                assignments[(last, state)].append(committee_name.strip())

    return dict(assignments)
