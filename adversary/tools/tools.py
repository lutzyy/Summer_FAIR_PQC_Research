#!/usr/bin/env python3
"""Red team tools. Runs INSIDE the sealed attacker container.
Usage:  python3 tools.py detect  <target>
        python3 tools.py replay  <target> <pcap_path>
        python3 tools.py craft   <target>
Always prints ONE line of JSON with the four contract keys.
"""
import sys, json, subprocess


def detect_crypto(target: str) -> dict:
    host, _, port = target.partition(":")
    port = port or "443"
    proc = subprocess.run(
        ["openssl", "s_client", "-connect", f"{host}:{port}", "-brief"],
        input="", capture_output=True, text=True, timeout=15,
    )
    out = proc.stdout + proc.stderr
    proto = cipher = "unknown"
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("Protocol"):
            proto = s.split(":")[-1].strip()
        if s.startswith("Ciphersuite") or s.startswith("Cipher"):
            cipher = s.split(":")[-1].strip()
    ok = proto != "unknown"
    return {
        "attack_name": "tls_probe",
        "crypto_detected": f"{proto} / {cipher}",
        "attack_params": {"target": target},
        "outcome_notes": "Handshake completed." if ok else "Could not read handshake.",
    }


def replay_pcap(target: str, pcap: str) -> dict:
    proc = subprocess.run(
        ["tcpreplay", "--intf1=eth0", pcap],
        capture_output=True, text=True, timeout=60,
    )
    out = (proc.stdout + proc.stderr).strip()
    return {
        "attack_name": "pcap_replay",
        "crypto_detected": None,
        "attack_params": {"target": target, "pcap": pcap},
        "outcome_notes": out[-400:] if out else "Replay finished.",
    }


def craft_probe(target: str) -> dict:
    from scapy.all import IP, TCP, sr1, conf
    conf.verb = 0
    host, _, port = target.partition(":")
    port = int(port or "443")
    resp = sr1(IP(dst=host) / TCP(dport=port, flags="S"), timeout=5)
    if resp and resp.haslayer(TCP):
        note = f"Port {port} responded with TCP flags {resp[TCP].flags}."
    else:
        note = f"No response from port {port}."
    return {
        "attack_name": "scapy_syn_probe",
        "crypto_detected": None,
        "attack_params": {"target": target, "port": port},
        "outcome_notes": note,
    }


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "detect":
            result = detect_crypto(sys.argv[2])
        elif cmd == "replay":
            result = replay_pcap(sys.argv[2], sys.argv[3])
        elif cmd == "craft":
            result = craft_probe(sys.argv[2])
        else:
            result = {"attack_name": "none", "crypto_detected": None,
                      "attack_params": {}, "outcome_notes": f"Unknown command: {cmd}"}
    except Exception as e:
        result = {"attack_name": cmd or "none", "crypto_detected": None,
                  "attack_params": {}, "outcome_notes": f"Tool error: {e}"}
    print(json.dumps(result))