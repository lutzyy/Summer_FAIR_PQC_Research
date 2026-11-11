"""Assemble an EvidenceBundle from independently toggleable collectors."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable

_BLUE_ROOT = Path(__file__).resolve().parents[1]
if str(_BLUE_ROOT) not in sys.path:
    sys.path.insert(0, str(_BLUE_ROOT))

from models import EvidenceBundle  # noqa: E402
from rubric.loader import objective_for  # noqa: E402

DEFAULT_SOURCES = (
    "tool_output",
    "server_logs",
    "sensor_logs",
    "crypto_config",
    "attack_objective",
)


def _as_run_dict(run: Any) -> dict[str, Any]:
    if isinstance(run, dict):
        return dict(run)
    if hasattr(run, "model_dump"):
        return run.model_dump()
    return dict(getattr(run, "__dict__", {}))


def collect_tool_output(run: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Attack tool output from the run record (stdout-derived fields only today)."""
    payload = {
        "attack_name": run.get("attack_name"),
        "crypto_detected": run.get("crypto_detected"),
        "attack_params": run.get("attack_params") or {},
        "outcome_notes": run.get("outcome_notes") or "",
        "stderr": None,
        "exit_status": None,
        "note": "stderr and exit_status are not stored in runs; only contract fields available",
    }
    available = bool(payload["attack_name"] or payload["outcome_notes"])
    return payload, available


def collect_server_logs(run: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """nginx / TLS handshake logs — not wired yet."""
    return {
        "available": False,
        "reason": "Target/server logs are not collected per run in the current lab",
        "target": run.get("target"),
    }, False


def collect_sensor_logs(run: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Zeek/Suricata for the run time window — not deployed in repo."""
    return {
        "available": False,
        "reason": "Zeek/Suricata not deployed or tied to run windows; without_sensors is default",
        "timestamp": run.get("timestamp"),
    }, False


def infer_crypto_config(run: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Best-effort config from target name + crypto_detected."""
    target = (run.get("target") or "").lower()
    detected = run.get("crypto_detected") or ""
    if "pqc" in target or "4433" in target:
        profile = "pqc_or_hybrid_target"
        key_exchange = "unknown_or_hybrid_pqc"
        auth = "likely_mldsa_or_oqs"
    elif "practice-target" in target:
        profile = "classical_practice_target"
        key_exchange = "classical_tls"
        auth = "rsa_or_ecdsa"
    else:
        profile = "unknown"
        key_exchange = "unknown"
        auth = "unknown"
    low = detected.lower()
    if "mldsa" in low or "ml-dsa" in low or "mlkem" in low or "ml-kem" in low:
        profile = "pqc_signals_in_crypto_detected"
    return {
        "target": run.get("target"),
        "crypto_detected": detected or None,
        "inferred_profile": profile,
        "key_exchange": key_exchange,
        "authentication": auth,
        "device_constraint": "unconstrained",
        "service_protocol": "https_practice_target",
    }, True


def collect_attack_objective(
    run: dict[str, Any], rubric_version: str = "v1"
) -> tuple[dict[str, Any], bool]:
    attack = run.get("attack_name") or "none"
    obj = objective_for(str(attack), version=rubric_version)
    return obj, True


def collect_evidence(
    run: Any,
    *,
    enabled: Iterable[str] | None = None,
    rubric_version: str = "v1",
) -> EvidenceBundle:
    """
    Gather evidence for a run.

    Each collector is independently toggleable via `enabled`.
    Default enables all collectors; unavailable ones still appear with available=False.
    """
    run_d = _as_run_dict(run)
    run_id = str(run_d.get("run_id") or "")
    wanted = list(enabled) if enabled is not None else list(DEFAULT_SOURCES)

    bundle = EvidenceBundle(
        run_id=run_id,
        run_record={
            k: run_d.get(k)
            for k in (
                "run_id",
                "timestamp",
                "target",
                "crypto_detected",
                "attack_name",
                "attack_params",
                "outcome_notes",
            )
        },
        sources_enabled=wanted,
    )
    available: list[str] = []

    if "tool_output" in wanted:
        data, ok = collect_tool_output(run_d)
        bundle.tool_output = data
        if ok:
            available.append("tool_output")

    if "server_logs" in wanted:
        data, ok = collect_server_logs(run_d)
        bundle.server_logs = data
        if ok:
            available.append("server_logs")

    if "sensor_logs" in wanted:
        data, ok = collect_sensor_logs(run_d)
        bundle.sensor_logs = data
        if ok:
            available.append("sensor_logs")

    if "crypto_config" in wanted:
        data, ok = infer_crypto_config(run_d)
        bundle.crypto_config = data
        if ok:
            available.append("crypto_config")

    if "attack_objective" in wanted:
        data, ok = collect_attack_objective(run_d, rubric_version=rubric_version)
        bundle.attack_objective = data
        if ok:
            available.append("attack_objective")

    bundle.sources_available = available
    return bundle
