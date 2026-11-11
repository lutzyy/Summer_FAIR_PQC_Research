#!/usr/bin/env python3
"""Baselines: full fixed sweep and random sampling."""
from __future__ import annotations

import argparse
import json
import random
from typing import Callable

from config_space import Experiment, valid_experiments
from simulator import SimResult, simulate


def full_sweep(
    evaluate: Callable[[Experiment], SimResult] | None = None,
    seed: int = 0,
) -> list[dict]:
    rng = random.Random(seed)
    evaluate = evaluate or (lambda e: simulate(e, rng))
    rows = []
    for exp in valid_experiments():
        result = evaluate(exp)
        rows.append({**exp.as_dict(), "success": result.success, "selected_by": "sweep"})
    return rows


def random_sample(
    budget: int,
    evaluate: Callable[[Experiment], SimResult] | None = None,
    seed: int = 0,
) -> list[dict]:
    rng = random.Random(seed)
    evaluate = evaluate or (lambda e: simulate(e, rng))
    pool = list(valid_experiments())
    rng.shuffle(pool)
    rows = []
    for exp in pool[:budget]:
        result = evaluate(exp)
        rows.append({**exp.as_dict(), "success": result.success, "selected_by": "random"})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sweep", "random"], default="sweep")
    parser.add_argument("--budget", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    if args.mode == "sweep":
        rows = full_sweep(seed=args.seed)
    else:
        rows = random_sample(args.budget, seed=args.seed)
    text = json.dumps(rows, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
