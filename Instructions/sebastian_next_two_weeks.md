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

## The goal for these two weeks (prep only — no converge yet)

**Converge is scheduled for the week of July 13 with Dr. Zareen present.** Do not enable real tools or merge converge wiring to `main` before that session.

1. **Week 1 (Jun 25 – Jul 1):** Fix small bugs, verify infrastructure, prep converge code locally (stub mode only).
2. **Week 2 (Jul 2 – Jul 9):** `.env` for secrets, keep stub loop healthy, optional multi-step loop in **stub mode only**.
3. **Week of Jul 13:** Converge live with Dr. Zareen + Stefan (see `Instructions/converge_day.md`).

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

Stefan's blocker is deploying the lab on MIDAS 2 (his Step 9). You cannot converge until his containers run — and **converge itself waits until the week of July 13 with Dr. Zareen**.

- [ ] Message Stefan (Teams) and confirm his timeline against `Instructions/stefan_next_two_weeks.md`.
- [ ] Ask specifically:
  - Are `practice-target` and `attacker` running?
  - Did all three `docker exec` tool tests pass?
  - Does `verify-lab-safety.sh` pass?
- [ ] Tell Dr. Zareen when Stefan confirms lab-ready (converge scheduling happens for **Jul 13–19**).
- [ ] While waiting, read Stefan's `tools.py` and confirm it prints the four keys your `RunRecord` expects.

**Done when:** Stefan's lab is verified and you understand converge is **not** before Jul 13.

---

### Days 4–5 (Tue–Wed Jun 30 – Jul 1) — Prep the converge change (do not enable yet)

Prepare locally so converge week is fast. **Keep stub mode as the default until Dr. Zareen is present on Jul 13+.**

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
- Develop with stubs through Jul 9: `python3 agent.py`
- Converge with Dr. Zareen (Jul 13+): `USE_REAL_TOOLS=1 python3 agent.py`

#### Option B (runbook approach): Direct swap

Change line 60 in `agent.py` from `_execute` to `real_execute` — **only on converge day**, not before.

- [ ] Implement Option A or B locally
- [ ] If using Option A, you may commit the toggle on `student2-brain` — default stays stub (`USE_REAL_TOOLS=0`)
- [ ] **Do not** run `USE_REAL_TOOLS=1` or push a direct swap until the converge session with Dr. Zareen

**Done when:** Converge change is coded and ready to flip on Jul 13+.

---

## Week 2 — Prep and stub-only improvements (Jul 2 – Jul 9)

**No converge this week. No real tools.** Continue stub testing only until the session with Dr. Zareen.

### Days 6–7 (Jul 2–3) — Keep infrastructure healthy

- [ ] At each MIDAS session: confirm `brain` and `records` running, run stub `python3 agent.py`
- [ ] Confirm Stefan's lab status — he should finish Step 9 and `start-lab.sh` this week
- [ ] Do **not** enable real tools yet

**Done when:** Your stub loop still works and Stefan reports lab-ready.

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

### Days 9–10 (Jul 7–9) — Multi-step agent loop in stub mode (stretch)

Practice the detect-then-attack pattern using **stubs only** before converge:

- [ ] Update `main()` to accept a CLI goal argument (see previous template in this doc)
- [ ] Test a two-step stub run — confirm **two** `stub_` rows in Postgres
- [ ] Commit on `student2-brain`, open PR

**Done when:** Two-step stub loop works. Real two-step loop happens **after** converge.

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

## Success criteria (end of Jul 9 — prep complete)

- [ ] `verify-lab-safety.sh` run at start of every MIDAS session
- [ ] Contract typo fixed, `requirements.txt` added
- [ ] Converge wiring prepared (toggle or swap ready) — **still in stub mode**
- [ ] Stub loop and optional two-step stub loop work
- [ ] DB password moved to `.env` (stretch)

**Not due until converge week (Jul 13+):** real tool rows, end-to-end with Stefan, converge PR merged.

---

## Converge week (Jul 13–19) — with Dr. Zareen

See **`Instructions/converge_day.md`** for the full session checklist.

**Your role:** Enable real tools during the session (`USE_REAL_TOOLS=1` or swap to `real_execute`), run `agent.py`, confirm real Postgres row, open converge PR.

**Hold until this session:** Do not enable real tools on your own before Dr. Zareen is present.

### After converge (same week or following week)

- [ ] Test all three attack types (`detect`, `replay`, `craft`) with real tools
- [ ] Multi-step loop with real tools (detect then attack)
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

## What comes after converge (week of Jul 13+)

The adversary agent will need a **grading** component (did the attack succeed? was crypto broken?) — that's the second agent mentioned in the README. After the converge session with Dr. Zareen:

1. A grading function that reads `RunRecord` and assigns success/failure.
2. Wiring the adversary to attack a real hospital service (once the `lab/` folder exists).
3. Handing results to the orchestrator (planned `orchestrator/` folder).

Your records in Postgres are the foundation for all of that — every experiment loop produces one row your schema already supports.
