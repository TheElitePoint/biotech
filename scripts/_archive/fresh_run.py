"""One-shot fresh pipeline: enumerate -> intent -> final.xlsx.

Everything is collected live. No Tavily cache is read (use_cache=False), and the
universe is re-pulled from ClinicalTrials.gov, so the resulting final.xlsx contains
entirely new data. Progress prints unbuffered; the last line is the completion marker.

    python -u fresh_run.py
"""

from __future__ import annotations

import sys
import time
from collections import Counter

from intent_pipeline import universe, universe_intent as ui
from intent_pipeline.tavily import Tavily, TavilyError

WINDOW_DAYS = 365


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main() -> int:
    t0 = time.time()

    # 1. Fresh universe from ClinicalTrials.gov (all intervention queries).
    log("STEP 1/3  enumerating universe from ClinicalTrials.gov (live)...")
    companies = universe.build(max_pages=120)
    universe.save(companies)
    log(f"  universe: {len(companies)} companies")

    rows = universe.load()
    eligible = [r for r in rows if int(r.get("trial_count") or 0) >= 1]

    # 2. Registry intent (free) + live web intent on every company, no cache.
    log(f"STEP 2/3  scoring intent on {len(eligible)} companies (window {WINDOW_DAYS}d)...")
    reg = {}
    for r in eligible:
        it = ui.registry_intent(r, WINDOW_DAYS)
        if it:
            reg[r["company_key"]] = it
    log(f"  registry triggers (free): {len(reg)}")

    try:
        client = Tavily(use_cache=False)  # force live collection
    except TavilyError as exc:
        log(f"  Tavily unavailable ({exc}); registry-only run")
        client = None

    web = {}
    if client:
        log(f"  web-checking all {len(eligible)} companies live (this is the slow part)...")
        found = 0
        for i, r in enumerate(eligible, 1):
            it = ui.web_intent(client, r["canonical_company"], WINDOW_DAYS)
            if it:
                web[r["company_key"]] = it
                found += 1
            if i % 100 == 0:
                log(f"    {i}/{len(eligible)} checked, {found} web triggers, "
                    f"{int(time.time() - t0)}s elapsed")
        log(f"  web triggers: {found}")

    # 3. Assemble, score, write final.xlsx.
    log("STEP 3/3  assembling and writing final.xlsx...")
    by_key = {r["company_key"]: r for r in eligible}
    qualified = []
    for key in set(reg) | set(web):
        intent = ui._combine(reg.get(key), web.get(key))
        total, bottlenecks, modality = ui.score(by_key[key], intent)
        if key in reg and key in web:
            total = min(100, total + 8)
        qualified.append({**by_key[key], **intent, "score": total,
                          "bottlenecks": "; ".join(bottlenecks), "modality": modality})

    for r in qualified:
        r["priority"] = ("A" if r["score"] >= 80 else "B" if r["score"] >= 68
                         else "Review" if r["score"] >= 55 else "Reject")
    keep = [r for r in qualified if r["priority"] != "Reject"]

    ui.INTENT_CSV.parent.mkdir(parents=True, exist_ok=True)
    import csv
    fields = ["company_key", "canonical_company", "priority", "score", "trigger",
              "signal_type", "signal_date", "modality", "bottlenecks", "phases",
              "statuses", "conditions", "interventions", "trial_count", "evidence",
              "evidence_url", "note"]
    with ui.INTENT_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(keep, key=lambda r: -r["score"]))

    # Reuse the existing Excel writer via save_final --universe.
    import subprocess
    subprocess.run([sys.executable, "save_final.py", "--universe"], check=False)

    dt = int(time.time() - t0)
    log(f"DONE in {dt}s: {len(keep)} companies -> output/final.xlsx")
    log(f"  priority: {dict(Counter(r['priority'] for r in keep))}")
    log(f"  trigger : {dict(Counter(r['trigger'] for r in keep))}")
    log(f"  type    : {dict(Counter(r['signal_type'] for r in keep))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
