"""Submit and collect category summaries through the OpenAI Batch API.

The synchronous path in generate_summaries.py holds the organization's
tokens-per-minute ceiling for the length of a full-corpus run. Batch trades
latency for headroom and a lower per-token rate, so a whole-corpus regeneration
becomes one submission to collect later rather than hours of held throughput.

Sections and overviews are separate submissions by necessity: an overview is
synthesized from stored section summaries, so the sections must be collected and
written before the overview requests can be built.

    python backend/schemas/generate_summaries_batch.py submit-sections --all
    python backend/schemas/generate_summaries_batch.py collect <batch_id>
    python backend/schemas/generate_summaries_batch.py submit-overviews --all
    python backend/schemas/generate_summaries_batch.py collect <batch_id>
    python backend/schemas/generate_summaries_batch.py status <batch_id>
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from openai.lib._pydantic import to_strict_json_schema

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.schemas import generate_summaries as gs


BATCH_DIR = Path("/tmp/der_batches")
COMPLETION_WINDOW = "24h"
SECTION_PREFIX = "sections"
OVERVIEW_PREFIX = "overview"


def _request_line(custom_id, instructions, prompt, payload_model, schema_name):
    """One JSONL request mirroring the synchronous responses.parse call."""
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/responses",
        "body": {
            "model": gs.SUMMARY_MODEL,
            "reasoning": {"effort": "none"},
            "instructions": instructions,
            "input": prompt,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": to_strict_json_schema(payload_model),
                    "strict": True,
                }
            },
        },
    }


def build_section_requests(conn, region_ids, evidence_limit):
    """Build one section-batch request per region that still needs sections."""
    requests, skipped = [], []
    for region_id in region_ids:
        evidence_by_category = {}
        for category in gs.SECTION_CATEGORIES:
            if gs.get_existing_summary_id(conn, region_id, category) is not None:
                continue
            rows = gs.get_evidence_for_category(
                conn, region_id, category, limit=evidence_limit
            )
            if rows:
                evidence_by_category[category] = rows
        if not evidence_by_category:
            skipped.append(region_id)
            continue
        instructions, prompt = gs.build_section_batch_prompt(
            region_id, evidence_by_category
        )
        requests.append(
            _request_line(
                f"{SECTION_PREFIX}:{region_id}",
                instructions,
                prompt,
                gs.SectionBatchPayload,
                "SectionBatchPayload",
            )
        )
    return requests, skipped


def build_overview_requests(conn, region_ids):
    """Build one overview request per region whose overview is missing or stale."""
    requests, skipped = [], []
    for region_id in region_ids:
        sources = gs.get_overview_sources(conn, region_id)
        if len(sources) < gs.MIN_OVERVIEW_SOURCE_SECTIONS:
            skipped.append(region_id)
            continue
        existing = gs.get_existing_summary_id(conn, region_id, gs.OVERVIEW_CATEGORY)
        if existing is not None and not gs.overview_is_stale(conn, region_id, sources):
            skipped.append(region_id)
            continue
        missing = gs.missing_section_categories(conn, region_id, sources)
        instructions, prompt = gs.build_overview_prompt(region_id, sources, missing)
        requests.append(
            _request_line(
                f"{OVERVIEW_PREFIX}:{region_id}",
                instructions,
                prompt,
                gs.SummaryPayload,
                "SummaryPayload",
            )
        )
    return requests, skipped


def submit(client, requests, label):
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = BATCH_DIR / f"{label}-{stamp}.jsonl"
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in requests) + "\n")

    uploaded = client.files.create(file=open(path, "rb"), purpose="batch")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/responses",
        completion_window=COMPLETION_WINDOW,
        metadata={"label": label, "summary_version": gs.SUMMARY_VERSION},
    )
    print(f"submitted {len(requests)} requests as {batch.id} (input {path})")
    return batch


def _parse_output_text(body):
    """Pull the structured payload text out of a Responses API result body."""
    for item in reversed(body.get("output", [])):
        for chunk in item.get("content", []):
            if chunk.get("type") in {"output_text", "text"} and chunk.get("text"):
                return chunk["text"]
    raise ValueError("no output text in response body")


def collect(client, conn, batch_id, evidence_limit):
    """Validate and store every successful result, reusing the sync-path checks."""
    batch = client.batches.retrieve(batch_id)
    if batch.status != "completed":
        print(f"batch {batch_id} is {batch.status}; nothing collected", file=sys.stderr)
        return 1
    if not batch.output_file_id:
        print(f"batch {batch_id} has no output file", file=sys.stderr)
        return 1

    stored = failed = 0
    failures = []
    for raw in client.files.content(batch.output_file_id).text.splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        custom_id = row["custom_id"]
        kind, region_id = custom_id.split(":", 1)
        response = row.get("response") or {}
        if row.get("error") or response.get("status_code") != 200:
            failures.append(f"{custom_id}: {row.get('error') or response.get('status_code')}")
            failed += 1
            continue
        try:
            text = _parse_output_text(response["body"])
            if kind == SECTION_PREFIX:
                stored += _store_sections(conn, region_id, text, evidence_limit)
            else:
                stored += _store_overview(conn, region_id, text)
        except Exception as exc:  # one bad region must not abort the collection
            conn.rollback()
            failures.append(f"{custom_id}: {exc}")
            failed += 1

    print(f"stored {stored} summaries; {failed} requests failed")
    for failure in failures[:20]:
        print(f"  failed {failure}", file=sys.stderr)
    if len(failures) > 20:
        print(f"  ... and {len(failures) - 20} more", file=sys.stderr)
    return 0


def _store_sections(conn, region_id, text, evidence_limit):
    evidence_by_category = {}
    for category in gs.SECTION_CATEGORIES:
        rows = gs.get_evidence_for_category(
            conn, region_id, category, limit=evidence_limit
        )
        if rows:
            evidence_by_category[category] = rows

    payload = gs.SectionBatchPayload.model_validate_json(text)
    # Only the categories actually requested are present in the response.
    returned = {section.category for section in payload.sections}
    scoped = {c: r for c, r in evidence_by_category.items() if c in returned}
    gs.validate_section_batch_payload(payload, scoped)

    generated_at = datetime.now(timezone.utc).isoformat()
    batch_categories = [c for c in gs.SECTION_CATEGORIES if c in scoped]
    count = 0
    try:
        for section in payload.sections:
            rows = scoped[section.category]
            snapshot = {
                "region_id": region_id,
                "category": section.category,
                "evidence_ids_retrieved": [r["evidence_id"] for r in rows],
                "evidence_ids_linked": section.evidence_ids_used,
                "source_model_versions": [
                    r["model_version"] for r in rows if "model_version" in r.keys()
                ],
                "source_observation_periods": sorted(
                    {
                        str(r["observed_at"])
                        for r in rows
                        if "observed_at" in r.keys() and r["observed_at"] is not None
                    }
                ),
                "batch_categories": batch_categories,
                "summary_model": gs.SUMMARY_MODEL,
                "summary_version": gs.SUMMARY_VERSION,
                "delivery": "batch_api",
            }
            gs.store_summary_response(
                conn,
                region_id,
                section.category,
                section,
                snapshot,
                existing_summary_id=gs.get_existing_summary_id(
                    conn, region_id, section.category
                ),
                generated_at=generated_at,
            )
            count += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return count


def _store_overview(conn, region_id, text):
    sources = gs.get_overview_sources(conn, region_id)
    allowed = {e for s in sources for e in s.evidence_ids}
    payload = gs.SummaryPayload.model_validate_json(text)
    gs.validate_llm_evidence_ids(payload, allowed)

    snapshot = {
        "region_id": region_id,
        "category": gs.OVERVIEW_CATEGORY,
        "source_summary_ids": [s.summary_id for s in sources],
        "source_categories": [s.category for s in sources],
        "unavailable_categories": gs.missing_section_categories(
            conn, region_id, sources
        ),
        "evidence_ids_linked": payload.evidence_ids_used,
        "summary_model": gs.SUMMARY_MODEL,
        "summary_version": gs.SUMMARY_VERSION,
        "delivery": "batch_api",
    }
    try:
        gs.store_summary_response(
            conn,
            region_id,
            gs.OVERVIEW_CATEGORY,
            payload,
            snapshot,
            existing_summary_id=gs.get_existing_summary_id(
                conn, region_id, gs.OVERVIEW_CATEGORY
            ),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return 1


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("submit-sections", "submit-overviews"):
        p = sub.add_parser(name)
        group = p.add_mutually_exclusive_group(required=True)
        group.add_argument("--all", action="store_true")
        group.add_argument("--region-id", nargs="+")
        p.add_argument(
            "--evidence-limit", type=int, default=gs.DEFAULT_CATEGORY_EVIDENCE_LIMIT
        )
        p.add_argument("--dry-run", action="store_true")
    c = sub.add_parser("collect")
    c.add_argument("batch_id")
    c.add_argument(
        "--evidence-limit", type=int, default=gs.DEFAULT_CATEGORY_EVIDENCE_LIMIT
    )
    s = sub.add_parser("status")
    s.add_argument("batch_id")
    return parser


def main():
    args = build_parser().parse_args()
    conn = sqlite3.connect(gs.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        if args.command == "status":
            batch = gs.get_openai_client().batches.retrieve(args.batch_id)
            print(f"{batch.id}: {batch.status} {batch.request_counts}")
            return 0
        if args.command == "collect":
            return collect(
                gs.get_openai_client(), conn, args.batch_id, args.evidence_limit
            )

        if args.all:
            region_ids = [
                r["region_id"]
                for r in conn.execute("SELECT region_id FROM regions ORDER BY region_id")
            ]
        else:
            region_ids = [gs.normalize_region_id(v) for v in args.region_id]

        if args.command == "submit-sections":
            requests, skipped = build_section_requests(
                conn, region_ids, args.evidence_limit
            )
            label = "sections"
        else:
            requests, skipped = build_overview_requests(conn, region_ids)
            label = "overviews"

        print(f"{len(requests)} requests to submit; {len(skipped)} regions skipped")
        if not requests:
            return 0
        if args.dry_run:
            print("dry run; nothing submitted")
            print(json.dumps(requests[0])[:400])
            return 0
        submit(gs.get_openai_client(), requests, label)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
