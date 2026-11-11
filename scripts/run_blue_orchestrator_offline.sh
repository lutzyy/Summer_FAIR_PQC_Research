#!/usr/bin/env bash
# Single-command offline reproduction (no Docker / no MIDAS required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p results dataset/v1

echo "=== Lab safety (informational in non-MIDAS envs) ==="
bash adversary/tools/verify-lab-safety.sh || echo "(safety failed — expected without Docker; continuing offline stubs)"

echo "=== Config space ==="
python3 orchestrator/config_space.py > results/config_space.json

echo "=== Orchestrator learning curve (simulator) ==="
python3 orchestrator/engine.py --learning-curve --seed 0 --out results/learning_curve.json
python3 orchestrator/baselines.py --mode sweep --seed 0 --out results/sweep.json
python3 orchestrator/migration_order.py --results-json results/sweep.json --out results/migration_order.json

echo "=== Blue Agent R1 eval on fixtures ==="
python3 adversary/blue/evaluation/run_eval.py \
  --runs-json adversary/blue/fixtures/sample_runs.json \
  --out results/r1_eval.json

echo "=== Dataset v1 export ==="
python3 dataset/export_dataset.py \
  --runs-json adversary/blue/fixtures/sample_runs.json \
  --out-csv dataset/v1/dataset_v1.csv \
  --out-json dataset/v1/dataset_v1.json

echo "=== Pytest (offline; excludes live e2e) ==="
python3 -m pytest -q -m "not e2e"

echo "=== Done ==="
ls -la results dataset/v1
