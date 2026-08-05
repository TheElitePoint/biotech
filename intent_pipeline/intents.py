"""The intent catalog: every distinct query this pipeline runs, across every
free source, described in one place for reporting and future per-intent
tuning (enable/disable, cadence, retire a noisy query — SOP page 27's Seed
Sources table).

Each source module owns its own query list and does its own internal loop
over it in one `fetch()` call (a bulk sweep for ClinicalTrials.gov/NIH
RePORTER, N individual searches for the rest) — that is more efficient than
calling `fetch()` once per query. `catalog()` below only *introspects* those
lists; it never duplicates a query string by hand, so there is exactly one
place to add or remove a query and both the running pipeline and this report
pick it up.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sources import account_based, bing_news, biotech_rss, clinicaltrials, crossref, europepmc, nih_reporter, pubmed, sec_edgar


@dataclass
class Intent:
    id: str
    source: str
    signal_type: str
    query: str


def catalog() -> list[Intent]:
    items: list[Intent] = []

    for q in clinicaltrials.INTERVENTION_QUERIES:
        items.append(Intent(f"CTGOV::{q}", "clinicaltrials.gov", "program", q))

    for q in nih_reporter.TEXT_QUERIES:
        items.append(Intent(f"REPORTER::{q}", "nih_reporter", "capital", q))

    for q in europepmc.TERMS:
        items.append(Intent(f"EPMC::{q}", "europepmc", "scientific", q))

    for q in pubmed.TERMS:
        items.append(Intent(f"PUBMED::{q}", "pubmed", "scientific", q))

    for q, signal_type in bing_news.QUERIES:
        items.append(Intent(f"BING::{q}", "bing_news", signal_type, q))

    for q, signal_type in sec_edgar.QUERIES:
        items.append(Intent(f"SEC::{q}", "sec_edgar", signal_type, q))

    for q in crossref.TERMS:
        items.append(Intent(f"CROSSREF::{q}", "crossref", "scientific", q))

    for name, url in biotech_rss.FEEDS:
        items.append(Intent(f"RSS::{name}", "biotech_rss", "program", f"{name} feed ({url})"))

    for template, signal_type in account_based.ACCOUNT_QUERY_TEMPLATES:
        items.append(Intent(f"ACCOUNT::{template}", "account_based", signal_type, template))

    return items


# Which source module's fetch() the orchestrator calls for a given source name.
# Every fetch() already loops over that source's full query list internally.
SOURCES = {
    "clinicaltrials.gov": clinicaltrials.fetch,
    "nih_reporter": nih_reporter.fetch,
    "europepmc": europepmc.fetch,
    "pubmed": pubmed.fetch,
    "bing_news": bing_news.fetch,
    "sec_edgar": sec_edgar.fetch,
    "crossref": crossref.fetch,
    "biotech_rss": biotech_rss.fetch,
    "account_based": account_based.fetch,
}


def summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for intent in catalog():
        counts[intent.source] = counts.get(intent.source, 0) + 1
    return counts
