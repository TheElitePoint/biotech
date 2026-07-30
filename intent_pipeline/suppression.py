"""Historical company suppression for daily non-repeating discovery runs."""

from __future__ import annotations

import csv
import re
from pathlib import Path

SUPPRESSION = (
    Path(__file__).resolve().parent.parent / "output" / "historical_suppression.csv"
)


def normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


_ROOT_SUFFIX = re.compile(
    r"(?:\bincorporated\b|\binc\b|\bllc\b|\bltd\b|\blimited\b|\bcorp(?:oration)?\b|"
    r"\bcompany\b|\bco\b|\bgmbh\b|\bplc\b|\bpty\b|\bpte\b|\bholdings?\b|\bgroup\b|"
    r"\btherapeutics?\b|\bbiotherapeutics?\b|\bbiosciences?\b|\bbiotechnolog(?:y|ies)\b|"
    r"\bbiotech\b|\bpharmaceuticals?\b|\bpharma\b|\bbiologics?\b|\bbiomed\b)\W*$",
    re.I,
)
_GEO_SUFFIX = re.compile(
    r"(?:\busa\b|\buk\b|\bchina\b|\bsouth korea\b|\bkorea\b|\bshanghai\b|"
    r"\bbeijing\b|\bchengdu\b|\bseoul\b|\bprague\b|\bjapan\b|\beurope\b)\W*$",
    re.I,
)


def company_root(value: str | None) -> str:
    text = re.sub(r"\([^)]*\)", " ", value or "")
    text = re.sub(r"https?://|www\.", "", text, flags=re.I)
    text = re.sub(r"\.(com|bio|ai|co|org|net|io)\b.*$", "", text, flags=re.I)
    previous = None
    while text != previous:
        previous = text
        text = _GEO_SUFFIX.sub("", text).strip(" .,-")
        text = _ROOT_SUFFIX.sub("", text).strip(" .,-")
    return normalize(text)


def load() -> set[str]:
    """Return all known company keys, names and domains in normalized form."""
    if not SUPPRESSION.exists():
        return set()
    keys: set[str] = set()
    with SUPPRESSION.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            for field in ("company_key", "normalized_name", "domain", "canonical_company"):
                raw = row.get(field)
                for value in (normalize(raw), company_root(raw)):
                    if value:
                        keys.add(value)
    return keys


def contains(
    known: set[str],
    *,
    key: str | None = None,
    name: str | None = None,
    domain: str | None = None,
) -> bool:
    candidates = {
        normalize(key),
        normalize(name),
        normalize(domain),
        company_root(key),
        company_root(name),
        company_root(domain),
    }
    candidates.discard("")
    return bool(candidates & known)
