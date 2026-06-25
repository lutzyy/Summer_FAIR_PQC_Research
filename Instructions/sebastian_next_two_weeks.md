# Sebastian — Next Two Weeks (Jun 25 – Jul 9, 2026)

**Your role:** Brain & Records (`adversary/brain/`)  
**Working folder:** `~/Summer_FAIR_PQC_Research/adversary/brain` on MIDAS 2  
**Runbook reference:** `Instructions/sebastian_brain_and_records (1).md`  
**Safety reference:** `Instructions/lab_safety_checklist.md`

---

## Safety first — every MIDAS 2 session

Before enabling real tools or running `agent.py` against Stefan's lab:

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/tools
bash verify-lab-safety.sh
```

**Run this every time** you connect to MIDAS 2, and **again** after any Docker change or before converge.

| Your responsibility | Rule |
|---------------------|------|
| Keep `brain` / `records` off `lab-net` | Never add `--network lab-net` to those containers |
| Trigger attacks only via `agent.py` | Never run `tools.py` or `tcpreplay` on the host |
| Real tools only when script passes | Use stubs if Stefan's lab is down or checks fail |

If the script prints **FAIL**, use stub mode and tell Stefan — do not run real attacks.

---

## Where you are now

| Done | Not done yet |
|------|--------------|
| `contract.py`, `db.py`, `schema.sql`, `agent.py` committed (Jun 20) | Converge not completed — agent still calls stub `_execute` |
| Step 9 checklist marked `[DONE]` in your runbook | `real_execute()` exists but is dead code (line 60 still calls `_execute`) |
| Full stub loop tested: model → tool → Postgres | No `requirements.txt` in repo |
| `real_execute()` already written per converge instructions | Contract typo: `cypto_detected` in `TOOL_OUTPUT_KEYS` |
| | DB password hardcoded as `changeme` in `db.py` |
| | No end-to-end test with Stefan's real tools |

**Bottom line:** Your half works in isolation with fake data. Stefan landed his tools code on Jun 22. The critical path now is: Stefan deploys the lab → you wire `real_execute` → first real end-to-end run.

---

## The goal for these two weeks

1. **Week 1:** Fix small bugs, verify infrastructure still healthy, coordinate converge with Stefan.
2. **End of Week 1 / start of Week 2:** Converge day — swap stub for real tools, first real database row.
3. **Week 2:** Improve the agent, test all attack types, prepare for multi-step attack loops.

---

## Week 1 — Polish and prep for converge (Jun 25 – Jul 1)

### Day 1 (Thu Jun 25) — Infrastructure health check

Reconnect to MIDAS 2 and confirm everything you built in Step 9 still runs.

- [ ] `git pull` on `main` — confirm you have `adversary/tools/verify-lab-safety.sh` and `Instructions/lab_safety_checklist.md`.
- [ ] **Run `bash ../tools/verify-lab-safety.sh`** (from `brain/` or `tools/`). If Stefan's lab is not up yet, expect failures — use stub mode only until it passes.
- [ ] Check containers:
  ```bash
  docker ps --filter name=brain
  docker ps --filter name=records
  ```
- [ ] If `brain` or `records` stopped, restart them (commands in your runbook Steps 3–4).
- [ ] Verify brain is serving:
  ```bash
  curl http://localhost:8000/v1/models
  ```
- [ ] Verify database:
  ```bash
  docker exec -i records psql -U postgres -c "\d runs"
  ```
- [ ] Activate venv and run a quick stub test:
  ```bash
  cd ~/Summer_FAIR_PQC_Research/adversary/brain
  source venv/bin/activate
  python3 agent.py
  docker exec -i records psql -U postgres -c \
    "SELECT attack_name, outcome_notes FROM runs ORDER BY timestamp DESC LIMIT 1;"
  ```

**Done when:** A new `stub_` row appears and the model responds.

---

### Day 2 (Fri Jun 26) — Fix known bugs (small PR)

These are quick fixes that prevent converge-day confusion.

#### Fix 1: Contract typo in `contract.py`

Line 6 currently has `"cypto_detected"`. Change to `"crypto_detected"`:

```python
TOOL_OUTPUT_KEYS = ["attack_name", "crypto_detected", "attack_params", "outcome_notes"]
```

#### Fix 2: Typo in `agent.py` system prompt

Change `hostpital` → `hospital`.

#### Fix 3: Add `requirements.txt`

Create `adversary/brain/requirements.txt`:

```
pydantic-ai
psycopg[binary]
```

- [ ] Make all three fixes on branch `student2-brain`
- [ ] Commit and push:
  ```bash
  git add adversary/brain/contract.py adversary/brain/agent.py adversary/brain/requirements.txt
  git commit -m "Fix contract typo and add requirements.txt"
  git push -u origin student2-brain
  ```
- [ ] Open PR to `main`

**Done when:** PR merged or ready for review.

---

### Day 3 (Mon Jun 29) — Coordinate with Stefan

Stefan's blocker is deploying the lab on MIDAS 2 (his Step 9). You cannot converge until his containers run.

- [ ] Message Stefan (Teams) and confirm his timeline against `Instructions/stefan_next_two_weeks.md`.
- [ ] Ask specifically:
  - Are `practice-target` and `attacker` running?
  - Did all three `docker exec` tool tests pass?
  - When can you do converge (target: Thu Jul 2 or Fri Jul 3)?
- [ ] While waiting, read Stefan's `tools.py` and confirm it prints the four keys your `RunRecord` expects.

**Done when:** Converge date is scheduled and Stefan confirms tools are tested.

---

### Days 4–5 (Tue–Wed Jun 30 – Jul 1) — Prep the converge change

Do not merge the converge change until Stefan's lab is verified. But prepare it locally so converge day is fast.

#### Option A (recommended): Environment variable toggle

Replace the stub/real split with a flag so you can test both modes:

```python
import os

USE_REAL_TOOLS = os.environ.get("USE_REAL_TOOLS", "0") == "1"

def _execute(target: str, attack: str) -> dict:
    if USE_REAL_TOOLS:
        return real_execute(target, attack)
    return {
        "attack_name": f"stub_{attack}",
        "crypto_detected": "TLSv1.3 / TLS_AES_256_GCM_SHA384",
        "attack_params": {"target": target, "attack": attack},
        "outcome_notes": "STUB result — set USE_REAL_TOOLS=1 for real tools.",
    }
```

This lets you:
- Develop with stubs: `python3 agent.py`
- Converge with real tools: `USE_REAL_TOOLS=1 python3 agent.py`

#### Option B (runbook approach): Direct swap

Change line 60 in `agent.py` from `_execute` to `real_execute` and delete the stub function.

- [ ] Implement Option A or B locally (do not push converge wiring until Stefan is ready, unless using Option A with default `0`)
- [ ] If using Option A, commit the toggle on `student2-brain` — it's safe because default is stub mode.

**Done when:** Converge change is coded and ready to flip.

---

## Converge day (Thu Jul 2 or Fri Jul 3) — ~1 hour with Stefan

### Pre-flight (you do this first)

```bash
docker ps    # brain, records, practice-target, attacker all running
curl http://localhost:8000/v1/models
cd ~/Summer_FAIR_PQC_Research/adversary/tools && bash verify-lab-safety.sh
```

All safety checks must **PASS** before enabling real tools.

### Converge steps

1. [ ] Stefan demonstrates all three tools returning clean JSON.
2. [ ] Confirm JSON keys match your `contract.py` (`crypto_detected`, not `cypto_detected`).
3. [ ] Enable real tools:
   - **Option A:** `USE_REAL_TOOLS=1 python3 agent.py`
   - **Option B:** Change `run_attack` to call `real_execute`, commit on branch `converge`
4. [ ] Watch the agent run. It should call Stefan's tool via `docker exec`.
5. [ ] Verify a real row in Postgres:
   ```bash
   docker exec -i records psql -U postgres -c \
     "SELECT attack_name, crypto_detected, outcome_notes FROM runs ORDER BY timestamp DESC LIMIT 3;"
   ```
   Expected: `tls_probe`, `pcap_replay`, or `scapy_syn_probe` — **not** `stub_detect`.
6. [ ] Commit and push:
   ```bash
   git checkout -b converge
   git add adversary/brain/agent.py
   git commit -m "Wire agent to real tools — first end-to-end run"
   git push -u origin converge
   ```
7. [ ] Open PR to `main`. This commit is the project milestone.

### If converge breaks

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Could not parse tool output` | Extra stdout from `tools.py` | Stefan removes stray prints |
| `attacker` not found | Container not running | Stefan runs `start-lab.sh` or Day 3 commands |
| Model doesn't call tool | vLLM tool-calling flags | Check `--enable-auto-tool-choice --tool-call-parser hermes` on brain container |
| `stub_` row still appears | Wrong execute function called | Confirm `USE_REAL_TOOLS=1` or `real_execute` is wired |
| DB connection error | `records` container down | `docker start records` |

---

## Week 2 — Improve the agent (Jul 2 – Jul 9)

After converge, the adversary "works" but is still minimal: one tool call, one record, one report. Week 2 makes it more capable and production-ready.

### Days 6–7 (Jul 2–3) — Test all three attack types end-to-end

Run the agent three times with goals that steer it toward each attack:

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/brain
source venv/bin/activate
USE_REAL_TOOLS=1 python3 -c "
from agent import agent
agent.run_sync('Target practice-target:443. Run detect to inspect the TLS crypto and report.')
"
# Repeat with goals mentioning replay and craft
```

- [ ] Confirm `tls_probe` row from detect
- [ ] Confirm `pcap_replay` row from replay
- [ ] Confirm `scapy_syn_probe` row from craft
- [ ] Log any cases where the model picks the wrong attack or fails to call the tool

**Done when:** All three attack types produce real database rows.

---

### Day 8 (Mon Jul 6) — Move secrets to `.env`

Hardcoded `changeme` in `db.py` is fine for the lab but should not stay in committed code.

- [ ] Create `adversary/brain/.env` (gitignored):
  ```
  POSTGRES_PASSWORD=your_real_password
  ```
- [ ] Update `db.py` to read from environment:
  ```python
  import os
  DSN = f"host=localhost port=5432 dbname=postgres user=postgres password={os.environ.get('POSTGRES_PASSWORD', 'changeme')}"
  ```
- [ ] Document in a one-line comment: "Set POSTGRES_PASSWORD in .env"
- [ ] Commit `db.py` change (not `.env`)

---

### Days 9–10 (Jul 7–9) — Multi-step agent loop (stretch toward Q1)

The current agent calls one tool per run. The project eventually needs: detect crypto → choose attack → run attack → grade result. Start the first expansion:

- [ ] Update `main()` to accept a CLI goal argument:
  ```python
  import sys
  def main():
      goal = sys.argv[1] if len(sys.argv) > 1 else (
          "Target practice-target:443. Detect the crypto, then run one further attack, then summarize."
      )
      result = agent.run_sync(goal)
      print("\n--- agent report ---\n", result.output)
  ```
- [ ] Change the system prompt to allow **two** tool calls when the goal requires detect-then-attack:
  ```
  Given a target, you may call run_attack up to twice: first 'detect' to inspect crypto,
  then one of 'replay' or 'craft' based on what you learned. Save happens automatically.
  ```
- [ ] Test a two-step run and confirm **two** rows in Postgres (one `tls_probe`, one follow-up).
- [ ] Commit on `student2-brain`, open PR.

**Done when:** Agent can detect then attack in one session with two saved records.

---

## Git workflow reminder

```bash
git checkout main && git pull
git checkout student2-brain
# ... make changes in adversary/brain/ only ...
git add adversary/brain/
git commit -m "Enable multi-step attack loop"
git push -u origin student2-brain
```

**You own `contract.py`.** If keys ever need to change, change them once in your folder and tell Stefan.

**Never commit:** `venv/`, `.env`, `pgdata/`

---

## Success criteria (end of Jul 9)

- [ ] `verify-lab-safety.sh` run at start of every MIDAS session before real tool use
- [ ] Contract typo fixed, `requirements.txt` added
- [ ] Converge completed — real tool rows in Postgres
- [ ] All three attack types tested end-to-end with real tools
- [ ] DB password moved to `.env` (not in committed code)
- [ ] Agent supports at least a detect-then-attack two-step loop
- [ ] Converge PR merged to `main`

---

## Who to ask for help

| Issue | Contact |
|-------|---------|
| Stefan's containers / tool output | Stefan |
| GPU / vLLM / Docker | Server admin (Dr. Zareen / Teams) |
| Contract changes affecting Stefan's tools | Stefan (coordinate before changing keys) |
| Git / PR / converge process | Dr. Zareen |

---

## What comes after these two weeks

The adversary agent will need a **grading** component (did the attack succeed? was crypto broken?) — that's the second agent mentioned in the README. After your two-step loop works, the next build target is likely:

1. A grading function that reads `RunRecord` and assigns success/failure.
2. Wiring the adversary to attack a real hospital service (once the `lab/` folder exists).
3. Handing results to the orchestrator (planned `orchestrator/` folder).

Your records in Postgres are the foundation for all of that — every experiment loop produces one row your schema already supports.
