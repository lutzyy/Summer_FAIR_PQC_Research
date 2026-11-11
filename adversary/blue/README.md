# Blue Agent

Judges whether a red-team attack met its stated objective. Produces the **outcome label** column for Dataset v1. Does not replace the rule-based grader — both labels live side by side.

## Safety

```bash
bash adversary/tools/verify-lab-safety.sh
```

If any check FAILs, fix isolation before MIDAS lab work. LLM calls must use **self-hosted vLLM** only (`VLLM_BASE_URL`, default `http://localhost:8000/v1`).

## Layout

| Path | Role |
|------|------|
| `agent.py` | Entry: `--run-id` or `--json-run` → structured judgment |
| `models.py` | Pydantic judgment / evidence models |
| `schema.sql` | `blue_agent_judgments`, `rule_based_grades`, `gold_labels`, … |
| `db.py` | Postgres helpers (does not alter `runs`) |
| `rule_grader.py` | Provisional rule grader (Sebastian’s not in repo yet) |
| `rubric/v1.yaml` | Versioned per-attack success definitions |
| `collectors/` | Toggleable evidence collectors |
| `evaluation/` | R1 metrics (agreement, kappa, ablation, consistency) |
| `fixtures/sample_runs.json` | Offline runs for CI / no-Docker |

## Quick start (offline)

```bash
cd adversary/blue
python3 agent.py --json-run fixtures/sample_runs.json --heuristic --also-rule-grade
python3 evaluation/run_eval.py --runs-json fixtures/sample_runs.json --out ../../../results/r1_eval.json

# from repo root — Blue-only + mocked red→blue tests (no Docker)
pytest -q -m "not e2e"
```

See `tests/README.md`. Live MIDAS e2e: `RUN_E2E=1 pytest -m e2e`.

## MIDAS (Postgres + vLLM)

```bash
# apply new tables only (leaves runs untouched)
psql "$DSN" -f schema.sql

python3 agent.py --run-id <uuid> --save
python3 rule_grader.py --run-id <uuid> --save
```

Environment: same `.env` password as `adversary/brain/.env` (`POSTGRES_PASSWORD`). Optional Langfuse: `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` (local JSONL audit always written under `.langfuse_local/`).

## Contract

Does **not** change `adversary/brain/contract.py` keys or the `runs` table schema.
