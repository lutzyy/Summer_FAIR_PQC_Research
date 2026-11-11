#!/usr/bin/env python3
"""
Typed, enumerable cryptographic configuration space for the orchestrator.

Mark combinations the lab cannot run as invalid instead of failing at runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import Iterator


class KeyExchange(str, Enum):
    CLASSICAL = "classical"  # e.g. X25519 / ECDHE
    HYBRID = "hybrid"  # e.g. X25519MLKEM768
    PURE_PQC = "pure_pqc"  # e.g. ML-KEM


class Authentication(str, Enum):
    CLASSICAL = "classical"  # RSA / ECDSA
    PQC = "pqc"  # ML-DSA
    HYBRID = "hybrid"  # where supported


class ServiceProtocol(str, Enum):
    PRACTICE_HTTPS = "practice_https"
    # Designed for later — invalid until lab services exist
    FHIR_REST = "fhir_rest"
    DICOM = "dicom"
    MQTT_HL7 = "mqtt_hl7"


class DeviceConstraint(str, Enum):
    UNCONSTRAINED = "unconstrained"
    CONSTRAINED = "constrained"  # invalid until lab supports device profiles


class Attack(str, Enum):
    TLS_PROBE = "tls_probe"
    PCAP_REPLAY = "pcap_replay"
    SCAPY_SYN_PROBE = "scapy_syn_probe"


@dataclass(frozen=True)
class CryptoConfig:
    key_exchange: KeyExchange
    authentication: Authentication
    service_protocol: ServiceProtocol
    device_constraint: DeviceConstraint = DeviceConstraint.UNCONSTRAINED

    def as_dict(self) -> dict[str, str]:
        return {
            "key_exchange": self.key_exchange.value,
            "authentication": self.authentication.value,
            "service_protocol": self.service_protocol.value,
            "device_constraint": self.device_constraint.value,
        }


@dataclass(frozen=True)
class Experiment:
    config: CryptoConfig
    attack: Attack

    @property
    def cell_id(self) -> str:
        c = self.config
        return (
            f"{c.key_exchange.value}|{c.authentication.value}|"
            f"{c.service_protocol.value}|{c.device_constraint.value}|{self.attack.value}"
        )

    def as_dict(self) -> dict:
        return {**self.config.as_dict(), "attack": self.attack.value, "cell_id": self.cell_id}


def _lab_supports(config: CryptoConfig) -> tuple[bool, str]:
    """
    Map to what the repo can actually run today:

    - classical practice-target:443 → classical KX + classical auth + practice_https + unconstrained
    - practice-target-pqc:4433 (OQS nginx) → hybrid/pure_pqc KX signals + PQC auth (ML-DSA) + practice_https

    Exact OpenSSL group negotiation may vary; we treat PQC target as supporting
    hybrid and pure_pqc key exchange with PQC authentication.
    """
    if config.device_constraint != DeviceConstraint.UNCONSTRAINED:
        return False, "constrained device profile not supported in lab yet"
    if config.service_protocol != ServiceProtocol.PRACTICE_HTTPS:
        return False, f"{config.service_protocol.value} service not deployed yet"

    classical_ok = (
        config.key_exchange == KeyExchange.CLASSICAL
        and config.authentication == Authentication.CLASSICAL
    )
    pqc_ok = (
        config.key_exchange in (KeyExchange.HYBRID, KeyExchange.PURE_PQC)
        and config.authentication == Authentication.PQC
    )
    # Hybrid auth not exposed as a distinct target today
    if config.authentication == Authentication.HYBRID:
        return False, "hybrid authentication target not available"
    if classical_ok or pqc_ok:
        return True, "ok"
    return False, "no practice target matches this kx/auth pairing"


def target_for(config: CryptoConfig) -> str | None:
    ok, _ = _lab_supports(config)
    if not ok:
        return None
    if config.key_exchange == KeyExchange.CLASSICAL:
        return "practice-target:443"
    return "practice-target-pqc:4433"


def iter_all_experiments() -> Iterator[Experiment]:
    for kx, auth, svc, dev, atk in product(
        KeyExchange, Authentication, ServiceProtocol, DeviceConstraint, Attack
    ):
        yield Experiment(
            CryptoConfig(kx, auth, svc, dev),
            atk,
        )


def enumerate_space() -> list[dict]:
    """Return every cell with validity flag and reason."""
    rows = []
    for exp in iter_all_experiments():
        ok, reason = _lab_supports(exp.config)
        rows.append(
            {
                **exp.as_dict(),
                "valid": ok,
                "invalid_reason": None if ok else reason,
                "target": target_for(exp.config) if ok else None,
            }
        )
    return rows


def valid_experiments() -> list[Experiment]:
    return [e for e in iter_all_experiments() if _lab_supports(e.config)[0]]


def main() -> None:
    import json

    rows = enumerate_space()
    valid = [r for r in rows if r["valid"]]
    print(json.dumps({"total": len(rows), "valid": len(valid), "valid_cells": valid}, indent=2))


if __name__ == "__main__":
    main()
