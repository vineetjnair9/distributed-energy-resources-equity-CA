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
    "PV_system_size_DC": ("kW", "der_observed", "LBNL Tracking the Sun processed"),
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


def format_metric_evidence(row):
    """
    Build category-aware metric evidence text for the LLM prompt.

    The wording intentionally carries provenance and interpretation context so
    generated summaries do not overstate coarse gridded weather controls or
    processed outcome variables.
    """
    region_id = row["region_id"]
    metric_name = row["metric_name"]
    metric_value = row["metric_value"]
    metric_unit = row["metric_unit"]
    metric_category = row["metric_category"]
    source_name = row["source_name"]

    if metric_category in {"weather", "solar_resource", "wind_resource"}:
        return (
            f"For region {region_id}, {source_name} {metric_name} is "
            f"{metric_value} {metric_unit}. This is coarse gridded climate or resource "
            "context based on the ZCTA centroid, not a precise ZIP-level "
            "measurement."
        )

    if metric_category in {"demographic", "socioeconomic", "education", "housing"}:
        return (
            f"For region {region_id}, {source_name} {metric_name} is "
            f"{metric_value} {metric_unit}."
        )

    if metric_category == "der_observed":
        return (
            f"For region {region_id}, observed DER metric {metric_name} is "
            f"{metric_value} {metric_unit}."
        )

    if metric_category == "energy_affordability":
        return (
            f"For region {region_id}, {source_name} {metric_name} is "
            f"{metric_value} {metric_unit}."
        )

    if metric_category == "demand":
        return (
            f"For region {region_id}, {source_name} {metric_name} is "
            f"{metric_value} {metric_unit}."
        )

    return (
        f"For region {region_id}, {source_name} {metric_name} is "
        f"{metric_value} {metric_unit}."
    )


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

    for row in model_rows:
        evidence_text = (
            f"For region {row['region_id']}, model {row['model_version']} "
            f"for {row['outcome_name']} estimated an actual value of "
            f"{row['actual_value']}, a predicted value of {row['predicted_value']}, "
            f"and a residual of {row['residual_value']}. "
            f"The residual percentile is {row['residual_percentile']}, "
            f"and the priority flag is {row['priority_flag']}."
        )

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
    df_shape = pd.read_csv(CSV_W_SHAPE_PATH)
    df_outputs = pd.read_csv(MODEL_OUTPUTS_PATH)
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
