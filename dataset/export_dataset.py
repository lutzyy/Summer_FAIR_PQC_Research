#!/usr/bin/env python3
"""
Export Dataset v1: one row per experiment joining runs + blue + rule (+ gold).

Offline mode: join fixture runs with judgments produced in-process.
Postgres mode: join tables when records DB is available.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_BLUE = _ROOT / "adversary" / "blue"
if str(_BLUE) not in sys.path:
    sys.path.insert(0, str(_BLUE))
_ORCH = _ROOT / "orchestrator"
if str(_ORCH) not in sys.path:
    sys.path.insert(0, str(_ORCH))

from agent import judge_run  # noqa: E402
from collectors.bundle import infer_crypto_config  # noqa: E402
from rule_grader import grade_run  # noqa: E402


COLUMNS = [
    "run_id",
    "timestamp",
    "target",
    "key_exchange",
    "authentication",
    "service_protocol",
    "device_constraint",
    "attack_type",
    "attack_params",
    "blue_agent_outcome",
    "blue_confidence",
    "blue_rationale",
    "rule_based_outcome",
    "gold_label",
    "evidence_sources_available",
    "blue_model",
    "blue_prompt_version",
    "selected_by",
    "crypto_detected",
    "outcome_notes",
]


def _row_from_run(
    run: dict[str, Any],
    *,
    selected_by: str = "unknown",
    gold: dict[str, str] | None = None,
    heuristic: bool = True,
) -> dict[str, Any]:
    crypto, _ = infer_crypto_config(run)
    judgment = judge_run(run, force_heuristic=heuristic)
    rule = grade_run(run)
    rid = str(run.get("run_id"))
    return {
        "run_id": rid,
        "timestamp": run.get("timestamp"),
        "target": run.get("target"),
        "key_exchange": crypto.get("key_exchange"),
        "authentication": crypto.get("authentication"),
        "service_protocol": crypto.get("service_protocol"),
        "device_constraint": crypto.get("device_constraint"),
        "attack_type": run.get("attack_name"),
        "attack_params": json.dumps(run.get("attack_params") or {}),
        "blue_agent_outcome": judgment.verdict.value,
        "blue_confidence": judgment.confidence,
        "blue_rationale": judgment.rationale,
        "rule_based_outcome": rule.verdict.value,
        "gold_label": (gold or {}).get(rid, ""),
        "evidence_sources_available": json.dumps(judgment.evidence_sources_used),
        "blue_model": judgment.model,
        "blue_prompt_version": judgment.prompt_version,
        "selected_by": selected_by,
        "crypto_detected": run.get("crypto_detected"),
        "outcome_notes": run.get("outcome_notes"),
    }


def export_rows(runs: list[dict], **kwargs) -> list[dict]:
    return [_row_from_run(r, **kwargs) for r in runs]


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in COLUMNS})


def write_parquet(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Parquet export requires pandas + pyarrow. pip install pandas pyarrow"
        ) from exc
    pd.DataFrame(rows, columns=COLUMNS).to_parquet(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export dataset v1")
    parser.add_argument(
        "--runs-json",
        default=str(_BLUE / "fixtures" / "sample_runs.json"),
        help="Offline runs fixture or DB export",
    )
    parser.add_argument("--gold-json", default="")
    parser.add_argument("--selected-by", default="fixture")
    parser.add_argument("--out-csv", default=str(_ROOT / "dataset" / "v1" / "dataset_v1.csv"))
    parser.add_argument("--out-parquet", default="")
    parser.add_argument("--out-json", default=str(_ROOT / "dataset" / "v1" / "dataset_v1.json"))
    args = parser.parse_args()

    runs = json.loads(Path(args.runs_json).read_text())
    if isinstance(runs, dict):
        runs = runs.get("runs", [runs])
    gold = json.loads(Path(args.gold_json).read_text()) if args.gold_json else None
    rows = export_rows(runs, selected_by=args.selected_by, gold=gold)
    write_csv(rows, Path(args.out_csv))
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(rows, indent=2))
    if args.out_parquet:
        write_parquet(rows, Path(args.out_parquet))
    print(f"Exported {len(rows)} rows → {args.out_csv}")


if __name__ == "__main__":
    main()
