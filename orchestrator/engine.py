#!/usr/bin/env python3
"""
Factor-aware active-learning orchestrator.

Chooses the next (config, attack) experiment to reveal which crypto factors
change outcomes faster than a full sweep. Consumes labels (simulator or Blue Agent).
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from baselines import full_sweep, random_sample
from config_space import Experiment, valid_experiments
from simulator import SimResult, factor_importance_truth, simulate


FACTORS = (
    "key_exchange",
    "authentication",
    "service_protocol",
    "device_constraint",
    "attack",
)


@dataclass
class OrchestratorState:
    labeled: list[dict] = field(default_factory=list)
    remaining: list[Experiment] = field(default_factory=list)

    def factor_stats(self) -> dict[str, dict[str, list[int]]]:
        """For each factor → level → [successes, trials]."""
        stats: dict[str, dict[str, list[int]]] = {
            f: defaultdict(lambda: [0, 0]) for f in FACTORS
        }
        for row in self.labeled:
            success = 1 if row.get("success") else 0
            for f in FACTORS:
                level = str(row.get(f))
                stats[f][level][0] += success
                stats[f][level][1] += 1
        return stats


def _beta_var(successes: int, trials: int) -> float:
    # Beta(1+s, 1+f) variance as uncertainty proxy
    a = 1 + successes
    b = 1 + (trials - successes)
    return (a * b) / (((a + b) ** 2) * (a + b + 1))


def acquisition_score(exp: Experiment, state: OrchestratorState) -> float:
    """
    Score unevaluated cells by factor-level uncertainty + novelty.
    Higher = more useful to label next.
    """
    stats = state.factor_stats()
    d = exp.as_dict()
    score = 0.0
    for f in FACTORS:
        level = str(d[f])
        s, n = stats[f].get(level, [0, 0])
        score += _beta_var(s, n)
        # Novelty: prefer unseen factor levels
        if n == 0:
            score += 0.5
    # Prefer cells that contrast current best/worst key_exchange if we have data
    kx_stats = stats["key_exchange"]
    if len(kx_stats) >= 1:
        rates = []
        for level, (s, n) in kx_stats.items():
            if n:
                rates.append(s / n)
        if rates:
            score += 0.1 * (max(rates) - min(rates) + 1e-6)
    return score


def choose_next(state: OrchestratorState, rng: random.Random) -> Experiment | None:
    if not state.remaining:
        return None
    scored = [(acquisition_score(e, state), e) for e in state.remaining]
    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[0][0]
    candidates = [e for s, e in scored if math.isclose(s, top) or s >= top - 1e-9]
    return rng.choice(candidates)


def run_orchestrator(
    budget: int,
    evaluate: Callable[[Experiment], SimResult] | None = None,
    seed: int = 0,
) -> list[dict]:
    rng = random.Random(seed)
    evaluate = evaluate or (lambda e: simulate(e, rng))
    state = OrchestratorState(remaining=list(valid_experiments()))
    rows: list[dict] = []
    for _ in range(min(budget, len(state.remaining))):
        pick = choose_next(state, rng)
        if pick is None:
            break
        state.remaining = [e for e in state.remaining if e.cell_id != pick.cell_id]
        result = evaluate(pick)
        row = {
            **pick.as_dict(),
            "success": result.success,
            "selected_by": "orchestrator",
        }
        state.labeled.append(row)
        rows.append(row)
    return rows


def estimate_factor_ranking(rows: list[dict]) -> list[tuple[str, float]]:
    """
    Rank factors by variance of empirical success rates across levels.
    """
    by_factor: dict[str, dict[str, list[int]]] = {
        f: defaultdict(lambda: [0, 0]) for f in FACTORS
    }
    for row in rows:
        for f in FACTORS:
            s, n = by_factor[f][str(row[f])]
            by_factor[f][str(row[f])][0] = s + (1 if row["success"] else 0)
            by_factor[f][str(row[f])][1] = n + 1
    scores = []
    for f, levels in by_factor.items():
        rates = [s / n for s, n in levels.values() if n]
        if len(rates) < 2:
            scores.append((f, 0.0))
        else:
            mean = sum(rates) / len(rates)
            var = sum((r - mean) ** 2 for r in rates) / len(rates)
            scores.append((f, var))
    scores.sort(key=lambda t: t[1], reverse=True)
    return scores


def ranking_agreement(est: list[tuple[str, float]], truth: list[tuple[str, float]], k: int = 2) -> float:
    top_est = [f for f, _ in est[:k]]
    top_truth = [f for f, _ in truth[:k]]
    return len(set(top_est) & set(top_truth)) / float(k)


def learning_curve(seed: int = 0, max_budget: int | None = None) -> dict:
    """Compare orchestrator vs random on recovering top factors vs full sweep truth."""
    sweep = full_sweep(seed=seed)
    truth_rank = estimate_factor_ranking(sweep)
    # Also expose synthetic designed truth for reference
    designed = factor_importance_truth()
    n = max_budget or len(valid_experiments())
    curve = []
    for b in range(1, n + 1):
        orch = run_orchestrator(b, seed=seed)
        rand = random_sample(b, seed=seed + 1)
        curve.append(
            {
                "budget": b,
                "orchestrator_top2_agreement": ranking_agreement(
                    estimate_factor_ranking(orch), truth_rank, k=2
                ),
                "random_top2_agreement": ranking_agreement(
                    estimate_factor_ranking(rand), truth_rank, k=2
                ),
            }
        )
    return {
        "sweep_factor_ranking": truth_rank,
        "designed_factor_importance": designed,
        "curve": curve,
        "valid_cells": len(valid_experiments()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="PQC lab experiment orchestrator")
    parser.add_argument("--budget", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--learning-curve", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    if args.learning_curve:
        payload = learning_curve(seed=args.seed)
    else:
        payload = {"experiments": run_orchestrator(args.budget, seed=args.seed)}
    text = json.dumps(payload, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
