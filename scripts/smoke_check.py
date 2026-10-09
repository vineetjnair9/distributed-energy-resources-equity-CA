"""Smoke-check a running deployment end to end through its public API.

    python scripts/smoke_check.py https://ca-der-explorer.onrender.com
    python scripts/smoke_check.py http://127.0.0.1:8000 --retries 20

Uses only the standard library so it runs anywhere, including CI.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def call(base, path, body=None):
    request = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content_type = response.headers.get("content-type", "")
        text = response.read().decode()
        return json.loads(text) if "json" in content_type else text


def check(base):
    health = call(base, "/health")
    assert health["status"] == "ready", health
    regions = call(base, "/api/regions?limit=2")
    assert regions["total"] > 0 and regions["items"], "no regions"
    region_id = regions["items"][0]["region_id"]
    detail = call(base, f"/api/regions/{region_id}")
    assert detail["region"]["region_id"] == region_id
    call(base, f"/api/model-output/{region_id}")
    summary = call(base, "/api/summaries", {"region_id": region_id, "category": "overview"})
    assert summary["status"] in {"available", "unavailable"}
    if summary["status"] == "available":
        assert summary["evidence_ids"], "available summary without evidence"
    ids = [item["region_id"] for item in regions["items"]]
    if len(ids) == 2:
        compare = call(base, f"/api/compare?region_ids={ids[0]}&region_ids={ids[1]}")
        assert compare["region_ids"] == ids
    page = call(base, f"/regions/{region_id}")
    assert '<div id="root">' in page, "frontend shell not served"
    return {"region_id": region_id, "summary": summary["status"],
            "synthetic": health.get("synthetic")}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base_url")
    parser.add_argument("--retries", type=int, default=1,
                        help="Attempts, 3 s apart (free hosts cold-start slowly).")
    args = parser.parse_args()
    for attempt in range(1, args.retries + 1):
        try:
            result = check(args.base_url)
            print(f"Smoke check passed: {json.dumps(result)}")
            return
        except (urllib.error.URLError, ConnectionError, TimeoutError, AssertionError, KeyError) as exc:
            if attempt == args.retries:
                sys.exit(f"Smoke check failed: {exc!r}")
            time.sleep(3)


if __name__ == "__main__":
    main()
