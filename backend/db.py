"""
Module: Database Layer (SQLite)
Handles case storage for the forensic analysis platform.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "cases.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            filename TEXT,
            fraud_score INTEGER,
            risk_tier TEXT,
            flags TEXT,
            llm_explanation TEXT,
            header_analysis TEXT,
            geo_trace TEXT,
            campaign_data TEXT,
            evidence_hash TEXT,
            raw_eml_hash TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_case(result, filename=None):
    """Save an analysis result as a new case. Returns the case_id."""
    conn = get_connection()
    case_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    conn.execute("""
        INSERT INTO cases (id, created_at, filename, fraud_score, risk_tier, flags,
                           llm_explanation, header_analysis, geo_trace, campaign_data,
                           evidence_hash, raw_eml_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        case_id,
        now,
        filename,
        result.get("fraud_score"),
        result.get("risk_tier"),
        json.dumps(result.get("flags", [])),
        result.get("llm_explanation"),
        json.dumps(result.get("header_analysis", {})),
        json.dumps(result.get("geo_trace", {})),
        json.dumps(result.get("campaign_data", {})),
        result.get("evidence_hash"),
        result.get("raw_eml_hash"),
    ))
    conn.commit()
    conn.close()
    return case_id


def get_case(case_id):
    """Retrieve a single case by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def get_all_cases():
    """Retrieve all cases, most recent first."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def delete_case(case_id):
    """Delete a case by ID."""
    conn = get_connection()
    conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
    conn.commit()
    conn.close()


def _row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict, parsing JSON fields."""
    d = dict(row)
    for key in ("flags", "header_analysis", "geo_trace", "campaign_data"):
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# Auto-initialize on import
init_db()
