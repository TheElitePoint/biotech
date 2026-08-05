"""Europe PMC source adapter.

Free, no API key. Every call uses a date window computed from *today*, never
a fixed hardcoded range, so a run next month searches next month's window —
not last year's. Finds commercial-affiliated antibody/protein papers and
resolves the company from the author affiliation text (ported from the old
daily_publications.py).
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from ..suppression import company_root
from .base import get_with_retry, make_item, make_session

TERMS = [
    '"bispecific antibody"',
    '"multispecific antibody"',
    "nanobody",
    '"antibody engineering"',
    '"antibody humanization"',
    '"affinity maturation"',
    '"antibody developability"',
    '"antibody-drug conjugate"',
    '"T cell engager"',
    "immunocytokine",
    '"therapeutic protein engineering"',
]

COMPANY_WORD = re.compile(
    r"\b(Therapeutics?|Biotherapeutics?|Biosciences?|Biotech(?:nology)?|"
    r"Pharmaceuticals?|Pharma|Biologics?|BioMed|Bio\b|Inc\.?|LLC|Ltd\.?|"
    r"Limited|GmbH|Corporation|Corp\.?|S\.?A\.?|A\.?G\.?)\b",
    re.I,
)
LEGAL_ONLY = re.compile(r"^(Inc\.?|LLC|Ltd\.?|Limited|GmbH|Corporation|Corp\.?|S\.?A\.?|A\.?G\.?)$", re.I)
LEGAL_CUT = re.compile(
    r"^(.{2,100}?\b(?:Inc\.?|LLC|Ltd\.?|Limited|GmbH|Corporation|Corp\.?|"
    r"Co\.?\s*,?\s*Ltd\.?|A\.?G\.?|S\.?A\.?|a\.s\.))\b",
    re.I,
)
SECTOR_CUT = re.compile(
    r"^(.{2,100}?\b(?:Therapeutics?|Biotherapeutics?|Biosciences?|"
    r"Biotech(?:nology)?|Pharmaceuticals?|Pharma|Biologics?|BioMed))\b",
    re.I,
)
ACADEMIC = re.compile(
    r"university|college|hospital|school of|institute|institut\b|academy|"
    r"medical center|medical centre|foundation|department of|laboratory of|"
    r"national center|national centre|ministry|clinic\b",
    re.I,
)
ORG_NOISE = re.compile(
    r"department|\bdept\b|research and development|research & development|laborator|"
    r"\bcenter\b|\bcentre\b|medical communications|therapeutic area|"
    r"strategy and innovation|manufacturing|clinical research|research group|"
    r"contract research|analytical research|process research|product research",
    re.I,
)
KNOWN_NON_NEW_OR_SERVICE = re.compile(
    r"pfizer|merck|abbvie|boehringer|chugai|roche|hoffmann|gilead|amgen|"
    r"regeneron|sanofi|moderna|bristol|astrazeneca|janssen|novartis|"
    r"eli lilly|takeda|astellas|bayer|gsk|glaxosmithkline|genentech|"
    r"wuxi|evotec|omniab|acrobiosystems|certara|nanotag|pinnacle research|"
    r"smobio|fairjourney|mosaic biosciences",
    re.I,
)
NOISE = re.compile(
    r"diagnostic|assay|biosimilar|manufacturing|production platform|"
    r"research reagent|review|position statement|comparison of|outcomes and impact|"
    r"practice in|workflow|biomarker|supplementary|case report|real-world|"
    r"meta-analysis|corrigendum|antibodies to watch|market|"
    r"veterinary|broiler|sensor|detection|COVID-19 test",
    re.I,
)
MODALITY = re.compile(
    r"bispecific|multispecific|nanobody|\bVHH\b|\bscFv\b|antibody|"
    r"immunocytokine|T[- ]cell engager|therapeutic protein",
    re.I,
)
DEVELOPMENT_ACTIVITY = re.compile(
    r"novel|engineer|develop|design|preclinical|first-in-human|phase [Ii1-3]|"
    r"clinical trial|therapeutic efficacy|antitumor|anti-tumor|candidate|"
    r"discovery|optimization|maturation|humanized|targeting|potent|IND-enabling",
    re.I,
)


def _company_from_affiliation(affiliation: str) -> str:
    if (
        not affiliation
        or ACADEMIC.search(affiliation)
        or ORG_NOISE.search(affiliation)
        or KNOWN_NON_NEW_OR_SERVICE.search(affiliation)
    ):
        return ""
    parts = [p.strip(" .") for p in re.split(r"[,;]", affiliation) if p.strip()]
    for index, part in enumerate(parts):
        if not COMPANY_WORD.search(part):
            continue
        candidate = f"{parts[index - 1]} {part}" if LEGAL_ONLY.match(part) and index else part
        cut = LEGAL_CUT.match(candidate) or SECTOR_CUT.match(candidate)
        if cut:
            candidate = cut.group(1)
        candidate = re.sub(r"\s+", " ", candidate).strip(" .,-")
        if (
            3 <= len(candidate) <= 100
            and not ACADEMIC.search(candidate)
            and not ORG_NOISE.search(candidate)
            and not KNOWN_NON_NEW_OR_SERVICE.search(candidate)
            and candidate.lower() not in {"bioscience", "biotech", "biotechnology", "pharma", "biologics"}
        ):
            return candidate
    return ""


def _affiliations(result: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for author in (result.get("authorList") or {}).get("author", []) or []:
        for detail in (author.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []) or []:
            value = detail.get("affiliation") or ""
            if value:
                found.append(value)
    first = result.get("authorString") or ""
    if first:
        found.append(first)
    return found


def _source_url(result: dict[str, Any]) -> str:
    if result.get("pmcid"):
        return f"https://europepmc.org/article/PMC/{result['pmcid']}"
    if result.get("pmid"):
        return f"https://europepmc.org/article/MED/{result['pmid']}"
    if result.get("doi"):
        return f"https://doi.org/{result['doi']}"
    return ""


def _search(session, term: str, start: str, end: str) -> list[dict[str, Any]]:
    query = f'FIRST_PDATE:[{start} TO {end}] AND TITLE_ABS:{term} AND (LANG:"eng" OR LANG:"en")'
    r = get_with_retry(
        session,
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={"query": query, "format": "json", "resultType": "core", "pageSize": 1000},
        timeout=(10, 60),
    )
    if r is None:
        return []
    return (r.json().get("resultList") or {}).get("result", []) or []


def fetch(days: int = 365, terms: list[str] | None = None) -> list[dict[str, Any]]:
    session = make_session("antibody-intent-research/1.1")
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()

    items: list[dict[str, Any]] = []
    seen_companies: set[str] = set()
    for term in terms or TERMS:
        for result in _search(session, term, start, end):
            title = (result.get("title") or "").strip()
            abstract = (result.get("abstractText") or "").strip()
            if (
                not title
                or NOISE.search(title)
                or not MODALITY.search(f"{title} {abstract}")
                or not DEVELOPMENT_ACTIVITY.search(title)
            ):
                continue
            url = _source_url(result)
            if not url:
                continue
            published = (
                result.get("firstPublicationDate")
                or result.get("electronicPublicationDate")
                or result.get("journalInfo", {}).get("printPublicationDate")
                or ""
            )[:10]
            for affiliation in _affiliations(result):
                company = _company_from_affiliation(affiliation)
                if not company:
                    continue
                key = company_root(company)
                dedupe_key = f"{key}|{url}"
                if not key or dedupe_key in seen_companies:
                    continue
                seen_companies.add(dedupe_key)
                items.append(
                    make_item(
                        url=url,
                        title=title,
                        content=f"{abstract[:600]} | affiliation: {affiliation[:300]}",
                        published_date=published,
                        seed_id=f"EPMC-{re.sub(chr(34), '', term)[:20]}",
                        query=term,
                        signal_type="scientific",
                        days=days,
                        known_company=company,
                    )
                )
                break  # one company per paper is enough evidence
    return items
