# Stefan — Next Two Weeks (Jun 25 – Jul 9, 2026)

**Your role:** Tools & Targets (`adversary/tools/`)  
**Working folder:** `~/Summer_FAIR_PQC_Research/adversary/tools` on MIDAS 2  
**Runbook reference:** `Instructions/stefan_tools_and_targets (1).md`  
**Safety reference:** `Instructions/lab_safety_checklist.md`

---

## Safety first — every MIDAS 2 session

Before any attack, pcap replay, or lab work, run:

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/tools
bash verify-lab-safety.sh
```

**Run this again** whenever you add or change: a pcap, container, `tools.py`, `Dockerfile`, `nginx.conf`, certs, or network settings.

| Rule | Why |
|------|-----|
| Tools run **only** via `docker exec attacker` | Host is not sealed; pcaps must not execute on MIDAS 2 directly |
| `lab-net` must stay `--internal` | Blocks internet egress from the attack lab |
| Pcaps/certs **never** committed | Botnet captures stay on server only (gitignored) |
| Replay only at `practice-target` on `lab-net` | Traffic stays inside the fake hospital |

If the script prints **FAIL**, stop and fix before continuing.

---

## Where you are now

| Done | Not done yet |
|------|--------------|
| `Dockerfile`, `nginx.conf`, and `tools.py` committed to `main` (Jun 22) | Step 9 checklist — lab not verified on MIDAS 2 |
| Code matches the runbook template and contract keys | `lab-net`, `practice-target`, and `attacker` containers not evidenced in git |
| Root `.gitignore` expanded for certs, captures, venv | No startup script or run documentation for others |
| | Converge with Sebastian not completed |

**Bottom line:** Your *code* is in the repo. Your *lab environment* still needs to be stood up and tested on MIDAS 2 before Sebastian can wire his agent to your real tools.

Sebastian finished his brain half on Jun 20 and marked Step 9 done. His `agent.py` already has a `real_execute()` function ready — it is waiting on your containers running and your three tools returning clean JSON.

---

## The goal for these two weeks (prep only — no converge yet)

**Converge is scheduled for the week of July 13 with Dr. Zareen present.** Do not wire Sebastian's agent to your real tools before that session.

1. **Week 1 (Jun 25 – Jul 1):** Deploy and verify the sealed lab on MIDAS 2 (Steps 1–8 from your runbook).
2. **Week 2 (Jul 2 – Jul 9):** Harden the lab (`start-lab.sh`), optional PQC target, second pcap — stay ready for converge.
3. **Week of Jul 13:** Converge live with Dr. Zareen + Sebastian (see `Instructions/converge_day.md`).

---

## Week 1 — Deploy and verify the lab (Jun 25 – Jul 1)

### Day 1 (Thu Jun 25) — Confirm access and folder setup

- [DONE] Connect to MIDAS 2 via Cursor (see `Instructions/midas2_cursor_setup_guide.md`).
- [DONE] `git pull` on `main` — confirm you have `verify-lab-safety.sh` and the safety checklist.
- [DONE] After the lab is up (Days 2–3), run `bash verify-lab-safety.sh` — **repeat at the start of every future session**.
- [DONE] Confirm Docker works:
  ```bash
  docker --version
  docker ps
  docker run --rm hello-world
  ```
- [DONE] Go to your folder and create captures:
  ```bash
  cd ~/Summer_FAIR_PQC_Research/adversary/tools
  mkdir -p captures target-certs
  cp /shared/zareen_research/captures/mirai_capture.pcap ./captures/sample.pcap
  ```

**Done when:** `hello-world` runs without permission errors and `sample.pcap` exists locally.

---

### Day 2 (Fri Jun 26) — Sealed network and practice target

- [DONE] Create the sealed network:
  ```bash
  docker network create --internal lab-net
  ```
  (If it already exists, skip — `docker network ls` to check.)
- [DONE] Prove the wall works (this **must fail**):
  ```bash
  docker run --rm --network lab-net alpine ping -c 2 8.8.8.8
  ```
- [DONE] Generate target TLS certs:
  ```bash
  openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout target-certs/key.pem \
    -out target-certs/cert.pem \
    -days 365 -subj "/CN=practice-target"
  ```
- [DONE] Start `practice-target`:
  ```bash
  docker run -d --name practice-target --network lab-net \
    -v "$PWD/target-certs":/certs:ro \
    -v "$PWD/nginx.conf":/etc/nginx/nginx.conf:ro \
    nginx
  docker ps --filter name=practice-target
  ```

**Done when:** `practice-target` is running and the internet ping test fails.

---

### Day 3 (Mon Jun 29) — Build and run the attacker container

- [DONE] Build the attacker image:
  ```bash
  cd ~/Summer_FAIR_PQC_Research/adversary/tools
  docker build -t redteam-attacker .
  ```
- [DONE] Start the attacker (sealed on `lab-net`):
  ```bash
  docker run -d --name attacker --network lab-net \
    --cap-add=NET_RAW --cap-add=NET_ADMIN \
    -v "$PWD":/opt/redteam \
    redteam-attacker
  ```
- [DONE] Verify isolation:
  ```bash
  docker exec attacker ping -c 2 practice-target   # must SUCCEED
  docker exec attacker ping -c 2 8.8.8.8            # must FAIL
  ```
- [DONE] Run `bash verify-lab-safety.sh` — must pass before Day 4 tool tests.

**Done when:** Attacker reaches the target but not the internet, and safety script passes.

---

### Day 4 (Tue Jun 30) — Test all three tools by hand

This is the most important step. Run each command and confirm **one clean JSON line** with all four contract keys:

```bash
docker exec attacker python3 /opt/redteam/tools.py detect practice-target:443
docker exec attacker python3 /opt/redteam/tools.py replay practice-target:443 /opt/redteam/captures/sample.pcap
docker exec attacker python3 /opt/redteam/tools.py craft  practice-target:443
```

For each output, verify these keys exist and match `../brain/contract.py`:
- `attack_name`
- `crypto_detected`
- `attack_params` (must include `target`)
- `outcome_notes`

- [DONE] `detect` returns a real TLS protocol and cipher (not `unknown / unknown`)
- [DONE] `replay` completes without a tool error
- [DONE] `craft` returns a TCP response note
- [DONE] No extra lines printed before the JSON (Sebastian reads the **last** line of stdout)

**If something fails:** fix `tools.py` in Cursor and re-run — no rebuild needed (folder is mounted).

- [DONE] **After all three tool tests:** run `bash verify-lab-safety.sh` again (required after any code or pcap change).

**Done when:** All three tools pass and safety script passes. Tick every item in Step 9 of your runbook.

---

### Day 5 (Wed Jul 1) — Lab ready report (do not converge yet)

- [DONE] Confirm all containers are still running: `docker ps` should show `practice-target` and `attacker`.
- [DONE] Run `bash verify-lab-safety.sh` one final time.
- [DONE] Message Dr. Zareen and Sebastian on Teams:
  - Lab is up and safety checks pass
  - All three tools tested and returning valid JSON
  - You are ready for **converge week of July 13** (not before)

**Hold:** Do not run integration with Sebastian's real agent until the scheduled converge session with Dr. Zareen. See `Instructions/converge_day.md`.

---

## Week 2 — Harden the lab (Jul 2 – Jul 9)

**No converge this week.** Prepare everything so converge on **week of July 13** is a short, smooth session with Dr. Zareen.

### Days 6–7 (Jul 2–3) — Lab startup script

Create `adversary/tools/start-lab.sh` (commit this — no secrets inside):

```bash
#!/bin/bash
# Starts the sealed red-team lab. Run from adversary/tools/.
set -e
cd "$(dirname "$0")"

docker network inspect lab-net >/dev/null 2>&1 || docker network create --internal lab-net

if ! docker ps --filter name=practice-target --format '{{.Names}}' | grep -q practice-target; then
  docker run -d --name practice-target --network lab-net \
    -v "$PWD/target-certs":/certs:ro \
    -v "$PWD/nginx.conf":/etc/nginx/nginx.conf:ro \
    nginx
fi

if ! docker ps --filter name=attacker --format '{{.Names}}' | grep -q attacker; then
  docker run -d --name attacker --network lab-net \
    --cap-add=NET_RAW --cap-add=NET_ADMIN \
    -v "$PWD":/opt/redteam \
    redteam-attacker
fi

echo "Running safety checks..."
bash "$(dirname "$0")/verify-lab-safety.sh"
```

- [DONE] Write and test `start-lab.sh` (must call `verify-lab-safety.sh` at the end)
- [DONE] Add a matching `stop-lab.sh` (`docker stop practice-target attacker`)
- [DONE] Commit on branch `student1-tools`, open PR to `main`

---

### Days 8–9 (Jul 6–7) — PQC practice target (stretch goal)

The runbook mentions swapping nginx for an Open Quantum Safe demo server later. This is the first step toward Q1 roadmap goals.

- [DONE] Research the OQS demo server image or nginx + oqs-provider TLS config.
- [DONE] Stand up a **second** target container (e.g. `practice-target-pqc`) on `lab-net` with post-quantum or hybrid TLS.
- [DONE] Confirm `tools.py detect` reports the PQC cipher suite on the new target.
- [DONE] Document the target name and port in a short `adversary/tools/README.md`.

**Done when:** `detect` against the PQC target returns a distinguishable cipher string in `crypto_detected`.

---

### Day 10 (Jul 8–9) — Additional captures and wrap-up

- [ ] Copy a second pcap from `/shared/zareen_research/captures/` (Bashlite or Torii) into `captures/`.
- [ ] **Run `bash verify-lab-safety.sh` before first replay of the new pcap.**
- [ ] Test replay with the new capture:
  ```bash
  docker exec attacker python3 /opt/redteam/tools.py replay practice-target:443 /opt/redteam/captures/bashlite.pcap
  ```
- [ ] Re-run `bash verify-lab-safety.sh` after the new pcap test.
- [ ] Confirm lab still starts cleanly with `start-lab.sh` (containers may have stopped over the week — that's fine).
- [ ] Update Step 9 checklist in your runbook to `[DONE]`.

**Do not** run Sebastian's agent with real tools yet — that happens at converge (`Instructions/converge_day.md`).

---

## Git workflow reminder

```bash
git checkout main && git pull
git checkout student1-tools    # or create: git checkout -b student1-tools
# ... make changes in adversary/tools/ only ...
git add adversary/tools/
git commit -m "Add lab startup script"
git push -u origin student1-tools
# Open PR on GitHub
```

**Never commit:** `target-certs/`, `captures/*.pcap`, `.env`, `*.pem`

---

## Success criteria (end of Jul 9 — prep complete)

- [ ] `verify-lab-safety.sh` passes reliably; `start-lab.sh` runs it automatically
- [ ] Step 9 checklist fully complete on MIDAS 2
- [ ] All three tools tested; optional PQC target and second pcap done
- [ ] Dr. Zareen notified: lab ready for converge **week of July 13**

**Not due until converge week:** real rows in Postgres, end-to-end run with Sebastian's agent.

---

## Converge week (Jul 13–19) — with Dr. Zareen

See **`Instructions/converge_day.md`** for the full session checklist.

**Your role:** Demo running lab, run `verify-lab-safety.sh`, demo one tool live. No code changes on your side.

**Before the session:** Run `start-lab.sh` (or start containers manually) so `practice-target` and `attacker` are up when Dr. Zareen joins.

---

## Who to ask for help

| Issue | Contact |
|-------|---------|
| Docker permission denied | Server admin (Dr. Zareen / Teams) |
| Contract / JSON key questions | Sebastian |
| MIDAS 2 / VPN access | Dr. Zareen |
| Git / PR questions | Dr. Zareen or Sebastian |

---

## What comes after converge (week of Jul 13+)

Once Dr. Zareen is present and the first end-to-end run succeeds, the project moves toward testing all attack types with the real agent, then Q1 foundation goals: connecting the adversary to a simulated hospital (EHR, personas) and an orchestrator that records graded results.
