-- Blue Agent + provisional rule grader tables.
-- Does NOT alter the existing `runs` table or contract.py keys.

CREATE TABLE IF NOT EXISTS blue_agent_judgments (
    judgment_id       TEXT PRIMARY KEY,
    run_id            TEXT NOT NULL REFERENCES runs(run_id),
    verdict           TEXT NOT NULL CHECK (verdict IN ('success', 'failure', 'inconclusive')),
    confidence        DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    rationale         TEXT NOT NULL,
    evidence_cited    JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_sources_used JSONB NOT NULL DEFAULT '[]'::jsonb,
    model             TEXT NOT NULL,
    prompt_version    TEXT NOT NULL,
    rubric_version    TEXT NOT NULL,
    timestamp         TEXT NOT NULL,
    langfuse_trace_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_blue_judgments_run_id ON blue_agent_judgments(run_id);

-- Provisional rule-based grades (side-by-side with Blue Agent; replace when Sebastian's grader lands)
CREATE TABLE IF NOT EXISTS rule_based_grades (
    grade_id   TEXT PRIMARY KEY,
    run_id     TEXT NOT NULL REFERENCES runs(run_id),
    verdict    TEXT NOT NULL CHECK (verdict IN ('success', 'failure', 'inconclusive')),
    rationale  TEXT NOT NULL,
    grader_version TEXT NOT NULL,
    timestamp  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rule_grades_run_id ON rule_based_grades(run_id);

-- Hand-adjudicated gold subset for R1 accuracy (not agreement-with-grader)
CREATE TABLE IF NOT EXISTS gold_labels (
    gold_id    TEXT PRIMARY KEY,
    run_id     TEXT NOT NULL UNIQUE REFERENCES runs(run_id),
    verdict    TEXT NOT NULL CHECK (verdict IN ('success', 'failure', 'inconclusive')),
    adjudicator TEXT NOT NULL,
    notes      TEXT NOT NULL DEFAULT '',
    strata     JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS disagreement_cases (
    case_id    TEXT PRIMARY KEY,
    run_id     TEXT NOT NULL REFERENCES runs(run_id),
    blue_verdict TEXT NOT NULL,
    rule_verdict TEXT NOT NULL,
    who_was_right TEXT CHECK (who_was_right IN ('blue', 'rule', 'both_wrong', 'unknown', 'gold')),
    failure_mode TEXT NOT NULL,
    notes      TEXT NOT NULL DEFAULT '',
    timestamp  TEXT NOT NULL
);
