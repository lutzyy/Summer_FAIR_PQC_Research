"""Load versioned attack-success rubrics for the Blue Agent."""
from __future__ import annotations

from pathlib import Path
from typing import Any

_RUBRIC_DIR = Path(__file__).resolve().parent

# Embedded fallback identical to v1.yaml so the agent works without PyYAML.
_V1_FALLBACK: dict[str, Any] = {
    "version": "v1",
    "updated": "2026-11-11",
    "notes": (
        "Provisional until attack owners confirm. Replay/craft do not equal crypto "
        "breaks; they measure tool-visible network outcomes only."
    ),
    "attacks": {
        "tls_probe": {
            "agent_alias": "detect",
            "objective": (
                "Recover the target's negotiated TLS parameters (protocol, ciphersuite, "
                "key-share group, certificate signature type) via a completed handshake probe."
            ),
            "success_when": [
                "Handshake completed (outcome_notes indicates completion OR crypto_detected "
                "is non-null with protocol != unknown)",
                "crypto_detected includes distinguishable protocol and/or cipher information",
            ],
            "failure_when": [
                "Could not read handshake / protocol remains unknown / tool error",
            ],
            "inconclusive_when": [
                "Partial fields only, or tool output ambiguous",
            ],
            "not_success": (
                "A completed handshake alone is NOT a crypto break; success here means the "
                "probe objective (parameter recovery) was met."
            ),
        },
        "pcap_replay": {
            "agent_alias": "replay",
            "objective": (
                "Replay a recorded lab pcap onto the sealed lab interface toward the target."
            ),
            "success_when": [
                "Tool finishes without tool error and outcome_notes indicate replay finished / sent packets",
            ],
            "failure_when": [
                "Tool error, missing pcap, or empty failure output",
            ],
            "inconclusive_when": [
                "Replay reports completion but no packet counters and no error",
            ],
            "not_success": (
                "Successful replay is NOT evidence that cryptography was broken or plaintext recovered."
            ),
        },
        "scapy_syn_probe": {
            "agent_alias": "craft",
            "objective": (
                "Determine whether the target TCP port responds to a crafted SYN probe."
            ),
            "success_when": [
                "Outcome notes report a TCP response with flags from the target port",
            ],
            "failure_when": [
                "No response from the port, or tool error",
            ],
            "inconclusive_when": [
                "Ambiguous flags / unexpected parsing",
            ],
            "not_success": (
                "Port reachability is reconnaissance, not a cryptographic compromise."
            ),
        },
        "none": {
            "agent_alias": "none",
            "objective": "No attack executed.",
            "success_when": [],
            "failure_when": ["Unknown attack or no-op"],
            "inconclusive_when": [],
        },
    },
}


def load_rubric(version: str = "v1") -> dict[str, Any]:
    path = _RUBRIC_DIR / f"{version}.yaml"
    if path.exists():
        try:
            import yaml  # type: ignore

            with path.open() as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict) and "attacks" in data:
                return data
        except Exception:
            pass
    if version == "v1":
        return dict(_V1_FALLBACK)
    raise FileNotFoundError(f"Rubric version not found: {version}")


def objective_for(attack_name: str, version: str = "v1") -> dict[str, Any]:
    rubric = load_rubric(version)
    attacks = rubric.get("attacks", {})
    if attack_name in attacks:
        return {"rubric_version": rubric.get("version", version), **attacks[attack_name]}
    # Map agent aliases
    for name, spec in attacks.items():
        if spec.get("agent_alias") == attack_name:
            return {"rubric_version": rubric.get("version", version), "attack_name": name, **spec}
    return {
        "rubric_version": rubric.get("version", version),
        "objective": f"Unknown attack '{attack_name}'; treat as inconclusive unless tool error.",
        "success_when": [],
        "failure_when": ["Unknown attack"],
        "inconclusive_when": ["No rubric entry"],
    }
