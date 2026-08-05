"""Tier 1A: the company's own website — the brief's primary authority.

Per brief §3, company pipeline / technology / careers / news / publications
pages are "the primary authority for program ownership, modality, stage and
company direction." Everything else in the pipeline reads *about* a company
second-hand; this reads what the company says about itself.

This is the fix for the failure pattern seen across every earlier run: nearly
every candidate failed Gate 2 (stage not visible) and Gate 3 (no bottleneck),
because a third-party news article almost never states a program's stage or a
design problem, while a /pipeline page states stage explicitly and a /careers
page states the bottleneck in the company's own words.

Crawl discipline (small and polite by construction):
  * links are discovered from the homepage nav rather than brute-forced, with a
    short list of conventional paths as fallback;
  * at most `max_pages` pages per company (default 6);
  * a delay between requests and a descriptive User-Agent.
"""

from __future__ import annotations

import html
import re
import time
from typing import Any
from urllib.parse import urljoin, urlparse

from .. import extraction
from . import apify_crawler
from .base import make_item, make_session

UA = "antibody-prospecting-research/1.0 (+contact:research@example.invalid)"

# Page taxonomy -> URL/anchor cues. Order matters: first match wins.
PAGE_TYPES: list[tuple[str, re.Pattern[str]]] = [
    ("pipeline", re.compile(r"pipeline|our[-_ ]?programs?|portfolio|product[-_ ]?candidates", re.I)),
    ("technology", re.compile(r"technolog|platform|our[-_ ]?science|approach|innovation", re.I)),
    ("careers", re.compile(r"careers?|jobs?|join[-_ ]?us|work[-_ ]?with[-_ ]?us|opportunities", re.I)),
    ("publications", re.compile(r"publications?|papers|posters|scientific[-_ ]?resources", re.I)),
    ("company_news", re.compile(r"news|press|media|newsroom|announcements", re.I)),
]

FALLBACK_PATHS: dict[str, list[str]] = {
    "pipeline": ["/pipeline", "/our-pipeline", "/programs", "/our-programs", "/portfolio"],
    "technology": ["/technology", "/platform", "/science", "/our-science", "/approach"],
    "careers": ["/careers", "/careers/", "/jobs", "/join-us"],
    "publications": ["/publications", "/publications/", "/papers"],
    "company_news": ["/news", "/newsroom", "/press-releases", "/media"],
}

# Signal type per page type, for the downstream SOP scoring model.
SIGNAL_TYPE = {
    "pipeline": "program",
    "technology": "program",
    "careers": "hiring",
    "publications": "scientific",
    "company_news": "milestone",
}

_TAG_RE = re.compile(r"(?is)<(script|style|noscript|svg|header|footer|nav).*?>.*?</\1>")
_HREF_RE = re.compile(r"""<a\s[^>]*href=["']([^"'#]+)["'][^>]*>(.*?)</a>""", re.I | re.S)


def _text_of(page_html: str) -> str:
    body = _TAG_RE.sub(" ", page_html)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    body = html.unescape(body)
    return re.sub(r"\s+", " ", body).strip()


def _fetch(session, url: str) -> str | None:
    try:
        r = session.get(url, timeout=(8, 20), allow_redirects=True)
    except Exception:  # noqa: BLE001 - unreachable page is not a pipeline failure
        return None
    if r.status_code >= 400:
        return None
    if "html" not in r.headers.get("content-type", "").lower():
        return None
    return r.text


def discover_pages(session, domain: str, max_pages: int = 6) -> dict[str, str]:
    """Find the company's key pages. Homepage nav first, conventional paths second."""
    base = f"https://{domain}"
    found: dict[str, str] = {}

    home = _fetch(session, base)
    if home:
        for href, anchor in _HREF_RE.findall(home):
            label = re.sub(r"(?s)<[^>]+>", " ", anchor)
            haystack = f"{href} {label}"
            for page_type, pattern in PAGE_TYPES:
                if page_type in found:
                    continue
                if pattern.search(haystack):
                    absolute = urljoin(base, href.strip())
                    # Stay on the company's own site; an off-site careers portal
                    # is handled by the jobs source, not crawled as a company page.
                    if urlparse(absolute).netloc.replace("www.", "").endswith(domain):
                        found[page_type] = absolute
                    break

    for page_type, paths in FALLBACK_PATHS.items():
        if page_type in found or len(found) >= max_pages:
            continue
        for path in paths:
            candidate = base + path
            if _fetch(session, candidate) is not None:
                found[page_type] = candidate
                break
            time.sleep(0.15)

    return dict(list(found.items())[:max_pages])


def fetch_company(
    session, company: str, domain: str, days: int = 180, max_pages: int = 6
) -> list[dict[str, Any]]:
    """Crawl one company's own pages and emit one item per page with evidence."""
    items: list[dict[str, Any]] = []
    for page_type, url in discover_pages(session, domain, max_pages).items():
        page_html = _fetch(session, url)
        if not page_html:
            continue
        text = _text_of(page_html)
        # Many biotech sites (Genmab, Almirall, Moderna) render content
        # client-side, so a plain fetch returns a large HTML shell with almost
        # no readable text. Storing that would look like evidence while being
        # nothing, so it is skipped rather than recorded. Reading those sites
        # would require a headless browser; deliberately not a dependency here.
        if len(text) < 800 or (len(page_html) > 40_000 and len(text) / len(page_html) < 0.02):
            continue

        facts = extraction.extract(text, url)
        # Only keep a page that actually carries antibody/protein evidence —
        # a generic "About us" page is not evidence of anything (§17.14).
        if not facts["all_modalities"] and not facts["bottlenecks"] and not facts["all_stages"]:
            continue

        title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", page_html)
        title = html.unescape(title_match.group(1)).strip() if title_match else f"{company} {page_type}"

        item = make_item(
            url=url,
            title=f"{company} — {page_type.replace('_', ' ')}: {title[:80]}",
            content=text[:4000],
            raw_content=text[:20000],
            published_date="",
            seed_id=f"SITE-{page_type.upper()}",
            query=f"company_site:{page_type}",
            signal_type=SIGNAL_TYPE.get(page_type, "program"),
            days=days,
            known_company=company,
            known_domain=domain,
        )
        item["_page_type"] = page_type
        item["_facts"] = facts
        items.append(item)
        time.sleep(0.2)
    return items


def _js_shell_pages(session, company: str, domain: str, max_pages: int) -> list[tuple[str, str]]:
    """Pages that exist but returned no readable text — candidates for rendering."""
    out = []
    for page_type, url in discover_pages(session, domain, max_pages).items():
        page_html = _fetch(session, url)
        if page_html and len(_text_of(page_html)) < 800:
            out.append((page_type, url))
    return out


def fetch(
    days: int = 180,
    companies: list[tuple[str, str]] | None = None,
    max_pages: int = 6,
    use_apify: bool = True,
) -> list[dict[str, Any]]:
    """`companies` is [(canonical_name, domain)]. Without it there is nothing to
    crawl — this source is account-driven by design, not a discovery search.
    """
    if not companies:
        return []
    session = make_session(UA)
    items: list[dict[str, Any]] = []
    unrendered: list[tuple[str, str, str]] = []  # (company, page_type, url)

    for company, domain in companies:
        if not domain:
            continue
        got = fetch_company(session, company, domain, days, max_pages)
        items.extend(got)
        if not got:
            # Nothing readable over plain HTTP: either a JS-rendered site or a
            # site with no matching pages. Queue the pages that do exist for
            # cloud rendering rather than silently writing the company off.
            for page_type, url in _js_shell_pages(session, company, domain, max_pages):
                unrendered.append((company, page_type, url))

    if unrendered and use_apify and apify_crawler.available():
        rendered = apify_crawler.crawl([u for _, _, u in unrendered])
        for company, page_type, url in unrendered:
            text = rendered.get(url)
            if not text:
                continue
            facts = extraction.extract(text, url)
            if not facts["all_modalities"] and not facts["bottlenecks"] and not facts["all_stages"]:
                continue
            item = make_item(
                url=url,
                title=f"{company} — {page_type.replace('_', ' ')} (rendered)",
                content=text[:4000],
                raw_content=text[:20000],
                published_date="",
                seed_id=f"SITE-{page_type.upper()}",
                query=f"company_site:{page_type}:rendered",
                signal_type=SIGNAL_TYPE.get(page_type, "program"),
                days=days,
                known_company=company,
                known_domain=url.split("/")[2].replace("www.", ""),
            )
            item["_page_type"] = page_type
            item["_facts"] = facts
            item["_rendered"] = True
            items.append(item)

    return items
