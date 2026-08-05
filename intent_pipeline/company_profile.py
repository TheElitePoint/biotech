"""Company profile resolution: canonical name -> official website domain + size.

This unblocks Tier 1A entirely. The brief makes company-owned pages the primary
authority for ownership, modality and stage — but you cannot fetch a company's
/pipeline page without first knowing its domain, and until now nearly every
company in the dataset had domain = NULL.

Resolution order, cheapest and most authoritative first:

  1. Wikidata P856 (official website) + P1128 (employees) in a single
     wbgetentities call. Free, no key, and P856 is a curated first-party fact.
  2. Tavily search fallback, only for companies Wikidata has no P856 for
     (e.g. Almirall in testing). Tavily is quota-limited and previously
     returned 432 when exhausted, so it is deliberately the fallback and only
     ever costs one search per unresolved company, cached thereafter.

Per brief §17.3, a domain that cannot be resolved stays None — it is never
guessed from the company name (guessing "almirall.com" and crawling it would
manufacture evidence, which §12.8 forbids outright).
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config import NON_COMPANY_DOMAINS
from .sources.base import get_with_retry, make_session

CACHE = Path(__file__).resolve().parent.parent / "data" / "company_profiles.json"
WD_API = "https://www.wikidata.org/w/api.php"
TAVILY_SEARCH = "https://api.tavily.com/search"

UA = "antibody-prospecting-research/1.0 (contact:research@example.invalid)"

_STOPWORDS = re.compile(
    r"\b(inc|llc|ltd|limited|corp|corporation|co|plc|gmbh|ag|se|ab|sa|nv|bv|pte|pty|"
    r"holdings?|group|therapeutics?|biotherapeutics?|biosciences?|biotechnology|"
    r"biotech|pharmaceuticals?|pharma|biologics?|biomed)\b\.?",
    re.I,
)

# Hosts that are never a company's own site. Split deliberately into exact and
# substring matching: a substring rule for short hosts is dangerous. "x.com"
# as a substring rejected clasptx.com, arcustx.com, kymeratx.com — the "...tx.com"
# convention is pervasive in biotech, so that one pattern was silently discarding
# a large share of valid company domains.
_BAD_DOMAIN_EXACT = {
    "x.com", "twitter.com", "facebook.com", "instagram.com", "youtube.com",
    "dnb.com", "craft.co", "owler.com", "sec.gov", "clinicaltrials.gov",
}
_BAD_DOMAIN_SUB = re.compile(
    r"(wikipedia|linkedin|crunchbase|bloomberg|reuters|yahoo|google|glassdoor|"
    r"indeed|zoominfo|pitchbook|marketscreener|investing\.com|nasdaq|"
    r"duckduckgo|bing\.com|globenewswire|prnewswire|businesswire)",
    re.I,
)


def _is_bad_domain(host: str) -> bool:
    return host in _BAD_DOMAIN_EXACT or bool(_BAD_DOMAIN_SUB.search(host))


@dataclass
class Profile:
    canonical_name: str
    domain: str | None = None
    employees: int | None = None
    wikidata_qid: str | None = None
    domain_source: str | None = None   # 'wikidata' | 'tavily' | None
    evidence_url: str | None = None


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


def normalize_domain(url_or_host: str | None) -> str | None:
    if not url_or_host:
        return None
    text = url_or_host.strip()
    if "//" not in text:
        text = "https://" + text
    host = (urlparse(text).netloc or "").lower().strip()
    if host.startswith("www."):
        host = host[4:]
    host = host.split(":")[0]
    if not host or "." not in host:
        return None
    if _is_bad_domain(host) or host in NON_COMPANY_DOMAINS:
        return None
    return host


def _name_matches(label: str, company: str) -> bool:
    core = re.sub(r"[^a-z0-9 ]", "", _STOPWORDS.sub("", company).lower()).strip()
    if not core:
        return False
    return core in label.lower() or label.lower() in core


_LEGAL_TAIL = re.compile(
    r"[,\s]+(inc|llc|ltd|limited|corp|corporation|co|plc|gmbh|ag|se|ab|sa|s\.a\.?|nv|bv|"
    r"pte|pty|aps|oy|spa|srl|kk|holdings?|group)\.?\s*$",
    re.I,
)


def search_name(company: str) -> str:
    """Wikidata's search rejects trailing legal forms outright: "AbCellera
    Biologics Inc." returns zero hits while "AbCellera Biologics" resolves.
    This silently cost ~87% of domain coverage (39 of 45 companies unresolved)
    until it was traced, so the suffix is stripped before searching.
    """
    name = company.strip()
    previous = None
    while name != previous:
        previous = name
        name = _LEGAL_TAIL.sub("", name).strip(" ,.")
    return name or company.strip()


def _wikidata(session, company: str) -> Profile:
    profile = Profile(canonical_name=company)
    r = get_with_retry(
        session, WD_API,
        params={"action": "wbsearchentities", "search": search_name(company), "language": "en",
                "format": "json", "type": "item", "limit": 5},
        timeout=(8, 20),
    )
    if r is None:
        return profile
    try:
        hits = r.json().get("search", [])
    except ValueError:
        return profile

    for hit in hits:
        label = hit.get("label") or ""
        if not _name_matches(label, company):
            continue
        qid = hit["id"]
        r2 = get_with_retry(
            session, WD_API,
            params={"action": "wbgetentities", "ids": qid, "props": "claims", "format": "json"},
            timeout=(8, 25),
        )
        if r2 is None:
            continue
        try:
            claims = r2.json().get("entities", {}).get(qid, {}).get("claims", {})
        except ValueError:
            continue

        profile.wikidata_qid = qid

        site_claims = claims.get("P856") or []
        for claim in site_claims:
            value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
            domain = normalize_domain(value)
            if domain:
                profile.domain = domain
                profile.domain_source = "wikidata"
                profile.evidence_url = f"https://www.wikidata.org/wiki/{qid}"
                break

        profile.employees = _latest_employees(claims.get("P1128") or [])
        if profile.domain or profile.employees is not None:
            return profile
    return profile


def _latest_employees(entries: list[dict[str, Any]]) -> int | None:
    dated, undated = [], []
    for entry in entries:
        amount = entry.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("amount")
        if amount is None:
            continue
        try:
            value = int(float(amount))
        except (TypeError, ValueError):
            continue
        when = (
            entry.get("qualifiers", {}).get("P585", [{}])[0]
            .get("datavalue", {}).get("value", {}).get("time", "")
        )
        (dated if when else undated).append((when, value))
    if dated:
        dated.sort(key=lambda t: t[0], reverse=True)
        return dated[0][1]
    return undated[0][1] if undated else None


def _accept_domain(company: str, url: str) -> str | None:
    """Accept a search result only when the domain actually echoes the company.

    Guards against recording a press-release host as the company's own site.
    Deliberately tolerant of abbreviation — Clasp Therapeutics really is
    `clasptx.com` — which is also why the domain is never *constructed* from
    the name: it is only ever confirmed from a real search result.
    """
    domain = normalize_domain(url)
    if not domain:
        return None
    token = re.sub(r"[^a-z0-9]", "", _STOPWORDS.sub("", company).lower())
    stem = re.sub(r"[^a-z0-9]", "", domain.split(".")[0])
    if not token or not stem:
        return None
    head = token[:6]
    if head and (head in stem or stem[:6] in token):
        return domain
    return None


def _duckduckgo_domain(session, company: str) -> tuple[str | None, str | None]:
    """Free, key-less, quota-less domain lookup.

    Replaces the Tavily fallback, which returned HTTP 432 (plan limit) and left
    every small or recently founded biotech unresolved — exactly the companies
    Wikidata does not cover either.
    """
    # A dedicated session: reusing the Wikidata session's research User-Agent
    # made DuckDuckGo answer 202 with an anti-bot page instead of results.
    import requests as _requests

    ddg = _requests.Session()
    ddg.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        r = ddg.post(
            "https://html.duckduckgo.com/html/",
            data={"q": f"{search_name(company)} biotech official website"},
            timeout=(10, 25),
        )
        if r.status_code != 200:
            return None, None
    except Exception:  # noqa: BLE001 - a failed lookup leaves the domain unresolved
        return None, None

    for url in re.findall(r'href="(https?://[^"]+)"', r.text):
        domain = _accept_domain(company, url)
        if domain:
            return domain, url
    return None, None


def _tavily_domain(session, company: str) -> tuple[str | None, str | None]:
    """Optional Tavily lookup, used only when a key is configured and working."""
    key = os.environ.get("TAVILY_API_KEY", "")
    if not key:
        return None, None
    try:
        r = session.post(
            TAVILY_SEARCH,
            json={
                "api_key": key,
                "query": f'"{company}" official company website pipeline',
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": False,
            },
            timeout=(10, 25),
        )
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception:  # noqa: BLE001 - quota/network failures fall back to unresolved
        return None, None

    for item in results:
        domain = _accept_domain(company, item.get("url", ""))
        if domain:
            return domain, item.get("url", "")
    return None, None


def resolve(names: list[str], use_tavily_fallback: bool = True) -> dict[str, Profile]:
    """Resolve a batch of company names to profiles, caching every lookup."""
    from .tavily import load_dotenv

    load_dotenv()
    cache = _load_cache()
    session = make_session(UA)
    out: dict[str, Profile] = {}
    dirty = False

    for name in names:
        if not name:
            continue
        key = name.strip().lower()
        if key in cache:
            out[name] = Profile(**cache[key])
            continue

        profile = _wikidata(session, name)
        if profile.domain is None and use_tavily_fallback:
            # DuckDuckGo first: free and unmetered, so it carries the bulk of
            # the long tail. Tavily only as a second try, since its quota runs
            # out and returns 432.
            domain, evidence = _duckduckgo_domain(session, name)
            source = "duckduckgo"
            if not domain:
                domain, evidence = _tavily_domain(session, name)
                source = "tavily"
            if domain:
                profile.domain = domain
                profile.domain_source = source
                profile.evidence_url = evidence
        cache[key] = asdict(profile)
        out[name] = profile
        dirty = True
        time.sleep(0.12)

    if dirty:
        _save_cache(cache)
    return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Resolve company domains and sizes")
    parser.add_argument("companies", nargs="+")
    parser.add_argument("--no-tavily", action="store_true")
    args = parser.parse_args()

    for name, profile in resolve(args.companies, not args.no_tavily).items():
        print(f"{name:32} {str(profile.domain):32} emp={profile.employees} "
              f"via={profile.domain_source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
