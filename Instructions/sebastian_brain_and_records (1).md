# Sebastian — Brain & Records

**Your half of the red team agent.** You run the AI model, set up the database that stores every result, and build the agent that does the thinking — it decides what to attack, calls a tool, and saves a record. While you build, you use a *fake* tool so you don't depend on Stefan. At converge, you swap the fake tool for a one-line call into Stefan's sealed attacker box.

You and Stefan work independently. The only thing that has to line up is **the contract** below. Read it first.

> **Where you work.** Everything here runs on the **MIDAS 2** server, through **Cursor**. Connect Cursor to the server, open the project folder, and open a terminal (Ctrl+`); its prompt should read `yourusername@midas2`. Your working folder is your part of the cloned repo:
> ```
> cd ~/Summer_FAIR_PQC_Research/adversary/brain
> ```
> All of Sebastian's files (contract.py, agent.py, db.py, schema.sql, your venv) live in that `brain/` folder.

---

## The contract (read this first)

Stefan's tools each print **one line of JSON** with exactly these keys:

```json
{
  "attack_name": "tls_probe",
  "crypto_detected": "TLSv1.3 / TLS_AES_256_GCM_SHA384",
  "attack_params": {"target": "practice-target:443"},
  "outcome_notes": "Handshake completed."
}
```

Your agent reads that JSON and turns it into a database row. You own the single canonical copy of `contract.py` (Step 6), which lives in your `brain/` folder; Stefan's tools just match its keys.

---

## How your half fits the whole system

```
  [ practice-target ]      [ attacker ]      <-- Stefan's containers, sealed lab-net
       (Stefan)              (Stefan)            (no internet, no brain access)
             \                /
              \  docker exec /
               \            /
          [ agent.py ]                       <-- YOU: the only thing touching both sides
               /            \
              /              \
       localhost:8000    localhost:5432
       [ vLLM brain ]    [ Postgres records ]   <-- YOUR containers (normal networking)
            (you)             (you)
```

Your `vLLM` and `Postgres` containers use normal Docker networking with published ports, so your agent reaches them at `localhost`. **Never attach them to `lab-net`** — they must stay outside the sealed network. Your agent is the bridge: it talks to the brain and database on one side, and reaches into the sealed attacker box with `docker exec` on the other.

---

## Tools you'll use — what, why, and what's already set up

On MIDAS 2 you don't have admin rights, so the heavy pieces are provided for you and you just verify them. The only things you install yourself are two Python packages, inside your own virtual environment.

### Provided by the admin / already on MIDAS 2 — you only verify

- **Docker** — runs the model server and the database in containers. The admin installs it and adds you to the `docker` group. Confirm with `docker --version` and `docker ps` (no permission error).
- **GPU + drivers** — already working on MIDAS 2: **two NVIDIA A40 GPUs (~46 GB each)**, drivers installed. You don't touch these. The **NVIDIA Container Toolkit** (which lets Docker use the GPUs) is set up by the admin as part of installing Docker — you just verify `docker run --gpus all` can see a card.
- **Python 3.12 + venv** — already available on MIDAS 2. Nothing to install; you just create your environment.

### You install — inside your virtual environment only (no admin needed)

- **pydantic-ai** — the agent framework. It runs the "think, decide, call a tool" logic and talks to your local model. It pulls in the OpenAI-style client and pydantic automatically.
- **psycopg[binary]** — the PostgreSQL client, so your code can save records to the database.

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/brain
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pydantic-ai "psycopg[binary]"
```

### Pulled automatically as Docker images — no manual install

- **vllm/vllm-openai** — serves the AI model behind a standard API your agent calls. Uses the GPU.
- **postgres** — the database that stores every experiment record.

### Downloaded on first run — not an install you do

- **Qwen2.5-14B-Instruct** — the model's weights (~28 GB) download automatically the first time vLLM starts. That's the long first-run wait, not a step you run yourself. It fits comfortably on one A40.

---

## Step 1 — Confirm Docker works

First, check Docker is installed and you can reach it without `sudo`:

```bash
docker --version
docker ps
```

Then run the standard Docker self-test:

```bash
docker run --rm hello-world
```

You should see a **"Hello from Docker!"** message — that confirms Docker works for your account.

> If `docker ps` or `hello-world` says *permission denied*, you're not in the `docker` group yet — ask the admin to add you, then **log out and back in** (close your terminal and open a fresh one, or reconnect Cursor). Confirm with `groups` (it should list `docker`). Don't continue until `hello-world` runs cleanly.

---

## Step 2 — Confirm the GPU works through Docker

The two A40s and their drivers are already set up on MIDAS 2. Check the host sees them:

```bash
nvidia-smi
```

You should see **two A40** cards (~46 GB each). Then confirm Docker itself can reach a GPU:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

If that also shows the A40s, you're ready. You should see a table listing **both A40 cards** (`0 NVIDIA A40` and `1 NVIDIA A40`), each with about `46068MiB` of memory, idle and with no running processes — that's a fully working GPU passthrough. If `nvidia-smi` works on the host but the Docker version fails, the NVIDIA Container Toolkit isn't wired into Docker yet — flag it for the admin (it's part of the Docker setup), don't try to fix it yourself.

---

## Step 3 — Start the AI model (the brain)

This runs vLLM, which serves the model behind a standard API your agent can call. Because there are two A40s, you pin the model to **one** card (`device=0`) and leave the other free for the rest of the team. The tool-calling flags at the end are essential — without them, the agent's tools won't fire.

```bash
docker run -d --name brain --gpus '"device=0"' -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-14B-Instruct \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

The first run **downloads the model** (~28 GB) — this takes a while; that's normal. Watch the logs until it stops scrolling:

```bash
docker logs -f brain
```

When it settles, test it from another terminal:

```bash
curl http://localhost:8000/v1/models
```

If it prints the model name back, the brain is alive. (`Qwen2.5-14B-Instruct` fits easily on one ~46 GB A40 and is good at calling tools. If tool calls later don't fire, the `--tool-call-parser` is the first thing to check for your vLLM version.)

---

## Step 4 — Start the database (records)

This stores every attack result. It uses normal networking with a published port so your agent reaches it at `localhost:5432`. The data directory lives in your home folder (outside the repo, so it's never committed).

```bash
docker run -d --name records \
  -e POSTGRES_PASSWORD=changeme \
  -p 5432:5432 \
  -v ~/pgdata:/var/lib/postgresql/data \
  postgres
```

> Change `changeme` to a real password, and keep it out of GitHub (use a `.env` file, which `.gitignore` already excludes). If you change it here, change it in `db.py` (Step 6) too.

Give it a few seconds to start, then create the table that matches the contract:

```bash
docker exec -i records psql -U postgres -c "
CREATE TABLE IF NOT EXISTS runs (
  run_id          TEXT PRIMARY KEY,
  timestamp       TEXT,
  target          TEXT,
  crypto_detected TEXT,
  attack_name     TEXT,
  attack_params   JSONB,
  outcome_notes   TEXT
);"
```

Confirm the table exists:

```bash
docker exec -i records psql -U postgres -c "\d runs"
```

(Save that `CREATE TABLE` statement as `schema.sql` in your `brain/` folder so it's tracked in the repo.)

---

## Step 5 — Set up your Python workspace

If you didn't already do this in the "Tools you'll use" section above, create your isolated environment in your `brain/` folder:

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/brain
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pydantic-ai "psycopg[binary]"
```

`pydantic-ai` is the agent framework (it brings in the OpenAI-compatible client and pydantic). `psycopg[binary]` is the PostgreSQL client. Activate this environment (`source venv/bin/activate`) every time you work. The `venv/` folder is excluded from GitHub by `.gitignore`.

---

## Step 6 — Write the contract and the database helper

Two files in your `brain/` folder.

### `contract.py` (the single source of truth for both halves)

```python
"""Shared contract between Stefan (tools) and Sebastian (agent).
This is the one canonical copy, in adversary/brain/. Stefan's tools just match these keys.
"""
from datetime import datetime, timezone
from typing import Any
import uuid
from pydantic import BaseModel, Field

TOOL_OUTPUT_KEYS = ["attack_name", "crypto_detected", "attack_params", "outcome_notes"]

class RunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    target: str
    crypto_detected: str | None = None
    attack_name: str
    attack_params: dict[str, Any] = {}
    outcome_notes: str = ""
```

### `db.py`

```python
"""Saves a RunRecord to the Postgres 'records' container."""
import json
import psycopg
from contract import RunRecord

DSN = "host=localhost port=5432 dbname=postgres user=postgres password=changeme"

def save_record(rec: RunRecord) -> None:
    with psycopg.connect(DSN) as conn:
        conn.execute(
            """INSERT INTO runs
               (run_id, timestamp, target, crypto_detected,
                attack_name, attack_params, outcome_notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (rec.run_id, rec.timestamp, rec.target, rec.crypto_detected,
             rec.attack_name, json.dumps(rec.attack_params), rec.outcome_notes),
        )
        conn.commit()
```

Quick test that the database path works end to end (with your venv active):

```bash
python3 -c "from contract import RunRecord; from db import save_record; \
save_record(RunRecord(target='test', attack_name='manual_test', outcome_notes='hello')); \
print('saved')"
docker exec -i records psql -U postgres -c "SELECT run_id, attack_name FROM runs;"
```

You should see your `manual_test` row. If so, your records half works.

---

## Step 7 — Build the agent (with a fake tool for now)

This is the heart of your half. The agent connects to your local model, has one tool, and when given a goal it *thinks*, *calls the tool*, and the tool *saves a record* as a guaranteed side effect.

While building, the tool's `_execute` function returns **fake** data — so you can test the full think → call → save loop without Stefan's container existing yet.

### `agent.py`

```python
"""The red team adversary agent. Runs on the host.
Thinks with the local model, calls one attack tool, saves a record."""
import json, subprocess
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from contract import RunRecord
from db import save_record

MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct"

model = OpenAIChatModel(
    MODEL_NAME,
    provider=OpenAIProvider(base_url="http://localhost:8000/v1", api_key="not-needed"),
)

agent = Agent(
    model,
    system_prompt=(
        "You are a red-team adversary operating ONLY against an isolated practice "
        "hospital in a lab. Given a target, decide on one attack, call the run_attack "
        "tool exactly once, then briefly report what happened. Never act on anything "
        "other than the target you are given."
    ),
)


# ---- The bridge to the attacker. FAKE for now; real version at converge. ----
def _execute(target: str, attack: str) -> dict:
    return {
        "attack_name": f"stub_{attack}",
        "crypto_detected": "TLSv1.3 / TLS_AES_256_GCM_SHA384",
        "attack_params": {"target": target, "attack": attack},
        "outcome_notes": "STUB result — replace _execute at converge.",
    }
# -----------------------------------------------------------------------------


@agent.tool_plain
def run_attack(target: str, attack: str) -> str:
    """Run ONE attack against the target and record the result.
    attack must be one of: 'detect', 'replay', 'craft'."""
    result = _execute(target, attack)
    rec = RunRecord(
        target=target,
        crypto_detected=result.get("crypto_detected"),
        attack_name=result["attack_name"],
        attack_params=result.get("attack_params", {}),
        outcome_notes=result.get("outcome_notes", ""),
    )
    save_record(rec)
    return result["outcome_notes"]


def main():
    goal = ("Target practice-target:443. First detect the crypto, then run one "
            "attack you judge appropriate, then report what happened.")
    result = agent.run_sync(goal)
    print("\n--- agent report ---\n", result.output)


if __name__ == "__main__":
    main()
```

The key design choice: the tool **saves the record itself**, then returns a short note to the model. That way a record is guaranteed for every tool call, and you don't depend on parsing the model's chatter.

---

## Step 8 — Test the whole loop

With `brain` and `records` running and your venv active:

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/brain
source venv/bin/activate
python3 agent.py
```

Watch it: the model reads the goal, calls `run_attack`, the tool saves a record and returns a note, and the model prints a short report. Then confirm a row landed:

```bash
docker exec -i records psql -U postgres -c \
  "SELECT attack_name, crypto_detected, outcome_notes FROM runs ORDER BY timestamp DESC LIMIT 3;"
```

You should see a `stub_...` row. That means your full half works: thinking → tool call → saved record. The data is fake, but the machine is real.

---

## Step 9 — You're done when you can tick all of these

- [ ] `docker --version` / `docker ps` work, and `docker run --gpus all` sees an A40
- [ ] `brain` is serving — `curl localhost:8000/v1/models` returns the model name
- [ ] `records` is running and the `runs` table exists
- [ ] Your venv has `pydantic-ai` and `psycopg`
- [ ] A manual `save_record` test inserts a row
- [ ] `python3 agent.py` runs: the model calls the tool and a `stub_` row appears
- [ ] Your `contract.py` is the one both halves rely on

---

## Converge day — connecting to Stefan's real tools

This is a **one-function change**. Replace the fake `_execute` in `agent.py` with the real version that calls Stefan's tool inside the sealed attacker container:

```python
def _execute(target: str, attack: str) -> dict:
    args = {
        "detect": ["detect", target],
        "replay": ["replay", target, "/opt/redteam/captures/sample.pcap"],
        "craft":  ["craft", target],
    }.get(attack)
    if not args:
        return {"attack_name": "none", "crypto_detected": None,
                "attack_params": {"attack": attack},
                "outcome_notes": f"Unknown attack: {attack}"}
    proc = subprocess.run(
        ["docker", "exec", "attacker", "python3", "/opt/redteam/tools.py", *args],
        capture_output=True, text=True, timeout=120,
    )
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {"attack_name": attack, "crypto_detected": None,
                "attack_params": {"target": target},
                "outcome_notes": f"Could not parse tool output: {e}; raw: {proc.stdout[-300:]}"}
```

Everything else stays the same — the tool still builds a `RunRecord` and saves it. Because Stefan's tools print the same JSON keys your `RunRecord` expects, it just works.

Steps for the day:
1. Confirm Stefan's tools output the keys defined in your `contract.py`.
2. Make sure Stefan's `attacker` and `practice-target` containers are running (`docker ps`).
3. Swap in the real `_execute` above and run `python3 agent.py`.
4. Watch the first real run: the agent detects the crypto on the live target, picks an attack, runs *Stefan's* tool through `docker exec`, and a real row appears in the database. That's the milestone — the full system, end to end.

If it breaks, it's almost always the contract (key names) or extra text on the tool's stdout (your code reads the **last** line, which absorbs most stray output). Both are quick fixes.
