"""SEC EDGAR full-text search source adapter. Free, no API key.

SEC requires a descriptive User-Agent with contact info for fair-access
compliance (not a real secret, just their access policy) — set here directly
rather than pulled from any credential store.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from .base import fetch_snippet, get_with_retry, make_item, make_session

SEARCH = "https://efts.sec.gov/LATEST/search-index"

QUERIES: list[tuple[str, str]] = [
    ('"bispecific antibody"', "program"),
    ('"monoclonal antibody"', "program"),
    ('"multispecific antibody"', "program"),
    ('"antibody-drug conjugate"', "program"),
    ('"development candidate"', "milestone"),
    ('"lead optimization"', "program"),
    ('"antibody discovery"', "program"),
]

_TRAILING_PAREN = re.compile(r"\s*\([^()]*\)\s*$")


def _company_name(display_name: str) -> str:
    """Strip the trailing "(CIK ...)" or "(TICKER)" annotation EDGAR appends."""
    name = display_name
    previous = None
    while name != previous:
        previous = name
        name = _TRAILING_PAREN.sub("", name).strip()
    return name or display_name.strip()


def fetch(days: int = 365, queries: list[tuple[str, str]] | None = None, max_snippet_fetches: int = 120) -> list[dict[str, Any]]:
    session = make_session("antibody-prospecting-research contact:research@example.invalid")
    startdt = (date.today() - timedelta(days=days)).isoformat()
    enddt = date.today().isoformat()

    items: list[dict[str, Any]] = []
    for query, signal_type in queries or QUERIES:
        params = {
            "q": query,
            "dateRange": "custom",
            "startdt": startdt,
            "enddt": enddt,
            "forms": "8-K,S-1,10-K,10-Q",
        }
        r = get_with_retry(session, SEARCH, params=params, timeout=(10, 30))
        if r is None:
            continue
        try:
            data = r.json()
        except ValueError:
            continue
        for hit in (data.get("hits", {}) or {}).get("hits", []) or []:
            src = hit.get("_source", {}) or {}
            names = src.get("display_names") or []
            ciks = src.get("ciks") or []
            if not names:
                continue
            company = _company_name(names[0])
            cik = ciks[0] if ciks else ""
            if not company:
                continue
            file_date = src.get("file_date", "")
            form_type = src.get("root_forms", [""])[0] if src.get("root_forms") else src.get("file_type", "")

            doc_id = hit.get("_id", "")
            accession, _, filename = doc_id.partition(":")
            accession_nodash = accession.replace("-", "")
            url = ""
            if cik and accession_nodash and filename:
                url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_nodash}/{filename}"
            elif cik:
                url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"

            items.append(
                make_item(
                    url=url,
                    title=f"{company}: {form_type} filing matching {query}",
                    content=f"SEC {form_type} filing ({file_date}) mentions: {query}",
                    published_date=file_date,
                    seed_id=f"SEC-{re.sub(r'[^a-z0-9]+', '-', query.lower()).strip('-')}",
                    query=query,
                    signal_type=signal_type,
                    days=days,
                    known_company=company,
                )
            )

    # EDGAR's search API returns metadata only, no excerpt — fetch the real filing
    # text for the most recent hits (capped) so scoring has genuine evidence to
    # read instead of just a restated query. Older/lower-priority hits keep the
    # synthetic content rather than spending a fetch on them.
    items.sort(key=lambda it: it.get("published_date") or "", reverse=True)
    for item in items[:max_snippet_fetches]:
        if not item["url"].startswith("https://www.sec.gov/Archives/"):
            continue
        phrase = item["_query"].strip('"')
        snippet = fetch_snippet(session, item["url"], phrase)
        if snippet:
            item["content"] = snippet
            item["raw_content"] = snippet

    return items
