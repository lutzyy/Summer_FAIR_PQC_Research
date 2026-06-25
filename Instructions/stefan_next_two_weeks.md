# Stefan — Next Two Weeks (Jun 25 – Jul 9, 2026)

**Your role:** Tools & Targets (`adversary/tools/`)  
**Working folder:** `~/Summer_FAIR_PQC_Research/adversary/tools` on MIDAS 2  
**Runbook reference:** `Instructions/stefan_tools_and_targets (1).md`

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

## The goal for these two weeks

1. **Week 1:** Deploy and verify the sealed lab on MIDAS 2 (Steps 1–8 from your runbook).
2. **End of Week 1 / start of Week 2:** Converge day with Sebastian — first real end-to-end attack.
3. **Week 2:** Harden the lab, add a PQC practice target, and document how to start everything.

---

## Week 1 — Deploy and verify the lab (Jun 25 – Jul 1)

### Day 1 (Thu Jun 25) — Confirm access and folder setup

- [ ] Connect to MIDAS 2 via Cursor (see `Instructions/midas2_cursor_setup_guide.md`).
- [ ] `git pull` on `main` — confirm you see Sebastian's `adversary/brain/` files.
- [ ] Confirm Docker works:
  ```bash
  docker --version
  docker ps
  docker run --rm hello-world
  ```
- [ ] Go to your folder and create captures:
  ```bash
  cd ~/Summer_FAIR_PQC_Research/adversary/tools
  mkdir -p captures target-certs
  cp /shared/zareen_research/captures/mirai_capture.pcap ./captures/sample.pcap
  ```

**Done when:** `hello-world` runs without permission errors and `sample.pcap` exists locally.

---

### Day 2 (Fri Jun 26) — Sealed network and practice target

- [ ] Create the sealed network:
  ```bash
  docker network create --internal lab-net
  ```
  (If it already exists, skip — `docker network ls` to check.)
- [ ] Prove the wall works (this **must fail**):
  ```bash
  docker run --rm --network lab-net alpine ping -c 2 8.8.8.8
  ```
- [ ] Generate target TLS certs:
  ```bash
  openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout target-certs/key.pem \
    -out target-certs/cert.pem \
    -days 365 -subj "/CN=practice-target"
  ```
- [ ] Start `practice-target`:
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

- [ ] Build the attacker image:
  ```bash
  cd ~/Summer_FAIR_PQC_Research/adversary/tools
  docker build -t redteam-attacker .
  ```
- [ ] Start the attacker (sealed on `lab-net`):
  ```bash
  docker run -d --name attacker --network lab-net \
    --cap-add=NET_RAW --cap-add=NET_ADMIN \
    -v "$PWD":/opt/redteam \
    redteam-attacker
  ```
- [ ] Verify isolation:
  ```bash
  docker exec attacker ping -c 2 practice-target   # must SUCCEED
  docker exec attacker ping -c 2 8.8.8.8            # must FAIL
  ```

**Done when:** Attacker reaches the target but not the internet.

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

- [ ] `detect` returns a real TLS protocol and cipher (not `unknown / unknown`)
- [ ] `replay` completes without a tool error
- [ ] `craft` returns a TCP response note
- [ ] No extra lines printed before the JSON (Sebastian reads the **last** line of stdout)

**If something fails:** fix `tools.py` in Cursor and re-run — no rebuild needed (folder is mounted).

**Done when:** All three tools pass. Tick every item in Step 9 of your runbook.

---

### Day 5 (Wed Jul 1) — Prep for converge + message Sebastian

- [ ] Confirm all containers are still running: `docker ps` should show `practice-target` and `attacker`.
- [ ] Send Sebastian (or post in Teams) a short status:
  - Containers are up
  - All three tools tested and returning valid JSON
  - You're ready for converge
- [ ] Schedule converge for Thu Jul 2 or Fri Jul 3 (see Sebastian's doc — you both need to be on MIDAS 2 at the same time).

**Do not change your code for converge.** Sebastian's agent will call the exact `docker exec` commands you tested in Day 4.

---

## Converge day (Thu Jul 2 or Fri Jul 3) — ~1 hour with Sebastian

This is a joint milestone, not solo work.

### Your checklist on converge day

1. [ ] `docker ps` — `practice-target` and `attacker` are running.
2. [ ] Re-run one tool test live so Sebastian can see the JSON:
   ```bash
   docker exec attacker python3 /opt/redteam/tools.py detect practice-target:443
   ```
3. [ ] Confirm your JSON keys match `adversary/brain/contract.py` exactly.
4. [ ] Watch Sebastian run `python3 agent.py` with real tools wired in.
5. [ ] Confirm a **non-`stub_`** row appears in Postgres:
   ```bash
   docker exec -i records psql -U postgres -c \
     "SELECT attack_name, crypto_detected, outcome_notes FROM runs ORDER BY timestamp DESC LIMIT 3;"
   ```

### If converge breaks

| Symptom | Likely cause | Your fix |
|---------|--------------|----------|
| `attacker` container not found | Container stopped | `docker start attacker` or re-run Day 3 |
| JSON parse error | Extra stdout before JSON | Remove any `print()` calls in `tools.py` except the final `json.dumps` |
| Key mismatch | Wrong key names in output | Match exactly: `crypto_detected` not `cypto_detected` |
| `detect` returns unknown | Target not reachable | `docker exec attacker ping practice-target` |

---

## Week 2 — Harden and extend (Jul 2 – Jul 9)

After converge succeeds, shift from "get it working" to "make it reliable and ready for the next project phase."

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

echo "Lab ready. Test with:"
echo "  docker exec attacker python3 /opt/redteam/tools.py detect practice-target:443"
```

- [ ] Write and test `start-lab.sh`
- [ ] Add a matching `stop-lab.sh` (`docker stop practice-target attacker`)
- [ ] Commit on branch `student1-tools`, open PR to `main`

---

### Days 8–9 (Jul 6–7) — PQC practice target (stretch goal)

The runbook mentions swapping nginx for an Open Quantum Safe demo server later. This is the first step toward Q1 roadmap goals.

- [ ] Research the OQS demo server image or nginx + oqs-provider TLS config.
- [ ] Stand up a **second** target container (e.g. `practice-target-pqc`) on `lab-net` with post-quantum or hybrid TLS.
- [ ] Confirm `tools.py detect` reports the PQC cipher suite on the new target.
- [ ] Document the target name and port in a short `adversary/tools/README.md`.

**Done when:** `detect` against the PQC target returns a distinguishable cipher string in `crypto_detected`.

---

### Day 10 (Jul 8–9) — Additional captures and wrap-up

- [ ] Copy a second pcap from `/shared/zareen_research/captures/` (Bashlite or Torii) into `captures/`.
- [ ] Test replay with the new capture:
  ```bash
  docker exec attacker python3 /opt/redteam/tools.py replay practice-target:443 /opt/redteam/captures/bashlite.pcap
  ```
- [ ] Run a full end-to-end test with Sebastian's agent (all three attack types: detect, replay, craft).
- [ ] Update Step 9 checklist in your runbook to `[DONE]` and commit any doc updates.

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

## Success criteria (end of Jul 9)

- [ ] Step 9 checklist fully complete on MIDAS 2
- [ ] Converge completed — real rows (not `stub_`) in Postgres
- [ ] `start-lab.sh` lets anyone bring the lab up in one command
- [ ] At least one PQC or hybrid target tested (stretch)
- [ ] Second botnet capture tested with `replay`

---

## Who to ask for help

| Issue | Contact |
|-------|---------|
| Docker permission denied | Server admin (Dr. Zareen / Teams) |
| Contract / JSON key questions | Sebastian |
| MIDAS 2 / VPN access | Dr. Zareen |
| Git / PR questions | Dr. Zareen or Sebastian |

---

## What comes after these two weeks

Once the adversary loop is solid end-to-end, the project moves toward Q1 foundation goals: connecting the adversary to a simulated hospital (EHR, personas) and an orchestrator that records graded results. Your tools will eventually attack real hospital services, not just nginx — but the contract and sealed-lab pattern stay the same.
