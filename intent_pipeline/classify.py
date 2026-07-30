"""Optional LLM layer implementing the SOP prompts on pages 81-84.

Boundary from SOP page 80: the model structures and proposes. It never invents
evidence and never final-approves. It runs only on records that already survived
the deterministic gates, and it can downgrade a record but not promote a Reject.
"""

from __future__ import annotations

import json
import os
from typing import Any

from .gates import Verdict
from .signals import Signal

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
PROMPT_VERSION = "sop-p81-84.v1"

SYSTEM = """You classify biomedical buying signals for an AI antibody and protein design platform.

Return JSON only. Extract only facts supported by the supplied source text.
Never infer therapeutic ownership from author affiliation or a press mention alone.
Mark anything not stated in the source as an inference, and set the field to null
rather than guessing.

Hard reject: CRO, CDMO, diagnostics-only, reagent/catalogue suppliers, manufacturing
and service providers, academic-only work with no asset-owning company, and direct
competitors (AI antibody design / protein language model platforms).

Approve only if the company owns or co-owns a therapeutic antibody or protein program
AND a current design/optimization work package can be stated in one sentence.

Schema:
{
  "canonical_company": str|null,
  "domain": str|null,
  "therapeutic_owner_status": "owner"|"co_owner"|"licensee"|"service_provider"|"academic"|"unclear",
  "target": str|null,
  "disease": str|null,
  "modality": str|null,
  "asset_stage": str|null,
  "scientific_problem": str|null,
  "problem_is_inference": bool,
  "signal_type": "capital"|"hiring"|"program"|"scientific"|"execution"|"milestone",
  "evidence_quotes": [str],
  "decision": "Approve"|"Review"|"Reject",
  "failed_gates": [str],
  "project_hypothesis": {
    "objective": str|null,
    "client_inputs": [str],
    "platform_outputs": [str],
    "validation_path": str|null,
    "unresolved_risk": str|null
  },
  "buyer_titles": [str],
  "confidence": int,
  "next_action": str
}

Forbidden language in the hypothesis: guaranteed, solved, revolutionary, or a generic
strategic partnership. Allowed: could support, may be relevant, focused pilot,
ranked shortlist, wet-lab validation. Scope to one target or one lead series."""


def _user_prompt(sig: Signal, verdict: Verdict) -> str:
    body = (sig.raw_text or sig.snippet)[:12000]
    return json.dumps(
        {
            "source_type": sig.signal_type,
            "source_url": sig.source_url,
            "source_domain": sig.source_domain,
            "source_level": sig.source_level,
            "signal_date": sig.signal_date,
            "title": sig.title,
            "company_candidate": sig.company_candidate,
            "company_domain": sig.company_domain,
            "resolution_note": sig.resolution_note,
            "deterministic_gate_result": {
                "score": verdict.score,
                "passed": verdict.passed_gates,
                "failed": verdict.failed_gates,
                "evidence_terms": verdict.evidence,
            },
            "source_text": body,
        },
        indent=2,
    )


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def classify(sig: Signal, verdict: Verdict) -> dict[str, Any] | None:
    """Return the model's structured judgment, or None if unavailable/failed."""
    if not available():
        return None
    try:
        import anthropic
    except ImportError:
        return None

    client = anthropic.Anthropic()
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM,
            messages=[{"role": "user", "content": _user_prompt(sig, verdict)}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```")
        data = json.loads(text)
    except Exception as exc:  # noqa: BLE001 - a bad model call must not stop the run
        return {"_error": str(exc)}

    data["_model"] = MODEL
    data["_prompt_version"] = PROMPT_VERSION
    return data


def reconcile(verdict: Verdict, llm: dict[str, Any] | None) -> Verdict:
    """Merge the model's judgment under the SOP boundary rules.

    The model may downgrade (Approve -> Review/Reject) but never upgrade a record
    the deterministic gates rejected.
    """
    if not llm or "_error" in llm:
        return verdict

    rank = {"Reject": 0, "Review": 1, "Approve": 2}
    model_decision = llm.get("decision", "Review")
    if rank.get(model_decision, 1) < rank.get(verdict.decision, 1):
        verdict.decision = model_decision
        verdict.priority = model_decision if model_decision != "Approve" else verdict.priority
        for gate in llm.get("failed_gates", []):
            if gate not in verdict.failed_gates:
                verdict.failed_gates.append(f"LLM: {gate}")

    if llm.get("therapeutic_owner_status") in ("service_provider", "academic"):
        verdict.decision = "Reject"
        verdict.priority = "Reject"
        verdict.exclusion_reason = f"LLM ownership status: {llm['therapeutic_owner_status']}"

    if not verdict.open_question:
        verdict.open_question = llm.get("next_action", "")
    return verdict
