import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import rebuild_processed_data


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_ACS = ROOT / "data" / "raw" / "acs"


def test_released_dataset_has_complete_housing_composition():
    path = PROCESSED / "combined_der_dataset_w_controls_predictors.csv"
    frame = pd.read_csv(path, dtype={"zip_code": "string", "county_geoid": "string"})
    structure = [
        "pct_single_family_units",
        "pct_multifamily_units",
        "pct_mobile_home_units",
        "pct_other_housing_units",
    ]

    assert not any(column.startswith("Unnamed:") for column in frame.columns)
    assert set(structure + ["owner_occupied_rate"]).issubset(frame.columns)
    complete = frame[structure].dropna()
    assert len(complete) >= 1_300
    assert ((complete >= -1e-10) & (complete <= 1 + 1e-10)).all().all()
    assert np.allclose(complete.sum(axis=1), 1.0, atol=1e-8, rtol=0)
    assert frame["zip_code"].str.fullmatch(r"\d{5}").all()
    assert frame["zip_code"].is_unique


def test_small_county_zctas_remain_in_shared_release_dataset():
    frame = pd.read_csv(
        PROCESSED / "combined_der_dataset_w_controls_predictors.csv",
        dtype={"zip_code": "string"},
    )
    assert {"95023", "95045", "95223", "96120"}.issubset(set(frame["zip_code"]))


def test_release_and_clusters_exclude_non_california_zips():
    release = pd.read_csv(
        PROCESSED / "combined_der_dataset_w_controls_predictors.csv",
        dtype={"zip_code": "string"},
    )
    assignments = pd.read_csv(
        ROOT / "outputs" / "tables" / "pca_kmeans_cluster_assignments.csv",
        dtype={"zip_code": "string"},
    )

    release_zips = pd.to_numeric(release["zip_code"])
    assert release_zips.between(90001, 96162).all()
    assert "98125" not in set(release["zip_code"])
    assert "98125" not in set(assignments["zip_code"])


def test_acs_housing_snapshot_has_estimates_moes_and_matching_manifest():
    csv_path = RAW_ACS / "acs_2023_5yr_housing_ca_zcta.csv"
    manifest_path = RAW_ACS / "acs_2023_5yr_housing_query_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame = pd.read_csv(csv_path, dtype={"zip_code": "string"})

    expected_estimates = {
        *{f"B25024_{index:03d}E" for index in range(1, 12)},
        *{f"B25003_{index:03d}E" for index in range(1, 4)},
    }
    expected_moes = {variable[:-1] + "M" for variable in expected_estimates}
    assert expected_estimates | expected_moes <= set(frame.columns)
    assert manifest["row_count"] == len(frame)
    assert manifest["credentials_persisted"] is False
    assert manifest["sha256"] == hashlib.sha256(csv_path.read_bytes()).hexdigest()


def test_acs_request_errors_redact_credentials(monkeypatch):
    secret = "not-for-logs"

    def fail_request(*args, **kwargs):
        raise rebuild_processed_data.requests.ConnectionError(
            f"failed URL https://api.census.gov/data?key={secret}"
        )

    monkeypatch.setattr(rebuild_processed_data.requests, "get", fail_request)
    with pytest.raises(RuntimeError) as error:
        rebuild_processed_data.fetch_acs_response(
            "https://api.census.gov/data/2023/acs/acs5",
            ["B25024_001E"],
            secret,
        )

    assert secret not in str(error.value)
    assert "redacted" in str(error.value)
