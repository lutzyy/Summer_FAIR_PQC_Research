"""Blue-only: R1 metric helpers and eval entrypoint on fixtures."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.metrics import (
    agreement_rate,
    cohens_kappa,
    confusion_matrix,
    consistency_flip_rate,
    label_reliability_decision,
)
from evaluation.run_eval import evaluate


@pytest.mark.offline
def test_agreement_kappa_perfect():
    a = ["success", "failure", "inconclusive"]
    b = list(a)
    assert agreement_rate(a, b) == 1.0
    assert cohens_kappa(a, b) == 1.0
    cm = confusion_matrix(a, b)
    assert cm["success"]["success"] == 1
    assert cm["failure"]["success"] == 0


@pytest.mark.offline
def test_consistency_flip_rate():
    assert consistency_flip_rate([["success", "success"], ["failure", "failure"]]) == 0.0
    assert consistency_flip_rate([["success", "failure"]]) == 1.0


@pytest.mark.offline
def test_label_reliability_requires_gold():
    decision = label_reliability_decision(
        gold_accuracy=None, kappa_vs_grader=1.0, flip_rate=0.0
    )
    assert decision["reliable_enough_for_label"] is False


@pytest.mark.offline
def test_label_reliability_met_with_gold():
    decision = label_reliability_decision(
        gold_accuracy=0.9, kappa_vs_grader=0.5, flip_rate=0.05
    )
    assert decision["reliable_enough_for_label"] is True


@pytest.mark.offline
def test_run_eval_on_fixtures(sample_runs, gold_labels, tmp_path: Path):
    report = evaluate(
        sample_runs, repeats=2, gold=gold_labels, heuristic=True
    )
    assert report["n_runs"] == len(sample_runs)
    assert report["agreement_with_grader"] == 1.0
    assert report["gold_accuracy_blue"] == 1.0
    assert report["consistency_flip_rate"] == 0.0
    out = tmp_path / "r1.json"
    out.write_text(json.dumps(report))
    assert out.exists()
