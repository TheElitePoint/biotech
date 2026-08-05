"""Fresh daily intent discovery using Bing News RSS as the no-key fallback.

The output is a research queue, not an auto-approved sales list. Every row has a
current source URL and passes automated modality/exclusion checks. Ownership,
program and bottleneck gaps remain explicit for human verification.
"""

from __future__ import annotations

import csv
import html
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse

import requests

from intent_pipeline.gates import Verdict, route
from intent_pipeline.signals import Signal, canonical_name, dedupe, normalize
from intent_pipeline.suppression import contains as is_suppressed
from intent_pipeline.suppression import load as load_suppression

OUT = Path(__file__).resolve().parent / "output"
RAW = OUT / "daily_raw_signals.csv"
CANDIDATES = OUT / "daily_company_candidates.csv"

WINDOW_DAYS = 365

QUERIES = [
    ('"antibody" biotech raises funding', "capital"),
    ('"bispecific antibody" financing biotech', "capital"),
    ('"multispecific antibody" funding company', "capital"),
    ('"nanobody" funding therapeutic company', "capital"),
    ('"therapeutic protein" biotech funding', "capital"),
    ('"protein engineering" therapeutics funding', "capital"),
    ('"antibody pipeline" Series A biotech', "capital"),
    ('"antibody program" seed financing biotech', "capital"),
    ('"development candidate" antibody company', "milestone"),
    ('"candidate nomination" antibody biotech', "milestone"),
    ('"IND-enabling" antibody company', "milestone"),
    ('"IND application" bispecific antibody company', "milestone"),
    ('"preclinical" bispecific antibody company', "program"),
    ('"lead optimization" antibody biotech', "program"),
    ('"pipeline expansion" antibody company', "program"),
    ('"new antibody program" biotech', "program"),
    ('"antibody-drug conjugate" preclinical company', "program"),
    ('"bispecific ADC" company pipeline', "program"),
    ('"T-cell engager" preclinical biotech', "program"),
    ('"antibody fragment" therapeutic company', "program"),
    ('"VHH" therapeutic biotech company', "program"),
    ('"scFv" therapeutic company', "program"),
    ('"Fc fusion" therapeutic biotech', "program"),
    ('"fusion protein" preclinical biotech', "program"),
    ('"immunocytokine" biotech company', "program"),
    ('"engineered protein therapeutic" company', "program"),
    ('"affinity maturation" therapeutic company', "scientific"),
    ('"antibody humanization" therapeutic company', "scientific"),
    ('"antibody developability" biotech company', "scientific"),
    ('"protein stability" therapeutic biotech', "scientific"),
    ('"antibody specificity" biotech program', "scientific"),
    ('"membrane protein" antibody company', "scientific"),
    ('"GPCR antibody" therapeutic company', "scientific"),
    ('"antibody discovery" biotech partnership', "execution"),
    ('"protein engineering" biotech partnership', "execution"),
    ('"wet-lab validation" antibody biotech', "execution"),
    ('"antibody discovery" hiring biotech', "hiring"),
    ('"protein engineering" hiring therapeutics', "hiring"),
    ('"antibody engineering" scientist biotech', "hiring"),
    ('"developability" scientist antibody company', "hiring"),
]

BAD_TITLE = re.compile(
    r"market size|market report|forecast|review article|conference agenda|"
    r"webinar|podcast|supplier|services|CRO\b|CDMO\b|diagnostic|assay kit|"
    r"research use only|stock to watch|best stocks|investor alert",
    re.I,
)

EXPLICIT_MODALITY = re.compile(
    r"monoclonal antibod|bispecific|multispecific|trispecific|nanobod|"
    r"\bVHH\b|\bscFv\b|antibody fragment|therapeutic antibod|"
    r"antibody-drug conjugate|\bADC\b|T-cell engager|Fc fusion|"
    r"fusion protein|immunocytokine|engineered protein|therapeutic protein",
    re.I,
)

EARLY_STAGE = re.compile(
    r"discovery|lead optimization|candidate nomination|development candidate|"
    r"preclinical|IND-enabling|IND application|pipeline expansion|new program|"
    r"Series A|Series B|seed financ|raises|funding",
    re.I,
)


def direct_url(link: str) -> str:
    parsed = urlparse(link)
    target = parse_qs(parsed.query).get("url", [""])[0]
    return target or link


def rss_items(session: requests.Session, query: str, signal_type: str) -> list[dict[str, Any]]:
    url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
    response = session.get(url, timeout=(10, 30))
    response.raise_for_status()
    root = ET.fromstring(response.content)
    out: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        title = html.unescape(item.findtext("title") or "").strip()
        description = html.unescape(item.findtext("description") or "").strip()
        link = direct_url(item.findtext("link") or "")
        published = (item.findtext("pubDate") or "").strip()
        if not title or not link or BAD_TITLE.search(title):
            continue
        out.append(
            {
                "url": link,
                "title": title,
                "content": re.sub(r"<[^>]+>", " ", description),
                "published_date": published,
                "_seed_id": f"RSS-{signal_type.upper()}",
                "_query": query,
                "_signal_type": signal_type,
                "_date_window_days": WINDOW_DAYS,
            }
        )
    return out


def fetch_text(session: requests.Session, url: str) -> str:
    try:
        response = session.get(url, timeout=(8, 20), allow_redirects=True)
        if response.status_code >= 400 or "text/html" not in response.headers.get(
            "content-type", ""
        ):
            return ""
        text = response.text
        text = re.sub(r"(?is)<(script|style|svg|noscript).*?>.*?</\1>", " ", text)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()[:20000]
    except requests.RequestException:
        return ""


def signal_row(sig: Signal, verdict: Verdict) -> dict[str, Any]:
    return {
        **sig.as_row(),
        "raw_text": "",
        "decision": verdict.decision,
        "priority": verdict.priority,
        "score": verdict.score,
        "exclusion_reason": verdict.exclusion_reason,
        "failed_gates": "; ".join(verdict.failed_gates),
        "modality": "; ".join(
            verdict.evidence.get("modality_approve", [])
            + verdict.evidence.get("modality_conditional", [])
        ),
        "asset_stage": "; ".join(verdict.evidence.get("stages", [])),
        "bottlenecks": "; ".join(verdict.evidence.get("bottlenecks", [])),
    }


def candidate_rows(records: list[tuple[Signal, Verdict]]) -> list[dict[str, Any]]:
    known = load_suppression()
    grouped: dict[str, list[tuple[Signal, Verdict]]] = defaultdict(list)
    for sig, verdict in records:
        name = sig.company_candidate or ""
        domain = sig.company_domain or ""
        key = (domain or canonical_name(name).lower()).strip()
        if not key or is_suppressed(known, key=key, name=name, domain=domain):
            continue
        if verdict.exclusion_reason or not EXPLICIT_MODALITY.search(
            f"{sig.title} {sig.snippet} {sig.raw_text}"
        ):
            continue
        if not EARLY_STAGE.search(f"{sig.title} {sig.snippet} {sig.raw_text}"):
            continue
        grouped[key].append((sig, verdict))

    rows: list[dict[str, Any]] = []
    for key, group in grouped.items():
        group.sort(key=lambda item: item[1].score, reverse=True)
        sig, verdict = group[0]
        evidence_text = f"{sig.title} {sig.snippet} {sig.raw_text}"
        modality = (
            verdict.evidence.get("modality_approve", [])
            + verdict.evidence.get("modality_conditional", [])
        )
        stages = verdict.evidence.get("stages", [])
        bottlenecks = verdict.evidence.get("bottlenecks", [])
        verified_domain = bool(sig.company_domain)
        ownership = "Company-owned source domain" if verified_domain else "Unverified from announcement"
        missing = (
            "Confirm exact owned asset/program, current company website, and "
            "company-source evidence; then identify one supported bottleneck."
        )
        if verified_domain and stages and bottlenecks:
            missing = (
                "Confirm asset ownership and validate that the stated bottleneck "
                "belongs to the named therapeutic program."
            )

        scientific_fit = min(25, verdict.breakdown.get("scientific_fit", 0))
        intent_score = min(25, verdict.breakdown.get("intent", 0))
        clarity = min(20, verdict.breakdown.get("project_clarity", 0))
        budget = min(15, verdict.breakdown.get("budget", 0))
        confidence = min(5, verdict.breakdown.get("data_confidence", 0))
        quality_score = scientific_fit + intent_score + clarity + budget + confidence

        rows.append(
            {
                "Original Dataset Priority": "New",
                "Corrected Status": "Review",
                "Current Company Name": sig.company_candidate or "",
                "Company Website": f"https://{sig.company_domain}" if verified_domain else "",
                "Headquarters": "",
                "Company Type / Ownership": ownership,
                "Therapeutic Asset or Program": "",
                "Biological Target": "",
                "Disease / Indication": "",
                "Confirmed Modality": "; ".join(dict.fromkeys(modality)),
                "Current Program Stage": "; ".join(stages),
                "Trigger Type": sig.signal_type,
                "Signal Date": sig.signal_date or "",
                "Signal Summary": sig.title,
                "Original Trigger Source URL": sig.source_url,
                "Company / Pipeline Source URL": (
                    sig.source_url if verified_domain else ""
                ),
                "Asset Ownership Evidence": (
                    sig.resolution_note if verified_domain else ""
                ),
                "Scientific / Development Requirement": "; ".join(bottlenecks),
                "Evidence for Requirement": (
                    sig.title if bottlenecks else ""
                ),
                "Direct Project Hypothesis": "",
                "Proposed Pilot / Project Type": "",
                "Budget / Purchase-Likelihood Evidence": (
                    "Current funding or capital event"
                    if sig.signal_type == "capital"
                    else "Current program, milestone, hiring, or scientific activity"
                ),
                "Validation Capacity": "",
                "Competitor / Service-Provider Check": "Passed automated hard-exclusion screen",
                "Hard Exclusion Result": "Pass - no automated exclusion matched",
                "Scientific Fit (25)": scientific_fit,
                "Intent & Timing (25)": intent_score,
                "Project Clarity (20)": clarity,
                "Budget (15)": budget,
                "Data Confidence (5)": confidence,
                "Total Score": quality_score,
                "Final Decision Reason": (
                    "Evidence-backed current intent candidate; remains Review until "
                    "owned asset and company-source program evidence are confirmed."
                ),
                "Missing Fact / Next Verification": missing,
                "Verification Date": date.today().isoformat(),
                "Research Notes": (
                    f"Discovered live via Bing News RSS query: {sig.query}. "
                    f"Source domain: {sig.source_domain}."
                ),
                "_company_key": key,
                "_evidence_count": len({item[0].source_url for item in group}),
                "_raw_evidence_text": evidence_text[:500],
            }
        )

    rows.sort(
        key=lambda row: (
            row["Company Website"] == "",
            -int(row["Total Score"]),
            -int(row["_evidence_count"]),
            row["Current Company Name"],
        )
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (compatible; antibody-intent-research/1.0)"
    )
    items: list[dict[str, Any]] = []
    for index, (query, signal_type) in enumerate(QUERIES, 1):
        try:
            found = rss_items(session, query, signal_type)
            items.extend(found)
            print(f"{index:02}/{len(QUERIES)} {signal_type:10} {len(found):2} {query}")
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"{index:02}/{len(QUERIES)} failed: {exc}")
        time.sleep(0.1)

    signals = dedupe([normalize(item) for item in items])
    first = [(sig, route(sig)) for sig in signals]
    fetchable = [
        sig
        for sig, verdict in first
        if sig.company_candidate
        and not verdict.exclusion_reason
        and EXPLICIT_MODALITY.search(f"{sig.title} {sig.snippet}")
        and EARLY_STAGE.search(f"{sig.title} {sig.snippet}")
    ][:250]
    print(f"Fetching full text for {len(fetchable)} first-pass candidates...")
    for index, sig in enumerate(fetchable, 1):
        text = fetch_text(session, sig.source_url)
        if text:
            sig.raw_text = text
        if index % 25 == 0:
            print(f"  fetched {index}/{len(fetchable)}")

    records = [(sig, route(sig)) for sig in signals]
    rows = candidate_rows(records)
    write_csv(RAW, [signal_row(sig, verdict) for sig, verdict in records])
    write_csv(CANDIDATES, rows)
    print(f"{len(signals)} unique live signals")
    print(f"{len(rows)} non-repeating evidence-backed candidates -> {CANDIDATES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
