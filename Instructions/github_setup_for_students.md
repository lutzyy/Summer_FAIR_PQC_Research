# GitHub Setup for Students

This guide explains how to put your work into the project's GitHub repository and how the two of you work in it without overwriting each other. It builds directly on your two runbooks (`student1_tools_and_targets.md` and `student2_brain_and_records.md`) — those tell you *what to build*; this tells you *where the files live and how to share them*.

Read the whole thing once before you start. It's short, and the few rules here prevent the most common ways two people working in one repo step on each other.

---

## Why we use GitHub here

You're two people building two halves of one program. GitHub is the single shared place where both halves live, so that:

- there's one source of truth for the code (not files emailed back and forth),
- you can each work without overwriting the other's changes,
- the shared contract that makes your halves fit together can't quietly drift apart,
- and on converge day, joining your work is a clean, tracked step rather than a scramble.

Think of it as a shared workshop with a logbook: everyone works on their own bench, and every change is written down so nothing gets lost.

---

## One-time setup (do this once each)

### 1. Install Git

Git is the tool that talks to GitHub. Check if it's there:

```bash
git --version
```

If not installed:

```bash
sudo apt-get install -y git
```

### 2. Tell Git who you are

This stamps your name on your changes:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3. Get access to the repository

Ask the project owner to add your GitHub account as a collaborator on the repo. Then set up authentication so Git can push your work. The simplest path:

- Create a **Personal Access Token** on GitHub: Settings → Developer settings → Personal access tokens → generate one with `repo` access.
- When Git asks for a password while pushing, paste the **token** (not your GitHub password — password pushing no longer works).

(If you prefer, you can set up an SSH key instead — GitHub's docs walk through it — but the token is the quickest way to get going.)

### 4. Clone the repository

"Cloning" downloads a working copy of the repo to the server. Pick a home for it:

```bash
cd ~
git clone https://github.com/<owner>/pqc-hospital-testbed.git
cd pqc-hospital-testbed
```

You now have the whole project on disk. This folder — `~/pqc-hospital-testbed` — replaces the `~/redteam` folder mentioned in your runbook. (See "Mapping your runbook to the repo" below.)

---

## Where your files go

The repo is organized so each of you owns a clear folder. Put your work only in your folder.

```
pqc-hospital-testbed/
└── adversary/
    ├── tools/        <-- STUDENT 1 works here
    │   ├── Dockerfile
    │   ├── tools.py
    │   ├── nginx.conf
    │   └── captures/        (your pcaps live here but are NOT committed — see below)
    └── brain/        <-- STUDENT 2 works here
        ├── contract.py      (the shared contract — see below)
        ├── agent.py
        ├── db.py
        └── schema.sql
```

- **Student 1**, everything from your runbook goes in `adversary/tools/`: your `Dockerfile`, `tools.py`, and `nginx.conf`. Your capture files go in `adversary/tools/captures/` on disk, but they are **not** committed to GitHub (they're large and sensitive — see the next section).
- **Student 2**, everything from your runbook goes in `adversary/brain/`: `contract.py`, `agent.py`, `db.py`, and a `schema.sql` file holding the `CREATE TABLE` statement from your runbook.

### The shared contract — now a single file

Your runbooks each told you to keep your own copy of `contract.py` and check that they match. In the repo we do better: there is **one** `contract.py`, at `adversary/brain/contract.py`, and it is the single source of truth. Student 2's code imports it directly. Student 1 doesn't import it — your tools just need to print the four keys it defines (`attack_name`, `crypto_detected`, `attack_params`, `outcome_notes`). One file means it can never drift. If those keys ever need to change, change them there, once, and tell each other.

---

## What must NEVER be committed

Some files must stay out of GitHub — because they're secret, huge, or machine-specific. The repo includes a `.gitignore` file that tells Git to skip them. **Before your first commit, confirm `.gitignore` exists at the repo root and contains at least this:**

```gitignore
# Python
__pycache__/
*.pyc
venv/
.venv/

# Secrets and keys — NEVER commit these
.env
*.pem
*.key
target-certs/

# Large or sensitive data
captures/
*.pcap
pgdata/

# Editor noise
.DS_Store
```

Why each matters:

- **`venv/`** — Student 2's Python environment; it's machine-specific and large. Each person makes their own.
- **`.env`, `*.pem`, `*.key`, `target-certs/`** — passwords and private keys. Committing a secret to GitHub is a real security incident, even in a private repo. The Postgres password (`changeme` in your runbook) should be moved into a `.env` file that stays out of Git.
- **`captures/`, `*.pcap`, `pgdata/`** — the botnet captures and the database's data directory are large and not meant to be shared through Git.

If you're ever unsure whether something is safe to commit, ask before you push. It's much easier to never commit a secret than to remove one after the fact.

---

## Mapping your runbook to the repo

Your runbooks use `~/redteam` as the working folder and `/opt/redteam` as the path inside the attacker container. Now that you work inside the clone, here's the only adjustment:

- **Your working folder** is now your part of the clone:
  - Student 1: `~/pqc-hospital-testbed/adversary/tools`
  - Student 2: `~/pqc-hospital-testbed/adversary/brain`
- **Student 1's container mount** — run your `docker build` and `docker run` from inside `adversary/tools`, and mount the current folder:
  ```bash
  cd ~/pqc-hospital-testbed/adversary/tools
  docker build -t redteam-attacker .
  docker run -d --name attacker --network lab-net \
    --cap-add=NET_RAW --cap-add=NET_ADMIN \
    -v "$PWD":/opt/redteam \
    redteam-attacker
  ```
  Everything else in your runbook works unchanged — the path inside the container is still `/opt/redteam`. Put your pcaps in `adversary/tools/captures/` and they appear at `/opt/redteam/captures/` inside the box.
- **Student 2's commands** — run your Python from inside `adversary/brain` (with your venv active) so `contract.py`, `agent.py`, and `db.py` sit together:
  ```bash
  cd ~/pqc-hospital-testbed/adversary/brain
  python3 -m venv venv          # venv is gitignored — it stays local
  source venv/bin/activate
  pip install pydantic-ai "psycopg[binary]"
  python3 agent.py
  ```

Nothing else about your runbooks changes.

---

## Your daily workflow

You each work on your own **branch** — a private line of changes — and merge into the shared `main` branch through a **pull request**. This is how two people avoid overwriting each other.

### First, make your branch (once)

```bash
git checkout main
git pull                                  # get the latest
git checkout -b student1-tools            # Student 1's branch
# (Student 2 uses:  git checkout -b student2-brain)
```

### Then, every time you've made progress

```bash
git add adversary/tools                   # stage your folder's changes (Student 1)
git commit -m "Add TLS detect tool"       # save a labeled snapshot
git push -u origin student1-tools         # send it to GitHub
```

Commit small and often, with short messages saying what you did. Each commit is a save point you can return to.

### When a piece is working, open a pull request

On GitHub, click **Compare & pull request** for your branch. This proposes merging your work into `main`. The other person (or the project owner) can glance at it and merge. Once merged, your work is part of the shared project.

### Keep up to date

Before starting work each day, pull the latest `main` into your branch so you're building on everyone's newest code:

```bash
git checkout main
git pull
git checkout student1-tools
git merge main
```

---

## Converge day in Git

When both halves work on their own branches, joining them is a tracked, low-drama step:

1. Merge both branches into `main` (through pull requests). Because Student 1's files live in `adversary/tools/` and Student 2's in `adversary/brain/`, they don't touch the same files — so there are no conflicts.
2. Make a converge branch: `git checkout -b converge`.
3. Apply the one change converge requires: in `adversary/brain/agent.py`, replace the fake `_execute` with the real version (the one that calls Student 1's tool via `docker exec`, shown at the end of Student 2's runbook).
4. Run the first real end-to-end attack. When a real row lands in the database, commit it: `git commit -m "Wire agent to real tools — first end-to-end run"`, push, and open a pull request into `main`.

That commit is the milestone — the moment the two halves become one working system, recorded in the project history.

---

## Quick command cheat sheet

```bash
git status                 # what have I changed?
git add <folder>           # stage changes to commit
git commit -m "message"    # save a snapshot with a label
git push                   # send commits to GitHub
git pull                   # get the latest from GitHub
git checkout -b <name>     # make and switch to a new branch
git checkout <name>        # switch to an existing branch
git log --oneline          # see the history of changes
```

If Git ever says something confusing or you're worried you'll lose work: stop and ask before running commands you're unsure about. Git almost never loses committed work, so committing often is your safety net.
