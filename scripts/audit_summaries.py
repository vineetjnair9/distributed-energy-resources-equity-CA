"""Audit stored summaries against their cited evidence; optionally regenerate failures.

Runs the same deterministic claim checks the API applies (backend/grounding.py)
across the whole database. The API already withholds failures, so this exists
to find and repair them, not to protect readers.

Section failures are regenerated one category per request, which in a pilot
removed the cross-section leakage that batching all sections together caused.
An overview is regenerated after its sections, since it is written from them.

    python scripts/audit_summaries.py                    # report only
    python scripts/audit_summaries.py --regenerate       # repair (needs OPENAI_API_KEY)
"""

import argparse
import sqlite3
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.database import database_path  # noqa: E402
from backend.grounding import claim_problems  # noqa: E402


def audit(conn):
    failures = []
    for summary_id, region_id, category, text in conn.execute(
        "SELECT summary_id, region_id, category, summary_text FROM summary_responses "
        "ORDER BY region_id, category"
    ):
        evidence = [row[0] for row in conn.execute(
            "SELECT e.evidence_text FROM summary_evidence se "
            "JOIN evidence_chunks e USING (evidence_id) WHERE se.summary_id = ?",
            (summary_id,),
        )]
        problems = claim_problems(text, evidence) if evidence else ["cites no evidence"]
        if problems:
            failures.append((region_id, category, problems))
    return failures


def regenerate(failures):
    by_region = defaultdict(set)
    for region_id, category, _ in failures:
        by_region[region_id].add(category)
    script = ROOT / "backend" / "schemas" / "generate_summaries.py"
    for region_id, categories in sorted(by_region.items()):
        sections = sorted(categories - {"overview"})
        for category in sections:  # one request per section
            _run(script, region_id, [category])
        # A repaired section makes the overview stale; rewrite it from the new text.
        if sections or "overview" in categories:
            _run(script, region_id, ["overview"])


def _run(script, region_id, categories):
    subprocess.run(
        [sys.executable, str(script), "--region-id", region_id,
         "--category", *categories, "--replace-existing"],
        check=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--regenerate", action="store_true")
    args = parser.parse_args()
    path = database_path()
    with sqlite3.connect(path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM summary_responses").fetchone()[0]
        failures = audit(conn)
    print(f"{path.name}: {total} summaries, {len(failures)} fail claim checks")
    for region_id, category, problems in failures[:50]:
        print(f"  {region_id}/{category}: {'; '.join(problems)}")
    if len(failures) > 50:
        print(f"  ... and {len(failures) - 50} more")
    if args.regenerate and failures:
        regenerate(failures)
        with sqlite3.connect(path) as conn:
            remaining = audit(conn)
        print(f"after regeneration: {len(remaining)} still fail")
        for region_id, category, problems in remaining:
            print(f"  {region_id}/{category}: {'; '.join(problems)}")
        return 1 if remaining else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
