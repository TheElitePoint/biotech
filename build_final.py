"""Combine free live sources into the final company list. No Tavily.

Two independent, freshly-collected sources:

  ClinicalTrials.gov  -> program intent (a live trial touched in the window)
  NIH RePORTER SBIR   -> capital intent (a dated small-business grant award)

RePORTER supplies the seed-to-Series-B ICP that trials miss; ClinicalTrials.gov
supplies the mid/large asset owners. A company appearing in both carries two
independent triggers and scores highest (SOP page 79).

    python -m intent_pipeline.reporter          # refresh RePORTER first
    python -m intent_pipeline.universe          # refresh CTgov first
    python build_final.py
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from intent_pipeline import reporter, universe, universe_intent as ui

OUT = Path(__file__).resolve().parent / "output"
WINDOW_DAYS = 365


def _recency(signal_date: str) -> float:
    try:
        age = (date.today() - datetime.strptime(signal_date[:10], "%Y-%m-%d").date()).days
    except (ValueError, TypeError):
        return 0.5
    if age <= 30:
        return 1.0
    if age <= 90:
        return 0.85
    if age <= 180:
        return 0.65
    if age <= 365:
        return 0.4
    return 0.15


def reporter_intent(row: dict[str, str]) -> dict | None:
    """A dated SBIR/STTR award is a capital trigger (SOP page 17)."""
    when = (row.get("latest_award_date") or "").strip()
    if not when:
        return None
    try:
        age = (date.today() - datetime.strptime(when[:10], "%Y-%m-%d").date()).days
    except ValueError:
        return None
    if age > WINDOW_DAYS:
        return None
    amt = int(row.get("latest_award_amount") or 0)
    code = row.get("activity_code") or ""
    return {
        "trigger": "reporter",
        "signal_type": "capital",
        "signal_date": when[:10],
        "age_days": age,
        "early_phase": False,
        "evidence": f"SBIR/STTR {code} ${amt:,} awarded {when[:10]}: {row.get('latest_project', '')[:90]}",
        "evidence_url": row.get("project_url", ""),
    }


def score_reporter(row: dict[str, str], intent: dict) -> tuple[int, str]:
    text = f"{row.get('matched_queries','')} {row.get('latest_project','')}".lower()
    is_antibody = any(t in text for t in ("antibody", "bispecific", "nanobody", "scfv"))
    is_protein = "protein" in text

    fit = 12 if (is_antibody or is_protein) else 6
    fit += 6  # SBIR recipients are, by rule, small active companies (ICP)

    recency = _recency(intent["signal_date"])
    intent_score = round(25 * 1.0 * recency)  # capital = strength 1.0

    amt = int(row.get("latest_award_amount") or 0)
    awards = int(row.get("award_count") or 1)
    budget = min(15, 6 + (4 if amt >= 1_000_000 else 2) + min(awards, 3))
    clarity = 12  # named program + funded objective
    buyer = 6
    confidence = 5  # first-party government award record

    total = min(fit, 25) + intent_score + min(clarity, 20) + budget + buyer + confidence
    modality = "antibody" if is_antibody else "engineered protein" if is_protein else ""
    return total, modality


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    uni = {r["company_key"]: r for r in universe.load()}
    rep = {r["company_key"]: r for r in reporter.load()}
    if not uni and not rep:
        raise SystemExit("No sources found. Run universe and reporter first.")

    print(f"Sources: {len(uni)} trial companies, {len(rep)} SBIR companies")

    records: dict[str, dict] = {}

    # RePORTER capital intent (the ICP core).
    for key, row in rep.items():
        intent = reporter_intent(row)
        if not intent:
            continue
        total, modality = score_reporter(row, intent)
        records[key] = {
            "company_key": key,
            "canonical_company": row["canonical_company"],
            **intent,
            "score": total,
            "modality": modality,
            "bottlenecks": "",
            "phases": "",
            "statuses": "SBIR active" if row.get("is_active") == "True" else "",
            "conditions": "",
            "interventions": row.get("latest_project", ""),
            "trial_count": "",
            "note": f"SBIR small business ({row.get('location','')})",
        }

    # ClinicalTrials.gov program intent, combined where the company is already present.
    for key, row in uni.items():
        if int(row.get("trial_count") or 0) < 1:
            continue
        intent = ui.registry_intent(row, WINDOW_DAYS)
        if not intent:
            continue
        total, bottlenecks, modality = ui.score(row, intent)
        if key in records:
            # Two independent sources on one company — strongest evidence.
            existing = records[key]
            existing["score"] = min(100, max(existing["score"], total) + 8)
            existing["trigger"] = "reporter+registry"
            existing["evidence"] = f"{existing['evidence']} | also live trial {row.get('active_nct','')}"
            existing["phases"] = row.get("active_phases", "")
            existing["trial_count"] = row.get("trial_count", "")
        else:
            records[key] = {
                "company_key": key,
                "canonical_company": row["canonical_company"],
                **intent,
                "score": total,
                "modality": modality,
                "bottlenecks": "; ".join(bottlenecks),
                "phases": row.get("phases", ""),
                "statuses": row.get("statuses", ""),
                "conditions": row.get("conditions", ""),
                "interventions": row.get("interventions", ""),
                "trial_count": row.get("trial_count", ""),
                "note": row.get("note", ""),
            }

    rows = list(records.values())
    for r in rows:
        r["priority"] = ("A" if r["score"] >= 80 else "B" if r["score"] >= 68
                         else "Review" if r["score"] >= 55 else "Reject")
    keep = [r for r in rows if r["priority"] != "Reject"]
    keep.sort(key=lambda r: -r["score"])

    fields = ["company_key", "canonical_company", "priority", "score", "trigger",
              "signal_type", "signal_date", "modality", "bottlenecks", "phases",
              "statuses", "conditions", "interventions", "trial_count", "evidence",
              "evidence_url", "note"]
    ui.INTENT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with ui.INTENT_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(keep)

    import subprocess, sys
    subprocess.run([sys.executable, "save_final.py", "--universe"], check=False)

    from collections import Counter
    print(f"\n{len(keep)} companies -> output/final.xlsx")
    print(f"  priority: {dict(Counter(r['priority'] for r in keep))}")
    print(f"  trigger : {dict(Counter(r['trigger'] for r in keep))}")
    print(f"  type    : {dict(Counter(r['signal_type'] for r in keep))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
