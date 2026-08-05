"""Crossref source adapter. Free, no API key (the "polite pool" just wants a
mailto param, which is what's set below — not a credential).

Supplements Europe PMC with broader journal/preprint coverage and cleaner
citation metadata. Same affiliation-based company resolution as the other
literature sources.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from ..suppression import company_root
from .base import get_with_retry, make_item, make_session
from .europepmc import DEVELOPMENT_ACTIVITY, MODALITY, NOISE, _company_from_affiliation

API = "https://api.crossref.org/works"

TERMS = [
    "bispecific antibody engineering",
    "antibody affinity maturation therapeutic",
    "antibody humanization preclinical",
    "protein engineering therapeutic antibody",
    "nanobody VHH therapeutic discovery",
]


def _published(item: dict[str, Any]) -> str:
    for field in ("published-print", "published-online", "published", "issued"):
        parts = (item.get(field) or {}).get("date-parts") or []
        if parts and parts[0]:
            p = parts[0] + [1, 1]
            return f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}"
    return ""


def _affiliations(item: dict[str, Any]) -> list[str]:
    found = []
    for author in item.get("author", []) or []:
        for aff in author.get("affiliation", []) or []:
            name = (aff.get("name") or "").strip()
            if name:
                found.append(name)
    return found


def fetch(days: int = 365, terms: list[str] | None = None) -> list[dict[str, Any]]:
    session = make_session("antibody-intent-research/1.1 (mailto:research@example.invalid)")
    since = (date.today() - timedelta(days=days)).isoformat()

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for term in terms or TERMS:
        params = {
            "query.bibliographic": term,
            "filter": f"from-pub-date:{since},type:journal-article",
            "rows": 100,
            "mailto": "research@example.invalid",
        }
        r = get_with_retry(session, API, params=params, timeout=(10, 40))
        if r is None:
            continue
        try:
            works = r.json().get("message", {}).get("items", [])
        except ValueError:
            continue
        for work in works:
            titles = work.get("title") or []
            title = (titles[0] if titles else "").strip()
            if not title or NOISE.search(title) or not MODALITY.search(title):
                continue
            if not DEVELOPMENT_ACTIVITY.search(title):
                continue
            doi = work.get("DOI", "")
            url = f"https://doi.org/{doi}" if doi else (work.get("URL") or "")
            if not url:
                continue
            published = _published(work)
            for affiliation in _affiliations(work):
                company = _company_from_affiliation(affiliation)
                if not company:
                    continue
                key = company_root(company)
                dedupe_key = f"{key}|{doi}"
                if not key or dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                items.append(
                    make_item(
                        url=url,
                        title=title,
                        content=f"{work.get('container-title', [''])[0] if work.get('container-title') else ''} | affiliation: {affiliation[:300]}",
                        published_date=published,
                        seed_id=f"CROSSREF-{re.sub(r'[^a-z0-9]+', '-', term.lower()).strip('-')}",
                        query=term,
                        signal_type="scientific",
                        days=days,
                        known_company=company,
                    )
                )
                break
    return items
