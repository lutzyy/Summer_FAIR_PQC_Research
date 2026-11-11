"""R1 evaluation helpers: agreement, kappa, confusion matrix, consistency."""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Sequence


LABELS = ("success", "failure", "inconclusive")


def confusion_matrix(
    y_true: Sequence[str], y_pred: Sequence[str], labels: Sequence[str] = LABELS
) -> dict[str, dict[str, int]]:
    matrix = {a: {b: 0 for b in labels} for a in labels}
    for t, p in zip(y_true, y_pred):
        t = t if t in matrix else "inconclusive"
        p = p if p in matrix[t] else "inconclusive"
        matrix[t][p] += 1
    return matrix


def agreement_rate(y_a: Sequence[str], y_b: Sequence[str]) -> float:
    if not y_a:
        return 0.0
    return sum(1 for a, b in zip(y_a, y_b) if a == b) / len(y_a)


def cohens_kappa(y_a: Sequence[str], y_b: Sequence[str], labels: Sequence[str] = LABELS) -> float:
    """Cohen's kappa for categorical labels."""
    n = len(y_a)
    if n == 0:
        return 0.0
    po = agreement_rate(y_a, y_b)
    ca = Counter(y_a)
    cb = Counter(y_b)
    pe = sum((ca[l] / n) * (cb[l] / n) for l in labels)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1.0 - pe)


def consistency_flip_rate(verdicts_per_run: Iterable[Sequence[str]]) -> float:
    """Fraction of runs whose repeated judgments are not all identical."""
    runs = list(verdicts_per_run)
    if not runs:
        return 0.0
    flips = sum(1 for vs in runs if len(set(vs)) > 1)
    return flips / len(runs)


def label_reliability_decision(
    *,
    gold_accuracy: float | None,
    kappa_vs_grader: float,
    flip_rate: float,
    min_gold_accuracy: float = 0.85,
    max_flip_rate: float = 0.10,
) -> dict:
    """
    Clear criterion: reliable enough to be the dataset label if
    - gold-subset accuracy >= 0.85 (when gold exists), else defer
    - consistency flip rate <= 0.10
    Agreement with the rule grader alone is NOT accuracy.
    """
    reasons = []
    met = True
    if gold_accuracy is None:
        met = False
        reasons.append("No gold subset accuracy yet — cannot claim label reliability.")
    elif gold_accuracy < min_gold_accuracy:
        met = False
        reasons.append(
            f"Gold accuracy {gold_accuracy:.3f} < {min_gold_accuracy} threshold."
        )
    else:
        reasons.append(f"Gold accuracy {gold_accuracy:.3f} meets threshold.")

    if flip_rate > max_flip_rate:
        met = False
        reasons.append(f"Consistency flip rate {flip_rate:.3f} > {max_flip_rate}.")
    else:
        reasons.append(f"Consistency flip rate {flip_rate:.3f} within budget.")

    reasons.append(
        f"Kappa vs rule grader={kappa_vs_grader:.3f} (informational; not the accuracy criterion)."
    )
    return {
        "reliable_enough_for_label": met,
        "criterion": {
            "min_gold_accuracy": min_gold_accuracy,
            "max_flip_rate": max_flip_rate,
            "note": "Agreement with rule grader is not accuracy.",
        },
        "reasons": reasons,
    }
