#!/usr/bin/env python3
import json, subprocess
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from contract import RunRecord
from db import save_record

MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct"

model = OpenAIChatModel(
        MODEL_NAME,
        provider=OpenAIProvider(base_url="http://localhost:8000/v1", api_key="not-needed"),
        )

agent = Agent(
        model,
        system_prompt=(
            """
            You are a red-team adversary operating ONLY against an isolated practice 
            hospital in a lab. Given a target, decide on one attack, call the run_attack tool
            exactly once, then briefly report what happened. Never act on anything other
            than the target you are given.
            """
            ),
        )
def _execute(target: str, attack: str) -> dict:
    args = {
        "detect": ["detect", target],
        "replay": ["replay", target, "/opt/redteam/captures/sample.pcap"],
        "craft":  ["craft", target],
    }.get(attack)
    if not args:
        return {"attack_name": "none", "crypto_detected": None,
                "attack_params": {"attack": attack},
                "outcome_notes": f"Unknown attack: {attack}"}
    proc = subprocess.run(
        ["docker", "exec", "attacker", "python3", "/opt/redteam/tools.py", *args],
        capture_output=True, text=True, timeout=120,
    )
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {"attack_name": attack, "crypto_detected": None,
                "attack_params": {"target": target},
                "outcome_notes": f"Could not parse tool output: {e}; raw: {proc.stdout[-300:]}"}

@agent.tool_plain
def run_attack(target: str, attack: str) -> str:
    """
    Run ONE attack against the target and record the result.
    attack must be one of: 'detect', 'replay', 'craft'.
    """
    result = _execute(target, attack)
    rec = RunRecord(
            target=target,
            crypto_detected=result.get("crypto_detected"),
            attack_name=result["attack_name"],
            attack_params=result.get("attack_params", {}),
            outcome_notes=result.get("outcome_notes", ""),
            )
    save_record(rec)
    return result["outcome_notes"]

def main():
    goal=("Target practice-target:443. First detect the crypto, then run one attack you judge appropriate, then report what happened.")
    result = agent.run_sync(goal)
    print("\n--- agent report ---\n", result.output)

if __name__ == "__main__":
    main()




