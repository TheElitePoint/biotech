"""Apify Website Content Crawler — reads JavaScript-rendered company sites.

The SOP names this actor directly (§44 "apify/website-content-crawler"). It
exists here to solve one specific, measured problem: several biotech sites
(Genmab, Almirall, Moderna in testing) render their pipeline and careers pages
client-side, so a plain HTTP fetch returns a large HTML shell containing no
readable content. Rather than installing a headless browser locally (~150MB of
browser binaries plus per-page CPU), the rendering happens in Apify's cloud.

Cost discipline, since this is the only paid-capable dependency in the project:

  * only domains that plain HTTP has already *failed* on are sent here;
  * `maxCrawlDepth=0` — the exact URLs given, no link-following;
  * media/CSS blocked and one batched run for all URLs, not one run per company.

Requires APIFY_TOKEN in .env. Without it this module is a no-op and the
pipeline degrades to plain-HTTP-only Tier 1A rather than failing.
"""

from __future__ import annotations

import os
from typing import Any

import requests

ACTOR = "apify~website-content-crawler"
RUN_SYNC = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items"


def available() -> bool:
    from ..tavily import load_dotenv

    load_dotenv()
    return bool(os.environ.get("APIFY_TOKEN"))


def crawl(urls: list[str], timeout: int = 300, max_results: int | None = None) -> dict[str, str]:
    """Render the given URLs and return {url: extracted_text}.

    Returns {} when no token is configured or the run fails — callers treat a
    missing page as unreadable, never as an empty-but-valid page.
    """
    from ..tavily import load_dotenv

    load_dotenv()
    token = os.environ.get("APIFY_TOKEN")
    if not token or not urls:
        return {}

    payload: dict[str, Any] = {
        "startUrls": [{"url": u} for u in urls],
        "crawlerType": "playwright:adaptive",  # renders JS, falls back to raw HTTP when static
        "maxCrawlDepth": 0,                     # exactly these pages, no link-following
        "maxCrawlPages": len(urls),
        "maxResults": max_results or len(urls),
        "blockMedia": True,                     # no images/fonts/CSS — cheaper and faster
        "removeCookieWarnings": True,
        "saveMarkdown": True,
        "respectRobotsTxtFile": True,
        "proxyConfiguration": {"useApifyProxy": True},
    }

    try:
        r = requests.post(
            RUN_SYNC,
            params={"token": token, "timeout": timeout},
            json=payload,
            timeout=(15, timeout + 30),
        )
        r.raise_for_status()
        items = r.json()
    except Exception:  # noqa: BLE001 - a failed render is a missing page, not a crash
        return {}

    out: dict[str, str] = {}
    for item in items if isinstance(items, list) else []:
        url = item.get("url") or item.get("loadedUrl")
        text = item.get("markdown") or item.get("text") or ""
        if url and text and len(text.strip()) > 200:
            out[url] = text.strip()
    return out
