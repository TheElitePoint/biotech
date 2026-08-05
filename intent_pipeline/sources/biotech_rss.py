"""Biotech trade-press RSS source adapter. Free, no API key.

Unlike the query-driven sources, these are fixed feeds — filtering happens
locally against the full recent feed rather than via a search query. Feed
URLs were verified live before wiring in (FierceBiotech and BioSpace's various
documented RSS paths 404; these four resolve with a real RSS content-type).
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any

from .base import get_with_retry, make_item, make_session

FEEDS = [
    ("FierceBiotech", "https://www.fiercebiotech.com/rss.xml"),
    ("FiercePharma", "https://www.fiercepharma.com/rss.xml"),
    ("GEN", "https://www.genengnews.com/feed/"),
    ("Labiotech", "https://www.labiotech.eu/feed/"),
]

KEEP = re.compile(
    r"antibody|antibodies|bispecific|multispecific|nanobody|\bVHH\b|\bscFv\b|"
    r"protein engineering|protein design|humaniz|affinity maturation|"
    r"developability|antibody-drug conjugate|\bADC\b|T-cell engager|"
    r"fusion protein|biologics discovery",
    re.I,
)
DROP = re.compile(
    r"market size|market report|forecast|webinar|podcast|job posting|"
    r"stock to watch|conference agenda",
    re.I,
)


def fetch(days: int = 30) -> list[dict[str, Any]]:
    session = make_session("Mozilla/5.0 (compatible; antibody-intent-research/1.1)")
    items: list[dict[str, Any]] = []

    for source_name, url in FEEDS:
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
            link = (entry.findtext("link") or "").strip()
            published = (entry.findtext("pubDate") or "").strip()
            blob = f"{title} {description}"
            if not title or not link or DROP.search(title) or not KEEP.search(blob):
                continue
            items.append(
                make_item(
                    url=link,
                    title=title,
                    content=re.sub(r"<[^>]+>", " ", description)[:600],
                    published_date=published,
                    seed_id=f"RSS-{source_name.upper()}",
                    query=f"{source_name} RSS feed (keyword-filtered)",
                    signal_type="program",
                    days=days,
                )
            )
    return items
