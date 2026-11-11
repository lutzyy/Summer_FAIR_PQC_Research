"""Shared fixtures for Blue Agent and red→blue coordination tests."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BLUE = ROOT / "adversary" / "blue"
BRAIN = ROOT / "adversary" / "brain"
ORCH = ROOT / "orchestrator"
FIXTURES = BLUE / "fixtures"

for path in (BLUE, BRAIN, ORCH, str(ROOT)):
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def sample_runs() -> list[dict]:
    return json.loads((FIXTURES / "sample_runs.json").read_text())


@pytest.fixture
def sample_run(sample_runs) -> dict:
    return dict(sample_runs[0])


@pytest.fixture(scope="session")
def gold_labels() -> dict[str, str]:
    raw = json.loads((FIXTURES / "gold_subset.example.json").read_text())
    return {k: v for k, v in raw.items() if not str(k).startswith("_")}


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "e2e: live lab end-to-end; requires RUN_E2E=1 and Docker/vLLM/Postgres",
    )


def pytest_collection_modifyitems(config, items):
    """Skip @pytest.mark.e2e unless RUN_E2E=1."""
    if os.environ.get("RUN_E2E", "0") == "1":
        return
    skip_e2e = pytest.mark.skip(reason="live e2e disabled (set RUN_E2E=1 on MIDAS)")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)
