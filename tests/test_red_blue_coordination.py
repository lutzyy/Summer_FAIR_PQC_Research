"""
Mocked red → blue coordination (no Docker).

Simulates what the red agent/tools emit under contract.py, then ensures the
Blue Agent can judge those records without mutating the run contract fields.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from agent import judge_run
from contract import TOOL_OUTPUT_KEYS, RunRecord
from models import Verdict
from rule_grader import grade_run

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "dataset") not in sys.path:
    sys.path.insert(0, str(_ROOT / "dataset"))


def _mock_red_tool_output(attack: str, target: str) -> dict[str, Any]:
    """Mirror adversary/tools/tools.py JSON shape without calling Docker."""
    if attack == "detect":
        return {
            "attack_name": "tls_probe",
            "crypto_detected": (
                "TLSv1.3 / TLS_AES_256_GCM_SHA384 / group=X25519 / "
                "sig=rsa_pss_rsae_sha256"
            ),
            "attack_params": {"target": target},
            "outcome_notes": "Handshake completed.",
        }
    if attack == "replay":
        return {
            "attack_name": "pcap_replay",
            "crypto_detected": None,
            "attack_params": {
                "target": target,
                "pcap": "/opt/redteam/captures/sample.pcap",
            },
            "outcome_notes": "Actual: 10 packets sent. Replay finished.",
        }
    if attack == "craft":
        return {
            "attack_name": "scapy_syn_probe",
            "crypto_detected": None,
            "attack_params": {"target": target, "port": 443},
            "outcome_notes": "Port 443 responded with TCP flags SA.",
        }
    return {
        "attack_name": "none",
        "crypto_detected": None,
        "attack_params": {"attack": attack},
        "outcome_notes": f"Unknown attack: {attack}",
    }


def _red_execute_to_run_record(target: str, attack: str) -> RunRecord:
    """Same handoff shape as adversary/brain/agent.py → RunRecord → DB."""
    result = _mock_red_tool_output(attack, target)
    return RunRecord(
        target=target,
        crypto_detected=result.get("crypto_detected"),
        attack_name=result["attack_name"],
        attack_params=result.get("attack_params", {}),
        outcome_notes=result.get("outcome_notes", ""),
    )


@pytest.mark.offline
@pytest.mark.parametrize("attack", ["detect", "replay", "craft"])
def test_mock_red_output_matches_contract_keys(attack):
    out = _mock_red_tool_output(attack, "practice-target:443")
    for key in TOOL_OUTPUT_KEYS:
        assert key in out


@pytest.mark.offline
@pytest.mark.parametrize(
    "attack,expected_verdict",
    [
        ("detect", Verdict.SUCCESS),
        ("replay", Verdict.SUCCESS),
        ("craft", Verdict.SUCCESS),
    ],
)
def test_blue_judges_mocked_red_run(attack, expected_verdict):
    rec = _red_execute_to_run_record("practice-target:443", attack)
    run = rec.model_dump()

    for key in ("attack_name", "crypto_detected", "attack_params", "outcome_notes"):
        assert key in run

    blue = judge_run(run, force_heuristic=True)
    rule = grade_run(run)

    assert blue.run_id == rec.run_id
    assert blue.verdict == expected_verdict
    assert rule.verdict == expected_verdict
    # Side-by-side labels: both exist; neither overwrites the run record
    assert run["attack_name"] == rec.attack_name
    assert run["outcome_notes"] == rec.outcome_notes


@pytest.mark.offline
def test_red_failure_path_labeled_failure_by_both():
    rec = RunRecord(
        target="practice-target:443",
        crypto_detected=None,
        attack_name="tls_probe",
        attack_params={"target": "practice-target:443"},
        outcome_notes="Could not read handshake.",
    )
    run = rec.model_dump()
    blue = judge_run(run, force_heuristic=True)
    rule = grade_run(run)
    assert blue.verdict == Verdict.FAILURE
    assert rule.verdict == Verdict.FAILURE


@pytest.mark.offline
def test_pqc_target_red_to_blue_handoff():
    rec = RunRecord(
        target="practice-target-pqc:4433",
        crypto_detected=(
            "TLSv1.3 / TLS_AES_256_GCM_SHA384 / group=X25519MLKEM768 / sig=mldsa65"
        ),
        attack_name="tls_probe",
        attack_params={"target": "practice-target-pqc:4433"},
        outcome_notes="Handshake completed.",
    )
    j = judge_run(rec.model_dump(), force_heuristic=True)
    assert j.verdict == Verdict.SUCCESS
    assert j.evidence_cited or j.evidence_sources_used


@pytest.mark.offline
def test_dataset_row_join_keeps_red_fields(sample_run):
    from export_dataset import _row_from_run

    row = _row_from_run(sample_run, selected_by="test", heuristic=True)
    assert row["run_id"] == sample_run["run_id"]
    assert row["attack_type"] == sample_run["attack_name"]
    assert row["blue_agent_outcome"] in {"success", "failure", "inconclusive"}
    assert row["rule_based_outcome"] in {"success", "failure", "inconclusive"}
    assert row["outcome_notes"] == sample_run["outcome_notes"]


@pytest.mark.offline
def test_run_record_json_roundtrip_for_blue():
    rec = _red_execute_to_run_record("practice-target:443", "detect")
    payload = json.loads(rec.model_dump_json())
    j = judge_run(payload, force_heuristic=True)
    assert j.verdict == Verdict.SUCCESS
