"""Thin client for the official congress.gov API (api.congress.gov).

Used for member bio data and committee name lookups. Requires a free key
from https://api.congress.gov/sign-up/, set as CONGRESS_API_KEY in .env.
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Iterator

from app.cache.http_cache import CachedFetcher
from config.settings import settings

BASE_URL = "https://api.congress.gov/v3"


def current_congress_number(today: dt.date | None = None) -> int:
    """119th Congress runs Jan 2025-Jan 2027, etc. Congresses start in odd years."""
    today = today or dt.date.today()
    start_year = today.year if today.year % 2 == 1 else today.year - 1
    return (start_year - 1789) // 2 + 1


class CongressApiClient:
    def __init__(self, fetcher: CachedFetcher | None = None) -> None:
        if not settings.congress_api_key:
            raise RuntimeError(
                "CONGRESS_API_KEY is not set. Get a free key at "
                "https://api.congress.gov/sign-up/ and add it to .env"
            )
        self._owns_fetcher = fetcher is None
        self.fetcher = fetcher or CachedFetcher("congress_api", check_robots=False)

    def close(self) -> None:
        if self._owns_fetcher:
            self.fetcher.close()

    def _paginate(self, path: str, params: dict, *, items_key: str) -> Iterator[dict]:
        # Deliberately NOT following payload["pagination"]["next"]: it comes back
        # using the API's own default limit (20) instead of the limit actually
        # requested, so trusting it re-walks the same records in smaller steps
        # forever. Self-managing offset/limit avoids that entirely.
        page_size = params.get("limit", 250)
        url = f"{BASE_URL}{path}"
        page = 0
        MAX_PAGES = 50  # ~12,500 records at limit=250 -- far more than any /member or /committee list
        while True:
            if page >= MAX_PAGES:
                raise RuntimeError(
                    f"_paginate({path}) exceeded {MAX_PAGES} pages -- aborting "
                    f"rather than risk an unbounded loop."
                )
            request_params = {**params, "offset": page * page_size, "api_key": settings.congress_api_key, "format": "json"}
            cache_key = f"{url}?{sorted(request_params.items())}"
            raw = self.fetcher.get(url, cache_key=cache_key, params=request_params)
            payload = json.loads(raw)
            items = payload.get(items_key, [])
            print(f"  ...{path} page {page}: {len(items)} {items_key}")
            yield from items
            if len(items) < page_size:
                break
            page += 1

    def iter_current_members(self) -> Iterator[dict]:
        yield from self._paginate(
            "/member", {"currentMember": "true", "limit": 250}, items_key="members"
        )

    def iter_committees(self, chamber: str, congress: int | None = None) -> Iterator[dict]:
        congress = congress or current_congress_number()
        yield from self._paginate(
            f"/committee/{congress}/{chamber}", {"limit": 250}, items_key="committees"
        )
