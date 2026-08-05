"""Intent packs, exclusions and scoring weights.

Everything the researcher tunes lives here. Code elsewhere should not hardcode
queries, domains or weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SignalType = Literal[
    "capital", "hiring", "program", "scientific", "execution", "milestone"
]


@dataclass
class Seed:
    """One row of the SOP Seed Sources table (page 27)."""

    seed_id: str
    query: str
    signal_type: SignalType
    # Tavily search depth: "basic" is cheap, "advanced" pulls more page text.
    depth: str = "basic"
    # Days of recency. SOP page 69: 180 for backfill, 7-30 for heartbeat.
    days: int = 30
    max_results: int = 20
    include_domains: list[str] = field(default_factory=list)
    exclude_domains: list[str] = field(default_factory=list)
    status: str = "Test"  # Test | Active | Reduce | Pause | Retired


# --- Domains ---------------------------------------------------------------

# Aggregators and directories: useful to read, never the company itself.
NEWS_DOMAINS = [
    "fiercebiotech.com",
    "biospace.com",
    "endpts.com",
    "businesswire.com",
    "prnewswire.com",
    "globenewswire.com",
    "labiotech.eu",
    "biopharmadive.com",
    # Press-release syndication / finance-news hosts. None of these are ever the
    # subject company — but a ticker mention like "(Nasdaq: XYZ)" in the article
    # body was enough to fool the domain-matches-content check into resolving
    # the company as "Nasdaq" or "Yahoo" itself (caught in testing on a
    # nasdaq.com-hosted Celldex/AC Immune press release).
    "nasdaq.com",
    "finance.yahoo.com",
    "uk.sports.yahoo.com",
    "morningstar.com",
    "benzinga.com",
    "streetinsider.com",
    "marketwatch.com",
    "seekingalpha.com",
    "pharmabiz.com",
    "pharmatimes.com",
    "medindia.net",
    "tmcnet.com",
    "dutchnews.nl",
    "manilatimes.net",
    "pharmaphorum.com",
]

# Applicant tracking systems. Unlike job boards, an ATS posting belongs to exactly one
# company and the URL path names it, so these resolve cleanly. Keeping them out of the
# blocked list is what makes the hiring trigger work at all.
ATS_HOSTS = {
    "boards.greenhouse.io": "path",
    "job-boards.greenhouse.io": "path",
    "jobs.lever.co": "path",
    "jobs.ashbyhq.com": "path",
    "apply.workable.com": "path",
    "jobs.smartrecruiters.com": "path",
    "careers.jobscore.com": "path",
    "recruiting.paylocity.com": "path",
}

# ATS platforms that put the company in the subdomain instead of the path.
ATS_SUBDOMAIN_SUFFIXES = (
    ".applytojob.com",
    ".bamboohr.com",
    ".breezy.hr",
    ".rippling-ats.com",
    ".teamtailor.com",
)

# Never resolve a company from these; they are sources, not asset owners.
NON_COMPANY_DOMAINS = set(NEWS_DOMAINS) | {
    "linkedin.com",
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "clinicaltrials.gov",
    "reporter.nih.gov",
    "patents.google.com",
    "sec.gov",
    "crunchbase.com",
    "pitchbook.com",
    "dealroom.co",
    "europepmc.org",
    "biorxiv.org",
    "medrxiv.org",
    "nature.com",
    "sciencedirect.com",
    "wikipedia.org",
    "glassdoor.com",
    "indeed.com",
    "ziprecruiter.com",
    "builtin.com",
    "x.com",
    "twitter.com",
    "youtube.com",
    "reddit.com",
}

# Junk that should never enter the queue at all.
BLOCKED_DOMAINS = {
    "indeed.com",
    "ziprecruiter.com",
    "glassdoor.com",
    "jooble.org",
    "simplyhired.com",
    "marketresearch.com",
    "grandviewresearch.com",
    "marketsandmarkets.com",
    "researchandmarkets.com",
    "prweb.com",
    "medium.com",
    "quora.com",
}


# --- Hard exclusions (SOP page 20 / 68) ------------------------------------

EXCLUSION_PATTERNS: dict[str, list[str]] = {
    "cro_cdmo": [
        "contract research organization",
        "contract development and manufacturing",
        "contract manufacturing",
        "fee-for-service",
        "our services include",
        "outsourcing partner",
        "we offer antibody discovery services",
        "custom antibody production",
    ],
    "diagnostics_reagent": [
        "research use only",
        r"\bruo\b",
        "diagnostic assay",
        "test kit",
        "catalog antibody",
        "catalogue antibody",
        "primary antibodies for",
        "elisa kit",
        "companion diagnostic only",
    ],
    "academic_only": [
        "department of",
        "school of medicine",
        r"\buniversity\b",
        "college of",
        r"\bfaculty of\b",
    ],
    "non_buyer": [
        "venture capital",
        "consulting services",
        "accelerator program",
        "market report",
        "industry report",
        "staffing agency",
        "recruitment agency",
    ],
    # Bare "CRO"/"CDMO" is deliberately NOT here. A therapeutic company naming its
    # manufacturing partner would be excluded by it, which costs real prospects.
    # gates.py treats the bare acronym as an exclusion only when the record is
    # *about* the service provider — see AMBIGUOUS_SERVICE_TERMS.
    "competitor": [
        "ai-powered antibody design platform",
        "generative protein design platform",
        "protein language model platform",
        "in silico antibody design services",
        "computational antibody engineering services",
    ],
}

# Terms that identify a service provider only when the record is *about* them —
# in the title, or next to self-referential language. A passing mention in the body
# of an otherwise good therapeutic company's news is not grounds for rejection.
AMBIGUOUS_SERVICE_TERMS = [r"\bcro\b", r"\bcdmo\b", "contract manufacturer"]

SELF_REFERENTIAL = [
    "we are a",
    "we provide",
    "our clients",
    "our customers",
    "our services",
    "is a leading",
    "as a global",
    "service offering",
    "capabilities include",
]

# Named competitors — reject on domain or name match (SOP page 21).
COMPETITOR_DOMAINS = {
    "absci.com",
    "generatebiomedicines.com",
    "biolojic.com",
    "nabla.bio",
    "chai-discovery.com",
    "cradle.bio",
    "diffusebio.com",
    "abcellera.com",
    "adaptyvbio.com",
    "isomorphiclabs.com",
    "exscientia.ai",
    "profluent.bio",
    "latentlabs.com",
}

# Confirmed non-prospects found during live runs. These are service or platform
# businesses that read like asset owners in search results, so the text-pattern
# exclusions miss them. Add here as review confirms them (SOP page 38: a rejected
# company cannot re-enter without new evidence).
EXCLUDED_DOMAINS = {
    "vivabiotech.com": "CRO: structure-based drug discovery services",
    "ginkgobioworks.com": "platform/services: synthetic biology foundry, not an asset owner",
    "twistbioscience.com": "reagent supplier: synthetic DNA and antibody libraries",
    "eurofins.com": "CRO: contract testing and lab services",
    "jubilantbiosys.com": "CRO: contract research services",
}


# --- Modality vocabulary (SOP page 15) -------------------------------------

MODALITY_TERMS = {
    "approve": [
        "monoclonal antibody",
        "bispecific",
        "multispecific",
        "trispecific",
        "nanobody",
        "vhh",
        "scfv",
        "fab fragment",
        "antibody fragment",
        "engineered protein",
        "therapeutic binder",
        "antibody therapeutic",
        "biologic candidate",
    ],
    "conditional": [
        "antibody-drug conjugate",
        r"\badc\b",
        "fusion protein",
        "cytokine engineering",
        "il-2",
        "fc fusion",
        "car-t",
        "cell therapy",
    ],
    "reject": [
        "small molecule",
        "gene therapy",
        "aav vector",
        "mrna vaccine",
        "sirna",
        "antisense oligonucleotide",
        "crispr editing",
        "microbiome",
    ],
}

# --- Bottleneck vocabulary (SOP page 16) -----------------------------------

BOTTLENECK_TERMS = {
    "discovery": [
        "difficult target",
        "undruggable",
        "hit rate",
        "binder diversity",
        "de novo",
        "no known binder",
        "gpcr",
        "membrane protein",
        "ion channel",
    ],
    "binding_performance": [
        "affinity maturation",
        "picomolar",
        "potency",
        "epitope coverage",
        "arm balancing",
        "avidity",
    ],
    "specificity": [
        "cross-reactivity",
        "off-target",
        "selectivity",
        "polyreactivity",
        "target family discrimination",
    ],
    "sequence_risk": [
        "humanization",
        "immunogenicity",
        "sequence liabilit",
        "aggregation",
        "thermostability",
        "deamidation",
    ],
    "development_risk": [
        "developability",
        "expression titer",
        "solubility",
        "manufacturability",
        "viscosity",
        "format conversion",
    ],
    "decision_risk": [
        "candidate selection",
        "shortlist",
        "wet-lab capacity",
        "prioritize variants",
        "screening throughput",
    ],
}

# --- Stage vocabulary (SOP page 13/14) -------------------------------------

STAGE_TERMS = {
    "discovery": ["discovery stage", "hit identification", "binder generation"],
    "lead_optimization": ["lead optimization", "lead series", "optimization campaign"],
    "candidate_selection": [
        "development candidate",
        "candidate nomination",
        "candidate selection",
    ],
    "preclinical": ["preclinical", "ind-enabling", "ind enabling", "gLP toxicology"],
    "clinical": ["phase 1", "phase 2", "phase 3", "first-in-human"],
}

# Stage evidence specific to hiring signals. A job description states the stage through
# the role it is filling, not through pipeline language: nobody writes "we are at the
# lead optimization stage" in a posting, they advertise for a lead optimization scientist.
ROLE_STAGE_TERMS = {
    "discovery": [
        "antibody discovery",
        "biologics discovery",
        "hit discovery",
        "target discovery",
        "discovery scientist",
        "discovery research",
    ],
    "lead_optimization": [
        "lead optimization",
        "antibody engineering",
        "affinity engineering",
        "molecule optimization",
        "protein optimization",
    ],
    "candidate_selection": [
        "candidate selection",
        "candidate nomination",
        "molecule assessment",
    ],
    "preclinical": [
        "preclinical development",
        "ind-enabling",
        "translational research",
    ],
}

FUNDING_TERMS = [
    "series a",
    "series b",
    "seed round",
    "seed financing",
    "oversubscribed",
    "raises $",
    "raised $",
    "million financing",
    "sbir",
    "sttr",
    "non-dilutive",
]


# --- Scoring weights (SOP pages 24 and 85) ---------------------------------

SCORE_CAPS = {
    "scientific_fit": 25,
    "intent": 25,
    "project_clarity": 20,
    "budget": 15,
    "buyer_access": 10,
    "data_confidence": 5,
}

ROUTING = [(80, "A"), (68, "B"), (55, "Review")]  # below 55 -> Reject

# Recency decay for the intent score. Days since signal -> multiplier.
INTENT_RECENCY = [(14, 1.0), (30, 0.9), (60, 0.7), (120, 0.45), (180, 0.25)]

# Relative strength of each trigger family before recency decay (SOP page 17).
SIGNAL_STRENGTH: dict[str, float] = {
    "capital": 1.00,
    "milestone": 0.95,
    "program": 0.90,
    "hiring": 0.80,
    "execution": 0.70,
    "scientific": 0.60,
}


# --- Buyer titles (SOP page 19) --------------------------------------------

BUYER_TITLES = {
    "economic": ["chief scientific officer", "cso", "founder", "ceo", "vp discovery"],
    "technical": [
        "head of antibody discovery",
        "head of protein engineering",
        "director, protein engineering",
        "head of biologics",
        "vp biologics",
    ],
    "champion": [
        "principal scientist",
        "director of antibody engineering",
        "senior scientist, protein engineering",
    ],
    "facilitator": ["head of business development", "external innovation"],
}


# --- Seed bank -------------------------------------------------------------
# Negative terms are appended by tavily.py so they stay in one place.

# Passed as include_domains on the hiring seeds so those queries only return postings
# whose URL identifies the employer.
ATS_DOMAINS = sorted(
    set(ATS_HOSTS) | {"myworkdayjobs.com", "bamboohr.com", "applytojob.com", "breezy.hr"}
)


NEGATIVE_TERMS = (
    "-CRO -CDMO -\"contract research\" -diagnostic -reagent -\"research use only\" "
    "-supplier -catalog -\"market report\""
)


SEEDS: list[Seed] = [
    # --- Capital triggers (SOP page 62) ---
    Seed("CAP-01", '"Series A" antibody pipeline biotech financing', "capital", days=30),
    Seed("CAP-02", 'seed financing "protein engineering" therapeutics startup', "capital", days=45),
    Seed("CAP-03", 'biotech raises funding "bispecific antibody" preclinical', "capital", days=30),
    Seed("CAP-04", 'financing "advance our antibody pipeline" biotech', "capital", days=60),
    Seed("CAP-05", 'startup emerges from stealth antibody discovery funding', "capital", days=60),
    # --- Program / milestone triggers (SOP page 63) ---
    Seed("PRG-01", '"development candidate" nomination antibody biotech', "milestone", days=30),
    Seed("PRG-02", '"lead optimization" therapeutic antibody company program', "program", days=45),
    Seed("PRG-03", '"pipeline expansion" bispecific antibody biotech', "program", days=45),
    Seed("PRG-04", '"new antibody program" preclinical biotech target', "program", days=45),
    Seed("PRG-05", 'biotech "IND-enabling" antibody candidate announcement', "milestone", days=45),
    # --- Hiring triggers (SOP page 61) ---
    # Aimed at applicant-tracking systems, not job boards. A Greenhouse or Lever URL
    # names the employer; an Indeed listing does not, and aggregators are blocked, so
    # the earlier general-search versions of these queries resolved zero companies.
    Seed(
        "JOB-01",
        '"antibody discovery" OR "protein engineering" scientist job',
        "hiring",
        days=45,
        include_domains=ATS_DOMAINS,
    ),
    Seed(
        "JOB-02",
        '"protein engineering" OR "computational protein design" biologics role',
        "hiring",
        days=45,
        include_domains=ATS_DOMAINS,
    ),
    Seed(
        "JOB-03",
        '"antibody engineering" OR "developability" OR "bispecific" scientist position',
        "hiring",
        days=45,
        include_domains=ATS_DOMAINS,
    ),
    # Company-hosted careers pages, which the ATS queries miss.
    Seed(
        "JOB-04",
        'biotech careers "antibody discovery" "our pipeline" open position',
        "hiring",
        days=45,
    ),
    Seed(
        "JOB-05",
        '"we are hiring" antibody OR "protein engineering" preclinical biotech team',
        "hiring",
        days=45,
    ),
    # --- Scientific triggers (SOP page 64) ---
    Seed("SCI-01", '"affinity maturation" therapeutic antibody company publication', "scientific", days=90),
    Seed("SCI-02", '"antibody humanization" therapeutic candidate company', "scientific", days=90),
    Seed("SCI-03", 'membrane protein GPCR therapeutic antibody discovery company', "scientific", days=90),
    Seed("SCI-04", 'antibody developability aggregation therapeutic company study', "scientific", days=90),
    # --- Execution triggers ---
    Seed("EXE-01", 'biotech partners wet-lab validation antibody discovery collaboration', "execution", days=60),
    Seed("EXE-02", 'biotech builds antibody discovery capability platform in-house', "execution", days=60),
]


def active_seeds(only: list[str] | None = None) -> list[Seed]:
    seeds = [s for s in SEEDS if s.status in ("Test", "Active")]
    if only:
        wanted = {o.upper() for o in only}
        seeds = [
            s
            for s in seeds
            if s.seed_id.upper() in wanted
            or s.seed_id.split("-")[0].upper() in wanted
            or s.signal_type.upper() in wanted
        ]
    return seeds
