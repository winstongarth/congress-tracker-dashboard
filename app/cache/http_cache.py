"""Shared fetch layer enforcing CLAUDE.md's scraping etiquette (Sec 2):
cache every fetched page/PDF by a stable key, rate-limit, identify the
client, and respect robots.txt where applicable.
"""

from __future__ import annotations

import hashlib
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import httpx

from config.settings import settings


class RobotsDisallowed(Exception):
    pass


class CachedFetcher:
    def __init__(
        self,
        cache_subdir: str,
        *,
        user_agent: str | None = None,
        delay_seconds: float | None = None,
        check_robots: bool = True,
    ) -> None:
        self.cache_dir = Path(settings.cache_dir) / cache_subdir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent or settings.user_agent
        self.delay_seconds = (
            delay_seconds if delay_seconds is not None else settings.request_delay_seconds
        )
        self.check_robots = check_robots
        self._robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._last_request_at = 0.0
        self.client = httpx.Client(
            headers={"User-Agent": self.user_agent},
            timeout=30.0,
            follow_redirects=True,
        )

    def __enter__(self) -> "CachedFetcher":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self.client.close()

    def _cache_path(self, cache_key: str) -> Path:
        digest = hashlib.sha256(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{digest}.bin"

    def _wait_for_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)

    def _assert_allowed(self, url: str) -> None:
        if not self.check_robots:
            return
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._robots_cache.get(origin)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{origin}/robots.txt")
            try:
                rp.read()
            except OSError:
                rp = None  # no robots.txt reachable: treat as unrestricted
            self._robots_cache[origin] = rp
        if rp is not None and not rp.can_fetch(self.user_agent, url):
            raise RobotsDisallowed(f"robots.txt disallows fetching {url}")

    def get(self, url: str, *, cache_key: str | None = None, params: dict | None = None) -> bytes:
        """GET with on-disk caching. Reads from cache if present; never re-fetches
        a previously-fetched filing/page."""
        key = cache_key or url
        path = self._cache_path(key)
        if path.exists():
            return path.read_bytes()

        self._assert_allowed(url)
        self._wait_for_rate_limit()
        resp = self.client.get(url, params=params)
        resp.raise_for_status()
        self._last_request_at = time.monotonic()

        path.write_bytes(resp.content)
        return resp.content

    def post(self, url: str, *, data: dict | None = None, headers: dict | None = None) -> httpx.Response:
        """POST is not cached: used for session/agreement-acceptance steps, which are
        not idempotent content fetches."""
        self._assert_allowed(url)
        self._wait_for_rate_limit()
        resp = self.client.post(url, data=data, headers=headers)
        resp.raise_for_status()
        self._last_request_at = time.monotonic()
        return resp
