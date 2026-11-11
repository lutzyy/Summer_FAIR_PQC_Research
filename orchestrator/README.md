# Orchestrator

Chooses which `(crypto_config, attack)` experiments to run next and learns which crypto factors change outcomes (R2). Consumes Blue Agent labels on real targets; uses the simulator offline.

## Decision problem

See `docs/blue_orchestrator/decision_problem.md`. Framing: **factor-aware active learning**, compared to full sweep and random baselines.

## Layout

| Path | Role |
|------|------|
| `config_space.py` | Typed enumerable space; marks invalid lab combos |
| `simulator.py` | Synthetic outcome function for strategy tests |
| `baselines.py` | Full sweep + random sampling |
| `engine.py` | Selection loop + learning curve |
| `migration_order.py` | Ranked upgrade recommendation from results |

## Quick start

```bash
cd orchestrator
python3 config_space.py
python3 simulator.py | head
python3 baselines.py --mode sweep --out ../results/sweep.json
python3 engine.py --budget 8 --out ../results/orch.json
python3 engine.py --learning-curve --out ../results/learning_curve.json
python3 migration_order.py --results-json ../results/sweep.json --out ../results/migration_order.json
```

## Real targets (MIDAS)

Valid cells map to:

- classical → `practice-target:443`
- hybrid / pure_pqc + PQC auth → `practice-target-pqc:4433`

Wire Prefect later to: pick cell → ensure target → invoke red agent attack → Blue Agent `--run-id --save` → append label. Do not bridge `lab-net` to the records stack.
