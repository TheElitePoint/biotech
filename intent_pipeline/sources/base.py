"""Shared helpers for source adapters: HTTP session with retry, and the two
item shapes every adapter emits.

Tavily-shaped item (consumed by signals.normalize -> resolve_company):
    {url, title, content, raw_content, published_date,
     _seed_id, _query, _signal_type, _date_window_days}

Registry-shaped item: the same dict, plus `_known_company` / `_known_domain`
when the source already knows the exact company (ClinicalTrials.gov and NIH
RePORTER resolve a canonical org name themselves — resolve_company() would
only be guessing worse). `attach_known_company()` below overwrites the
guessed fields on the Signal after normalize() runs, so signals.py itself
never needs to change.
"""

from __future__ import annotations

import re
import time
from typing import Any

import requests


def make_session(user_agent: str) -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = user_agent
    return session


def get_with_retry(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: tuple[int, int] = (10, 30),
    attempts: int = 3,
) -> requests.Response | None:
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            r = session.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as exc:  # noqa: BLE001 - retried below
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    return None


def post_with_retry(
    session: requests.Session,
    url: str,
    *,
    json: dict[str, Any] | None = None,
    timeout: tuple[int, int] = (10, 30),
    attempts: int = 3,
) -> requests.Response | None:
    for attempt in range(attempts):
        try:
            r = session.post(url, json=json, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception:  # noqa: BLE001 - retried below
            time.sleep(1.5 * (attempt + 1))
    return None


def make_item(
    *,
    url: str,
    title: str,
    content: str,
    published_date: str = "",
    seed_id: str,
    query: str,
    signal_type: str,
    days: int,
    raw_content: str = "",
    known_company: str = "",
    known_domain: str = "",
) -> dict[str, Any]:
    """Build one Tavily-shaped raw item for signals.normalize()."""
    item: dict[str, Any] = {
        "url": url,
        "title": title,
        "content": content,
        "raw_content": raw_content,
        "published_date": published_date,
        "_seed_id": seed_id,
        "_query": query,
        "_signal_type": signal_type,
        "_date_window_days": days,
    }
    if known_company:
        item["_known_company"] = known_company
        item["_known_domain"] = known_domain
    return item


def fetch_snippet(
    session: requests.Session,
    url: str,
    phrase: str = "",
    *,
    window: int = 900,
    timeout: tuple[int, int] = (8, 20),
) -> str:
    """Fetch a page and return real text around `phrase` (or the page start if
    `phrase` isn't found / isn't given). Used to turn a metadata-only search
    hit (SEC EDGAR full-text search returns no excerpt) into one backed by
    actual document text, instead of just restating the query.
    """
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400 or "html" not in r.headers.get("content-type", "").lower():
            return ""
    except requests.RequestException:
        return ""
    text = r.text
    text = re.sub(r"(?is)<(script|style|svg|noscript).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if phrase:
        idx = text.lower().find(phrase.lower())
        if idx == -1:
            return ""
        start = max(0, idx - window // 2)
        return text[start : start + window]
    return text[:window]


def attach_known_company(sig: Any, item: dict[str, Any]) -> None:
    """Overwrite resolve_company()'s guess when the source already knows the owner.

    ClinicalTrials.gov and NIH RePORTER hand back a clean sponsor/recipient name —
    trusting that beats re-deriving it from a synthetic title the way resolve_company()
    would have to.

    Company domain is explicitly reset to whatever the source actually knows
    (usually nothing) rather than left as resolve_company()'s guess. Left alone,
    two articles about the same known company hosted on different domains
    (e.g. two Yahoo Finance syndication paths) can each get a different guessed
    company_domain, which store/build_company_rows uses as the dedupe key — that
    silently split "Bayer" into two separate company rows in testing. Once we
    already know the company, a stale guessed domain is worse than none.
    """
    known = item.get("_known_company")
    if not known:
        return
    sig.company_candidate = known
    sig.company_domain = item.get("_known_domain") or ""
    sig.resolution_note = "resolved directly from source registry (canonical recipient/sponsor name)"
