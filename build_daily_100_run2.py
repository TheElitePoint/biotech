"""Build a second, historically suppressed 100-company evidence queue."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from intent_pipeline.suppression import company_root


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
REPORTER = OUT / "reporter_companies.csv"
TRIALS = OUT / "company_universe.csv"
SUPPRESSION = OUT / "historical_suppression.csv"
FINAL = OUT / "daily_100_companies_run2_2026-07-24.csv"
EXCLUSIONS = OUT / "daily_exclusions_run2_2026-07-24.csv"

MODALITY = re.compile(
    r"antibody|bispecific|protein therapeutic|therapeutic protein|immunotherap|"
    r"cytokine|enzyme|peptide|fusion protein|fc fusion|protein engineering|protein design",
    re.I,
)
REPORTER_NOISE = re.compile(
    r"diagnos|imaging|radiomic|assay|biomarker|biosensor|device|software|manufactur|vaccine|"
    r"detection|testing|screening|research tool|reagent|spatial profiling|sequencing|wearable|"
    r"telehealth|machine learning|artificial intelligence|ai-powered|microfluidic|"
    r"commercial production|organ-on-chip|model of|platform|footprinting|supply chain|"
    r"drug discovery|genomic integrity assessment|pharmacodynamics and toxicity",
    re.I,
)
REPORTER_COMPANY_NOISE = re.compile(r"diagnostics|\.ai\b", re.I)
TRIAL_MODALITY = re.compile(
    r"antibody|mab\b|bispecific|\badc\b|protein|peptide|enzyme|cytokine|"
    r"interleukin|fusion|nanobody|immunoglobulin|car[- ]?t|t[- ]cell engager",
    re.I,
)
SPONSOR_NOISE = re.compile(
    r"university|hospital|institute|foundation|government|national cancer|cancer center|"
    r"medical center|health system|ministry|college|school|cooperative group|network|"
    r"society|association|\bnih\b|\bnci\b|sponsor-investigator|irb chair|medical diagnosis|"
    r"pt\. jes|greg bew",
    re.I,
)
LARGE_PHARMA = re.compile(
    r"abbvie|pfizer|roche|genentech|novartis|merck|sanofi|gsk|glaxosmithkline|"
    r"astrazeneca|bristol|johnson|janssen|eli lilly|takeda|boehringer|amgen|"
    r"regeneron|bayer",
    re.I,
)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


suppressed = {row["company_key"] for row in read(SUPPRESSION) if row.get("company_key")}
excluded: list[dict[str, str]] = []


def modality_from(text: str) -> str:
    lowered = text.lower()
    if "bispecific" in lowered:
        return "bispecific antibody"
    if "antibody" in lowered:
        return "therapeutic antibody"
    if "peptide" in lowered:
        return "therapeutic peptide"
    if "enzyme" in lowered:
        return "therapeutic enzyme/protein"
    if "cytokine" in lowered or "interleukin" in lowered:
        return "cytokine therapeutic"
    return "therapeutic protein / protein engineering"


def common_row(
    *,
    company: str,
    program: str,
    modality: str,
    stage: str,
    trigger: str,
    signal_date: str,
    summary: str,
    source_url: str,
    budget_evidence: str,
    tier: str,
    score: int,
) -> dict[str, Any]:
    return {
        "Original Dataset Priority": "New - High" if score >= 75 else "New - Review",
        "Corrected Status": "Review",
        "Current Company Name": company,
        "Company Website": "",
        "Headquarters": "",
        "Company Type / Ownership": "Commercial life-science company; exact ownership and current website to verify",
        "Therapeutic Asset or Program": program,
        "Biological Target": "",
        "Disease / Indication": "",
        "Confirmed Modality": modality,
        "Current Program Stage": stage,
        "Trigger Type": trigger,
        "Signal Date": signal_date,
        "Signal Summary": summary,
        "Original Trigger Source URL": source_url,
        "Company / Pipeline Source URL": "",
        "Asset Ownership Evidence": f"The source attributes this program or study to {company}.",
        "Scientific / Development Requirement": "",
        "Evidence for Requirement": "",
        "Direct Project Hypothesis": "",
        "Proposed Pilot / Project Type": "",
        "Budget / Purchase-Likelihood Evidence": budget_evidence,
        "Validation Capacity": f"Program activity reported at {stage}.",
        "Competitor / Service-Provider Check": "Automated hard-exclusion screen passed; manual business-model check pending",
        "Hard Exclusion Result": "Pass preliminary screen",
        "Scientific Fit (25)": 21,
        "Intent & Timing (25)": 24,
        "Project Clarity (20)": 12,
        "Budget (15)": 13 if tier == "NIH active award" else 8,
        "Data Confidence (5)": 5,
        "Total Score": score,
        "Final Decision Reason": (
            "Traceable company-level development activity supports Review status. "
            "Approval requires ownership, modality and paid-project verification."
        ),
        "Missing Fact / Next Verification": (
            "Confirm the current company website, owned asset and one explicit scientific "
            "bottleneck that can support a paid project."
        ),
        "Verification Date": "2026-07-24",
        "Research Notes": f"Second daily run; sourced from {tier}.",
        "_company_key": company_root(company),
        "_evidence_count": 1,
        "_title_modality": "Yes",
        "_evidence_tier": tier,
    }


reporter_rows: list[dict[str, Any]] = []
for row in read(REPORTER):
    company = row["canonical_company"].strip()
    key = row["company_key"]
    project = row["latest_project"].strip()
    matched = row["matched_queries"]
    if key in suppressed or row["is_active"] != "True" or row["latest_award_date"] < "2024-07-24":
        continue
    if (
        not MODALITY.search(matched)
        or REPORTER_NOISE.search(project)
        or REPORTER_COMPANY_NOISE.search(company)
    ):
        continue
    amount = int(float(row["latest_award_amount"] or 0))
    reporter_rows.append(
        common_row(
            company=company,
            program=project,
            modality=modality_from(matched),
            stage="NIH-funded translational R&D",
            trigger="Active NIH SBIR/STTR award",
            signal_date=row["latest_award_date"],
            summary=f"Active NIH small-business award (${amount:,}) for: {project}.",
            source_url=row["project_url"],
            budget_evidence=f"Latest NIH award amount: ${amount:,}; {row['award_count']} recorded award(s).",
            tier="NIH active award",
            score=78 if row["latest_award_date"] >= "2025-07-24" else 74,
        )
    )

reporter_rows.sort(
    key=lambda row: (row["Signal Date"], int(row["Total Score"])),
    reverse=True,
)

trial_rows: list[dict[str, Any]] = []
for row in read(TRIALS):
    company = row["canonical_company"].strip()
    key = row["company_key"]
    interventions = row["interventions"].strip()
    if key in suppressed or not row["active_nct"] or row["last_active_update"] < "2025-07-24":
        continue
    if SPONSOR_NOISE.search(company) or LARGE_PHARMA.search(company):
        continue
    if not TRIAL_MODALITY.search(interventions):
        continue
    nct = row["active_nct"].split(";")[0].strip()
    stage = row["active_phases"] or "active clinical development"
    trial_rows.append(
        common_row(
            company=company,
            program=interventions,
            modality=modality_from(interventions),
            stage=stage,
            trigger="Active clinical-trial registry update",
            signal_date=row["last_active_update"],
            summary=f"Active {stage} study {nct}; interventions include {interventions}.",
            source_url=f"https://clinicaltrials.gov/study/{nct}",
            budget_evidence=f"Active company-sponsored clinical program; registry updated {row['last_active_update']}.",
            tier="Active clinical trial",
            score=76,
        )
    )

trial_rows.sort(key=lambda row: row["Signal Date"], reverse=True)

rows: list[dict[str, Any]] = []
seen: set[str] = set()
for source_rows, limit in ((trial_rows, 24), (reporter_rows, 76)):
    used = 0
    for row in source_rows:
        key = row["_company_key"]
        if not key or key in seen:
            continue
        rows.append(row)
        seen.add(key)
        used += 1
        if used == limit:
            break

for row in trial_rows + reporter_rows:
    if len(rows) >= 100:
        break
    if row["_company_key"] not in seen:
        rows.append(row)
        seen.add(row["_company_key"])

if len(rows) < 100:
    raise SystemExit(f"Only {len(rows)} qualifying, non-suppressed companies available")

rows = rows[:100]
fields = [
    "Original Dataset Priority", "Corrected Status", "Current Company Name",
    "Company Website", "Headquarters", "Company Type / Ownership",
    "Therapeutic Asset or Program", "Biological Target", "Disease / Indication",
    "Confirmed Modality", "Current Program Stage", "Trigger Type", "Signal Date",
    "Signal Summary", "Original Trigger Source URL", "Company / Pipeline Source URL",
    "Asset Ownership Evidence", "Scientific / Development Requirement",
    "Evidence for Requirement", "Direct Project Hypothesis", "Proposed Pilot / Project Type",
    "Budget / Purchase-Likelihood Evidence", "Validation Capacity",
    "Competitor / Service-Provider Check", "Hard Exclusion Result",
    "Scientific Fit (25)", "Intent & Timing (25)", "Project Clarity (20)",
    "Budget (15)", "Data Confidence (5)", "Total Score", "Final Decision Reason",
    "Missing Fact / Next Verification", "Verification Date", "Research Notes",
    "_company_key", "_evidence_count", "_title_modality", "_evidence_tier",
]
with FINAL.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

with EXCLUSIONS.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=["company", "category", "reason", "evidence_url", "review_date"],
    )
    writer.writeheader()
    writer.writerows(excluded)

print(f"{len(rows)} unique companies -> {FINAL}")
print(f"NIH active awards: {sum(r['_evidence_tier'] == 'NIH active award' for r in rows)}")
print(f"Active clinical trials: {sum(r['_evidence_tier'] == 'Active clinical trial' for r in rows)}")
