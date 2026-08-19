import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "der_tool.db"
# change from DROP if exists to CREATE TABLE IF NOT EXISTS
SCHEMA = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS summary_evidence;
DROP TABLE IF EXISTS summary_responses;
DROP TABLE IF EXISTS evidence_chunks;
DROP TABLE IF EXISTS model_outputs;
DROP TABLE IF EXISTS metric_observations;
DROP TABLE IF EXISTS region_geometries;
DROP TABLE IF EXISTS regions;
DROP TABLE IF EXISTS utilities;
DROP TABLE IF EXISTS llm_usage_log;

CREATE TABLE utilities (
    utility_id INTEGER PRIMARY KEY AUTOINCREMENT,
    utility_acronym TEXT,
    utility_name TEXT NOT NULL UNIQUE,
    utility_type TEXT
);

CREATE TABLE regions (
    region_id TEXT PRIMARY KEY,
    region_name TEXT,
    region_type TEXT NOT NULL,
    state TEXT,
    county TEXT,
    utility_id INTEGER,
    FOREIGN KEY (utility_id) REFERENCES utilities(utility_id)
);

CREATE TABLE region_geometries (
    region_id TEXT PRIMARY KEY,
    geometry_wkt TEXT NOT NULL,
    geometry_format TEXT NOT NULL DEFAULT 'WKT',
    crs TEXT NOT NULL DEFAULT 'EPSG:4326',
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

CREATE TABLE metric_observations (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    metric_unit TEXT,
    metric_category TEXT,
    source_name TEXT,
    observed_at TEXT,
    FOREIGN KEY (region_id) REFERENCES regions(region_id),
    UNIQUE(region_id, metric_name, observed_at)
);

CREATE TABLE model_outputs (
    model_output_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT NOT NULL,
    outcome_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    actual_value REAL,
    predicted_value REAL,
    residual_value REAL,
    residual_percentile REAL,
    priority_flag INTEGER,
    assumptions TEXT,
    generated_at TEXT,
    FOREIGN KEY (region_id) REFERENCES regions(region_id),
    UNIQUE (region_id, outcome_name, model_version)
);

CREATE TABLE evidence_chunks (
    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT,
    evidence_text TEXT NOT NULL,
    source_name TEXT,
    source_url TEXT,
    evidence_type TEXT,
    created_at TEXT,
    FOREIGN KEY (region_id) REFERENCES regions(region_id),
    UNIQUE(region_id, evidence_text, evidence_type)
);

CREATE TABLE summary_responses (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    region_id TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    metric_snapshot TEXT,
    model_version TEXT,
    generated_at TEXT,
    FOREIGN KEY (region_id) REFERENCES regions(region_id),
    UNIQUE(region_id, category, model_version)
);

CREATE TABLE summary_evidence (
    summary_id INTEGER NOT NULL,
    evidence_id INTEGER NOT NULL,
    PRIMARY KEY (summary_id, evidence_id),
    FOREIGN KEY (summary_id) REFERENCES summary_responses(summary_id),
    FOREIGN KEY (evidence_id) REFERENCES evidence_chunks(evidence_id)
);

CREATE TABLE llm_usage_log (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    region_id TEXT,
    task_type TEXT NOT NULL,
    model_name TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost_usd REAL,
    created_at TEXT
);
"""

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

    print(f"Created database at {DB_PATH}")

if __name__ == "__main__":
    main()
