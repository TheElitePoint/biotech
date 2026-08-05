"""Account-based source adapter for large pharma/biotech. Free, no API key.

The manual is explicit: "Large pharma: Account-based only — target a named
discovery unit and a defined program, not the whole company." A mega-corp
does not publish "we have this exact antibody design bottleneck" in a press
release the way a startup does, so broad discovery search (the other 8
sources) structurally can't surface them — that's not a bug in those sources,
it's a different population that needs a different method: watch a known set
of large companies for hiring/pipeline/leadership signals.

The account list itself is never hardcoded. `discover_accounts()` queries
Wikidata live for real companies classified as pharmaceutical/biotech (by
type or by industry) with a real P1128 employee count in range — a fresh
answer every run, not a stored list. Each discovered account then gets a
handful of company-scoped searches.
"""

from __future__ import annotations

import html
import re
import time
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse

from . import company_size
from .base import get_with_retry, make_item, make_session

SPARQL = "https://query.wikidata.org/sparql"

# Wikidata classes for "is a pharma/biotech company" and "industry = pharmaceutical".
PHARMA_COMPANY_QID = "Q19644607"
BIOTECH_COMPANY_QID = "Q90298876"
PHARMA_INDUSTRY_QID = "Q507443"

ACCOUNT_QUERY_TEMPLATES: list[tuple[str, str]] = [
    ('"{company}" antibody discovery hiring', "hiring"),
    ('"{company}" "bispecific antibody" OR "protein engineering" pipeline', "program"),
    ('"{company}" "Head of Antibody" OR "Head of Protein Engineering" OR "VP Discovery"', "execution"),
    ('"{company}" "development candidate" antibody', "milestone"),
    ('"{company}" "antibody-drug conjugate" OR "ADC" collaboration', "execution"),
    ('"{company}" "protein engineering" hiring OR platform', "hiring"),
    ('"{company}" nanobody OR "VHH" OR "multispecific antibody"', "program"),
    ('"{company}" "antibody discovery platform" OR "antibody engineering" partner', "execution"),
    ('"{company}" "humanized antibody" OR "antibody humanization"', "scientific"),
    ('"{company}" "IND-enabling" OR "candidate nomination" antibody', "milestone"),
]

BAD_TITLE = re.compile(
    r"market size|market report|forecast|webinar|podcast|stock to watch|"
    r"best stocks|investor alert",
    re.I,
)
_QID_LABEL = re.compile(r"^Q\d+$")


def discover_accounts(min_employees: int = 500, max_employees: int | None = None, limit: int = 200) -> list[tuple[str, int]]:
    """Live Wikidata SPARQL query for real pharma/biotech companies in range.
    Returns [(company_name, employees)], deduped, largest first. Nothing here
    is a stored list — a different run at a different time can return a
    different set as Wikidata's data changes.
    """
    cap = f"FILTER(?employees <= {max_employees})" if max_employees else ""
    query = f"""
    SELECT DISTINCT ?companyLabel ?employees WHERE {{
      {{ ?company wdt:P31 wd:{PHARMA_COMPANY_QID} . }}
      UNION {{ ?company wdt:P31 wd:{BIOTECH_COMPANY_QID} . }}
      UNION {{ ?company wdt:P452 wd:{PHARMA_INDUSTRY_QID} . }}
      UNION {{ ?company wdt:P31 ?t . ?t wdt:P279* wd:{PHARMA_INDUSTRY_QID} . }}
      ?company wdt:P1128 ?employees .
      FILTER(?employees >= {min_employees})
      {cap}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    ORDER BY DESC(?employees)
    LIMIT {limit}
    """
    session = make_session("antibody-prospecting-research/1.0 (contact:research@example.invalid)")
    r = get_with_retry(session, SPARQL, params={"query": query, "format": "json"}, timeout=(15, 60))
    if r is None:
        return []
    try:
        rows = r.json().get("results", {}).get("bindings", [])
    except ValueError:
        return []

    best: dict[str, int] = {}
    for row in rows:
        name = row.get("companyLabel", {}).get("value", "")
        if not name or _QID_LABEL.match(name):
            continue  # label service failed to resolve — not a usable name
        try:
            employees = int(float(row.get("employees", {}).get("value", 0)))
        except (TypeError, ValueError):
            continue
        if employees > best.get(name, 0):
            best[name] = employees

    return sorted(best.items(), key=lambda kv: -kv[1])


# Note: no name-length filter here on purpose. An earlier attempt rejected
# short single-word labels to kill "Star"/"Protek" noise, but that also drops
# Genmab, Amgen, Pfizer, Bayer, Sanofi and Ipsen — all legitimate accounts.
# Precision comes instead from (a) phrase-boundary matching above and
# (b) the modality requirement on the large-account floor in orchestrate.py.


def _direct_url(link: str) -> str:
    parsed = urlparse(link)
    target = parse_qs(parsed.query).get("url", [""])[0]
    return target or link


def _bing_search(session, query: str) -> list[dict[str, str]]:
    url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
    r = get_with_retry(session, url, timeout=(10, 25))
    if r is None:
        return []
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        return []
    out = []
    for entry in root.findall("./channel/item"):
        title = html.unescape(entry.findtext("title") or "").strip()
        description = html.unescape(entry.findtext("description") or "").strip()
        link = _direct_url(entry.findtext("link") or "")
        published = (entry.findtext("pubDate") or "").strip()
        if not title or not link or BAD_TITLE.search(title):
            continue
        out.append({"title": title, "description": description, "link": link, "published": published})
    return out


def fetch(days: int = 180, min_employees: int = 500, max_employees: int | None = None, max_accounts: int = 120) -> list[dict[str, Any]]:
    accounts = discover_accounts(min_employees, max_employees, limit=max_accounts * 3)[:max_accounts]
    if not accounts:
        return []

    # These employee counts are already confirmed by the same discovery query
    # that selected these accounts — prime the shared cache so the pipeline's
    # later size-filter step doesn't spend a second Wikidata lookup on them.
    cache = company_size._load_cache()
    for name, employees in accounts:
        cache[name.strip().lower()] = employees
    company_size._save_cache(cache)

    session = make_session("Mozilla/5.0 (compatible; antibody-intent-research/1.1)")
    items: list[dict[str, Any]] = []

    for company, employees in accounts:
        for template, signal_type in ACCOUNT_QUERY_TEMPLATES:
            query = template.format(company=company)
            for hit in _bing_search(session, query):
                blob = f"{hit['title']} {hit['description']}"
                # Match the company as a standalone phrase, not a substring.
                # Plain substring matching resolved an article about "F-star"
                # to an unrelated company called "Star"; the lookarounds below
                # reject a match glued to another word or hyphenated into one.
                if not re.search(
                    rf"(?<![\w-]){re.escape(company)}(?![\w-])", blob, re.I
                ):
                    continue  # article doesn't actually name this account
                items.append(
                    make_item(
                        url=hit["link"],
                        title=hit["title"],
                        content=re.sub(r"<[^>]+>", " ", hit["description"]),
                        published_date=hit["published"],
                        seed_id=f"ACCOUNT-{signal_type.upper()}",
                        query=query,
                        signal_type=signal_type,
                        days=days,
                        known_company=company,
                    )
                )
            time.sleep(0.1)

    return items
