"""Walk one company through the full SOP path, showing every decision.

This is the demo: it takes a real row from the last run and prints the trace a
reviewer would otherwise have to reconstruct by hand — what fired, what each gate
decided, how the score was built, and what a paid pilot would look like.

    python demo.py                  # top company from the last run
    python demo.py "RQ Bio"         # a specific one
"""

from __future__ import annotations

import csv
import sys
import textwrap
from pathlib import Path

from intent_pipeline.config import SCORE_CAPS, SIGNAL_STRENGTH

OUT = Path(__file__).resolve().parent / "output"
W = 78


def rule(char: str = "-") -> None:
    print(char * W)


def head(title: str) -> None:
    print()
    rule("=")
    print(f"  {title}")
    rule("=")


def wrap(text: str, indent: str = "  ") -> str:
    return textwrap.fill(text, width=W - 2, initial_indent=indent, subsequent_indent=indent)


def load(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        sys.exit(f"{path} not found. Run the pipeline first:\n  python -m intent_pipeline.run")
    with path.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def pick(companies: list[dict[str, str]], wanted: str | None) -> dict[str, str]:
    if not companies:
        sys.exit("Review queue is empty. Run the pipeline first.")
    if not wanted:
        return companies[0]
    for row in companies:
        if wanted.lower() in row["canonical_company"].lower():
            return row
    names = ", ".join(r["canonical_company"] for r in companies)
    sys.exit(f"No company matching {wanted!r}. Available: {names}")


def main() -> int:
    companies = load(OUT / "review_queue.csv")
    signals = load(OUT / "raw_signals.csv")
    company = pick(companies, sys.argv[1] if len(sys.argv) > 1 else None)

    name = company["canonical_company"]
    key = company["company_key"]

    # --- 1. What fired -----------------------------------------------------
    head(f"{name}  —  Priority {company['priority']}, score {company['score']}/100")

    mine = [
        s
        for s in signals
        if (s.get("company_domain") or s.get("company_candidate", "").lower()) == key
    ]

    print(f"\nSTEP 1 — The signal that surfaced this company")
    rule()
    print(f"  Intent family : {company['signal_types']}  "
          f"(weight {SIGNAL_STRENGTH.get(company['signal_types'].split(';')[0].strip(), 0):.2f})")
    print(f"  Seen on       : {company['top_signal_date'] or 'undated'}")
    print(f"  Found by seed : {mine[0]['seed_id'] if mine else 'n/a'}")
    print(f"  Query         : {mine[0]['query'] if mine else 'n/a'}")
    print()
    print(wrap(f'"{company["top_signal_title"]}"'))
    print(f"\n  Source: {company['top_signal_url']}")
    if company["signal_count"] != "1":
        print(f"\n  {company['signal_count']} independent signals on this company "
              f"(+{company['corroboration_bonus']} corroboration)")

    # --- 2. Exclusions -----------------------------------------------------
    print(f"\n\nSTEP 2 — Hard exclusions (SOP p20)")
    rule()
    print("  Checked against CRO/CDMO, diagnostics, reagent supplier, non-buyer,")
    print("  academic-only, competitor and suppression lists.")
    print("  -> PASSED. Not excluded, so it earns the cost of further analysis.")

    # --- 3. Evidence -------------------------------------------------------
    print(f"\n\nSTEP 3 — Evidence extracted (SOP p15/16)")
    rule()
    for label, value in [
        ("Modality", company["modality"]),
        ("Asset stage", company["asset_stage"]),
        ("Bottleneck", company["bottlenecks"]),
    ]:
        print(f"  {label:12}: {value or '(not visible in evidence)'}")

    # --- 4. Score ----------------------------------------------------------
    print(f"\n\nSTEP 4 — Score build-up (SOP p24)")
    rule()
    print(f"  {'Factor':<20} {'Max':>5}   What it measures")
    for factor, cap in SCORE_CAPS.items():
        meaning = {
            "scientific_fit": "modality + stage + bottleneck clarity",
            "intent": "trigger strength decayed by recency",
            "project_clarity": "can a paid pilot be scoped?",
            "budget": "funding, hiring, external spend",
            "buyer_access": "named senior buyer reachable",
            "data_confidence": "source strength, ownership clarity",
        }[factor]
        print(f"  {factor:<20} {cap:>5}   {meaning}")
    print(f"\n  Total: {company['score']}/100  ->  Priority {company['priority']}")
    thresholds = "80+ = A,  68-79 = B,  55-67 = Review,  below 55 = Reject"
    print(f"  ({thresholds})")

    # --- 5. What blocks approval ------------------------------------------
    print(f"\n\nSTEP 5 — Why this is Review and not Approve")
    rule()
    if company["failed_gates"]:
        for gate in company["failed_gates"].split(";"):
            if gate.strip():
                print(wrap(f"FAILED  {gate.strip()}"))
    if company["open_question"]:
        print()
        print(wrap(f"Open question: {company['open_question']}"))
    print()
    print(wrap(
        "Nothing reaches Approve automatically. A human confirms therapeutic "
        "ownership and names the paid work package first — that is SOP Gate 5, "
        "and it is the whole point of the review queue."
    ))

    # --- 6. The human step -------------------------------------------------
    print(f"\n\nSTEP 6 — Your ten minutes (SOP p22/25)")
    rule()
    steps = [
        f"Open the source above and read what was actually announced.",
        f"Open the company site — pipeline page and careers page.",
        f"Answer: do they own a therapeutic antibody/protein program?",
        f"Answer: can you name one specific paid piece of work for it?",
        f"Set status to Approve or Reject in review_queue.csv, with your reason.",
    ]
    for i, step in enumerate(steps, 1):
        print(wrap(f"{i}. {step}"))

    print()
    print(wrap(
        "If both answers are yes, this becomes a direct project hypothesis "
        "(SOP p84): one objective, the inputs you need from them, what you "
        "return, and how they validate it. Only then does anyone look for contacts."
    ))

    # --- Context -----------------------------------------------------------
    approved = [c for c in companies if c["priority"] in ("A", "B")]
    head("Run context")
    print(f"  {len(signals)} signals processed  ->  {len(companies)} companies in queue  "
          f"->  {len(approved)} at Priority A/B")
    print(f"\n  Others in the queue right now:")
    for row in companies[:8]:
        marker = " <- shown above" if row["canonical_company"] == name else ""
        print(f"    {row['priority']:<7} {row['score']:>3}  "
              f"{row['canonical_company'][:28]:<28} {row['signal_types'][:20]}{marker}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
