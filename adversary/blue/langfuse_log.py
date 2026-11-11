"""Optional Langfuse logging. Never requires network at import time."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOG_DIR = Path(__file__).resolve().parent / ".langfuse_local"
_PROMPT_VERSION = "blue-judge-v1"


def prompt_version() -> str:
    return os.environ.get("BLUE_PROMPT_VERSION", _PROMPT_VERSION)


def log_llm_call(
    *,
    run_id: str,
    model: str,
    prompt: str,
    response: str,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """
    Log every Blue Agent LLM call.

    If LANGFUSE_* env vars are set and the SDK is installed, send a generation.
    Always also append a local JSONL audit line (gitignored via .langfuse_local/).
    Returns a trace id string when available.
    """
    trace_id = None
    meta = metadata or {}
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "model": model,
        "prompt_version": prompt_version(),
        "prompt": prompt,
        "response": response,
        "metadata": meta,
    }

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (_LOG_DIR / "calls.jsonl").open("a") as f:
        f.write(json.dumps(record) + "\n")

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
    if public_key and secret_key:
        try:
            from langfuse import Langfuse  # type: ignore

            lf = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
            trace = lf.trace(name="blue_agent_judge", metadata={"run_id": run_id, **meta})
            trace.generation(
                name="blue_judgment",
                model=model,
                input=prompt,
                output=response,
                metadata={"prompt_version": prompt_version(), **meta},
            )
            lf.flush()
            trace_id = getattr(trace, "id", None) or str(trace)
        except Exception as exc:
            record["langfuse_error"] = str(exc)
            with (_LOG_DIR / "calls.jsonl").open("a") as f:
                f.write(json.dumps({"ts": record["ts"], "langfuse_error": str(exc)}) + "\n")

    return trace_id
