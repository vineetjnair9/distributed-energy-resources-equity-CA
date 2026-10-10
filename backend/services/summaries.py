"""Serve precomputed grounded summaries with traceability guardrails.

The web server never calls an LLM. Summaries are generated offline by
backend/schemas/generate_summaries.py, which retrieves a bounded evidence packet
per category, generates from it, and stores the evidence IDs it cited. This
module returns those records and refuses to present one as grounded unless its
citations check out:

* a summary that cites no evidence is withheld;
* a summary citing evidence from a different region is withheld;
* a summary whose percentile or observed-zero claims don't match the evidence
  it cites is withheld (backend/grounding.py);
* when no summary exists, the response says so and still returns the evidence
  packet the generator would have used, so the user sees data, not silence.
"""

import json

from backend.grounding import claim_problems

from backend.schemas.generate_summaries import (
    DESCRIPTIVE_CATEGORIES,
    INSUFFICIENT_DATA_OVERVIEW,
    MODEL_CATEGORIES,
    OVERVIEW_CATEGORY,
    SECTION_CATEGORIES,
    SUMMARY_CATEGORIES,
    get_evidence_for_category,
)
from backend.services.regions import get_region

FIXTURE_MODEL_PREFIX = "fixture_"
OVERVIEW_FALLBACK_PER_SECTION = 2

NO_SUMMARY = (
    "No stored summary exists for this region and category. Summaries are "
    "generated offline; the evidence that would ground one is listed instead."
)
NO_EVIDENCE = "The stored summary cites no evidence, so it is withheld as unsupported."
FOREIGN_EVIDENCE = (
    "The stored summary cites evidence belonging to another region, so it is "
    "withheld as untraceable."
)
MISSTATED_EVIDENCE = (
    "The stored summary misstates the evidence it cites, so it is withheld."
)
FIXTURE_WARNING = "Synthetic fixture text for development; not a research finding."
INSUFFICIENT_WARNING = "Too little data for an integrated overview of this region."


class UnknownCategory(ValueError):
    pass


def category_labels():
    labels = {key: config.label for key, config in DESCRIPTIVE_CATEGORIES.items()}
    labels.update({key: config.label for key, config in MODEL_CATEGORIES.items()})
    labels[OVERVIEW_CATEGORY] = "Overview"
    return {category: labels[category] for category in SUMMARY_CATEGORIES}


def _evidence_dict(row):
    return {key: row[key] for key in (
        "evidence_id", "region_id", "evidence_text", "evidence_type",
        "source_name", "source_url",
    )}


def retrieve_evidence(conn, region_id, category):
    """The packet the offline generator retrieves for this category."""
    if category != OVERVIEW_CATEGORY:
        return [_evidence_dict(row) for row in get_evidence_for_category(
            conn, region_id, category)]
    evidence, seen = [], set()
    for section in SECTION_CATEGORIES:
        for row in get_evidence_for_category(conn, region_id, section)[
            :OVERVIEW_FALLBACK_PER_SECTION
        ]:
            if row["evidence_id"] not in seen:
                seen.add(row["evidence_id"])
                evidence.append(_evidence_dict(row))
    return evidence


def _unavailable(conn, region_id, category, reason, record=None):
    evidence = retrieve_evidence(conn, region_id, category)
    warnings = [reason]
    if not evidence:
        warnings.append("No evidence was found for this category either.")
    return {
        "status": "unavailable",
        "summary_id": record["summary_id"] if record else None,
        "region_id": region_id,
        "category": category,
        "summary_text": None,
        "evidence_ids": [item["evidence_id"] for item in evidence],
        "evidence": evidence,
        "metric_snapshot": None,
        "model_version": record["model_version"] if record else None,
        "generated_at": record["generated_at"] if record else None,
        "warnings": warnings,
    }


def get_summary(conn, region_id, category=OVERVIEW_CATEGORY):
    if category not in SUMMARY_CATEGORIES:
        raise UnknownCategory(category)
    get_region(conn, region_id)
    record = conn.execute(
        """
        SELECT summary_id, summary_text, metric_snapshot, model_version, generated_at
        FROM summary_responses
        WHERE region_id = ? AND category = ?
        ORDER BY generated_at DESC, summary_id DESC
        LIMIT 1
        """,
        (region_id, category),
    ).fetchone()
    if record is None:
        return _unavailable(conn, region_id, category, NO_SUMMARY)

    evidence = [_evidence_dict(row) for row in conn.execute(
        """
        SELECT e.evidence_id, e.region_id, e.evidence_text, e.evidence_type,
               e.source_name, e.source_url
        FROM summary_evidence se
        JOIN evidence_chunks e ON e.evidence_id = se.evidence_id
        WHERE se.summary_id = ?
        ORDER BY e.evidence_id
        """,
        (record["summary_id"],),
    )]
    if not evidence:
        return _unavailable(conn, region_id, category, NO_EVIDENCE, record)
    if any(item["region_id"] != region_id for item in evidence):
        return _unavailable(conn, region_id, category, FOREIGN_EVIDENCE, record)
    problems = claim_problems(record["summary_text"], [item["evidence_text"] for item in evidence])
    if problems:
        return _unavailable(
            conn, region_id, category,
            f"{MISSTATED_EVIDENCE} It {'; it '.join(problems)}.", record,
        )

    try:
        snapshot = json.loads(record["metric_snapshot"]) if record["metric_snapshot"] else None
    except json.JSONDecodeError:
        snapshot = None
    warnings = []
    if (record["model_version"] or "").startswith(FIXTURE_MODEL_PREFIX):
        warnings.append(FIXTURE_WARNING)
    if record["summary_text"] == INSUFFICIENT_DATA_OVERVIEW or (
        isinstance(snapshot, dict) and snapshot.get("insufficient_data")
    ):
        warnings.append(INSUFFICIENT_WARNING)
    if snapshot is None and record["metric_snapshot"]:
        warnings.append("The stored metric snapshot could not be parsed.")

    return {
        "status": "available",
        "summary_id": record["summary_id"],
        "region_id": region_id,
        "category": category,
        "summary_text": record["summary_text"],
        "evidence_ids": [item["evidence_id"] for item in evidence],
        "evidence": evidence,
        "metric_snapshot": snapshot,
        "model_version": record["model_version"],
        "generated_at": record["generated_at"],
        "warnings": warnings,
    }


def list_summary_categories(conn, region_id):
    get_region(conn, region_id)
    rows = conn.execute(
        """
        SELECT sr.category, sr.summary_id, sr.model_version, sr.generated_at,
               COUNT(se.evidence_id) AS evidence_count
        FROM summary_responses sr
        LEFT JOIN summary_evidence se ON se.summary_id = sr.summary_id
        WHERE sr.region_id = ?
        GROUP BY sr.summary_id
        ORDER BY sr.generated_at DESC, sr.summary_id DESC
        """,
        (region_id,),
    ).fetchall()
    latest = {}
    for row in rows:
        latest.setdefault(row["category"], dict(row))
    order = {category: index for index, category in enumerate(SUMMARY_CATEGORIES)}
    items = sorted(latest.values(), key=lambda item: order.get(item["category"], len(order)))
    return {"region_id": region_id, "items": items}
