"""Company universe enumeration from public registries.

Search discovers companies twelve at a time and most results resolve to nobody.
Registries are the opposite: ClinicalTrials.gov returns hundreds of records per call
and every one names its sponsor. That makes enumeration the cheap way to reach
thousands of companies, and leaves search to do what it is actually good at —
detecting that something changed.

This module builds the universe. Intent scoring runs on top of it.

    python -m intent_pipeline.universe --pages 30
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import requests

CTGOV = "https://clinicaltrials.gov/api/v2/studies"
OUT = Path(__file__).resolve().parent.parent / "output"
UNIVERSE_CSV = OUT / "company_universe.csv"

# Intervention queries. Each is a separate sweep; sponsors accumulate across them.
INTERVENTION_QUERIES = [
    "antibody",
    "monoclonal antibody",
    "bispecific antibody",
    "antibody drug conjugate",
    "nanobody",
    "fusion protein",
    "recombinant protein",
]

# Sponsor names that are never the buyer, matched on the name itself. The text-based
# exclusions in gates.py cannot help here — a registry gives a name, not a page.
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

# Very large pharma. Kept, but flagged: SOP page 14 says account-based only, targeting a
# named discovery unit rather than the whole company.
BIG_PHARMA = {
    "pfizer", "merck", "novartis", "roche", "genentech", "astrazeneca", "sanofi",
    "gsk", "glaxosmithkline", "johnson", "janssen", "abbvie", "abbott", "amgen",
    "bristol", "eli lilly", "lilly", "bayer", "boehringer", "takeda", "novo nordisk",
    "gilead", "biogen", "regeneron", "moderna", "daiichi", "astellas", "eisai",
}

_LEGAL = re.compile(
    r"[,\s]+(inc|llc|ltd|limited|corp|corporation|co|plc|gmbh|ag|ab|a\.?s|sa|s\.a\.?|"
    r"nv|bv|pte|pty|aps|oy|srl|s\.r\.l\.?|kk|k\.k\.?|holdings?|group)\.?$",
    re.I,
)


# Registry states that mean the program is live rather than finished.
ACTIVE_STATUSES = {
    "RECRUITING",
    "NOT_YET_RECRUITING",
    "ENROLLING_BY_INVITATION",
    "ACTIVE_NOT_RECRUITING",
}


@dataclass
class Company:
    name: str
    nct_ids: list[str] = field(default_factory=list)
    phases: set[str] = field(default_factory=set)
    conditions: set[str] = field(default_factory=set)
    interventions: set[str] = field(default_factory=set)
    statuses: set[str] = field(default_factory=set)
    last_update: str = ""
    # The date that actually carries intent: the newest update on a trial that is
    # still live. A 2019 update on a completed study says nothing about buying now.
    last_active_update: str = ""
    active_nct: str = ""
    active_phases: set[str] = field(default_factory=set)
    matched_queries: set[str] = field(default_factory=set)

    @property
    def key(self) -> str:
        n = _LEGAL.sub("", self.name).strip().lower()
        return re.sub(r"[^a-z0-9]", "", n)


def _classify(name: str) -> tuple[bool, str]:
    """Return (keep, note)."""
    if SPONSOR_EXCLUDE.search(name):
        return False, "academic or hospital sponsor"
    if CRO_EXCLUDE.search(name):
        return False, "service provider name"
    low = name.lower()
    for big in BIG_PHARMA:
        if big in low:
            return True, "large pharma — account-based only (SOP p14)"
    return True, ""


def sweep(
    session: requests.Session, query: str, max_pages: int, page_size: int = 200
) -> Iterator[dict[str, Any]]:
    """Page through one intervention query."""
    token = None
    for page in range(max_pages):
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

        for attempt in range(3):
            try:
                r = session.get(CTGOV, params=params, timeout=90)
                r.raise_for_status()
                data = r.json()
                break
            except Exception:
                if attempt == 2:
                    return
                time.sleep(2 ** attempt)
        else:
            return

        for study in data.get("studies", []):
            yield study

        token = data.get("nextPageToken")
        if not token:
            return
        time.sleep(0.2)


def build(max_pages: int, queries: list[str] | None = None) -> dict[str, Company]:
    session = requests.Session()
    session.headers["User-Agent"] = "antibody-prospecting/0.1"
    companies: dict[str, Company] = {}

    for query in queries or INTERVENTION_QUERIES:
        seen_before = len(companies)
        studies = 0
        for study in sweep(session, query, max_pages):
            studies += 1
            proto = study.get("protocolSection", {})
            sponsors = proto.get("sponsorCollaboratorsModule", {})
            lead = sponsors.get("leadSponsor") or {}
            if lead.get("class") != "INDUSTRY":
                continue
            name = (lead.get("name") or "").strip()
            if not name:
                continue

            keep, _ = _classify(name)
            if not keep:
                continue

            status = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            key = re.sub(r"[^a-z0-9]", "", _LEGAL.sub("", name).strip().lower())
            if not key:
                continue

            company = companies.setdefault(key, Company(name=name))
            nct = proto.get("identificationModule", {}).get("nctId", "")
            if nct and len(company.nct_ids) < 25:
                company.nct_ids.append(nct)
            company.phases.update(design.get("phases") or [])
            company.conditions.update((proto.get("conditionsModule", {}).get("conditions") or [])[:5])
            for iv in (proto.get("armsInterventionsModule", {}).get("interventions") or [])[:5]:
                if iv.get("name"):
                    company.interventions.add(iv["name"][:60])
            overall = status.get("overallStatus") or ""
            if overall:
                company.statuses.add(overall)

            # v2 returns a plain string here, not a {date, type} struct.
            updated = status.get("lastUpdateSubmitDate") or (
                status.get("lastUpdatePostDateStruct") or {}
            ).get("date", "")
            if updated > company.last_update:
                company.last_update = updated

            if overall in ACTIVE_STATUSES:
                phases = design.get("phases") or []
                company.active_phases.update(phases)
                if updated > company.last_active_update:
                    company.last_active_update = updated
                    company.active_nct = nct

            company.matched_queries.add(query)

        print(
            f"  {query:26} {studies:5} studies  ->  "
            f"{len(companies) - seen_before:4} new companies  (total {len(companies)})"
        )

    return companies


def save(companies: dict[str, Company]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for company in companies.values():
        _, note = _classify(company.name)
        rows.append(
            {
                "company_key": company.key,
                "canonical_company": company.name,
                "trial_count": len(company.nct_ids),
                "phases": "; ".join(sorted(company.phases)),
                "statuses": "; ".join(sorted(company.statuses)),
                "conditions": "; ".join(sorted(company.conditions)[:6]),
                "interventions": "; ".join(sorted(company.interventions)[:6]),
                "last_registry_update": company.last_update,
                "last_active_update": company.last_active_update,
                "active_nct": company.active_nct,
                "active_phases": "; ".join(sorted(company.active_phases)),
                "matched_queries": "; ".join(sorted(company.matched_queries)),
                "nct_ids": "; ".join(company.nct_ids[:10]),
                "note": note,
                "source": "clinicaltrials.gov",
            }
        )

    rows.sort(key=lambda r: (-r["trial_count"], r["canonical_company"]))
    with UNIVERSE_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["company_key"])
        writer.writeheader()
        writer.writerows(rows)
    return UNIVERSE_CSV


def load() -> list[dict[str, str]]:
    if not UNIVERSE_CSV.exists():
        return []
    with UNIVERSE_CSV.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    parser = argparse.ArgumentParser(description="Enumerate the company universe")
    parser.add_argument("--pages", type=int, default=20, help="Max pages per query (200 studies each)")
    parser.add_argument("--queries", default="", help="Comma-separated subset of intervention queries")
    args = parser.parse_args()

    queries = [q.strip() for q in args.queries.split(",") if q.strip()] or None
    print(f"Enumerating company universe (up to {args.pages} pages x 200 studies per query)\n")

    companies = build(args.pages, queries)
    if not companies:
        print("No companies found.")
        return 1

    path = save(companies)
    multi = sum(1 for c in companies.values() if len(c.nct_ids) > 1)
    print(f"\n{len(companies)} unique companies -> {path}")
    print(f"  {multi} have more than one registered trial")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
