"""Blue-only: versioned success rubric."""
from __future__ import annotations

import pytest

from rubric.loader import load_rubric, objective_for


@pytest.mark.offline
def test_rubric_v1_loads_and_has_known_attacks():
    rubric = load_rubric("v1")
    assert rubric["version"] == "v1"
    for name in ("tls_probe", "pcap_replay", "scapy_syn_probe", "none"):
        assert name in rubric["attacks"]
        assert "objective" in rubric["attacks"][name]


@pytest.mark.offline
def test_objective_for_attack_name_and_alias():
    by_name = objective_for("tls_probe")
    by_alias = objective_for("detect")
    assert "Recover" in by_name["objective"] or "recover" in by_name["objective"].lower()
    assert by_alias["objective"] == by_name["objective"]


@pytest.mark.offline
def test_unknown_attack_is_inconclusive_guidance():
    obj = objective_for("totally_unknown_attack")
    assert "Unknown" in obj["objective"] or obj.get("failure_when")
