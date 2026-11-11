"""Pydantic models for Blue Agent judgments (separate from red-team RunRecord)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    INCONCLUSIVE = "inconclusive"


class EvidenceCitation(BaseModel):
    source: str
    lines: list[str] = Field(default_factory=list)
    note: str = ""


class BlueJudgment(BaseModel):
    """Structured Blue Agent output — stored in blue_agent_judgments."""

    judgment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    evidence_cited: list[EvidenceCitation] = Field(default_factory=list)
    evidence_sources_used: list[str] = Field(default_factory=list)
    model: str
    prompt_version: str
    rubric_version: str = "v1"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    langfuse_trace_id: str | None = None


class RuleGrade(BaseModel):
    grade_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    verdict: Verdict
    rationale: str
    grader_version: str = "provisional-v1"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EvidenceBundle(BaseModel):
    """Gathered evidence for one run; collectors fill fields independently."""

    run_id: str
    run_record: dict[str, Any] = Field(default_factory=dict)
    tool_output: dict[str, Any] = Field(default_factory=dict)
    server_logs: dict[str, Any] = Field(default_factory=dict)
    sensor_logs: dict[str, Any] = Field(default_factory=dict)
    crypto_config: dict[str, Any] = Field(default_factory=dict)
    attack_objective: dict[str, Any] = Field(default_factory=dict)
    sources_available: list[str] = Field(default_factory=list)
    sources_enabled: list[str] = Field(default_factory=list)
