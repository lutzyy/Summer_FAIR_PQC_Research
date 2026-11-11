# Orchestrator decision problem

Written before coding the selection strategy (spec §6).

## What it chooses

The next experiment: a pair `(crypto_config, attack)` from the enumerable config space in `orchestrator/config_space.py`, restricted to combinations marked **valid** for the current lab (practice targets + existing attack library).

## What it is trying to learn

Which **config factors** change attack outcomes:

- Key exchange class: classical / hybrid / pure PQC
- Authentication class: classical / PQC / hybrid
- Service/protocol (practice HTTPS now; FHIR/DICOM/MQTT later)
- Device constraint profile (when supported)
- Interaction with attack type

Outcome labels come from the **Blue Agent** (dataset label candidate), with the rule-based grader kept side by side for comparison — not as ground truth.

## When to stop

Stop when either:

1. **Budget:** `max_experiments` reached (default for lab sessions), or
2. **Confidence:** factor-importance ranks stabilize — top-k factor ordering unchanged for `patience` consecutive iterations (simulator / analysis).

## Framing (chosen approach)

**Active learning with a factor-aware acquisition score** (greedy reduction of outcome uncertainty across config factors), not full RL and not pure LLM reasoning for the first version.

### Why this framing

| Approach | Fit | Why accepted/rejected for v1 |
|----------|-----|------------------------------|
| Exhaustive fixed sweep | Baseline | Correct but sample-inefficient; is the ground truth for “what mattered” |
| Random sampling | Baseline | Simple control for sample-efficiency curves |
| Rules / checklist | Too brittle | Hardcodes migration beliefs we want to *discover* |
| Bandit (per-cell) | Possible | Ignores factor structure; treats each full config as an arm |
| RL | Overkill now | Needs a stable reward and many episodes; lab budget is small |
| LLM reasoning alone | Unsafe as sole chooser | Useful for explaining migration order later; not the selection kernel |
| **Factor-aware active learning** | **Chosen** | Directly targets R2: recover which factors matter with fewer experiments than a full sweep |

### Acquisition sketch

Maintain empirical success rates (and Beta posteriors) for each factor level from labeled outcomes. Score unevaluated valid cells by expected information about factor contrasts (disagreement between factor-level predictions + novelty). Pick the max-scoring cell; break ties with random among top scores.

## Baselines required

1. Full fixed sweep over all **valid** cells.
2. Random sampling without replacement under the same budget.

## Migration order (downstream)

After labeling, rank upgrades by estimated reduction in attack success (or risk) when moving a factor from classical → hybrid → PQC, producing an ordered recommendation with supporting experiment ids.
