"""Manual override list -- only used when selection_method = "manual" in
settings.py. The default is now "all" (every active member, both chambers);
this list is for when you want to scope back down to a curated subset.

Entries are resolved to member_id (bioguide_id) against the `members` table
after each roster scrape, by name + state, rather than hardcoding bioguide
IDs here -- a wrong hardcoded ID would silently corrupt every trade pulled
for that "member" (CLAUDE.md Sec 9). See app/selection/top30.py:resolve_manual_list.
"""

MANUAL_TRACKED_MEMBERS = [
    {"name": "Nancy Pelosi", "state": "CA", "chamber": "house"},
    {"name": "Tommy Tuberville", "state": "AL", "chamber": "senate"},
    {"name": "Marjorie Taylor Greene", "state": "GA", "chamber": "house"},
    {"name": "Josh Gottheimer", "state": "NJ", "chamber": "house"},
    {"name": "Dan Crenshaw", "state": "TX", "chamber": "house"},
    {"name": "Ro Khanna", "state": "CA", "chamber": "house"},
    {"name": "Markwayne Mullin", "state": "OK", "chamber": "senate"},
    {"name": "Michael McCaul", "state": "TX", "chamber": "house"},
    {"name": "Susie Lee", "state": "NV", "chamber": "house"},
    {"name": "Pat Fallon", "state": "TX", "chamber": "house"},
    {"name": "Dan Meuser", "state": "PA", "chamber": "house"},
    {"name": "Diana Harshbarger", "state": "TN", "chamber": "house"},
    {"name": "French Hill", "state": "AR", "chamber": "house"},
    {"name": "Virginia Foxx", "state": "NC", "chamber": "house"},
    {"name": "Earl Blumenauer", "state": "OR", "chamber": "house"},
    {"name": "Mark Green", "state": "TN", "chamber": "house"},
    {"name": "Debbie Wasserman Schultz", "state": "FL", "chamber": "house"},
    {"name": "Kevin Hern", "state": "OK", "chamber": "house"},
    {"name": "Garret Graves", "state": "LA", "chamber": "house"},
    {"name": "Shelley Moore Capito", "state": "WV", "chamber": "senate"},
]
