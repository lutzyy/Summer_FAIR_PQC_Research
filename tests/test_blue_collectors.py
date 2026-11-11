"""Blue-only: toggleable evidence collectors."""
from __future__ import annotations

import pytest

from collectors.bundle import collect_evidence


@pytest.mark.offline
def test_default_collectors_mark_sensors_unavailable(sample_run):
    bundle = collect_evidence(sample_run)
    assert "tool_output" in bundle.sources_available
    assert "attack_objective" in bundle.sources_available
    assert "crypto_config" in bundle.sources_available
    assert "sensor_logs" not in bundle.sources_available
    assert bundle.sensor_logs.get("available") is False
    assert bundle.server_logs.get("available") is False


@pytest.mark.offline
def test_tool_output_only_toggle(sample_run):
    bundle = collect_evidence(
        sample_run, enabled=["tool_output", "attack_objective"]
    )
    assert bundle.sources_enabled == ["tool_output", "attack_objective"]
    assert set(bundle.sources_available) <= {"tool_output", "attack_objective"}
    assert bundle.tool_output["attack_name"] == sample_run["attack_name"]
    assert bundle.tool_output["stderr"] is None  # not in contract


@pytest.mark.offline
def test_pqc_target_inferred_profile(sample_runs):
    pqc = next(r for r in sample_runs if "pqc" in r["target"])
    bundle = collect_evidence(pqc, enabled=["crypto_config"])
    assert "pqc" in bundle.crypto_config["inferred_profile"] or "pqc" in bundle.crypto_config[
        "authentication"
    ]
