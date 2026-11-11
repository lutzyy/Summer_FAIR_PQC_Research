"""Blue-only: provisional rule grader verdicts on fixtures."""
from __future__ import annotations

import pytest

from rule_grader import GRADER_VERSION, grade_run


@pytest.mark.offline
@pytest.mark.parametrize(
    "run_id,expected",
    [
        ("fixture-tls-ok", "success"),
        ("fixture-tls-fail", "failure"),
        ("fixture-tls-pqc", "success"),
        ("fixture-replay-ok", "success"),
        ("fixture-syn-ok", "success"),
        ("fixture-syn-fail", "failure"),
    ],
)
def test_rule_grader_fixture_verdicts(sample_runs, run_id, expected):
    run = next(r for r in sample_runs if r["run_id"] == run_id)
    grade = grade_run(run)
    assert grade.verdict.value == expected
    assert grade.grader_version == GRADER_VERSION
    assert grade.run_id == run_id
    assert grade.rationale


@pytest.mark.offline
def test_rule_grader_unknown_attack_inconclusive():
    grade = grade_run(
        {
            "run_id": "x",
            "attack_name": "future_quantum_decrypt",
            "outcome_notes": "maybe?",
            "crypto_detected": None,
        }
    )
    assert grade.verdict.value == "inconclusive"
