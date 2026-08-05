"""Live employee-count lookup via Wikidata. Free, no API key.

Every lookup is a real per-company query against Wikidata's public API
(wbsearchentities to resolve the company to a QID, wbgetclaims for property
P1128 "employees") — nothing here is a static list of companies. Results are
cached locally (data/employee_counts.json) purely so a company already sized
in a prior run isn't queried again; the cache is populated only by live
lookups, never seeded by hand.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from .base import get_with_retry, make_session

CACHE = Path(__file__).resolve().parent.parent.parent / "data" / "employee_counts.json"
SEARCH = "https://www.wikidata.org/w/api.php"

_STOPWORDS = re.compile(
    r"\b(inc|llc|ltd|limited|corp|corporation|co|plc|gmbh|ag|ab|sa|nv|bv|pte|pty|"
    r"holdings?|group|therapeutics?|biotherapeutics?|biosciences?|biotechnology|"
    r"biotech|pharmaceuticals?|pharma|biologics?|biomed)\b\.?",
    re.I,
)


def _load_cache() -> dict[str, Any]:
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def _save_cache(cache: dict[str, Any]) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True), encoding="utf-8")


def _name_matches(candidate_label: str, company: str) -> bool:
    """Guard against Wikidata search's fuzzy matches (e.g. "Pfizer" -> "Pitzer
    College" by alias). Require the core token to actually appear in the label.
    """
    core = _STOPWORDS.sub("", company).strip().lower()
    core = re.sub(r"[^a-z0-9 ]", "", core).strip()
    if not core:
        return False
    label = candidate_label.lower()
    return core in label or label in core


def _best_employee_count(claims: dict[str, Any]) -> int | None:
    entries = claims.get("claims", {}).get("P1128", [])
    if not entries:
        return None
    # Prefer the entry with the latest "point in time" (P585) qualifier; fall
    # back to the first normal-rank statement if none carry a date.
    dated = []
    undated = []
    for entry in entries:
        amount = entry.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("amount")
        if amount is None:
            continue
        try:
            value = int(float(amount))
        except ValueError:
            continue
        time_qual = entry.get("qualifiers", {}).get("P585", [{}])[0]
        when = time_qual.get("datavalue", {}).get("value", {}).get("time", "")
        if when:
            dated.append((when, value))
        else:
            undated.append(value)
    if dated:
        dated.sort(key=lambda t: t[0], reverse=True)
        return dated[0][1]
    if undated:
        return undated[0]
    return None


def lookup_employee_count(session, company: str) -> int | None:
    """Live Wikidata lookup for one company's employee count, or None if not found."""
    r = get_with_retry(
        session, SEARCH,
        params={"action": "wbsearchentities", "search": company, "language": "en",
                "format": "json", "type": "item", "limit": 3},
        timeout=(8, 20),
    )
    if r is None:
        return None
    try:
        results = r.json().get("search", [])
    except ValueError:
        return None

    for candidate in results:
        label = candidate.get("label") or candidate.get("display", {}).get("label", {}).get("value", "")
        if not _name_matches(label, company):
            continue
        qid = candidate["id"]
        r2 = get_with_retry(
            session, SEARCH,
            params={"action": "wbgetclaims", "entity": qid, "property": "P1128", "format": "json"},
            timeout=(8, 20),
        )
        if r2 is None:
            continue
        try:
            claims = r2.json()
        except ValueError:
            continue
        count = _best_employee_count(claims)
        if count is not None:
            return count
    return None


def enrich(companies: list[str]) -> dict[str, int | None]:
    """Look up employee counts for a list of company names, using and updating
    the on-disk cache so repeat runs don't re-query a company already sized.
    """
    cache = _load_cache()
    session = make_session("antibody-prospecting-research/1.0 (contact:research@example.invalid)")
    out: dict[str, int | None] = {}
    dirty = False

    for name in companies:
        key = name.strip().lower()
        if key in cache:
            out[name] = cache[key]
            continue
        count = lookup_employee_count(session, name)
        cache[key] = count
        out[name] = count
        dirty = True
        time.sleep(0.15)

    if dirty:
        _save_cache(cache)
    return out
