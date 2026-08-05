"""PubMed source adapter (NCBI E-utilities). Free; no key required, though an
NCBI API key would raise the rate limit from 3/sec to 10/sec if this ever
needs to scale — not needed at current query volume.

esearch finds PMIDs inside a date window computed from *today*; efetch pulls
title/abstract/affiliation XML for those PMIDs. Company resolution reuses the
same affiliation-parsing rules as the Europe PMC adapter so a company found
via either source dedupes to the same key downstream.
"""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Any

from ..suppression import company_root
from .base import get_with_retry, make_item, make_session
from .europepmc import DEVELOPMENT_ACTIVITY, MODALITY, NOISE, _company_from_affiliation

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

TERMS = [
    "antibody affinity maturation",
    "de novo antibody design",
    "antibody humanization",
    "antibody developability",
    "membrane protein antibody target",
    "bispecific antibody preclinical",
    "antibody off-target specificity",
    "antibody epitope mapping",
    "secreted protein antibody target",
    "nanobody VHH therapeutic",
]


def _esearch(session, term: str, mindate: str, maxdate: str, retmax: int = 200) -> list[str]:
    params = {
        "db": "pubmed",
        "term": f"{term}[tiab]",
        "datetype": "pdat",
        "mindate": mindate,
        "maxdate": maxdate,
        "retmax": retmax,
        "retmode": "json",
    }
    r = get_with_retry(session, ESEARCH, params=params, timeout=(10, 30))
    if r is None:
        return []
    return r.json().get("esearchresult", {}).get("idlist", [])


def _efetch(session, pmids: list[str]) -> list[dict[str, Any]]:
    if not pmids:
        return []
    out = []
    for i in range(0, len(pmids), 100):
        batch = pmids[i : i + 100]
        r = get_with_retry(
            session, EFETCH,
            params={"db": "pubmed", "id": ",".join(batch), "rettype": "abstract", "retmode": "xml"},
            timeout=(10, 60),
        )
        if r is None:
            continue
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError:
            continue
        for article in root.findall(".//PubmedArticle"):
            out.append(_parse_article(article))
        time.sleep(0.34)  # stay under the 3 req/sec unauthenticated cap
    return out


def _parse_article(article: ET.Element) -> dict[str, Any]:
    pmid = article.findtext(".//PMID") or ""
    title = "".join(article.find(".//ArticleTitle").itertext()) if article.find(".//ArticleTitle") is not None else ""
    abstract_parts = [
        "".join(el.itertext()) for el in article.findall(".//AbstractText")
    ]
    abstract = " ".join(abstract_parts)

    year = article.findtext(".//Article/Journal/JournalIssue/PubDate/Year") or ""
    month = article.findtext(".//Article/Journal/JournalIssue/PubDate/Month") or "01"
    day = article.findtext(".//Article/Journal/JournalIssue/PubDate/Day") or "01"
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
    }
    month = month_map.get(month, month if month.isdigit() else "01")
    published = f"{year}-{month.zfill(2)}-{day.zfill(2)}" if year else ""

    affiliations = [
        "".join(el.itertext()) for el in article.findall(".//AffiliationInfo/Affiliation")
    ]

    return {"pmid": pmid, "title": title.strip(), "abstract": abstract.strip(),
            "published": published, "affiliations": affiliations}


def fetch(days: int = 365, terms: list[str] | None = None) -> list[dict[str, Any]]:
    session = make_session("antibody-intent-research/1.1 (mailto:research@example.invalid)")
    maxdate = date.today().strftime("%Y/%m/%d")
    mindate = (date.today() - timedelta(days=days)).strftime("%Y/%m/%d")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for term in terms or TERMS:
        pmids = _esearch(session, term, mindate, maxdate)
        for article in _efetch(session, pmids):
            title, abstract = article["title"], article["abstract"]
            if (
                not title
                or NOISE.search(title)
                or not MODALITY.search(f"{title} {abstract}")
                or not DEVELOPMENT_ACTIVITY.search(title)
            ):
                continue
            for affiliation in article["affiliations"]:
                company = _company_from_affiliation(affiliation)
                if not company:
                    continue
                key = company_root(company)
                dedupe_key = f"{key}|{article['pmid']}"
                if not key or dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                items.append(
                    make_item(
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/",
                        title=title,
                        content=f"{abstract[:600]} | affiliation: {affiliation[:300]}",
                        published_date=article["published"],
                        seed_id=f"PUBMED-{re.sub(r'[^a-z0-9]+', '-', term.lower()).strip('-')}",
                        query=term,
                        signal_type="scientific",
                        days=days,
                        known_company=company,
                    )
                )
                break
        time.sleep(0.34)
    return items
