import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "der_tool.db"

app = FastAPI()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows):
    return [row_to_dict(row) for row in rows]


@app.get("/health")
def home():
    return {"message": "DER API is running"}


@app.get("/regions")
def get_regions():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM regions
            ORDER BY region_id
            """
        ).fetchall()
    return rows_to_dicts(rows)


@app.get("/regions/{region_id}")
def get_region(region_id: str):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM regions
            WHERE region_id = ?
            """,
            (region_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Region not found")
    return row_to_dict(row)


@app.get("/regions/{region_id}/metrics")
def get_region_metrics(region_id: str):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM metric_observations
            WHERE region_id = ?
            ORDER BY metric_name
            """,
            (region_id,),
        ).fetchall()
    return rows_to_dicts(rows)


@app.get("/regions/{region_id}/model-outputs")
def get_region_model_outputs(
    region_id: str,
    outcome_name: str | None = None,
    model_version: str | None = None,
):
    filters = ["region_id = ?"]
    params = [region_id]

    if outcome_name is not None:
        filters.append("outcome_name = ?")
        params.append(outcome_name)

    if model_version is not None:
        filters.append("model_version = ?")
        params.append(model_version)

    query = f"""
        SELECT *
        FROM model_outputs
        WHERE {' AND '.join(filters)}
        ORDER BY outcome_name, model_version
    """

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return rows_to_dicts(rows)


@app.get("/regions/{region_id}/evidence")
def get_region_chunks(region_id: str):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM evidence_chunks
            WHERE region_id = ?
            ORDER BY evidence_type, evidence_id
            """,
            (region_id,),
        ).fetchall()
    return rows_to_dicts(rows)


@app.get("/regions/{region_id}/summary-responses")
def get_region_summary(region_id: str):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                sr.summary_id,
                sr.region_id,
                sr.summary_text,
                sr.metric_snapshot,
                sr.model_version,
                sr.generated_at,
                ec.evidence_id,
                ec.evidence_text,
                ec.source_name
            FROM summary_responses sr
            LEFT JOIN summary_evidence se
              ON se.summary_id = sr.summary_id
            LEFT JOIN evidence_chunks ec
              ON ec.evidence_id = se.evidence_id
            WHERE sr.region_id = ?
            ORDER BY sr.generated_at DESC, ec.evidence_id
            """,
            (region_id,),
        ).fetchall()
    return rows_to_dicts(rows)


@app.get("/compare")
def compare_regions(region_ids: list[str] = Query(...)):
    placeholders = ",".join("?" for _ in region_ids)
    query = f"""
        SELECT
            region_id,
            summary_id,
            summary_text,
            metric_snapshot,
            model_version,
            generated_at
        FROM summary_responses
        WHERE region_id IN ({placeholders})
        ORDER BY region_id, generated_at DESC
    """

    with get_connection() as conn:
        rows = conn.execute(query, region_ids).fetchall()
    return rows_to_dicts(rows)


@app.get("/regions/{region_id}/profile")
def get_region_profile(region_id: str):
    return {
        "region": get_region(region_id),
        "metrics": get_region_metrics(region_id),
        "model_outputs": get_region_model_outputs(region_id),
        "evidence": get_region_chunks(region_id),
        "summary": get_region_summary(region_id),
    }
