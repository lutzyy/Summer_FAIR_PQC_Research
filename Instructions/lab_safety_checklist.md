# Lab safety checklist — run every MIDAS 2 session

**Required:** Run this checklist **every time** you connect to MIDAS 2, and **again** after you add or change anything in the lab — a new pcap, container, config file, Docker image, network, or code under `adversary/tools/`.

Do **not** run attacks, replay pcaps, or enable real tools in the agent until every check passes.

**Converge (connecting Sebastian's agent to Stefan's real tools)** is scheduled for the **week of July 13, 2026, with Dr. Zareen present** — not before. See `Instructions/converge_day.md`.

---

## Why this matters

This project uses **recorded botnet traffic** (Mirai, Bashlite, Torii) and attack tools (packet replay, crafted probes). They are for **defensive research inside a sealed lab only**. The sealed network (`lab-net`) must never reach the internet, and sensitive files must never leak to GitHub.

**Python `venv` is not network isolation.** Only Docker containers on `lab-net` are sealed.

---

## Quick run (both students)

From the repo on MIDAS 2:

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/tools
bash verify-lab-safety.sh
```

If any check **FAILs**, stop and fix before continuing. Ask Dr. Zareen if a check fails and you are unsure why.

---

## The rules (never break these)

1. **Run tools only inside the `attacker` container** — always via `docker exec attacker ...`. Never run `tools.py` or `tcpreplay` directly on the MIDAS 2 host.
2. **Attack targets must be on `lab-net` only** — e.g. `practice-target:443`. Never point tools at hosts outside the lab.
3. **Pcap replay stays in the lab** — pcaps live in `captures/` (gitignored). Replay only from inside `attacker` against `practice-target`.
4. **Never commit** pcaps, certs, keys, or passwords — see root `.gitignore` (`captures/`, `*.pcap`, `target-certs/`, `.env`, `*.pem`).
5. **`brain` and `records` must never join `lab-net`** — Sebastian owns those; they stay on normal Docker networking with `localhost` ports only.
6. **Copy pcaps from the shared folder only** — do not download attack captures from the public internet onto MIDAS 2.

---

## Manual checks (if the script is unavailable)

### 1. Sealed network exists and is internal

```bash
docker network inspect lab-net --format '{{.Internal}}'
```

Expected: `true`

### 2. Lab containers are on `lab-net` only

```bash
docker inspect practice-target --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
docker inspect attacker --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
```

Expected: each prints `lab-net` only (for running containers).

### 3. Brain and database are NOT on `lab-net`

```bash
docker inspect brain --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>/dev/null || echo "brain not running"
docker inspect records --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>/dev/null || echo "records not running"
```

Expected: `bridge` or similar — **not** `lab-net`.

### 4. Attacker cannot reach the internet

```bash
docker exec attacker ping -c 2 8.8.8.8
```

Expected: **fails** (100% packet loss, bad address, or unreachable).

### 5. Attacker can reach the practice target only

```bash
docker exec attacker ping -c 2 practice-target
```

Expected: **succeeds** (replies received).

### 6. No sensitive files staged for git

```bash
cd ~/Summer_FAIR_PQC_Research
git status
```

Expected: no `captures/`, `*.pcap`, `target-certs/`, `.env`, or `*.pem` listed. If any appear, do **not** commit — fix `.gitignore` or unstage.

---

## After you add something new

| You added… | Re-run safety check? | Extra step |
|------------|----------------------|------------|
| New pcap in `captures/` | **Yes, before first replay** | Replay only via `docker exec attacker` |
| Changed `tools.py` / `Dockerfile` | **Yes** | Rebuild image if Dockerfile changed |
| New target container | **Yes** | New container must use `--network lab-net` only |
| Restarted containers | **Yes** | Confirm networks unchanged |
| Sebastian enabled real tools | **Yes** | Only at converge (week of Jul 13) with Dr. Zareen; Stefan confirms lab checks pass first |

---

## If a check fails

| Failure | Likely cause | Fix |
|---------|--------------|-----|
| Attacker reaches internet | Not on `lab-net`, or network not `--internal` | Recreate `lab-net` with `docker network create --internal lab-net` and reconnect containers |
| `brain` on `lab-net` | Wrong `docker run` | Recreate `brain` without `--network lab-net` |
| Pcap in `git status` | Accidental `git add` | `git reset` the file; confirm `.gitignore` |
| Tool works on host but not in container | Ran outside `attacker` | Use `docker exec attacker` only |

When in doubt, stop and ask before running replay or real agent attacks.
