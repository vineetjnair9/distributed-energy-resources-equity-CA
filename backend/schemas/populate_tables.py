import sqlite3
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "der_tool.db"
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "combined_der_dataset_w_controls_predictors.csv"
CSV_W_SHAPE_PATH = PROJECT_ROOT / "data" / "processed" / "combined_der_dataset_w_shape.csv"
CSV_UTILITY_PATH = PROJECT_ROOT / "data" / "processed" / "zip_to_utility.csv"
MODEL_OUTPUTS_PATH = PROJECT_ROOT / "data" / "processed" / "model_outputs_by_region.csv"


def _short(path):
    try:
        return path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        return path


def _read_required(path, command, what):
    """Read a pipeline output, naming the command that creates it when absent.

    These live under data/processed, which is not version-controlled, so a fresh
    clone has none of them. Failing with a bare FileNotFoundError sends the reader
    looking for a missing file rather than for the stage that writes it.
    """
    if not path.exists():
        raise SystemExit(
            f"missing {_short(path)} ({what}).\n"
            f"Build it first:  {command}"
        )
    return pd.read_csv(path)


REGION_ID_COL = "zip_code"

METRIC_COLUMNS = {
    "total_population": ("people", "demographic", "ACS 5-year"),
    "population": ("people", "demographic", "ACS 5-year"),
    "median_household_income": ("dollars", "socioeconomic", "ACS 5-year"),
    "poverty_rate": ("share", "socioeconomic", "ACS 5-year"),
    "pct_bachelors_plus": ("share", "education", "ACS 5-year"),
    "pct_black": ("share", "demographic", "ACS 5-year"),
    "pct_hispanic": ("share", "demographic", "ACS 5-year"),
    "pct_asian": ("share", "demographic", "ACS 5-year"),
    "median_housing_value": ("dollars", "housing", "ACS 5-year"),
    "pct_single_family_units": ("share", "housing", "ACS 5-year"),
    "pct_multifamily_units": ("share", "housing", "ACS 5-year"),
    "pct_mobile_home_units": ("share", "housing", "ACS 5-year"),
    "pct_other_housing_units": ("share", "housing", "ACS 5-year"),
    "owner_occupied_rate": ("share", "housing", "ACS 5-year"),
    # rebuild_processed_data.py converts the source kW values to MW before
    # aggregating them by ZCTA.
    "PV_system_size_DC": ("MW", "der_observed", "LBNL Tracking the Sun processed"),
    "storage_capacity_mw": ("MW", "der_observed", "CEC Energy Storage System Survey export"),
    "total_chargers": ("chargers", "der_observed", "CEC ZEV Infrastructure Stats export"),
    "level1_chargers": ("chargers", "der_observed", "CEC ZEV Infrastructure Stats export"),
    "level2_chargers": ("chargers", "der_observed", "CEC ZEV Infrastructure Stats export"),
    "dc_fast_chargers": ("chargers", "der_observed", "CEC ZEV Infrastructure Stats export"),
    "wind_capacity_mw": ("MW", "der_observed", "USGS USWTDB"),
    "wind_turbine_count": ("turbines", "der_observed", "USGS USWTDB"),
    "energy_burden_pct": ("share", "energy_affordability", "Energy burden Tableau export"),
    "energy_affordability_index": ("index", "energy_affordability", "Energy burden Tableau export"),
    "energy_affordability_gap": ("dollars", "energy_affordability", "Energy burden Tableau export"),
    "kwh_annual_total": ("kWh", "demand", "Utility electricity usage by ZIP export"),
    "cdd65_2023": ("degree_days", "weather", "NASA POWER gridded centroid"),
    "hdd65_2023": ("degree_days", "weather", "NASA POWER gridded centroid"),
    "ghi_mean_kwh_m2_day_2023": ("kWh/m2/day", "solar_resource", "NASA POWER gridded centroid"),
    "wind_ws10m_mean_2023": ("m/s", "wind_resource", "NASA POWER gridded centroid"),
    "wind_ws50m_mean_2023": ("m/s", "wind_resource", "NASA POWER gridded centroid"),
}

SOURCE_URLS = {
    "ACS 5-year": "https://www.census.gov/programs-surveys/acs",
    "NASA POWER gridded centroid": "https://power.larc.nasa.gov/",
    "LBNL Tracking the Sun processed": "https://emp.lbl.gov/tracking-the-sun/",
    "CEC Energy Storage System Survey export": "https://www.energy.ca.gov/data-reports/energy-almanac/california-electricity-data/california-energy-storage-system-survey",
    "CEC ZEV Infrastructure Stats export": "https://www.energy.ca.gov/data-reports/energy-almanac/zero-emission-vehicle-and-infrastructure-statistics-collection/electric",
    "USGS USWTDB": "https://energy.usgs.gov/uswtdb/data/",
    "Energy burden Tableau export": "https://www.energy.ca.gov/data-reports/data-exploration-tools/energy-equity-indicators-dashboard-collection/deep-dive-energy",
    "Utility electricity usage by ZIP export": (
        "https://www.sce.com/regulatory/regulatory-information/energy-data-reports-compliances; "
        "https://pge-energydatarequest.com/public_datasets; "
        "https://energydata.sdge.com"
    ),
    "Regression model outputs": None,
}

MODEL_COLUMNS = {
    "pv_model_score": "pv_adoption_score",
    "storage_model_score": "storage_adoption_score",
    "charger_model_score": "charger_adoption_score",
}

METRIC_INTERPRETATIONS = {
    "pct_black": "This is the non-Hispanic Black share of the population.",
    "pct_hispanic": "This is the Hispanic or Latino share of the population, of any race.",
    "pct_asian": "This is the non-Hispanic Asian share of the population.",
    "poverty_rate": (
        "This is the share of the population for whom poverty status was determined "
        "that is below the poverty line."
    ),
    "pct_bachelors_plus": (
        "This is the share of residents age 25 or older with a bachelor's degree "
        "or higher."
    ),
    "pct_single_family_units": (
        "This is the share of all housing units that are single-family."
    ),
    "pct_multifamily_units": (
        "This is the share of all housing units that are multifamily."
    ),
    "pct_mobile_home_units": (
        "This is the share of all housing units that are mobile homes."
    ),
    "pct_other_housing_units": (
        "This is the share of all housing units in other structures."
    ),
    "owner_occupied_rate": (
        "This is the share of occupied housing units that are owner-occupied."
    ),
    "PV_system_size_DC": (
        "This is aggregate reported PV capacity in the processed Tracking the Sun data."
    ),
    "kwh_annual_total": (
        "This is the electricity usage reported for this ZIP in the utility export. "
        "Coverage is uneven across ZIPs and utilities, so treat it as reported usage "
        "for the accounts present in that export, not as total ZCTA consumption."
    ),
    "energy_burden_pct": (
        "This is the percentage of income spent on energy annually. It is a "
        "ZCTA-level figure and is not a household burden, so it cannot be compared "
        "against the 7% household affordability threshold."
    ),
    "energy_affordability_gap": (
        "The CEC defines this as a population-weighted measure of the gap between "
        "affordable and unaffordable energy burdens; burdens above 7% are treated "
        "as unaffordable in this analysis."
    ),
    "energy_affordability_index": (
        "The CEC index combines the percentile of financial energy burden with the "
        "percentile of disposable income per person to represent household burden "
        "and ability to respond to energy-price changes."
    ),
}

DER_PRIORITY_OUTCOMES = {
    "y_pv",
    "y_storage",
    "y_chargers",
    "y_level1_chargers",
    "y_level2_chargers",
    "y_dc_fast_chargers",
    "y_wind_mw",
}
BURDEN_PRIORITY_OUTCOMES = {
    "energy_burden_pct",
    "energy_affordability_index",
    "log_energy_gap_per_capita",
}

# Above this share of zero observations an outcome carries too little variation
# for a residual percentile to describe an observed shortfall: the ranking is
# driven by the fitted values instead.
NEAR_DEGENERATE_ZERO_SHARE = 0.95


def build_id_lookup(conn, table_name, id_column, lookup_column):
    """
    Build a dictionary mapping a human-readable value to a database ID.

    Example:
        {"Pacific Gas & Electric Company": 1}
    """
    rows = conn.execute(
        f"""
        SELECT {id_column}, {lookup_column}
        FROM {table_name}
        """
    ).fetchall()

    return {
        row[lookup_column]: row[id_column]
        for row in rows
    }


def clean_region_id(value):
    """
    Keeps ZCTAs as 5-character strings.
    Example: 9001 -> '09001'
    """
    if pd.isna(value):
        return None
    return str(value).split(".")[0].zfill(5)


def source_url_for(source_name):
    """
    Return a stable public URL for source families when available.
    """
    return SOURCE_URLS.get(source_name)


def _trimmed_decimal(value, places):
    formatted = f"{float(value):,.{places}f}".rstrip("0").rstrip(".")
    return "0" if formatted == "-0" else formatted


def format_metric_value(metric_value, metric_unit):
    """Format a stored metric for people rather than exposing database precision."""
    value = float(metric_value)
    if metric_unit == "share":
        return f"{value:.1%}"
    if metric_unit == "dollars":
        return f"${value:,.0f}"
    if metric_unit in {"chargers", "turbines"}:
        label = metric_unit[:-1] if round(value) == 1 else metric_unit
        return f"{value:,.0f} {label}"
    if metric_unit in {"people", "kWh"}:
        return f"{value:,.0f} {metric_unit}"
    if metric_unit == "degree_days":
        return f"{value:,.0f} degree days"
    if metric_unit == "index":
        return f"{value:,.1f} index points"
    if metric_unit == "MW":
        return f"{_trimmed_decimal(value, 3)} MW"
    if metric_unit == "kWh/m2/day":
        return f"{_trimmed_decimal(value, 2)} kWh/m²/day"
    if metric_unit == "m/s":
        return f"{_trimmed_decimal(value, 2)} m/s"
    return f"{_trimmed_decimal(metric_value, 3)} {metric_unit}".strip()


def format_metric_evidence(row):
    """
    Build category-aware metric evidence text for the LLM prompt.

    The wording intentionally carries provenance and interpretation context so
    generated summaries do not overstate coarse gridded weather controls or
    processed outcome variables.
    """
    region_id = row["region_id"]
    metric_name = row["metric_name"]
    display_value = format_metric_value(row["metric_value"], row["metric_unit"])
    metric_category = row["metric_category"]
    source_name = row["source_name"]
    evidence_text = (
        f"For region {region_id}, {source_name} metric {metric_name} is "
        f"{display_value}."
    )

    interpretation = METRIC_INTERPRETATIONS.get(metric_name)
    if interpretation:
        evidence_text += f" {interpretation}"

    if row["observed_at"] is not None:
        evidence_text += f" Observation period: {row['observed_at']}."

    if metric_category in {"weather", "solar_resource", "wind_resource"}:
        evidence_text += (
            " This is coarse gridded climate or resource context based on the ZCTA "
            "centroid, not a precise ZIP-level measurement."
        )

    return evidence_text


def _format_model_number(value):
    if value is None:
        return "not available"
    return _trimmed_decimal(value, 4)


def _ordinal(percentile):
    if 10 <= percentile % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(percentile % 10, "th")
    return f"{percentile}{suffix}"


def _cutoff_percentile_for_outcome(outcome_name):
    """Return the whole-number percentile at which this outcome's flag switches."""
    if outcome_name in DER_PRIORITY_OUTCOMES:
        return 25
    return 75


def _ordinal_percentile(value):
    percentile = max(0, min(100, round(float(value) * 100)))
    return f"{_ordinal(percentile)} percentile"


def _cutoff_tie_note(value, cutoff):
    """Warn when a rounded percentile lands on the flag cutoff.

    Rounding to a whole number puts values on both sides of a cutoff into the
    same bucket: 0.2506 is flagged and 0.2508 is not, yet both round to the 25th
    percentile. Reported alone that reads as a contradiction against the stated
    "at or below the 25th-percentile cutoff" rule. The cutoff is an empirical
    quantile rather than exactly 25.0, so the rounded figure cannot say which
    side a near-tie falls on; point at the priority status instead.
    """
    if cutoff is None:
        return ""
    if max(0, min(100, round(float(value) * 100))) != cutoff:
        return ""
    return (
        f" That rounds to the outcome-model's {_ordinal(cutoff)}-percentile cutoff, "
        "so the priority status below, not the rounded percentile, determines "
        "whether this region is flagged."
    )


def direction_agreement(conn):
    """Residual sign agreement across every fitted specification, per region.

    The narrative compares a small selected subset, which cannot show how
    contested a residual's direction is: two specs can agree while a third of the
    remaining set disagrees. Counting the full set costs one clause and covers
    every specification instead of only the selected ones.
    """
    return {
        (row["region_id"], row["outcome_name"]): (
            row["negative_count"],
            row["total_count"],
        )
        for row in conn.execute(
            """
            SELECT
                region_id,
                outcome_name,
                SUM(CASE WHEN residual_value < 0 THEN 1 ELSE 0 END) AS negative_count,
                COUNT(*) AS total_count
            FROM model_outputs
            WHERE residual_value IS NOT NULL
            GROUP BY region_id, outcome_name
            """
        ).fetchall()
    }


def zero_share_by_outcome(conn):
    """Share of fitted regions whose observed value is zero, per outcome.

    Used to mark outcomes that are so close to constant that a residual
    percentile ranks fitted values rather than any observed shortfall.
    """
    return {
        row["outcome_name"]: row["zero_share"]
        for row in conn.execute(
            """
            SELECT
                outcome_name,
                AVG(CASE WHEN actual_value = 0 THEN 1.0 ELSE 0.0 END) AS zero_share
            FROM model_outputs
            WHERE actual_value IS NOT NULL
            GROUP BY outcome_name
            """
        ).fetchall()
    }


def format_model_evidence(row, zero_shares=None, agreement=None):
    """Format a model-output evidence row with explicit flag semantics.

    zero_shares maps an outcome to the share of regions observed at zero, as
    returned by zero_share_by_outcome. Supplying it adds the caveat that a
    near-constant outcome cannot support an observed-shortfall reading.

    agreement maps (region, outcome) to (negative_count, total_count) across all
    fitted specifications, as returned by direction_agreement. Supplying it adds
    the full-set directional agreement the selected subset cannot show.
    """
    outcome_name = row["outcome_name"]
    actual = row["actual_value"]
    predicted = row["predicted_value"]
    evidence_text = (
        f"For region {row['region_id']}, model {row['model_version']} "
        f"for {outcome_name} estimated an actual value of "
        f"{_format_model_number(actual)}, a predicted value of "
        f"{_format_model_number(predicted)}, and a residual of "
        f"{_format_model_number(row['residual_value'])}."
    )

    if row["residual_percentile"] is not None:
        percentile = row["residual_percentile"]
        evidence_text += (
            f" The residual ranks at the {_ordinal_percentile(percentile)} "
            "within the fitted sample."
        )
        evidence_text += _cutoff_tie_note(
            percentile,
            _cutoff_percentile_for_outcome(outcome_name),
        )

    # A linear specification can fit a value below zero for an outcome that
    # cannot go below zero. Where it does, a positive residual only records that
    # the fitted value was negative; it does not mean the region has more
    # infrastructure than the model expected.
    if predicted is not None and float(predicted) < 0:
        evidence_text += (
            " The predicted value is below zero, which this linear specification "
            "permits even though the outcome cannot be negative."
        )
        if actual is not None and float(actual) == 0:
            evidence_text += (
                " The observed value is zero, so the positive residual reflects the "
                "negative fitted value rather than observed deployment above the "
                "prediction."
            )

    counts = (agreement or {}).get((row["region_id"], outcome_name))
    if counts is not None:
        negative, total = counts
        if total:
            majority, direction = (
                (negative, "negative") if negative >= total - negative
                else (total - negative, "positive")
            )
            evidence_text += (
                f" Across all {total} fitted specifications for this region and "
                f"outcome, the residual is {direction} in {majority}."
            )

    zero_share = (zero_shares or {}).get(outcome_name)
    if zero_share is not None and zero_share >= NEAR_DEGENERATE_ZERO_SHARE:
        evidence_text += (
            f" This outcome is observed as zero in {round(zero_share * 100)}% of "
            "fitted regions, so its residual percentile mainly orders fitted values "
            "and is not evidence of an observed shortfall in this region."
        )

    if row["priority_flag"] is None:
        return evidence_text

    status = "flagged" if int(row["priority_flag"]) == 1 else "not flagged"
    if outcome_name in DER_PRIORITY_OUTCOMES:
        definition = (
            "For DER outcomes, flagged means the residual is at or below the "
            "outcome-model's 25th-percentile residual cutoff."
        )
    elif outcome_name in BURDEN_PRIORITY_OUTCOMES:
        definition = (
            "For affordability outcomes, flagged means the residual is at or above "
            "the outcome-model's 75th-percentile residual cutoff."
        )
    else:
        definition = (
            "For this outcome, flagged means the absolute residual is at or above "
            "the outcome-model's 75th-percentile absolute-residual cutoff, so a "
            "flag can come from either an unusually low or an unusually high residual."
        )

    return f"{evidence_text} Priority status: {status}. {definition}"


def populate_utilities_table(conn, df_utils):
    """
    Populate the utilities table from a CSV with columns:
    - acronym
    - utility

    Inserts one row per unique utility acronym/name pair.
    """
    if "utility" not in df_utils.columns:
        raise ValueError(f"Missing required utility column in {CSV_UTILITY_PATH}")

    utilities_df = (
        df_utils[["acronym", "utility", "utility_type"]]
        .dropna(subset=["utility"])
        .drop_duplicates(subset=["utility"])
        .rename(columns={
            "acronym": "utility_acronym",
            "utility": "utility_name",
        })
    )

    conn.executemany(
        """
        INSERT OR IGNORE INTO utilities (
            utility_acronym,
            utility_name,
            utility_type
        )
        VALUES (?, ?, ?)
        """,
        utilities_df[["utility_acronym", "utility_name", "utility_type"]].itertuples(
            index=False,
            name=None,
        ),
    )

    conn.commit()

    print(f"Inserted {len(utilities_df)} utilities.")


def populate_geometries_table(conn, df_shape):
    """
    Populate the utilities table from a CSV with columns:
    - acronym
    - utility

    Inserts one row per unique utility acronym/name pair.
    """
    if "geometry" not in df_shape.columns or "zip_code" not in df_shape.columns:
        raise ValueError(f"Missing required columns in {CSV_W_SHAPE_PATH}")

    df_shape = df_shape.copy()
    df_shape["zip_code"] = df_shape["zip_code"].apply(clean_region_id)
    geometries_df = (
        df_shape[["zip_code", "geometry"]]
        .dropna(subset=["geometry", "zip_code"])
        .drop_duplicates(subset=["zip_code"])
        .rename(columns={
            "zip_code": "region_id",
        })
    )
    existing_region_ids = {
        row["region_id"]
        for row in conn.execute(
            """
            SELECT region_id
            FROM regions
            """
        ).fetchall()
    }

    before_count = len(geometries_df)
    geometries_df = geometries_df[
        geometries_df["region_id"].isin(existing_region_ids)
    ].copy()
    skipped_count = before_count - len(geometries_df)
    conn.executemany(
        """
        INSERT OR REPLACE INTO region_geometries (
            region_id,
            geometry_wkt,
            geometry_format,
            crs
        )
        VALUES (?, ?, 'WKT', 'EPSG:4326')
        """,
        geometries_df[["region_id", "geometry"]].itertuples(
            index=False,
            name=None,
        ),
    )

    conn.commit()

    print(f"Inserted {len(geometries_df)} geometries.")
    print(f"Skipped {skipped_count} geometries with no matching region.")


def load_main_dataset():
    """
    Load and clean the main processed DER dataset.
    """
    df = pd.read_csv(CSV_PATH)

    df[REGION_ID_COL] = df[REGION_ID_COL].apply(clean_region_id)
    df = df.dropna(subset=[REGION_ID_COL])

    return df


def populate_regions_table(df, df_utils, conn, utility_lookup):
    """
    Populate the regions table from the main processed DER dataset.
    """
    for _, row in df.iterrows():
        region_id = row[REGION_ID_COL]
        if region_id in df_utils.index:
            utility_name = df_utils.loc[region_id, "utility"]
            utility_id = utility_lookup.get(utility_name)
        else:
            utility_id = None
        county = row["county"] if "county" in df.columns and pd.notna(row.get("county")) else None
        conn.execute(
            """
            INSERT OR REPLACE INTO regions (
                region_id, region_name, region_type, state, county, utility_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                region_id,
                f"ZCTA {region_id}",
                "zcta",
                "CA",
                county,
                utility_id,
            ),
        )

    print("Loaded regions table.")


def populate_metric_observations_table(df, conn):
    """
    Populate the metric_observations table from the main processed DER dataset.
    """
    for _, row in df.iterrows():
        region_id = row[REGION_ID_COL]

        for col, (unit, category, source_name) in METRIC_COLUMNS.items():
            if col not in df.columns:
                continue

            value = row[col]

            if pd.isna(value):
                continue

            conn.execute(
                """
                INSERT OR REPLACE INTO metric_observations (
                    region_id,
                    metric_name,
                    metric_value,
                    metric_unit,
                    metric_category,
                    source_name,
                    observed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    region_id,
                    col,
                    float(value),
                    unit,
                    category,
                    source_name,
                    "2023",
                ),
            )

    print("Loaded metric_observations table.")


def populate_model_outputs_table(df, conn):
    """
    Populate the model_outputs table from model_outputs_by_region.csv.

    Expected CSV columns:
    - region_id
    - outcome_name
    - model_version
    - actual_value
    - predicted_value
    - residual_value
    - residual_percentile
    - priority_flag
    - assumptions
    - generated_at
    """
    required_columns = {
        "region_id",
        "outcome_name",
        "model_version",
        "actual_value",
        "predicted_value",
        "residual_value",
        "residual_percentile",
        "priority_flag",
        "assumptions",
        "generated_at",
    }
    if required_columns - set(df.columns):
        raise ValueError(
            f"Missing required columns in {required_columns - set(df.columns)}"
        )

    df["region_id"] = df["region_id"].apply(clean_region_id)

    df = df.dropna(
        subset=[
            "region_id",
            "outcome_name",
            "model_version",
        ]
    )
    existing_region_ids = {
        row["region_id"]
        for row in conn.execute(
            """
            SELECT region_id
            FROM regions
            """
        ).fetchall()
    }

    before_count = len(df)

    df = df[
        df["region_id"].isin(existing_region_ids)
    ].copy()

    skipped_count = before_count - len(df)

    conn.executemany(
        """
        INSERT OR REPLACE INTO model_outputs (
            region_id,
            outcome_name,
            model_version,
            actual_value,
            predicted_value,
            residual_value,
            residual_percentile,
            priority_flag,
            assumptions,
            generated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        df[
            [
                "region_id",
                "outcome_name",
                "model_version",
                "actual_value",
                "predicted_value",
                "residual_value",
                "residual_percentile",
                "priority_flag",
                "assumptions",
                "generated_at",
            ]
        ].itertuples(index=False, name=None),
    )

    print(f"Inserted {len(df)} model output rows.")
    print(f"Skipped {skipped_count} model output rows with no matching region.")


def populate_evidence_chunks_table(conn):
    """
    Populate evidence_chunks from metric_observations and model_outputs.

    This creates short factual evidence statements that can later support
    generated summaries.
    """
    created_at = datetime.now(timezone.utc).isoformat()

    # Changing generated evidence invalidates summary citations, so clear
    # summaries and links before replacing evidence chunks.
    conn.execute(
        """
        DELETE FROM summary_evidence
        """
    )
    conn.execute(
        """
        DELETE FROM summary_responses
        """
    )
    conn.execute(
        """
        DELETE FROM evidence_chunks
        WHERE evidence_type IN ('metric', 'model_output')
        """
    )

    metric_rows = conn.execute(
        """
        SELECT
            region_id,
            metric_name,
            metric_value,
            metric_unit,
            metric_category,
            source_name,
            observed_at
        FROM metric_observations
        """
    ).fetchall()

    evidence_rows = []

    for row in metric_rows:
        evidence_text = format_metric_evidence(row)

        evidence_rows.append(
            (
                row["region_id"],
                evidence_text,
                row["source_name"],
                source_url_for(row["source_name"]),
                "metric",
                created_at,
            )
        )

    model_rows = conn.execute(
        """
        SELECT
            region_id,
            outcome_name,
            model_version,
            actual_value,
            predicted_value,
            residual_value,
            residual_percentile,
            priority_flag,
            generated_at
        FROM model_outputs
        """
    ).fetchall()

    zero_shares = zero_share_by_outcome(conn)
    agreement = direction_agreement(conn)

    for row in model_rows:
        evidence_text = format_model_evidence(row, zero_shares, agreement)

        evidence_rows.append(
            (
                row["region_id"],
                evidence_text,
                "Regression model outputs",
                source_url_for("Regression model outputs"),
                "model_output",
                created_at,
            )
        )

    conn.executemany(
        """
        INSERT OR REPLACE INTO evidence_chunks (
            region_id,
            evidence_text,
            source_name,
            source_url,
            evidence_type,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        evidence_rows,
    )

    print(f"Inserted {len(evidence_rows)} evidence chunks.")


def reset_tables(conn):
    """
    Clear tables before repopulating them.

    Delete child/dependent tables first, then parent tables.
    This avoids foreign key constraint errors.
    """
    tables = [
        "summary_evidence",
        "summary_responses",
        "evidence_chunks",
        "model_outputs",
        "metric_observations",
        "region_geometries",
        "regions",
        "utilities",
    ]

    for table in tables:
        conn.execute(f"DELETE FROM {table}")

    conn.commit()
    print("Reset database tables.")


def main():
    df = load_main_dataset()
    df_utils = pd.read_csv(CSV_UTILITY_PATH)
    df_utils["zip_code"] = df_utils["zip_code"].apply(clean_region_id)
    df_utils = df_utils.set_index("zip_code")
    df_shape = _read_required(
        CSV_W_SHAPE_PATH,
        "python scripts/run_all.py --only data",
        "ZCTA polygons for the geometries table",
    )
    df_outputs = _read_required(
        MODEL_OUTPUTS_PATH,
        "python scripts/run_all.py --only models",
        "per-ZIP predictions and residuals, written by notebooks/regression.ipynb",
    )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        reset_tables(conn)
        populate_utilities_table(conn, df_utils)
        utility_lookup = build_id_lookup(
            conn=conn,
            table_name="utilities",
            id_column="utility_id",
            lookup_column="utility_name",
        )

        populate_regions_table(df, df_utils, conn, utility_lookup)
        populate_geometries_table(conn, df_shape)
        populate_metric_observations_table(df, conn)
        populate_model_outputs_table(df_outputs, conn)
        populate_evidence_chunks_table(conn)

        conn.commit()

    finally:
        conn.close()

    print("Loaded core data into database.")

if __name__ == "__main__":
    main()
