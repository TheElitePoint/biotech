"""CLI orchestrator.

    python -m intent_pipeline.run --seeds CAP,JOB --days 30 --max-results 15
    python -m intent_pipeline.run --backfill        # 180-day window, all seeds
    python -m intent_pipeline.run --list-seeds
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

from . import classify, excel, history, store
from .config import SEEDS, active_seeds
from .gates import route
from .signals import Signal, dedupe, normalize
from .tavily import Tavily, TavilyError


def _load_dotenv() -> None:
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(description="Intent-driven biotech prospecting run")
    parser.add_argument(
        "--seeds",
        default="",
        help="Comma-separated seed IDs, families (CAP/JOB/PRG/SCI/EXE) or signal types",
    )
    parser.add_argument("--days", type=int, help="Override the date window for all seeds")
    parser.add_argument("--max-results", type=int, help="Override per-seed result cap")
    parser.add_argument("--depth", choices=["basic", "advanced"], help="Tavily search depth")
    parser.add_argument(
        "--backfill", action="store_true", help="180-day window across every active seed"
    )
    parser.add_argument("--no-llm", action="store_true", help="Skip the model layer")
    parser.add_argument(
        "--no-extract", action="store_true", help="Skip the full-text extraction pass"
    )
    parser.add_argument(
        "--extract-floor",
        type=int,
        default=25,
        help="Minimum first-pass score before spending an extraction call (default 25)",
    )
    parser.add_argument("--no-cache", action="store_true", help="Ignore the local Tavily cache")
    parser.add_argument("--list-seeds", action="store_true")
    args = parser.parse_args(argv)

    if args.list_seeds:
        for seed in SEEDS:
            print(f"{seed.seed_id:8} {seed.signal_type:10} {seed.status:8} {seed.query}")
        return 0

    only = [s for s in args.seeds.split(",") if s.strip()] or None
    seeds = active_seeds(only)
    if not seeds:
        print("No seeds matched.", file=sys.stderr)
        return 1

    for seed in seeds:
        if args.backfill:
            seed.days = 180
        if args.days:
            seed.days = args.days
        if args.max_results:
            seed.max_results = args.max_results
        if args.depth:
            seed.depth = args.depth

    try:
        client = Tavily(use_cache=not args.no_cache)
    except TavilyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    use_llm = not args.no_llm and classify.available()
    print(f"Running {len(seeds)} seeds | LLM layer: {'on' if use_llm else 'off'}\n")

    signals: list[Signal] = []
    per_seed: dict[str, int] = {}
    for seed in seeds:
        try:
            items = client.search(seed)
        except TavilyError as exc:
            print(f"  {seed.seed_id}: search failed — {exc}", file=sys.stderr)
            store.append_run_log(
                {"seed_id": seed.seed_id, "query": seed.query, "status": "error",
                 "raw_results": 0, "note": str(exc)[:200]}
            )
            continue
        store.save_raw(items)
        per_seed[seed.seed_id] = len(items)
        signals.extend(normalize(item) for item in items)
        print(f"  {seed.seed_id:8} {len(items):3} results  ({seed.days}d)  {seed.query[:60]}")

    signals = dedupe(signals)
    print(f"\n{len(signals)} unique signals after dedupe. Applying gates...")

    # Pass 1 on the search snippet, purely to discard the obvious.
    first_pass = [(sig, route(sig)) for sig in signals]

    # Pass 2: search snippets are too short to prove a bottleneck or program stage,
    # so fetch full page text — but only for records that survived the exclusions.
    # Spending extraction credits on a known CRO is exactly what SOP page 78 forbids.
    if not args.no_extract:
        candidates = [
            sig
            for sig, verdict in first_pass
            if not verdict.exclusion_reason and verdict.score >= args.extract_floor
        ]
        if candidates:
            print(f"Extracting full text for {len(candidates)} surviving candidates...")
            pages = client.extract([s.source_url for s in candidates])
            enriched = 0
            for sig in candidates:
                text = pages.get(sig.source_url, "")
                if len(text) > len(sig.raw_text):
                    sig.raw_text = text[:20000]
                    enriched += 1
            print(f"  {enriched} pages enriched; re-scoring.")
            signals = [sig for sig, _ in first_pass]

    records = []
    for sig in signals:
        verdict = route(sig)
        llm = None
        if use_llm and verdict.decision != "Reject":
            llm = classify.classify(sig, verdict)
            verdict = classify.reconcile(verdict, llm)
        records.append((sig, verdict, llm))

    store.save_signals(records)
    companies = store.build_company_master(records)
    store.save_companies(companies)

    # Pull any decisions the reviewer made in last week's spreadsheet before
    # classifying this run, so a company they closed does not resurface.
    adopted = excel.sync_decisions()
    if adopted:
        print(f"\nRead {adopted} reviewer decision(s) from last week's Excel file.")

    tracked = [c for c in companies if c["priority"] != "Reject"]
    weekly, counts = history.apply(tracked)
    fresh = [r for r in weekly if r["movement"] in ("New", "Updated")]
    report = excel.write(fresh, history.all_rows(), counts)

    decisions = Counter(v.decision for _, v, _ in records)
    excluded = Counter(
        v.exclusion_reason.split(":")[0] for _, v, _ in records if v.exclusion_reason
    )
    priorities = Counter(c["priority"] for c in companies)

    for seed in seeds:
        seed_records = [(s, v) for s, v, _ in records if s.seed_id == seed.seed_id]
        approved = sum(1 for _, v in seed_records if v.decision == "Approve")
        store.append_run_log(
            {
                "seed_id": seed.seed_id,
                "query": seed.query,
                "signal_type": seed.signal_type,
                "days": seed.days,
                "status": "ok",
                "raw_results": per_seed.get(seed.seed_id, 0),
                "unique_signals": len(seed_records),
                "approved": approved,
                "rejected": sum(1 for _, v in seed_records if v.decision == "Reject"),
                "note": "",
            }
        )

    print(f"\nSignal decisions: {dict(decisions)}")
    if excluded:
        print(f"Hard exclusions:  {dict(excluded)}")
    print(f"Companies:        {len(companies)}  {dict(priorities)}")
    print(
        f"Since last run:   {counts['New']} new, {counts['Updated']} updated, "
        f"{counts['Unchanged']} unchanged, {counts['Suppressed']} closed by reviewer"
    )

    print(f"\n>> EXCEL REPORT -> {report}")
    print(f"   Review queue (csv) -> {store.REVIEW_CSV}")
    print(f"   History            -> {history.HISTORY}")

    if fresh:
        print(f"\nNew and changed this run ({len(fresh)}):")
        for c in fresh:
            print(
                f"  {c['movement']:<9} {c['priority']:<7} {c['score']:>3}  "
                f"{c['canonical_company'][:28]:28} {c['signal_types'][:24]}"
            )
    else:
        print("\nNothing new since the last run. The Excel file lists no companies to review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
