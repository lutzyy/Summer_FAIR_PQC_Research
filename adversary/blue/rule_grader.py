#!/usr/bin/env python3
"""
Provisional rule-based grader (Sebastian's grader is not in the repo yet).

Writes to `rule_based_grades` only. Never modifies `runs` or Blue Agent tables.
Replace with Sebastian's implementation when agreed — keep both label columns.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_BLUE = Path(__file__).resolve().parent
if str(_BLUE) not in sys.path:
    sys.path.insert(0, str(_BLUE))

from models import RuleGrade, Verdict  # noqa: E402

GRADER_VERSION = "provisional-v1"


def grade_run(run: dict[str, Any]) -> RuleGrade:
    attack = (run.get("attack_name") or "").strip()
    notes = (run.get("outcome_notes") or "").strip()
    crypto = run.get("crypto_detected")
    low = notes.lower()
    run_id = str(run.get("run_id") or "")

    if attack in ("", "none"):
        return RuleGrade(
            run_id=run_id,
            verdict=Verdict.FAILURE,
            rationale="No attack executed (attack_name empty/none).",
            grader_version=GRADER_VERSION,
        )

    if "tool error" in low or "could not parse" in low or "unknown attack" in low:
        return RuleGrade(
            run_id=run_id,
            verdict=Verdict.FAILURE,
            rationale=f"Tool-level failure in outcome_notes: {notes[:200]}",
            grader_version=GRADER_VERSION,
        )

    if attack == "tls_probe":
        handshake_ok = "handshake completed" in low
        crypto_ok = bool(crypto) and "unknown" not in str(crypto).split("/", 1)[0].lower()
        if handshake_ok or crypto_ok:
            return RuleGrade(
                run_id=run_id,
                verdict=Verdict.SUCCESS,
                rationale="tls_probe: handshake/crypto parameters recovered.",
                grader_version=GRADER_VERSION,
            )
        if "could not read handshake" in low:
            return RuleGrade(
                run_id=run_id,
                verdict=Verdict.FAILURE,
                rationale="tls_probe: handshake not readable.",
                grader_version=GRADER_VERSION,
            )
        return RuleGrade(
            run_id=run_id,
            verdict=Verdict.INCONCLUSIVE,
            rationale="tls_probe: ambiguous outcome_notes/crypto_detected.",
            grader_version=GRADER_VERSION,
        )

    if attack == "pcap_replay":
        if "tool error" in low or "no such file" in low:
            return RuleGrade(
                run_id=run_id,
                verdict=Verdict.FAILURE,
                rationale="pcap_replay: error in tool output.",
                grader_version=GRADER_VERSION,
            )
        if "replay finished" in low or "sent" in low or "packets" in low or notes:
            # Non-empty completion-ish notes → success per rubric (not a crypto break)
            return RuleGrade(
                run_id=run_id,
                verdict=Verdict.SUCCESS,
                rationale="pcap_replay: replay appears to have completed (tool-visible).",
                grader_version=GRADER_VERSION,
            )
        return RuleGrade(
            run_id=run_id,
            verdict=Verdict.INCONCLUSIVE,
            rationale="pcap_replay: empty or unclear notes.",
            grader_version=GRADER_VERSION,
        )

    if attack == "scapy_syn_probe":
        if re.search(r"responded with tcp flags", low):
            return RuleGrade(
                run_id=run_id,
                verdict=Verdict.SUCCESS,
                rationale="scapy_syn_probe: TCP response observed.",
                grader_version=GRADER_VERSION,
            )
        if "no response" in low:
            return RuleGrade(
                run_id=run_id,
                verdict=Verdict.FAILURE,
                rationale="scapy_syn_probe: no TCP response.",
                grader_version=GRADER_VERSION,
            )
        return RuleGrade(
            run_id=run_id,
            verdict=Verdict.INCONCLUSIVE,
            rationale="scapy_syn_probe: ambiguous notes.",
            grader_version=GRADER_VERSION,
        )

    return RuleGrade(
        run_id=run_id,
        verdict=Verdict.INCONCLUSIVE,
        rationale=f"No rule for attack_name={attack!r}.",
        grader_version=GRADER_VERSION,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Provisional rule-based grader")
    parser.add_argument("--run-id", help="Grade one run from Postgres")
    parser.add_argument(
        "--json-run",
        help="Path to a single RunRecord JSON file (offline)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Grade all runs in Postgres",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Persist grades to rule_based_grades",
    )
    args = parser.parse_args()

    runs: list[dict[str, Any]] = []
    if args.json_run:
        runs.append(json.loads(Path(args.json_run).read_text()))
    elif args.run_id or args.all:
        import db as blue_db

        if args.all:
            runs = blue_db.fetch_all_runs()
        else:
            row = blue_db.fetch_run(args.run_id)
            if not row:
                raise SystemExit(f"run not found: {args.run_id}")
            runs = [row]
    else:
        parser.error("Provide --run-id, --all, or --json-run")

    for run in runs:
        grade = grade_run(run)
        print(grade.model_dump_json())
        if args.save:
            import db as blue_db

            blue_db.save_rule_grade(grade)


if __name__ == "__main__":
    main()
