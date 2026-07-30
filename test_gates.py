"""Offline check of the gate + scoring layer using synthetic signals.

Runs without any API key. Use this after editing config.py to confirm that
exclusions still fire and that a good signal still scores as expected.

    python test_gates.py
"""

from __future__ import annotations

from datetime import date, timedelta

from intent_pipeline.gates import route
from intent_pipeline.signals import normalize
from intent_pipeline.store import build_company_master

RECENT = (date.today() - timedelta(days=6)).isoformat()
STALE = (date.today() - timedelta(days=200)).isoformat()


def make(url, title, content, seed="CAP-01", stype="capital", published=RECENT):
    return normalize(
        {
            "url": url,
            "title": title,
            "content": content,
            "published_date": published,
            "_seed_id": seed,
            "_query": "test",
            "_signal_type": stype,
            "_date_window_days": 30,
        }
    )


CASES = [
    (
        "strong: funded preclinical bispecific with a named bottleneck",
        make(
            "https://novabinder.com/news/series-a",
            "NovaBinder raises $42M Series A to advance its bispecific antibody pipeline",
            "The Series A will fund lead optimization of our preclinical bispecific "
            "program, where affinity maturation and arm balancing against a difficult "
            "membrane protein target remain the key challenges ahead of candidate "
            "selection. Developability and aggregation risk will be assessed in house.",
        ),
        "Approve",
    ),
    (
        "hard exclusion: CRO service provider",
        make(
            "https://someservices.com/antibody-discovery",
            "Antibody discovery services for biotech partners",
            "As a contract research organization we offer antibody discovery services, "
            "affinity maturation and humanization on a fee-for-service basis.",
            seed="SCI-01",
            stype="scientific",
        ),
        "Reject",
    ),
    (
        "hard exclusion: named competitor domain",
        make(
            "https://absci.com/news/platform",
            "Absci announces generative antibody design results",
            "Our generative AI platform performs de novo antibody design and affinity "
            "maturation for preclinical bispecific programs.",
        ),
        "Reject",
    ),
    (
        "hard exclusion: reagent / RUO supplier",
        make(
            "https://catalogbio.com/products",
            "Primary antibodies for research",
            "Catalog antibody products for research use only, including ELISA kit "
            "reagents and diagnostic assay components.",
        ),
        "Reject",
    ),
    (
        "downgrade: right modality but stale and no bottleneck",
        make(
            "https://oldco.com/news/update",
            "OldCo provides a corporate update",
            "OldCo continues to develop its monoclonal antibody portfolio.",
            published=STALE,
        ),
        # Score falls below 55, so SOP page 24 routes this to Reject rather than
        # leaving it in a permanent grey queue.
        "Reject",
    ),
    (
        "wrong modality: small molecule only",
        make(
            "https://chemco.com/pipeline",
            "ChemCo advances small molecule pipeline",
            "Our small molecule inhibitors and gene therapy AAV vector programs "
            "continue toward the clinic.",
        ),
        "Reject",  # fails the modality gate outright (SOP page 15)
    ),
    (
        "unresolved company: news headline only, no domain",
        make(
            "https://fiercebiotech.com/biotech/heliaxbio-raises-30m",
            "HeliaxBio raises $30M to expand antibody discovery team",
            "HeliaxBio will use the financing for lead optimization and humanization "
            "of its preclinical monoclonal antibody programs and candidate selection.",
        ),
        "Review",  # named but unverified domain must not auto-approve
    ),
]


def main() -> int:
    failures = 0
    records = []
    for label, sig, expected in CASES:
        verdict = route(sig)
        records.append((sig, verdict, None))
        ok = verdict.decision == expected
        failures += 0 if ok else 1
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {label}")
        print(
            f"       decision={verdict.decision} priority={verdict.priority} "
            f"score={verdict.score} expected={expected}"
        )
        if verdict.exclusion_reason:
            print(f"       excluded: {verdict.exclusion_reason}")
        if verdict.breakdown:
            print(f"       breakdown: {verdict.breakdown}")
        if verdict.failed_gates:
            print(f"       failed: {'; '.join(verdict.failed_gates)}")
        print()

    companies = build_company_master(records)
    print(f"Company master rows: {len(companies)}")
    for c in companies:
        print(
            f"  {c['priority']:6} {c['score']:3} {c['canonical_company'][:28]:28} "
            f"signals={c['signal_count']} {c['bottlenecks']}"
        )

    print(f"\n{len(CASES) - failures}/{len(CASES)} cases passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
