# Dataset v1 — crypto config × attack → outcome

## What this is

Each row is one experiment in the simulated hospital / practice-target lab:

> crypto configuration used by the target + attack that ran + whether it succeeded (+ run details)

Labels:

| Column | Meaning |
|--------|---------|
| `blue_agent_outcome` | Blue Agent verdict (`success` / `failure` / `inconclusive`) + confidence/rationale |
| `rule_based_outcome` | Provisional rule grader (Sebastian’s grader not yet in repo) |
| `gold_label` | Hand-adjudicated subset only (empty when not adjudicated) |

**Agreement with the rule grader is not accuracy.** Prefer `gold_label` for R1 accuracy claims.

## How it was collected

1. Red agent / tools produce `runs` rows under `adversary/brain/contract.py` (unchanged).
2. Blue Agent collectors gather evidence (tool output required; sensors optional/absent).
3. Blue Agent writes `blue_agent_judgments` (or offline fixture judgments during export).
4. Provisional rule grader writes `rule_based_grades` side by side — never overwrites Blue labels.
5. Orchestrator / sweep / random may set `selected_by` when experiments are scheduled that way.

Offline bootstrap (this Cloud Agent environment, no Docker/Postgres):

```bash
python dataset/export_dataset.py \
  --runs-json adversary/blue/fixtures/sample_runs.json \
  --out-csv dataset/v1/dataset_v1.csv
```

## Coverage (v1)

- Targets: `practice-target:443` (classical), `practice-target-pqc:4433` (OQS/PQC).
- Attacks: `tls_probe`, `pcap_replay`, `scapy_syn_probe`.
- Evidence default: tool output + inferred crypto config + rubric objective (**no Zeek/Suricata** in repo).
- Patient data: none in adversary practice targets; future EHR loads use Synthea (no PHI).

## What it does **not** cover

- Real “store now, decrypt later” quantum decryption — only lab-observable outcomes.
- FHIR / DICOM / MQTT services (config space marks them invalid until deployed).
- Constrained device profiles.
- Server TLS logs and network sensor evidence (collectors exist but report unavailable).
- Guaranteed Blue Agent label reliability — see R1 `label_reliability_decision` in eval output.

## Known label caveats

1. Provisional rule grader may disagree with a future Sebastian grader; both should be re-compared.
2. Heuristic Blue Agent mode (no vLLM) mirrors the rule grader and inflates agreement — use vLLM on MIDAS for R1.
3. Successful `tls_probe` means parameter recovery, not cryptographic break.
4. Successful `pcap_replay` means replay completed, not plaintext recovery.
5. `stderr` / process exit codes are not in the run contract; collectors cannot cite them.

## Export schema

See columns in `dataset/export_dataset.py` (`COLUMNS`). CSV and JSON under `dataset/v1/`; Parquet optional via `--out-parquet` (needs pandas/pyarrow).
