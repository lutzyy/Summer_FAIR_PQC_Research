import json
import psycopg
from contract import RunRecord

DSN = "host=localhost port=5432 dbname=postgres user=postgres password=changeme"

def save_record(rec: RunRecord) -> None:
    with psycopg.connect(DSN) as conn:
        conn.execute("""
            INSERT INTO runs
            (run_id, timestamp, target, crypto_detected, attack_name, attack_params, outcome_notes)
            VALUES(%s, %s, %s, %s, %s, %s, %s)
            """, (rec.run_id, rec.timestamp, rec.target, rec.crypto_detected, rec.attack_name, json.dumps(rec.attack_params), rec.outcome_notes           ),
        )
        conn.commit()
