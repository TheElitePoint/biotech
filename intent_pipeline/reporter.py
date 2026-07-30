"""NIH RePORTER as a free, live intent + enumeration source.

Why this exists: Tavily is rate-limited and ClinicalTrials.gov over-represents large
pharma. RePORTER's SBIR/STTR awards are, by eligibility rule, small businesses (<500
staff) — exactly the seed-to-Series-B ICP the SOP targets. Better still, an award
carries a *date and a dollar amount*, so it is a genuine dated capital trigger
(SOP page 17), not mere program-liveness.

No API key. No cache dependency — every call is live.

    python -m intent_pipeline.reporter --years 2024 2025 2026
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

import requests

API = "https://api.reporter.nih.gov/v2/projects/search"
OUT = Path(__file__).resolve().parent.parent / "output"
REPORTER_CSV = OUT / "reporter_companies.csv"

# SBIR/STTR = small-business set-aside grants. This is the ICP filter, for free.
SBIR_CODES = ["R43", "R44", "R41", "R42"]

TEXT_QUERIES = [
    "antibody",
    "monoclonal antibody",
    "bispecific",
    "nanobody",
    "VHH",
    "scFv",
    "multispecific antibody",
    "antibody fragment",
    "protein engineering",
    "antibody discovery",
    "affinity maturation",
    "protein design",
    "therapeutic protein",
    "protein therapeutic",
    "Fc fusion",
    "immunocytokine",
    "cytokine engineering",
    "de novo protein",
]

# Same non-buyer name filter as the trial universe.
EXCLUDE_NAME = re.compile(
    r"\b(university|universit|college|school of|institut|hospital|clinic|"
    r"health system|foundation|trust|regents|board of|research foundation)\b",
    re.I,
)

_LEGAL = re.compile(
    r"[,\s]+(inc|llc|ltd|limited|corp|corporation|co|plc|gmbh|ag|ab|sa|nv|bv|"
    r"pte|pty|holdings?|group)\.?$",
    re.I,
)


@dataclass
class Award:
    name: str
    latest_date: str = ""
    latest_title: str = ""
    latest_amount: int = 0
    latest_code: str = ""
    total_amount: int = 0
    award_count: int = 0
    city: str = ""
    state: str = ""
    project_url: str = ""
    is_active: bool = False
    queries: set[str] = field(default_factory=set)

    @property
    def key(self) -> str:
        n = _LEGAL.sub("", self.name).strip().lower()
        return re.sub(r"[^a-z0-9]", "", n)


def _search(session: requests.Session, text: str, years: list[int], offset: int) -> dict[str, Any]:
    body = {
        "criteria": {
            "advanced_text_search": {
                "operator": "and",
                "search_field": "projecttitle,abstracttext,terms",
                "search_text": text,
            },
            "activity_codes": SBIR_CODES,
            "fiscal_years": years,
        },
        # No include_fields: specifying it flattens the response and drops the nested
        # organization block we need for the company name.
        "offset": offset,
        "limit": 500,
        "sort_field": "award_notice_date",
        "sort_order": "desc",
    }
    for attempt in range(3):
        try:
            r = session.post(API, json=body, timeout=(10, 40))
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 2:
                return {}
            time.sleep(2 * (attempt + 1))
    return {}


def sweep(session: requests.Session, text: str, years: list[int]) -> Iterator[dict[str, Any]]:
    offset = 0
    while True:
        data = _search(session, text, years, offset)
        results = data.get("results", [])
        if not results:
            return
        for row in results:
            yield row
        total = data.get("meta", {}).get("total", 0)
        offset += len(results)
        if offset >= total or offset >= 2000:  # API caps deep paging
            return
        time.sleep(0.3)


def build(years: list[int], queries: list[str] | None = None) -> dict[str, Award]:
    session = requests.Session()
    session.headers["User-Agent"] = "antibody-prospecting/0.1"
    companies: dict[str, Award] = {}

    for text in queries or TEXT_QUERIES:
        before = len(companies)
        count = 0
        for row in sweep(session, text, years):
            count += 1
            org = row.get("organization") or {}
            name = (org.get("org_name") or "").strip()
            if not name or EXCLUDE_NAME.search(name):
                continue

            key = re.sub(r"[^a-z0-9]", "", _LEGAL.sub("", name).strip().lower())
            if not key:
                continue
            company = companies.setdefault(key, Award(name=name.title()))

            award_date = (row.get("award_notice_date") or "")[:10]
            amount = int(row.get("award_amount") or 0)
            company.award_count += 1
            company.total_amount += amount
            company.queries.add(text)
            if row.get("is_active"):
                company.is_active = True
            if award_date > company.latest_date:
                company.latest_date = award_date
                company.latest_title = (row.get("project_title") or "")[:120]
                company.latest_amount = amount
                company.latest_code = row.get("activity_code") or ""
                company.project_url = row.get("project_detail_url") or ""
                company.city = org.get("org_city") or ""
                company.state = org.get("org_state") or ""

        print(f"  {text:24} {count:5} awards  ->  {len(companies) - before:4} new  (total {len(companies)})")

    return companies


def save(companies: dict[str, Award]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in companies.values():
        rows.append({
            "company_key": c.key,
            "canonical_company": c.name,
            "latest_award_date": c.latest_date,
            "latest_award_amount": c.latest_amount,
            "total_award_amount": c.total_amount,
            "award_count": c.award_count,
            "activity_code": c.latest_code,
            "is_active": c.is_active,
            "location": f"{c.city}, {c.state}".strip(", "),
            "latest_project": c.latest_title,
            "matched_queries": "; ".join(sorted(c.queries)),
            "project_url": c.project_url,
        })
    rows.sort(key=lambda r: r["latest_award_date"], reverse=True)
    with REPORTER_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["company_key"])
        w.writeheader()
        w.writerows(rows)
    return REPORTER_CSV


def load() -> list[dict[str, str]]:
    if not REPORTER_CSV.exists():
        return []
    with REPORTER_CSV.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    parser = argparse.ArgumentParser(description="Enumerate SBIR/STTR antibody companies")
    parser.add_argument("--years", type=int, nargs="+", default=[2024, 2025, 2026])
    args = parser.parse_args()

    print(f"NIH RePORTER SBIR/STTR sweep, fiscal years {args.years}\n")
    companies = build(args.years)
    if not companies:
        print("No companies found.")
        return 1
    path = save(companies)
    active = sum(1 for c in companies.values() if c.is_active)
    print(f"\n{len(companies)} small-business companies -> {path}")
    print(f"  {active} with a currently active award")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
