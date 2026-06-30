import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_EVIDENCE_LIMIT = 40
DEFAULT_METRIC_LIMIT = 20
DEFAULT_MODEL_EVIDENCE_LIMIT = 200
SUMMARY_MODEL = "gpt-5.5"
SUMMARY_VERSION = "llm_summary_v2"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "der_tool.db"
load_dotenv(PROJECT_ROOT / ".env")
client = OpenAI()

PRIMARY_OUTCOMES = {
    "y_pv",
    "y_storage",
    "y_chargers",
    "y_wind_mw",
    "energy_burden_pct",
    "log_energy_gap_per_capita",
}

OUTCOME_PRIORITY = [
    "y_pv",
    "y_storage",
    "y_chargers",
    "y_wind_mw",
    "energy_burden_pct",
    "log_energy_gap_per_capita",
]

MODEL_VERSION_PRIORITIES = {
    "Model 1 baseline": 35,
    "Model 6B county fe": 30,
    "Model 7 (infrastructure controls, outcome-safe)": 30,
    "Model 7 (per-capita infrastructure controls)": 30,
    "Model 8 add demand proxy": 30,
    "Model 5 utility FE": 20,
    "Model 2 (add bachelors)": 15,
    "Model 2 (add housing value)": 15,
}

COMPARISON_MODEL_MARKERS = [
    "Model 1 baseline",
    "Model 6B county fe",
    "Model 7 (infrastructure controls, outcome-safe)",
    "Model 7 (per-capita infrastructure controls)",
    "Model 8 add demand proxy",
    "Model 5 utility FE",
    "Model 2 (add bachelors)",
    "Model 2 (add housing value)",
]


def get_evidence_for_region(conn, region_id, limit=DEFAULT_EVIDENCE_LIMIT):
    metric_rows = get_metric_evidence_for_region(
        conn,
        region_id
    )
    model_rows = get_model_evidence_for_region(
        conn,
        region_id,
    )

    selected = select_summary_evidence(
        model_rows=model_rows,
        metric_rows=metric_rows,
        limit=limit,
    )

    return selected


def get_model_evidence_for_region(conn, region_id, limit=DEFAULT_MODEL_EVIDENCE_LIMIT):
    """
    Retrieve candidate model-output evidence chunks with structured model fields.

    evidence_chunks stores the text used in prompts, while model_outputs stores
    the residuals and flags needed for deterministic ranking.
    """
    rows = conn.execute(
        """
        SELECT
            e.evidence_id,
            e.region_id,
            e.evidence_text,
            e.source_name,
            e.source_url,
            e.evidence_type,
            e.created_at,
            m.outcome_name,
            m.model_version,
            m.actual_value,
            m.predicted_value,
            m.residual_value,
            m.residual_percentile,
            m.priority_flag
        FROM evidence_chunks e
        JOIN model_outputs m
          ON m.region_id = e.region_id
         AND e.evidence_type = 'model_output'
         AND e.evidence_text LIKE
             'For region ' || m.region_id || ', model ' || m.model_version ||
             ' for ' || m.outcome_name || ' estimated%'
        WHERE e.region_id = ?
        ORDER BY
            m.priority_flag DESC,
            m.residual_percentile ASC,
            ABS(m.residual_value) DESC,
            e.evidence_id
        LIMIT ?
        """,
        (region_id, limit),
    ).fetchall()

    return rows


def get_metric_evidence_for_region(conn, region_id, limit=DEFAULT_METRIC_LIMIT):
    """
    Retrieve metric/context evidence chunks for one region.
    """
    rows = conn.execute(
        """
        SELECT
            evidence_id,
            region_id,
            evidence_text,
            source_name,
            source_url,
            evidence_type,
            created_at
        FROM evidence_chunks
        WHERE region_id = ?
          AND evidence_type = 'metric'
        ORDER BY evidence_id
        LIMIT ?
        """,
        (region_id, limit),
    ).fetchall()

    return rows


def model_evidence_score(row):
    """
    Score model evidence for summary relevance.

    Priority flags and low residual percentiles are the strongest signals.
    Specific model specifications are retained because they help explain whether
    a signal persists across baseline, county, infrastructure, and demand views.
    """
    score = 0

    if row["priority_flag"]:
        score += 100

    if row["outcome_name"] in PRIMARY_OUTCOMES:
        score += 25

    residual_percentile = row["residual_percentile"]
    if residual_percentile is not None:
        score += max(0, int((0.5 - residual_percentile) * 100))

    residual_value = row["residual_value"]
    if residual_value < 0:
        score += 15  # below prediction, possible gap
    elif residual_value > 0:
        score += 5   # above prediction, possible bright spot

    model_version = row["model_version"] or ""
    for marker, marker_score in MODEL_VERSION_PRIORITIES.items():
        if marker in model_version:
            score += marker_score
            break

    return score


def select_summary_evidence(model_rows, metric_rows, limit=DEFAULT_EVIDENCE_LIMIT):
    """
    Select evidence for summary generation.

    Keep all available metric context first, then fill the remaining packet with
    high-signal model rows. Deduplicate by evidence_id and keep output ordering
    stable for the prompt.
    """
    selected = []
    seen_evidence_ids = set()

    for row in metric_rows:
        evidence_id = row["evidence_id"]
        if evidence_id not in seen_evidence_ids:
            selected.append(row)
            seen_evidence_ids.add(evidence_id)

    model_slots = max(limit - len(selected), 0)
    ranked_primary_rows = sorted(
        [row for row in model_rows if row["outcome_name"] in PRIMARY_OUTCOMES],
        key=lambda row: (
            -model_evidence_score(row),
            OUTCOME_PRIORITY.index(row["outcome_name"]),
            row["model_version"] or "",
            row["evidence_id"],
        ),
    )
    # reserve at least half of the model slots for high-signal rows but allow at least one
    high_signal_slots = max(1, model_slots // 2)
    for row in ranked_primary_rows:
        if high_signal_slots == 0 or len(selected) >= limit:
            break
        evidence_id = row["evidence_id"]
        if evidence_id not in seen_evidence_ids:
            selected.append(row)
            seen_evidence_ids.add(evidence_id)
            high_signal_slots -= 1
    # fill remaining model slots with any primary rows not already selected
    rows_by_outcome_and_marker = {}
    for row in ranked_primary_rows:
        model_version = row["model_version"] or ""
        for marker in COMPARISON_MODEL_MARKERS:
            if marker in model_version:
                key = (row["outcome_name"], marker)
                rows_by_outcome_and_marker.setdefault(key, row)
                break

    for outcome_name in OUTCOME_PRIORITY:
        for marker in COMPARISON_MODEL_MARKERS:
            if len(selected) >= limit:
                break
            row = rows_by_outcome_and_marker.get((outcome_name, marker))
            if row is None:
                continue
            evidence_id = row["evidence_id"]
            if evidence_id not in seen_evidence_ids:
                selected.append(row)
                seen_evidence_ids.add(evidence_id)
        if len(selected) >= limit:
            break

    for row in ranked_primary_rows:
        if len(selected) >= limit:
            break
        evidence_id = row["evidence_id"]
        if evidence_id not in seen_evidence_ids:
            selected.append(row)
            seen_evidence_ids.add(evidence_id)

    return sorted(selected, key=lambda row: row["evidence_id"])


def build_summary_prompt(region_id, evidence_rows):
    evidence_lines = []
    for row in evidence_rows:
        evidence_lines.append(
            f"[Evidence ID {row['evidence_id']}] {row['evidence_text']}"
        )
    evidence_block = "\n".join(evidence_lines)

    instructions = """
    You are generating concise summaries for a Distributed Energy Resource equity decision-support tool.

    Return only valid JSON, with no Markdown, no code block, and no extra text.
    The JSON object must have exactly these keys:
    - "summary_text": string
    - "evidence_ids_used": array of integer evidence IDs

    "summary_text" must not include an "Evidence used" line.
    "evidence_ids_used" must contain only IDs from the provided evidence.
    Include only evidence IDs that directly support claims made in "summary_text".

    Follow these rules:
    - Use only the provided evidence.
    - Do not invent facts.
    - Do not use outside knowledge.
    - Do not claim that race, income, climate, utility context, or socioeconomic context causes the observed outcome.
    - Use cautious, screening-oriented language.
    - Treat model outputs, residuals, and priority flags as decision-support signals, not proof of causation.
    - Climate metrics such as cdd65_2023 and hdd65_2023 are NASA POWER gridded centroid-based indicators. Describe them as coarse climate context, not precise ZIP-level measurements.
    - Only cite evidence IDs that appear in the provided evidence.
    """.strip()

    prompt = f"""
    Instructions:
    Write one concise paragraph, around 4 to 6 sentences.

    The summary should:
    1. Identify the most important DER adoption or infrastructure signals.
    2. Mention model residuals or priority flags if present.
    3. Mention socioeconomic, demographic, climate, or utility context if present. If using climate metrics, describe them as coarse NASA POWER gridded centroid-based climate indicators.
    4. Avoid overstating causality.
    5. Return your answer as valid JSON:
    {{
        "summary_text": "A concise 4-6 sentence summary.",
        "evidence_ids_used": [123, 456]
    }}

    Use cautious language such as:
    - "may indicate"
    - "is flagged for review"
    - "relative to the selected model"
    - "is associated with"
    - "should be interpreted as a screening signal"

    Input:
    Region ID: {region_id}

    Evidence:
    {evidence_block}
    """.strip()

    return instructions, prompt

def generate_summary_with_llm(region_id, evidence_chunks):
    instructions, prompt = build_summary_prompt(region_id, evidence_chunks)
    response = client.responses.create(
        model=SUMMARY_MODEL,
        instructions=instructions,
        input=prompt,
    )

    return parse_summary_response(response.output_text)


def parse_summary_response(response_text):
    """
    Parse and validate the model's JSON summary response.
    """
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Summary response was not valid JSON") from exc

    if set(payload.keys()) != {"summary_text", "evidence_ids_used"}:
        raise ValueError("Summary response must contain exactly summary_text and evidence_ids_used")

    if not isinstance(payload["summary_text"], str):
        raise ValueError("summary_text must be a string")

    if "Evidence used:" in payload["summary_text"]:
        raise ValueError("summary_text must not include an Evidence used line")

    evidence_ids_used = payload["evidence_ids_used"]
    if not isinstance(evidence_ids_used, list):
        raise ValueError("evidence_ids_used must be a list")

    if not evidence_ids_used:
        raise ValueError("evidence_ids_used must not be empty")

    if not all(isinstance(evidence_id, int) for evidence_id in evidence_ids_used):
        raise ValueError("evidence_ids_used must contain only integers")

    payload["summary_text"] = payload["summary_text"].strip()
    return payload


def insert_summary_response(
    conn,
    region_id,
    summary_text,
    metric_snapshot,
    model_version=SUMMARY_VERSION,
):
    generated_at = datetime.utcnow().isoformat()

    cursor = conn.execute(
        """
        INSERT INTO summary_responses (
            region_id,
            summary_text,
            metric_snapshot,
            model_version,
            generated_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            region_id,
            summary_text,
            json.dumps(metric_snapshot),
            model_version,
            generated_at,
        ),
    )
    return cursor.lastrowid


def link_summary_to_evidence(conn, summary_id, evidence_ids):
    """
    Insert links into summary_evidence.
    """
    rows = [
        (summary_id, evidence_id)
        for evidence_id in evidence_ids
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO summary_evidence (
            summary_id,
            evidence_id
        )
        VALUES (?, ?)
        """,
        rows,
    )


def delete_existing_summary(conn, summary_id):
    """
    Delete an existing summary and its evidence links before replacement.
    """
    conn.execute(
        """
        DELETE FROM summary_evidence
        WHERE summary_id = ?
        """,
        (summary_id,),
    )
    conn.execute(
        """
        DELETE FROM summary_responses
        WHERE summary_id = ?
        """,
        (summary_id,),
    )
    print(f"Removed summary with id: {summary_id}")


def generate_and_store_region_summary(
    conn,
    region_id,
    evidence_limit=DEFAULT_EVIDENCE_LIMIT,
    replace_existing=False,
):
    """
    Generate and store one LLM summary for one region.
    """
    existing = conn.execute(
        """
        SELECT summary_id
        FROM summary_responses
        WHERE region_id = ?
          AND model_version = ?
        LIMIT 1
        """,
        (region_id, SUMMARY_VERSION),
    ).fetchone()

    if existing and not replace_existing:
        print(f"Skipping {region_id}: summary already exists.")
        return existing["summary_id"]

    if existing and replace_existing:
        delete_existing_summary(conn, existing["summary_id"])

    evidence_rows = get_evidence_for_region(
        conn=conn,
        region_id=region_id,
        limit=evidence_limit,
    )

    if not evidence_rows:
        print(f"Skipping {region_id}: no evidence found.")
        return None

    summary_payload = generate_summary_with_llm(region_id, evidence_rows)
    evidence_ids_from_llm = summary_payload["evidence_ids_used"]
    all_retrieved_evidence_ids = [row["evidence_id"] for row in evidence_rows]
    valid_retrieved_evidence_ids = set(all_retrieved_evidence_ids)

    invalid_evidence_ids = sorted(
        set(evidence_ids_from_llm) - valid_retrieved_evidence_ids
    )
    if invalid_evidence_ids:
        raise ValueError(
            f"Summary cited evidence IDs that were not retrieved: {invalid_evidence_ids}"
        )

    evidence_ids_to_link = evidence_ids_from_llm

    clean_summary_text = summary_payload["summary_text"]

    metric_snapshot = {
        "region_id": region_id,
        "evidence_ids_retrieved": all_retrieved_evidence_ids,
        "evidence_ids_linked": evidence_ids_to_link,
        "summary_model": SUMMARY_MODEL,
        "summary_version": SUMMARY_VERSION,
    }

    summary_id = insert_summary_response(
        conn=conn,
        region_id=region_id,
        summary_text=clean_summary_text,
        metric_snapshot=metric_snapshot,
        model_version=SUMMARY_VERSION,
    )

    link_summary_to_evidence(
        conn=conn,
        summary_id=summary_id,
        evidence_ids=evidence_ids_to_link,
    )

    conn.commit()

    print(f"Generated summary for {region_id}: summary_id={summary_id}")

    return summary_id


def main():
    parser = argparse.ArgumentParser(description="Generate and store LLM region summaries.")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of regions to summarize. Defaults to 5 for pilot runs.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate summaries for all regions.",
    )
    parser.add_argument(
        "--region-id",
        nargs="+",
        help="One or more specific region IDs to summarize.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing summaries for the current summary version.",
    )
    parser.add_argument(
        "--evidence-limit",
        type=int,
        default=DEFAULT_EVIDENCE_LIMIT,
        help="Maximum number of evidence chunks to send for each region.",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        if args.region_id:
            placeholders = ",".join("?" for _ in args.region_id)
            region_rows = conn.execute(
                f"""
                SELECT region_id
                FROM regions
                WHERE region_id IN ({placeholders})
                ORDER BY region_id
                """,
                args.region_id,
            ).fetchall()
        elif args.all:
            region_rows = conn.execute(
                """
                SELECT region_id
                FROM regions
                ORDER BY region_id
                """
            ).fetchall()
        else:
            region_rows = conn.execute(
                """
                SELECT region_id
                FROM regions
                ORDER BY region_id
                LIMIT ?
                """,
                (args.limit,),
            ).fetchall()

        for row in region_rows:
            generate_and_store_region_summary(
                conn,
                row["region_id"],
                evidence_limit=args.evidence_limit,
                replace_existing=args.replace_existing,
            )

    finally:
        conn.close()

if __name__ == "__main__":
    main()
