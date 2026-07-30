# n8n Workflow — Antibody Intent Prospecting

Live at https://vccc.app.n8n.cloud/workflow/QurN7WcQQvaYKZyd (personal project).
Source of truth is [workflow.ts](workflow.ts), built with the n8n Workflow SDK.

Same pipeline as the Python version in the parent directory, running on a schedule
instead of on your machine. Both enforce the identical gates from `sop.md`.

## Before the first run

The workflow is created **inactive**. Three things to set up:

1. **Tavily credential.** Open either HTTP Request node ("Tavily Search" or "Tavily
   Extract Full Page"), and create a Bearer Auth credential named `Tavily API` with your
   key as the token. Both nodes share it. Credential auto-assignment skips HTTP Request
   nodes, so this is manual.
2. **Google Sheet.** Create a spreadsheet, add a tab named exactly `review_queue`, then
   pick that document in the "Upsert Into Review Queue" node. The Google Sheets
   credential was auto-assigned. Column headers are created on first write.
3. **Test with a trimmed seed list.** Open "Build Intent Seed Queries" and cut `SEEDS`
   down to two or three entries, then run manually. A full 21-seed run makes 21 search
   calls plus one extract call per surviving signal — worth confirming the wiring first.

Activate the workflow only once a manual run produces sensible rows.

## Flow

```
Schedule (daily 07:00)
  → Build Intent Seed Queries          21 seeds, five trigger families
  → Loop Over Seeds  ──────────────►   Tavily Search → Attach Seed Metadata
  → Resolve, Exclude and Score         dedupe, resolve company, hard exclusions, score
  → Survived Hard Exclusions           filter: not excluded AND score ≥ 25
  → Loop Over Surviving Signals ───►   Tavily Extract → Merge Page Text
  → Rescore and Build Company Master   one row per company + corroboration bonus
  → Qualified For Human Review         filter: priority ≠ Reject
  → Upsert Into Review Queue           Google Sheets, keyed on company_key
```

The two loops exist to keep one failing request from killing the run. Both HTTP nodes use
`onError: continueRegularOutput` with retries, so a single dead URL costs one row, not the
execution.

## Where the SOP rules live

- **Hard exclusions** (SOP p20) — "Resolve, Exclude and Score", `EXCL` object. Runs before
  any extract call so no credits are spent on a known CRO (SOP p78).
- **Scoring** (SOP p24/85) — same node. Six factors, capped, routed A/B/Review/Reject.
- **Intent weighting** (SOP p17) — `STRENGTH` map times recency decay.
- **Company dedupe** (SOP p29/79) — "Rescore and Build Company Master", grouped on domain.
- **Enrichment boundary** (SOP p04) — enforced by omission. Nothing downstream of the
  review queue exists. Contact and email enrichment stay manual until a human sets
  status to Approved.

## Tuning

Seed bank, exclusion patterns, competitor domains and bottleneck vocabulary are all in the
Code nodes — no other node needs touching. Two behaviours worth knowing before you loosen
anything:

- A record failing the modality or project-clarity gate cannot reach Priority A or B
  regardless of score.
- A company whose domain was never verified cannot reach Approve, only Review.

Both exist because scoring alone lets bad records through. They were added after live
runs put trade publications in the queue as prospects.

## Differences from the Python version

The Python pipeline has an optional Anthropic classification layer (SOP p81-84) that
extracts target, disease and a project hypothesis. This workflow does not — it stops at
the deterministic gates. Adding it means an OpenAI or Anthropic node with a structured
output parser after "Merge Page Text Into Signal". Worth doing once the seed bank is
tuned, since the model layer is only as good as what survives the gates.

The Python version also writes an `actor_run_log.csv` tracking per-seed approval rates
(SOP p77). To get that here, add a second Sheets node on the "Rescore" branch writing one
row per seed_id.
