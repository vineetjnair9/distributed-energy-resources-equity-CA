import json
import sqlite3
from types import SimpleNamespace

import pytest

from backend.schemas import create_db, generate_summaries, populate_tables


class FakeResponses:
    def __init__(self):
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["text_format"] is generate_summaries.SectionBatchPayload:
            request = json.loads(kwargs["input"])
            sections = [
                generate_summaries.SectionSummaryPayload(
                    category=packet["category"],
                    summary_text=f"Summary for {packet['category']}.",
                    evidence_ids_used=[packet["evidence"][0]["evidence_id"]],
                )
                for packet in request["category_packets"]
            ]
            payload = generate_summaries.SectionBatchPayload(sections=sections)
        else:
            payload = generate_summaries.SummaryPayload(
                summary_text="Integrated overview.",
                evidence_ids_used=[1, 2],
            )
        return SimpleNamespace(
            output_parsed=payload,
            usage=SimpleNamespace(input_tokens=100, output_tokens=20),
        )


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


@pytest.fixture
def summary_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(create_db.SCHEMA)
    conn.execute(
        "INSERT INTO regions (region_id, region_type) VALUES ('90001', 'ZCTA')"
    )
    metrics = [
        (
            "total_population",
            10_000,
            "people",
            "demographic",
            "ACS 5-year",
            "2023",
        ),
        (
            "PV_system_size_DC",
            2.5,
            "MW",
            "der_observed",
            "LBNL Tracking the Sun processed",
            "2023",
        ),
    ]
    for metric_name, value, unit, category, source, observed_at in metrics:
        conn.execute(
            """
            INSERT INTO metric_observations (
                region_id, metric_name, metric_value, metric_unit,
                metric_category, source_name, observed_at
            ) VALUES ('90001', ?, ?, ?, ?, ?, ?)
            """,
            (metric_name, value, unit, category, source, observed_at),
        )
        conn.execute(
            """
            INSERT INTO evidence_chunks (
                region_id, evidence_text, source_name, evidence_type, created_at
            ) VALUES ('90001', ?, ?, 'metric', '2026-01-01')
            """,
            (
                f"For region 90001, {source} metric {metric_name} is {value} {unit}.",
                source,
            ),
        )
    conn.commit()
    yield conn
    conn.close()


def test_two_call_flow_is_scoped_atomic_and_idempotent(summary_db, monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr(generate_summaries, "_client", fake_client)
    categories = ("community_demographics", "observed_der")

    batch = generate_summaries.generate_and_store_section_batch(
        summary_db, "90001", categories
    )
    overview = generate_summaries.generate_and_store_overview(summary_db, "90001")

    assert batch.changed is True
    assert overview is not None and overview.changed is True
    assert summary_db.execute("SELECT COUNT(*) FROM summary_responses").fetchone()[0] == 3
    assert [
        row[0]
        for row in summary_db.execute(
            "SELECT task_type FROM llm_usage_log ORDER BY usage_id"
        )
    ] == ["category_summary_batch", "category_summary:overview"]
    assert len(fake_client.responses.calls) == 2
    assert all(
        call["model"] == "gpt-5.6-luna"
        and call["reasoning"] == {"effort": "none"}
        for call in fake_client.responses.calls
    )

    generate_summaries.generate_and_store_section_batch(
        summary_db, "90001", categories
    )
    generate_summaries.generate_and_store_overview(summary_db, "90001")
    assert len(fake_client.responses.calls) == 2
    assert summary_db.execute("SELECT COUNT(*) FROM summary_responses").fetchone()[0] == 3
    assert summary_db.execute("SELECT COUNT(*) FROM llm_usage_log").fetchone()[0] == 2


def test_batch_validation_rejects_cross_category_evidence(summary_db):
    evidence_by_category = {
        category: generate_summaries.get_evidence_for_category(
            summary_db, "90001", category
        )
        for category in ("community_demographics", "observed_der")
    }
    demographic_id = evidence_by_category["community_demographics"][0]["evidence_id"]
    observed_id = evidence_by_category["observed_der"][0]["evidence_id"]
    payload = generate_summaries.SectionBatchPayload(
        sections=[
            generate_summaries.SectionSummaryPayload(
                category="community_demographics",
                summary_text="Demographic summary.",
                evidence_ids_used=[observed_id],
            ),
            generate_summaries.SectionSummaryPayload(
                category="observed_der",
                summary_text="Observed DER summary.",
                evidence_ids_used=[demographic_id],
            ),
        ]
    )

    with pytest.raises(ValueError, match="not in its packet"):
        generate_summaries.validate_section_batch_payload(
            payload, evidence_by_category
        )


def _model_evidence_rows(comparison_model):
    return [
        {
            "model_version": (
                "energy_burden_pct | Model 1 baseline (climate controls) | raw"
            )
        },
        {"model_version": f"energy_burden_pct | {comparison_model} | raw"},
    ]


def test_affordability_rules_describe_selected_model_9a():
    rules = generate_summaries.category_task_rules(
        "model_energy_burden",
        _model_evidence_rows("Model 9A (predicting burden)"),
    )

    assert "Model 9A (predicting burden)" in rules
    assert "different descriptive prediction question" in rules
    assert "added-control robustness/context" not in rules


def test_affordability_rules_do_not_name_unselected_model_9a():
    rules = generate_summaries.category_task_rules(
        "model_energy_burden",
        _model_evidence_rows(
            "Model 7 (infrastructure controls, outcome-safe)"
        ),
    )

    assert "Model 9A" not in rules
    assert "Model 7 (infrastructure controls, outcome-safe)" in rules
    assert "added-control robustness/context" in rules


def test_metric_evidence_includes_year_and_affordability_definition():
    text = populate_tables.format_metric_evidence(
        {
            "region_id": "90001",
            "metric_name": "energy_affordability_gap",
            "metric_value": 6_111_343,
            "metric_unit": "dollars",
            "metric_category": "energy_affordability",
            "source_name": "Energy burden Tableau export",
            "observed_at": "2023",
        }
    )

    assert "$6,111,343" in text
    assert "population-weighted measure" in text
    assert "burdens above 7%" in text
    assert "Observation period: 2023." in text

    rules = generate_summaries.category_task_rules("energy_affordability")
    assert "define each available measure" in rules
    assert "what the index combines" in rules
    assert "stated affordability threshold" in rules


def _model_row(**overrides):
    row = {
        "region_id": "90005",
        "outcome_name": "any_turbines",
        "model_version": "any_turbines | Model 1 baseline (climate controls) | raw",
        "actual_value": 0,
        "predicted_value": -0.0024,
        "residual_value": 0.0024,
        "residual_percentile": 0.85,
        "priority_flag": 0,
    }
    row.update(overrides)
    return row


def test_negative_fitted_value_is_disclosed_not_read_as_surplus():
    text = populate_tables.format_model_evidence(_model_row())

    assert "predicted value is below zero" in text
    assert "observed value is zero" in text
    assert "rather than observed deployment above the prediction" in text


def test_positive_residual_on_nonzero_observation_gets_no_zero_caveat():
    text = populate_tables.format_model_evidence(
        _model_row(actual_value=4.0, predicted_value=3.0, residual_value=1.0)
    )

    assert "below zero" not in text
    assert "observed value is zero" not in text


def test_near_degenerate_outcome_carries_a_variation_caveat():
    text = populate_tables.format_model_evidence(
        _model_row(), {"any_turbines": 0.974}
    )

    assert "97% of fitted regions" in text
    assert "not evidence of an observed shortfall" in text

    unaffected = populate_tables.format_model_evidence(
        _model_row(outcome_name="y_pv"), {"y_pv": 0.05}
    )
    assert "of fitted regions" not in unaffected


def test_percentile_rounding_onto_the_cutoff_defers_to_priority_status():
    flagged = populate_tables.format_model_evidence(
        _model_row(
            outcome_name="y_chargers",
            model_version="y_chargers | Model 1 baseline (climate controls) | raw",
            actual_value=0.17,
            predicted_value=0.65,
            residual_value=-0.48,
            residual_percentile=0.2506,
            priority_flag=1,
        )
    )
    unflagged = populate_tables.format_model_evidence(
        _model_row(
            outcome_name="y_chargers",
            model_version="y_chargers | Model 8 add demand proxy | raw",
            actual_value=0.28,
            predicted_value=0.74,
            residual_value=-0.47,
            residual_percentile=0.2508,
            priority_flag=0,
        )
    )

    # Both round to the 25th percentile but land on opposite sides of the flag,
    # so neither may present the rounded figure as the deciding rule.
    for text in (flagged, unflagged):
        assert "25th percentile" in text
        assert "not the rounded percentile, determines whether this region" in text

    assert "Priority status: flagged." in flagged
    assert "Priority status: not flagged." in unflagged


def test_percentile_away_from_the_cutoff_stays_plain():
    text = populate_tables.format_model_evidence(
        _model_row(outcome_name="y_pv", residual_percentile=0.15, priority_flag=1)
    )

    assert "15th percentile within the fitted sample." in text
    assert "rounds to the outcome-model" not in text


def test_overview_is_stale_when_a_section_is_newer(summary_db):
    conn = summary_db
    sources = [
        generate_summaries.OverviewSource(
            summary_id=1,
            category="observed_der",
            summary_text="Sections.",
            evidence_ids=[1],
            generated_at="2026-08-19T08:07:29+00:00",
        )
    ]
    conn.execute(
        """
        INSERT INTO summary_responses (
            category, region_id, summary_text, metric_snapshot,
            model_version, generated_at
        )
        VALUES ('overview', '90001', 'Overview.', '{}', ?, ?)
        """,
        (generate_summaries.SUMMARY_VERSION, "2026-08-19T08:01:53+00:00"),
    )
    conn.commit()

    assert generate_summaries.overview_is_stale(conn, "90001", sources) is True

    sources[0].generated_at = "2026-08-19T08:00:00+00:00"
    assert generate_summaries.overview_is_stale(conn, "90001", sources) is False


def test_overview_prompt_names_categories_with_no_summary():
    sources = [
        generate_summaries.OverviewSource(
            summary_id=1,
            category="observed_der",
            summary_text="Reported DER.",
            evidence_ids=[1],
        )
    ]

    _, prompt = generate_summaries.build_overview_prompt(
        "90010",
        sources,
        ["energy_affordability", "model_energy_burden"],
    )

    assert "not assessed" in prompt
    assert "energy_affordability, model_energy_burden" in prompt

    _, complete = generate_summaries.build_overview_prompt("90001", sources)
    assert "(not assessed): none" in complete


def test_agreement_clause_reports_full_set_direction():
    agreement = {("90005", "any_turbines"): (7, 15)}
    text = populate_tables.format_model_evidence(_model_row(), None, agreement)
    assert "Across all 15 fitted specifications" in text
    assert "the residual is positive in 8." in text

    unanimous = populate_tables.format_model_evidence(
        _model_row(), None, {("90005", "any_turbines"): (18, 18)}
    )
    assert "the residual is negative in 18." in unanimous

    # Without the mapping the clause is simply absent.
    assert "fitted specifications" not in populate_tables.format_model_evidence(
        _model_row()
    )


def test_model_selection_takes_four_specs_in_fallback_order():
    rows = [
        {"evidence_id": 1, "model_version": "y_pv | Model 1 baseline (climate controls) | raw"},
        {"evidence_id": 2, "model_version": "y_pv | Model 8 add demand proxy | raw"},
        {"evidence_id": 3, "model_version": "y_pv | Model 2D (add housing structure and tenure) | raw"},
        {"evidence_id": 4, "model_version": "y_pv | Model 6B county fe | raw"},
        {"evidence_id": 5, "model_version": "y_pv | Model 7 (infrastructure controls, outcome-safe) | raw"},
    ]
    selected = generate_summaries.select_model_evidence(
        rows, preferred_marker="Model 7 (infrastructure controls, outcome-safe)"
    )

    # baseline, preferred, then 6B and 2D by measured share of dissent revealed.
    assert [row["evidence_id"] for row in selected] == [1, 5, 4, 3]

    # With the preferred specification missing, Model 7 must still be reachable
    # within the three comparison slots, so it outranks Model 8.
    storage_rows = [
        dict(row, model_version=row["model_version"].replace("y_pv", "y_storage"))
        for row in rows
    ]
    without_preferred = generate_summaries.select_model_evidence(
        storage_rows,
        preferred_marker="Model 9 + pv control (most controlled)",
    )
    assert [row["evidence_id"] for row in without_preferred] == [1, 4, 3, 5]


def test_descriptive_truncation_is_logged(summary_db, capsys):
    rows = generate_summaries.get_metric_evidence_for_category(
        summary_db, "90001", ("demographic", "der_observed"), limit=1
    )
    warning = capsys.readouterr().err
    assert len(rows) == 1
    assert "limit is 1" in warning
    assert "dropping PV_system_size_DC" in warning

    # No warning when the packet fits.
    generate_summaries.get_metric_evidence_for_category(
        summary_db, "90001", ("demographic", "der_observed"), limit=20
    )
    assert capsys.readouterr().err == ""


def test_batch_request_mirrors_the_synchronous_call(summary_db):
    from backend.schemas import generate_summaries_batch as gsb

    requests, skipped = gsb.build_section_requests(summary_db, ["90001"], 20)
    assert skipped == []
    assert len(requests) == 1

    request = requests[0]
    assert request["custom_id"] == "sections:90001"
    assert request["url"] == "/v1/responses"

    body = request["body"]
    assert body["model"] == generate_summaries.SUMMARY_MODEL
    # Same model, effort and schema as responses.parse uses synchronously, or the
    # two delivery paths would silently produce different summaries.
    assert body["reasoning"] == {"effort": "none"}
    fmt = body["text"]["format"]
    assert fmt["type"] == "json_schema" and fmt["strict"] is True
    assert "sections" in fmt["schema"]["properties"]

    packets = json.loads(body["input"])["category_packets"]
    assert {p["category"] for p in packets} == {
        "community_demographics",
        "observed_der",
    }


def test_batch_skips_regions_whose_sections_already_exist(summary_db):
    from backend.schemas import generate_summaries_batch as gsb

    for category in ("community_demographics", "observed_der"):
        summary_db.execute(
            """
            INSERT INTO summary_responses (
                category, region_id, summary_text, metric_snapshot,
                model_version, generated_at
            ) VALUES (?, '90001', 'done', '{}', ?, '2026-01-01')
            """,
            (category, generate_summaries.SUMMARY_VERSION),
        )
    summary_db.commit()

    requests, skipped = gsb.build_section_requests(summary_db, ["90001"], 20)
    assert requests == []
    assert skipped == ["90001"]
