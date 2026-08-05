"""ClinicalTrials.gov source adapter.

Enumerates industry-sponsored trials matching antibody/protein intervention
terms (free, no API key — ported from the old intent_pipeline/universe.py),
then emits one Tavily-shaped item per company whose most recent *active* trial
update falls inside the window. Company name comes straight from the
registry's sponsor field, so it is passed through as `_known_company` —
resolve_company() never has to guess it from a headline.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterator

from .base import get_with_retry, make_item, make_session

CTGOV = "https://clinicaltrials.gov/api/v2/studies"

INTERVENTION_QUERIES = [
    "antibody",
    "monoclonal antibody",
    "bispecific antibody",
    "antibody drug conjugate",
    "nanobody",
    "fusion protein",
    "recombinant protein",
]

SPONSOR_EXCLUDE = re.compile(
    r"\b(university|universit|college|school of|institut|hospital|clinic|medical center|"
    r"medical centre|health system|foundation|trust|ministry|national cancer|nih|nci|"
    r"academy|academia|cancer center|cancer centre|research center|research centre|"
    r"assistance publique|charite|charité|inserm|cnrs|max planck|fred hutchinson|"
    r"mayo clinic|cleveland clinic|md anderson|memorial sloan)\b",
    re.I,
)
CRO_EXCLUDE = re.compile(
    r"\b(contract research|cro\b|cdmo\b|laborator(y|ies)|diagnostics|reagent|"
    r"consulting|consultants|staffing|logistics|packaging|manufacturing services)\b",
    re.I,
)
BIG_PHARMA = {
    "pfizer", "merck", "novartis", "roche", "genentech", "astrazeneca", "sanofi",
    "gsk", "glaxosmithkline", "johnson", "janssen", "abbvie", "abbott", "amgen",
    "bristol", "eli lilly", "lilly", "bayer", "boehringer", "takeda", "novo nordisk",
    "gilead", "biogen", "regeneron", "moderna", "daiichi", "astellas", "eisai",
}
ACTIVE_STATUSES = {"RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION", "ACTIVE_NOT_RECRUITING"}
_LEGAL = re.compile(
    r"[,\s]+(inc|llc|ltd|limited|corp|corporation|co|plc|gmbh|ag|ab|a\.?s|sa|s\.a\.?|"
    r"nv|bv|pte|pty|aps|oy|srl|s\.r\.l\.?|kk|k\.k\.?|holdings?|group)\.?$",
    re.I,
)


def _classify(name: str) -> tuple[bool, str]:
    if SPONSOR_EXCLUDE.search(name):
        return False, "academic or hospital sponsor"
    if CRO_EXCLUDE.search(name):
        return False, "service provider name"
    low = name.lower()
    for big in BIG_PHARMA:
        if big in low:
            return True, "large pharma — account-based only (SOP p14)"
    return True, ""


def _key(name: str) -> str:
    n = _LEGAL.sub("", name.strip()).strip().lower()
    return re.sub(r"[^a-z0-9]", "", n)


@dataclass
class _Company:
    name: str
    interventions: set[str] = field(default_factory=set)
    conditions: set[str] = field(default_factory=set)
    phases: set[str] = field(default_factory=set)
    active_phases: set[str] = field(default_factory=set)
    statuses: set[str] = field(default_factory=set)
    active_nct: str = ""
    last_active_update: str = ""
    matched_query: str = ""


def _sweep(session, query: str, max_pages: int, page_size: int = 200) -> Iterator[dict[str, Any]]:
    token = None
    for _ in range(max_pages):
        params = {
            "query.intr": query,
            "fields": (
                "protocolSection.identificationModule.nctId,"
                "protocolSection.sponsorCollaboratorsModule,"
                "protocolSection.statusModule,"
                "protocolSection.designModule.phases,"
                "protocolSection.conditionsModule.conditions,"
                "protocolSection.armsInterventionsModule.interventions"
            ),
            "pageSize": page_size,
        }
        if token:
            params["pageToken"] = token
        r = get_with_retry(session, CTGOV, params=params, timeout=(10, 90))
        if r is None:
            return
        data = r.json()
        for study in data.get("studies", []):
            yield study
        token = data.get("nextPageToken")
        if not token:
            return
        time.sleep(0.15)


def fetch(days: int = 180, max_pages: int = 20, queries: list[str] | None = None) -> list[dict[str, Any]]:
    session = make_session("antibody-prospecting/0.2")
    companies: dict[str, _Company] = {}

    for query in queries or INTERVENTION_QUERIES:
        for study in _sweep(session, query, max_pages):
            proto = study.get("protocolSection", {})
            sponsors = proto.get("sponsorCollaboratorsModule", {})
            lead = sponsors.get("leadSponsor") or {}
            if lead.get("class") != "INDUSTRY":
                continue
            name = (lead.get("name") or "").strip()
            if not name:
                continue
            keep, note = _classify(name)
            if not keep:
                continue

            key = _key(name)
            if not key:
                continue
            company = companies.setdefault(key, _Company(name=name))
            company.matched_query = query

            status = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            nct = proto.get("identificationModule", {}).get("nctId", "")
            company.phases.update(design.get("phases") or [])
            company.conditions.update((proto.get("conditionsModule", {}).get("conditions") or [])[:5])
            for iv in (proto.get("armsInterventionsModule", {}).get("interventions") or [])[:5]:
                if iv.get("name"):
                    company.interventions.add(iv["name"][:60])
            overall = status.get("overallStatus") or ""
            if overall:
                company.statuses.add(overall)

            updated = status.get("lastUpdateSubmitDate") or (
                status.get("lastUpdatePostDateStruct") or {}
            ).get("date", "")
            if overall in ACTIVE_STATUSES and updated > company.last_active_update:
                design_phases = design.get("phases") or []
                company.active_phases.update(design_phases)
                company.last_active_update = updated
                company.active_nct = nct

    items: list[dict[str, Any]] = []
    for key, c in companies.items():
        if not c.last_active_update:
            continue
        try:
            age = (date.today() - datetime.strptime(c.last_active_update[:10], "%Y-%m-%d").date()).days
        except ValueError:
            continue
        if age > days:
            continue
        _, note = _classify(c.name)
        summary = (
            f"Sponsor {c.name}; interventions: {'; '.join(sorted(c.interventions)[:5])}; "
            f"conditions: {'; '.join(sorted(c.conditions)[:3])}; "
            f"active phases: {'; '.join(sorted(c.active_phases)) or 'n/a'}; "
            f"status: {'/'.join(sorted(c.statuses & ACTIVE_STATUSES))}"
        )
        items.append(
            make_item(
                url=f"https://clinicaltrials.gov/study/{c.active_nct}" if c.active_nct else "",
                title=f"{c.name}: active clinical-trial update",
                content=summary + (f" [{note}]" if note else ""),
                published_date=c.last_active_update[:10],
                seed_id=f"CTGOV-{re.sub(r'[^a-z0-9]+', '-', c.matched_query.lower()).strip('-')}",
                query=c.matched_query,
                signal_type="program",
                days=days,
                known_company=c.name,
            )
        )
    return items
