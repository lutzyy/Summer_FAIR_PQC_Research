"""Blue-only: offline heuristic judge (no vLLM / Docker)."""
from __future__ import annotations

import pytest

from agent import judge_run
from models import BlueJudgment, Verdict


@pytest.mark.offline
def test_heuristic_judgment_schema(sample_run):
    j = judge_run(sample_run, force_heuristic=True)
    assert isinstance(j, BlueJudgment)
    assert j.run_id == sample_run["run_id"]
    assert j.verdict in Verdict
    assert 0.0 <= j.confidence <= 1.0
    assert j.rationale
    assert j.evidence_cited
    assert j.model.startswith("heuristic")
    assert j.prompt_version
    assert j.rubric_version == "v1"


@pytest.mark.offline
def test_heuristic_matches_gold_on_fixtures(sample_runs, gold_labels):
    for run in sample_runs:
        j = judge_run(run, force_heuristic=True)
        assert j.verdict.value == gold_labels[run["run_id"]], run["run_id"]


@pytest.mark.offline
def test_ablation_tool_output_only_still_judges(sample_run):
    j = judge_run(
        sample_run,
        enabled_sources=["tool_output", "attack_objective"],
        force_heuristic=True,
    )
    assert j.verdict == Verdict.SUCCESS
    assert "tool_output" in j.evidence_sources_used


@pytest.mark.offline
def test_never_mutates_input_run(sample_run):
    original = dict(sample_run)
    judge_run(sample_run, force_heuristic=True)
    assert sample_run == original
