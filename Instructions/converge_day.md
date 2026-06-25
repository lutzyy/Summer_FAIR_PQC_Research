# Converge day — week of July 13, 2026

**Do not converge before this week.** Stefan and Sebastian prepare their halves separately through **July 9**. The live integration happens **one session in the week of July 13** with **Dr. Zareen present** on MIDAS 2 (or on a scheduled video call with both students on the server).

Converge is when the two halves become one system: Sebastian's agent calls Stefan's real tools and a **non-`stub_`** row lands in Postgres.

---

## Before converge (students — complete by Jul 9)

### Stefan must have done:
- [ ] `lab-net`, `practice-target`, and `attacker` running on MIDAS 2
- [ ] All three tools tested via `docker exec` (detect, replay, craft)
- [ ] `bash verify-lab-safety.sh` passes
- [ ] `start-lab.sh` written and tested (recommended)

### Sebastian must have done:
- [ ] `brain` and `records` containers running
- [ ] Contract typo fixed (`crypto_detected`), `requirements.txt` added
- [ ] Converge wiring prepared locally (`USE_REAL_TOOLS` toggle or `real_execute` ready) — **not enabled on `main` until converge day**
- [ ] Stub loop still works (`python3 agent.py` without real tools)

### Dr. Zareen schedules:
- [ ] One ~1 hour slot during **Jul 13–19** when all three are available
- [ ] Confirms both students have MIDAS 2 access that day

---

## Converge session (~1 hour)

### 1. Safety check (everyone)

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/tools
bash verify-lab-safety.sh
```

**Stop if any check FAILs.** Fix before continuing.

### 2. Stefan demos his half (~15 min)

```bash
docker ps --filter name=practice-target
docker ps --filter name=attacker
docker exec attacker python3 /opt/redteam/tools.py detect practice-target:443
```

Confirm one clean JSON line with all four contract keys.

### 3. Sebastian verifies infrastructure (~10 min)

```bash
curl http://localhost:8000/v1/models
docker exec -i records psql -U postgres -c "\d runs"
```

### 4. Enable real tools and run (~20 min)

Sebastian (with Dr. Zareen watching):

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/brain
source venv/bin/activate
USE_REAL_TOOLS=1 python3 agent.py
```

Or apply the one-function swap from `sebastian_brain_and_records (1).md` if not using the toggle.

### 5. Confirm milestone (~5 min)

```bash
docker exec -i records psql -U postgres -c \
  "SELECT attack_name, crypto_detected, outcome_notes FROM runs ORDER BY timestamp DESC LIMIT 3;"
```

**Success:** a row with `tls_probe`, `pcap_replay`, or `scapy_syn_probe` — **not** `stub_detect`.

### 6. Commit (~10 min)

```bash
git checkout -b converge
git add adversary/brain/agent.py
git commit -m "Wire agent to real tools — first end-to-end run"
git push -u origin converge
```

Open PR to `main`. Dr. Zareen or students merge when checks pass.

---

## If something breaks

| Symptom | Who fixes |
|---------|-----------|
| Docker permission denied | Dr. Zareen (server admin) |
| GPU / vLLM not working | Dr. Zareen |
| `verify-lab-safety.sh` fails | Stefan |
| JSON parse error | Stefan (extra stdout in `tools.py`) |
| Key mismatch | Sebastian (`contract.py`) |
| `stub_` row still appears | Sebastian (real tools not enabled) |
| `attacker` not running | Stefan (`start-lab.sh` or manual start) |

---

## After converge

Students continue post-converge tasks in their instruction docs:
- Test all three attack types with real tools
- Multi-step agent loop (detect then attack)
- PQC target and additional pcaps (Stefan)
