import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from contract import RunRecord

# Set POSTGRES_PASSWORD in .env (never commit that file)
load_dotenv(Path(__file__).with_name(".env"))

_password = os.environ.get("POSTGRES_PASSWORD")
env_path = Path(__file__).with_name(".env")

if not _password:
    raise RuntimeError("POSTGRES_PASSWORD is not set; add it to adversary/brain/.env")
DSN = f"host=127.0.0.1 port=5432 dbname=postgres user=postgres password={_password}"

def save_record(rec: RunRecord) -> None:
    with psycopg.connect(DSN) as conn:
        conn.execute("""
            INSERT INTO runs
            (run_id, timestamp, target, crypto_detected, attack_name, attack_params, outcome_notes)
            VALUES(%s, %s, %s, %s, %s, %s, %s)
            """, (rec.run_id, rec.timestamp, rec.target, rec.crypto_detected, rec.attack_name, json.dumps(rec.attack_params), rec.outcome_notes           ),
        )
        conn.commit()

