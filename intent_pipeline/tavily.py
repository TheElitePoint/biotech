"""Tavily search/extract client.

Only the two endpoints the pipeline needs, with retry and a small on-disk cache
so re-runs during query tuning do not burn credits.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

from .config import BLOCKED_DOMAINS, NEGATIVE_TERMS, Seed

API = "https://api.tavily.com"
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "tavily"


class TavilyError(RuntimeError):
    pass


def load_dotenv() -> None:
    """Read .env into the environment. Safe to call repeatedly.

    Lives here rather than in a single entry point so every consumer of the client
    picks up the key, however the pipeline was invoked.
    """
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


class Tavily:
    def __init__(self, api_key: str | None = None, use_cache: bool = True):
        load_dotenv()
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY", "")
        if not self.api_key:
            raise TavilyError(
                "TAVILY_API_KEY is not set. Put it in .env or the environment."
            )
        self.use_cache = use_cache
        self.session = requests.Session()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # -- internals ---------------------------------------------------------

    def _cache_path(self, endpoint: str, payload: dict[str, Any]) -> Path:
        key = hashlib.sha256(
            (endpoint + json.dumps(payload, sort_keys=True)).encode()
        ).hexdigest()[:32]
        return CACHE_DIR / f"{endpoint}-{key}.json"

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        cache = self._cache_path(endpoint, payload)
        if self.use_cache and cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))

        body = dict(payload, api_key=self.api_key)
        last_err: Exception | None = None
        # (connect, read) timeout. A short read timeout means a hung endpoint fails in
        # ~25s rather than stalling the whole sweep, as happened on the cached run.
        for attempt in range(3):
            try:
                r = self.session.post(f"{API}/{endpoint}", json=body, timeout=(10, 25))
                if r.status_code == 429:
                    time.sleep(2 ** attempt * 2)
                    continue
                r.raise_for_status()
                data = r.json()
                if self.use_cache:
                    cache.write_text(json.dumps(data), encoding="utf-8")
                return data
            except Exception as exc:  # noqa: BLE001 - retried below
                last_err = exc
                time.sleep(1.5 * (attempt + 1))
        raise TavilyError(f"{endpoint} failed after retries: {last_err}")

    # -- public ------------------------------------------------------------

    def search(self, seed: Seed) -> list[dict[str, Any]]:
        """Run one seed query and return raw Tavily results with seed metadata."""
        payload: dict[str, Any] = {
            "query": f"{seed.query} {NEGATIVE_TERMS}".strip(),
            "search_depth": seed.depth,
            "max_results": seed.max_results,
            "include_raw_content": seed.depth == "advanced",
            "include_answer": False,
            "days": seed.days,
            "topic": "news" if seed.signal_type in ("capital", "milestone") else "general",
        }
        if seed.include_domains:
            payload["include_domains"] = seed.include_domains
        exclude = sorted(set(seed.exclude_domains) | BLOCKED_DOMAINS)
        payload["exclude_domains"] = exclude

        data = self._post("search", payload)
        out = []
        for item in data.get("results", []):
            item["_seed_id"] = seed.seed_id
            item["_query"] = seed.query
            item["_signal_type"] = seed.signal_type
            item["_date_window_days"] = seed.days
            out.append(item)
        return out

    def extract(self, urls: list[str]) -> dict[str, str]:
        """Fetch page text for up to 20 URLs at a time. Returns url -> content."""
        content: dict[str, str] = {}
        for i in range(0, len(urls), 20):
            batch = urls[i : i + 20]
            try:
                data = self._post("extract", {"urls": batch})
            except TavilyError:
                continue
            for res in data.get("results", []):
                url = res.get("url")
                if url:
                    content[url] = res.get("raw_content") or ""
        return content
