CREATE TABLE IF NOT EXISTS runs(
run_id TEXT PRIMARY KEY,
timestamp TEXT,
target TEXT,
crypto_detected TEXT,
attack_name TEXT,
attack_params JSONB,
outcome_notes TEXT
);
