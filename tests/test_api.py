"""API, schema, and grounding tests against the synthetic fixture database.

The fixture is built once per session through the production database builder
(backend.fixtures.build_fixture_db -> build_database), so these tests also cover
the loaders and validation on a clean clone with no processed data present.
"""

import hashlib
import shutil
import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from backend.api import api
from backend.database import validate_database
from backend.fixtures import build_fixture_db as fixture
from backend.schemas import populate_tables
from backend.services import regions as region_service


@pytest.fixture(scope="session")
def fixture_db(tmp_path_factory):
    return fixture.build_fixture_database(tmp_path_factory.mktemp("db") / "der.db")


@pytest.fixture()
def client(fixture_db, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", fixture_db)
    return TestClient(api.app)


@pytest.fixture()
def mutable_client(fixture_db, tmp_path, monkeypatch):
    """A private copy for tests that corrupt data to exercise guardrails."""
    path = tmp_path / "copy.db"
    shutil.copy(fixture_db, path)
    monkeypatch.setattr(api, "DB_PATH", path)
    return TestClient(api.app), path


def summary(client, region_id, category="overview"):
    response = client.post("/api/summaries", json={"region_id": region_id, "category": category})
    assert response.status_code == 200
    return response.json()


# --- schema -----------------------------------------------------------------

def test_fixture_passes_full_validation(fixture_db):
    with closing(sqlite3.connect(fixture_db)) as conn:
        validate_database(conn, full_check=True)


def test_region_id_is_a_stable_five_character_key_everywhere(fixture_db):
    with closing(sqlite3.connect(fixture_db)) as conn:
        for table in ("regions", "region_geometries", "metric_observations",
                      "model_outputs", "evidence_chunks", "summary_responses"):
            bad = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE length(region_id) != 5 "
                "OR region_id NOT IN (SELECT region_id FROM regions)"
            ).fetchone()[0]
            assert bad == 0, table


def test_metric_categories_match_the_loader():
    loader = {category for _, category, _ in populate_tables.METRIC_COLUMNS.values()}
    assert set(region_service.METRIC_CATEGORIES) == loader


def test_every_stored_summary_cites_evidence_from_its_own_region(fixture_db):
    with closing(sqlite3.connect(fixture_db)) as conn:
        uncited = conn.execute(
            "SELECT COUNT(*) FROM summary_responses sr WHERE NOT EXISTS "
            "(SELECT 1 FROM summary_evidence se WHERE se.summary_id = sr.summary_id)"
        ).fetchone()[0]
        foreign = conn.execute(
            "SELECT COUNT(*) FROM summary_evidence se "
            "JOIN summary_responses sr ON sr.summary_id = se.summary_id "
            "JOIN evidence_chunks e ON e.evidence_id = se.evidence_id "
            "WHERE e.region_id != sr.region_id"
        ).fetchone()[0]
    assert (uncited, foreign) == (0, 0)


# --- API contract -------------------------------------------------------------

def test_openapi_documents_the_required_surface(client):
    paths = client.get("/api/openapi.json").json()["paths"]
    for path in ("/api/regions", "/api/regions/{region_id}", "/api/compare",
                 "/api/model-output/{region_id}", "/api/summaries", "/api/health"):
        assert path in paths
    assert "post" in paths["/api/summaries"]


def test_health_reports_ready_and_synthetic(client):
    for path in ("/health", "/api/health"):
        body = client.get(path).json()
        assert body["status"] == "ready"
        assert body["synthetic"] is True
        assert "/" not in body["database"]


def test_health_is_503_with_setup_command_when_database_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "absent.db")
    response = TestClient(api.app).get("/api/health")
    assert response.status_code == 503
    assert response.json()["setup_command"]
    assert not (tmp_path / "absent.db").exists()
    assert TestClient(api.app).get("/api/regions").status_code == 503


def test_region_search_filters_and_paginates(client):
    body = client.get("/api/regions", params={"county": "alameda"}).json()
    assert body["total"] == 4
    assert {item["county"] for item in body["items"]} == {"Alameda"}

    page = client.get("/api/regions", params={"limit": 5, "offset": 5}).json()
    assert page["total"] == len(fixture.REGIONS)
    assert len(page["items"]) == 5

    assert client.get("/api/regions", params={"q": "9000"}).json()["items"][0]["region_id"] == "90001"
    assert client.get("/api/regions", params={"utility": "SMUD"}).json()["total"] == 2


def test_every_fixture_region_has_its_county(fixture_db):
    # Regression: the loader read a "county" column, but the pipeline writes
    # "county_name", so every real region silently lost its county.
    with closing(sqlite3.connect(fixture_db)) as conn:
        counties = dict(conn.execute("SELECT region_id, county FROM regions"))
    assert counties == {zcta: county for zcta, county, *_ in fixture.REGIONS}


def test_region_without_utility_mapping_returns_null_utility(client):
    assert client.get("/api/regions/93654").json()["region"]["utility"] is None


def test_region_detail_formats_metrics_and_reports_missing_categories(client):
    body = client.get("/api/regions/90001").json()
    metric = next(m for m in body["metrics"] if m["metric_name"] == "poverty_rate")
    assert metric["display_value"].endswith("%")
    assert body["missing_metric_categories"] == []
    assert body["geometry"]["geometry_wkt"].startswith("POLYGON")

    thin = client.get(f"/api/regions/{fixture.THIN_REGION}").json()
    assert {m["metric_category"] for m in thin["metrics"]} == {"der_observed"}
    assert "demographic" in thin["missing_metric_categories"]


def test_unknown_region_is_404_on_every_region_route(client):
    for path in ("/api/regions/00000", "/api/regions/00000/evidence",
                 "/api/model-output/00000", "/api/regions/00000/summaries"):
        assert client.get(path).status_code == 404, path
    assert client.post("/api/summaries", json={"region_id": "00000"}).status_code == 404


def test_model_output_filters_and_types(client):
    body = client.get("/api/model-output/90001", params={"outcome_name": "y_pv"}).json()
    assert len(body["items"]) == 2
    for item in body["items"]:
        assert item["outcome_name"] == "y_pv"
        assert isinstance(item["priority_flag"], bool)
        assert 0 <= item["residual_percentile"] <= 1
    assert client.get(f"/api/model-output/{fixture.THIN_REGION}").json()["items"] == []


def test_priority_flags_follow_the_documented_cutoffs(client):
    for region_id, *_ in fixture.REGIONS:
        for item in client.get(f"/api/model-output/{region_id}").json()["items"]:
            pct = item["residual_percentile"]
            expected = pct <= 0.25 if item["outcome_name"].startswith("y_") else pct >= 0.75
            assert item["priority_flag"] is expected


def test_compare_keeps_request_order_and_marks_missing_values(client):
    ids = ["90210", fixture.THIN_REGION, "90001"]
    body = client.get("/api/compare", params={"region_ids": ids}).json()
    assert body["region_ids"] == ids
    assert [r["region_id"] for r in body["regions"]] == ids
    income = next(m for m in body["metrics"] if m["metric_name"] == "median_household_income")
    assert income["values"][fixture.THIN_REGION] is None
    assert income["display_values"]["90001"].startswith("$")
    assert set(body["overviews"]) == set(ids)


def test_compare_accepts_comma_separated_ids_and_dedupes(client):
    body = client.get("/api/compare", params={"region_ids": "90001,90210,90001"}).json()
    assert body["region_ids"] == ["90001", "90210"]


@pytest.mark.parametrize("ids", [["90001"], ["90001"] * 3, [str(90001 + i) for i in range(7)]])
def test_compare_rejects_too_few_or_too_many(client, ids):
    assert client.get("/api/compare", params={"region_ids": ids}).status_code == 400


def test_compare_names_every_unknown_region(client):
    response = client.get("/api/compare", params={"region_ids": ["90001", "00000", "00001"]})
    assert response.status_code == 404
    assert "00000, 00001" in response.json()["detail"]


# --- grounding ----------------------------------------------------------------

def test_available_summary_exposes_traceable_evidence(client):
    body = summary(client, "90001")
    assert body["status"] == "available"
    assert body["evidence_ids"] == [item["evidence_id"] for item in body["evidence"]]
    assert body["evidence_ids"]
    assert {item["region_id"] for item in body["evidence"]} == {"90001"}
    assert body["model_version"] == fixture.FIXTURE_VERSION
    assert body["generated_at"]
    assert isinstance(body["metric_snapshot"], dict)
    assert any("Synthetic" in warning for warning in body["warnings"])


def test_missing_summary_falls_back_to_evidence_not_text(client):
    for category in ("overview", "community_demographics", "model_pv"):
        body = summary(client, fixture.NO_SUMMARY_REGION, category)
        assert body["status"] == "unavailable"
        assert body["summary_text"] is None
        assert body["evidence"], category
        assert {item["region_id"] for item in body["evidence"]} == {fixture.NO_SUMMARY_REGION}
        assert "No stored summary" in body["warnings"][0]


def test_category_without_evidence_says_so(client):
    body = summary(client, fixture.THIN_REGION, "community_demographics")
    assert body["status"] == "unavailable"
    assert body["evidence"] == []
    assert any("No evidence" in warning for warning in body["warnings"])


def test_thin_region_overview_carries_insufficient_data_warning(client):
    body = summary(client, fixture.THIN_REGION)
    assert body["status"] == "available"
    assert any("Too little data" in warning for warning in body["warnings"])


def test_summary_without_evidence_links_is_withheld(mutable_client):
    client, path = mutable_client
    with closing(sqlite3.connect(path)) as conn:
        summary_id = conn.execute(
            "SELECT summary_id FROM summary_responses "
            "WHERE region_id = '90001' AND category = 'overview'"
        ).fetchone()[0]
        conn.execute("DELETE FROM summary_evidence WHERE summary_id = ?", (summary_id,))
        conn.commit()
    body = summary(client, "90001")
    assert body["status"] == "unavailable"
    assert body["summary_text"] is None
    assert "cites no evidence" in body["warnings"][0]
    assert body["evidence"]


def test_summary_citing_another_regions_evidence_is_withheld(mutable_client):
    client, path = mutable_client
    with closing(sqlite3.connect(path)) as conn:
        summary_id = conn.execute(
            "SELECT summary_id FROM summary_responses "
            "WHERE region_id = '90001' AND category = 'overview'"
        ).fetchone()[0]
        foreign = conn.execute(
            "SELECT evidence_id FROM evidence_chunks WHERE region_id = '90210' LIMIT 1"
        ).fetchone()[0]
        conn.execute("INSERT INTO summary_evidence VALUES (?, ?)", (summary_id, foreign))
        conn.commit()
    body = summary(client, "90001")
    assert body["status"] == "unavailable"
    assert "another region" in body["warnings"][0]


def test_unknown_category_lists_valid_ones(client):
    response = client.post("/api/summaries", json={"region_id": "90001", "category": "nope"})
    assert response.status_code == 422
    assert "overview" in response.json()["detail"]["valid_categories"]


def test_summary_category_index_matches_stored_rows(client):
    categories = client.get("/api/summary-categories").json()
    assert categories["overview"] == "Overview"
    items = client.get("/api/regions/90001/summaries").json()["items"]
    assert [item["category"] for item in items][-1] == "overview"
    assert all(item["evidence_count"] > 0 for item in items)
    for item in items:
        assert item["category"] in categories


# --- regression ---------------------------------------------------------------

def _digest(frames):
    return hashlib.sha256(
        b"".join(frame.to_csv(index=False).encode() for frame in frames)
    ).hexdigest()


def test_fixture_data_is_deterministic():
    assert _digest(fixture.synthetic_frames()) == _digest(fixture.synthetic_frames())
    assert _digest(fixture.synthetic_frames()) != _digest(fixture.synthetic_frames(seed=1))


def test_evidence_text_format_is_stable(client):
    evidence = client.get("/api/regions/90001/evidence", params={"evidence_type": "metric"}).json()
    texts = [item["evidence_text"] for item in evidence]
    assert any(t.startswith("For region 90001, ACS 5-year metric poverty_rate is ") for t in texts)
    models = client.get("/api/regions/90001/evidence",
                        params={"evidence_type": "model_output"}).json()
    assert all("Priority status:" in item["evidence_text"] for item in models)


# --- smoke: frontend shell --------------------------------------------------------

def test_spa_routes_serve_index_and_api_404s_stay_json(client):
    if not (api.FRONTEND_DIST / "index.html").is_file():
        pytest.skip("frontend not built (npm --prefix frontend run build)")
    for path in ("/", "/regions/90001", "/compare"):
        response = client.get(path)
        assert response.status_code == 200
        assert "<div id=\"root\">" in response.text
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")


# --- screening and facets -------------------------------------------------------

def test_facets_list_counties_utilities_and_outcomes(client):
    body = client.get("/api/facets").json()
    counties = {item["value"]: item["count"] for item in body["counties"]}
    assert counties["Alameda"] == 4
    assert sum(counties.values()) == len(fixture.REGIONS)
    assert {"LADWP", "PG&E", "SMUD"} <= {item["value"] for item in body["utilities"]}
    assert {item["value"] for item in body["outcomes"]} == set(fixture.MODELS)


def test_screening_ranks_by_agreement_then_extremity(client):
    body = client.get("/api/screening", params={"outcome_name": "y_pv", "limit": 200}).json()
    assert body["direction"] == "low"
    assert body["total"] == len(body["items"]) > 0
    keys = [(-row["flagged_count"] / row["specification_count"], row["mean_residual_percentile"])
            for row in body["items"]]
    assert keys == sorted(keys)
    for row in body["items"]:
        flags = [item["priority_flag"] for item in client.get(
            f"/api/model-output/{row['region']['region_id']}",
            params={"outcome_name": "y_pv"}).json()["items"]]
        assert sum(flags) == row["flagged_count"] > 0


def test_screening_burden_flags_high_and_filters(client):
    body = client.get("/api/screening", params={
        "outcome_name": "energy_burden_pct", "county": "Los Angeles"}).json()
    assert body["direction"] == "high"
    assert {row["region"]["county"] for row in body["items"]} <= {"Los Angeles"}


def test_screening_unknown_outcome_is_404(client):
    assert client.get("/api/screening", params={"outcome_name": "nope"}).status_code == 404


# --- security -----------------------------------------------------------------

@pytest.mark.parametrize("path", ["/api/health", "/api/regions", "/api/regions/00000", "/"])
def test_every_response_carries_security_headers(client, path):
    headers = client.get(path).headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    csp = headers["content-security-policy"]
    assert "frame-ancestors 'none'" in csp
    assert "script-src 'self';" in csp  # no inline or third-party scripts in the app


def test_only_swagger_docs_may_load_its_cdn_scripts(client):
    csp = client.get("/api/docs").headers["content-security-policy"]
    assert "https://cdn.jsdelivr.net" in csp


def test_no_cross_origin_access_is_granted(client):
    response = client.get("/api/regions", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("request_args", [
    ("get", "/api/regions", {"params": {"q": "x" * 101}}),
    ("get", "/api/screening", {"params": {"county": "x" * 101}}),
    ("get", "/api/regions/" + "9" * 17, {}),
    ("post", "/api/summaries", {"json": {"region_id": "9" * 17}}),
    ("get", "/api/compare", {"params": {"region_ids": [str(i) for i in range(13)]}}),
])
def test_oversized_inputs_are_rejected(client, request_args):
    method, path, kwargs = request_args
    assert getattr(client, method)(path, **kwargs).status_code == 422


def test_injection_strings_are_treated_as_data(client):
    assert client.get("/api/regions", params={"q": "' OR 1=1 --"}).json()["total"] == 0
    assert client.get("/api/regions/' OR '1'='1").status_code == 404


@pytest.mark.parametrize("path", [
    "/..%2f..%2fbackend%2fapi%2fapi.py", "/%2e%2e/%2e%2e/README.md", "/assets/..%2f..%2f..%2fREADME.md",
])
def test_static_route_never_serves_files_outside_the_build(client, path):
    if not (api.FRONTEND_DIST / "index.html").is_file():
        pytest.skip("frontend not built")
    response = client.get(path)
    assert "import " not in response.text and "# DER Data UROP" not in response.text


def test_summary_misstating_its_evidence_is_withheld(mutable_client):
    client, path = mutable_client
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            "UPDATE summary_responses SET summary_text = ? "
            "WHERE region_id = '90001' AND category = 'model_pv'",
            ("The PV residual ranked at the 3rd percentile; the observed value was zero.",),
        )
        conn.commit()
    body = summary(client, "90001", "model_pv")
    assert body["status"] == "unavailable"
    assert body["summary_text"] is None
    assert "misstates the evidence" in body["warnings"][0]
    assert body["evidence"]


# --- definitions ----------------------------------------------------------------

def test_definitions_cover_everything_the_app_shows(client, fixture_db):
    body = client.get("/api/definitions").json()
    assert {t["term"] for t in body["terms"]} >= {"Priority", "Residual", "Residual rank"}
    defined = {m["metric_name"] for m in body["metrics"]}
    with closing(sqlite3.connect(fixture_db)) as conn:
        stored = {r[0] for r in conn.execute("SELECT DISTINCT metric_name FROM metric_observations")}
        outcomes = {r[0] for r in conn.execute("SELECT DISTINCT outcome_name FROM model_outputs")}
        specs = {r[0].split(" | ")[-2] if " | " in r[0] else r[0]
                 for r in conn.execute("SELECT DISTINCT model_version FROM model_outputs")}
    assert stored <= defined
    assert outcomes <= {o["outcome_name"] for o in body["outcomes"]}
    assert specs <= {s["name"] for s in body["specifications"]}
    rules = {o["outcome_name"]: o["flag_rule"] for o in body["outcomes"]}
    assert (rules["y_pv"], rules["energy_burden_pct"], rules["any_turbines"]) == ("low", "high", "absolute")


def test_frontend_labels_match_the_catalog():
    # The UI keeps its own label map for synchronous rendering; keep it honest.
    import re
    from pathlib import Path
    from backend import catalog
    source = (Path(__file__).resolve().parents[1] / "frontend/src/lib/labels.ts").read_text()
    block = source[source.index("METRIC_LABELS"):source.index("};", source.index("METRIC_LABELS"))]
    ui = dict(re.findall(r"(\w+): \"([^\"]+)\"", block))
    for name, (label, _) in catalog.METRIC_DEFINITIONS.items():
        assert ui.get(name) == label, name
