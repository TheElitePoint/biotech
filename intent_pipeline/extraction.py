"""Evidence-span extraction and the brief's controlled vocabularies (§4 Layer 3/6).

Two hard rules from the brief drive this module:

  * "Every extracted value must include an evidence span" — so every value here
    carries `character_start`/`character_end` into the exact source text plus a
    quoted `evidence_text`, not just a boolean match.
  * "If the source does not support a value, return null" (§17.3) — a field with
    no match is None. Nothing is inferred to fill a gap.

Bottlenecks additionally carry `explicit_or_inferred` (§4 Layer 6): a phrase the
company itself wrote ("we need to improve affinity") is explicit; a bottleneck
implied by context (a job ad for an affinity-maturation scientist) is inferred.
Per the brief, an inferred bottleneck is never stored as established fact.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

NORMALIZATION_VERSION = "v1.0"

# --- Controlled vocabularies (brief §4 Layer 6) -----------------------------

MODALITIES: dict[str, list[str]] = {
    "monoclonal antibody": [r"monoclonal antibod\w*", r"\bmAb\b"],
    "bispecific": [r"bispecific"],
    "multispecific": [r"multispecific", r"trispecific"],
    "antibody fragment": [r"antibody fragment"],
    "Fab": [r"\bFab\b", r"Fab fragment"],
    "scFv": [r"\bscFv\b", r"single[- ]chain variable fragment"],
    "nanobody": [r"nanobod\w*", r"\bVHH\b", r"single[- ]domain antibod\w*"],
    "engineered protein": [r"engineered protein", r"protein engineering", r"de novo protein"],
    "therapeutic binder": [r"therapeutic binder", r"\bbinder\b"],
    "fusion protein": [r"fusion protein", r"\bFc[- ]fusion\b"],
    "cytokine engineering": [r"cytokine engineering", r"engineered cytokine", r"immunocytokine"],
    "ADC binder engineering": [r"antibody[- ]drug conjugate", r"\bADC\b"],
}

STAGES: dict[str, list[str]] = {
    "discovery": [r"\bdiscovery stage\b", r"\bhit identification\b", r"\bdiscovery program\b"],
    "binder generation": [r"binder generation", r"hit generation", r"antibody generation"],
    "lead generation": [r"lead generation", r"lead identification"],
    "lead optimization": [r"lead optimi[sz]ation", r"lead series"],
    "candidate selection": [r"candidate selection", r"development candidate", r"candidate nomination"],
    "preclinical": [r"preclinical", r"pre-clinical"],
    "IND-enabling": [r"IND[- ]enabling", r"GLP toxicolog\w*"],
    "early clinical with active discovery expansion": [r"phase 1", r"phase i\b", r"first[- ]in[- ]human"],
}

# The brief's 20-item bottleneck taxonomy.
BOTTLENECKS: dict[str, list[str]] = {
    "de_novo_design": [r"de novo design", r"de novo antibod\w*", r"design from scratch"],
    "low_binder_diversity": [r"binder diversity", r"limited diversity", r"repertoire diversity"],
    "low_hit_rate": [r"hit rate", r"few hits", r"low hit"],
    "affinity": [r"affinity maturation", r"improve affinity", r"picomolar", r"binding affinity"],
    "potency": [r"\bpotency\b", r"more potent"],
    "specificity": [r"\bspecificity\b", r"selectivity"],
    "cross_reactivity": [r"cross[- ]reactivity", r"off[- ]target binding", r"polyreactivity"],
    "epitope_coverage": [r"epitope coverage", r"epitope mapping", r"epitope bin"],
    "humanization": [r"humani[sz]ation", r"humani[sz]ed antibod\w*"],
    "immunogenicity": [r"immunogenicity"],
    "sequence_liability": [r"sequence liabilit\w*", r"deamidation", r"oxidation site"],
    "stability": [r"thermal stabilit\w*", r"\bstability\b"],
    "aggregation": [r"aggregation"],
    "expression": [r"expression titer", r"low expression", r"expression level"],
    "solubility": [r"solubilit\w*"],
    "manufacturability": [r"manufacturabilit\w*", r"developabilit\w*"],
    "format_compatibility": [r"format compatibilit\w*", r"format conversion"],
    "bispecific_balancing": [r"arm balancing", r"affinity balanc\w*", r"chain pairing"],
    "candidate_shortlisting": [r"candidate shortlist\w*", r"prioriti[sz]e candidates", r"rank candidates"],
    "wet_lab_capacity": [r"wet[- ]lab capacity", r"screening capacity", r"throughput limitation"],
}

# The brief's 18 intent types.
INTENT_TYPES: dict[str, list[str]] = {
    "funding": [r"series [a-e]\b", r"seed financing", r"raises \$", r"raised \$", r"oversubscribed", r"financing"],
    "hiring": [r"\bhiring\b", r"we are looking for", r"join our team", r"open position", r"apply now"],
    "new_program": [r"new program", r"new antibody program", r"launch\w* a program"],
    "pipeline_expansion": [r"pipeline expansion", r"expand\w* (?:our|the) pipeline"],
    "lead_optimization": [r"lead optimi[sz]ation"],
    "candidate_selection": [r"candidate selection"],
    "candidate_nomination": [r"candidate nomination", r"development candidate"],
    "publication": [r"published in", r"\bpublication\b", r"peer[- ]reviewed"],
    "patent": [r"\bpatent\b", r"granted a patent"],
    "grant": [r"\bSBIR\b", r"\bSTTR\b", r"awarded a grant", r"grant funding"],
    "conference_data": [r"\bposter\b", r"oral presentation", r"present\w* data at"],
    "trial_update": [r"\bNCT\d+", r"clinical trial", r"enrolling"],
    "new_partnership": [r"partnership", r"collaborat\w*", r"license agreement", r"alliance"],
    "website_change": [],  # set by the crawler on material content change, not by text
    "team_expansion": [r"expand\w* (?:our|the) team", r"growing team", r"new hire"],
    "manufacturing_preparation": [r"manufactur\w* preparation", r"GMP manufactur\w*", r"tech transfer"],
    "program_pause": [r"discontinu\w*", r"paused", r"deprioriti[sz]ed"],
    "next_generation_program": [r"next[- ]generation", r"second[- ]generation"],
}

# Phrases where the company states a need in its own voice -> explicit bottleneck.
_EXPLICIT_CUES = re.compile(
    r"\b(we need|we are seeking|we seek|challenge|challenging|difficult|"
    r"limitation|limited by|bottleneck|hurdle|struggle|remains? unsolved|"
    r"unmet need|to improve|to optimi[sz]e|to overcome|risk of)\b",
    re.I,
)


@dataclass
class Span:
    value: str
    confidence: int
    evidence_text: str
    character_start: int
    character_end: int
    source_url: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _window(text: str, start: int, end: int, pad: int = 90) -> tuple[str, int, int]:
    lo = max(0, start - pad)
    hi = min(len(text), end + pad)
    return text[lo:hi].strip(), lo, hi


def find_spans(
    text: str,
    vocabulary: dict[str, list[str]],
    source_url: str | None = None,
    base_confidence: int = 85,
    limit_per_value: int = 2,
) -> dict[str, list[Span]]:
    """Locate every vocabulary value in `text`, keeping character offsets.

    Returns {value: [Span, ...]}. A value absent from the text is absent from
    the result — callers must treat that as null, never as a negative fact.
    """
    found: dict[str, list[Span]] = {}
    if not text:
        return found

    for value, patterns in vocabulary.items():
        hits: list[Span] = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.I):
                evidence, lo, hi = _window(text, match.start(), match.end())
                hits.append(
                    Span(
                        value=value,
                        confidence=base_confidence,
                        evidence_text=evidence,
                        character_start=match.start(),
                        character_end=match.end(),
                        source_url=source_url,
                    )
                )
                if len(hits) >= limit_per_value:
                    break
            if len(hits) >= limit_per_value:
                break
        if hits:
            found[value] = hits
    return found


def classify_bottlenecks(text: str, source_url: str | None = None) -> list[dict[str, Any]]:
    """Bottlenecks with the brief's mandatory explicit-vs-inferred distinction."""
    out: list[dict[str, Any]] = []
    for value, spans in find_spans(text, BOTTLENECKS, source_url).items():
        span = spans[0]
        # Explicit only when the company frames it as a problem/need in the
        # surrounding sentence. A bare mention of "stability" in a product
        # blurb is an inference at best.
        explicit = bool(_EXPLICIT_CUES.search(span.evidence_text))
        out.append(
            {
                "value": value,
                "explicit_or_inferred": "explicit" if explicit else "inferred",
                "confidence": 88 if explicit else 62,
                "evidence": span.as_dict(),
            }
        )
    return out


def best_value(spans: dict[str, list[Span]]) -> tuple[str | None, dict[str, Any] | None]:
    """Highest-confidence single value for a field, or (None, None) if unsupported."""
    if not spans:
        return None, None
    value = max(spans, key=lambda v: spans[v][0].confidence)
    return value, spans[value][0].as_dict()


def extract(text: str, source_url: str | None = None) -> dict[str, Any]:
    """Produce the brief's normalized-signal field set for one blob of text."""
    modality_spans = find_spans(text, MODALITIES, source_url, base_confidence=92)
    stage_spans = find_spans(text, STAGES, source_url, base_confidence=88)
    intent_spans = find_spans(text, INTENT_TYPES, source_url, base_confidence=80)
    bottlenecks = classify_bottlenecks(text, source_url)

    modality, modality_ev = best_value(modality_spans)
    stage, stage_ev = best_value(stage_spans)

    evidence_spans: list[dict[str, Any]] = []
    for group in (modality_spans, stage_spans, intent_spans):
        for spans in group.values():
            evidence_spans.extend(s.as_dict() for s in spans)

    field_confidence: dict[str, int] = {}
    if modality_ev:
        field_confidence["modality"] = modality_ev["confidence"]
    if stage_ev:
        field_confidence["asset_stage"] = stage_ev["confidence"]

    return {
        "modality": modality,                       # None when unsupported
        "modality_evidence": modality_ev,
        "all_modalities": sorted(modality_spans),
        "asset_stage": stage,
        "asset_stage_evidence": stage_ev,
        "all_stages": sorted(stage_spans),
        "intent_types": sorted(intent_spans),
        "bottlenecks": bottlenecks,
        "evidence_spans": evidence_spans,
        "field_confidence": field_confidence,
        "normalization_version": NORMALIZATION_VERSION,
    }
