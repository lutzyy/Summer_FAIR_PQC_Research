"""
Live MIDAS e2e placeholder.

Skipped unless RUN_E2E=1. Intended path on the lab server:

1. bash adversary/tools/verify-lab-safety.sh  (must PASS)
2. Red agent produces a real runs row (Docker attacker + target)
3. Blue agent: python adversary/blue/agent.py --run-id <id> --save
4. Assert blue_agent_judgments row exists alongside runs (no contract mutation)
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.e2e
def test_safety_script_passes_on_lab():
    script = ROOT / "adversary" / "tools" / "verify-lab-safety.sh"
    assert script.exists()
    if shutil.which("docker") is None:
        pytest.skip("docker not installed")
    proc = subprocess.run(
        ["bash", str(script)],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.e2e
def test_red_then_blue_live_pipeline():
    """
    Requires: Docker lab up, Postgres with runs, optional vLLM.
    Enable with: RUN_E2E=1 BLUE_FORCE_HEURISTIC=1|0 pytest -m e2e
    """
    if os.environ.get("POSTGRES_PASSWORD") is None:
        pytest.skip("POSTGRES_PASSWORD not set")

    # Deferred live wiring: keep the mark and structure ready for MIDAS.
    # Implementers should: insert/fetch a real run_id, call judge_run_id(save=True),
    # fetch_latest_judgment, and assert verdict in {success,failure,inconclusive}.
    pytest.skip(
        "Live red→blue DB pipeline not enabled in this environment; "
        "hook up judge_run_id + fetch_run when MIDAS records are available."
    )
