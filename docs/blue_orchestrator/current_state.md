# Current state (verified against the repo)

Written for the Blue Agent + Orchestrator track. Verified by reading the tree and attempting a lab run in this environment. **Not** based on the top-level README alone.

## Safety

- Script: `adversary/tools/verify-lab-safety.sh`
- Result in this Cloud Agent environment: **FAIL** — Docker is not installed (`docker: command not found`), so `lab-net`, `practice-target`, and `attacker` cannot be checked.
- Implication: end-to-end MIDAS lab runs are **not** possible here. Offline stubs, synthetic runs, and the orchestrator simulator are used until MIDAS is available.

## Run-record fields (contract — do not change without agreement)

Source: `adversary/brain/contract.py` / `adversary/brain/schema.sql`

| Field | Type | Notes |
|-------|------|--------|
| `run_id` | TEXT PK | UUID string |
| `timestamp` | TEXT | UTC ISO-8601 |
| `target` | TEXT | e.g. `practice-target:443` |
| `crypto_detected` | TEXT \| NULL | Probe summary or null |
| `attack_name` | TEXT | Tool-reported attack id |
| `attack_params` | JSONB | Always includes `target` when tools succeed |
| `outcome_notes` | TEXT | Short human-readable tool result |

Tool JSON keys (`TOOL_OUTPUT_KEYS`): `attack_name`, `crypto_detected`, `attack_params`, `outcome_notes`.

## Attacks that exist today

| CLI / agent name | `attack_name` in JSON | What it does | Stated objective (for Blue Agent rubric) |
|------------------|----------------------|--------------|------------------------------------------|
| `detect` | `tls_probe` | `openssl s_client -brief` against target | Recover TLS protocol, ciphersuite, group, and signature type |
| `replay` | `pcap_replay` | `tcpreplay` of a lab pcap onto `eth0` | Replay completes with tool output (not a crypto break by itself) |
| `craft` | `scapy_syn_probe` | Scapy TCP SYN to target port | Receive a TCP response (port reachable / responds) |

Agent wiring: `adversary/brain/agent.py` maps `detect`/`replay`/`craft` → `docker exec attacker python3 /opt/redteam/tools.py …`.

## Rule-based grader

**Not present in the repository.** Sebastian’s post-converge notes (`Instructions/sebastian_next_two_weeks.md`) list “a grading function that reads `RunRecord` and assigns success/failure” as future work.

**Conflict with the Fall 2026 Blue Agent spec:** the spec assumes Sebastian’s rule-based grader already labels runs. Until that lands (or is agreed in writing), this track ships a **provisional** rule grader at `adversary/blue/rule_grader.py` writing to table `rule_based_grades` (new table; `runs` / `contract.py` untouched). Blue Agent labels live in `blue_agent_judgments` side by side. Replace the provisional grader when Sebastian’s version is available — do not overwrite either label column.

## Evidence sources available per run

| Source | Available now? | Notes |
|--------|----------------|-------|
| Attack tool output | **Yes** (in `runs`) | `outcome_notes`, `attack_params`, exit parsing happens only in agent `_execute` (stdout JSON); stderr/exit not stored in DB today |
| Target/server logs (nginx, TLS) | **No** | Not collected or stored per run |
| Zeek / Suricata | **No** | Mentioned in README; no compose, no log paths, not tied to run windows |
| Crypto config of target | **Partial** | Inferable from `target` name / `crypto_detected` after `tls_probe`; no orchestrator-driven config switch yet |
| Attack stated objective | **Via rubric** | Versioned in `adversary/blue/rubric/`; not in the run record |

Default evidence mode until sensors exist: **tool output + run metadata + rubric** (`without_sensors`).

## Graded runs in the DB

- Postgres schema: `runs` only (`adversary/brain/schema.sql`).
- This environment: **0** (no Postgres, no `.env`, Docker absent).
- On MIDAS: count with `SELECT COUNT(*) FROM runs;` after `records` is up. Re-run and update the number here when the lab is available.

## Stack status (verified vs planned)

| Component | Status |
|-----------|--------|
| Practice targets (classical + PQC) | Code/scripts exist (`start-lab.sh`); not running here |
| Attack tools | `adversary/tools/tools.py` present |
| Red agent (PydanticAI → vLLM) | `adversary/brain/agent.py`; model `Qwen/Qwen2.5-14B-Instruct` @ `localhost:8000` |
| Postgres records | `db.py` + `schema.sql`; password via gitignored `.env` |
| Prefect / Langfuse / Grafana | Documented; **not** in repo |
| oqs-provider / OpenSSL PQC target | Via `openquantumsafe/nginx` image on port **4433** |
| Zeek + Suricata | **Not deployed** in this repo |

## How crypto config is switched today

- **Two fixed containers**, not a runtime config matrix:
  - Classical: `practice-target:443` (stock nginx + RSA cert)
  - PQC/hybrid: `practice-target-pqc:4433` (`openquantumsafe/nginx`)
- No env-var / rebuild orchestrator switch yet. Config space for the orchestrator must mark combinations the lab cannot run as `invalid`.

## vLLM for Blue Agent

- Same self-hosted endpoint as red agent: `http://localhost:8000/v1`
- Model name in code: `Qwen/Qwen2.5-14B-Instruct`
- Context length from Sebastian’s runbook: `--max-model-len 8192`
- **Never** call hosted APIs (OpenAI/Anthropic). Offline/heuristic fallback is for CI and non-MIDAS development only.

## Quantum-attacker assumption (roadmap)

Not implemented. Dataset v1 records classical/lab-observable attack outcomes only. “Store now, decrypt later” success is **not** measured; document that limitation in `dataset/DATASET.md`.

## Open questions (do not guess — escalate)

See `docs/blue_orchestrator/OPEN_QUESTIONS.md`.
