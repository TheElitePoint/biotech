# Phase 1 Engineering Brief: Therapeutic Company Intent Data Pipeline

## 1. Objective

Build a production-ready data pipeline that continuously discovers therapeutic biotech and pharma companies showing active antibody or protein-engineering buying intent.

The pipeline must convert public-source records into a deduplicated, evidence-backed company dataset containing:

1. Canonical company identity
2. Therapeutic asset ownership
3. Antibody or protein modality
4. Named program, target or asset
5. Program stage
6. Recent intent trigger
7. Scientific bottleneck
8. Possible paid project
9. Evidence and confidence
10. Approve, Review or Reject recommendation

The output is not a generic lead list.

The required logical chain is:

`Public signal → company resolution → therapeutic ownership → program → modality → stage → bottleneck → intent trigger → project hypothesis → human decision`

Do not build contact enrichment, email discovery, outreach generation or sequencing in Phase 1. The SOP requires company approval before buyer or email enrichment.

---

# 2. Phase 1 Scope

## In scope

* Source ingestion
* Raw evidence storage
* Schema normalization
* Company-name and domain resolution
* Therapeutic-owner verification
* Biomedical entity extraction
* Hard-exclusion filtering
* Signal deduplication
* Company-level signal aggregation
* Intent scoring
* Paid-project hypothesis generation
* Human review queue
* Pipeline-quality dashboard
* Source and query benchmarking

## Out of scope

* LinkedIn employee enrichment
* Email enrichment
* Buyer contact information
* Automated outreach
* CRM sequencing
* Autonomous final approval
* General AI drug-discovery company lists
* CRO, CDMO or diagnostics prospecting

---

# 3. Initial Source Priority

Implement sources in this order.

## Tier 1A: Company-owned sources

1. Company news and press releases
2. Company pipeline pages
3. Company technology pages
4. Company careers pages
5. Company publications pages

These sources are the primary authority for program ownership, modality, stage and company direction.

## Tier 1B: High-velocity external signals

1. Google News
2. Public job listings
3. PubMed

## Tier 2

1. ClinicalTrials.gov
2. NIH RePORTER
3. Google Patents or patent APIs
4. Conference abstracts
5. SEC filings for public biotech companies

The SOP prioritizes company news, pipeline pages and careers daily, PubMed twice weekly, and trials, grants and patents weekly or less frequently.

---

# 4. System Architecture

Use a staged architecture so raw evidence is never mixed with interpreted or approved data.

## Layer 1: Source Connectors

Create a separate connector for every source.

Each connector must return a common envelope:

```json
{
  "source_type": "company_news",
  "source_item_id": "source-native-id",
  "source_url": "https://...",
  "query_id": "QUERY-001",
  "query_text": "\"antibody affinity maturation\" biotech",
  "published_at": "2026-07-20T00:00:00Z",
  "collected_at": "2026-08-04T10:00:00Z",
  "title": "Raw source title",
  "raw_text": "Full source content",
  "source_metadata": {},
  "actor_run_id": "optional-run-id"
}
```

Never delete or overwrite the original source record.

## Layer 2: Raw Signal Store

Store immutable source records in a `raw_signals` table.

Minimum fields:

```text
signal_id
source_type
source_item_id
source_url
query_id
query_text
published_at
collected_at
title
raw_text
raw_json
content_hash
actor_run_id
ingestion_status
ingestion_error
```

Use object storage for large raw HTML, JSON and markdown payloads.

## Layer 3: Normalization

Normalize all records into a common scientific signal schema.

```json
{
  "signal_id": "SIG-001",
  "company_candidate": "Example Therapeutics",
  "organization_mentions": [],
  "target": null,
  "disease": null,
  "modality": null,
  "antibody_format": null,
  "asset_name": null,
  "asset_stage": null,
  "scientific_problem": null,
  "signal_type": null,
  "signal_date": null,
  "evidence_spans": [],
  "field_confidence": {},
  "normalization_version": "v1.0"
}
```

Every extracted value must include an evidence span.

Example:

```json
{
  "asset_stage": {
    "value": "lead optimization",
    "confidence": 93,
    "evidence_text": "the company is advancing the program through lead optimization",
    "source_url": "https://...",
    "character_start": 1204,
    "character_end": 1272
  }
}
```

If the source does not support a value, return `null`.

The SOP explicitly requires unresolved fields to remain null instead of being guessed.

## Layer 4: Company Resolver

Convert company candidates, author affiliations, sponsors and assignees into a canonical organization.

Create a `company_master` table:

```text
company_id
canonical_name
normalized_domain
legal_name
aliases
former_names
country
company_type
private_public
funding_stage
last_funding_date
last_funding_amount
therapeutic_owner_status
competitor_status
company_status
created_at
updated_at
```

Resolver output:

```json
{
  "canonical_company": "Example Therapeutics",
  "domain": "exampletherapeutics.com",
  "aliases": ["Example Bio"],
  "relationship_to_asset": "owner",
  "therapeutic_owner_confirmed": true,
  "evidence": [
    {
      "source_url": "https://...",
      "evidence_text": "Example Therapeutics is developing..."
    }
  ],
  "confidence": 94,
  "unresolved_question": null
}
```

Allowed ownership statuses:

```text
owner
co_owner
licensee
originator
service_provider
academic_institution
manufacturer
unclear
```

Do not infer commercial ownership from publication affiliation alone. Prefer company pages, trials, patents, grants, filings and registries.

## Layer 5: Hard-Exclusion Engine

Run exclusions before expensive enrichment or scoring.

Immediately reject:

```text
CRO
CDMO
contract discovery provider
manufacturer
diagnostics-only company
assay company
reagent supplier
catalogue antibody supplier
academic-only institution
consultancy
investor
accelerator
direct AI antibody-design competitor
service provider without therapeutic ownership
```

Store:

```json
{
  "excluded": true,
  "exclusion_category": "CRO",
  "exclusion_reason": "Company sells antibody engineering services and does not own the therapeutic asset.",
  "evidence_text": "...",
  "source_url": "https://..."
}
```

A hard exclusion must override every numeric score.

## Layer 6: Biomedical Classification

Classify:

### Supported modalities

```text
monoclonal antibody
bispecific
multispecific
antibody fragment
Fab
scFv
nanobody
engineered protein
therapeutic binder
fusion protein
cytokine engineering
ADC binder engineering
```

### Supported stages

```text
discovery
binder generation
lead generation
lead optimization
candidate selection
preclinical
IND-enabling
early clinical with active discovery expansion
```

### Bottleneck taxonomy

```text
de_novo_design
low_binder_diversity
low_hit_rate
affinity
potency
specificity
cross_reactivity
epitope_coverage
humanization
immunogenicity
sequence_liability
stability
aggregation
expression
solubility
manufacturability
format_compatibility
bispecific_balancing
candidate_shortlisting
wet_lab_capacity
unknown
```

Each bottleneck must have:

```text
value
explicit_or_inferred
confidence
evidence
```

Never store an inferred bottleneck as an established fact.

## Layer 7: Intent Event Detection

Classify every signal into one or more intent types:

```text
funding
hiring
new_program
pipeline_expansion
lead_optimization
candidate_selection
candidate_nomination
publication
patent
grant
conference_data
trial_update
new_partnership
website_change
team_expansion
manufacturing_preparation
program_pause
next_generation_program
```

Store all intent events separately:

```text
intent_event_id
company_id
signal_id
intent_type
event_date
strength
recency_score
program_name
evidence_text
source_url
confidence
```

Do not use a single job listing, funding announcement or trial as sufficient buying intent.

Build company intent from multiple independent signals.

---

# 5. Signal-Stacking Logic

Calculate intent at company-program level, not only company level.

A strong company should usually have:

```text
Ownership evidence
+ relevant therapeutic program
+ supported modality
+ relevant program stage
+ recent commercial or scientific trigger
+ visible or inferable bottleneck
```

Recommended signal combinations:

## Very strong

```text
Funding + named pipeline expansion
Funding + lead optimization milestone
New program + antibody engineering hiring
Publication limitation + active commercial asset
Patent + recent funding + active pipeline
Candidate selection + developability hiring
Grant + commercial company + defined milestone
```

## Medium

```text
Hiring + active pipeline
Publication + confirmed ownership
Patent + active company
Conference presentation + named preclinical program
```

## Weak

```text
Funding without use of proceeds
A single job listing
A clinical trial with no discovery pipeline
Generic AI or platform language
Old publication without a current trigger
```

---

# 6. Paid-Project Hypothesis Generator

For every company that passes ownership, modality and stage checks, generate one narrow project hypothesis.

Required format:

```json
{
  "program": "Named program or target",
  "objective": "One concrete design or optimization objective",
  "supporting_evidence": [],
  "client_inputs": [
    "existing sequences",
    "assay data",
    "target constraints"
  ],
  "platform_outputs": [
    "ranked candidate panel",
    "sequence-level rationale",
    "developability risk ranking"
  ],
  "validation_path": "Company internal lab or named wet-lab partner",
  "likely_buyer_titles": [],
  "unresolved_risk": null,
  "project_confidence": 82
}
```

Allowed project types:

```text
focused de novo design pilot
affinity maturation
lead optimization
humanization
specificity optimization
developability optimization
bispecific component selection
candidate shortlisting
recurring target-design support
```

Do not generate generic partnership recommendations.

Do not invent internal data, sequences, performance expectations or validation capacity.

Route the record to Review when client inputs or the validation path are unknown.

---

# 7. Qualification Decision Engine

Use deterministic gates before scoring.

## Gate 1: Therapeutic ownership

```text
Pass: Company owns, co-owns or licenses the therapeutic asset.
Fail: Service provider, academic institution or unclear ownership.
```

## Gate 2: Modality fit

```text
Pass: Supported antibody or therapeutic protein modality.
Fail: Small molecule only, diagnostics only, reagent only or unrelated modality.
```

## Gate 3: Stage fit

```text
Pass: Discovery through active preclinical optimization.
Review: Early clinical with a parallel discovery program.
Fail: Late-clinical-only company with no new discovery work.
```

## Gate 4: Bottleneck

```text
Pass: Relevant problem is explicit or reasonably inferable.
Review: Bottleneck is the only missing fact.
Fail: No plausible platform work can be defined.
```

## Gate 5: Recent intent

```text
Pass: Recent funding, hiring, program, publication, patent, grant or milestone.
Review: Program fit exists but trigger is weak or stale.
```

## Gate 6: Paid-project clarity

```text
Pass: A narrow paid work package can be described.
Fail: Only a generic partnership or company-level fit can be described.
```

## Decision values

```text
APPROVE
REVIEW
REJECT
```

`REVIEW` is allowed only when exactly one meaningful fact is missing.

Return:

```json
{
  "decision": "REVIEW",
  "passed_gates": [1, 2, 3, 5, 6],
  "failed_gates": [],
  "unresolved_gate": 4,
  "unresolved_question": "Is affinity or developability the current optimization objective?",
  "next_verification_action": "Review the latest pipeline presentation and careers page.",
  "decision_confidence": 79
}
```

---

# 8. Scoring Model

Only score companies after exclusions and mandatory gates.

```text
Scientific fit:       0–25
Intent:               0–25
Project clarity:      0–20
Budget likelihood:   0–15
Buyer-role visibility:0–10
Evidence confidence:  0–5
Total:                0–100
```

Routing:

```text
80–100: Priority A
68–79:  Priority B
55–67:  Review
0–54:   Reject
```

Any hard exclusion must force Reject regardless of score.

The scoring weights and thresholds come directly from the SOP.

---

# 9. Query Management

Create a `query_registry` table.

```text
query_id
source_type
query_family
query_text
negative_terms
geography
date_window
max_results
cadence
status
version
owner
created_at
last_tested_at
```

Allowed statuses:

```text
DRAFT
TESTING
APPROVED_FOR_SCHEDULE
ACTIVE
REDUCE
PAUSED
RETIRED
```

Recommended query structure:

```text
[modality or technical problem]
+ [therapeutic company term]
+ [stage or intent trigger]
- [negative categories]
```

Example:

```text
"antibody affinity maturation"
biotech
preclinical
-CRO
-CDMO
-diagnostic
-reagent
-services
```

Test each query manually or with a small run before scheduling. The SOP specifies 10–30 test results and requires at least 70% of sampled records to be classifiable before production scheduling.

---

# 10. Deduplication

## Company key

```text
normalized_domain + canonical_company_name
```

## Signal keys

```text
News:
canonical_url + meaningful_update_date

Publication:
PMID or DOI

Trial:
NCT_ID + last_update_date

Job:
job_id or canonical_job_url + posted_date

Patent:
publication_number or patent_family_id

Grant:
project_number + fiscal_year

Website:
canonical_url + content_hash
```

Do not create a duplicate company when a new signal appears.

Attach the signal to the existing company and recalculate intent.

Only create a new website signal when the content change is material.

---

# 11. Human Review Interface

Create one review screen per company.

## Evidence panel

* Source
* URL
* Published date
* Exact evidence phrase
* Raw surrounding text
* Source reliability level

## Company panel

* Canonical company
* Domain
* Therapeutic ownership
* Funding stage
* Modality
* Programs
* Asset stages
* Exclusions
* Competitor check

## Intent panel

* Timeline of events
* Signal strengths
* Recency
* Independent source count
* Intent score

## Project panel

* Bottleneck
* Explicit versus inferred
* Proposed paid project
* Required client inputs
* Expected outputs
* Validation path
* Unresolved risk

## Decision controls

```text
Approve
Review with one question
Reject with reason
```

Store reviewer, timestamp, prompt version, model version and decision history.

The reviewer should be able to make the decision without searching across multiple systems.

---

# 12. Required Benchmarks

There are two benchmark groups:

1. SOP acceptance benchmarks
2. Recommended engineering-quality benchmarks

## A. SOP acceptance benchmarks

### Query classifiability

```text
Target: ≥70%
Definition:
Classifiable records / sampled source records
```

Do not automate a query below this threshold.

### Evidence completeness

```text
Target: 100% for approved records
```

Every approved record must have:

```text
source URL
signal date
exact evidence phrase
canonical company
therapeutic ownership evidence
modality
asset stage
intent trigger
project hypothesis
decision reason
```

### Review backlog

```text
Target: No Review item older than two working days
```

### Operational launch target

```text
20–30 raw signals reviewed per researcher per day
8–12 companies deeply researched
2–4 approved companies
```

These are controlled-launch operating targets from the SOP.

## B. Recommended engineering benchmarks

These additional values are implementation targets and should be validated against the first manually labelled dataset.

### 1. Ingestion reliability

```text
Successful scheduled runs: ≥99%
Records silently dropped: 0
Records without source URL: <1%
Records without collected_at: 0
```

### 2. Schema validity

```text
Valid normalized JSON: ≥99.5%
Required-field schema errors: <0.5%
Unparseable dates: <2%
```

### 3. Deduplication

```text
Company duplicate rate: <2%
Signal duplicate rate after dedupe: <5%
Incorrect company merges: <1%
```

Incorrect merges are more damaging than missed merges. Optimize precision before recall.

### 4. Company resolution

On a manually labelled set of at least 200 signals:

```text
Canonical-company precision: ≥95%
Canonical-company recall: ≥85%
Therapeutic-owner precision: ≥95%
Service-provider rejection precision: ≥97%
```

### 5. Biomedical extraction

Evaluate only fields that are explicitly supported by source evidence.

```text
Modality precision: ≥95%
Asset-stage precision: ≥90%
Target precision: ≥90%
Disease precision: ≥90%
Scientific-problem precision: ≥85%
Evidence-span validity: ≥98%
Unsupported factual extraction rate: <2%
```

### 6. Hard-exclusion classification

On a balanced benchmark set containing CROs, CDMOs, diagnostics, reagent companies, academics, therapeutic owners and competitors:

```text
Hard-exclusion precision: ≥97%
Hard-exclusion recall: ≥95%
False rejection of real therapeutic owners: <3%
```

### 7. Intent-event classification

```text
Intent-type precision: ≥90%
Intent-date accuracy: ≥95%
Funding-use-of-proceeds precision: ≥90%
Hiring-signal precision: ≥90%
Program-milestone precision: ≥90%
```

### 8. Hallucination control

```text
Invented company: 0
Invented source URL: 0
Invented evidence quote: 0
Invented asset ownership: 0
Invented named program: 0
Unsupported bottleneck stored as fact: 0
```

### 9. Human-review agreement

Build a gold-label set reviewed by one scientific reviewer and one commercial reviewer.

```text
AI versus human Approve/Review/Reject agreement: ≥85%
Hard-exclusion agreement: ≥95%
Therapeutic-ownership agreement: ≥90%
Project-hypothesis usability: ≥80%
```

Project usability means a human reviewer agrees that the hypothesis is specific, evidence-linked and commercially discussable.

### 10. Source economics

Track:

```text
Cost per raw record
Cost per resolved company
Cost per qualified company
Cost per approved company
Approval rate per source
Approval rate per query
```

Do not optimize for cost per scraped record.

Optimize for cost per approved company and eventually cost per qualified meeting.

---

# 13. Benchmark Dataset

Before production, manually label at least 500 raw signals.

Recommended composition:

```text
100 genuine therapeutic owners with strong intent
100 therapeutic owners with weak or stale intent
75 CRO/CDMO/service providers
50 diagnostics/reagent companies
50 academic-only records
50 direct competitors
75 ambiguous ownership or mixed records
```

Each benchmark record must contain human labels for:

```text
canonical company
company domain
ownership status
hard exclusion
modality
program
target
asset stage
intent type
intent strength
bottleneck
explicit versus inferred
decision
decision reason
```

Split:

```text
60% development
20% validation
20% locked test
```

Never tune prompts or thresholds on the locked test set.

Rebuild or expand the benchmark when:

```text
A source changes schema
A new source is introduced
A new modality is introduced
False-positive patterns change
The model or main prompt is changed
```

---

# 14. Source-Level Go/No-Go Rules

A source or query can enter production only when:

```text
Classifiable rate ≥70%
Company resolution precision ≥90%
Hard exclusions work reliably
Source URLs and dates are present
Cost per approved company is acceptable
No material schema instability exists
A human reviewer signs off
```

Pause a source when:

```text
Two consecutive runs are dominated by noise
Hard-exclusion categories exceed 50% unexpectedly
Source schema changes
Duplicate rate exceeds 15%
Company resolution precision falls below 85%
Source produces no approved companies after a meaningful sample
```

---

# 15. Scheduling

Recommended Phase 1 cadence:

```text
Company news: daily
Google News: daily
Company careers: twice weekly
Public jobs: twice weekly
PubMed: weekly
Company pipeline pages: weekly
ClinicalTrials.gov: weekly
NIH RePORTER: biweekly or monthly
Patents: monthly
SEC filings: event-driven or weekly for monitored accounts
```

Use:

```text
7-day window for fast-moving news
30-day window for jobs, publications and trials
180-day initial backfill
Monthly window for patents, grants and filings
60-day evidence-expiry check for approved companies
```

These date windows follow the SOP’s recommended backfill, heartbeat and revalidation logic.

---

# 16. Implementation Sequence

## Week 1: Data foundation

Build:

```text
raw_signals
normalized_signals
company_master
company_aliases
company_signals
intent_events
programs
qualification_decisions
query_registry
pipeline_runs
review_history
```

Implement:

* Raw storage
* Schema validation
* Query IDs
* Run IDs
* Deduplication
* Audit logging

## Week 2: Manual-source proof

Test only:

```text
Company websites
Google News
Public jobs
PubMed
```

Collect and manually label at least 200 records.

Do not schedule recurring automation yet.

## Week 3: Resolution and classification

Implement:

* Company resolver
* Ownership classifier
* Biomedical extractor
* Hard-exclusion engine
* Confidence scores
* Evidence spans

Run benchmark evaluation.

## Week 4: Qualification and human QA

Implement:

* Intent-event detection
* Signal stacking
* Qualification gates
* Scoring
* Project-hypothesis generator
* Human review UI

Increase benchmark set to at least 500 records.

## Production promotion

Promote only sources and queries that pass the go/no-go benchmarks.

---

# 17. Non-Negotiable Engineering Rules

1. Raw source data must be immutable.

2. Every normalized fact must point to supporting evidence.

3. Missing information must remain null.

4. AI may recommend but cannot final-approve.

5. Hard exclusions run before scoring.

6. No company is approved without therapeutic ownership.

7. No company is approved without a definable paid project.

8. No contacts or emails are collected during Phase 1.

9. Every model output must store model version, prompt version and raw response.

10. Every decision must be reproducible from stored evidence.

11. Company-level scores must be recalculated when a material new signal arrives.

12. The system must distinguish fact, inference and unresolved information.

13. Query performance must be measured by approved-company output, not scraped-record volume.

14. A pipeline that produces fewer accurate companies is better than one producing thousands of weak records.

---

# 18. Definition of Done

Phase 1 is complete when the system can:

1. Run approved source queries on schedule.
2. Store all raw evidence without silent loss.
3. Resolve companies with at least 95% precision.
4. Reject obvious non-buyers with at least 97% precision.
5. Extract modality, program, stage and intent with evidence.
6. Deduplicate signals and companies reliably.
7. Aggregate multiple signals at company-program level.
8. Produce a narrow, evidence-linked paid-project hypothesis.
9. Route companies to Approve, Review or Reject.
10. Let a human reviewer make a decision from one screen.
11. Pass the locked benchmark dataset.
12. Produce source-level quality and cost metrics.
13. Maintain 100% evidence completeness for approved records.

Do not proceed to buyer enrichment until these conditions are met.
