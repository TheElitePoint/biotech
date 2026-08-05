"""Unified seen-company registry for the multi-source pipeline.

Same proven logic as intent_pipeline/history.py (New/Updated/Unchanged
classification, reviewer-decision persistence so a rejected company never
resurfaces), pointed at its own file (data/registry.csv) so the new
multi-source orchestrator has a single seen-company ledger across all 8
sources without touching history.py — which stays exactly as it is for the
legacy Tavily path (intent_pipeline.run).

The point of this table: before a company gets re-shown as "new" or spends
another round of scoring, check here first. A company already Approved,
Rejected, Contacted or Do Not Contact is permanently skipped; a company seen
before with no new evidence is Unchanged and dropped from the run's report,
not re-researched.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any, Literal

REGISTRY = Path(__file__).resolve().parent.parent / "data" / "registry.csv"

Movement = Literal["New", "Updated", "Unchanged"]

FIELDS = [
    "company_key",
    "canonical_company",
    "domain",
    "first_seen",
    "last_seen",
    "times_seen",
    "best_score",
    "best_priority",
    "employees",
    "modality",
    "bottlenecks",
    "signal_types_seen",
    "sources_seen",
    "known_evidence_urls",
    # Reviewer-owned. The pipeline reads these and never overwrites them.
    "reviewer_status",
    "reviewer",
    "review_date",
    "reviewer_notes",
]

CLOSED = {"rejected", "approved", "contacted", "do not contact"}


def load() -> dict[str, dict[str, str]]:
    if not REGISTRY.exists():
        return {}
    with REGISTRY.open(encoding="utf-8-sig") as fh:
        return {row["company_key"]: row for row in csv.DictReader(fh) if row.get("company_key")}


def save(registry: dict[str, dict[str, str]]) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in sorted(registry.values(), key=lambda r: r.get("last_seen", ""), reverse=True):
            writer.writerow(row)


def is_closed(key: str, registry: dict[str, dict[str, str]] | None = None) -> bool:
    """True if the reviewer already decided this company — never re-show it."""
    reg = registry if registry is not None else load()
    entry = reg.get(key)
    if not entry:
        return False
    return (entry.get("reviewer_status") or "").strip().lower() in CLOSED


def all_rows() -> list[dict[str, Any]]:
    """Every company ever surfaced, newest activity first — the master sheet population."""
    rows = list(load().values())
    rows.sort(key=lambda r: (r.get("last_seen", ""), int(r.get("best_score") or 0)), reverse=True)
    return [
        {
            "movement": "",
            "priority": r.get("best_priority", ""),
            "score": r.get("best_score", ""),
            "canonical_company": r.get("canonical_company", ""),
            "domain": r.get("domain", ""),
            "employees": r.get("employees", ""),
            "signal_types": r.get("signal_types_seen", ""),
            "sources": r.get("sources_seen", ""),
            "modality": r.get("modality", ""),
            "bottlenecks": r.get("bottlenecks", ""),
            "top_signal_title": "",
            "top_signal_url": (r.get("known_evidence_urls", "").split("|")[0] or "").strip(),
            "open_question": "",
            "times_seen": r.get("times_seen", ""),
            "reviewer_status": r.get("reviewer_status", ""),
            "reviewer": r.get("reviewer", ""),
            "reviewer_notes": r.get("reviewer_notes", ""),
        }
        for r in rows
    ]


def record_decisions(decisions: dict[str, dict[str, str]]) -> int:
    if not decisions:
        return 0
    reg = load()
    adopted = 0
    for key, fields in decisions.items():
        if key not in reg:
            continue
        status = (fields.get("reviewer_status") or "").strip()
        if not status or status == (reg[key].get("reviewer_status") or "").strip():
            continue
        reg[key].update(
            {
                "reviewer_status": status,
                "reviewer": fields.get("reviewer", "").strip(),
                "review_date": fields.get("review_date", "").strip() or date.today().isoformat(),
                "reviewer_notes": fields.get("reviewer_notes", "").strip(),
            }
        )
        adopted += 1
    if adopted:
        save(reg)
    return adopted


def _urls(value: str) -> set[str]:
    return {u.strip() for u in (value or "").split("|") if u.strip()}


def apply(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Classify this run's companies against the registry and update it.

    Returns the rows annotated with `movement` and `times_seen`, plus counts.
    Companies the reviewer already closed are dropped entirely — this is the
    "don't waste effort on old companies" gate for the report; the per-source
    bulk sweeps still ran (ClinicalTrials.gov/NIH RePORTER return everything
    matching the query in one call regardless), but nothing downstream spends
    another review cycle on a company already decided.
    """
    registry = load()
    today = date.today().isoformat()
    counts = {"New": 0, "Updated": 0, "Unchanged": 0, "Suppressed": 0}
    out: list[dict[str, Any]] = []

    for row in rows:
        key = row["company_key"]
        prior = registry.get(key)
        row_sources = {s.strip() for s in (row.get("sources") or "").split(";") if s.strip()}

        if prior:
            if is_closed(key, registry):
                prior["last_seen"] = today
                prior["times_seen"] = str(int(prior.get("times_seen") or 0) + 1)
                counts["Suppressed"] += 1
                continue

            seen_urls = _urls(prior.get("known_evidence_urls", ""))
            new_urls = _urls(row.get("all_evidence_urls", "") or row.get("evidence_urls", ""))
            fresh = new_urls - seen_urls
            better = int(row.get("score") or 0) > int(prior.get("best_score") or 0)
            movement: Movement = "Updated" if (fresh or better) else "Unchanged"

            merged_urls = sorted(seen_urls | new_urls)[:20]
            types = sorted(
                {t.strip() for t in (prior.get("signal_types_seen", "") + "; " + row.get("signal_types", "")).split(";") if t.strip()}
            )
            sources = sorted(
                {s.strip() for s in (prior.get("sources_seen", "") + "; " + row.get("sources", "")).split(";") if s.strip()}
                | row_sources
            )

            registry[key] = {
                **prior,
                "canonical_company": row["canonical_company"] or prior.get("canonical_company", ""),
                "domain": row.get("domain") or prior.get("domain", ""),
                "employees": row.get("employees") or prior.get("employees", ""),
                "modality": row.get("modality") or prior.get("modality", ""),
                "bottlenecks": row.get("bottlenecks") or prior.get("bottlenecks", ""),
                "last_seen": today,
                "times_seen": str(int(prior.get("times_seen") or 0) + 1),
                "best_score": str(max(int(row.get("score") or 0), int(prior.get("best_score") or 0))),
                "best_priority": row["priority"] if better else prior.get("best_priority", row["priority"]),
                "signal_types_seen": "; ".join(types),
                "sources_seen": "; ".join(sources),
                "known_evidence_urls": " | ".join(merged_urls),
            }
        else:
            movement = "New"
            registry[key] = {
                "company_key": key,
                "canonical_company": row["canonical_company"],
                "domain": row.get("domain", ""),
                "employees": row.get("employees", ""),
                "modality": row.get("modality", ""),
                "bottlenecks": row.get("bottlenecks", ""),
                "first_seen": today,
                "last_seen": today,
                "times_seen": "1",
                "best_score": str(row.get("score") or 0),
                "best_priority": row["priority"],
                "signal_types_seen": row.get("signal_types", ""),
                "sources_seen": row.get("sources", ""),
                "known_evidence_urls": row.get("all_evidence_urls", "") or row.get("evidence_urls", ""),
                "reviewer_status": "",
                "reviewer": "",
                "review_date": "",
                "reviewer_notes": "",
            }

        counts[movement] += 1
        entry = registry[key]
        out.append(
            {
                **row,
                "movement": movement,
                "times_seen": entry["times_seen"],
                "reviewer_status": entry.get("reviewer_status", ""),
                "reviewer": entry.get("reviewer", ""),
                "reviewer_notes": entry.get("reviewer_notes", ""),
            }
        )

    save(registry)
    return out, counts
