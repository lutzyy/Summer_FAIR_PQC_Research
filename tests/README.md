# Tests

Offline by default (no Docker). Live MIDAS e2e is opt-in.

```bash
# from repo root
pip install -r requirements.txt
pytest -q                 # Blue-only + mocked red→blue + orchestrator sim
pytest -q -m offline      # same, explicit
RUN_E2E=1 pytest -q -m e2e   # only on MIDAS after safety script passes
```

| File | Covers |
|------|--------|
| `test_blue_*.py` | Rubric, collectors, rule grader, heuristic judge, R1 metrics |
| `test_red_blue_coordination.py` | Mocked red tool JSON → `RunRecord` → Blue + rule labels |
| `test_orchestrator_offline.py` | Config space, sweep/random/orchestrator, migration order |
| `test_e2e_live.py` | `@pytest.mark.e2e` stubs for Docker/Postgres/vLLM |

Heuristic Blue mode is used offline so CI does not need vLLM. On MIDAS, drop `--heuristic` / unset `BLUE_FORCE_HEURISTIC` for real LLM judgments.
