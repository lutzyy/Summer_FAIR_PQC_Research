#!/usr/bin/env python3
"""
R1 evaluation entrypoint.

Computes agreement with provisional rule grader, optional gold accuracy,
ablation across evidence source sets, and consistency across repeats.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BLUE = Path(__file__).resolve().parents[1]
if str(_BLUE) not in sys.path:
    sys.path.insert(0, str(_BLUE))

from agent import judge_run  # noqa: E402
from evaluation.metrics import (  # noqa: E402
    agreement_rate,
    cohens_kappa,
    confusion_matrix,
    consistency_flip_rate,
    label_reliability_decision,
)
from rule_grader import grade_run  # noqa: E402

ABLATION_SETS = {
    "all_sources": None,  # default collectors
    "tool_output_only": ["tool_output", "attack_objective"],
    "no_sensors": [
        "tool_output",
        "server_logs",
        "crypto_config",
        "attack_objective",
    ],  # sensors omitted from enabled list
}


def _load_runs(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "runs" in data:
        return data["runs"]
    return [data]


def evaluate(
    runs: list[dict],
    *,
    repeats: int = 3,
    gold: dict[str, str] | None = None,
    heuristic: bool = True,
) -> dict:
    blue_labels = []
    rule_labels = []
    per_run = []
    ablation = {name: [] for name in ABLATION_SETS}
    consistency_sets = []

    for run in runs:
        rule = grade_run(run)
        rule_labels.append(rule.verdict.value)

        repeats_v = []
        for _ in range(max(1, repeats)):
            j = judge_run(run, force_heuristic=heuristic)
            repeats_v.append(j.verdict.value)
        consistency_sets.append(repeats_v)
        blue_labels.append(repeats_v[0])

        for name, sources in ABLATION_SETS.items():
            j = judge_run(
                run,
                enabled_sources=sources,
                force_heuristic=heuristic,
            )
            ablation[name].append(j.verdict.value)

        per_run.append(
            {
                "run_id": run.get("run_id"),
                "attack_name": run.get("attack_name"),
                "blue": repeats_v[0],
                "rule": rule.verdict.value,
                "agree": repeats_v[0] == rule.verdict.value,
                "repeats": repeats_v,
            }
        )

    disagreements = [r for r in per_run if not r["agree"]]
    gold_acc = None
    if gold:
        paired_blue = []
        paired_gold = []
        for run, b in zip(runs, blue_labels):
            rid = str(run.get("run_id"))
            if rid in gold:
                paired_blue.append(b)
                paired_gold.append(gold[rid])
        if paired_gold:
            gold_acc = agreement_rate(paired_gold, paired_blue)

    kappa = cohens_kappa(rule_labels, blue_labels)
    flip = consistency_flip_rate(consistency_sets)
    decision = label_reliability_decision(
        gold_accuracy=gold_acc, kappa_vs_grader=kappa, flip_rate=flip
    )

    ablation_agreement = {
        name: agreement_rate(rule_labels, preds) for name, preds in ablation.items()
    }

    return {
        "n_runs": len(runs),
        "agreement_with_grader": agreement_rate(rule_labels, blue_labels),
        "cohens_kappa_vs_grader": kappa,
        "confusion_matrix_rule_vs_blue": confusion_matrix(rule_labels, blue_labels),
        "gold_accuracy_blue": gold_acc,
        "consistency_flip_rate": flip,
        "ablation_agreement_with_grader": ablation_agreement,
        "disagreements": disagreements,
        "label_reliability_decision": decision,
        "per_run": per_run,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Blue Agent R1 evaluation")
    parser.add_argument(
        "--runs-json",
        required=True,
        help="JSON list of RunRecord dicts (offline fixture or DB export)",
    )
    parser.add_argument("--gold-json", help='Optional {"run_id": "success"|...}')
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--out", default="results/r1_eval.json")
    parser.add_argument(
        "--heuristic",
        action="store_true",
        default=True,
        help="Use heuristic judge (default True for offline)",
    )
    args = parser.parse_args()

    runs = _load_runs(Path(args.runs_json))
    gold = None
    if args.gold_json:
        raw_gold = json.loads(Path(args.gold_json).read_text())
        gold = {k: v for k, v in raw_gold.items() if not str(k).startswith("_")}
    report = evaluate(runs, repeats=args.repeats, gold=gold, heuristic=args.heuristic)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in report if k != "per_run"}, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
