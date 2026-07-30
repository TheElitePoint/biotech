"""Cross-run company history.

The pipeline runs weekly against overlapping date windows, so the same funding
announcement surfaces several weeks running. Without state, every run hands the
reviewer the same companies again and the queue stops meaning anything.

This module keeps one persistent row per company and classifies each run's output:

    New        first time this company has ever appeared
    Updated    seen before, but this run brought evidence it did not have
    Unchanged  seen before, nothing new — kept in history, dropped from the report

Reviewer decisions live here too and survive every run. A company the reviewer
rejected never comes back (SOP page 38: a rejected company cannot re-enter without
new evidence and explicit approval).
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any, Literal

HISTORY = Path(__file__).resolve().parent.parent / "output" / "company_history.csv"

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
    "signal_types_seen",
    "known_evidence_urls",
    # Reviewer-owned. The pipeline reads these and never overwrites them.
    "reviewer_status",
    "reviewer",
    "review_date",
    "reviewer_notes",
]

# Reviewer statuses that stop a company reappearing in the weekly report.
CLOSED = {"rejected", "approved", "contacted", "do not contact"}


def load() -> dict[str, dict[str, str]]:
    if not HISTORY.exists():
        return {}
    with HISTORY.open(encoding="utf-8-sig") as fh:
        return {row["company_key"]: row for row in csv.DictReader(fh) if row.get("company_key")}


def save(history: dict[str, dict[str, str]]) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in sorted(history.values(), key=lambda r: r.get("last_seen", ""), reverse=True):
            writer.writerow(row)


def all_rows() -> list[dict[str, Any]]:
    """Every company ever surfaced, newest activity first, for the All Companies tab."""
    rows = list(load().values())
    rows.sort(key=lambda r: (r.get("last_seen", ""), int(r.get("best_score") or 0)), reverse=True)
    return [
        {
            "movement": "",
            "priority": r.get("best_priority", ""),
            "score": r.get("best_score", ""),
            "canonical_company": r.get("canonical_company", ""),
            "domain": r.get("domain", ""),
            "signal_types": r.get("signal_types_seen", ""),
            "top_signal_date": r.get("last_seen", ""),
            "modality": "",
            "asset_stage": "",
            "bottlenecks": "",
            "top_signal_title": "",
            "top_signal_url": (r.get("known_evidence_urls", "").split("|")[0] or "").strip(),
            "open_question": "",
            "failed_gates": "",
            "signal_count": "",
            "times_seen": r.get("times_seen", ""),
            "first_seen": r.get("first_seen", ""),
            "reviewer_status": r.get("reviewer_status", ""),
            "reviewer": r.get("reviewer", ""),
            "review_date": r.get("review_date", ""),
            "reviewer_notes": r.get("reviewer_notes", ""),
        }
        for r in rows
    ]


def record_decisions(decisions: dict[str, dict[str, str]]) -> int:
    """Write reviewer decisions back into history. Returns how many were adopted."""
    if not decisions:
        return 0
    hist = load()
    adopted = 0
    for key, fields in decisions.items():
        if key not in hist:
            continue
        status = (fields.get("reviewer_status") or "").strip()
        if not status or status == (hist[key].get("reviewer_status") or "").strip():
            continue
        hist[key].update(
            {
                "reviewer_status": status,
                "reviewer": fields.get("reviewer", "").strip(),
                "review_date": fields.get("review_date", "").strip() or date.today().isoformat(),
                "reviewer_notes": fields.get("reviewer_notes", "").strip(),
            }
        )
        adopted += 1
    if adopted:
        save(hist)
    return adopted


def _urls(value: str) -> set[str]:
    return {u.strip() for u in (value or "").split("|") if u.strip()}


def apply(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Classify this run against history and update it.

    Returns the rows annotated with `movement` and `times_seen`, plus a count
    summary. Companies the reviewer has already closed are dropped entirely.
    """
    history = load()
    today = date.today().isoformat()
    counts = {"New": 0, "Updated": 0, "Unchanged": 0, "Suppressed": 0}
    out: list[dict[str, Any]] = []

    for row in rows:
        key = row["company_key"]
        prior = history.get(key)

        if prior:
            status = (prior.get("reviewer_status") or "").strip().lower()
            if status in CLOSED:
                # Already decided. Refresh last_seen so the history stays honest,
                # but keep it out of the report.
                prior["last_seen"] = today
                prior["times_seen"] = str(int(prior.get("times_seen") or 0) + 1)
                counts["Suppressed"] += 1
                continue

            seen_urls = _urls(prior.get("known_evidence_urls", ""))
            # Company Master calls this field `all_evidence_urls`. Accept the older
            # n8n-style name too so evidence movement remains backward compatible.
            new_urls = _urls(
                row.get("all_evidence_urls", "") or row.get("evidence_urls", "")
            )
            fresh = new_urls - seen_urls
            better = int(row.get("score") or 0) > int(prior.get("best_score") or 0)

            movement: Movement = "Updated" if (fresh or better) else "Unchanged"

            merged_urls = sorted(seen_urls | new_urls)[:20]
            types = sorted(
                {t.strip() for t in (prior.get("signal_types_seen", "") + "; " + row.get("signal_types", "")).split(";") if t.strip()}
            )

            history[key] = {
                **prior,
                "canonical_company": row["canonical_company"] or prior.get("canonical_company", ""),
                "domain": row["domain"] or prior.get("domain", ""),
                "last_seen": today,
                "times_seen": str(int(prior.get("times_seen") or 0) + 1),
                "best_score": str(max(int(row.get("score") or 0), int(prior.get("best_score") or 0))),
                "best_priority": row["priority"] if better else prior.get("best_priority", row["priority"]),
                "signal_types_seen": "; ".join(types),
                "known_evidence_urls": " | ".join(merged_urls),
            }
        else:
            movement = "New"
            history[key] = {
                "company_key": key,
                "canonical_company": row["canonical_company"],
                "domain": row["domain"],
                "first_seen": today,
                "last_seen": today,
                "times_seen": "1",
                "best_score": str(row.get("score") or 0),
                "best_priority": row["priority"],
                "signal_types_seen": row.get("signal_types", ""),
                "known_evidence_urls": (
                    row.get("all_evidence_urls", "") or row.get("evidence_urls", "")
                ),
                "reviewer_status": "",
                "reviewer": "",
                "review_date": "",
                "reviewer_notes": "",
            }

        counts[movement] += 1
        entry = history[key]
        out.append(
            {
                **row,
                "movement": movement,
                "times_seen": entry["times_seen"],
                "first_seen": entry["first_seen"],
                "reviewer_status": entry.get("reviewer_status", ""),
                "reviewer": entry.get("reviewer", ""),
                "review_date": entry.get("review_date", ""),
                "reviewer_notes": entry.get("reviewer_notes", ""),
            }
        )

    save(history)
    return out, counts
