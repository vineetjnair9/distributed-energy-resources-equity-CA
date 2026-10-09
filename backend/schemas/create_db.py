"""Initialize an empty database without deleting an existing database."""

import argparse
from contextlib import closing
import sqlite3
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.database import database_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS utilities (
    utility_id INTEGER PRIMARY KEY AUTOINCREMENT,
    utility_acronym TEXT,
    utility_name TEXT NOT NULL UNIQUE,
    utility_type TEXT
);

CREATE TABLE IF NOT EXISTS regions (
    region_id TEXT PRIMARY KEY,
    region_name TEXT,
    region_type TEXT NOT NULL,
    state TEXT,
    county TEXT,
    utility_id INTEGER,
    FOREIGN KEY (utility_id) REFERENCES utilities(utility_id)
);

CREATE TABLE IF NOT EXISTS region_geometries (
    region_id TEXT PRIMARY KEY,
    geometry_wkt TEXT NOT NULL,
    geometry_format TEXT NOT NULL DEFAULT 'WKT',
    crs TEXT NOT NULL DEFAULT 'EPSG:4326',
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

CREATE TABLE IF NOT EXISTS metric_observations (
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

CREATE TABLE IF NOT EXISTS model_outputs (
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

CREATE TABLE IF NOT EXISTS evidence_chunks (
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

CREATE TABLE IF NOT EXISTS summary_responses (
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

CREATE TABLE IF NOT EXISTS summary_evidence (
    summary_id INTEGER NOT NULL,
    evidence_id INTEGER NOT NULL,
    PRIMARY KEY (summary_id, evidence_id),
    FOREIGN KEY (summary_id) REFERENCES summary_responses(summary_id),
    FOREIGN KEY (evidence_id) REFERENCES evidence_chunks(evidence_id)
);

CREATE TABLE IF NOT EXISTS llm_usage_log (
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

def initialize_database(path):
    """Create the schema only in a missing or zero-length database file.

    Existing databases are never migrated or reset by this command. Rebuilding
    belongs to build_database, which validates a separate file before publishing.
    """
    path = Path(path).expanduser().resolve()
    if path.exists() and path.stat().st_size:
        raise FileExistsError(
            f"Database already exists at {path}. No data was changed. "
            "Use python -m backend.schemas.build_database --replace-existing "
            "for an explicit rebuild with a backup."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        path = initialize_database(args.database or database_path())
    except (OSError, sqlite3.Error) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Created empty database schema at {path}")
    print("Load validated data with python -m backend.schemas.build_database --replace-existing")


if __name__ == "__main__":
    main()
