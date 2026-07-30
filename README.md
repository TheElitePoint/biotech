# Intent-Driven Prospecting Pipeline

Implements the discovery half of `sop.md` — from a public buying signal to a scored,
evidence-backed company record ready for human QA. Tavily is the collection layer in
place of the SOP's Apify actors; every gate, exclusion and scoring rule from the SOP is
enforced in code.

The pipeline stops exactly where the SOP says it must: at the review queue. It never
enriches contacts, never finds emails and never sends anything. Enrichment happens only
after a human sets a company to Approved (SOP pages 04 and 74).

## Setup

```powershell
python -m pip install -r requirements.txt
copy .env.example .env      # then paste your Tavily key into .env
```

Only `TAVILY_API_KEY` is required. `ANTHROPIC_API_KEY` is optional and turns on the
classification layer (SOP pages 81-84); without it the pipeline runs fully on the
deterministic rules and simply leaves the model-derived columns blank.

## Running

```powershell
python -m intent_pipeline.run --list-seeds           # see the seed bank
python -m intent_pipeline.run --seeds CAP --days 30  # capital triggers, last 30 days
python -m intent_pipeline.run --seeds JOB,PRG        # hiring + program triggers
python -m intent_pipeline.run --backfill             # 180-day window, all seeds
python -m intent_pipeline.run --no-extract           # cheaper, lower yield
python test_gates.py                                 # offline check, no API key needed
```

`--seeds` accepts seed IDs (`CAP-01`), families (`CAP`, `JOB`, `PRG`, `SCI`, `EXE`) or
signal types (`capital`, `hiring`). Results are cached on disk, so re-running while you
tune queries costs nothing.

Follow the SOP's build order: run one family at a time with `--max-results 15`, read the
raw signals, tighten the query in `config.py`, and only then widen the window. A seed is
production-ready when 70% of sampled records are classifiable (SOP page 59).

## Weekly operation

```powershell
python -m intent_pipeline.run                 # a weekly run
run_weekly.bat                                # same, for Task Scheduler
```

Register it with Windows Task Scheduler:

```powershell
schtasks /create /tn "Antibody Prospecting" /tr "C:\Users\aniru\biotech\run_weekly.bat" /sc weekly /d MON /st 07:00
```

**The report only ever shows movement.** `output/prospect_review_queue.xlsx` has a
*New This Week* tab holding companies that are new or have new evidence since the last
run — never the same list twice. A company you have already decided on cannot come back
(SOP page 38).

That works through `output/company_history.csv`, one persistent row per company holding
`first_seen`, `times_seen`, and your decision. Each run classifies its output against it:

| Movement | Meaning | In the report? |
|---|---|---|
| New | First time ever surfaced | Yes |
| Updated | Seen before, this run found new evidence or a higher score | Yes |
| Unchanged | Seen before, nothing new | No — stays in history |
| Suppressed | You set a DECISION on it | No — never resurfaces |

**Your decisions live in the spreadsheet.** Set the yellow DECISION column to Approved,
Rejected, Watching or Needs Info. The next run reads that column *before* writing the new
file and folds it into history. Close Excel before the scheduled run — the file is
replaced each time, and an open handle means that week's decisions are not picked up.

## What comes out

`output/prospect_review_queue.xlsx` is the deliverable — three tabs:

- **New This Week** — the queue. Only new and changed companies, with a dropdown on the
  DECISION column and the evidence URL as a live link.
- **All Companies** — everything ever surfaced, with decisions preserved across runs.
- **Run Summary** — counts and a short how-to-use legend.

The CSVs remain alongside it for anything you want to script against:

- `review_queue.csv` — the only file a reviewer needs. One row per company, sorted by
  priority, with the evidence URL, bottleneck, project hypothesis and the one open
  question blocking approval.
- `company_master.csv` — all resolved companies including rejects, deduplicated on
  domain (SOP page 29).
- `raw_signals.csv` — one row per signal with its decision and failed gates.
- `raw_signals.jsonl` — append-only, immutable raw evidence (SOP page 28).
- `actor_run_log.csv` — per-seed volume and approval counts, so you can retire seeds on
  evidence rather than instinct (SOP page 77).

## How a signal becomes a company

1. **Search** — each seed runs against Tavily with its own recency window, negative
   keywords and blocked domains.
2. **Normalize and dedupe** — one Raw Signal row per canonical URL plus update date.
3. **Resolve** — a signal from a company's own domain resolves strongly; a company name
   parsed from a news headline is marked unverified and can never auto-approve.
4. **Hard exclusions** — CRO/CDMO, diagnostics, reagents, non-buyers and named
   competitors are rejected before anything else is spent on them.
5. **Full-text pass** — surviving candidates get their page fetched and re-scored.
   Search snippets run ~200 characters, which is far too short to prove a bottleneck or
   a program stage; in testing this pass roughly doubled the qualified set. Extraction
   runs *after* the exclusions so no credits are spent on a known CRO (SOP page 78).
   Tune with `--extract-floor`, or skip entirely with `--no-extract`.
6. **Evidence extraction** — modality, program stage, bottleneck family and funding
   language, each with the matched phrase retained.
7. **Score and route** — the SOP's six-factor model, then A/B/Review/Reject.
8. **Model layer (optional)** — extracts target, disease and a project hypothesis. It can
   downgrade a record but never rescue one the deterministic gates rejected.
9. **Company master** — signals collapse per company; independent trigger families on the
   same company add a corroboration bonus.

### Two rules that keep publishers out of the queue

Trade press is the main source of noise, because an article about ten biotechs looks
structurally like a company's own press release. Two rules do most of the work, and both
are worth understanding before you loosen them:

- A domain resolves as the company only if the domain's own name appears in the page
  title or opening text. A company's release names the company; an article surveying the
  sector does not name its publisher.
- The publisher's branding suffix (`... - BioTechniques`) is stripped before that check,
  since otherwise every trade headline appears to name its owner.

Enumerating publishers by hand was the first approach and it kept losing to the long
tail. Requiring positive evidence generalizes to outlets the list has never seen.

Two safeguards are stricter than the raw score. A record that fails the modality gate or
the project-clarity gate cannot reach A or B regardless of points, and a company whose
domain was never verified cannot reach Approve at all.

## Intent ideas worth adding

The SOP's six triggers on page 17 are all *announcement*-shaped: they fire when a company
publishes something. That biases the pipeline toward companies with a communications
budget and means you arrive at the same time as everyone else reading the same press
release. The signals below are mostly *behavioural* — they fire when a company does
something, often weeks before it announces anything — and they are the ones I would add
to the SOP's trigger library.

**Signals that precede the announcement**

- *Careers page delta.* Snapshot each watched company's careers page weekly and diff it.
  A protein-engineering role appearing is a signal; the same role still open after 90 days
  is a much stronger one, because it means they have been unable to hire the capability
  and the work is still not getting done. That gap is the single most direct evidence of
  outsourcing appetite in the entire signal set, and nobody publishes it.
- *Pipeline page delta.* Diff `/pipeline` on a schedule. A program quietly moving from
  Discovery to Lead Optimization, or a new target row appearing, precedes the press
  release by months. A program *disappearing* is equally interesting — a paused asset is
  the SOP's own milestone trigger for next-generation design work (page 17).
- *Job description depth, not job title.* The SOP treats hiring as one signal. But a
  posting that names the modality, the target class and the specific assays tells you the
  program's exact bottleneck in the company's own words. Rank hiring signals by how much
  technical detail the description contains, not by seniority of the title.
- *Conference abstract acceptance.* Abstract titles publish weeks before the meeting and
  state the scientific claim precisely. A company presenting preclinical binder data at
  PEGS or AET has a program at exactly the stage where design work is purchasable, and the
  presenting author is a named internal champion (SOP page 56).

**Signals of a capability gap rather than activity**

- *First computational hire.* A company hiring its first computational or ML person into a
  wet-lab-heavy team is building the capability the platform sells. That is a genuine fork
  — either they buy while they build, or they will not buy for two years. It deserves its
  own trigger and a different message from a pure capacity signal.
- *Absence of the counter-signal.* Invert the competitor check. A company with an active
  antibody program and *no* computational design staff on LinkedIn, no in-silico language
  on its technology page and no AI-design partner announced is a better prospect than one
  with a small internal team. The SOP checks for competitors; it does not check for the
  absence of an internal substitute, which is the actual buying condition.
- *Vendor-adjacency.* Companies already paying external partners for wet-lab screening or
  structural work have both a procurement path and a proven willingness to buy discovery
  services. A named CRO partner in a press release is a positive budget signal even though
  CROs themselves are excluded as prospects.
- *Recent expensive failure.* A discontinued program, a failed candidate or a disclosed
  developability problem in a filing is the strongest possible bottleneck evidence, and it
  is stated by the company rather than inferred. SOP page 42 warns against treating
  clinical bad news as buying intent, which is right for late-stage failures — but a
  *preclinical* candidate that failed on immunogenicity or aggregation is a design problem
  with a named owner and a live budget.

**Signals of who to talk to and when**

- *New scientific leader in the first 90 days.* A newly hired CSO or Head of Antibody
  Discovery has budget discretion, a mandate to change how things are done and no
  incumbent vendor loyalty. Their start date is public on LinkedIn. This is a timing
  trigger about a *person* rather than a program, which the SOP's model currently has no
  slot for.
- *Grant milestone dates, not grant awards.* The SOP mines NIH RePORTER for new awards.
  The better signal is the budget-period end date on an existing SBIR: that is a hard
  deadline with allocated money and a specific deliverable, and it tells you exactly when
  the team is under pressure.
- *Patent filing without a matching publication.* An assignee filing on a target with no
  corresponding paper is running an active undisclosed program. Filing date beats
  publication date by 18 months, so search by priority date where the source allows.

**A structural change worth making**

The SOP scores each signal in isolation and keeps the highest. Intent is really about
*accumulation*: a company with a funding announcement, two open protein-engineering roles
and a new pipeline program in the same quarter is a far better prospect than one with a
single strong signal, and its true score is higher than any of its parts. This pipeline
implements a first version of that (`corroboration_bonus` in `store.py`), but the richer
version is a per-company intent timeline where independent trigger families compound and
old signals decay, rather than a single best-signal score. I would make that the primary
ranking once you have a few weeks of runs to calibrate against.

## Adding your own seeds

Add a `Seed` to `SEEDS` in `config.py` with a signal type that already exists in
`SIGNAL_STRENGTH`. Everything downstream — negative keywords, recency decay, run logging —
picks it up automatically. New exclusion patterns, competitor domains and bottleneck
vocabulary go in the same file; nothing is hardcoded elsewhere.
