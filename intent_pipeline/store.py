"""Output tables: Raw Signals, Company Master, Review Queue and the Run Log.

CSV so a researcher can open them in Sheets/Airtable directly (SOP page 26), plus
a JSONL copy of every raw item because raw evidence is immutable (SOP page 28).
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gates import Verdict
from .signals import Signal, canonical_name
from .suppression import contains as is_suppressed
from .suppression import load as load_suppression

OUT = Path(__file__).resolve().parent.parent / "output"

RAW_JSONL = OUT / "raw_signals.jsonl"
SIGNALS_CSV = OUT / "raw_signals.csv"
COMPANIES_CSV = OUT / "company_master.csv"
REVIEW_CSV = OUT / "review_queue.csv"
RUNLOG_CSV = OUT / "actor_run_log.csv"


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_raw(items: list[dict[str, Any]]) -> None:
    RAW_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with RAW_JSONL.open("a", encoding="utf-8") as fh:
        for item in items:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")


def save_signals(records: list[tuple[Signal, Verdict, dict[str, Any] | None]]) -> None:
    rows = []
    for sig, verdict, llm in records:
        row = sig.as_row()
        row.pop("raw_text", None)
        row.update(
            {
                "decision": verdict.decision,
                "priority": verdict.priority,
                "score": verdict.score,
                "exclusion_reason": verdict.exclusion_reason,
                "failed_gates": "; ".join(verdict.failed_gates),
                "passed_gates": "; ".join(verdict.passed_gates),
                "bottlenecks": "; ".join(verdict.evidence.get("bottlenecks", [])),
                "modality_evidence": "; ".join(verdict.evidence.get("modality_approve", [])),
                "open_question": verdict.open_question,
                "llm_decision": (llm or {}).get("decision", ""),
                "llm_target": (llm or {}).get("target", ""),
                "llm_problem": (llm or {}).get("scientific_problem", ""),
            }
        )
        rows.append(row)
    _write_csv(SIGNALS_CSV, rows)


def build_company_master(
    records: list[tuple[Signal, Verdict, dict[str, Any] | None]]
) -> list[dict[str, Any]]:
    """Collapse signals into one row per company (SOP page 29 dedupe key).

    A company accumulates intent: multiple independent signals raise the score
    without creating a second record (SOP page 79).
    """
    groups: dict[str, list[tuple[Signal, Verdict, dict[str, Any] | None]]] = defaultdict(list)
    suppressed = load_suppression()
    for sig, verdict, llm in records:
        if verdict.decision == "Reject" and verdict.exclusion_reason:
            continue
        name = (llm or {}).get("canonical_company") or sig.company_candidate
        domain = (llm or {}).get("domain") or sig.company_domain
        key = (domain or canonical_name(name or "").lower()).strip()
        if not key:
            continue
        if is_suppressed(suppressed, key=key, name=name, domain=domain):
            continue
        groups[key].append((sig, verdict, llm))

    rows = []
    for key, group in groups.items():
        group.sort(key=lambda g: g[1].score, reverse=True)
        best_sig, best_verdict, best_llm = group[0]
        signal_types = sorted({s.signal_type for s, _, _ in group})
        bottlenecks = sorted(
            {b for _, v, _ in group for b in v.evidence.get("bottlenecks", [])}
        )
        # Corroboration bonus: distinct trigger families on the same company.
        bonus = min(8, 4 * (len(signal_types) - 1))
        total = min(100, best_verdict.score + bonus)
        priority = (
            "A" if total >= 80 else "B" if total >= 68 else "Review" if total >= 55 else "Reject"
        )
        if best_verdict.decision != "Approve":
            priority = best_verdict.priority

        hypothesis = (best_llm or {}).get("project_hypothesis") or {}
        rows.append(
            {
                "company_key": key,
                "canonical_company": (best_llm or {}).get("canonical_company")
                or best_sig.company_candidate
                or "",
                "domain": (best_llm or {}).get("domain") or best_sig.company_domain or "",
                "status": best_verdict.decision,
                "priority": priority,
                "score": total,
                "signal_count": len(group),
                "signal_types": "; ".join(signal_types),
                "corroboration_bonus": bonus,
                "modality": (best_llm or {}).get("modality")
                or "; ".join(best_verdict.evidence.get("modality_approve", [])),
                "target": (best_llm or {}).get("target", ""),
                "disease": (best_llm or {}).get("disease", ""),
                "asset_stage": (best_llm or {}).get("asset_stage", "")
                or "; ".join(best_verdict.evidence.get("stages", [])),
                "bottlenecks": "; ".join(bottlenecks),
                "project_objective": hypothesis.get("objective", ""),
                "client_inputs": "; ".join(hypothesis.get("client_inputs", []) or []),
                "platform_outputs": "; ".join(hypothesis.get("platform_outputs", []) or []),
                "validation_path": hypothesis.get("validation_path", "") or "",
                "unresolved_risk": hypothesis.get("unresolved_risk", "") or "",
                "buyer_titles": "; ".join((best_llm or {}).get("buyer_titles", []) or []),
                "top_signal_url": best_sig.source_url,
                "top_signal_date": best_sig.signal_date or "",
                "top_signal_title": best_sig.title,
                "all_evidence_urls": " | ".join(s.source_url for s, _, _ in group[:6]),
                "open_question": best_verdict.open_question,
                "failed_gates": "; ".join(best_verdict.failed_gates),
                "reviewer": "",
                "review_date": "",
            }
        )

    rows.sort(key=lambda r: (r["priority"] not in ("A", "B"), -r["score"]))
    return rows


def save_companies(rows: list[dict[str, Any]]) -> None:
    _write_csv(COMPANIES_CSV, rows)
    _write_csv(REVIEW_CSV, [r for r in rows if r["priority"] in ("A", "B", "Review")])


def append_run_log(entry: dict[str, Any]) -> None:
    RUNLOG_CSV.parent.mkdir(parents=True, exist_ok=True)
    entry = dict(entry, run_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    exists = RUNLOG_CSV.exists() and RUNLOG_CSV.stat().st_size > 0
    with RUNLOG_CSV.open("a", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(entry), extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(entry)
