"""Build a small synthetic database for development, tests, and the demo deploy.

Every value here is SYNTHETIC. Region IDs are real California ZCTAs so the map
and county labels look plausible, but metrics, model outputs, and summaries are
generated from a seeded random draw and must never be read as findings.

The fixture goes through the production path on purpose: it writes the same four
processed CSVs the pipeline produces, then calls build_database, which runs the
real loaders, evidence formatting, and validation. Summaries are stored through
generate_summaries.store_summary_response with deterministic template text and
model_version ``fixture_template_v1``, so no LLM or API key is involved.

    python -m backend.fixtures.build_fixture_db            # data/der_fixture.db
    python -m backend.fixtures.build_fixture_db --database /tmp/der.db --replace
"""

import argparse
import json
import math
import random
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from backend.database import PROJECT_ROOT
from backend.formatting import format_metric_value
from backend.schemas.build_database import build_database
from backend.schemas.generate_summaries import (
    INSUFFICIENT_DATA_OVERVIEW,
    SummaryPayload,
    store_summary_response,
)


DEFAULT_PATH = PROJECT_ROOT / "data" / "der_fixture.db"
FIXTURE_VERSION = "fixture_template_v1"
GENERATED_AT = "2026-01-01T00:00:00+00:00"
SEED = 20260101

# (zcta, county, lat, lon, utility acronym, income tier 0-1, wind site)
REGIONS = [
    ("90001", "Los Angeles", 33.973, -118.249, "LADWP", 0.10, False),
    ("90011", "Los Angeles", 34.007, -118.258, "LADWP", 0.08, False),
    ("90049", "Los Angeles", 34.069, -118.470, "LADWP", 0.95, False),
    ("90210", "Los Angeles", 34.090, -118.410, "SCE", 0.98, False),
    ("91331", "Los Angeles", 34.255, -118.420, "LADWP", 0.30, False),
    ("90731", "Los Angeles", 33.730, -118.280, "LADWP", 0.35, False),
    ("94601", "Alameda", 37.776, -122.218, "PG&E", 0.25, False),
    ("94611", "Alameda", 37.830, -122.210, "PG&E", 0.90, False),
    ("94704", "Alameda", 37.866, -122.257, "PG&E", 0.40, False),
    ("94541", "Alameda", 37.674, -122.087, "PG&E", 0.50, False),
    ("93701", "Fresno", 36.749, -119.787, "PG&E", 0.05, False),
    ("93711", "Fresno", 36.830, -119.830, "PG&E", 0.75, False),
    ("93654", "Fresno", 36.600, -119.450, None, 0.30, False),
    ("92101", "San Diego", 32.720, -117.160, "SDG&E", 0.70, False),
    ("92037", "San Diego", 32.850, -117.250, "SDG&E", 0.97, False),
    ("92154", "San Diego", 32.570, -117.000, "SDG&E", 0.35, False),
    ("93301", "Kern", 35.380, -119.020, "PG&E", 0.20, False),
    ("93501", "Kern", 35.050, -118.170, "SCE", 0.30, True),
    ("92243", "Imperial", 32.790, -115.560, "IID", 0.15, False),
    ("92227", "Imperial", 32.980, -115.530, "IID", 0.12, False),
    ("95814", "Sacramento", 38.580, -121.490, "SMUD", 0.55, False),
    ("95823", "Sacramento", 38.470, -121.440, "SMUD", 0.22, False),
    ("92262", "Riverside", 33.840, -116.540, "SCE", 0.60, True),
    ("93505", "Kern", 35.130, -117.980, "SCE", 0.28, False),
]

UTILITIES = {
    "LADWP": ("Los Angeles Department of Water and Power", "Publicly Owned Utility"),
    "SCE": ("Southern California Edison", "Investor Owned Utility"),
    "PG&E": ("Pacific Gas and Electric Company", "Investor Owned Utility"),
    "SDG&E": ("San Diego Gas & Electric", "Investor Owned Utility"),
    "IID": ("Imperial Irrigation District", "Publicly Owned Utility"),
    "SMUD": ("Sacramento Municipal Utility District", "Publicly Owned Utility"),
}

# Only reported DER observations exist here, all zero: exercises the
# not-enough-data overview, as thin rural ZCTAs do in the real build.
THIN_REGION = "93505"
# Has metrics and model outputs but no stored summaries: exercises the
# API's explicit unavailable fallback.
NO_SUMMARY_REGION = "94541"

DER_COLUMNS = (
    "PV_system_size_DC", "storage_capacity_mw", "total_chargers", "level1_chargers",
    "level2_chargers", "dc_fast_chargers", "wind_capacity_mw", "wind_turbine_count",
)

MODELS = {
    "y_pv": ("Model 1 baseline (climate controls)",
             "Model 7 (infrastructure controls, outcome-safe)"),
    "y_storage": ("Model 1 baseline (climate controls)",
                  "Model 9 + pv control (most controlled)"),
    "y_chargers": ("Model 1 baseline (climate controls)",
                   "Model 7 (infrastructure controls, outcome-safe)"),
    "energy_burden_pct": ("Model 1 baseline (climate controls)",
                          "Model 9A (predicting burden)"),
}
DER_OUTCOMES = {"y_pv", "y_storage", "y_chargers"}


def _hexagon_wkt(lat, lon, radius=0.025):
    # Longitude degrees shrink with latitude; widen them so shapes look regular.
    scale = 1 / math.cos(math.radians(lat))
    points = [
        (lon + radius * scale * math.cos(math.radians(a)),
         lat + radius * math.sin(math.radians(a)))
        for a in range(0, 360, 60)
    ]
    points.append(points[0])
    return "POLYGON ((" + ", ".join(f"{x:.5f} {y:.5f}" for x, y in points) + "))"


def _clamp(value, low, high):
    return max(low, min(high, value))


def synthetic_frames(seed=SEED):
    """Return the four processed tables the database builder reads."""
    rng = random.Random(seed)
    dataset, shapes, utilities = [], [], []

    for zcta, county, lat, lon, acronym, tier, wind_site in REGIONS:
        noise = lambda scale=1.0: rng.gauss(0, 0.08 * scale)  # noqa: E731
        population = rng.randint(9_000, 62_000)
        row = {"zip_code": int(zcta), "county": county}
        if zcta == THIN_REGION:
            row.update({column: 0.0 for column in DER_COLUMNS})
        else:
            hispanic = _clamp(0.85 - 0.7 * tier + noise(), 0.03, 0.95)
            black = _clamp(0.12 * (1 - tier) + noise(0.4), 0.0, 0.4)
            asian = _clamp(0.06 + 0.2 * tier + noise(0.5), 0.0, 1 - hispanic - black)
            owner = _clamp(0.25 + 0.55 * tier + noise(), 0.1, 0.9)
            pv_per_capita_kw = _clamp(0.04 + 0.35 * tier * owner + noise(0.5), 0.005, 0.6)
            pv_mw = population * pv_per_capita_kw / 1000
            level2 = max(0, round(population / 1000 * (0.4 + 4 * tier) + rng.gauss(0, 3)))
            level1 = max(0, round(level2 * rng.uniform(0.02, 0.12)))
            dcfc = max(0, round(level2 * rng.uniform(0.05, 0.3) - 1))
            income = 28_000 + 190_000 * tier ** 1.4 + rng.gauss(0, 6_000)
            row.update({
                "total_population": population,
                "median_household_income": round(income, -2),
                "poverty_rate": _clamp(0.32 - 0.29 * tier + noise(0.5), 0.02, 0.5),
                "pct_bachelors_plus": _clamp(0.06 + 0.7 * tier + noise(), 0.02, 0.92),
                "pct_black": black,
                "pct_hispanic": hispanic,
                "pct_asian": asian,
                "median_housing_value": round(240_000 + 2_600_000 * tier ** 2.2, -3),
                "pct_single_family_units": _clamp(0.35 + 0.45 * owner + noise(), 0.1, 0.95),
                "pct_multifamily_units": _clamp(0.6 - 0.45 * owner + noise(), 0.03, 0.85),
                "pct_mobile_home_units": _clamp(0.02 + noise(0.2), 0.0, 0.15),
                "pct_other_housing_units": _clamp(0.004 + noise(0.02), 0.0, 0.02),
                "owner_occupied_rate": owner,
                "PV_system_size_DC": pv_mw,
                "storage_capacity_mw": pv_mw * _clamp(0.04 + 0.1 * tier + noise(0.3), 0.0, 0.3),
                "total_chargers": level1 + level2 + dcfc,
                "level1_chargers": level1,
                "level2_chargers": level2,
                "dc_fast_chargers": dcfc,
                "wind_capacity_mw": rng.uniform(40, 320) if wind_site else 0.0,
                "wind_turbine_count": rng.randint(30, 210) if wind_site else 0,
                # Stored as a share, as rebuild_processed_data.py writes it (0.046 = 4.6%).
                "energy_burden_pct": _clamp(0.046 - 0.034 * tier + noise(0.04), 0.008, 0.075),
                "energy_affordability_index": _clamp(80 - 70 * tier + noise(60), 1, 99),
                "energy_affordability_gap": max(0.0, 2_600_000 * (1 - tier) ** 2
                                                + rng.gauss(0, 120_000)),
                "kwh_annual_total": population * rng.uniform(1_900, 3_400),
                "cdd65_2023": _clamp(400 + (37.5 - lat) * 700 + (-lon - 118) * -120
                                     + rng.gauss(0, 150), 50, 4_200),
                "hdd65_2023": _clamp(900 + (lat - 32.5) * 380 + rng.gauss(0, 120), 400, 3_400),
                "ghi_mean_kwh_m2_day_2023": _clamp(5.9 - (lat - 32.5) * 0.18
                                                   + rng.gauss(0, 0.1), 4.4, 6.2),
                "wind_ws10m_mean_2023": _clamp(rng.uniform(2.6, 3.6) + (2.4 if wind_site else 0),
                                               1.5, 7.5),
                "wind_ws50m_mean_2023": _clamp(rng.uniform(3.6, 4.9) + (3.0 if wind_site else 0),
                                               2.5, 9.5),
            })
        dataset.append(row)
        shapes.append({"zip_code": int(zcta), "geometry": _hexagon_wkt(lat, lon)})
        if acronym is not None:
            name, kind = UTILITIES[acronym]
            utilities.append({
                "zip_code": int(zcta), "acronym": acronym,
                "utility": name, "utility_type": kind,
            })

    df = pd.DataFrame(dataset)
    return df, pd.DataFrame(shapes), pd.DataFrame(utilities), model_frame(df, rng)


def model_frame(df, rng):
    """Synthetic predictions with percentile and priority semantics of the real ones."""
    fitted = df[df["zip_code"].astype(str).str.zfill(5) != THIN_REGION]
    actual_by_outcome = {
        "y_pv": fitted["PV_system_size_DC"] / fitted["total_population"] * 1000,
        "y_storage": fitted["storage_capacity_mw"] / fitted["total_population"] * 1000,
        "y_chargers": fitted["total_chargers"] / fitted["total_population"] * 1000,
        "energy_burden_pct": fitted["energy_burden_pct"],
    }
    rows = []
    for outcome, versions in MODELS.items():
        actual = actual_by_outcome[outcome]
        spread = float(actual.std())
        for version in versions:
            # Richer specifications explain more, so their residuals shrink.
            scale = 0.7 if version.startswith("Model 1 ") else 0.4
            residuals = [rng.gauss(0, spread * scale) for _ in actual]
            ranks = pd.Series(residuals).rank(pct=True).tolist()
            for zcta, value, residual, pct in zip(
                fitted["zip_code"], actual, residuals, ranks
            ):
                flagged = pct <= 0.25 if outcome in DER_OUTCOMES else pct >= 0.75
                rows.append({
                    "region_id": int(zcta),
                    "outcome_name": outcome,
                    "model_version": version,
                    "actual_value": float(value),
                    "predicted_value": float(value) - residual,
                    "residual_value": residual,
                    "residual_percentile": pct,
                    "priority_flag": int(flagged),
                    "assumptions": (
                        "SYNTHETIC fixture output. Real outputs come from OLS "
                        "specifications in notebooks/regression.ipynb fitted on "
                        "ZCTA-level 2023 data; residuals are screening signals, "
                        "not causal effects."
                    ),
                    "generated_at": GENERATED_AT,
                })
    return pd.DataFrame(rows)


def write_processed_dir(directory, seed=SEED):
    directory = Path(directory)
    dataset, shapes, utilities, models = synthetic_frames(seed)
    dataset.to_csv(directory / "combined_der_dataset_w_controls_predictors.csv", index=False)
    shapes.to_csv(directory / "combined_der_dataset_w_shape.csv", index=False)
    utilities.to_csv(directory / "zip_to_utility.csv", index=False)
    models.to_csv(directory / "model_outputs_by_region.csv", index=False)
    return directory


def _evidence(conn, region_id, evidence_type, like=None):
    query = (
        "SELECT evidence_id, evidence_text FROM evidence_chunks "
        "WHERE region_id = ? AND evidence_type = ?"
    )
    params = [region_id, evidence_type]
    if like is not None:
        query += " AND evidence_text LIKE ?"
        params.append(like)
    return conn.execute(query + " ORDER BY evidence_id", params).fetchall()


def _metrics(conn, region_id, category):
    return conn.execute(
        "SELECT metric_name, metric_value, metric_unit FROM metric_observations "
        "WHERE region_id = ? AND metric_category = ? ORDER BY metric_name",
        (region_id, category),
    ).fetchall()


def _store(conn, region_id, category, text, evidence_ids, snapshot):
    store_summary_response(
        conn, region_id, category,
        SummaryPayload(summary_text=text, evidence_ids_used=evidence_ids),
        {"region_id": region_id, "category": category, "fixture": True, **snapshot},
        model_version=FIXTURE_VERSION,
        generated_at=GENERATED_AT,
    )


def store_template_summaries(conn):
    """Deterministic, evidence-linked summaries standing in for LLM output."""
    region_ids = [row[0] for row in conn.execute("SELECT region_id FROM regions ORDER BY 1")]
    for region_id in region_ids:
        if region_id == NO_SUMMARY_REGION:
            continue
        der = {m["metric_name"]: m for m in _metrics(conn, region_id, "der_observed")}
        der_evidence = [
            row["evidence_id"] for row in _evidence(conn, region_id, "metric")
            if any(f" {name} " in row["evidence_text"] for name in der)
        ]
        pv = format_metric_value(der["PV_system_size_DC"]["metric_value"], "MW")
        chargers = format_metric_value(der["total_chargers"]["metric_value"], "chargers")
        observed_text = (
            f"[Synthetic fixture] ZCTA {region_id} reports {pv} of PV capacity and "
            f"{chargers} in the processed observations. Recorded zeros reflect an "
            "absence of records, not confirmed absence of infrastructure."
        )
        _store(conn, region_id, "observed_der", observed_text, der_evidence,
               {"PV_system_size_DC": pv, "total_chargers": chargers})

        if region_id == THIN_REGION:
            _store(conn, region_id, "overview", INSUFFICIENT_DATA_OVERVIEW, der_evidence,
                   {"insufficient_data": True, "source_categories": ["observed_der"]})
            continue

        pv_models = [row for row in _evidence(conn, region_id, "model_output", "%for y_pv %")]
        flagged = sum("Priority status: flagged" in row["evidence_text"] for row in pv_models)
        model_text = (
            f"[Synthetic fixture] {flagged} of {len(pv_models)} PV specifications flag "
            f"ZCTA {region_id} as a priority region, meaning observed PV per capita "
            "sits at or below the 25th-percentile residual. Treat this as a screening "
            "signal, not a causal estimate."
        )
        pv_ids = [row["evidence_id"] for row in pv_models]
        _store(conn, region_id, "model_pv", model_text, pv_ids,
               {"pv_specifications": len(pv_models), "pv_flagged": flagged})

        social = {m["metric_name"]: m for m in _metrics(conn, region_id, "socioeconomic")}
        income = format_metric_value(social["median_household_income"]["metric_value"], "dollars")
        income_ids = [
            row["evidence_id"] for row in _evidence(
                conn, region_id, "metric", "%median_household_income%")
        ]
        overview_text = (
            f"[Synthetic fixture] ZCTA {region_id} has a median household income of "
            f"{income}, reports {pv} of PV and {chargers}, and is flagged by "
            f"{flagged} of {len(pv_models)} PV screening specifications."
        )
        _store(conn, region_id, "overview", overview_text,
               income_ids + der_evidence[:2] + pv_ids,
               {"median_household_income": income, "pv_flagged": flagged})
    conn.commit()


def build_fixture_database(path=DEFAULT_PATH, *, replace=False, seed=SEED):
    path = Path(path).expanduser().resolve()
    with tempfile.TemporaryDirectory() as tmp:
        write_processed_dir(tmp, seed)
        build_database(path, processed_dir=tmp, replace_existing=replace)
    with closing(sqlite3.connect(path)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        store_template_summaries(conn)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--replace", action="store_true",
                        help="Replace an existing fixture database (a backup is kept).")
    args = parser.parse_args(argv)
    path = build_fixture_database(args.database, replace=args.replace)
    print(json.dumps({"fixture_database": str(path), "synthetic": True}))


if __name__ == "__main__":
    main()
