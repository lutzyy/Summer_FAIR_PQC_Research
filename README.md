# Summer_FAIR_PQC_Research
Simulated hospital network and AI adversary for stress-testing post-quantum cryptography migration under attack.

## Overview

The cryptography that secures hospital networks today will eventually be broken by quantum computers. Migrating to post-quantum cryptography (PQC) is not a single switch — it's a long, connection-by-connection upgrade across a complex environment of clinical systems, medical devices, and patient services. The open research questions are practical ones: in what order should connections be upgraded, which algorithms hold up under real attack, and what are the performance and resilience trade-offs along the way?

This project builds a self-hosted, AI-orchestrated environment to answer those questions empirically. It simulates a hospital network where every connection uses cryptography that can be swapped between classical, post-quantum, and hybrid. An AI orchestrator decides what to upgrade and when, while an AI adversary attacks the network — including a simulated future quantum attacker. The output is a migration plan graded against attack outcomes.

Everything runs on our own hardware. No patient data is real, and no data leaves the network.

## How it works

The system runs the same four-step loop over and over. Each loop tests one combination of connection, cryptographic upgrade, and attack, and produces one graded result.

1. **Upgrade** — the orchestrator swaps in a post-quantum algorithm on one hospital connection.
2. **Run the hospital** — clinical personas and devices use the system like a normal day.
3. **Attack** — the adversary launches a realistic attack against the upgraded connection.
4. **Grade & learn** — did the attack succeed? Was performance still acceptable? The result feeds the next loop.

A full year of these loops produces a complete migration plan: which connections to upgrade first, which crypto choices held up, and where the trade-offs are.

## The three agent populations

- **Personas** — AI agents that behave like the people in a hospital (doctors, nurses, patients, admin staff), producing realistic clinical traffic rather than a synthetic load test. Predictable devices like infusion pumps stay scripted.
- **Orchestrator (the brain)** — catalogs every cryptographic connection, decides which to upgrade and in what order, runs the experiments, and learns from the results.
- **Adversary (the red team)** — picks from a library of realistic attacks and launches them against the network; a second agent watches and grades whether each attack worked. **This is the first component being built** (see Getting started).

## Architecture

Two isolated environments. Keeping them apart means an attack experiment can never reach the orchestrator.

**Brain — AI & orchestration**

| Role | Tools |
|------|-------|
| AI models | vLLM serving Llama / Qwen (self-hosted) |
| Agents | LangGraph + PydanticAI |
| Workflow | Prefect (schedules and reruns experiments) |
| Records | Postgres, Langfuse, Grafana |

**Lab — hospital + adversary**

| Role | Tools |
|------|-------|
| EHR | HAPI FHIR |
| Imaging / IoT | Orthanc, Mosquitto, HL7 |
| Crypto | oqs-provider for OpenSSL 3 (and native OpenSSL 3.5+) for post-quantum and hybrid TLS |
| Sensors | Zeek, Suricata |

## Data

- **Synthetic patients** — [Synthea](https://github.com/synthetichealth/synthea) (MITRE-funded, open source) generates realistic patient populations loaded into the EHR.
- **Real attack captures** — recorded IoT botnet traffic (Mirai, Bashlite, Torii) replayed against the network.
- **Realism references** — CIDDS, MAWILab, and HHS 405(d) used to confirm the testbed resembles a real hospital network.

## Hardware

- **Control** — a Mac mini used as the developer cockpit (remote access, dashboards, code). Not a compute node.
- **Server** — a Dell PowerEdge R7625 (dual AMD EPYC 9004, NVIDIA A40 48 GB GPU). Runs vLLM, the simulated hospital, the adversary, the sensors, and the records stack.

## Repository structure

```
pqc-hospital-testbed/
├── README.md
├── .gitignore
├── docs/                       # Build guides and onboarding
│   ├── student1_tools_and_targets.md
│   ├── student2_brain_and_records.md
│   └── github_setup_for_students.md
├── adversary/                  # The red team agent (current focus)
│   ├── tools/                  # Tools & targets  (Student 1)
│   │   ├── Dockerfile
│   │   ├── tools.py
│   │   ├── nginx.conf
│   │   └── captures/           # botnet pcaps (gitignored — not committed)
│   └── brain/                  # Agent & records  (Student 2)
│       ├── contract.py         # shared run-record contract (single source of truth)
│       ├── agent.py
│       ├── db.py
│       └── schema.sql
├── orchestrator/               # The brain: crypto inventory & migration decisions (planned)
├── lab/                        # The simulated hospital: EHR, imaging, devices (planned)
└── infra/                      # Compose files, network setup, shared infra (planned)
```

## Getting started

The first build target is the **adversary agent**. It's being built by two students working in parallel, then converging. Start with these guides in `docs/`:

- `student1_tools_and_targets.md` — builds the practice target, the sealed attacker, and the attack tools.
- `student2_brain_and_records.md` — runs the model, the database, and the thinking agent.
- `github_setup_for_students.md` — how to configure and commit your files in this repository.

The two halves meet through one shared contract (`adversary/brain/contract.py`): every tool emits the same four-field JSON record, and the agent stores it. As long as that contract holds, the pieces fit together.

**Safety:** Before every MIDAS 2 session or lab change, run `bash adversary/tools/verify-lab-safety.sh`. See `Instructions/lab_safety_checklist.md`.

## Roadmap

- **Q1 — Foundation:** servers and base infrastructure; one persona talking to one EHR; one attack running against it; the orchestrator records the result.
- **Q2 — Fill in the hospital:** more personas; synthetic patient population; full segmented network; five or more attack scenarios; automated crypto inventory.
- **Q3 — Close the loop:** the orchestrator proposes its own migration steps; quantum adversary simulator; methodology paper drafted; clinical review of personas.
- **Q4 — Output:** full migration plan generated and graded; final experiments at scale; paper submitted; documentation for the next team.

## Safety & isolation

The adversary runs inside a sealed network that can reach only the simulated hospital — never the orchestrator, the records, or the internet. All attacks target the lab environment only, and the botnet captures used are existing public recordings replayed in a contained setting. This is defensive security research: the goal is to measure resilience, not to produce attack tooling for use elsewhere.

## License

TBD.

