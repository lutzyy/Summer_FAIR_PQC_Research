#!/usr/bin/env python3
"""
Produce a ranked migration-order recommendation from graded experiment results.

Evidence is empirical: estimated drop in attack success when moving a factor
from classical → hybrid → pure PQC (where data exists).
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def _rate(rows: list[dict], **filters) -> tuple[float | None, int]:
    matched = [
        r
        for r in rows
        if all(str(r.get(k)) == str(v) for k, v in filters.items())
    ]
    if not matched:
        return None, 0
    succ = sum(1 for r in matched if r.get("success"))
    return succ / len(matched), len(matched)


def recommend(rows: list[dict]) -> dict:
    """
    Rank upgrade steps by estimated risk reduction (drop in attack success rate).
    """
    steps = []

    # Key exchange classical → hybrid
    r_c, n_c = _rate(rows, key_exchange="classical")
    r_h, n_h = _rate(rows, key_exchange="hybrid")
    r_p, n_p = _rate(rows, key_exchange="pure_pqc")
    if r_c is not None and r_h is not None:
        steps.append(
            {
                "step": "Upgrade key exchange classical → hybrid",
                "risk_reduction": r_c - r_h,
                "evidence": {
                    "classical_success_rate": r_c,
                    "n_classical": n_c,
                    "hybrid_success_rate": r_h,
                    "n_hybrid": n_h,
                },
            }
        )
    if r_h is not None and r_p is not None:
        steps.append(
            {
                "step": "Upgrade key exchange hybrid → pure_pqc",
                "risk_reduction": r_h - r_p,
                "evidence": {
                    "hybrid_success_rate": r_h,
                    "n_hybrid": n_h,
                    "pure_pqc_success_rate": r_p,
                    "n_pure_pqc": n_p,
                },
            }
        )
    if r_c is not None and r_p is not None:
        steps.append(
            {
                "step": "Upgrade key exchange classical → pure_pqc",
                "risk_reduction": r_c - r_p,
                "evidence": {
                    "classical_success_rate": r_c,
                    "n_classical": n_c,
                    "pure_pqc_success_rate": r_p,
                    "n_pure_pqc": n_p,
                },
            }
        )

    a_c, na_c = _rate(rows, authentication="classical")
    a_p, na_p = _rate(rows, authentication="pqc")
    if a_c is not None and a_p is not None:
        steps.append(
            {
                "step": "Upgrade authentication classical → pqc (ML-DSA)",
                "risk_reduction": a_c - a_p,
                "evidence": {
                    "classical_success_rate": a_c,
                    "n_classical": na_c,
                    "pqc_success_rate": a_p,
                    "n_pqc": na_p,
                },
            }
        )

    steps.sort(key=lambda s: s["risk_reduction"], reverse=True)
    return {
        "migration_order": steps,
        "caveat": (
            "Derived from labeled experiments in this dataset only. "
            "Does not measure store-now-decrypt-later quantum advantage."
        ),
        "n_experiments": len(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-json",
        required=True,
        help="List of experiment rows with success bool + factor columns",
    )
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    rows = json.loads(Path(args.results_json).read_text())
    if isinstance(rows, dict) and "experiments" in rows:
        rows = rows["experiments"]
    payload = recommend(rows)
    text = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
