"""Database configuration and checks shared by the API and offline builder."""

import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Generated summaries and usage logs may be empty; serving observations must not
# depend on an OpenAI key or on having generated prose for every region.
CORE_TABLES = (
    "regions", "region_geometries", "metric_observations",
    "model_outputs", "evidence_chunks",
)
REQUIRED_COLUMNS = {
    "utilities": {"utility_id", "utility_acronym", "utility_name", "utility_type"},
    "regions": {"region_id", "region_name", "region_type", "state", "county", "utility_id"},
    "region_geometries": {"region_id", "geometry_wkt", "geometry_format", "crs"},
    "metric_observations": {
        "metric_id", "region_id", "metric_name", "metric_value", "metric_unit",
        "metric_category", "source_name", "observed_at",
    },
    "model_outputs": {
        "model_output_id", "region_id", "outcome_name", "model_version",
        "actual_value", "predicted_value", "residual_value", "residual_percentile",
        "priority_flag", "assumptions", "generated_at",
    },
    "evidence_chunks": {
        "evidence_id", "region_id", "evidence_text", "source_name", "source_url",
        "evidence_type", "created_at",
    },
    "summary_responses": {
        "summary_id", "category", "region_id", "summary_text", "metric_snapshot",
        "model_version", "generated_at",
    },
    "summary_evidence": {"summary_id", "evidence_id"},
    "llm_usage_log": {
        "usage_id", "user_id", "region_id", "task_type", "model_name",
        "input_tokens", "output_tokens", "estimated_cost_usd", "created_at",
    },
}


class DatabaseNotReady(RuntimeError):
    """The database cannot yet serve the application's core data."""


def database_path() -> Path:
    configured = os.environ.get("DER_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return PROJECT_ROOT / "data" / "der_tool.db"


def connect_readonly(path: Path) -> sqlite3.Connection:
    """Open an existing database without ever creating an empty file."""
    conn = None
    try:
        conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA query_only = ON")
        return conn
    except (OSError, sqlite3.Error) as exc:
        if conn is not None:
            conn.close()
        raise DatabaseNotReady("Database is missing, unreadable, or invalid.") from exc


def validate_database(conn: sqlite3.Connection, *, full_check: bool = False) -> None:
    """Check serving readiness, with expensive integrity checks only at build time."""
    try:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )}
        missing = sorted(REQUIRED_COLUMNS.keys() - tables)
        if missing:
            raise DatabaseNotReady("Missing database tables: " + ", ".join(missing))
        for table, required in REQUIRED_COLUMNS.items():
            columns = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}
            if required - columns:
                raise DatabaseNotReady(
                    f"Incompatible table {table}; missing columns: "
                    + ", ".join(sorted(required - columns))
                )
        empty = [table for table in CORE_TABLES if conn.execute(
            f'SELECT 1 FROM "{table}" LIMIT 1'
        ).fetchone() is None]
        if empty:
            raise DatabaseNotReady("Core data is empty: " + ", ".join(empty))
        if full_check:
            integrity = [row[0] for row in conn.execute("PRAGMA integrity_check")]
            if integrity != ["ok"]:
                raise DatabaseNotReady("Database integrity check failed.")
            if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise DatabaseNotReady("Database contains broken foreign-key references.")
    except sqlite3.Error as exc:
        raise DatabaseNotReady("Database cannot be read or its schema is invalid.") from exc


def check_database(path: Path, *, full_check: bool = False) -> None:
    conn = connect_readonly(path)
    try:
        validate_database(conn, full_check=full_check)
    finally:
        conn.close()
