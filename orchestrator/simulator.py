#!/usr/bin/env python3
"""
Synthetic outcome simulator with a known ground-truth factor function.

Use this to test orchestrator selection BEFORE real targets (spec weeks 3–5).
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from config_space import (
    Attack,
    Authentication,
    CryptoConfig,
    Experiment,
    KeyExchange,
)


@dataclass
class SimResult:
    cell_id: str
    success: bool
    p_success: float


def _base_rate(attack: Attack) -> float:
    return {
        Attack.TLS_PROBE: 0.9,
        Attack.PCAP_REPLAY: 0.7,
        Attack.SCAPY_SYN_PROBE: 0.8,
    }[attack]


def true_success_probability(exp: Experiment) -> float:
    """
    Known synthetic function (ground truth for simulator eval):

    - Classical auth+kx is easier to “succeed” against for probes.
    - Pure PQC + PQC auth reduces success probability sharply for tls_probe.
    - Hybrid sits in between.
    - Replay is mostly config-insensitive (network outcome).
    """
    p = _base_rate(exp.attack)
    cfg = exp.config

    if exp.attack == Attack.PCAP_REPLAY:
        return min(0.95, p)

    if cfg.key_exchange == KeyExchange.HYBRID:
        p *= 0.75
    elif cfg.key_exchange == KeyExchange.PURE_PQC:
        p *= 0.45

    if cfg.authentication == Authentication.PQC:
        p *= 0.7
    elif cfg.authentication == Authentication.HYBRID:
        p *= 0.85

    if exp.attack == Attack.TLS_PROBE and cfg.key_exchange == KeyExchange.PURE_PQC:
        p *= 0.8

    return max(0.02, min(0.98, p))


def factor_importance_truth() -> list[tuple[str, float]]:
    """
    Approximate ranking of factors by how much they move tls_probe success
    under the synthetic function (for learning-curve comparison).
    """
    return [
        ("key_exchange", 1.0),
        ("authentication", 0.7),
        ("attack", 0.5),
        ("service_protocol", 0.0),
        ("device_constraint", 0.0),
    ]


def simulate(exp: Experiment, rng: random.Random | None = None) -> SimResult:
    rng = rng or random.Random()
    p = true_success_probability(exp)
    # Stable secondary hash so demos without a seed still vary by cell
    if rng is None:
        h = int(hashlib.sha256(exp.cell_id.encode()).hexdigest()[:8], 16)
        success = ((h % 10_000) / 10_000.0) < p
    else:
        success = rng.random() < p
    return SimResult(cell_id=exp.cell_id, success=success, p_success=p)


def main() -> None:
    from config_space import valid_experiments
    import json

    rng = random.Random(0)
    rows = []
    for exp in valid_experiments():
        r = simulate(exp, rng)
        rows.append({**exp.as_dict(), "success": r.success, "p_success": r.p_success})
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
