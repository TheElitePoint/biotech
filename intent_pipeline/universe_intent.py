"""Attach live intent triggers to companies in the universe.

Two kinds of trigger, deliberately ordered cheapest-first:

1. Registry intent — free, already in hand. A trial registered or updated inside the
   window is a dated, first-party program signal (SOP page 33). No API call needed.
2. Web intent — one targeted Tavily search per company, only for those the registry
   could not already qualify. Company-scoped search resolves far better than
   open-ended discovery because the company is named in the query.

The output is the universe filtered to companies with a live trigger, which is what
the SOP asks for: modality fit alone is not a prospect (SOP page 17).

    python -m intent_pipeline.universe_intent --days 180 --limit 400
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .config import BOTTLENECK_TERMS, MODALITY_TERMS, SIGNAL_STRENGTH
from .tavily import Tavily, TavilyError
from .universe import OUT, load as load_universe

INTENT_CSV = OUT / "universe_intent.csv"

# Registry states that indicate a live or forward-moving program.
ACTIVE_STATUSES = {
    "RECRUITING",
    "NOT_YET_RECRUITING",
    "ENROLLING_BY_INVITATION",
    "ACTIVE_NOT_RECRUITING",
}

EARLY_PHASES = {"EARLY_PHASE1", "PHASE1", "PHASE1, PHASE2", "PHASE2"}


def _hits(text: str, terms: list[str]) -> list[str]:
    found = []
    for term in terms:
        pattern = term if any(c in term for c in r"\b[](){}|+*?^$") else re.escape(term)
        if re.search(pattern, text, re.I):
            found.append(term)
    return found


def registry_intent(row: dict[str, str], days: int) -> dict[str, Any] | None:
    """Trigger derived from the trial registry alone. Costs nothing.

    Keyed on the newest update to a *live* trial, not to any trial. A recent edit to
    a completed 2019 study is housekeeping, not intent.
    """
    updated = (row.get("last_active_update") or "").strip()
    if not updated:
        return None
    try:
        when = datetime.strptime(updated[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    age = (date.today() - when).days
    if age > days:
        return None

    active_phases = set((row.get("active_phases") or "").split("; "))
    statuses = set((row.get("statuses") or "").split("; ")) & ACTIVE_STATUSES
    nct = (row.get("active_nct") or "").strip()

    return {
        "trigger": "registry",
        "signal_type": "program",
        "signal_date": when.isoformat(),
        "age_days": age,
        "early_phase": bool(active_phases & EARLY_PHASES),
        "evidence": (
            f"live trial {nct} updated {when.isoformat()}"
            + (f", status {'/'.join(sorted(statuses))}" if statuses else "")
        ),
        "evidence_url": f"https://clinicaltrials.gov/study/{nct}" if nct else "",
    }


def web_intent(client: Tavily, company: str, days: int) -> dict[str, Any] | None:
    """One targeted search. The company is named, so results resolve reliably."""
    query = (
        f'"{company}" (funding OR "Series A" OR "Series B" OR hiring OR '
        f'"antibody discovery" OR "protein engineering" OR "development candidate")'
    )
    try:
        results = client.search(
            type(
                "S",
                (),
                {
                    "seed_id": "UNI-WEB",
                    "query": query,
                    "signal_type": "program",
                    "depth": "basic",
                    "days": days,
                    "max_results": 5,
                    "include_domains": [],
                    "exclude_domains": [],
                },
            )()
        )
    except TavilyError:
        return None

    for item in results:
        title = item.get("title") or ""
        content = item.get("content") or ""
        blob = f"{title} {content}"
        # The company must actually be named, or this is somebody else's news.
        token = re.sub(r"[^a-z0-9]", "", company.lower())[:12]
        if token and token not in re.sub(r"[^a-z0-9]", "", blob.lower()):
            continue

        low = blob.lower()
        if any(t in low for t in ("series a", "series b", "raises $", "financing", "funding round")):
            signal_type = "capital"
        elif any(t in low for t in ("hiring", "job", "we are looking for", "join our team")):
            signal_type = "hiring"
        elif any(t in low for t in ("development candidate", "ind-enabling", "nomination")):
            signal_type = "milestone"
        else:
            signal_type = "program"

        return {
            "trigger": "web",
            "signal_type": signal_type,
            "signal_date": (item.get("published_date") or "")[:16],
            "age_days": None,
            "early_phase": False,
            "evidence": title[:160],
            "evidence_url": item.get("url", ""),
        }
    return None


# Which enumeration query a company matched is itself modality evidence: the registry
# classified the intervention, which is stronger than string-matching a trade name.
# "XmAb541" and "IMA402" are antibodies; neither contains the word.
QUERY_MODALITY = {
    "antibody": "antibody (registry-classified)",
    "monoclonal antibody": "monoclonal antibody",
    "bispecific antibody": "bispecific antibody",
    "antibody drug conjugate": "antibody-drug conjugate",
    "nanobody": "nanobody",
    "fusion protein": "fusion protein",
    "recombinant protein": "engineered protein",
}


def score(row: dict[str, str], intent: dict[str, Any]) -> tuple[int, list[str], str]:
    """Reduced form of the SOP model, using registry fields as the evidence base."""
    text = " ".join(
        [row.get("interventions", ""), row.get("conditions", ""), row.get("canonical_company", "")]
    ).lower()

    # Prefer the registry's own classification; fall back to text for extra detail.
    matched = [q.strip() for q in (row.get("matched_queries") or "").split(";") if q.strip()]
    modality = [QUERY_MODALITY[q] for q in matched if q in QUERY_MODALITY]
    modality += [m for m in _hits(text, MODALITY_TERMS["approve"]) if m not in modality]

    bottlenecks = [fam for fam, terms in BOTTLENECK_TERMS.items() if _hits(text, terms)]

    strong = any(
        q in matched for q in ("antibody", "monoclonal antibody", "bispecific antibody",
                               "antibody drug conjugate", "nanobody")
    )

    fit = 0
    if strong or _hits(text, MODALITY_TERMS["approve"]):
        fit += 12
    elif modality or _hits(text, MODALITY_TERMS["conditional"]):
        fit += 6
    if intent.get("early_phase"):
        fit += 7
    if bottlenecks:
        fit += min(6, 3 * len(bottlenecks))

    age = intent.get("age_days")
    if age is None:
        recency = 0.75
    elif age <= 30:
        recency = 1.0
    elif age <= 90:
        recency = 0.8
    else:
        recency = 0.55
    intent_score = round(25 * SIGNAL_STRENGTH.get(intent["signal_type"], 0.7) * recency)

    trials = int(row.get("trial_count") or 0)
    budget = min(15, 4 + 2 * min(trials, 4) + (3 if intent["signal_type"] == "capital" else 0))
    # Registry data names the program and its stage but almost never the design
    # bottleneck — that needs a paper, a job ad or a pipeline page. So project
    # clarity stays capped here, and these companies land in Review rather than
    # Approve. That is the correct SOP outcome (G3/G5), not a scoring shortfall.
    clarity = 10 if bottlenecks else 5
    if strong or modality:
        clarity += 5
    buyer = 6
    confidence = 5 if intent["trigger"] == "registry" else 3

    total = min(fit, 25) + intent_score + min(clarity, 20) + budget + buyer + confidence
    return total, bottlenecks, "; ".join(modality[:3])


# A funding round or hiring push is stronger buying intent than a live trial. When a
# company shows both, the report should lead with the stronger one but record that the
# registry program is also live — that combination is the best evidence available.
_STRONGER = {"capital": 4, "milestone": 3, "program": 2, "hiring": 2, "execution": 1, "scientific": 1}


def _combine(reg: dict[str, Any] | None, web: dict[str, Any] | None) -> dict[str, Any]:
    """Merge a registry and a web trigger into one intent record."""
    if reg and web:
        lead = web if _STRONGER.get(web["signal_type"], 0) >= _STRONGER.get(reg["signal_type"], 0) else reg
        other = reg if lead is web else web
        return {
            **lead,
            "trigger": "registry+web",
            "evidence": f"{lead['evidence']} | also: {other['evidence']}",
        }
    return reg or web  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate the universe on live intent")
    parser.add_argument("--days", type=int, default=180, help="Trigger recency window")
    parser.add_argument("--limit", type=int, default=0, help="Max companies to web-check (0 = none)")
    parser.add_argument("--min-trials", type=int, default=1)
    parser.add_argument(
        "--web-all",
        action="store_true",
        help="Web-check every company, including those with a registry trigger, and combine signals",
    )
    args = parser.parse_args()

    universe = load_universe()
    if not universe:
        print("No universe found. Run: python -m intent_pipeline.universe")
        return 1

    print(f"Universe: {len(universe)} companies. Checking intent (window {args.days}d)...\n")

    eligible = [r for r in universe if int(r.get("trial_count") or 0) >= args.min_trials]
    reg_intent: dict[str, dict[str, Any]] = {}
    for row in eligible:
        intent = registry_intent(row, args.days)
        if intent:
            reg_intent[row["company_key"]] = intent

    print(f"Registry intent (free): {len(reg_intent)} companies with a live trigger")

    # Who to web-check. --web-all covers everyone; otherwise only registry misses.
    if args.web_all:
        to_check = eligible
    else:
        to_check = [r for r in eligible if r["company_key"] not in reg_intent]
    print(f"No registry trigger   : {len(eligible) - len(reg_intent)} companies")

    web_hits: dict[str, dict[str, Any]] = {}
    if args.limit and to_check:
        budget = min(args.limit, len(to_check))
        scope = "all companies" if args.web_all else "registry misses"
        print(f"\nWeb-checking {budget} ({scope}, 1 search each; cached ones are free)...")
        try:
            client = Tavily()
        except TavilyError as exc:
            print(f"  skipped: {exc}")
            budget = 0
        if budget:
            found = 0
            for i, row in enumerate(to_check[:budget], 1):
                intent = web_intent(client, row["canonical_company"], args.days)
                if intent:
                    web_hits[row["company_key"]] = intent
                    found += 1
                if i % 50 == 0:
                    print(f"  {i}/{budget} checked, {found} web triggers found")
                time.sleep(0.05)
            print(f"  web intent: {found} triggers")

    # Assemble one record per company from whichever triggers it has.
    by_key = {r["company_key"]: r for r in eligible}
    qualified: list[dict[str, Any]] = []
    for key in set(reg_intent) | set(web_hits):
        intent = _combine(reg_intent.get(key), web_hits.get(key))
        row = by_key[key]
        total, bottlenecks, modality = score(row, intent)
        # Two independent triggers on one company is stronger than either alone (SOP p79).
        if key in reg_intent and key in web_hits:
            total = min(100, total + 8)
        qualified.append({**row, **intent, "score": total,
                          "bottlenecks": "; ".join(bottlenecks), "modality": modality})

    qualified.sort(key=lambda r: -r["score"])
    for row in qualified:
        row["priority"] = (
            "A" if row["score"] >= 80 else "B" if row["score"] >= 68
            else "Review" if row["score"] >= 55 else "Reject"
        )

    keep = [r for r in qualified if r["priority"] != "Reject"]

    fields = [
        "company_key", "canonical_company", "priority", "score", "trigger", "signal_type",
        "signal_date", "modality", "bottlenecks", "phases", "statuses", "conditions",
        "interventions", "trial_count", "evidence", "evidence_url", "note",
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    with INTENT_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(keep)

    from collections import Counter
    print(f"\n{len(keep)} companies with a live intent trigger -> {INTENT_CSV}")
    print(f"  priority: {dict(Counter(r['priority'] for r in keep))}")
    print(f"  trigger : {dict(Counter(r['trigger'] for r in keep))}")
    print(f"  type    : {dict(Counter(r['signal_type'] for r in keep))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
