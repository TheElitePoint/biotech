"""Raw Signal normalization, dedupe and company resolution (SOP pages 28, 29, 79)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

from .config import (
    ATS_HOSTS,
    ATS_SUBDOMAIN_SUFFIXES,
    NEWS_DOMAINS,
    NON_COMPANY_DOMAINS,
)

_DATE_PATTERNS = [
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d",
    "%d %B %Y",
    "%B %d, %Y",
    "%b %d, %Y",
]

# Corporate form is always noise. Descriptive suffixes are only noise when something
# recognizable survives without them — "RQ Bio" must not become "RQ".
_LEGAL_SUFFIX = re.compile(
    r"[,\s]+(inc|llc|ltd|limited|corp|corporation|co|plc|gmbh|ab|sa|nv|bv|pte|pty)\.?$",
    re.I,
)
_DESCRIPTIVE_SUFFIX = re.compile(
    r"[,\s]+(therapeutics|biosciences|bioscience|biotherapeutics|pharmaceuticals|"
    r"pharma|labs|laboratories)\.?$",
    re.I,
)

# Trade-press headlines prefix the company with a descriptor: "Bispecific antibody
# firm Ollin raises...". Keep only what follows the descriptor noun.
_DESCRIPTOR_PREFIX = re.compile(
    r"^.*?\b(?:firm|biotech|startup|start-up|company|maker|developer|specialist|"
    r"outfit|player|group)\s+(?=[A-Z])",
)

# "Acme Bio raises $40M" / "Acme Therapeutics Announces ..." — headline case varies,
# so the verb match is case-insensitive while the name must still be capitalized.
_COMPANY_IN_TITLE = re.compile(
    r"^([A-Z][\w&'\-\.]*(?:\s+[A-Z][\w&'\-\.]*){0,3}?)\s+"
    r"(?i:raises|raised|announces|announced|launches|launched|secures|secured|closes|"
    r"closed|nominates|nominated|unveils|expands|appoints|doses|reports|emerges|"
    r"lands|nets|banks|debuts|adds|picks up|reels in)\b"
)

# Publisher/media domains resolve as sources, never as the asset owner. Matching by
# pattern as well as by name catches the long tail of trade press the seed bank turns
# up, which a fixed list will always trail behind.
_MEDIA_DOMAIN = re.compile(
    r"(news|press|wire|journal|daily|times|post|herald|report|magazine|media|blog|"
    r"today|insider|weekly|review|pharmaphorum|biopharma|biospace|endpts|fierce|"
    r"labiotech|statnews|scrip|genengnews)",
    re.I,
)


@dataclass
class Signal:
    """One row of the SOP Raw Signals table."""

    signal_id: str
    seed_id: str
    query: str
    signal_type: str
    source: str
    source_url: str
    source_domain: str
    title: str
    snippet: str
    raw_text: str
    signal_date: str | None
    collected_at: str
    date_window_days: int
    source_level: int  # SOP page 58 evidence hierarchy
    company_candidate: str | None = None
    company_domain: str | None = None
    resolution_note: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def as_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["extras"] = ""
        return row


def _domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _parse_date(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    # Tavily's news topic returns RFC 2822, e.g. "Thu, 09 Jul 2026 12:02:17 GMT".
    try:
        return parsedate_to_datetime(text).date().isoformat()
    except (TypeError, ValueError):
        pass
    for pattern in _DATE_PATTERNS:
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", text)
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}" if match else None


def _source_level(domain: str) -> int:
    """SOP page 58: 1 = primary/registry, 2 = literature, 3 = news, 4 = social."""
    if domain in {
        "clinicaltrials.gov",
        "reporter.nih.gov",
        "patents.google.com",
        "sec.gov",
    }:
        return 1
    if domain in {
        "pubmed.ncbi.nlm.nih.gov",
        "ncbi.nlm.nih.gov",
        "europepmc.org",
        "biorxiv.org",
        "nature.com",
        "sciencedirect.com",
    }:
        return 2
    if domain in set(NEWS_DOMAINS):
        return 3
    if domain in {"linkedin.com", "x.com", "twitter.com"}:
        return 4
    if domain in NON_COMPANY_DOMAINS or _MEDIA_DOMAIN.search(domain):
        return 3
    return 1  # company-owned page


def canonical_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name or "").strip(" .,-")
    name = _DESCRIPTOR_PREFIX.sub("", name).strip()
    name = _LEGAL_SUFFIX.sub("", name).strip()
    stripped = _DESCRIPTIVE_SUFFIX.sub("", name).strip()
    # Only drop the descriptive word if a usable name remains behind it.
    if len(stripped) >= 4 and stripped.lower() not in {"the", "new"}:
        name = stripped
    return name


def normalize(item: dict[str, Any]) -> Signal:
    url = item.get("url", "")
    domain = _domain(url)
    title = (item.get("title") or "").strip()
    snippet = (item.get("content") or "").strip()
    raw = (item.get("raw_content") or "")[:20000]

    sig = Signal(
        signal_id=hashlib.sha1(url.encode()).hexdigest()[:16],
        seed_id=item.get("_seed_id", ""),
        query=item.get("_query", ""),
        signal_type=item.get("_signal_type", ""),
        source="tavily",
        source_url=url,
        source_domain=domain,
        title=title,
        snippet=snippet,
        raw_text=raw,
        signal_date=_parse_date(item.get("published_date") or item.get("published_time")),
        collected_at=datetime.now(timezone.utc).date().isoformat(),
        date_window_days=int(item.get("_date_window_days", 30)),
        source_level=_source_level(domain),
        extras={"score": item.get("score")},
    )
    resolve_company(sig)
    return sig


def _domain_matches_content(sig: Signal) -> bool:
    """Does the domain owner actually appear to be the subject of the page?

    Enumerating every trade publication is a losing game, so require positive
    evidence instead: the domain's own name must show up in the title or the
    opening text. A company's press release names the company; an article that
    surveys ten companies does not name its publisher.
    """
    core = sig.source_domain.split(".")[0]
    if core in {"www", "news", "markets", "ir", "investors", "blog"}:
        # Subdomain carries no identity — fall back to the registrable part.
        parts = sig.source_domain.split(".")
        core = parts[1] if len(parts) > 2 else core
    token = re.sub(r"[^a-z0-9]", "", core.lower())
    if len(token) < 4:
        return False
    # Publishers append their own brand to every headline ("... - BioTechniques"),
    # which would otherwise look like the page naming its owner. Drop that suffix;
    # a company's own release names itself in the headline proper, not just the tail.
    title = re.split(r"\s+[-|–—]\s+", sig.title)[0] if sig.title else ""
    haystack = re.sub(r"[^a-z0-9]", "", f"{title} {sig.snippet[:500]}".lower())
    return token in haystack


def _resolve_from_ats(sig: Signal) -> bool:
    """Pull the employer out of an applicant-tracking URL.

    `jobs.lever.co/novabinder/abc-123` and `novabinder.bamboohr.com/careers/7` both
    name the company unambiguously. This is the only place a job posting yields a
    reliable employer without a second lookup, which is why the hiring trigger routes
    through ATS platforms rather than job boards.
    """
    host = sig.source_domain

    slug = ""
    if host in ATS_HOSTS:
        parts = [p for p in urlparse(sig.source_url).path.split("/") if p]
        if parts:
            slug = parts[0]
    else:
        for suffix in ATS_SUBDOMAIN_SUFFIXES:
            if host.endswith(suffix):
                slug = host[: -len(suffix)]
                break

    if not slug or slug.lower() in {"jobs", "careers", "search", "j", "embed"}:
        return False

    sig.company_candidate = canonical_name(slug.replace("-", " ").replace("_", " ").title())
    # The employer is known but its own website is not; enrichment must resolve it.
    sig.company_domain = ""
    sig.resolution_note = f"employer parsed from {host} posting; company domain unverified"
    return True


def resolve_company(sig: Signal) -> Signal:
    """Attach a company candidate.

    Rule from SOP page 82: never assume the publisher or affiliation is the
    commercial owner. A news domain gives a name only; the domain stays empty
    until website verification confirms it.
    """
    if _resolve_from_ats(sig):
        return sig

    is_publisher = (
        sig.source_domain in NON_COMPANY_DOMAINS
        or bool(_MEDIA_DOMAIN.search(sig.source_domain))
    )
    if sig.source_domain and not is_publisher and _domain_matches_content(sig):
        # Signal came straight off a company site — strongest resolution.
        sig.company_domain = sig.source_domain
        sig.company_candidate = canonical_name(
            sig.source_domain.split(".")[0].replace("-", " ").title()
        )
        sig.resolution_note = "resolved from source domain (company-owned page)"
        return sig

    # Strip any trade-press descriptor first so the headline starts at the company.
    headline = _DESCRIPTOR_PREFIX.sub("", sig.title).strip()
    match = _COMPANY_IN_TITLE.match(headline)
    if match:
        sig.company_candidate = canonical_name(match.group(1))
        sig.resolution_note = f"name parsed from {sig.source_domain} headline; domain unverified"
        return sig

    sig.resolution_note = "unresolved — needs company lookup before scoring"
    return sig


def dedupe(signals: list[Signal]) -> list[Signal]:
    """SOP page 79: signal key = canonical URL + meaningful update date."""
    seen: set[str] = set()
    out: list[Signal] = []
    for sig in signals:
        key = f"{sig.source_url}|{sig.signal_date or ''}"
        if key in seen:
            continue
        seen.add(key)
        out.append(sig)
    return out
