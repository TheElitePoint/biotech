"""SQLite store for the Phase 1 pipeline (brief §4, §17).

Design rules taken straight from the brief's non-negotiables:

  * `raw_signals` is immutable — inserts only, never updated or deleted. The
    original source payload is kept verbatim in `raw_json` alongside a
    `content_hash` so a re-fetch that changed nothing is not stored twice.
  * Every normalized fact carries its evidence (`evidence_spans` JSON with
    character offsets) and a confidence; unknown values stay NULL rather than
    being guessed.
  * Model/prompt versions are stored per decision so any decision can be
    reproduced from stored evidence.

Excel remains the human-facing export; this database is the system of record.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pipeline.db"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Layer 2: immutable raw evidence -------------------------------------------
CREATE TABLE IF NOT EXISTS raw_signals (
    signal_id        TEXT PRIMARY KEY,
    source_type      TEXT NOT NULL,
    source_item_id   TEXT,
    source_url       TEXT,
    query_id         TEXT,
    query_text       TEXT,
    published_at     TEXT,
    collected_at     TEXT NOT NULL,
    title            TEXT,
    raw_text         TEXT,
    raw_json         TEXT,
    content_hash     TEXT NOT NULL,
    actor_run_id     TEXT,
    ingestion_status TEXT NOT NULL DEFAULT 'ok',
    ingestion_error  TEXT,
    UNIQUE (source_type, content_hash)
);
CREATE INDEX IF NOT EXISTS ix_raw_source     ON raw_signals(source_type);
CREATE INDEX IF NOT EXISTS ix_raw_collected  ON raw_signals(collected_at);

-- Layer 3: normalization ----------------------------------------------------
CREATE TABLE IF NOT EXISTS normalized_signals (
    signal_id             TEXT PRIMARY KEY REFERENCES raw_signals(signal_id),
    company_candidate     TEXT,
    organization_mentions TEXT,
    target                TEXT,
    disease               TEXT,
    modality              TEXT,
    antibody_format       TEXT,
    asset_name            TEXT,
    asset_stage           TEXT,
    scientific_problem    TEXT,
    signal_type           TEXT,
    signal_date           TEXT,
    evidence_spans        TEXT,
    field_confidence      TEXT,
    normalization_version TEXT NOT NULL
);

-- Layer 4: company truth ----------------------------------------------------
CREATE TABLE IF NOT EXISTS company_master (
    company_id               TEXT PRIMARY KEY,
    canonical_name           TEXT NOT NULL,
    normalized_domain        TEXT,
    legal_name               TEXT,
    country                  TEXT,
    company_type             TEXT,
    private_public           TEXT,
    employees                INTEGER,
    funding_stage            TEXT,
    last_funding_date        TEXT,
    last_funding_amount      TEXT,
    therapeutic_owner_status TEXT,
    competitor_status        TEXT,
    company_status           TEXT,
    created_at               TEXT NOT NULL,
    updated_at               TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_company_domain ON company_master(normalized_domain);

CREATE TABLE IF NOT EXISTS company_aliases (
    company_id TEXT NOT NULL REFERENCES company_master(company_id),
    alias      TEXT NOT NULL,
    alias_type TEXT,
    PRIMARY KEY (company_id, alias)
);

CREATE TABLE IF NOT EXISTS company_signals (
    company_id TEXT NOT NULL REFERENCES company_master(company_id),
    signal_id  TEXT NOT NULL REFERENCES raw_signals(signal_id),
    PRIMARY KEY (company_id, signal_id)
);

-- Named programs, so intent can stack at company-program level (brief §5) ----
CREATE TABLE IF NOT EXISTS programs (
    program_id    TEXT PRIMARY KEY,
    company_id    TEXT NOT NULL REFERENCES company_master(company_id),
    program_name  TEXT,
    target        TEXT,
    disease       TEXT,
    modality      TEXT,
    asset_stage   TEXT,
    bottleneck    TEXT,
    bottleneck_basis TEXT,        -- 'explicit' | 'inferred'
    evidence_url  TEXT,
    evidence_text TEXT,
    confidence    INTEGER,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_programs_company ON programs(company_id);

CREATE TABLE IF NOT EXISTS intent_events (
    intent_event_id TEXT PRIMARY KEY,
    company_id      TEXT NOT NULL REFERENCES company_master(company_id),
    signal_id       TEXT REFERENCES raw_signals(signal_id),
    intent_type     TEXT NOT NULL,
    event_date      TEXT,
    strength        REAL,
    recency_score   REAL,
    program_name    TEXT,
    evidence_text   TEXT,
    source_url      TEXT,
    confidence      INTEGER
);
CREATE INDEX IF NOT EXISTS ix_intent_company ON intent_events(company_id);

-- Decisions, reproducible from stored evidence (brief §17.9, §17.10) --------
CREATE TABLE IF NOT EXISTS qualification_decisions (
    decision_id             TEXT PRIMARY KEY,
    company_id              TEXT NOT NULL REFERENCES company_master(company_id),
    decision                TEXT NOT NULL,
    passed_gates            TEXT,
    failed_gates            TEXT,
    unresolved_gate         TEXT,
    unresolved_question     TEXT,
    next_verification_action TEXT,
    score_total             INTEGER,
    score_breakdown         TEXT,
    project_hypothesis      TEXT,
    exclusion_category      TEXT,
    exclusion_reason        TEXT,
    decision_confidence     INTEGER,
    model_version           TEXT,
    prompt_version          TEXT,
    raw_model_response      TEXT,
    created_at              TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_decision_company ON qualification_decisions(company_id);

-- Source/query governance (brief §9, §14) -----------------------------------
CREATE TABLE IF NOT EXISTS query_registry (
    query_id       TEXT PRIMARY KEY,
    source_type    TEXT NOT NULL,
    query_family   TEXT,
    query_text     TEXT NOT NULL,
    negative_terms TEXT,
    geography      TEXT,
    date_window    INTEGER,
    max_results    INTEGER,
    cadence        TEXT,
    status         TEXT NOT NULL DEFAULT 'DRAFT',
    version        INTEGER NOT NULL DEFAULT 1,
    owner          TEXT,
    created_at     TEXT NOT NULL,
    last_tested_at TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id            TEXT PRIMARY KEY,
    started_at        TEXT NOT NULL,
    finished_at       TEXT,
    sources           TEXT,
    raw_count         INTEGER,
    normalized_count  INTEGER,
    company_count     INTEGER,
    approved_count    INTEGER,
    review_count      INTEGER,
    rejected_count    INTEGER,
    notes             TEXT
);

CREATE TABLE IF NOT EXISTS review_history (
    review_id   TEXT PRIMARY KEY,
    company_id  TEXT NOT NULL REFERENCES company_master(company_id),
    reviewer    TEXT,
    decision    TEXT,
    reason      TEXT,
    reviewed_at TEXT NOT NULL
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def content_hash(*parts: Any) -> str:
    blob = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()


def insert_raw_signal(conn: sqlite3.Connection, record: dict[str, Any]) -> str | None:
    """Insert one immutable raw signal. Returns signal_id, or None if the exact
    same content was already stored (dedupe on content_hash, brief §10).
    """
    digest = record.get("content_hash") or content_hash(
        record.get("source_url"), record.get("title"), record.get("raw_text")
    )
    signal_id = record.get("signal_id") or content_hash(record.get("source_type"), digest)[:32]
    try:
        conn.execute(
            """
            INSERT INTO raw_signals (
                signal_id, source_type, source_item_id, source_url, query_id, query_text,
                published_at, collected_at, title, raw_text, raw_json, content_hash,
                actor_run_id, ingestion_status, ingestion_error
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                signal_id,
                record.get("source_type"),
                record.get("source_item_id"),
                record.get("source_url"),
                record.get("query_id"),
                record.get("query_text"),
                record.get("published_at"),
                record.get("collected_at") or now(),
                record.get("title"),
                record.get("raw_text"),
                json.dumps(record.get("source_metadata") or {}, ensure_ascii=False),
                digest,
                record.get("actor_run_id"),
                record.get("ingestion_status", "ok"),
                record.get("ingestion_error"),
            ),
        )
        return signal_id
    except sqlite3.IntegrityError:
        return None  # identical content already stored — not an error


def upsert_company(conn: sqlite3.Connection, company: dict[str, Any]) -> str:
    company_id = company.get("company_id") or content_hash(
        company.get("normalized_domain") or company.get("canonical_name", "").lower()
    )[:32]
    existing = conn.execute(
        "SELECT company_id, created_at FROM company_master WHERE company_id = ?", (company_id,)
    ).fetchone()
    stamp = now()
    if existing:
        conn.execute(
            """
            UPDATE company_master SET
                canonical_name = COALESCE(?, canonical_name),
                normalized_domain = COALESCE(?, normalized_domain),
                employees = COALESCE(?, employees),
                therapeutic_owner_status = COALESCE(?, therapeutic_owner_status),
                competitor_status = COALESCE(?, competitor_status),
                company_status = COALESCE(?, company_status),
                updated_at = ?
            WHERE company_id = ?
            """,
            (
                company.get("canonical_name"),
                company.get("normalized_domain"),
                company.get("employees"),
                company.get("therapeutic_owner_status"),
                company.get("competitor_status"),
                company.get("company_status"),
                stamp,
                company_id,
            ),
        )
    else:
        conn.execute(
            """
            INSERT INTO company_master (
                company_id, canonical_name, normalized_domain, legal_name, country,
                company_type, private_public, employees, funding_stage, last_funding_date,
                last_funding_amount, therapeutic_owner_status, competitor_status,
                company_status, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                company_id,
                company.get("canonical_name"),
                company.get("normalized_domain"),
                company.get("legal_name"),
                company.get("country"),
                company.get("company_type"),
                company.get("private_public"),
                company.get("employees"),
                company.get("funding_stage"),
                company.get("last_funding_date"),
                company.get("last_funding_amount"),
                company.get("therapeutic_owner_status"),
                company.get("competitor_status"),
                company.get("company_status"),
                stamp,
                stamp,
            ),
        )
    return company_id


def start_run(conn: sqlite3.Connection, sources: list[str]) -> str:
    run_id = content_hash(now(), ",".join(sources))[:16]
    conn.execute(
        "INSERT INTO pipeline_runs (run_id, started_at, sources) VALUES (?,?,?)",
        (run_id, now(), ",".join(sources)),
    )
    conn.commit()
    return run_id


def finish_run(conn: sqlite3.Connection, run_id: str, **counts: Any) -> None:
    conn.execute(
        """
        UPDATE pipeline_runs SET finished_at = ?, raw_count = ?, normalized_count = ?,
            company_count = ?, approved_count = ?, review_count = ?, rejected_count = ?,
            notes = ?
        WHERE run_id = ?
        """,
        (
            now(),
            counts.get("raw_count"),
            counts.get("normalized_count"),
            counts.get("company_count"),
            counts.get("approved_count"),
            counts.get("review_count"),
            counts.get("rejected_count"),
            counts.get("notes"),
            run_id,
        ),
    )
    conn.commit()
