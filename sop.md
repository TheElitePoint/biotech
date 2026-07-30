**AI ANTIBODY & PROTEIN DESIGN**

**DIRECT-DEAL PROSPECTING  
OPERATING MANUAL**

100-Page Implementation System for Finding Therapeutic Companies  
with Active Antibody and Protein-Engineering Buying Intent

**Intern Research and Execution Manual  
July 2026**

**NON-NEGOTIABLE SCOPE**

**No CROs. No CDMOs. No diagnostics-only companies. No generic partnerships.  
Every approved account must support a direct paid pilot, project, or platform license.**

| **02** | **Purpose, Scope and Document Control** |
| ------ | --------------------------------------- |

This manual gives interns a source-by-source path from public buying signals to qualified direct-deal opportunities for an AI antibody and protein design platform.

## What this manual governs

**•** Prospect discovery for therapeutic antibody and protein-design buyers only.

**•** Manual research, Apify automation, AI classification, human approval, buyer enrichment and outreach handoff.

**•** A controlled path from a public scientific or commercial signal to a defined paid pilot hypothesis.

**•** Evidence retention, rejection logic, source ROI, team accountability and feedback loops.

## What it explicitly does not govern

**•** Fundraising, investor outreach, generic business development or networking.

**•** CRO, CDMO, diagnostics, reagent, assay-service, manufacturing or consultancy prospecting.

**•** Unqualified title-first lead generation or broad "AI drug discovery" messaging.

**•** Contact enrichment before the company has passed scientific, commercial and direct-deal gates.

## Document owner and review cycle

| **Owner**            | Commercial lead                                                            |
| -------------------- | -------------------------------------------------------------------------- |
| **Research owner**   | Research lead                                                              |
| **Automation owner** | Apify + n8n/Make operator                                                  |
| **Approval cadence** | Daily human QA; weekly source review                                       |
| **Version rule**     | Update actors, inputs and costs whenever the marketplace or source changes |

**Operating rule:** No direct scientific project hypothesis means no prospect.

| **03** | **Table of Contents** |
| ------ | --------------------- |

The manual is organized as a production sequence. Page numbers below are fixed for this edition.

| **Section**                                | **Pages** |
| ------------------------------------------ | --------- |
| **1\. Scope and operating architecture**   | 4-10      |
| **2\. Platform offer and direct-deal ICP** | 11-25     |
| **3\. Data model and control tables**      | 26-38     |
| **4\. Source-by-source research system**   | 39-58     |
| **5\. Query libraries and date logic**     | 59-69     |
| **6\. Apify build and automation control** | 70-80     |
| **7\. AI classification and human QA**     | 81-86     |
| **8\. Company and buyer enrichment**       | 87-92     |
| **9\. Direct pilot and outreach handoff**  | 93-96     |
| **10\. Daily, weekly and 30-day rollout**  | 97-100    |

## Fast start path

**1\.** Read pages 4-25 and lock the ICP and rejection rules before anyone researches.

**2\.** Build the minimum tables from pages 26-38 in Google Sheets or Airtable.

**3\.** Run manual research from pages 39-69 for five working days.

**4\.** Automate only proven queries using pages 70-80.

**5\.** Apply the prompts and human QA from pages 81-86.

**6\.** Enrich only approved companies using pages 87-92.

**7\.** Package direct pilots and move qualified accounts into outreach using pages 93-96.

**8\.** Operate the daily and weekly cadence from pages 97-100.

**Build sequence:** Manual proof first, automation second, enrichment third, outreach fourth. Reversing this order wastes money and creates irrelevant meetings.

| **04** | **End-to-End Operating Flow** |
| ------ | ----------------------------- |

Every record must move through the same controlled spine; no stage may be skipped.

## Production spine

**1\.** Run a high-intent query against a defined source and date window.

**2\.** Capture the raw signal, source URL, publication date and query used.

**3\.** Resolve the organization and verify that it owns a therapeutic program.

**4\.** Extract target, disease, antibody/protein modality, asset stage and bottleneck.

**5\.** Apply hard exclusions before spending time on contact discovery.

**6\.** Write a direct paid-project hypothesis for the platform.

**7\.** Score scientific fit, timing, project clarity, budget likelihood and buyer access.

**8\.** Human reviewer marks Approve, Review or Reject with evidence.

**9\.** Enrich approved company and find one primary and one backup buyer.

**10\.** Verify email, create signal-led outreach and place it in the approval queue.

**11\.** Record replies, meetings, project fit and rejection reasons.

**12\.** Update queries, weights and exclusions from real commercial outcomes.

## Automation boundary

| **Apify**            | Collect, crawl, normalize and enrich repeatable public data          |
| -------------------- | -------------------------------------------------------------------- |
| **AI**               | Extract concepts, classify and draft hypotheses; never final-approve |
| **Human researcher** | Verify scientific ownership, problem and direct project fit          |
| **Commercial lead**  | Approve account, buyer and outreach angle                            |
| **CRM**              | Store history, suppressions, outcomes and next actions               |

**Gate:** No contact or email enrichment until the company has an Approved status.

| **05** | **Roles and Daily Handoffs** |
| ------ | ---------------------------- |

Define who owns each decision so records do not move forward without accountability.

## Operating specification

| **Research lead**       | Owns queries, source quality, company resolution, scientific extraction and rejection notes. |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| **Automation builder**  | Owns Apify tasks, datasets, schedules, webhook delivery, dedupe and run logs.                |
| **Scientific reviewer** | Confirms modality, asset stage, bottleneck and realistic platform work package.              |
| **Commercial approver** | Confirms direct deal, budget plausibility, buyer authority and outreach readiness.           |
| **Outreach operator**   | Uses approved evidence only; logs every touch, reply and next action.                        |

## Done standard

**•** The responsible owner is named.

**•** The evidence and output fields are known.

**•** A stop rule exists for weak or noisy records.

**•** The next downstream stage is explicit.

**Non-negotiable:** No record advances because it "looks interesting"; it advances only when the required evidence exists.

| **06** | **System Architecture** |
| ------ | ----------------------- |

Use a layered architecture so raw evidence is never confused with an approved sales lead.

## Operating specification

| **Layer 1: Sources**           | Google News, PubMed, ClinicalTrials.gov, NIH RePORTER, company sites, jobs, patents and filings. |
| ------------------------------ | ------------------------------------------------------------------------------------------------ |
| **Layer 2: Collection**        | Manual browser work during validation; Apify actors after queries are proven.                    |
| **Layer 3: Storage**           | Raw Signals, Company Master, Evidence tables, Contacts and Outreach Queue.                       |
| **Layer 4: Intelligence**      | Concept extraction, company resolution, hard exclusions, scoring and direct-project hypothesis.  |
| **Layer 5: Revenue execution** | Buyer mapping, verified contact, outreach sequence, meeting and paid pilot qualification.        |

## Done standard

**•** The responsible owner is named.

**•** The evidence and output fields are known.

**•** A stop rule exists for weak or noisy records.

**•** The next downstream stage is explicit.

**Non-negotiable:** No record advances because it "looks interesting"; it advances only when the required evidence exists.

| **07** | **Minimum Tool Stack** |
| ------ | ---------------------- |

Start with the smallest stack that can produce accurate approved accounts.

## Operating specification

| **Google Sheets or Airtable**     | Central operating database with controlled statuses and evidence URLs.  |
| --------------------------------- | ----------------------------------------------------------------------- |
| **Google Search and Google News** | Manual signal discovery and query validation.                           |
| **Company websites**              | Pipeline, technology, careers, news, team and publication verification. |
| **PubMed and ClinicalTrials.gov** | Scientific and program-stage validation.                                |
| **LinkedIn Sales Navigator**      | Buyer mapping only after company approval.                              |
| **Apollo or equivalent**          | Email enrichment only for approved buyers.                              |
| **Email verifier**                | Final deliverability check before campaign upload.                      |

## Done standard

**•** The responsible owner is named.

**•** The evidence and output fields are known.

**•** A stop rule exists for weak or noisy records.

**•** The next downstream stage is explicit.

**Non-negotiable:** No record advances because it "looks interesting"; it advances only when the required evidence exists.

| **08** | **Advanced Tool Stack** |
| ------ | ----------------------- |

Add automation only after the manual system produces consistent approved companies.

## Operating specification

| **Apify**                           | Scheduled actors for PubMed, trials, jobs, news, websites and LinkedIn enrichment. |
| ----------------------------------- | ---------------------------------------------------------------------------------- |
| **n8n or Make**                     | Orchestrates actor runs, transformations, AI prompts, routing and alerts.          |
| **OpenAI-compatible model**         | Structured extraction and classification using fixed JSON schemas.                 |
| **Airtable**                        | Relational evidence, review views, approvals and dashboards.                       |
| **Instantly or approved sequencer** | Sends only human-approved outreach records.                                        |
| **CRM**                             | Tracks company-level history, meeting outcomes, pilots and exclusions.             |

## Done standard

**•** The responsible owner is named.

**•** The evidence and output fields are known.

**•** A stop rule exists for weak or noisy records.

**•** The next downstream stage is explicit.

**Non-negotiable:** No record advances because it "looks interesting"; it advances only when the required evidence exists.

| **09** | **Data, Security and Evidence Rules** |
| ------ | ------------------------------------- |

Protect the integrity of the system and keep every commercial claim traceable.

## Operating specification

| **Public evidence only** | Store public business and scientific data relevant to a professional buying decision.              |
| ------------------------ | -------------------------------------------------------------------------------------------------- |
| **Evidence retention**   | Keep source URL, date, exact phrase, query and actor run ID for every approved record.             |
| **Raw data backup**      | Retain the raw JSON or page text before normalization so fields can be reprocessed.                |
| **Secrets**              | Keep Apify, AI, Apollo and email-platform keys in environment variables or credential vaults.      |
| **Suppression**          | Maintain company and contact suppression lists; do not re-enrich or re-contact suppressed records. |
| **Platform terms**       | Use moderate volumes and review the current terms of each source and actor before scaling.         |

## Done standard

**•** The responsible owner is named.

**•** The evidence and output fields are known.

**•** A stop rule exists for weak or noisy records.

**•** The next downstream stage is explicit.

**Non-negotiable:** No record advances because it "looks interesting"; it advances only when the required evidence exists.

| **10** | **Operating Definitions** |
| ------ | ------------------------- |

Use exact definitions so researchers and automations make the same decision.

## Operating specification

| **Signal**                    | A dated public event indicating current scientific work, resource deployment or program movement.            |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Therapeutic owner**         | A company that owns, controls or co-controls the antibody/protein therapeutic asset or program.              |
| **Bottleneck**                | A design or optimization problem the platform can directly address.                                          |
| **Direct project hypothesis** | A specific paid work package tied to the visible signal and program.                                         |
| **Approved company**          | An asset owner with modality fit, timing fit, project clarity and a plausible buyer.                         |
| **Qualified meeting**         | A meeting where program, data access, validation path, budget authority and next project step are discussed. |

## Done standard

**•** The responsible owner is named.

**•** The evidence and output fields are known.

**•** A stop rule exists for weak or noisy records.

**•** The next downstream stage is explicit.

**Non-negotiable:** No record advances because it "looks interesting"; it advances only when the required evidence exists.

| **11** | **Platform Capability Map** |
| ------ | --------------------------- |

Translate platform capability into commercial work packages a buyer can purchase.

## Exact operating rules

| **De novo design**             | Generate candidate antibody/protein sequences around a defined target and desired binding profile.       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- |
| **Affinity maturation**        | Optimize an existing binder while preserving specificity and desired functional properties.              |
| **Humanization**               | Create and rank humanized variants with attention to retained binding and sequence liabilities.          |
| **Developability**             | Prioritize candidates for stability, aggregation, immunogenicity, expression and manufacturability risk. |
| **Off-target and specificity** | Evaluate likely cross-reactivity and rank candidates for cleaner target engagement.                      |
| **Candidate shortlisting**     | Reduce a broad design space to a wet-lab-ready ranked panel with rationale.                              |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **12** | **Direct Paid Deal Types** |
| ------ | -------------------------- |

Every approved account must map to at least one definable transaction.

## Exact operating rules

| **Focused design pilot**        | One target; agreed design constraints; ranked candidate panel for wet-lab validation.  |
| ------------------------------- | -------------------------------------------------------------------------------------- |
| **Lead optimization project**   | Existing sequence or lead series; affinity, specificity and developability objectives. |
| **Humanization project**        | Existing non-human binder; humanized candidates and risk-ranked shortlist.             |
| **Bispecific component work**   | Binder or arm selection, affinity balancing and candidate prioritization.              |
| **Recurring discovery support** | A defined series of targets or programs with milestone-based deliveries.               |
| **Platform license**            | Access or licensing after a successful pilot proves value and integration fit.         |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **13** | **Ideal Company Profile** |
| ------ | ------------------------- |

Target asset owners that can directly buy design or optimization work.

## Exact operating rules

| **Company type**  | Therapeutic biotech or pharma discovery unit owning antibody/protein programs.              |
| ----------------- | ------------------------------------------------------------------------------------------- |
| **Stage**         | Seed to Series B is primary; funded preclinical companies are highest priority.             |
| **Program stage** | Discovery, binder generation, lead optimization, candidate selection or early preclinical.  |
| **Team profile**  | Strong wet-lab biology but limited protein design, computational or optimization bandwidth. |
| **Trigger**       | Recent funding, hiring, program launch, publication, patent, grant or candidate milestone.  |
| **Buyer**         | CSO, VP Discovery, Head of Antibody Discovery, Head of Protein Engineering or founder-CSO.  |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **14** | **Company Stage and Size Filter** |
| ------ | --------------------------------- |

Use stage to estimate buying speed, budget and ability to use external design support.

## Exact operating rules

| **Seed / pre-seed**          | Approve only when funding is real, program ownership is clear and wet-lab validation exists.     |
| ---------------------------- | ------------------------------------------------------------------------------------------------ |
| **Series A**                 | Highest priority when capital is allocated to build an antibody pipeline or nominate candidates. |
| **Series B**                 | Strong priority when multiple programs require scale, optimization or candidate selection.       |
| **Public small-cap biotech** | Selective; approve only with active discovery programs and visible resource need.                |
| **Large pharma**             | Account-based only; target a named discovery unit and a defined program, not the whole company.  |
| **Late clinical-only**       | Reject when no new discovery or next-generation program is visible.                              |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **15** | **Modality Filter** |
| ------ | ------------------- |

Confirm the therapeutic modality before any company is treated as a qualified platform prospect.

## Exact operating rules

| **Approve**           | Monoclonal antibodies, bispecifics, multispecifics, antibody fragments, nanobodies, engineered proteins and therapeutic binders. |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Conditional**       | ADCs where binder engineering is active; cytokine or fusion proteins where sequence design is central.                           |
| **Review**            | Cell therapy companies only when the need is specifically scFv/binder or protein engineering for the construct.                  |
| **Reject**            | Small-molecule-only, gene-therapy-only, diagnostics-only, reagent antibodies and manufacturing-only operations.                  |
| **Evidence required** | Pipeline page, publication, patent, job description, trial intervention or company announcement.                                 |
| **Output**            | A normalized modality label and exact evidence phrase.                                                                           |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **16** | **Scientific Bottleneck Library** |
| ------ | --------------------------------- |

Research must identify a problem the platform can directly address.

## Exact operating rules

| **Discovery**           | Difficult target, insufficient binder diversity, low hit rate or need for de novo candidates.    |
| ----------------------- | ------------------------------------------------------------------------------------------------ |
| **Binding performance** | Weak affinity, poor potency, unbalanced bispecific arms or inadequate epitope coverage.          |
| **Specificity**         | Cross-reactivity, off-target binding, selectivity or target-family discrimination.               |
| **Sequence risk**       | Humanization, immunogenicity, liabilities, stability or aggregation.                             |
| **Development risk**    | Expression, solubility, manufacturability, format compatibility or developability.               |
| **Decision risk**       | Too many candidates, limited wet-lab capacity or uncertainty about which variants to test first. |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **17** | **High-Intent Timing Triggers** |
| ------ | ------------------------------- |

A modality match without a recent trigger is not enough.

## Exact operating rules

| **Capital trigger**    | Funding announcement explicitly tied to pipeline expansion, discovery or preclinical advancement.      |
| ---------------------- | ------------------------------------------------------------------------------------------------------ |
| **Hiring trigger**     | Open roles in antibody discovery, protein engineering, computational biology or developability.        |
| **Program trigger**    | New target, new antibody program, pipeline addition, lead optimization or candidate selection.         |
| **Scientific trigger** | Recent company-affiliated paper, preprint, patent or conference data.                                  |
| **Execution trigger**  | New wet-lab partner, preclinical collaboration, platform build or manufacturing preparation.           |
| **Milestone trigger**  | Candidate nomination, IND-enabling transition, failed/paused program requiring next-generation design. |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **18** | **Budget and Purchase-Likelihood Signals** |
| ------ | ------------------------------------------ |

Use public evidence to estimate whether a direct paid pilot is commercially plausible.

## Exact operating rules

| **Strong**              | Recent financing with clear use of proceeds, multiple active programs, senior discovery hiring or existing external vendors. |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Moderate**            | Grant-funded program, small team with active preclinical work, or company explicitly building discovery capability.          |
| **Weak**                | Old funding, vague platform language, no team growth, no program updates or purely academic work.                            |
| **Budget owner clue**   | CSO/founder controls program and external spend; external innovation or BD manages procurement.                              |
| **Validation capacity** | Company owns a lab or named wet-lab partner capable of testing delivered candidates.                                         |
| **Reject**              | No evidence of resources, asset ownership or ability to validate outputs.                                                    |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **19** | **Buyer Authority Model** |
| ------ | ------------------------- |

Find the person who can approve or sponsor the scientific project.

## Exact operating rules

| **Economic/scientific owner** | CSO, founder-CSO or VP Discovery.                                                              |
| ----------------------------- | ---------------------------------------------------------------------------------------------- |
| **Technical owner**           | Head of Antibody Discovery or Head of Protein Engineering.                                     |
| **Internal champion**         | Director/Principal Scientist leading the program or target.                                    |
| **Commercial facilitator**    | Head of BD or External Innovation only when tied to a named scientific program.                |
| **Procurement path**          | Large companies may require vendor onboarding after scientific sponsorship.                    |
| **Minimum mapping**           | One primary scientific buyer plus one backup authority; never rely only on a junior scientist. |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **20** | **Hard Exclusions** |
| ------ | ------------------- |

Remove non-buyers before scoring or enrichment.

## Exact operating rules

| **CRO and contract discovery providers**      | They sell research services and are not the therapeutic asset buyer.                         |
| --------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **CDMO and manufacturers**                    | They manufacture or develop processes without owning the discovery decision.                 |
| **Diagnostics and test kits**                 | Reject unless a separate therapeutic program is clearly owned and active.                    |
| **Reagent and catalogue antibody suppliers**  | Not therapeutic-program buyers.                                                              |
| **Consultancies, accelerators and investors** | No direct antibody-design project ownership.                                                 |
| **Academic-only labs**                        | Reject unless a funded commercial spinout owns the asset and can contract.                   |
| **Direct competitors**                        | Reject AI antibody/protein design providers unless an explicit subcontracting demand exists. |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **21** | **Competitor and Substitute Check** |
| ------ | ----------------------------------- |

Avoid sending prospects that already sell the same capability or have no external need.

## Exact operating rules

| **Direct competitor**   | AI antibody design, protein language model platform, antibody engineering CRO or in-silico biologics vendor.    |
| ----------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Internal substitute** | Large, mature computational protein-design team with no visible outsourcing trigger.                            |
| **Adjacent platform**   | May be valid only when its gap is explicit and a direct project can be defined.                                 |
| **How to check**        | Search company technology, services, team, publications, job roles, partners and recent announcements.          |
| **Decision**            | Reject competitor; Review internal substitute; Approve only when the external-work rationale is evidence-based. |
| **Record**              | Store competitor URL and one-sentence reason to prevent future re-entry.                                        |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **22** | **Strict Qualification Decision Tree** |
| ------ | -------------------------------------- |

Use the same gate for every company regardless of source.

## Exact operating rules

| **Gate 1** | Does the organization own or co-own a therapeutic antibody/protein program? If no: Reject.                            |
| ---------- | --------------------------------------------------------------------------------------------------------------------- |
| **Gate 2** | Is the program in discovery, optimization, candidate selection or active preclinical expansion? If no: Reject/Review. |
| **Gate 3** | Is a platform-relevant bottleneck visible or strongly inferable? If no: Review.                                       |
| **Gate 4** | Is there a recent timing or buying trigger? If no: Review or Reject.                                                  |
| **Gate 5** | Can a specific paid work package be described? If no: Reject.                                                         |
| **Gate 6** | Is a senior buyer identifiable and validation capacity plausible? If no: Review.                                      |
| **Final**  | Approve only when evidence passes all required gates.                                                                 |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **23** | **Approve, Review and Reject Rules** |
| ------ | ------------------------------------ |

Statuses must express evidence quality, not researcher optimism.

## Exact operating rules

| **Approve**        | All mandatory gates pass; direct project hypothesis and buyer role are written.                               |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Review**         | One resolvable gap remains: ownership, timing, bottleneck, buyer or validation path.                          |
| **Reject**         | Hard exclusion, no therapeutic ownership, wrong modality, no active program, competitor or no direct project. |
| **Review SLA**     | Resolve within two working days; otherwise reject to prevent a permanent grey queue.                          |
| **Rejection note** | Name the exact failed gate and evidence.                                                                      |
| **Approval note**  | Connect signal, program, bottleneck, platform work package and buyer in one paragraph.                        |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **24** | **Priority Scoring Model** |
| ------ | -------------------------- |

Score only after hard exclusions have been applied.

## Exact operating rules

| **Scientific fit: 0-25**    | Target/modality relevance, asset stage and bottleneck clarity.         |
| --------------------------- | ---------------------------------------------------------------------- |
| **Intent: 0-25**            | Recency and strength of funding, hiring, program or milestone trigger. |
| **Project clarity: 0-20**   | Can a paid pilot be scoped without guessing?                           |
| **Budget likelihood: 0-15** | Funding, team growth, external spend and validation capacity.          |
| **Buyer access: 0-10**      | Named senior buyer and reachable backup.                               |
| **Data confidence: 0-5**    | Evidence quality, source reliability and ownership clarity.            |
| **Threshold**               | 80+ Priority A; 68-79 Priority B; 55-67 Review; below 55 Reject.       |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **25** | **Research Completion Standard** |
| ------ | -------------------------------- |

A researched company is not complete until it is commercially actionable or explicitly rejected.

## Exact operating rules

| **Required evidence**   | Source URL, date, exact phrase, company website and query used.                                 |
| ----------------------- | ----------------------------------------------------------------------------------------------- |
| **Scientific fields**   | Target, disease, modality, asset stage and bottleneck.                                          |
| **Commercial fields**   | Direct project hypothesis, likely pilot, buyer role and budget clue.                            |
| **Decision fields**     | Score, status, approval/rejection note and reviewer.                                            |
| **Enrichment boundary** | Approved status required before LinkedIn employee or email enrichment.                          |
| **Done definition**     | A second reviewer can understand exactly why the company should or should not receive outreach. |

## Researcher action

**•** Capture evidence, not assumptions.

**•** Write the direct project in operational language.

**•** Apply the hard exclusion before scoring.

**•** Escalate only one clearly defined missing fact to Review.

**Revenue test:** Would the team be able to propose a defined paid pilot to this company now? If not, do not approve.

| **26** | **Data Architecture Overview** |
| ------ | ------------------------------ |

Separate source evidence, company truth, contacts and revenue execution.

## Table design

| **Seed Sources**    | Query, source, date window, owner, cadence, status and performance.                       |
| ------------------- | ----------------------------------------------------------------------------------------- |
| **Raw Signals**     | One row per article, job, trial, patent, grant, announcement or page change.              |
| **Company Master**  | One deduplicated company record with ownership, modality, stage and approval status.      |
| **Evidence tables** | Publications, jobs, trials, grants, patents and pipeline assets linked to Company Master. |
| **Contacts**        | Only buyers from approved companies, with role rationale and verification status.         |
| **Outreach Queue**  | Approved message, signal, project hypothesis, channel, sequence and outcome.              |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **27** | **Seed Sources Table** |
| ------ | ---------------------- |

Control what is searched and measure which queries produce direct-deal accounts.

## Table design

| **Required fields**    | Seed ID, source, query, product focus, country, date window, cadence, owner and status.              |
| ---------------------- | ---------------------------------------------------------------------------------------------------- |
| **Performance fields** | Raw results, resolved companies, approvals, rejections, contacts, replies, meetings and paid pilots. |
| **Status values**      | Test, Active, Reduce, Pause and Retired.                                                             |
| **Rule**               | Every raw signal must retain the Seed ID that produced it.                                           |
| **Review**             | Weekly; increase only seeds producing approved companies and qualified meetings.                     |
| **Stop**               | Pause after two noisy runs or when the same excluded categories dominate.                            |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **28** | **Raw Signals Table** |
| ------ | --------------------- |

Preserve source evidence before any AI or human interpretation.

## Table design

| **Identity**           | Signal ID, source, source URL, source type, query and actor run ID.            |
| ---------------------- | ------------------------------------------------------------------------------ |
| **Timing**             | Published/updated date, collected date and date-window used.                   |
| **Raw content**        | Title, snippet, abstract, job description, trial text or crawled page content. |
| **Candidate entities** | Company/institution, target, disease, modality and asset stage.                |
| **Routing**            | Resolve company, human review, reject or duplicate.                            |
| **Storage**            | Retain raw JSON or markdown in a backup field or object store.                 |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **29** | **Company Master Table** |
| ------ | ------------------------ |

Create one commercial truth record for each organization.

## Table design

| **Identity**           | Canonical company name, website, LinkedIn URL, location and aliases.             |
| ---------------------- | -------------------------------------------------------------------------------- |
| **Commercial profile** | Private/public, funding stage, headcount, last raise and active program count.   |
| **Scientific profile** | Therapeutic owner, modality, target classes, disease areas and asset stages.     |
| **Qualification**      | Hard exclusions, competitor status, direct project hypothesis, score and status. |
| **Ownership**          | Researcher, reviewer, approval date and next review date.                        |
| **Dedupe key**         | Normalized website domain plus canonical legal/company name.                     |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **30** | **Pipeline Assets Table** |
| ------ | ------------------------- |

Track the specific programs that create a direct platform project opportunity.

## Table design

| **Asset identity** | Asset/program name, target, disease, format and modality.                                      |
| ------------------ | ---------------------------------------------------------------------------------------------- |
| **Stage**          | Discovery, lead generation, lead optimization, candidate selection, preclinical or clinical.   |
| **Ownership**      | Originator, current owner, license status and collaboration partners.                          |
| **Bottleneck**     | Affinity, specificity, humanization, stability, developability, format or candidate selection. |
| **Evidence**       | Pipeline page, paper, patent, trial or announcement URL.                                       |
| **Commercial use** | Named pilot hypothesis and buyer who likely owns the program.                                  |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **31** | **Publications Table** |
| ------ | ---------------------- |

Use publications to validate science, company involvement and current program direction.

## Table design

| **Fields**       | PMID/DOI, title, date, journal, authors, affiliations and abstract.                               |
| ---------------- | ------------------------------------------------------------------------------------------------- |
| **Extraction**   | Company affiliation, target, disease, antibody/protein format, findings and stated limitations.   |
| **Company rule** | Academic paper alone is not a lead; company ownership or sponsored development must be confirmed. |
| **Intent rule**  | Recent company-affiliated work is stronger when tied to a pipeline, job or funding trigger.       |
| **Action**       | Link the paper to Company Master and relevant Pipeline Asset.                                     |
| **Reject**       | Review articles, academic-only work or unrelated diagnostic antibodies.                           |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **32** | **Jobs Table** |
| ------ | -------------- |

Treat hiring as a program-movement and capacity signal, not proof of outsourcing by itself.

## Table design

| **Fields**     | Job title, company, location, posted date, job URL and full description.                                      |
| -------------- | ------------------------------------------------------------------------------------------------------------- |
| **Extract**    | Program, target, modality, responsibilities, required methods and team reporting line.                        |
| **High value** | Antibody discovery, protein engineering, developability, computational design and biologics leadership roles. |
| **Inference**  | Hiring can indicate execution timing, capability gaps or new program investment.                              |
| **Validation** | Check pipeline, funding and company stage before approval.                                                    |
| **Expiry**     | Mark closed jobs; retain the evidence and original posted date.                                               |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **33** | **Trials Table** |
| ------ | ---------------- |

Use trial data to map sponsors and next-generation needs, not to target every clinical company.

## Table design

| **Fields**   | NCT ID, sponsor, intervention, phase, status, start/update date and conditions.                   |
| ------------ | ------------------------------------------------------------------------------------------------- |
| **Use**      | Confirm therapeutic ownership, modality and whether the company maintains new discovery programs. |
| **Priority** | Early clinical company with parallel discovery pipeline or next-generation antibody work.         |
| **Reject**   | Late-stage asset-only company with no continuing discovery or optimization need.                  |
| **Link**     | Connect trial to company and asset records.                                                       |
| **Output**   | Trial-based timing note, not an unsupported claim about trial problems.                           |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **34** | **Grants Table** |
| ------ | ---------------- |

Use non-dilutive funding to discover funded therapeutic programs and spinouts.

## Table design

| **Fields**          | Project number, organization, PI, award amount, dates, abstract and institute.  |
| ------------------- | ------------------------------------------------------------------------------- |
| **Company test**    | Recipient must be a company or a commercial spinout with contracting authority. |
| **Scientific test** | Award must support therapeutic antibody/protein discovery or optimization.      |
| **Commercial test** | A paid design pilot must fit within the funded work or next milestone.          |
| **Review**          | University grant with licensing/spinout unclear.                                |
| **Reject**          | Basic research with no commercial asset owner.                                  |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **35** | **Patents Table** |
| ------ | ----------------- |

Use patents to identify owned sequences, formats and active program investment.

## Table design

| **Fields**          | Publication number, assignee, inventors, filing/publication dates, claims and family.          |
| ------------------- | ---------------------------------------------------------------------------------------------- |
| **Extract**         | Target, antibody format, sequences, engineering concept and therapeutic use.                   |
| **Ownership check** | Verify current operating company and whether rights were assigned or licensed.                 |
| **Timing**          | Recent filing/publication is stronger when reinforced by funding, hiring or pipeline activity. |
| **Project clue**    | Optimization, humanization, specificity or design-around opportunity.                          |
| **Reject**          | Expired/inactive assignee, diagnostic-only claims or direct competitor platform patents.       |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **36** | **Contacts Table** |
| ------ | ------------------ |

Store only people who can influence or approve the direct scientific project.

## Table design

| **Fields**          | Name, title, company, LinkedIn URL, email, verification status and source.   |
| ------------------- | ---------------------------------------------------------------------------- |
| **Role logic**      | Primary owner, technical owner, internal champion or commercial facilitator. |
| **Why this person** | One sentence linking role to the exact program and bottleneck.               |
| **Quality**         | Current role verified; seniority adequate; backup contact identified.        |
| **Suppression**     | Opt-out, left company, wrong role and do-not-contact status.                 |
| **Boundary**        | No contact rows for rejected or unresolved companies.                        |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **37** | **Outreach Queue Table** |
| ------ | ------------------------ |

Convert an approved company into a controlled and reviewable revenue action.

## Table design

| **Company evidence** | Recent signal, source URL, direct project hypothesis and approval score.       |
| -------------------- | ------------------------------------------------------------------------------ |
| **Buyer evidence**   | Primary buyer, role rationale, verified channel and backup buyer.              |
| **Message**          | Signal-led first line, relevant platform work package and soft pilot CTA.      |
| **Controls**         | Human approver, approved date, sequence, send date and suppression check.      |
| **Outcomes**         | Reply class, meeting status, project fit, next action and rejection reason.    |
| **Stop**             | Remove when evidence becomes stale, buyer leaves or company changes direction. |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **38** | **Exclusions and Feedback Tables** |
| ------ | ---------------------------------- |

Prevent repeated waste and turn market outcomes into better targeting.

## Table design

| **Exclusions**          | Company/domain, category, reason, evidence, date, owner and review date.                |
| ----------------------- | --------------------------------------------------------------------------------------- |
| **Contact suppression** | Email/profile, reason, source and permanent/temporary status.                           |
| **Feedback log**        | Reply, objection, meeting outcome, project relevance, budget, timeline and next step.   |
| **Learning fields**     | Which signal, query, buyer and project hypothesis produced the result.                  |
| **Weekly action**       | Add new rejection patterns and update scoring weights.                                  |
| **Rule**                | A rejected company cannot re-enter without new evidence and explicit reviewer approval. |

## Implementation sequence

**1\.** Create fields and controlled status values.

**2\.** Load exclusions before importing signals.

**3\.** Test ten records manually.

**4\.** Lock the dedupe key and evidence requirements.

**5\.** Only then connect automation.

**Database principle:** Raw evidence is immutable; normalized fields and approval decisions may be updated with an audit trail.

| **39** | **Source Priority Matrix** |
| ------ | -------------------------- |

Decide where researchers and automation spend time.

## Where and how to work

| **Tier 1 - daily**        | Google News, company news, company pipeline pages and LinkedIn/company careers.     |
| ------------------------- | ----------------------------------------------------------------------------------- |
| **Tier 1 - twice weekly** | PubMed and targeted publications.                                                   |
| **Tier 2 - weekly**       | ClinicalTrials.gov, NIH RePORTER and patents.                                       |
| **Tier 2 - event driven** | Conference programs, SEC filings and biotech news sites.                            |
| **Tier 3 - validation**   | Open Targets, ChEMBL, PubChem and other scientific context sources.                 |
| **Rule**                  | Source priority is based on approved companies and meetings, not raw record volume. |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **40** | **Manual Google Search Workflow** |
| ------ | --------------------------------- |

Use Google to test query precision before creating any automated actor task.

## Where and how to work

| **Website** | google.com; use exact phrases, exclusions, site filters and date tools.                     |
| ----------- | ------------------------------------------------------------------------------------------- |
| **Input**   | One query from the approved query bank plus a last-180-day backfill window.                 |
| **Process** | Open original source, capture date and company, then verify on company website.             |
| **Output**  | Raw Signal with exact query and evidence URL.                                               |
| **Quality** | At least 7 of 10 reviewed results should be classifiable.                                   |
| **Stop**    | Narrow or retire a query producing media noise, CROs, diagnostics or academic-only results. |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **41** | **Google News Workflow** |
| ------ | ------------------------ |

Find funding, pipeline, hiring, partnership and milestone timing events.

## Where and how to work

| **Manual site** | news.google.com; search exact phrases with antibody/protein and biotech terms.   |
| --------------- | -------------------------------------------------------------------------------- |
| **Apify actor** | andok/google-news-scraper.                                                       |
| **Input**       | queries array, locale, date range/time period and conservative max results.      |
| **Output**      | Headline, publisher, published date, article URL, snippet and originating query. |
| **Validation**  | Open the original company release or reputable publisher before approval.        |
| **Cadence**     | Daily for active queries; weekly for broad monitoring.                           |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **42** | **Biotech News Sites** |
| ------ | ---------------------- |

Use sector publications to surface events, then confirm them on primary sources.

## Where and how to work

| **Sites**     | Fierce Biotech, BioSpace, Endpoints News, company press releases and business wires.               |
| ------------- | -------------------------------------------------------------------------------------------------- |
| **Search**    | Antibody, bispecific, protein engineering, preclinical pipeline, funding and candidate nomination. |
| **Use**       | Timing discovery and program context.                                                              |
| **Do not do** | Approve from headline alone or treat layoffs/clinical news as automatic buying intent.             |
| **Output**    | Source record linked to the primary company announcement.                                          |
| **Cadence**   | Daily scan or keyword alert; ingest only relevant articles.                                        |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **43** | **Company Website Research** |
| ------ | ---------------------------- |

The company website is the final authority for ownership, program and buyer context.

## Where and how to work

| **Pages**          | Pipeline, technology, publications, news, careers, team, partnerships and contact.          |
| ------------------ | ------------------------------------------------------------------------------------------- |
| **Extract**        | Asset stage, target, antibody format, current milestone, team capability and wet-lab setup. |
| **Ownership test** | Does the company clearly develop or co-develop the therapeutic asset?                       |
| **Project test**   | Can a direct design/optimization work package be tied to a named program?                   |
| **Output**         | Company Master update plus evidence URLs.                                                   |
| **Reject**         | Service provider language, diagnostic-only products or no active therapeutic pipeline.      |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **44** | **Apify Website Content Crawler** |
| ------ | --------------------------------- |

Automate approved-company website extraction after initial company resolution.

## Where and how to work

| **Actor**   | apify/website-content-crawler.                                                                                  |
| ----------- | --------------------------------------------------------------------------------------------------------------- |
| **Input**   | Approved company domain; include patterns for /pipeline, /technology, /news, /publications, /careers and /team. |
| **Exclude** | Privacy, terms, cookie, investor archive noise and unrelated blog tags.                                         |
| **Output**  | Clean markdown/text, page URL, crawl time and metadata.                                                         |
| **Routing** | Send text to entity extraction and company gate; retain raw crawl.                                              |
| **Stop**    | Pause domains with duplicate navigation, blocked content or irrelevant page explosion.                          |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **45** | **Manual LinkedIn Jobs Research** |
| ------ | --------------------------------- |

Use public job listings and company careers to detect program investment and capability gaps.

## Where and how to work

| **Websites**       | LinkedIn Jobs public search and company career pages.                                                          |
| ------------------ | -------------------------------------------------------------------------------------------------------------- |
| **Queries**        | Antibody discovery, protein engineering, biologics discovery, developability and computational protein design. |
| **Extract**        | Title, posted date, full responsibilities, team, program and reporting line.                                   |
| **Validation**     | Confirm job is current and belongs to the therapeutic asset owner.                                             |
| **Inference rule** | Hiring is a timing signal; it is not proof of outsourcing.                                                     |
| **Output**         | Job record plus a testable project hypothesis.                                                                 |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **46** | **Apify LinkedIn Jobs Actor** |
| ------ | ----------------------------- |

Scale only hiring queries that have produced qualified companies manually.

## Where and how to work

| **Actor**      | apimaestro/linkedin-jobs-scraper-api.                                       |
| -------------- | --------------------------------------------------------------------------- |
| **Input**      | Keyword, geography, date/recency, job type and result cap.                  |
| **Start test** | 5-20 results per query; inspect job descriptions and company fields.        |
| **Output**     | Job URL, company, title, location, date, description and search parameters. |
| **Cadence**    | Twice weekly for core terms; daily only for narrow high-performing queries. |
| **Stop**       | Pause when staffing agencies, CROs or non-therapeutic employers dominate.   |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **47** | **Manual PubMed Research** |
| ------ | -------------------------- |

Find company-affiliated scientific work that reveals target, modality and active design problems.

## Where and how to work

| **Website**            | pubmed.ncbi.nlm.nih.gov.                                                                           |
| ---------------------- | -------------------------------------------------------------------------------------------------- |
| **Search fields**      | Title/abstract terms, affiliation, date and article type.                                          |
| **Queries**            | Antibody affinity maturation, humanization, bispecific, membrane protein and developability terms. |
| **Extract**            | PMID, date, affiliations, target, disease, antibody format, findings and limitations.              |
| **Company resolution** | Verify affiliation and pipeline ownership on company website.                                      |
| **Reject**             | Academic-only papers, reviews and diagnostic antibodies without therapeutic program ownership.     |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **48** | **Apify PubMed Search Actor** |
| ------ | ----------------------------- |

Automate literature backfills and recurring heartbeat searches.

## Where and how to work

| **Actor**      | automation-lab/pubmed-search-scraper.                                              |
| -------------- | ---------------------------------------------------------------------------------- |
| **Input**      | queries, maxResultsPerQuery, includeAbstract and date range.                       |
| **Output**     | PMID, title, abstract, date, authors, affiliations, DOI, MeSH, keywords and query. |
| **Rate rule**  | Use conservative NCBI request rates; add an NCBI API key only when required.       |
| **Cadence**    | Weekly heartbeat; 180-day controlled backfill for new query families.              |
| **Acceptance** | 70% of a 10-30-record sample must be classifiable before scheduling.               |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **49** | **Europe PMC and Crossref** |
| ------ | --------------------------- |

Use secondary literature APIs for preprints, affiliation details and DOI resolution.

## Where and how to work

| **Websites** | europepmc.org and api.crossref.org.                                                    |
| ------------ | -------------------------------------------------------------------------------------- |
| **Best use** | Preprints, grant links, open abstracts, citation metadata and DOI normalization.       |
| **Input**    | Target/modality query, date window and organization terms.                             |
| **Output**   | Publication metadata and full-text/abstract links where available.                     |
| **Quality**  | Resolve the therapeutic company separately; do not promote institutions automatically. |
| **Cadence**  | On-demand validation or weekly for preprint-heavy areas.                               |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **50** | **Manual ClinicalTrials.gov Research** |
| ------ | -------------------------------------- |

Use trials selectively to confirm sponsors and detect next-generation antibody programs.

## Where and how to work

| **Website**  | clinicaltrials.gov.                                                                             |
| ------------ | ----------------------------------------------------------------------------------------------- |
| **Filters**  | Sponsor, intervention, condition, phase, status and last update.                                |
| **Extract**  | NCT ID, sponsor, intervention, antibody format, phase, dates and collaborators.                 |
| **Fit test** | Does the sponsor still have active discovery or preclinical programs?                           |
| **Use**      | Timing and ownership validation, not an assumption that clinical problems require the platform. |
| **Reject**   | Late-stage-only sponsor with no continuing discovery activity.                                  |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **51** | **Apify ClinicalTrials.gov Actors** |
| ------ | ----------------------------------- |

Collect structured trial records and deepen only selected high-fit studies.

## Where and how to work

| **Search actor**       | automation-lab/clinicaltrials-gov-studies-scraper.                                                       |
| ---------------------- | -------------------------------------------------------------------------------------------------------- |
| **Single-study actor** | automation-lab/clinicaltrials-gov-study-scraper.                                                         |
| **Input**              | Search term/condition, intervention, sponsor, statuses, phases, NCT IDs and maxItems.                    |
| **Output**             | Sponsor, intervention, status, phase, dates, locations and raw study.                                    |
| **Cadence**            | Weekly broad monitor; on-demand single-study enrichment.                                                 |
| **Stop**               | Do not scale trial queries that mostly produce hospitals, academic sponsors or late-stage-only accounts. |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **52** | **Manual NIH RePORTER Research** |
| ------ | -------------------------------- |

Find funded therapeutic discovery projects and company-backed spinouts.

## Where and how to work

| **Website**      | reporter.nih.gov.                                                                         |
| ---------------- | ----------------------------------------------------------------------------------------- |
| **Search**       | Antibody engineering, protein design, humanization, bispecific and target-specific terms. |
| **Extract**      | Recipient, PI, award amount, project dates, abstract and institute.                       |
| **Company gate** | Confirm commercial recipient or active spinout with rights and contracting authority.     |
| **Project gate** | Map the funded objective to a direct platform design/optimization work package.           |
| **Reject**       | University basic research with no asset-owning company.                                   |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **53** | **Apify NIH RePORTER Actor** |
| ------ | ---------------------------- |

Automate grant discovery from the official NIH RePORTER API.

## Where and how to work

| **Actor**      | automation-lab/nih-reporter-grant-search-scraper.                                 |
| -------------- | --------------------------------------------------------------------------------- |
| **Input**      | terms, fiscalYears, maxResults, pageSize and optional raw result.                 |
| **Output**     | Project number, title, award, organization, PI, dates, abstract and raw API data. |
| **Cadence**    | Monthly backfill and weekly/biweekly heartbeat for narrow themes.                 |
| **Validation** | Company resolution and direct project fit remain human-reviewed.                  |
| **Stop**       | Pause seeds producing mostly universities without commercialization evidence.     |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **54** | **Patent Research Workflow** |
| ------ | ---------------------------- |

Use Google Patents and USPTO data to identify owned antibody sequences, formats and engineering problems.

## Where and how to work

| **Websites**     | patents.google.com and data.uspto.gov.                                                            |
| ---------------- | ------------------------------------------------------------------------------------------------- |
| **Search**       | Assignee plus antibody, bispecific, humanization, affinity, epitope or protein-engineering terms. |
| **Extract**      | Assignee, dates, family, target, format, claims and sequence/design concepts.                     |
| **Validation**   | Confirm current assignee and active company.                                                      |
| **Project clue** | Lead optimization, design-around, specificity or developability work.                             |
| **Reject**       | Diagnostic claims, reagent patents, inactive assignees or competitor platform patents.            |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **55** | **Funding Databases and Company Filings** |
| ------ | ----------------------------------------- |

Use funding intelligence to prove resources and timing, not scientific fit by itself.

## Where and how to work

| **Sources**       | Company releases, Crunchbase, PitchBook, Dealroom, SEC filings and reputable news.              |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| **Extract**       | Round date, amount, stage, investors and stated use of proceeds.                                |
| **Strong signal** | Funds explicitly allocated to antibody pipeline, discovery, preclinical work or team expansion. |
| **Weak signal**   | General corporate financing without program detail.                                             |
| **Output**        | Budget likelihood note and timing score.                                                        |
| **Validation**    | Scientific fit and direct project hypothesis must come from pipeline or technical evidence.     |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **56** | **Conference Programs and Abstracts** |
| ------ | ------------------------------------- |

Use scientific meetings to detect active programs before or after public milestones.

## Where and how to work

| **Sources**    | AACR, ASCO, SITC, PEGS, Antibody Engineering & Therapeutics and company event pages.   |
| -------------- | -------------------------------------------------------------------------------------- |
| **Search**     | Company name, target, antibody format, poster, oral presentation and preclinical data. |
| **Extract**    | Abstract title, date, program, authors, affiliation and exact scientific claim.        |
| **Timing**     | Outreach near the event when a direct work package is relevant to the next milestone.  |
| **Buyer clue** | Presenting authors and program leaders can identify internal champions.                |
| **Reject**     | Academic-only presentations with no commercial asset owner.                            |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **57** | **SEC and Public-Company Filings** |
| ------ | ---------------------------------- |

Use filings for precise pipeline, cash runway, outsourcing and risk disclosures.

## Where and how to work

| **Website**          | sec.gov/edgar/search and company investor-relations pages.                        |
| -------------------- | --------------------------------------------------------------------------------- |
| **Forms**            | 10-K, 10-Q, 8-K, S-1 and investor presentations.                                  |
| **Extract**          | Pipeline changes, R&D spend, collaborators, cash runway and strategic priorities. |
| **Use**              | Selective account intelligence for small public biotech.                          |
| **Direct-deal test** | Named discovery program plus plausible external design need.                      |
| **Reject**           | Broad corporate filing with no actionable program or near-term budget.            |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **58** | **Source Reliability and Evidence Hierarchy** |
| ------ | --------------------------------------------- |

Use the strongest source available and clearly separate fact from inference.

## Where and how to work

| **Level 1**         | Official company pages, regulatory registries, patents, grants and filings.                         |
| ------------------- | --------------------------------------------------------------------------------------------------- |
| **Level 2**         | Peer-reviewed publications and conference abstracts.                                                |
| **Level 3**         | Reputable biotech news and funding databases.                                                       |
| **Level 4**         | LinkedIn jobs and employee profiles for current organizational signals.                             |
| **Inference label** | Bottleneck and project hypothesis must be explicitly marked as an inference unless stated.          |
| **Approval rule**   | High-priority accounts require at least one Level 1 or Level 2 source plus a recent timing trigger. |

## Operator checklist

**•** Use a controlled date window and save the query.

**•** Open the original source.

**•** Resolve the therapeutic owner.

**•** Extract the exact scientific problem.

**•** Apply hard exclusions before enrichment.

**Source rule:** The source finds evidence; it does not automatically create a sales lead.

| **59** | **Query Design Principles** |
| ------ | --------------------------- |

Build queries that reveal an owned program and an active design problem.

## Query specification

| **Structure**      | \[modality/problem phrase\] + \[therapeutic/company term\] + optional \[stage/trigger\]. |
| ------------------ | ---------------------------------------------------------------------------------------- |
| **Exact phrases**  | Quote technical phrases such as "affinity maturation" or "antibody humanization".        |
| **Company terms**  | biotech, therapeutics, company, startup, pipeline, preclinical or Series A.              |
| **Negative terms** | \-CRO -CDMO -diagnostic -reagent -supplier -services where supported.                    |
| **Date**           | 180 days for backfill; 7-30 days for heartbeat.                                          |
| **Measurement**    | Store query-to-approved-company and query-to-meeting conversion.                         |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **60** | **Core Antibody and Protein Query Bank** |
| ------ | ---------------------------------------- |

Use these queries as seeds, then narrow from observed noise.

## Query specification

| **Affinity**            | "antibody affinity maturation" biotech             |
| ----------------------- | -------------------------------------------------- |
| **De novo**             | "de novo antibody" therapeutics startup            |
| **Protein engineering** | "protein engineering" therapeutic antibody biotech |
| **Humanization**        | "antibody humanization" therapeutic company        |
| **Developability**      | "developability optimization" antibody biotech     |
| **Membrane targets**    | "membrane protein" antibody discovery company      |
| **Bispecific**          | "bispecific antibody" preclinical biotech          |
| **Specificity**         | "off-target screening" antibody discovery          |
| **Epitope**             | "epitope mapping" therapeutic antibody             |
| **Secreted target**     | "secreted protein" antibody discovery biotech      |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **61** | **Hiring Query Bank** |
| ------ | --------------------- |

Detect program expansion, internal gaps and execution timing.

## Query specification

| **Leadership**     | "Head of Antibody Discovery" hiring biotech    |
| ------------------ | ---------------------------------------------- |
| **Engineering**    | "Director Protein Engineering" biotech hiring  |
| **Discovery**      | "antibody discovery scientist" therapeutics    |
| **Developability** | "antibody developability" hiring biotech       |
| **Computational**  | "computational protein design" biotech hiring  |
| **Bispecific**     | "bispecific antibody scientist" job            |
| **Humanization**   | "antibody humanization" scientist job          |
| **Biologics**      | "biologics discovery" protein engineer company |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **62** | **Funding Query Bank** |
| ------ | ---------------------- |

Find companies that recently acquired resources for active antibody programs.

## Query specification

| **Series A**        | "Series A" antibody pipeline biotech                           |
| ------------------- | -------------------------------------------------------------- |
| **Seed**            | seed funding protein engineering therapeutics                  |
| **Bispecific**      | funding "bispecific antibody" preclinical                      |
| **Biologics**       | biologics startup raises funding antibody                      |
| **Use of proceeds** | funding "advance antibody pipeline" biotech                    |
| **Candidate**       | funding "preclinical candidate" antibody company               |
| **Expansion**       | raises capital "antibody discovery" team                       |
| **Direct test**     | Confirm use of proceeds and program stage on the company site. |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **63** | **Pipeline and Milestone Query Bank** |
| ------ | ------------------------------------- |

Find named programs moving into design, optimization or candidate selection.

## Query specification

| **New program**         | "new antibody program" biotech preclinical             |
| ----------------------- | ------------------------------------------------------ |
| **Expansion**           | "bispecific pipeline expansion" biotech                |
| **Optimization**        | "lead optimization" therapeutic antibody company       |
| **Candidate selection** | "preclinical candidate selection" antibody biotech     |
| **Target**              | "membrane protein target" antibody biotech             |
| **Nomination**          | "development candidate" antibody company               |
| **Platform**            | "antibody discovery platform" pipeline expansion       |
| **Direct test**         | Identify the exact asset and next technical milestone. |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **64** | **Publication Query Bank** |
| ------ | -------------------------- |

Find company-affiliated research that exposes target, modality and limitations.

## Query specification

| **Humanization**   | antibody humanization therapeutic \[date\]        |
| ------------------ | ------------------------------------------------- |
| **Affinity**       | antibody affinity maturation company affiliation  |
| **Bispecific**     | bispecific antibody preclinical target company    |
| **Membrane**       | membrane protein therapeutic antibody             |
| **Developability** | antibody stability developability therapeutic     |
| **Specificity**    | cross-reactivity therapeutic antibody target      |
| **Protein**        | engineered protein therapeutic company            |
| **Direct test**    | Affiliation and asset ownership must be verified. |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **65** | **Clinical Trial Query Bank** |
| ------ | ----------------------------- |

Use narrow trial searches for sponsor and next-generation program intelligence.

## Query specification

| **Intervention** | antibody OR monoclonal antibody OR bispecific                                |
| ---------------- | ---------------------------------------------------------------------------- |
| **Status**       | Recruiting, Active not recruiting or Not yet recruiting.                     |
| **Phase**        | Early Phase 1, Phase 1 and selected Phase 2.                                 |
| **Sponsor**      | Company name when monitoring a known approved account.                       |
| **Condition**    | Disease area linked to the target or program.                                |
| **Update**       | Last update in the selected heartbeat window.                                |
| **Reject**       | Trial presence alone does not create the platform intent.                    |
| **Direct test**  | Look for parallel discovery, new format or next-generation program evidence. |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **66** | **Grant Query Bank** |
| ------ | -------------------- |

Find funded therapeutic antibody/protein discovery and optimization work.

## Query specification

| **Design**         | "antibody engineering" therapeutic                            |
| ------------------ | ------------------------------------------------------------- |
| **Humanization**   | "antibody humanization" SBIR                                  |
| **Protein**        | "protein design" therapeutic antibody                         |
| **Bispecific**     | bispecific antibody SBIR                                      |
| **Target**         | membrane protein antibody therapeutic grant                   |
| **Developability** | antibody developability grant                                 |
| **Company filter** | Small business or company recipient preferred.                |
| **Direct test**    | Award objective must support a defined platform work package. |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **67** | **Patent Query Bank** |
| ------ | --------------------- |

Find recent assignee-owned sequence and format work.

## Query specification

| **Assignee**       | company name + antibody patent                           |
| ------------------ | -------------------------------------------------------- |
| **Affinity**       | "affinity maturation" antibody patent                    |
| **Humanization**   | humanized antibody assignee                              |
| **Bispecific**     | bispecific antibody target assignee                      |
| **Epitope**        | therapeutic antibody epitope patent                      |
| **Developability** | antibody stability sequence patent                       |
| **Format**         | nanobody, Fab, scFv, multispecific or fusion protein.    |
| **Direct test**    | Confirm assignee, active company and commercial program. |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **68** | **Negative Keywords and Noise Control** |
| ------ | --------------------------------------- |

Use exclusions aggressively so automation does not feed irrelevant companies.

## Query specification

| **Commercial exclusions**  | CRO, CDMO, contract, services, manufacturer, supplier, reagent and catalogue.    |
| -------------------------- | -------------------------------------------------------------------------------- |
| **Modality exclusions**    | diagnostic, assay, imaging, research use only and test kit.                      |
| **Institution exclusions** | university, hospital and institute when company ownership is absent.             |
| **Content exclusions**     | review, market report, job aggregator, conference sponsor and vendor directory.  |
| **Competitor exclusions**  | Known AI antibody-design and antibody-engineering service providers.             |
| **Practice**               | Maintain a versioned negative-keyword library per source because syntax differs. |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **69** | **Date Windows, Backfills and Heartbeats** |
| ------ | ------------------------------------------ |

Use recency appropriate to source velocity and commercial timing.

## Query specification

| **Initial backfill**   | Last 180 days for news, jobs, publications, grants and patents.         |
| ---------------------- | ----------------------------------------------------------------------- |
| **Fast heartbeat**     | Last 7 days for news and company announcements.                         |
| **Standard heartbeat** | Last 30 days for jobs, publications and trials.                         |
| **Slow sources**       | Monthly for patents, grants and filings.                                |
| **Known accounts**     | Monitor pipeline/news pages weekly and trials monthly.                  |
| **Staleness**          | Revalidate approved account evidence after 60 days before new outreach. |
| **Rule**               | Store the date window with every actor run and raw signal.              |

## Testing protocol

**1\.** Run 10-30 results manually or in a small actor test.

**2\.** Classify every result.

**3\.** Calculate relevant, resolved and approved rates.

**4\.** Add negative terms or tighten stage/modality.

**5\.** Schedule only when noise is controlled.

**Acceptance:** A query is production-ready only when obvious bad categories are rejected and at least 70% of sampled records can be classified.

| **70** | **Apify Operating Model** |
| ------ | ------------------------- |

Use Apify as the collection and enrichment layer, not the decision maker.

## Implementation specification

| **Discover**  | Run source-specific actors from saved tasks.                         |
| ------------- | -------------------------------------------------------------------- |
| **Store**     | Each actor writes a default dataset; preserve run ID and raw output. |
| **Transform** | n8n/Make or code normalizes fields into Raw Signals.                 |
| **Classify**  | AI extracts scientific entities and proposes routing.                |
| **Approve**   | Human reviewer controls Company Master status.                       |
| **Enrich**    | LinkedIn and email actors run only on Approved companies/contacts.   |
| **Measure**   | Actor Run Log tracks cost, output, errors, approvals and meetings.   |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **71** | **Apify Account and Workspace Setup** |
| ------ | ------------------------------------- |

Create a controlled production environment before scheduling actors.

## Implementation specification

| **Workspace**   | Dedicated project workspace and neutral naming convention.                      |
| --------------- | ------------------------------------------------------------------------------- |
| **Credentials** | Store APIFY_TOKEN securely; do not paste tokens into Sheets or prompts.         |
| **Naming**      | SENT-M1-PUBMED-\[query family\], SENT-M5-JOBS-\[region\], etc.                  |
| **Folders**     | Discovery, Validation, Company Enrichment, Contact Enrichment and Verification. |
| **Budgets**     | Set platform spend limits and actor-specific test caps.                         |
| **Access**      | Automation builder admin; researchers dataset/read access; approver view only.  |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **72** | **Actor Tasks and Input Templates** |
| ------ | ----------------------------------- |

Save a task only after a small run proves the actor schema and query.

## Implementation specification

| **Task content**    | Actor version, input JSON, query ID, date window, maxItems and proxy settings.          |
| ------------------- | --------------------------------------------------------------------------------------- |
| **Test size**       | 5-20 items for technical schema; 10-30 for relevance testing.                           |
| **Version control** | Export or document input JSON whenever changed.                                         |
| **Stable fields**   | Map only fields consistently present across test runs.                                  |
| **Raw backup**      | Keep the complete actor item alongside normalized fields.                               |
| **Promotion**       | Test -> Approved for schedule -> Production; never edit production task without retest. |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **73** | **Datasets, Storage and Field Mapping** |
| ------ | --------------------------------------- |

Move from actor-specific output to one normalized Raw Signal schema.

## Implementation specification

| **Dataset keys**  | Actor run ID, dataset ID, fetchedAt, source item ID and query.                                    |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| **Normalization** | source_url, signal_date, company_candidate, title, raw_text, target, disease, modality and stage. |
| **Idempotency**   | Unique key combines source, source item ID/URL and meaningful update date.                        |
| **Retention**     | Retain raw datasets at least through the feedback and QA period.                                  |
| **Exports**       | Use JSON for automation; CSV/Excel only for analyst review.                                       |
| **Failure**       | Schema change triggers mapping update before the next production run.                             |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **74** | **Schedules and Cadence** |
| ------ | ------------------------- |

Schedule according to source velocity, cost and decision value.

## Implementation specification

| **Daily**            | Google News and narrow company announcement queries.                     |
| -------------------- | ------------------------------------------------------------------------ |
| **Twice weekly**     | LinkedIn Jobs and selected hiring searches.                              |
| **Weekly**           | PubMed, company website crawls and ClinicalTrials.gov.                   |
| **Biweekly/monthly** | NIH RePORTER, patents, SEC and slow scientific sources.                  |
| **On demand**        | Single study, deep website crawl, company employee and email enrichment. |
| **Guardrail**        | Never schedule a contact-enrichment actor on an unapproved company list. |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **75** | **Webhooks and n8n/Make Handoff** |
| ------ | --------------------------------- |

Automate routing while keeping human approval visible.

## Implementation specification

| **Trigger**    | Apify actor run succeeds or dataset completes.                   |
| -------------- | ---------------------------------------------------------------- |
| **Step 1**     | Fetch dataset items and attach actor/query metadata.             |
| **Step 2**     | Normalize fields and deduplicate against Raw Signals.            |
| **Step 3**     | Call scientific extractor and company resolver.                  |
| **Step 4**     | Apply hard exclusions and route to Reject, Review or Human QA.   |
| **Step 5**     | Notify reviewer only for high-confidence candidates.             |
| **Error path** | Log failed runs, retry safely and never silently drop raw items. |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **76** | **Actor Testing and Acceptance QA** |
| ------ | ----------------------------------- |

Do not schedule an actor because it runs; schedule it because it produces usable records.

## Implementation specification

| **Technical test**  | Actor finishes, output schema is stable, URLs/dates are usable and no fields are silently truncated. |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| **Relevance test**  | At least 70% of sample records can be classified.                                                    |
| **Exclusion test**  | Obvious CRO, CDMO, diagnostics and academic-only examples are rejected.                              |
| **Resolution test** | Company can be resolved on a meaningful share of outputs.                                            |
| **Cost test**       | Cost per approved company is plausible at expected volume.                                           |
| **Approval**        | Research lead and automation builder sign off before recurring schedule.                             |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **77** | **Actor Run Log** |
| ------ | ----------------- |

Create one operational ledger for every automated run.

## Implementation specification

| **Identity**  | Run ID, actor, task, version, query family, start/end and status.          |
| ------------- | -------------------------------------------------------------------------- |
| **Volume**    | Input count, output count, duplicates and errors.                          |
| **Quality**   | Resolved companies, approved, review and rejected.                         |
| **Economics** | Compute units/actor charge, enrichment spend and cost per approval.        |
| **Outcome**   | Contacts, outreach, replies, meetings and pilots attributed to the source. |
| **Action**    | Increase, keep, reduce, pause or fix; owner and due date.                  |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **78** | **Apify Cost Control** |
| ------ | ---------------------- |

Spend only where a record has earned the next enrichment step.

## Implementation specification

| **Discovery cap**       | Small maxItems until source approval rate is known.                       |
| ----------------------- | ------------------------------------------------------------------------- |
| **Website crawl cap**   | Crawl approved or high-confidence candidate domains only.                 |
| **Company enrichment**  | One company detail call per canonical company; cache the result.          |
| **Employee enrichment** | Only approved companies; cap results and filter titles downstream.        |
| **Email enrichment**    | Only approved buyers; no bulk speculative enrichment.                     |
| **Verification**        | Verify just before outreach; reverify stale addresses.                    |
| **Metric**              | Cost per approved company and qualified meeting, not cost per raw record. |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **79** | **Deduplication and Change Detection** |
| ------ | -------------------------------------- |

Prevent duplicate work while preserving meaningful updates.

## Implementation specification

| **Company key** | Normalized domain plus canonical company name.                                |
| --------------- | ----------------------------------------------------------------------------- |
| **Signal key**  | Source item ID or canonical URL plus meaningful update date.                  |
| **Publication** | PMID/DOI.                                                                     |
| **Trial**       | NCT ID plus last update.                                                      |
| **Job**         | Job ID/URL plus posted date.                                                  |
| **Website**     | URL plus content hash; create a new signal only for material changes.         |
| **Rule**        | A new signal can raise intent score without creating a second company record. |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **80** | **AI Normalization Boundary** |
| ------ | ----------------------------- |

AI structures and proposes; it never invents evidence or final-approves an account.

## Implementation specification

| **Allowed**         | Entity extraction, modality/stage classification, company-name normalization and hypothesis drafting. |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| **Required output** | Strict JSON with evidence spans and confidence.                                                       |
| **Not allowed**     | Claiming a bottleneck as fact when only inferred.                                                     |
| **Fallback**        | Missing target/modality/bottleneck lowers confidence and routes to Review.                            |
| **Human checks**    | Therapeutic ownership, competitor status, direct project and buyer authority.                         |
| **Audit**           | Store model version, prompt version and raw response for approved records.                            |

## Production checklist

**•** Use saved tasks and controlled inputs.

**•** Retain raw actor output.

**•** Log cost and errors.

**•** Apply dedupe before AI.

**•** Require human approval before enrichment.

**Automation principle:** Automation increases repeatability; it does not lower the qualification standard.

| **81** | **Biomedical Signal Classifier Prompt** |
| ------ | --------------------------------------- |

Convert raw source text into structured scientific evidence with explicit confidence.

## Prompt or QA specification

| **Input**      | Source type, title, raw text, URL, date and company candidate.                                      |
| -------------- | --------------------------------------------------------------------------------------------------- |
| **Extract**    | Target, disease, modality, asset stage, therapeutic owner, scientific problem and evidence phrases. |
| **Classify**   | platform relevant / not relevant / uncertain.                                                       |
| **Confidence** | 0-100 for each extracted field.                                                                     |
| **Safety**     | Do not infer ownership from author affiliation alone.                                               |
| **Output**     | Strict JSON; unresolved fields are null, not guessed.                                               |

## Copy-ready core instruction

SYSTEM: You classify biomedical buying signals for an AI antibody and protein design platform.  
Return JSON only. Extract only facts supported by the supplied source.  
Fields: company_candidate, therapeutic_owner_status, target, disease, modality, asset_stage, scientific_problem, signal_type, signal_date, evidence_quotes, confidence, next_step.  
Hard reject CRO, CDMO, diagnostics-only, reagent, manufacturing and service providers.

## Human control

**•** Check every evidence phrase.

**•** Separate fact from inference.

**•** Reject hard exclusions immediately.

**•** Approve only a direct project, not a general relationship.

**Quality rule:** AI confidence cannot override missing ownership, missing direct project or a hard exclusion.

| **82** | **Company Resolver Prompt** |
| ------ | --------------------------- |

Map source organizations to the actual therapeutic asset owner.

## Prompt or QA specification

| **Input**        | Raw organization names, affiliations, sponsor, assignee, website clues and source URL. |
| ---------------- | -------------------------------------------------------------------------------------- |
| **Task**         | Return canonical company, domain, aliases and ownership relationship.                  |
| **Status**       | Owner, co-owner, licensee, service provider, academic institution or unclear.          |
| **Verification** | Prefer official company, registry, patent or trial evidence.                           |
| **Reject**       | Service provider or institution without a commercial asset owner.                      |
| **Output**       | Canonical company and evidence-backed resolution confidence.                           |

## Copy-ready core instruction

Resolve the organization behind this signal. Do not assume the publication affiliation is the commercial owner.  
Return JSON: canonical_company, domain, relationship_to_asset, therapeutic_owner_confirmed, evidence, confidence, unresolved_question.

## Human control

**•** Check every evidence phrase.

**•** Separate fact from inference.

**•** Reject hard exclusions immediately.

**•** Approve only a direct project, not a general relationship.

**Quality rule:** AI confidence cannot override missing ownership, missing direct project or a hard exclusion.

| **83** | **Direct-Deal ICP Gate Prompt** |
| ------ | ------------------------------- |

Apply the strict company gate before buyer or email enrichment.

## Prompt or QA specification

| **Mandatory**  | Therapeutic owner, supported antibody/protein modality, relevant stage, recent trigger and defined bottleneck. |
| -------------- | -------------------------------------------------------------------------------------------------------------- |
| **Commercial** | Specific paid project and plausible validation capacity.                                                       |
| **Exclusions** | CRO, CDMO, diagnostics, reagents, manufacturing, academic-only and direct competitors.                         |
| **Decision**   | Approve, Review or Reject.                                                                                     |
| **Review**     | Exactly one missing fact and the next verification action.                                                     |
| **Output**     | Decision, failed/passed gates, direct project hypothesis and evidence.                                         |

## Copy-ready core instruction

Evaluate for a direct paid platform project.  
Approve only if the company owns a therapeutic antibody/protein program and a current design/optimization work package can be stated.  
Return JSON: decision, passed_gates, failed_gates, project_hypothesis, buyer_titles, evidence, next_action.

## Human control

**•** Check every evidence phrase.

**•** Separate fact from inference.

**•** Reject hard exclusions immediately.

**•** Approve only a direct project, not a general relationship.

**Quality rule:** AI confidence cannot override missing ownership, missing direct project or a hard exclusion.

| **84** | **Direct Project Hypothesis Prompt** |
| ------ | ------------------------------------ |

Translate evidence into a realistic paid pilot without overclaiming.

## Prompt or QA specification

| **Input**            | Company, program, target, modality, stage, bottleneck, trigger and validation capacity. |
| -------------------- | --------------------------------------------------------------------------------------- |
| **Output**           | One precise project objective, required inputs, expected outputs and buyer.             |
| **Allowed language** | Could support, may be relevant, focused pilot, ranked shortlist and wet-lab validation. |
| **Forbidden**        | Guaranteed performance, solved asset, revolutionary or generic strategic partnership.   |
| **Scope**            | One target or one lead series whenever possible.                                        |
| **Decision**         | If inputs or validation path are missing, route to Review.                              |

## Copy-ready core instruction

Draft a direct paid pilot hypothesis.  
Format: objective; evidence; client inputs; Platform outputs; validation path; likely buyer; unresolved risk.  
Do not invent performance claims or non-public data.

## Human control

**•** Check every evidence phrase.

**•** Separate fact from inference.

**•** Reject hard exclusions immediately.

**•** Approve only a direct project, not a general relationship.

**Quality rule:** AI confidence cannot override missing ownership, missing direct project or a hard exclusion.

| **85** | **Scoring Formulas and Priority Routing** |
| ------ | ----------------------------------------- |

Use formulas for queue order, not as a substitute for hard exclusions or human judgment.

## Prompt or QA specification

| **Scientific fit**  | 0-25 based on modality, stage, target and bottleneck.                   |
| ------------------- | ----------------------------------------------------------------------- |
| **Intent**          | 0-25 based on trigger strength and recency.                             |
| **Project clarity** | 0-20 based on defined work package and needed inputs.                   |
| **Budget**          | 0-15 based on capital, team, program count and external spend.          |
| **Buyer**           | 0-10 based on authority and reachable backup.                           |
| **Confidence**      | 0-5 based on source strength and ownership clarity.                     |
| **Routing**         | A: 80+, B: 68-79, Review: 55-67, Reject below 55 or any hard exclusion. |

## Human control

**•** Check every evidence phrase.

**•** Separate fact from inference.

**•** Reject hard exclusions immediately.

**•** Approve only a direct project, not a general relationship.

**Quality rule:** AI confidence cannot override missing ownership, missing direct project or a hard exclusion.

| **86** | **Human QA and Approval View** |
| ------ | ------------------------------ |

The reviewer must be able to approve or reject from one screen without hunting across systems.

## Prompt or QA specification

| **Evidence panel**    | Source URL, date, exact phrase and raw text.                             |
| --------------------- | ------------------------------------------------------------------------ |
| **Company panel**     | Website, therapeutic ownership, modality, stage, funding and exclusions. |
| **Project panel**     | Bottleneck, direct pilot, client inputs, validation path and risks.      |
| **Buyer panel**       | Primary and backup roles; actual contacts remain locked until approval.  |
| **Decision controls** | Approve, Review with one question, Reject with reason.                   |
| **Audit**             | Reviewer, timestamp and change history.                                  |

## Human control

**•** Check every evidence phrase.

**•** Separate fact from inference.

**•** Reject hard exclusions immediately.

**•** Approve only a direct project, not a general relationship.

**Quality rule:** AI confidence cannot override missing ownership, missing direct project or a hard exclusion.

| **87** | **LinkedIn Company Enrichment** |
| ------ | ------------------------------- |

Enrich an approved company with current size, location and organizational context.

## Exact tool and operating rule

| **Actor**    | apimaestro/linkedin-company-detail.                                               |
| ------------ | --------------------------------------------------------------------------------- |
| **Input**    | Canonical company name or LinkedIn company URL.                                   |
| **Output**   | Overview, employee count, locations, industry, specialties and LinkedIn identity. |
| **Use**      | Confirm current operation, approximate scale and buyer-mapping feasibility.       |
| **Cache**    | One current record per company; refresh only when stale.                          |
| **Boundary** | Do not use this actor to discover unqualified companies.                          |

## Contact QA

**•** Current company and title verified.

**•** Role matches the named program.

**•** Seniority can sponsor or champion the project.

**•** Primary and backup are not identical functions.

**•** Email is verified before send.

**Enrichment rule:** The company earns enrichment by passing the gate; the contact earns outreach by matching the project.

| **88** | **LinkedIn Employee Discovery** |
| ------ | ------------------------------- |

Find the buyer set only after the company is approved.

## Exact tool and operating rule

| **Actor**  | apimaestro/linkedin-company-employees-scraper-no-cookies.                                                    |
| ---------- | ------------------------------------------------------------------------------------------------------------ |
| **Input**  | Approved company name/URL and conservative maximum results.                                                  |
| **Filter** | CSO, VP Discovery, Head/Director Antibody Discovery, Protein Engineering, Biologics and External Innovation. |
| **Output** | Name, title, profile URL and current company.                                                                |
| **QA**     | Verify current role on profile and company team page.                                                        |
| **Stop**   | Do not scrape all employees or enrich irrelevant functions.                                                  |

## Contact QA

**•** Current company and title verified.

**•** Role matches the named program.

**•** Seniority can sponsor or champion the project.

**•** Primary and backup are not identical functions.

**•** Email is verified before send.

**Enrichment rule:** The company earns enrichment by passing the gate; the contact earns outreach by matching the project.

| **89** | **Sales Navigator Operating Procedure** |
| ------ | --------------------------------------- |

Use Sales Navigator for precise buyer validation and relationship context.

## Exact tool and operating rule

| **Actor option**   | curious_coder/linkedin-sales-navigator-search-scraper; requires current Sales Navigator search URL/cookies per actor instructions. |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Manual filters** | Current company, seniority, function and exact title groups.                                                                       |
| **Account first**  | Open approved company/account, then search people inside that company.                                                             |
| **Output**         | Primary buyer, backup buyer, profile URL, tenure and role rationale.                                                               |
| **Deep search**    | Use only for Priority A accounts due cost and account risk.                                                                        |
| **Boundary**       | Never start with a broad biotech-title search.                                                                                     |

## Contact QA

**•** Current company and title verified.

**•** Role matches the named program.

**•** Seniority can sponsor or champion the project.

**•** Primary and backup are not identical functions.

**•** Email is verified before send.

**Enrichment rule:** The company earns enrichment by passing the gate; the contact earns outreach by matching the project.

| **90** | **Contact and Email Enrichment** |
| ------ | -------------------------------- |

Use the least expensive reliable method after buyer approval.

## Exact tool and operating rule

| **Preferred**     | Apollo native search/enrichment or another approved contact provider.                                                                               |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Apify caution** | coladeu/apollo-person-email-enrichment is listed under maintenance as of July 2026; do not make production dependent on it until status is cleared. |
| **Input**         | Approved person identity, company and profile/domain.                                                                                               |
| **Output**        | Work email, source, confidence and enrichment date.                                                                                                 |
| **Fallback**      | Company email pattern plus verification; never guess and send without verification.                                                                 |
| **Boundary**      | One primary and one backup buyer per account initially.                                                                                             |

## Contact QA

**•** Current company and title verified.

**•** Role matches the named program.

**•** Seniority can sponsor or champion the project.

**•** Primary and backup are not identical functions.

**•** Email is verified before send.

**Enrichment rule:** The company earns enrichment by passing the gate; the contact earns outreach by matching the project.

| **91** | **Email Verification and Deliverability Gate** |
| ------ | ---------------------------------------------- |

Verify every enriched address before it enters the outreach platform.

## Exact tool and operating rule

| **Actor 1**   | account56/email-verifier for bulk decisive verification.                           |
| ------------- | ---------------------------------------------------------------------------------- |
| **Actor 2**   | automation-lab/smtp-email-verifier for deeper high-value mailbox/catch-all checks. |
| **Status**    | Valid, invalid, catch-all, unknown, disposable and risky.                          |
| **Send rule** | Valid only by default; catch-all requires domain and buyer confidence review.      |
| **Recheck**   | Reverify after 60-90 days or before reactivation.                                  |
| **Log**       | Verification provider, result, date and raw reason.                                |

## Contact QA

**•** Current company and title verified.

**•** Role matches the named program.

**•** Seniority can sponsor or champion the project.

**•** Primary and backup are not identical functions.

**•** Email is verified before send.

**Enrichment rule:** The company earns enrichment by passing the gate; the contact earns outreach by matching the project.

| **92** | **Buyer Selection Matrix** |
| ------ | -------------------------- |

Choose the person closest to the scientific decision and budget.

## Exact tool and operating rule

| **CSO / founder-CSO**            | Best for early biotech, project sponsorship and budget.                       |
| -------------------------------- | ----------------------------------------------------------------------------- |
| **VP Discovery**                 | Best for multi-program discovery and external resource decisions.             |
| **Head of Antibody Discovery**   | Best technical owner for binder generation, affinity and candidate selection. |
| **Head of Protein Engineering**  | Best for sequence design, humanization, stability and developability.         |
| **Director/Principal Scientist** | Strong champion but usually needs an executive sponsor.                       |
| **BD/External Innovation**       | Secondary route only when tied to a named program and scientific owner.       |

## Contact QA

**•** Current company and title verified.

**•** Role matches the named program.

**•** Seniority can sponsor or champion the project.

**•** Primary and backup are not identical functions.

**•** Email is verified before send.

**Enrichment rule:** The company earns enrichment by passing the gate; the contact earns outreach by matching the project.

| **93** | **Direct Pilot Packaging** |
| ------ | -------------------------- |

Turn the research insight into a low-risk, purchasable scientific pilot.

## Direct-deal specification

| **Objective**        | One defined target or existing lead series; one clear optimization/design goal.                               |
| -------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Client inputs**    | Target/antigen information, sequences where relevant, desired profile, known liabilities and validation plan. |
| **Platform outputs** | Ranked candidate panel, design rationale, predicted strengths/risks and wet-lab validation order.             |
| **Commercial shape** | Fixed scope, milestone, timeline, responsibilities, data-handling terms and follow-on option.                 |
| **Qualification**    | Rights/access to input data, wet-lab capacity and buyer authority.                                            |
| **Expansion**        | Successful validation can lead to additional targets, recurring projects or license discussion.               |

## Commercial QA

**•** Name the asset or program.

**•** Name the work package.

**•** Name the buyer and validation path.

**•** Avoid generic strategic-partnership language.

**•** Record a concrete next step.

**Deal rule:** The target outcome is a scoped paid scientific engagement, not a general introduction or "explore synergies" call.

| **94** | **Outreach Queue and Message Handoff** |
| ------ | -------------------------------------- |

Outreach must lead toward the defined pilot, not a vague partnership conversation.

## Direct-deal specification

| **First line** | Reference the exact recent signal or program evidence.                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------------ |
| **Relevance**  | Name the design/optimization area without claiming the company has a confirmed problem.                      |
| **Offer**      | Suggest a focused discussion around candidate design, affinity, humanization, specificity or developability. |
| **CTA**        | Ask whether a short technical conversation around the named program would be useful.                         |
| **Evidence**   | Attach/store source internally; do not overload the message with research.                                   |
| **Approval**   | Commercial lead approves company, buyer, project hypothesis and message before send.                         |

## Commercial QA

**•** Name the asset or program.

**•** Name the work package.

**•** Name the buyer and validation path.

**•** Avoid generic strategic-partnership language.

**•** Record a concrete next step.

**Deal rule:** The target outcome is a scoped paid scientific engagement, not a general introduction or "explore synergies" call.

| **95** | **Reply Classification and Next Actions** |
| ------ | ----------------------------------------- |

Classify commercial meaning so the feedback loop improves the source and query system.

## Direct-deal specification

| **Positive - technical** | Buyer confirms relevance and asks about capability, data, pilot or meeting.    |
| ------------------------ | ------------------------------------------------------------------------------ |
| **Positive - referral**  | Contact identifies the correct scientific owner; update buyer map immediately. |
| **Timing**               | Relevant but later; record milestone/date and create a future task.            |
| **No need/internal**     | Record substitute capability and reduce similar accounts if repeated.          |
| **Wrong fit**            | Update exclusions, query negatives or company gate.                            |
| **No response**          | Do not interpret as wrong fit; test channel, buyer and message separately.     |

## Commercial QA

**•** Name the asset or program.

**•** Name the work package.

**•** Name the buyer and validation path.

**•** Avoid generic strategic-partnership language.

**•** Record a concrete next step.

**Deal rule:** The target outcome is a scoped paid scientific engagement, not a general introduction or "explore synergies" call.

| **96** | **Qualified Discovery Meeting Standard** |
| ------ | ---------------------------------------- |

A booked call is valuable only when it can progress toward a scoped scientific project.

## Direct-deal specification

| **Program**    | Named target/asset, modality and current stage.                                  |
| -------------- | -------------------------------------------------------------------------------- |
| **Problem**    | Design, optimization or candidate-selection objective.                           |
| **Inputs**     | Available sequences/data, ownership rights and constraints.                      |
| **Validation** | Internal lab or external wet-lab partner and decision criteria.                  |
| **Authority**  | Scientific sponsor, budget path and other stakeholders.                          |
| **Timing**     | Milestone and reason to act now.                                                 |
| **Next step**  | NDA/data review, technical scoping, pilot proposal or explicit disqualification. |

## Commercial QA

**•** Name the asset or program.

**•** Name the work package.

**•** Name the buyer and validation path.

**•** Avoid generic strategic-partnership language.

**•** Record a concrete next step.

**Deal rule:** The target outcome is a scoped paid scientific engagement, not a general introduction or "explore synergies" call.

| **97** | **Daily Operating SOP** |
| ------ | ----------------------- |

Run a consistent daily production cycle that protects research quality and keeps records moving.

## Morning: source intake

**1\.** Check scheduled Apify runs and actor errors.

**2\.** Import and deduplicate new Raw Signals.

**3\.** Review Google News/company announcements from the last 24-72 hours.

**4\.** Assign high-confidence signals to researchers.

## Research block

**1\.** Resolve company and therapeutic ownership.

**2\.** Open pipeline, technology, careers and team pages.

**3\.** Extract modality, stage, bottleneck and direct project hypothesis.

**4\.** Apply hard exclusions and score the account.

## Afternoon: QA and enrichment

**1\.** Scientific reviewer checks evidence and project realism.

**2\.** Commercial lead approves or rejects.

**3\.** Enrich only approved companies and buyers.

**4\.** Verify email and move approved messages to Outreach Queue.

## Daily target

| **Raw signals reviewed**        | 20-30 per researcher during controlled launch           |
| ------------------------------- | ------------------------------------------------------- |
| **Companies deeply researched** | 8-12                                                    |
| **Approved companies**          | 2-4 quality accounts                                    |
| **Review backlog**              | No item older than two working days                     |
| **Evidence quality**            | 100% approved records have URL, date and direct project |

**End-of-day test:** Can every approved company be explained in one paragraph from signal to paid pilot?

| **98** | **Weekly Operating SOP and Source Review** |
| ------ | ------------------------------------------ |

Use weekly evidence to decide where to increase, reduce or stop effort.

## Monday

**•** Run literature and funding backfills; review new company announcements.

## Tuesday

**•** Review trials, pipeline pages and approved-account changes.

## Wednesday

**•** Review patents, grants and conference/technical evidence.

## Thursday

**•** Run hiring, company enrichment and buyer mapping for approved accounts.

## Friday

**•** Approve outreach, review replies/meetings, update exclusions and source ROI.

## Weekly dashboard

| **Quality**    | Approvals, rejection reasons, wrong-fit rate and stale reviews               |
| -------------- | ---------------------------------------------------------------------------- |
| **Commercial** | Positive replies, qualified meetings, project proposals and pilots           |
| **Source ROI** | Raw signals, approvals, meetings and cost per approval by source/query       |
| **Learning**   | Objections, internal substitutes, buyer roles and winning project hypotheses |
| **Decision**   | Increase, keep, reduce or pause every active source family                   |

**Friday output:** One written decision per source: increase/keep/reduce/pause because of specific evidence.

| **99** | **30-Day Build Plan and First 100 Companies** |
| ------ | --------------------------------------------- |

Build in controlled stages; do not automate or scale before the previous gate works.

## Week 1: manual proof

**1\.** Create tables, exclusions, statuses and prompt versions.

**2\.** Test Google News, jobs, PubMed and company websites manually.

**3\.** Approve the first 20 approved therapeutic companies with full evidence.

**4\.** Document false positives and query changes.

## Week 2: signal spine

**1\.** Deploy small Apify tasks for proven queries.

**2\.** Normalize, dedupe and route Raw Signals.

**3\.** Test company resolver and ICP gate.

**4\.** Reach 40-50 approved companies cumulatively.

## Week 3: enrichment and outreach

**1\.** Add company detail, employee discovery and Sales Navigator validation.

**2\.** Enrich and verify two buyers per approved company.

**3\.** Send the first small human-approved outreach batch.

**4\.** Track technical replies and qualified meetings.

## Week 4: controlled scale

**1\.** Add grants, trials and patents only where useful.

**2\.** Complete the first 100 approved-company sprint in batches of ten.

**3\.** Measure source/query ROI and wrong-fit meetings.

**4\.** Scale only sources producing direct project conversations.

**Batch rule:** Each ten-company batch must contain evidence, project hypothesis, buyer title, exclusion check and outreach angle for every account.

| **100** | **Final Production Checklist and First Action** |
| ------- | ----------------------------------------------- |

The system is ready only when every control below is working in practice.

## Foundation checklist

**•** Platform work packages and direct-deal ICP locked.

**•** CRO, CDMO, diagnostics, reagent, manufacturing, academic-only and competitor exclusions loaded.

**•** Raw Signals, Company Master, evidence, Contacts and Outreach Queue live.

**•** Query bank, negative keywords and date windows versioned.

## Automation checklist

**•** Apify tasks tested with small samples and stable field mapping.

**•** Run log, spend caps, dedupe and failure alerts active.

**•** Raw actor output retained and AI prompts versioned.

**•** No company/contact enrichment automation bypasses approval.

## Revenue checklist

**•** Every approved account has a direct paid pilot hypothesis.

**•** Primary and backup buyers are role-verified.

**•** Email is verified and suppression checked.

**•** Outreach references real evidence and moves toward a technical pilot.

**•** Qualified meetings capture program, inputs, validation, authority, timing and next step.

## Start tomorrow

**1\.** Create the database and exclusion tabs.

**2\.** Run ten Google News queries and ten LinkedIn Jobs queries for the last 180 days.

**3\.** Research twenty raw signals and approve no more than five.

**4\.** Review the first five approvals with scientific leadership before automating.

**5\.** Build the first Apify tasks only from the queries that passed that review.

## Official implementation references

| **PubMed API**             | <https://www.ncbi.nlm.nih.gov/home/develop/api/>                              |
| -------------------------- | ----------------------------------------------------------------------------- |
| **ClinicalTrials.gov API** | <https://clinicaltrials.gov/data-api/api>                                     |
| **NIH RePORTER API**       | <https://api.reporter.nih.gov/>                                               |
| **USPTO Open Data**        | <https://data.uspto.gov/>                                                     |
| **SEC EDGAR APIs**         | <https://www.sec.gov/search-filings/edgar-application-programming-interfaces> |
| **Apify Store**            | <https://apify.com/store>                                                     |

**Final operating law:** No therapeutic ownership + no active platform-relevant problem + no direct paid project = no prospect.