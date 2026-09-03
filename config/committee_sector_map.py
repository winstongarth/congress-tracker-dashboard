"""Committee name -> relevant sector/industry keywords.

Deliberately a small, hand-maintained mapping table, not an external data
source -- committee jurisdiction is fuzzy enough (e.g. Ways and Means
touches nearly everything via tax policy) that some committees are
intentionally left unmapped rather than guessed at.

Matching is substring-based and case-insensitive in both directions: a
committee name keyword found in the member's committee list, paired against
a sector/industry keyword found in the ticker's `ticker_metadata.sector` or
`.industry` (yfinance's GICS-ish taxonomy).
"""

COMMITTEE_SECTOR_MAP: dict[str, list[str]] = {
    "armed services": ["aerospace", "defense", "industrials"],
    "energy and commerce": ["energy", "utilities", "oil", "gas"],
    "energy and natural resources": ["energy", "utilities", "oil", "gas", "mining"],
    "natural resources": ["oil", "gas", "mining", "energy"],
    "financial services": ["financ", "bank", "insurance", "asset management", "capital markets"],
    "banking, housing": ["financ", "bank", "insurance", "real estate", "reit"],
    "agriculture": ["agricultur", "farm", "food"],
    "transportation and infrastructure": ["airlines", "railroads", "trucking", "infrastructure", "construction"],
    "commerce, science, and transportation": ["technology", "semiconductor", "software", "airlines", "telecom"],
    "science, space, and technology": ["technology", "semiconductor", "software", "aerospace"],
    "homeland security": ["aerospace", "defense", "security"],
    "intelligence": ["aerospace", "defense", "communication"],
    "health, education, labor": ["healthcare", "pharmaceutical", "biotechnology", "drug manufacturers", "medical"],
    "veterans": ["healthcare", "medical"],
}


def relevant_sector_keywords(committee_names: list[str]) -> set[str]:
    keywords: set[str] = set()
    for committee in committee_names:
        committee_lower = committee.lower()
        for committee_keyword, sector_keywords in COMMITTEE_SECTOR_MAP.items():
            if committee_keyword in committee_lower:
                keywords.update(sector_keywords)
    return keywords
