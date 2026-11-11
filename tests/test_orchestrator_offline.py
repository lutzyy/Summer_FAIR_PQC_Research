"""Orchestrator simulator/baselines (no Docker)."""
from __future__ import annotations

import pytest

from baselines import full_sweep, random_sample
from config_space import enumerate_space, valid_experiments
from engine import estimate_factor_ranking, learning_curve, run_orchestrator
from migration_order import recommend


@pytest.mark.offline
def test_config_space_marks_invalid_and_has_valid_cells():
    rows = enumerate_space()
    assert any(r["valid"] for r in rows)
    assert any(not r["valid"] for r in rows)
    valid = valid_experiments()
    assert len(valid) >= 3  # at least classical×3 attacks


@pytest.mark.offline
def test_sweep_and_orchestrator_budgets():
    sweep = full_sweep(seed=0)
    assert len(sweep) == len(valid_experiments())
    orch = run_orchestrator(budget=3, seed=0)
    assert len(orch) == 3
    assert all(r["selected_by"] == "orchestrator" for r in orch)
    rand = random_sample(budget=3, seed=0)
    assert len(rand) == 3


@pytest.mark.offline
def test_migration_order_from_sweep():
    sweep = full_sweep(seed=0)
    payload = recommend(sweep)
    assert "migration_order" in payload
    assert payload["n_experiments"] == len(sweep)


@pytest.mark.offline
def test_learning_curve_shape():
    curve = learning_curve(seed=0, max_budget=3)
    assert curve["valid_cells"] == len(valid_experiments())
    assert len(curve["curve"]) == 3
    ranking = estimate_factor_ranking(full_sweep(seed=0))
    assert ranking[0][0] in {
        "key_exchange",
        "authentication",
        "attack",
        "service_protocol",
        "device_constraint",
    }
