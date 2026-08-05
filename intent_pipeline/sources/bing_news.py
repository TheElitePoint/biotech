"""Bing News RSS source adapter. Free, no API key.

Live news search per query, every run — Bing's own recency ranking, no stored
article list. Ported from the old daily_news.py.
"""

from __future__ import annotations

import html
import re
import time
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse

from .base import get_with_retry, make_item, make_session

# (query, signal_type) pairs spanning the SOP's six trigger families.
QUERIES: list[tuple[str, str]] = [
    ('"antibody" biotech raises funding', "capital"),
    ('"bispecific antibody" financing biotech', "capital"),
    ('"multispecific antibody" funding company', "capital"),
    ('"nanobody" funding therapeutic company', "capital"),
    ('"therapeutic protein" biotech funding', "capital"),
    ('"protein engineering" therapeutics funding', "capital"),
    ('"antibody pipeline" Series A biotech', "capital"),
    ('"antibody program" seed financing biotech', "capital"),
    ('"development candidate" antibody company', "milestone"),
    ('"candidate nomination" antibody biotech', "milestone"),
    ('"IND-enabling" antibody company', "milestone"),
    ('"IND application" bispecific antibody company', "milestone"),
    ('"preclinical" bispecific antibody company', "program"),
    ('"lead optimization" antibody biotech', "program"),
    ('"pipeline expansion" antibody company', "program"),
    ('"new antibody program" biotech', "program"),
    ('"antibody-drug conjugate" preclinical company', "program"),
    ('"bispecific ADC" company pipeline', "program"),
    ('"T-cell engager" preclinical biotech', "program"),
    ('"antibody fragment" therapeutic company', "program"),
    ('"VHH" therapeutic biotech company', "program"),
    ('"scFv" therapeutic company', "program"),
    ('"Fc fusion" therapeutic biotech', "program"),
    ('"fusion protein" preclinical biotech', "program"),
    ('"immunocytokine" biotech company', "program"),
    ('"engineered protein therapeutic" company', "program"),
    ('"affinity maturation" therapeutic company', "scientific"),
    ('"antibody humanization" therapeutic company', "scientific"),
    ('"antibody developability" biotech company', "scientific"),
    ('"protein stability" therapeutic biotech', "scientific"),
    ('"antibody specificity" biotech program', "scientific"),
    ('"membrane protein" antibody company', "scientific"),
    ('"GPCR antibody" therapeutic company', "scientific"),
    ('"antibody discovery" biotech partnership', "execution"),
    ('"protein engineering" biotech partnership', "execution"),
    ('"wet-lab validation" antibody biotech', "execution"),
    ('"antibody discovery" hiring biotech', "hiring"),
    ('"protein engineering" hiring therapeutics', "hiring"),
    ('"antibody engineering" scientist biotech', "hiring"),
    ('"developability" scientist antibody company', "hiring"),
]

BAD_TITLE = re.compile(
    r"market size|market report|forecast|review article|conference agenda|"
    r"webinar|podcast|supplier|services|CRO\b|CDMO\b|diagnostic|assay kit|"
    r"research use only|stock to watch|best stocks|investor alert",
    re.I,
)


def _direct_url(link: str) -> str:
    parsed = urlparse(link)
    target = parse_qs(parsed.query).get("url", [""])[0]
    return target or link


def fetch(days: int = 365, queries: list[tuple[str, str]] | None = None) -> list[dict[str, Any]]:
    session = make_session("Mozilla/5.0 (compatible; antibody-intent-research/1.1)")
    items: list[dict[str, Any]] = []

    for query, signal_type in queries or QUERIES:
        url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
        r = get_with_retry(session, url, timeout=(10, 30))
        if r is None:
            continue
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError:
            continue
        for entry in root.findall("./channel/item"):
            title = html.unescape(entry.findtext("title") or "").strip()
            description = html.unescape(entry.findtext("description") or "").strip()
            link = _direct_url(entry.findtext("link") or "")
            published = (entry.findtext("pubDate") or "").strip()
            if not title or not link or BAD_TITLE.search(title):
                continue
            items.append(
                make_item(
                    url=link,
                    title=title,
                    content=re.sub(r"<[^>]+>", " ", description),
                    published_date=published,
                    seed_id=f"BING-{signal_type.upper()}",
                    query=query,
                    signal_type=signal_type,
                    days=days,
                )
            )
        time.sleep(0.1)
    return items
