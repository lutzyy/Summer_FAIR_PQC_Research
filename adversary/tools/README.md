# Adversary tools (Student 1)

Sealed red-team lab targets and probes. Run everything from this directory on MIDAS 2.

## Lab network

| Resource | Value |
|----------|--------|
| Network | `lab-net` (Docker `--internal`, no internet) |
| Attacker container | `attacker` (image `redteam-attacker`) |

## Practice targets

| Name | Port | Image | TLS |
|------|------|--------|-----|
| `practice-target` | **443** | stock `nginx` + local `nginx.conf` / `target-certs/` | Classical (RSA cert; TLS 1.3) |
| `practice-target-pqc` | **4433** | [`openquantumsafe/nginx`](https://hub.docker.com/r/openquantumsafe/nginx) | Post-quantum / hybrid (OQS + OpenSSL 3; ML-DSA cert, hybrid key share) |

Both targets must stay on **`lab-net` only**. Do not publish ports to the host for attack demos.

### Why two targets?

- Classical `practice-target:443` — first tool target from the runbook.
- PQC `practice-target-pqc:4433` — Open Quantum Safe demo nginx (nginx + **oqs-provider** / PQ stack in a prebuilt image). Use this for Q1-style PQC migration experiments.

## Start / stop

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/tools
bash start-lab.sh          # lab-net + classical + PQC + attacker, then safety checks
bash verify-lab-safety.sh  # re-run anytime
bash stop-lab.sh
```

First time (or after Dockerfile changes):

```bash
docker build -t redteam-attacker .
docker pull openquantumsafe/nginx   # PQC demo server
```

## Detect crypto

```bash
docker exec attacker python3 /opt/redteam/tools.py detect practice-target:443
docker exec attacker python3 /opt/redteam/tools.py detect practice-target-pqc:4433
```

`crypto_detected` includes protocol, ciphersuite, TLS 1.3 group, and certificate signature type so the targets are distinguishable, for example:

- Classical: `… / group=X25519MLKEM768 / sig=rsa_pss_rsae_sha256`
- PQC OQS: `… / group=X25519MLKEM768 / sig=mldsa65`

(Exact group may vary with client OpenSSL; the **`sig=mldsa65`** vs RSA signature is the clear PQC marker for the OQS demo cert.)

## Research note (OQS vs DIY)

| Approach | Choice for this lab |
|----------|---------------------|
| **OQS demo image** `openquantumsafe/nginx` | **Used** — fastest path; OpenSSL 3 + PQ already wired; listens on **4433** |
| DIY nginx + oqs-provider | Deferred — same idea, more build/config work |

Optional client for manual PQ checks: `openquantumsafe/curl` on `lab-net` (not required for `tools.py` when the attacker OpenSSL is 3.5+).

## Safety

- Replay and craft only against lab targets (`practice-target:443`, `practice-target-pqc:4433`).
- Never commit `captures/`, `*.pcap`, `target-certs/`, or `*.pem` (see repo `.gitignore`).
