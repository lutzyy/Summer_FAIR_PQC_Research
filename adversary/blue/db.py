"""Postgres helpers for Blue Agent tables. Mirrors adversary/brain/db.py patterns."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_BLUE = Path(__file__).resolve().parent
_BRAIN = _BLUE.parent / "brain"
if str(_BLUE) not in sys.path:
    sys.path.insert(0, str(_BLUE))

# Prefer blue/.env, then brain/.env (same Postgres)
load_dotenv(_BLUE / ".env")
load_dotenv(_BRAIN / ".env")

from models import BlueJudgment, RuleGrade, Verdict  # noqa: E402


def _dsn() -> str:
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD is not set; add it to adversary/blue/.env or adversary/brain/.env"
        )
    host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "postgres")
    user = os.environ.get("POSTGRES_USER", "postgres")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def _connect():
    import psycopg

    return psycopg.connect(_dsn())


def init_schema(schema_path: Path | None = None) -> None:
    """Apply blue schema.sql (IF NOT EXISTS). Does not alter runs."""
    path = schema_path or (_BLUE / "schema.sql")
    sql = path.read_text()
    with _connect() as conn:
        conn.execute(sql)
        conn.commit()


def fetch_run(run_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT run_id, timestamp, target, crypto_detected,
                   attack_name, attack_params, outcome_notes
            FROM runs WHERE run_id = %s
            """,
            (run_id,),
        ).fetchone()
    if not row:
        return None
    keys = [
        "run_id",
        "timestamp",
        "target",
        "crypto_detected",
        "attack_name",
        "attack_params",
        "outcome_notes",
    ]
    data = dict(zip(keys, row))
    if isinstance(data.get("attack_params"), str):
        data["attack_params"] = json.loads(data["attack_params"])
    return data


def fetch_all_runs() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT run_id, timestamp, target, crypto_detected,
                   attack_name, attack_params, outcome_notes
            FROM runs ORDER BY timestamp
            """
        ).fetchall()
    out = []
    keys = [
        "run_id",
        "timestamp",
        "target",
        "crypto_detected",
        "attack_name",
        "attack_params",
        "outcome_notes",
    ]
    for row in rows:
        data = dict(zip(keys, row))
        if isinstance(data.get("attack_params"), str):
            data["attack_params"] = json.loads(data["attack_params"])
        out.append(data)
    return out


def count_runs() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) FROM runs").fetchone()
    return int(row[0]) if row else 0


def save_judgment(j: BlueJudgment) -> None:
    """Insert a Blue Agent judgment. Never updates rule_based_grades."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO blue_agent_judgments
            (judgment_id, run_id, verdict, confidence, rationale,
             evidence_cited, evidence_sources_used, model, prompt_version,
             rubric_version, timestamp, langfuse_trace_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                j.judgment_id,
                j.run_id,
                j.verdict.value if isinstance(j.verdict, Verdict) else j.verdict,
                j.confidence,
                j.rationale,
                json.dumps([c.model_dump() for c in j.evidence_cited]),
                json.dumps(j.evidence_sources_used),
                j.model,
                j.prompt_version,
                j.rubric_version,
                j.timestamp,
                j.langfuse_trace_id,
            ),
        )
        conn.commit()


def save_rule_grade(g: RuleGrade) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO rule_based_grades
            (grade_id, run_id, verdict, rationale, grader_version, timestamp)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (
                g.grade_id,
                g.run_id,
                g.verdict.value if isinstance(g.verdict, Verdict) else g.verdict,
                g.rationale,
                g.grader_version,
                g.timestamp,
            ),
        )
        conn.commit()


def fetch_latest_judgment(run_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT judgment_id, run_id, verdict, confidence, rationale,
                   evidence_cited, evidence_sources_used, model, prompt_version,
                   rubric_version, timestamp
            FROM blue_agent_judgments
            WHERE run_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()
    if not row:
        return None
    keys = [
        "judgment_id",
        "run_id",
        "verdict",
        "confidence",
        "rationale",
        "evidence_cited",
        "evidence_sources_used",
        "model",
        "prompt_version",
        "rubric_version",
        "timestamp",
    ]
    return dict(zip(keys, row))


def fetch_latest_rule_grade(run_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT grade_id, run_id, verdict, rationale, grader_version, timestamp
            FROM rule_based_grades
            WHERE run_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()
    if not row:
        return None
    keys = [
        "grade_id",
        "run_id",
        "verdict",
        "rationale",
        "grader_version",
        "timestamp",
    ]
    return dict(zip(keys, row))
