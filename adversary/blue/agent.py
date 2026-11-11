#!/usr/bin/env python3
"""
Blue Agent — observe a run, gather evidence, judge attack success.

Lab-only LLM: self-hosted vLLM (Llama/Qwen). Never call hosted OpenAI/Anthropic APIs.
Mirrors adversary/brain/agent.py wiring (OpenAI-compatible localhost:8000).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable

_BLUE = Path(__file__).resolve().parent
if str(_BLUE) not in sys.path:
    sys.path.insert(0, str(_BLUE))

from collectors.bundle import DEFAULT_SOURCES, collect_evidence  # noqa: E402
from langfuse_log import log_llm_call, prompt_version  # noqa: E402
from models import BlueJudgment, EvidenceBundle, EvidenceCitation, Verdict  # noqa: E402
from rule_grader import grade_run  # noqa: E402

MODEL_NAME = os.environ.get("BLUE_MODEL_NAME", "Qwen/Qwen2.5-14B-Instruct")
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
RUBRIC_VERSION = "v1"
PROMPT_VERSION = prompt_version()
TEMPERATURE = 0.0  # deterministic where possible


SYSTEM_PROMPT = """You are the Blue Agent for a sealed hospital PQC lab.
You judge whether an attack met its stated objective using ONLY the evidence provided.
You do not attack anything. You do not invent sensors or logs that are missing.
Respond with a single JSON object with keys:
  verdict: "success" | "failure" | "inconclusive"
  confidence: number from 0 to 1
  rationale: short text
  evidence_cited: list of {source, lines, note}
Use the rubric objective for this attack type. A completed TLS handshake is NOT a
crypto break unless the rubric says the probe objective was parameter recovery.
If evidence is missing or conflicting, prefer inconclusive over guessing.
"""


def _build_user_prompt(bundle: EvidenceBundle) -> str:
    return (
        f"prompt_version={PROMPT_VERSION}\nrubric_version={RUBRIC_VERSION}\n"
        f"run_id={bundle.run_id}\n"
        f"sources_enabled={bundle.sources_enabled}\n"
        f"sources_available={bundle.sources_available}\n\n"
        f"RUN RECORD:\n{json.dumps(bundle.run_record, indent=2)}\n\n"
        f"TOOL OUTPUT:\n{json.dumps(bundle.tool_output, indent=2)}\n\n"
        f"SERVER LOGS:\n{json.dumps(bundle.server_logs, indent=2)}\n\n"
        f"SENSOR LOGS:\n{json.dumps(bundle.sensor_logs, indent=2)}\n\n"
        f"CRYPTO CONFIG:\n{json.dumps(bundle.crypto_config, indent=2)}\n\n"
        f"ATTACK OBJECTIVE (rubric):\n{json.dumps(bundle.attack_objective, indent=2)}\n"
    )


def _parse_judgment_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def heuristic_judge(bundle: EvidenceBundle) -> BlueJudgment:
    """
    Offline/deterministic fallback when vLLM is unreachable.
    Aligns with the provisional rule grader on tool_output; used for CI and non-MIDAS.
    """
    run = bundle.run_record
    grade = grade_run(run)
    cited = [
        EvidenceCitation(
            source="tool_output",
            lines=[str(run.get("outcome_notes") or "")[:300]],
            note="heuristic_judge mirrored provisional rule grader",
        )
    ]
    return BlueJudgment(
        run_id=bundle.run_id,
        verdict=grade.verdict,
        confidence=0.55,
        rationale=f"[heuristic] {grade.rationale}",
        evidence_cited=cited,
        evidence_sources_used=list(bundle.sources_available),
        model="heuristic/rule_mirror",
        prompt_version=PROMPT_VERSION,
        rubric_version=RUBRIC_VERSION,
    )


def _vllm_available() -> bool:
    try:
        import urllib.request

        req = urllib.request.Request(f"{VLLM_BASE_URL}/models", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except Exception:
        return False


def llm_judge(bundle: EvidenceBundle) -> BlueJudgment:
    """Call self-hosted vLLM via OpenAI-compatible API (same pattern as red agent)."""
    user_prompt = _build_user_prompt(bundle)

    # Prefer pydantic-ai like the red agent; fall back to raw HTTP chat.completions.
    raw_text = ""
    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        model = OpenAIChatModel(
            MODEL_NAME,
            provider=OpenAIProvider(base_url=VLLM_BASE_URL, api_key="not-needed"),
            settings={"temperature": TEMPERATURE},
        )
        agent = Agent(model, system_prompt=SYSTEM_PROMPT, output_type=str)
        result = agent.run_sync(user_prompt)
        raw_text = result.output if hasattr(result, "output") else str(result)
    except Exception:
        import urllib.request

        body = json.dumps(
            {
                "model": MODEL_NAME,
                "temperature": TEMPERATURE,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            }
        ).encode()
        req = urllib.request.Request(
            f"{VLLM_BASE_URL}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode())
        raw_text = payload["choices"][0]["message"]["content"]

    trace_id = log_llm_call(
        run_id=bundle.run_id,
        model=MODEL_NAME,
        prompt=user_prompt,
        response=raw_text,
        metadata={"prompt_version": PROMPT_VERSION, "rubric_version": RUBRIC_VERSION},
    )
    data = _parse_judgment_json(raw_text)
    verdict = Verdict(str(data.get("verdict", "inconclusive")).lower())
    citations = []
    for item in data.get("evidence_cited") or []:
        if isinstance(item, dict):
            citations.append(
                EvidenceCitation(
                    source=str(item.get("source", "")),
                    lines=list(item.get("lines") or []),
                    note=str(item.get("note") or ""),
                )
            )
    return BlueJudgment(
        run_id=bundle.run_id,
        verdict=verdict,
        confidence=float(data.get("confidence", 0.5)),
        rationale=str(data.get("rationale") or ""),
        evidence_cited=citations,
        evidence_sources_used=list(bundle.sources_available),
        model=MODEL_NAME,
        prompt_version=PROMPT_VERSION,
        rubric_version=RUBRIC_VERSION,
        langfuse_trace_id=trace_id,
    )


def judge_run(
    run: dict[str, Any],
    *,
    enabled_sources: Iterable[str] | None = None,
    force_heuristic: bool | None = None,
) -> BlueJudgment:
    """Gather evidence for a run ID/record and return a structured judgment."""
    bundle = collect_evidence(
        run,
        enabled=enabled_sources or DEFAULT_SOURCES,
        rubric_version=RUBRIC_VERSION,
    )
    use_heuristic = (
        force_heuristic
        if force_heuristic is not None
        else os.environ.get("BLUE_FORCE_HEURISTIC", "0") == "1"
        or not _vllm_available()
    )
    if use_heuristic:
        judgment = heuristic_judge(bundle)
        log_llm_call(
            run_id=bundle.run_id,
            model=judgment.model,
            prompt=_build_user_prompt(bundle),
            response=judgment.model_dump_json(),
            metadata={"mode": "heuristic"},
        )
        return judgment
    try:
        return llm_judge(bundle)
    except Exception as exc:
        # Never call hosted APIs; degrade to heuristic on lab LLM failure.
        judgment = heuristic_judge(bundle)
        judgment.rationale = f"[fallback after vLLM error: {exc}] {judgment.rationale}"
        return judgment


def judge_run_id(
    run_id: str,
    *,
    enabled_sources: Iterable[str] | None = None,
    save: bool = False,
    force_heuristic: bool | None = None,
) -> BlueJudgment:
    import db as blue_db

    run = blue_db.fetch_run(run_id)
    if not run:
        raise SystemExit(f"run not found: {run_id}")
    judgment = judge_run(
        run, enabled_sources=enabled_sources, force_heuristic=force_heuristic
    )
    if save:
        blue_db.save_judgment(judgment)
    return judgment


def main() -> None:
    parser = argparse.ArgumentParser(description="Blue Agent — judge attack success")
    parser.add_argument("--run-id", help="Postgres run_id to judge")
    parser.add_argument("--json-run", help="Offline RunRecord JSON path")
    parser.add_argument(
        "--sources",
        default="all",
        help="Comma list of collectors or 'all' / 'tool_output_only'",
    )
    parser.add_argument("--save", action="store_true", help="Write to blue_agent_judgments")
    parser.add_argument(
        "--heuristic",
        action="store_true",
        help="Force offline heuristic (no vLLM)",
    )
    parser.add_argument(
        "--also-rule-grade",
        action="store_true",
        help="Also print provisional rule grade (does not overwrite)",
    )
    args = parser.parse_args()

    if args.sources == "all":
        enabled = list(DEFAULT_SOURCES)
    elif args.sources == "tool_output_only":
        enabled = ["tool_output", "attack_objective"]
    else:
        enabled = [s.strip() for s in args.sources.split(",") if s.strip()]

    if args.json_run:
        payload = json.loads(Path(args.json_run).read_text())
        runs = payload if isinstance(payload, list) else [payload]
        judgments = []
        for run in runs:
            judgment = judge_run(
                run, enabled_sources=enabled, force_heuristic=args.heuristic or None
            )
            judgments.append(judgment)
            if args.save:
                import db as blue_db

                blue_db.save_judgment(judgment)
        if args.also_rule_grade:
            for run, judgment in zip(runs, judgments):
                print(judgment.model_dump_json(indent=2))
                print("--- rule_based (provisional) ---")
                print(grade_run(run).model_dump_json(indent=2))
                print("---")
            return
        if len(judgments) == 1:
            print(judgments[0].model_dump_json(indent=2))
        else:
            print(json.dumps([j.model_dump(mode="json") for j in judgments], indent=2))
        return
    elif args.run_id:
        judgment = judge_run_id(
            args.run_id,
            enabled_sources=enabled,
            save=args.save,
            force_heuristic=True if args.heuristic else None,
        )
        run = {"run_id": args.run_id}
        if args.also_rule_grade:
            import db as blue_db

            run = blue_db.fetch_run(args.run_id) or run
    else:
        parser.error("Provide --run-id or --json-run")

    print(judgment.model_dump_json(indent=2))
    if args.also_rule_grade:
        if args.json_run:
            run = json.loads(Path(args.json_run).read_text())
        print("--- rule_based (provisional) ---")
        print(grade_run(run).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
