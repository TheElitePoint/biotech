"""Public job listings via applicant-tracking-system APIs (brief §3 Tier 1B).

Why this source carries disproportionate weight: the SOP notes that hiring is a
timing signal, but a *job description* is far more than that — it names the
modality, the target class and the specific assays, which means it states the
program's bottleneck in the company's own words. That is exactly the Gate 3
evidence third-party news never supplies.

These are structured public JSON APIs (no key, no HTML parsing, no JavaScript
rendering problem, no browser dependency):

    Greenhouse  boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
    Lever       api.lever.co/v0/postings/{token}?mode=json
    Ashby       api.ashbyhq.com/posting-api/job-board/{token}

The board token is discovered from the company's own careers page rather than
guessed, so a company is only queried on a board it actually publishes.
"""

from __future__ import annotations

import html
import re
import time
from typing import Any

from .. import extraction
from .base import get_with_retry, make_item, make_session

UA = "antibody-prospecting-research/1.0 (+contact:research@example.invalid)"

# Board-token patterns as they appear in careers-page markup / redirects.
BOARD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("greenhouse", re.compile(r"(?:boards|job-boards)\.greenhouse\.io/(?:embed/job_board\?for=)?([A-Za-z0-9_-]+)", re.I)),
    ("greenhouse", re.compile(r"boards-api\.greenhouse\.io/v1/boards/([A-Za-z0-9_-]+)", re.I)),
    ("lever", re.compile(r"jobs\.lever\.co/([A-Za-z0-9_-]+)", re.I)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([A-Za-z0-9_-]+)", re.I)),
]

# Roles that indicate antibody/protein design work. Matched against the job
# TITLE only: matching the description instead let "Associate Director, Sales"
# and "Director, Government Partnership" through, because nearly every posting
# repeats a company blurb mentioning biologics or protein therapeutics.
RELEVANT_ROLE = re.compile(
    r"antibod|protein engineer|protein design|biologic|bispecific|nanobod|\bVHH\b|"
    r"computational biolog|computational chem|structural biolog|"
    r"molecular design|discovery scientist|developability|"
    r"assay development|hit identification|lead optimi|"
    r"machine learning|protein scientist|biochemist",
    re.I,
)

# Non-technical functions never state a design bottleneck, even when the title
# happens to contain a science word ("Sales Director, Biologics").
EXCLUDE_ROLE = re.compile(
    r"\b(sales|commercial|marketing|business development|partnership|government|"
    r"policy|legal|counsel|finance|accounting|payroll|recruit|talent|"
    r"people operations|human resources|\bHR\b|facilities|administrative|"
    r"executive assistant|communications|investor relations|procurement)\b",
    re.I,
)

_TAG = re.compile(r"(?s)<[^>]+>")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", text or ""))).strip()


def discover_board(session, domain: str) -> tuple[str | None, str | None]:
    """Find which ATS a company publishes on, from its own careers page."""
    for path in ("/careers", "/careers/", "/jobs", "/join-us", ""):
        url = f"https://{domain}{path}"
        try:
            r = session.get(url, timeout=(8, 20), allow_redirects=True)
        except Exception:  # noqa: BLE001
            continue
        if r.status_code >= 400:
            continue
        blob = r.text
        for provider, pattern in BOARD_PATTERNS:
            match = pattern.search(blob)
            if match:
                token = match.group(1)
                if token.lower() not in {"embed", "job_board", "v1", "boards"}:
                    return provider, token
        time.sleep(0.15)
    return None, None


def _greenhouse(session, token: str) -> list[dict[str, Any]]:
    r = get_with_retry(
        session, f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs",
        params={"content": "true"}, timeout=(8, 25),
    )
    if r is None:
        return []
    try:
        jobs = r.json().get("jobs", [])
    except ValueError:
        return []
    out = []
    for job in jobs:
        out.append({
            "id": str(job.get("id", "")),
            "title": job.get("title", ""),
            "url": job.get("absolute_url", ""),
            "updated_at": (job.get("updated_at") or "")[:10],
            "description": _clean(job.get("content", "")),
            "location": (job.get("location") or {}).get("name", ""),
        })
    return out


def _lever(session, token: str) -> list[dict[str, Any]]:
    r = get_with_retry(
        session, f"https://api.lever.co/v0/postings/{token}",
        params={"mode": "json"}, timeout=(8, 25),
    )
    if r is None:
        return []
    try:
        jobs = r.json()
    except ValueError:
        return []
    out = []
    for job in jobs if isinstance(jobs, list) else []:
        out.append({
            "id": str(job.get("id", "")),
            "title": job.get("text", ""),
            "url": job.get("hostedUrl", ""),
            "updated_at": "",
            "description": _clean(job.get("descriptionPlain") or job.get("description", "")),
            "location": (job.get("categories") or {}).get("location", ""),
        })
    return out


def _ashby(session, token: str) -> list[dict[str, Any]]:
    r = get_with_retry(
        session, f"https://api.ashbyhq.com/posting-api/job-board/{token}",
        params={"includeCompensation": "false"}, timeout=(8, 25),
    )
    if r is None:
        return []
    try:
        jobs = r.json().get("jobs", [])
    except ValueError:
        return []
    out = []
    for job in jobs:
        out.append({
            "id": str(job.get("id", "")),
            "title": job.get("title", ""),
            "url": job.get("jobUrl", ""),
            "updated_at": (job.get("publishedAt") or "")[:10],
            "description": _clean(job.get("descriptionHtml") or job.get("descriptionPlain", "")),
            "location": job.get("location", ""),
        })
    return out


FETCHERS = {"greenhouse": _greenhouse, "lever": _lever, "ashby": _ashby}


def fetch_company(session, company: str, domain: str, days: int = 30) -> list[dict[str, Any]]:
    provider, token = discover_board(session, domain)
    if not provider or not token:
        return []
    jobs = FETCHERS[provider](session, token)

    items: list[dict[str, Any]] = []
    for job in jobs:
        title = job["title"]
        if EXCLUDE_ROLE.search(title) or not RELEVANT_ROLE.search(title):
            continue
        text = f"{title}. {job['description']}"
        facts = extraction.extract(text, job["url"])
        # A relevant-sounding title with no modality or bottleneck evidence in
        # the description is not usable evidence — skip rather than store it.
        if not facts["all_modalities"] and not facts["bottlenecks"]:
            continue

        item = make_item(
            url=job["url"],
            title=f"{company} is hiring: {title}",
            content=text[:4000],
            raw_content=text[:20000],
            published_date=job["updated_at"],
            seed_id=f"JOBS-{provider.upper()}",
            query=f"ats:{provider}/{token}",
            signal_type="hiring",
            days=days,
            known_company=company,
            known_domain=domain,
        )
        item["_facts"] = facts
        item["_job_id"] = job["id"]
        item["_ats"] = provider
        items.append(item)
    return items


def fetch(
    days: int = 30,
    companies: list[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """`companies` is [(canonical_name, domain)]; account-driven like company_site."""
    if not companies:
        return []
    session = make_session(UA)
    items: list[dict[str, Any]] = []
    for company, domain in companies:
        if not domain:
            continue
        items.extend(fetch_company(session, company, domain, days))
        time.sleep(0.2)
    return items
