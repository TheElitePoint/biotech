"""NIH RePORTER source adapter.

Sweeps SBIR/STTR small-business grant awards (free, no API key — ported from
the old intent_pipeline/reporter.py). Every award is live-queried each run;
nothing here is a stored or hardcoded company list. Emits one Tavily-shaped
item per company whose latest award falls inside the window, with the
recipient name passed through as `_known_company`.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterator

from .base import make_item, make_session, post_with_retry

API = "https://api.reporter.nih.gov/v2/projects/search"

SBIR_CODES = ["R43", "R44", "R41", "R42"]

TEXT_QUERIES = [
    "antibody",
    "monoclonal antibody",
    "bispecific",
    "nanobody",
    "VHH",
    "scFv",
    "multispecific antibody",
    "antibody fragment",
    "protein engineering",
    "antibody discovery",
    "affinity maturation",
    "protein design",
    "therapeutic protein",
    "protein therapeutic",
    "Fc fusion",
    "immunocytokine",
    "cytokine engineering",
    "de novo protein",
]

EXCLUDE_NAME = re.compile(
    r"\b(university|universit|college|school of|institut|hospital|clinic|"
    r"health system|foundation|trust|regents|board of|research foundation)\b",
    re.I,
)
_LEGAL = re.compile(
    r"[,\s]+(inc|llc|ltd|limited|corp|corporation|co|plc|gmbh|ag|ab|sa|nv|bv|"
    r"pte|pty|holdings?|group)\.?$",
    re.I,
)


@dataclass
class _Award:
    name: str
    latest_date: str = ""
    latest_title: str = ""
    latest_amount: int = 0
    latest_code: str = ""
    project_url: str = ""
    matched_query: str = ""
    is_active: bool = False


def _key(name: str) -> str:
    n = _LEGAL.sub("", name.strip()).strip().lower()
    return re.sub(r"[^a-z0-9]", "", n)


def _search(session, text: str, years: list[int], offset: int) -> dict[str, Any]:
    body = {
        "criteria": {
            "advanced_text_search": {
                "operator": "and",
                "search_field": "projecttitle,abstracttext,terms",
                "search_text": text,
            },
            "activity_codes": SBIR_CODES,
            "fiscal_years": years,
        },
        "offset": offset,
        "limit": 500,
        "sort_field": "award_notice_date",
        "sort_order": "desc",
    }
    r = post_with_retry(session, API, json=body, timeout=(10, 40))
    return r.json() if r is not None else {}


def _sweep(session, text: str, years: list[int]) -> Iterator[dict[str, Any]]:
    offset = 0
    while True:
        data = _search(session, text, years, offset)
        results = data.get("results", [])
        if not results:
            return
        yield from results
        total = data.get("meta", {}).get("total", 0)
        offset += len(results)
        if offset >= total or offset >= 2000:
            return
        time.sleep(0.25)


def fetch(days: int = 365, years: list[int] | None = None, queries: list[str] | None = None) -> list[dict[str, Any]]:
    session = make_session("antibody-prospecting/0.2")
    awards: dict[str, _Award] = {}
    current_year = date.today().year
    years = years or [current_year - 2, current_year - 1, current_year]

    for text in queries or TEXT_QUERIES:
        for row in _sweep(session, text, years):
            org = row.get("organization") or {}
            name = (org.get("org_name") or "").strip()
            if not name or EXCLUDE_NAME.search(name):
                continue
            key = _key(name)
            if not key:
                continue
            award = awards.setdefault(key, _Award(name=name.title()))
            award_date = (row.get("award_notice_date") or "")[:10]
            if row.get("is_active"):
                award.is_active = True
            if award_date > award.latest_date:
                award.latest_date = award_date
                award.latest_title = (row.get("project_title") or "")[:160]
                award.latest_amount = int(row.get("award_amount") or 0)
                award.latest_code = row.get("activity_code") or ""
                award.project_url = row.get("project_detail_url") or ""
                award.matched_query = text

    items: list[dict[str, Any]] = []
    for key, a in awards.items():
        if not a.latest_date:
            continue
        try:
            age = (date.today() - datetime.strptime(a.latest_date, "%Y-%m-%d").date()).days
        except ValueError:
            continue
        if age > days:
            continue
        items.append(
            make_item(
                url=a.project_url,
                title=f"{a.name}: active SBIR/STTR award" if a.is_active else f"{a.name}: SBIR/STTR award",
                content=(
                    f"{a.latest_code} ${a.latest_amount:,} awarded {a.latest_date}: {a.latest_title}"
                ),
                published_date=a.latest_date,
                seed_id=f"REPORTER-{re.sub(r'[^a-z0-9]+', '-', a.matched_query.lower()).strip('-')}",
                query=a.matched_query,
                signal_type="capital",
                days=days,
                known_company=a.name,
            )
        )
    return items
