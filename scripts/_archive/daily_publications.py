"""Discover non-repeating commercial antibody/protein signals from Europe PMC."""

from __future__ import annotations

import csv
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests

from intent_pipeline.suppression import company_root
from intent_pipeline.suppression import contains as is_suppressed
from intent_pipeline.suppression import load as load_suppression

OUT = Path(__file__).resolve().parent / "output"
OUTPUT = OUT / "daily_publication_candidates.csv"

START_DATE = "2025-07-24"
END_DATE = "2026-07-24"

TERMS = [
    '"bispecific antibody"',
    '"multispecific antibody"',
    "nanobody",
    '"antibody engineering"',
    '"antibody humanization"',
    '"affinity maturation"',
    '"antibody developability"',
    '"antibody-drug conjugate"',
    '"T cell engager"',
    "immunocytokine",
    '"therapeutic protein engineering"',
]

COMPANY_WORD = re.compile(
    r"\b(Therapeutics?|Biotherapeutics?|Biosciences?|Biotech(?:nology)?|"
    r"Pharmaceuticals?|Pharma|Biologics?|BioMed|Bio\b|Inc\.?|LLC|Ltd\.?|"
    r"Limited|GmbH|Corporation|Corp\.?|S\.?A\.?|A\.?G\.?)\b",
    re.I,
)
LEGAL_ONLY = re.compile(r"^(Inc\.?|LLC|Ltd\.?|Limited|GmbH|Corporation|Corp\.?|S\.?A\.?|A\.?G\.?)$", re.I)
LEGAL_CUT = re.compile(
    r"^(.{2,100}?\b(?:Inc\.?|LLC|Ltd\.?|Limited|GmbH|Corporation|Corp\.?|"
    r"Co\.?\s*,?\s*Ltd\.?|A\.?G\.?|S\.?A\.?|a\.s\.))\b",
    re.I,
)
SECTOR_CUT = re.compile(
    r"^(.{2,100}?\b(?:Therapeutics?|Biotherapeutics?|Biosciences?|"
    r"Biotech(?:nology)?|Pharmaceuticals?|Pharma|Biologics?|BioMed))\b",
    re.I,
)
ACADEMIC = re.compile(
    r"university|college|hospital|school of|institute|institut\b|academy|"
    r"medical center|medical centre|foundation|department of|laboratory of|"
    r"national center|national centre|ministry|clinic\b",
    re.I,
)
ORG_NOISE = re.compile(
    r"department|\bdept\b|research and development|research & development|laborator|"
    r"\bcenter\b|\bcentre\b|medical communications|therapeutic area|"
    r"strategy and innovation|manufacturing|clinical research|research group|"
    r"contract research|analytical research|process research|product research",
    re.I,
)
KNOWN_NON_NEW_OR_SERVICE = re.compile(
    r"pfizer|merck|abbvie|boehringer|chugai|roche|hoffmann|gilead|amgen|"
    r"regeneron|sanofi|moderna|bristol|astrazeneca|janssen|novartis|"
    r"eli lilly|takeda|astellas|bayer|gsk|glaxosmithkline|genentech|"
    r"wuxi|evotec|omniab|acrobiosystems|certara|nanotag|pinnacle research|"
    r"smobio|fairjourney|mosaic biosciences|o'brien|piha-paul|rodriguez-aponte|"
    r"\bhill ag\b|\bhamilton ag\b|mercy llc|healthcare global|medizinische hochschule|"
    r"q-pharm|syngene|precede biosciences|smart-nuclide|\bnj bio\b|"
    r"analytical biosciences|bioqual|microcrispr|x unfold|catalent|stratifyer|"
    r"ningbo dilato materials|koreavaccine|life edit|therapeutics discovery product|"
    r"biologics drug discovery|biologics engineering",
    re.I,
)
NOISE = re.compile(
    r"diagnostic|assay|biosimilar|manufacturing|production platform|"
    r"research reagent|review|position statement|comparison of|outcomes and impact|"
    r"practice in|workflow|biomarker|supplementary|case report|real-world|"
    r"meta-analysis|corrigendum|FDA TIDES|antibodies to watch|market|"
    r"veterinary|broiler|sensor|detection|COVID-19 test",
    re.I,
)
MODALITY = re.compile(
    r"bispecific|multispecific|nanobody|\bVHH\b|\bscFv\b|antibody|"
    r"immunocytokine|T[- ]cell engager|therapeutic protein",
    re.I,
)
DEVELOPMENT_ACTIVITY = re.compile(
    r"novel|engineer|develop|design|preclinical|first-in-human|phase [Ii1-3]|"
    r"clinical trial|therapeutic efficacy|antitumor|anti-tumor|candidate|"
    r"discovery|optimization|maturation|humanized|targeting|potent|IND-enabling",
    re.I,
)


def company_from_affiliation(affiliation: str) -> str:
    if (
        not affiliation
        or ACADEMIC.search(affiliation)
        or ORG_NOISE.search(affiliation)
        or KNOWN_NON_NEW_OR_SERVICE.search(affiliation)
    ):
        return ""
    parts = [part.strip(" .") for part in re.split(r"[,;]", affiliation) if part.strip()]
    for index, part in enumerate(parts):
        if not COMPANY_WORD.search(part):
            continue
        if LEGAL_ONLY.match(part) and index:
            candidate = f"{parts[index - 1]} {part}"
        else:
            candidate = part
        cut = LEGAL_CUT.match(candidate) or SECTOR_CUT.match(candidate)
        if cut:
            candidate = cut.group(1)
        candidate = re.sub(r"\s+", " ", candidate).strip(" .,-")
        if (
            3 <= len(candidate) <= 100
            and not ACADEMIC.search(candidate)
            and not ORG_NOISE.search(candidate)
            and not KNOWN_NON_NEW_OR_SERVICE.search(candidate)
            and candidate.lower() not in {"bioscience", "biotech", "biotechnology", "pharma", "biologics"}
            and not re.match(r"^[A-Z][a-z]+ S\.?A\.?$", candidate)
        ):
            return candidate
    return ""


def affiliations(result: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for author in (result.get("authorList") or {}).get("author", []) or []:
        details = (author.get("authorAffiliationDetailsList") or {}).get(
            "authorAffiliation", []
        ) or []
        for detail in details:
            value = detail.get("affiliation") or ""
            if value:
                found.append(value)
    first = result.get("authorString") or ""
    if first:
        found.append(first)
    return found


def search(session: requests.Session, term: str) -> list[dict[str, Any]]:
    query = (
        f'FIRST_PDATE:[{START_DATE} TO {END_DATE}] AND '
        f'TITLE_ABS:{term} AND (LANG:"eng" OR LANG:"en")'
    )
    response = session.get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={
            "query": query,
            "format": "json",
            "resultType": "core",
            "pageSize": 1000,
        },
        timeout=(10, 60),
    )
    response.raise_for_status()
    return (response.json().get("resultList") or {}).get("result", []) or []


def source_url(result: dict[str, Any]) -> str:
    if result.get("pmcid"):
        return f"https://europepmc.org/article/PMC/{result['pmcid']}"
    if result.get("pmid"):
        return f"https://europepmc.org/article/MED/{result['pmid']}"
    if result.get("doi"):
        return f"https://doi.org/{result['doi']}"
    return ""


def main() -> int:
    session = requests.Session()
    session.headers["User-Agent"] = "antibody-intent-research/1.0"
    known = load_suppression()
    by_company: dict[str, dict[str, Any]] = {}

    for index, term in enumerate(TERMS, 1):
        try:
            results = search(session, term)
        except requests.RequestException as exc:
            print(f"{index:02}/{len(TERMS)} failed {term}: {exc}")
            continue
        accepted = 0
        for result in results:
            title = (result.get("title") or "").strip()
            abstract = (result.get("abstractText") or "").strip()
            if (
                not title
                or NOISE.search(title)
                or not MODALITY.search(f"{title} {abstract}")
                or not DEVELOPMENT_ACTIVITY.search(title)
            ):
                continue
            published = (
                result.get("firstPublicationDate")
                or result.get("electronicPublicationDate")
                or result.get("journalInfo", {}).get("printPublicationDate")
                or ""
            )[:10]
            url = source_url(result)
            if not url:
                continue
            for affiliation in affiliations(result):
                company = company_from_affiliation(affiliation)
                if not company:
                    continue
                key = company_root(company)
                if not key or is_suppressed(known, key=key, name=company):
                    continue
                existing = by_company.get(key)
                modality_in_title = bool(MODALITY.search(title))
                scientific_fit = 14 if modality_in_title else 11
                confidence = 4 if modality_in_title else 3
                total_score = scientific_fit + 12 + 5 + 3 + confidence
                row = {
                    "Original Dataset Priority": "New",
                    "Corrected Status": "Review",
                    "Current Company Name": company,
                    "Company Website": "",
                    "Headquarters": "",
                    "Company Type / Ownership": "Commercial author affiliation; asset ownership unverified",
                    "Therapeutic Asset or Program": "",
                    "Biological Target": "",
                    "Disease / Indication": "",
                    "Confirmed Modality": term.strip('"'),
                    "Current Program Stage": "",
                    "Trigger Type": "scientific publication",
                    "Signal Date": published,
                    "Signal Summary": title,
                    "Original Trigger Source URL": url,
                    "Company / Pipeline Source URL": "",
                    "Asset Ownership Evidence": f"Commercial affiliation: {affiliation[:300]}",
                    "Scientific / Development Requirement": "",
                    "Evidence for Requirement": "",
                    "Direct Project Hypothesis": "",
                    "Proposed Pilot / Project Type": "",
                    "Budget / Purchase-Likelihood Evidence": "Current company-affiliated scientific activity",
                    "Validation Capacity": "Company-affiliated publication authors",
                    "Competitor / Service-Provider Check": "Requires company-site verification",
                    "Hard Exclusion Result": "No affiliation-name exclusion matched",
                    "Scientific Fit (25)": scientific_fit,
                    "Intent & Timing (25)": 12,
                    "Project Clarity (20)": 5,
                    "Budget (15)": 3,
                    "Data Confidence (5)": confidence,
                    "Total Score": total_score,
                    "Final Decision Reason": (
                        "Current commercial-affiliated antibody/protein publication; "
                        "Review until therapeutic ownership and program linkage are confirmed."
                    ),
                    "Missing Fact / Next Verification": (
                        "Confirm current company website, exact owned therapeutic asset, "
                        "program stage, and a source-supported scientific bottleneck."
                    ),
                    "Verification Date": date.today().isoformat(),
                    "Research Notes": f"Europe PMC query {term}; journal: {result.get('journalTitle', '')}",
                    "_company_key": key,
                    "_evidence_count": 1,
                    "_raw_evidence_text": abstract[:500],
                    "_title_modality": "Yes" if modality_in_title else "No",
                }
                if not existing or published > existing["Signal Date"]:
                    by_company[key] = row
                elif existing:
                    existing["_evidence_count"] += 1
                accepted += 1
        print(f"{index:02}/{len(TERMS)} {term:32} {len(results):4} papers -> {accepted:3} affiliations")
        time.sleep(0.1)

    rows = sorted(
        by_company.values(),
        key=lambda row: (
            row["_title_modality"] == "Yes",
            row["Signal Date"],
            row["_evidence_count"],
            row["Current Company Name"],
        ),
        reverse=True,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    if rows:
        with OUTPUT.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    else:
        OUTPUT.write_text("", encoding="utf-8")
    print(f"{len(rows)} non-repeating publication candidates -> {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
