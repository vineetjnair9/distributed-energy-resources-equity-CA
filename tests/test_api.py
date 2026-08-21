import sqlite3

import pytest

from backend.api import api
from backend.schemas import create_db


@pytest.fixture()
def api_db(tmp_path, monkeypatch):
    path = tmp_path / "api.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(create_db.SCHEMA)
    for region_id in ("90001", "90009"):
        conn.execute(
            "INSERT INTO regions (region_id, region_type) VALUES (?, 'zcta')",
            (region_id,),
        )
        conn.execute(
            """
            INSERT INTO summary_responses (
                category, region_id, summary_text, metric_snapshot,
                model_version, generated_at
            ) VALUES ('overview', ?, 'Overview text.', '{}', 'v3',
                      '2026-08-19T00:00:00+00:00')
            """,
            (region_id,),
        )
    conn.commit()
    conn.close()
    monkeypatch.setattr(api, "DB_PATH", path)
    return path


def test_compare_returns_every_requested_region(api_db):
    from fastapi.testclient import TestClient

    # /compare selects only overviews, so a region without one disappears from
    # the comparison without any signal. Every region carries an overview now,
    # including the thin ones that get the fixed not-enough-data text.
    response = TestClient(api.app).get(
        "/compare", params={"region_ids": ["90001", "90009"]}
    )

    assert response.status_code == 200
    assert [row["region_id"] for row in response.json()] == ["90001", "90009"]
