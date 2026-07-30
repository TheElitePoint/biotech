"""Hard exclusions, evidence extraction and priority scoring.

SOP pages 20-24 (exclusions, decision tree, scoring) and 85 (routing).
Everything here is deterministic and auditable — no model calls. The LLM layer
in classify.py runs *after* this and can only downgrade, never rescue, a record
that fails a hard gate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from .config import (
    AMBIGUOUS_SERVICE_TERMS,
    BOTTLENECK_TERMS,
    COMPETITOR_DOMAINS,
    EXCLUDED_DOMAINS,
    EXCLUSION_PATTERNS,
    FUNDING_TERMS,
    INTENT_RECENCY,
    MODALITY_TERMS,
    ROLE_STAGE_TERMS,
    ROUTING,
    SELF_REFERENTIAL,
    SIGNAL_STRENGTH,
    STAGE_TERMS,
)
from .signals import Signal


@dataclass
class Verdict:
    decision: str  # Approve | Review | Reject
    priority: str  # A | B | Review | Reject
    score: int
    breakdown: dict[str, int]
    failed_gates: list[str] = field(default_factory=list)
    passed_gates: list[str] = field(default_factory=list)
    exclusion_reason: str = ""
    evidence: dict[str, list[str]] = field(default_factory=dict)
    open_question: str = ""


def _hits(text: str, patterns: list[str]) -> list[str]:
    found = []
    for pat in patterns:
        # Treat plain phrases literally; anything with regex metachars as a pattern.
        rx = pat if any(c in pat for c in r"\b[](){}|+*?^$") else re.escape(pat)
        m = re.search(rx, text, re.I)
        if m:
            found.append(m.group(0).strip())
    return found


def _blob(sig: Signal) -> str:
    return " ".join([sig.title, sig.snippet, sig.raw_text]).lower()


# --- Gate 0: hard exclusions (SOP page 20) ---------------------------------


def check_exclusions(sig: Signal) -> tuple[bool, str]:
    """Return (excluded, reason)."""
    if sig.company_domain and sig.company_domain in COMPETITOR_DOMAINS:
        return True, "competitor: known AI antibody/protein design provider"

    # Match on the resolved domain or, for ATS-sourced signals that have no domain yet,
    # on the employer name against the same list.
    name_key = re.sub(r"[^a-z0-9]", "", (sig.company_candidate or "").lower())
    for domain, reason in EXCLUDED_DOMAINS.items():
        if sig.company_domain == domain:
            return True, f"suppressed {domain} — {reason}"
        if name_key and name_key == re.sub(r"[^a-z0-9]", "", domain.split(".")[0]):
            return True, f"suppressed {domain} — {reason}"

    text = _blob(sig)
    for category, patterns in EXCLUSION_PATTERNS.items():
        hits = _hits(text, patterns)
        if not hits:
            continue
        # Academic mentions are common in legitimate company news (collaborations,
        # founder bios). Only exclude when there is no company-side evidence.
        if category == "academic_only":
            commercial = _hits(
                text,
                ["our pipeline", "series a", "series b", "seed round", "biotech company",
                 "therapeutics inc", "spinout", "spin-out", "founded in"],
            )
            if commercial or sig.company_domain:
                continue
        return True, f"{category}: matched {hits[:2]}"

    # Ambiguous service terms: only exclude when the record is about the provider.
    service_hits = _hits(text, AMBIGUOUS_SERVICE_TERMS)
    if service_hits:
        in_title = bool(_hits(sig.title.lower(), AMBIGUOUS_SERVICE_TERMS))
        self_ref = bool(_hits(text, SELF_REFERENTIAL))
        if in_title or self_ref:
            where = "title" if in_title else "self-description"
            return True, f"cro_cdmo: {service_hits[:2]} in {where}"

    return False, ""


# --- Evidence extraction ---------------------------------------------------


def extract_evidence(sig: Signal) -> dict[str, list[str]]:
    text = _blob(sig)
    modality_approve = _hits(text, MODALITY_TERMS["approve"])
    modality_cond = _hits(text, MODALITY_TERMS["conditional"])
    modality_reject = _hits(text, MODALITY_TERMS["reject"])

    bottlenecks: list[str] = []
    for family, terms in BOTTLENECK_TERMS.items():
        if _hits(text, terms):
            bottlenecks.append(family)

    stages: list[str] = []
    for stage, terms in STAGE_TERMS.items():
        if _hits(text, terms):
            stages.append(stage)

    # A posting advertises the stage through the role it is filling.
    if sig.signal_type == "hiring":
        for stage, terms in ROLE_STAGE_TERMS.items():
            if stage not in stages and _hits(text, terms):
                stages.append(stage)

    return {
        "modality_approve": modality_approve,
        "modality_conditional": modality_cond,
        "modality_reject": modality_reject,
        "bottlenecks": bottlenecks,
        "stages": stages,
        "funding": _hits(text, FUNDING_TERMS),
    }


# --- Scoring (SOP pages 24 and 85) -----------------------------------------


def _recency_multiplier(signal_date: str | None, window_days: int | None = None) -> float:
    """Recency weight for the intent score.

    Undated evidence normally cannot claim strong timing. The exception is a result the
    search itself constrained: job postings almost never carry a publication date, but
    one returned under a 45-day filter is at most 45 days old. Falling back to the flat
    undated penalty there double-counts a recency limit already applied, which is what
    was rejecting every hiring signal.
    """
    if not signal_date:
        if window_days:
            for limit, mult in INTENT_RECENCY:
                if window_days <= limit:
                    # One step down: the window is an upper bound, not an observation.
                    return round(mult * 0.85, 3)
        return 0.5
    try:
        days = (date.today() - datetime.fromisoformat(signal_date).date()).days
    except ValueError:
        return 0.5
    for limit, mult in INTENT_RECENCY:
        if days <= limit:
            return mult
    return 0.1


def score(sig: Signal, ev: dict[str, list[str]]) -> tuple[dict[str, int], list[str], list[str], str]:
    passed: list[str] = []
    failed: list[str] = []
    question = ""

    # Gate 1 + scientific fit (0-25): modality, stage, bottleneck clarity.
    fit = 0
    if ev["modality_approve"]:
        fit += 12
        passed.append("G1 modality")
    elif ev["modality_conditional"]:
        fit += 6
        question = "confirm binder/sequence engineering is central to this modality"
    else:
        failed.append("G1 modality: no supported antibody/protein modality in evidence")
    if ev["modality_reject"] and not ev["modality_approve"]:
        failed.append("G1 modality: evidence points to an excluded modality")

    # Gate 2: program stage.
    early = {"discovery", "lead_optimization", "candidate_selection", "preclinical"}
    if early & set(ev["stages"]):
        fit += 7
        passed.append("G2 stage")
    elif "clinical" in ev["stages"]:
        question = question or "confirm a parallel discovery or next-gen program exists"
    else:
        failed.append("G2 stage: program stage not visible in evidence")

    # Gate 3: bottleneck.
    if ev["bottlenecks"]:
        fit += min(6, 3 * len(ev["bottlenecks"]))
        passed.append("G3 bottleneck")
    else:
        failed.append("G3 bottleneck: no platform-addressable problem visible")

    # Gate 4 + intent (0-25): trigger strength decayed by recency.
    strength = SIGNAL_STRENGTH.get(sig.signal_type, 0.5)
    intent = round(25 * strength * _recency_multiplier(sig.signal_date, sig.date_window_days))
    if intent >= 12:
        passed.append("G4 timing trigger")
    else:
        failed.append("G4 timing: trigger weak, stale or undated")

    # Gate 5 + project clarity (0-20): can a work package be named?
    clarity = 0
    if ev["bottlenecks"]:
        clarity += 10
    if ev["modality_approve"]:
        clarity += 5
    if early & set(ev["stages"]):
        clarity += 5
    if clarity >= 15:
        passed.append("G5 project clarity")
    else:
        failed.append("G5 project: paid work package cannot be scoped from this evidence")

    # Budget likelihood (0-15).
    budget = 0
    if ev["funding"]:
        budget += 9
    if sig.signal_type == "hiring":
        budget += 4
    if sig.signal_type in ("capital", "milestone"):
        budget += 3
    budget = min(budget, 15)

    # Buyer access (0-10) — heuristic only until enrichment runs.
    buyer = 6 if sig.company_domain else 3

    # Data confidence (0-5) from the evidence hierarchy.
    confidence = {1: 5, 2: 4, 3: 3, 4: 1}.get(sig.source_level, 2)
    if not sig.company_domain:
        confidence = max(1, confidence - 2)

    breakdown = {
        "scientific_fit": min(fit, 25),
        "intent": min(intent, 25),
        "project_clarity": min(clarity, 20),
        "budget": budget,
        "buyer_access": buyer,
        "data_confidence": confidence,
    }
    return breakdown, passed, failed, question


def route(sig: Signal) -> Verdict:
    excluded, reason = check_exclusions(sig)
    if excluded:
        return Verdict(
            decision="Reject",
            priority="Reject",
            score=0,
            breakdown={},
            failed_gates=["G0 hard exclusion"],
            exclusion_reason=reason,
        )

    ev = extract_evidence(sig)
    breakdown, passed, failed, question = score(sig, ev)
    total = sum(breakdown.values())

    priority = "Reject"
    for threshold, label in ROUTING:
        if total >= threshold:
            priority = label
            break

    # A hard requirement overrides the number (SOP page 85 quality rule).
    blocking = [g for g in failed if g.startswith(("G1", "G5"))]
    if blocking and priority in ("A", "B"):
        priority = "Review"

    decision = {"A": "Approve", "B": "Approve"}.get(priority, priority)
    if decision == "Approve" and not sig.company_domain:
        # Cannot approve a company we have not resolved to a real domain.
        decision, priority = "Review", "Review"
        question = question or "resolve the company website and confirm asset ownership"

    return Verdict(
        decision=decision,
        priority=priority,
        score=total,
        breakdown=breakdown,
        failed_gates=failed,
        passed_gates=passed,
        evidence={k: v for k, v in ev.items() if v},
        open_question=question,
    )
