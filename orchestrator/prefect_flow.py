#!/usr/bin/env python3
"""
Prefect flow stub: schedule orchestrator picks → (future) red attack → Blue Agent label.

Prefect is optional. This module runs as plain Python if Prefect is not installed.
Never attaches anything to lab-net.
"""
from __future__ import annotations

import json
from pathlib import Path

from engine import run_orchestrator
from migration_order import recommend


def experiment_batch(budget: int = 8, seed: int = 0) -> dict:
    rows = run_orchestrator(budget=budget, seed=seed)
    return {"experiments": rows, "migration_order": recommend(rows)}


def main() -> None:
    try:
        from prefect import flow  # type: ignore

        @flow(name="pqc-orchestrator-sim")
        def _flow(budget: int = 8, seed: int = 0) -> dict:
            return experiment_batch(budget=budget, seed=seed)

        result = _flow()
    except ImportError:
        result = experiment_batch()
    out = Path(__file__).resolve().parents[1] / "results" / "prefect_stub.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
