#!/usr/bin/env python3
"""
Rebuild processed California ZIP-level DER datasets in a clean, scriptable order.

This consolidates the logic that was previously split across:
  - notebooks/processing_energy_data_zip.ipynb
  - notebooks/adding_predictor_data.ipynb

Outputs written by this script:
  - data/processed/storage_der.csv
  - data/processed/uswtdb_wind.csv
  - data/processed/power_plant_der.csv
  - data/processed/ev_chargers.csv
  - data/processed/tracking_the_sun.csv
  - data/processed/aggregated_TTS.csv
  - data/processed/aggregated_ev_chargers.csv
  - data/processed/aggregated_ev_cars.csv
  - data/processed/aggregated_power_plant.csv
  - data/processed/aggregated_storage.csv
  - data/processed/aggregated_wind.csv
  - data/processed/combined_der_dataset_full.csv
  - data/processed/combined_der_dataset.csv
  - data/processed/combined_der_dataset_acs_matched.csv
  - data/processed/acs_predictors_ca_zip.csv
  - data/processed/ca_zip_wind_means_2023.csv
  - data/processed/ca_zip_ghi_mean_2023.csv
  - data/processed/ca_zip_temperature_controls_2023.csv
  - data/processed/zip_to_utility.csv
  - data/processed/demand.csv
  - data/processed/combined_der_dataset_w_controls_predictors.csv

Notes
-----
- ACS and NASA POWER calls are live network calls, matching the current methodology.
- The Census API key should be provided via --census-api-key or CENSUS_API_KEY.
"""

from __future__ import annotations

import argparse
import logging
import os
import pickle
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
MAPPING = ROOT / "data" / "mapping_files"

YEAR = 2023
START = f"{YEAR}0101"
END = f"{YEAR}1231"
DER_THRESHOLD = 5
BASE_F = 65.0
SLEEP_S = 0.2

ZCTA_SHP = RAW / "boundaries" / "tl_2023_us_zcta520" / "tl_2023_us_zcta520.shp"
COUNTY_SHP = RAW / "boundaries" / "tl_2023_us_county" / "tl_2023_us_county.shp"
CA_UTILITY_GEOJSON = RAW / "boundaries" / "ca_utility_territories.geojson"

LOGGER = logging.getLogger("rebuild_processed_data")


STATE_TO_ABBR = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}


POWER_PLANT_FIXES = {
    13284: {"County": "sonoma", "Street_Address": "30 Mark West Springs Rd", "City": "Santa Rosa", "Zip": 95403},
    13300: {"County": "fresno", "Street_Address": "S Howard Ave", "City": "Riverdale", "Zip": 93656},
    13305: {"County": "fresno", "Street_Address": "2704 S Maple Ave", "City": "Fresno", "Zip": 93725},
    13307: {"County": "tulare", "Street_Address": "2045 N Plaza Dr", "City": "Visalia", "Zip": 93291},
    13308: {"County": "tulare", "Street_Address": "13213 Rd 80", "City": "Tipton", "Zip": 93272},
    13309: {"County": "tulare", "Street_Address": "531 Poplar Ave", "City": "Tipton", "Zip": 93272},
    13310: {"County": "tulare", "Street_Address": "531 Poplar Ave", "City": "Tipton", "Zip": 93272},
    13312: {"County": "tulare", "Street_Address": "3240 N Plaza Dr", "City": "Visalia", "Zip": 93291},
    13314: {"County": "kern", "Street_Address": "Zerker Rd", "City": "McFarland", "Zip": 93250},
    13323: {"County": "solano", "Street_Address": "4451 Blum Rd", "City": "Martinez", "Zip": 94553},
    13324: {"County": "kern", "Street_Address": "1750 E Panama Ln", "City": "Bakersfield", "Zip": 93307},
    13332: {"County": "napa", "Street_Address": "303 Green Island Rd", "City": "American Canyon", "Zip": 94503},
    13338: {"County": "san luis obispo", "Street_Address": "9225 N River Rd", "City": "San Miguel", "Zip": 93451},
    13341: {"County": "kern", "Street_Address": "27125 Pond Rd", "City": "Wasco", "Zip": 93280},
    13427: {"County": "fresno", "Street_Address": "32581 W Harlan Ave", "City": "Cantua Creek", "Zip": 93608},
    13445: {"County": "merced", "Street_Address": "7870 Hutchins Rd", "City": "Dos Palos", "Zip": 93620},
    1939: {"Street_Address": "501 Stampede Dam Road", "Zip": 96161},
}


EV_CHARGER_ZIP_FIXES = {
    892: "96120",
    893: "96120",
    1934: "92328",
    1935: "92328",
    1942: "93526",
    1965: "93203",
    1966: "93203",
    2140: "93516",
    2141: "93516",
    2142: "93516",
    2143: "93516",
    2227: "93204",
    2187: "93266",
    2188: "93266",
    3458: "90249",
    7032: "95389",
    7033: "95389",
    7034: "95389",
    7035: "95389",
    7036: "95389",
    7037: "95389",
    7038: "95389",
    7039: "95389",
    7040: "95389",
    7041: "95389",
    7042: "95389",
    7043: "95389",
    7044: "95389",
    7045: "95389",
    7046: "95389",
    7047: "95389",
    7048: "95389",
    7049: "95389",
    7050: "95389",
    7051: "95389",
    7052: "95389",
    7053: "95389",
    7054: "95389",
    7055: "95389",
    7139: "93620",
    7140: "93620",
    7178: "96101",
    7179: "96101",
    7183: "93541",
    7184: "93541",
    7243: "93451",
    9225: "92675",
    9406: "92675",
    11019: "92338",
    11020: "92338",
    11206: "92364",
    11217: "92309",
    13076: "94122",
    13077: "94122",
    17432: "96125",
    17433: "96125",
    18039: "96063",
    18139: "95321",
    18140: "95321",
    18155: "95389",
    18163: "95389",
    18164: "95389",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--census-api-key",
        default=os.environ.get("CENSUS_API_KEY"),
        help="Census API key. Defaults to the CENSUS_API_KEY environment variable.",
    )
    parser.add_argument(
        "--skip-external",
        action="store_true",
        help="Reuse existing external outputs (ACS/NASA) instead of making live requests.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level), format="%(levelname)s %(message)s")


def load_name_to_fips() -> dict[str, str]:
    with open(MAPPING / "name_to_fips.pkl", "rb") as f:
        data = pickle.load(f)
    return {str(k).strip().lower(): str(v).zfill(5) for k, v in data.items()}


def clean_zip(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip()
    # Accept normal ZIPs, ZIP+4, and values that pandas may have coerced to xxxxx.0.
    # Leave malformed strings like "9327." as invalid so they can be filtered out later.
    cleaned = cleaned.str.extract(r"^(\d{1,5})(?:\.0+)?(?:-\d+)?$", expand=False)
    return cleaned.str.zfill(5)


def is_valid_zip(series: pd.Series) -> pd.Series:
    return clean_zip(series).str.fullmatch(r"\d{5}").fillna(False)


def load_zcta_shapes() -> gpd.GeoDataFrame:
    zcta = gpd.read_file(ZCTA_SHP)
    zcta = zcta.rename(columns={"ZCTA5CE20": "zip_code"})
    zcta["zip_code"] = zcta["zip_code"].astype(str).str.zfill(5)
    return zcta


def load_ca_zcta_centroids() -> pd.DataFrame:
    zcta = gpd.read_file(ZCTA_SHP)
    zcta["zip_code"] = zcta["ZCTA5CE20"].astype(str).str.zfill(5)
    county = gpd.read_file(COUNTY_SHP)
    ca = county[county["STATEFP"] == "06"].copy().dissolve()
    if ca.crs != zcta.crs:
        ca = ca.to_crs(zcta.crs)
    zcta_ca = gpd.overlay(zcta[["zip_code", "geometry"]], ca[["geometry"]], how="intersection")
    zcta_ca = zcta[["zip_code", "INTPTLAT20", "INTPTLON20"]].merge(
        zcta_ca[["zip_code"]].drop_duplicates(),
        on="zip_code",
        how="inner",
    )
    zcta_ca["lat"] = zcta_ca["INTPTLAT20"].astype(str).str.replace("+", "", regex=False).astype(float)
    zcta_ca["lon"] = zcta_ca["INTPTLON20"].astype(str).astype(float)
    return zcta_ca[["zip_code", "lat", "lon"]].drop_duplicates("zip_code").reset_index(drop=True)


def write_csv(df: pd.DataFrame, path: Path, *, index: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)
    LOGGER.info("Wrote %s (%s rows)", path.relative_to(ROOT), len(df))


def build_storage_der() -> pd.DataFrame:
    storage = pd.read_excel(RAW / "storage" / "Storage_LatLong.xlsx")
    rename_map = {
        "Utility": "utility_name",
        "Nameplate Capacity (MW)": "storage_capacity_mw",
        "Nameplate Capacity (in KW AC)": "nameplate_capacity_kw_ac",
        "Fuel Type": "fuel_type",
        "Facility City": "city",
        "County": "county",
        "CAISO Flag": "caiso_flag",
        "Facility Zip": "zip_code",
        "Customer Sector": "sector",
        "Approval Date": "approval_date",
        "Technology Type": "technology_type",
        "Disconnect Date": "disconnect_date",
        "OG Reported Technology Type": "og_reported_technology_type",
        "Count of Nameplate Capacity (in KW AC)": "count_of_nameplate_capacity_kw_ac",
        "Latitude (generated)": "latitude",
        "Longitude (generated)": "longitude",
    }
    storage = storage.rename(columns=rename_map)
    storage["storage_capacity_mw"] = pd.to_numeric(storage["nameplate_capacity_kw_ac"], errors="coerce") / 1000.0
    storage_der = storage[storage["sector"].isin(["Residential", "Commercial"])].copy()
    storage_der = storage_der[storage_der["storage_capacity_mw"] <= DER_THRESHOLD].copy()
    storage_der["zip_code"] = clean_zip(storage_der["zip_code"])
    storage_der = storage_der[is_valid_zip(storage_der["zip_code"])].copy()
    write_csv(storage_der, PROCESSED / "storage_der.csv")
    return storage_der


def build_wind_zip() -> tuple[pd.DataFrame, pd.DataFrame]:
    uswtdb_wind = pd.read_csv(RAW / "wind" / "USWTDB_wind_data.csv")
    uswtdb_wind = uswtdb_wind.rename(
        columns={
            "t_state": "state",
            "xlong": "longitude",
            "ylat": "latitude",
            "t_cap": "turbine_capacity_kw",
            "p_name": "project_name",
            "p_year": "project_year",
            "t_county": "t_county",
            "t_fips": "t_fips",
        }
    )
    uswtdb_wind = uswtdb_wind[uswtdb_wind["state"].eq("CA")].copy()
    write_csv(uswtdb_wind, PROCESSED / "uswtdb_wind.csv")

    gdf_wind = gpd.GeoDataFrame(
        uswtdb_wind,
        geometry=gpd.points_from_xy(uswtdb_wind["longitude"], uswtdb_wind["latitude"]),
        crs="EPSG:4326",
    )
    zip_shapes = load_zcta_shapes()
    if gdf_wind.crs != zip_shapes.crs:
        gdf_wind = gdf_wind.set_crs(zip_shapes.crs, allow_override=True)
    joined = gpd.sjoin(gdf_wind, zip_shapes[["zip_code", "geometry"]], how="left", predicate="intersects")
    joined["turbine_mw"] = pd.to_numeric(joined["turbine_capacity_kw"], errors="coerce") / 1000.0
    wind_zip = (
        joined.groupby("zip_code", dropna=True, as_index=False)
        .agg(wind_capacity_mw=("turbine_mw", "sum"), wind_turbine_count=("turbine_mw", "size"))
    )
    wind_zip["zip_code"] = clean_zip(wind_zip["zip_code"])
    wind_zip = wind_zip[is_valid_zip(wind_zip["zip_code"])].copy()
    write_csv(wind_zip, PROCESSED / "ca_zip_wind_capacity_from_uswtdb.csv", index=False)
    return uswtdb_wind, wind_zip


def build_power_plant_der(name_to_fips: dict[str, str]) -> pd.DataFrame:
    power_plant = pd.read_csv(RAW / "plants" / "Power_Plants.csv")
    power_plant["County"] = power_plant["County"].astype(str).str.strip().str.lower()
    for idx, updates in POWER_PLANT_FIXES.items():
        for col, val in updates.items():
            power_plant.loc[idx, col] = val

    power_plant["FIPS"] = power_plant["County"].map(name_to_fips).astype(str).str.zfill(5)
    rename_map = {
        "X": "x_coord",
        "Y": "y_coord",
        "OBJECTID": "object_id",
        "Plant_Code": "plant_code",
        "Plant_Name": "plant_name",
        "Utility_ID": "utility_id",
        "Utility_Name": "utility_name",
        "sector_name": "sector",
        "Street_Address": "street_address",
        "City": "city",
        "County": "county",
        "State": "state",
        "Zip": "zip_code",
        "PrimSource": "primary_source",
        "source_desc": "source_description",
        "tech_desc": "technology_description",
        "Install_MW": "installed_capacity_mw",
        "Total_MW": "plant_capacity_mw",
        "Bat_MW": "battery_capacity_mw",
        "Bio_MW": "biomass_capacity_mw",
        "Coal_MW": "coal_capacity_mw",
        "Geo_MW": "geothermal_capacity_mw",
        "Hydro_MW": "hydro_capacity_mw",
        "HydroPS_MW": "hydro_pumped_storage_mw",
        "NG_MW": "natural_gas_capacity_mw",
        "Nuclear_MW": "nuclear_capacity_mw",
        "Crude_MW": "crude_oil_capacity_mw",
        "Solar_MW": "solar_capacity_mw",
        "Wind_MW": "wind_capacity_mw",
        "Other_MW": "other_capacity_mw",
        "Source": "data_source",
        "Period": "reporting_period",
        "Longitude": "longitude",
        "Latitude": "latitude",
        "FIPS": "fips",
    }
    power_plant = power_plant.rename(columns=rename_map)
    power_plant["state"] = (
        power_plant["state"].astype(str).str.strip().str.lower().map(STATE_TO_ABBR).fillna(power_plant["state"])
    )
    power_plant["state"] = power_plant["state"].astype(str).str.upper()
    power_plant = power_plant[power_plant["state"] == "CA"].copy()
    power_plant["zip_code"] = clean_zip(power_plant["zip_code"])
    power_plant = power_plant[is_valid_zip(power_plant["zip_code"])].copy()
    power_plant = power_plant[power_plant["zip_code"].str.startswith("9")].copy()

    btm_sectors = [
        "Commercial Non-CHP",
        "Industrial Non-CHP",
        "Commercial CHP",
        "Industrial CHP",
    ]
    power_plant_der = power_plant[
        (power_plant["sector"].isin(btm_sectors))
        & power_plant["plant_capacity_mw"].notna()
        & (power_plant["plant_capacity_mw"] <= DER_THRESHOLD)
    ].copy()
    write_csv(power_plant_der, PROCESSED / "power_plant_der.csv")
    return power_plant_der


def build_ev_sources(name_to_fips: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ev_cars = pd.read_excel(RAW / "ev_chargers" / "Stock_Map_County (2)_Full Data_data.xlsx")
    ev_cars = ev_cars.rename(
        columns={
            "MAKE": "make",
            "MODEL": "model",
            "NonZEV vs ZEV": "nonzev_v_zev",
            "CA ZIP": "zip_code",
            "Fuel Type ": "fuel_type",
        }
    )
    ev_cars["zip_code"] = clean_zip(ev_cars["zip_code"])
    ev_cars = ev_cars[is_valid_zip(ev_cars["zip_code"])].copy()
    ev_cars = ev_cars[ev_cars["zip_code"].str.startswith("9")].copy()

    ev_chargers = pd.read_excel(RAW / "ev_chargers" / "Charger_County Map_Full Data_data_zip_lat-lon.xlsx")
    ev_chargers["County"] = ev_chargers["County"].astype(str).str.strip().str.lower()
    ev_chargers["fips"] = ev_chargers["County"].map(name_to_fips)
    ev_chargers = ev_chargers.drop(columns=["Calculation1", "For Additional info", "For Additional info (copy)"], errors="ignore")
    ev_chargers = ev_chargers.rename(
        columns={
            "County": "county",
            "Access": "access_type",
            "DC Fast": "dc_fast_chargers",
            "Level 1": "level1_chargers",
            "Level 2": "level2_chargers",
            "Number of Chargers": "total_chargers",
            "ZIP": "zip_code",
            "City": "city",
            "EV Connector Types": "ev_connector_types",
            "ID": "id",
            "Latitude": "latitude",
            "Longitude": "longitude",
            "Network": "network",
            "State": "state",
            "Station Name": "station_name",
            "Street Address": "street_address",
            "Level 1 & 2": "level1_2_chargers",
        }
    )
    ev_chargers["fips"] = ev_chargers["fips"].astype(str).str.zfill(5)
    ev_chargers["zip_code"] = clean_zip(ev_chargers["zip_code"])

    gdf_ev = gpd.GeoDataFrame(
        ev_chargers,
        geometry=gpd.points_from_xy(ev_chargers["longitude"], ev_chargers["latitude"]),
        crs="EPSG:4326",
    )
    zip_shapes = load_zcta_shapes()
    if gdf_ev.crs != zip_shapes.crs:
        gdf_ev = gdf_ev.set_crs(zip_shapes.crs, allow_override=True)
    joined = gpd.sjoin(gdf_ev, zip_shapes[["zip_code", "geometry"]], how="left", predicate="within")
    if "zip_code_right" in joined.columns:
        ev_chargers["zip_code"] = clean_zip(joined["zip_code_right"]).fillna(ev_chargers["zip_code"])
    elif "zip_code" in joined.columns:
        ev_chargers["zip_code"] = clean_zip(joined["zip_code"]).fillna(ev_chargers["zip_code"])
    for idx, zip_code in EV_CHARGER_ZIP_FIXES.items():
        if idx in ev_chargers.index:
            ev_chargers.loc[idx, "zip_code"] = zip_code
    ev_chargers = ev_chargers[is_valid_zip(ev_chargers["zip_code"])].copy()
    ev_chargers = ev_chargers[ev_chargers["zip_code"].str.startswith("9")].copy()

    write_csv(ev_chargers, PROCESSED / "ev_chargers.csv")
    return ev_cars, ev_chargers


def build_tracking_the_sun() -> pd.DataFrame:
    tracking = pd.read_csv(RAW / "solar" / "TTS_LBNL_public_file_29-Sep-2025_all.csv", low_memory=False)
    tracking["zip_code"] = clean_zip(tracking["zip_code"])
    tracking = tracking[tracking["state"] == "CA"].copy()
    bad = {"-0001", "-01.0", "000.0", "2399.", "831.0"}
    tracking = tracking[~tracking["zip_code"].isin(bad)].copy()
    tracking = tracking[is_valid_zip(tracking["zip_code"])].copy()
    tracking = tracking[tracking["zip_code"].str.startswith("9")].copy()
    tracking = tracking[tracking["PV_system_size_DC"] >= 0].copy()
    write_csv(tracking, PROCESSED / "tracking_the_sun.csv")
    return tracking


def aggregate_sources(
    tracking: pd.DataFrame,
    ev_chargers: pd.DataFrame,
    ev_cars: pd.DataFrame,
    power_plant_der: pd.DataFrame,
    storage_der: pd.DataFrame,
    wind_zip: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    aggregated_ev_chargers = ev_chargers.groupby("zip_code", as_index=False).agg(
        total_chargers=("total_chargers", "sum"),
        level1_chargers=("level1_chargers", "sum"),
        level2_chargers=("level2_chargers", "sum"),
        dc_fast_chargers=("dc_fast_chargers", "sum"),
    )

    aggregated_ev_cars = ev_cars.groupby("zip_code").size().rename("zev_count").reset_index()

    tracking = tracking.copy()
    tracking["PV_system_size_DC"] = pd.to_numeric(tracking["PV_system_size_DC"], errors="coerce") / 1000.0
    aggregated_tts = tracking.groupby("zip_code", as_index=False).agg(PV_system_size_DC=("PV_system_size_DC", "sum"))

    aggregated_power_plant = power_plant_der.groupby("zip_code", as_index=False).agg(
        plant_capacity_mw=("plant_capacity_mw", "sum")
    )
    aggregated_storage = storage_der.groupby("zip_code", as_index=False).agg(
        storage_capacity_mw=("storage_capacity_mw", "sum")
    )
    aggregated_wind = wind_zip.copy()

    outputs = {
        "aggregated_TTS.csv": aggregated_tts,
        "aggregated_ev_chargers.csv": aggregated_ev_chargers,
        "aggregated_ev_cars.csv": aggregated_ev_cars,
        "aggregated_power_plant.csv": aggregated_power_plant,
        "aggregated_storage.csv": aggregated_storage,
        "aggregated_wind.csv": aggregated_wind,
    }
    for name, df in outputs.items():
        df = df.copy()
        df["zip_code"] = clean_zip(df["zip_code"])
        df = df[df["zip_code"].str.fullmatch(r"\d{5}")].copy()
        outputs[name] = df
        write_csv(df, PROCESSED / name)
    return outputs


def build_combined_der_dataset_full(aggregated: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dfs = [
        aggregated["aggregated_TTS.csv"],
        aggregated["aggregated_ev_chargers.csv"],
        aggregated["aggregated_ev_cars.csv"],
        aggregated["aggregated_power_plant.csv"],
        aggregated["aggregated_storage.csv"],
        aggregated["aggregated_wind.csv"],
    ]
    merged = dfs[0].copy()
    for df in dfs[1:]:
        merged = pd.merge(merged, df, on="zip_code", how="outer")
    merged["zip_code"] = clean_zip(merged["zip_code"])
    merged = merged[merged["zip_code"].str.fullmatch(r"\d{5}")].copy()
    merged = merged.sort_values("zip_code").reset_index(drop=True)
    write_csv(merged, PROCESSED / "combined_der_dataset_full.csv")
    write_csv(merged, PROCESSED / "combined_der_dataset.csv")
    return merged


def fetch_acs_predictors(df_full: pd.DataFrame, census_api_key: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not census_api_key:
        raise ValueError("A Census API key is required unless --skip-external is used.")

    base_url = f"https://api.census.gov/data/{YEAR}/acs/acs5"
    edu_vars = [
        "B15003_001E",
        "B15003_017E",
        "B15003_018E",
        "B15003_019E",
        "B15003_020E",
        "B15003_021E",
        "B15003_022E",
        "B15003_023E",
        "B15003_024E",
        "B15003_025E",
    ]
    variables = [
        "B01003_001E",
        "B19013_001E",
        "B25077_001E",
        "B03002_001E",
        "B03002_003E",
        "B03002_004E",
        "B03002_006E",
        "B03002_012E",
        "B17001_001E",
        "B17001_002E",
    ] + edu_vars

    resp = requests.get(
        base_url,
        params={"get": ",".join(variables), "for": "zip code tabulation area:*", "key": census_api_key},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    acs = pd.DataFrame(data[1:], columns=data[0]).rename(columns={"zip code tabulation area": "zip_code"})
    acs["zip_code"] = clean_zip(acs["zip_code"])
    for col in variables:
        acs[col] = pd.to_numeric(acs[col], errors="coerce")

    panel_zips = set(clean_zip(df_full["zip_code"]))
    acs = acs[acs["zip_code"].isin(panel_zips)].copy()
    rename_map = {
        "B01003_001E": "total_population",
        "B19013_001E": "median_household_income",
        "B25077_001E": "median_housing_value",
        "B03002_001E": "raceeth_total",
        "B03002_003E": "white_not_hispanic",
        "B03002_004E": "black_not_hispanic",
        "B03002_006E": "asian_not_hispanic",
        "B03002_012E": "hispanic_any_race",
        "B17001_001E": "poverty_universe",
        "B17001_002E": "below_poverty",
        "B15003_001E": "edu_25plus_total",
        "B15003_017E": "hs_diploma",
        "B15003_018E": "ged",
        "B15003_019E": "some_college_lt1yr",
        "B15003_020E": "some_college_ge1yr_no_degree",
        "B15003_021E": "associates",
        "B15003_022E": "bachelors",
        "B15003_023E": "masters",
        "B15003_024E": "professional_school",
        "B15003_025E": "doctorate",
    }
    acs = acs.rename(columns=rename_map)
    acs.loc[acs["median_household_income"] < 0, "median_household_income"] = pd.NA
    acs.loc[acs["median_housing_value"] < 0, "median_housing_value"] = pd.NA
    acs = acs[acs["total_population"] > 0].copy()

    race_den = acs["raceeth_total"].replace({0: pd.NA})
    pov_den = acs["poverty_universe"].replace({0: pd.NA})
    edu_den = acs["edu_25plus_total"].replace({0: pd.NA})
    acs["pct_black"] = acs["black_not_hispanic"] / race_den
    acs["pct_hispanic"] = acs["hispanic_any_race"] / race_den
    acs["pct_asian"] = acs["asian_not_hispanic"] / race_den
    acs["poverty_rate"] = acs["below_poverty"] / pov_den
    acs["pct_bachelors_plus"] = (
        acs[["bachelors", "masters", "professional_school", "doctorate"]].sum(axis=1) / edu_den
    )
    acs_model = acs[
        [
            "zip_code",
            "median_household_income",
            "poverty_rate",
            "pct_bachelors_plus",
            "pct_black",
            "pct_hispanic",
            "pct_asian",
            "median_housing_value",
            "total_population",
        ]
    ].copy()
    write_csv(acs_model, PROCESSED / "acs_predictors_ca_zip.csv")

    matched = set(acs_model["zip_code"])
    df_acs = df_full[df_full["zip_code"].isin(matched)].copy()
    write_csv(df_acs, PROCESSED / "combined_der_dataset_acs_matched.csv")
    return acs_model, df_acs


def fetch_nasa_power_table(parameter_string: str, zip_points: pd.DataFrame) -> list[dict]:
    session = requests.Session()
    rows: list[dict] = []
    for _, row in zip_points.iterrows():
        url = (
            "https://power.larc.nasa.gov/api/temporal/daily/point"
            f"?parameters={parameter_string}"
            "&community=RE"
            f"&longitude={row['lon']}&latitude={row['lat']}"
            f"&start={START}&end={END}"
            "&format=JSON"
        )
        r = session.get(url, timeout=60)
        r.raise_for_status()
        rows.append({"zip_code": row["zip_code"], "lat": row["lat"], "lon": row["lon"], "payload": r.json()})
        time.sleep(SLEEP_S)
    return rows


def build_nasa_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    zcta_points = load_ca_zcta_centroids()

    wind_rows = []
    for item in fetch_nasa_power_table("WS10M,WS50M", zcta_points):
        params = item["payload"].get("properties", {}).get("parameter", {})
        ws10 = [v for v in params.get("WS10M", {}).values() if v is not None]
        ws50 = [v for v in params.get("WS50M", {}).values() if v is not None]
        wind_rows.append(
            {
                "zip_code": item["zip_code"],
                "wind_ws10m_mean_2023": (sum(ws10) / len(ws10)) if ws10 else pd.NA,
                "wind_ws50m_mean_2023": (sum(ws50) / len(ws50)) if ws50 else pd.NA,
                "lat": item["lat"],
                "lon": item["lon"],
            }
        )
    df_wind = pd.DataFrame(wind_rows)
    write_csv(df_wind, PROCESSED / "ca_zip_wind_means_2023.csv", index=False)

    ghi_rows = []
    for item in fetch_nasa_power_table("ALLSKY_SFC_SW_DWN", zcta_points):
        params = item["payload"].get("properties", {}).get("parameter", {})
        vals = [v for v in params.get("ALLSKY_SFC_SW_DWN", {}).values() if v is not None]
        ghi_rows.append(
            {
                "zip_code": item["zip_code"],
                "ghi_mean_kwh_m2_day_2023": (sum(vals) / len(vals)) if vals else pd.NA,
                "lat": item["lat"],
                "lon": item["lon"],
            }
        )
    df_ghi = pd.DataFrame(ghi_rows)
    write_csv(df_ghi, PROCESSED / "ca_zip_ghi_mean_2023.csv", index=False)

    temp_rows = []
    for item in fetch_nasa_power_table("T2M,T2M_MAX,T2M_MIN", zcta_points):
        params = item["payload"].get("properties", {}).get("parameter", {})
        t2m = params.get("T2M", {})
        tmax = params.get("T2M_MAX", {})
        tmin = params.get("T2M_MIN", {})
        t2m_vals = [v for v in t2m.values() if v is not None]
        tmax_vals = [v for v in tmax.values() if v is not None]
        tmin_vals = [v for v in tmin.values() if v is not None]
        summer_vals = [v for d, v in t2m.items() if v is not None and 6 <= int(str(d)[4:6]) <= 9]
        cdd = 0.0
        hdd = 0.0
        for v in t2m_vals:
            tf = (v * 9.0 / 5.0) + 32.0
            cdd += max(0.0, tf - BASE_F)
            hdd += max(0.0, BASE_F - tf)
        temp_rows.append(
            {
                "zip_code": item["zip_code"],
                "lat": item["lat"],
                "lon": item["lon"],
                f"t2m_mean_c_{YEAR}": (sum(t2m_vals) / len(t2m_vals)) if t2m_vals else pd.NA,
                f"t2m_max_mean_c_{YEAR}": (sum(tmax_vals) / len(tmax_vals)) if tmax_vals else pd.NA,
                f"t2m_min_mean_c_{YEAR}": (sum(tmin_vals) / len(tmin_vals)) if tmin_vals else pd.NA,
                f"t2m_summer_mean_c_{YEAR}": (sum(summer_vals) / len(summer_vals)) if summer_vals else pd.NA,
                f"cdd65_{YEAR}": cdd if t2m_vals else pd.NA,
                f"hdd65_{YEAR}": hdd if t2m_vals else pd.NA,
            }
        )
    df_temp = pd.DataFrame(temp_rows)
    write_csv(df_temp, PROCESSED / "ca_zip_temperature_controls_2023.csv", index=False)
    return df_wind, df_ghi, df_temp


def build_zip_to_utility() -> pd.DataFrame:
    territories = gpd.read_file(CA_UTILITY_GEOJSON).rename(
        columns={"Acronym": "acronym", "Utility": "utility", "Type": "utility_type"}
    )
    territories = territories[["acronym", "utility", "utility_type", "geometry"]].to_crs("EPSG:3310")

    zcta = gpd.read_file(ZCTA_SHP).rename(columns={"ZCTA5CE20": "zip_code"})
    zcta["zip_code"] = zcta["zip_code"].astype(str).str.zfill(5)
    county = gpd.read_file(COUNTY_SHP)
    ca = county[county["STATEFP"] == "06"].copy().dissolve()
    if ca.crs != zcta.crs:
        ca = ca.to_crs(zcta.crs)
    zcta_ca = gpd.overlay(zcta[["zip_code", "geometry"]], ca[["geometry"]], how="intersection").to_crs("EPSG:3310")
    inter = gpd.overlay(zcta_ca, territories, how="intersection")
    inter["overlap_area_m2"] = inter.geometry.area
    zip_area = zcta_ca.copy()
    zip_area["zip_area_m2"] = zip_area.geometry.area
    inter = inter.merge(zip_area[["zip_code", "zip_area_m2"]], on="zip_code", how="left")
    inter["overlap_share_of_zip"] = inter["overlap_area_m2"] / inter["zip_area_m2"]
    idx = inter.groupby("zip_code")["overlap_area_m2"].idxmax()
    dom = inter.loc[idx, ["zip_code", "acronym", "utility", "utility_type", "overlap_area_m2", "overlap_share_of_zip"]]
    dom = dom.sort_values("zip_code").reset_index(drop=True)
    write_csv(dom, PROCESSED / "zip_to_utility.csv", index=False)
    return dom


def annualize_utility(df: pd.DataFrame, util: str, cust_col_base: str) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    kwh_cols = [f"totalkwh_q{i}" for i in range(1, 5)]
    out[f"{util}_kwh_annual"] = df.reindex(columns=kwh_cols).sum(axis=1, min_count=1)
    cust_cols = [f"{cust_col_base}_q{i}" for i in range(1, 5)]
    cust_q_sum = df.reindex(columns=cust_cols).sum(axis=1, min_count=1)
    out[f"{util}_cust_months"] = 3 * cust_q_sum
    out[f"{util}_kwh_per_cust_month"] = out[f"{util}_kwh_annual"] / out[f"{util}_cust_months"].replace(0, np.nan)
    return out


def build_demand_controls() -> pd.DataFrame:
    pge = None
    for q in [1, 2, 3, 4]:
        temp = pd.read_csv(RAW / "demand" / f"PGE_2023_Q{q}_ElectricUsageByZip.csv")
        temp.columns = temp.columns.str.strip().str.lower()
        temp = temp.drop(columns=["month", "year", "customerclass", "combined"], errors="ignore")
        temp = temp.rename(columns={"zipcode": "zip_code"})
        temp["zip_code"] = clean_zip(temp["zip_code"])
        for col in ["totalcustomers", "totalkwh", "averagekwh"]:
            if col in temp.columns:
                temp[col] = pd.to_numeric(temp[col], errors="coerce")
        temp = temp.groupby("zip_code").sum(numeric_only=True).add_suffix(f"_q{q}")
        pge = temp if pge is None else pge.join(temp, how="outer")

    sce = None
    for q in [1, 2, 3, 4]:
        temp = pd.read_excel(RAW / "demand" / f"SCE_2023_Q{q}_ElectricUsageByZip.xlsx", skiprows=[0, 1])
        temp.columns = temp.columns.str.strip().str.lower()
        temp = temp.drop(columns=["month", "year", "customer\nclass", "combined"], errors="ignore")
        temp = temp.rename(columns={"zip\ncode": "zip_code"})
        temp["zip_code"] = clean_zip(temp["zip_code"])
        for col in ["totalaccounts", "totalkwh", "averagekwh"]:
            if col in temp.columns:
                temp[col] = pd.to_numeric(temp[col], errors="coerce")
        temp = temp.groupby("zip_code").sum(numeric_only=True).add_suffix(f"_q{q}")
        sce = temp if sce is None else sce.join(temp, how="outer")

    sdge = None
    for q in [1, 2, 3, 4]:
        temp = pd.read_csv(RAW / "demand" / f"SDGE-ELEC-2023-Q{q}.csv")
        temp.columns = temp.columns.str.strip().str.lower()
        temp = temp.drop(columns=["month", "year", "customerclass", "combined"], errors="ignore")
        temp = temp.rename(columns={"zipcode": "zip_code"})
        temp["zip_code"] = clean_zip(temp["zip_code"])
        for col in ["totalaccounts", "totalkwh", "averagekwh"]:
            if col in temp.columns:
                temp[col] = pd.to_numeric(temp[col], errors="coerce")
        temp = temp.groupby("zip_code").sum(numeric_only=True).add_suffix(f"_q{q}")
        sdge = temp if sdge is None else sdge.join(temp, how="outer")

    demand = annualize_utility(pge, "pge", "totalcustomers").join(
        annualize_utility(sce, "sce", "totalaccounts"), how="outer"
    ).join(
        annualize_utility(sdge, "sdge", "totalaccounts"), how="outer"
    )
    kwh_cols = [c for c in demand.columns if c.endswith("_kwh_annual")]
    cust_cols = [c for c in demand.columns if c.endswith("_cust_months")]
    demand["kwh_annual_total"] = demand[kwh_cols].sum(axis=1, min_count=1)
    demand["cust_months_total"] = demand[cust_cols].sum(axis=1, min_count=1)
    demand["kwh_per_cust_month_total"] = demand["kwh_annual_total"] / demand["cust_months_total"].replace(0, np.nan)
    demand["num_utils_reporting"] = demand[kwh_cols].gt(0).sum(axis=1)
    demand["dominant_util_share"] = demand[kwh_cols].max(axis=1) / demand["kwh_annual_total"].replace(0, np.nan)
    demand = demand.reset_index()
    demand_control = demand[["zip_code", "kwh_annual_total"]].copy()
    demand_control["log_kwh"] = np.log1p(demand_control["kwh_annual_total"])
    write_csv(demand_control, PROCESSED / "demand.csv")
    return demand_control


def build_final_analysis_dataset(
    df_full: pd.DataFrame,
    acs: pd.DataFrame,
    ghi: pd.DataFrame,
    temp: pd.DataFrame,
    wind_means: pd.DataFrame,
    zip_to_utility: pd.DataFrame,
    demand: pd.DataFrame,
) -> pd.DataFrame:
    df = df_full.copy()
    df["zip_code"] = clean_zip(df["zip_code"])
    for d in [acs, ghi, temp, wind_means, zip_to_utility, demand]:
        d = d.copy()
        d["zip_code"] = clean_zip(d["zip_code"])
        df = pd.merge(df, d, on="zip_code", how="left")

    for col in ["wind_capacity_mw", "wind_turbine_count", "plant_capacity_mw"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    zcta = gpd.read_file(ZCTA_SHP)
    county = gpd.read_file(COUNTY_SHP)
    zcta_id = "ZCTA5CE20" if "ZCTA5CE20" in zcta.columns else ("GEOID20" if "GEOID20" in zcta.columns else "GEOID")
    county_id = "GEOID" if "GEOID" in county.columns else ("GEOID20" if "GEOID20" in county.columns else "GEOID10")
    county_name_col = "NAME" if "NAME" in county.columns else None
    zcta = zcta[[zcta_id, "geometry"]].rename(columns={zcta_id: "zip_code"})
    keep = [county_id, "geometry"] + ([county_name_col] if county_name_col else [])
    county = county[keep].rename(columns={county_id: "county_geoid"})
    if county_name_col:
        county = county.rename(columns={county_name_col: "county_name"})
    zcta["zip_code"] = zcta["zip_code"].astype(str).str.zfill(5)
    zcta = zcta.to_crs("EPSG:5070")
    county = county.to_crs("EPSG:5070")
    pairs = gpd.sjoin(zcta, county, how="inner", predicate="intersects").drop(columns=["index_right"])
    county_geom = county.set_index("county_geoid").geometry
    other = gpd.GeoSeries(pairs["county_geoid"].map(county_geom), index=pairs.index, crs=pairs.crs)
    pairs["overlap_area"] = pairs.geometry.intersection(other).area
    pairs = pairs.sort_values(["zip_code", "overlap_area"], ascending=[True, False])
    cols = ["zip_code", "county_geoid"] + (["county_name"] if "county_name" in pairs.columns else [])
    zip_to_county = pairs.drop_duplicates("zip_code")[cols]

    df = df.merge(zip_to_county, on="zip_code", how="left")
    zcta_area = gpd.read_file(ZCTA_SHP)
    zcta_area = zcta_area[[zcta_id, "geometry"]].rename(columns={zcta_id: "zip_code"})
    zcta_area["zip_code"] = zcta_area["zip_code"].astype(str).str.zfill(5)
    zcta_area = zcta_area.to_crs("EPSG:5070")
    zcta_area["area_km2"] = zcta_area.geometry.area / 1e6
    df = df.merge(zcta_area[["zip_code", "area_km2"]], on="zip_code", how="left")
    df["pop_density_km2"] = df["total_population"] / df["area_km2"].replace(0, np.nan)
    df["log_pop_density"] = np.log1p(df["pop_density_km2"])

    min_n = 5
    df["county_geoid"] = df["county_geoid"].astype(str).str.strip()
    counts = df["county_geoid"].value_counts()
    keep = counts[counts >= min_n].index
    df = df[df["county_geoid"].isin(keep)].copy()
    write_csv(df, PROCESSED / "combined_der_dataset_w_controls_predictors.csv")
    return df


def read_or_fetch_external(args: argparse.Namespace, df_full: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if args.skip_external:
        LOGGER.warning("Using existing external-derived processed files because --skip-external was provided.")
        acs = pd.read_csv(PROCESSED / "acs_predictors_ca_zip.csv")
        ghi = pd.read_csv(PROCESSED / "ca_zip_ghi_mean_2023.csv")
        temp = pd.read_csv(PROCESSED / "ca_zip_temperature_controls_2023.csv")
        wind = pd.read_csv(PROCESSED / "ca_zip_wind_means_2023.csv")
        zip_to_utility = pd.read_csv(PROCESSED / "zip_to_utility.csv")
        demand = pd.read_csv(PROCESSED / "demand.csv")
        if (PROCESSED / "combined_der_dataset_acs_matched.csv").exists():
            df_acs = pd.read_csv(PROCESSED / "combined_der_dataset_acs_matched.csv")
        else:
            matched = set(acs["zip_code"].astype(str).str.zfill(5))
            df_acs = df_full[df_full["zip_code"].isin(matched)].copy()
            write_csv(df_acs, PROCESSED / "combined_der_dataset_acs_matched.csv")
        return acs, df_acs, ghi, temp, wind, zip_to_utility, demand

    acs, df_acs = fetch_acs_predictors(df_full, args.census_api_key)
    wind, ghi, temp = build_nasa_outputs()
    zip_to_utility = build_zip_to_utility()
    demand = build_demand_controls()
    return acs, df_acs, ghi, temp, wind, zip_to_utility, demand


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    name_to_fips = load_name_to_fips()
    storage_der = build_storage_der()
    _, wind_zip = build_wind_zip()
    power_plant_der = build_power_plant_der(name_to_fips)
    ev_cars, ev_chargers = build_ev_sources(name_to_fips)
    tracking = build_tracking_the_sun()
    aggregated = aggregate_sources(tracking, ev_chargers, ev_cars, power_plant_der, storage_der, wind_zip)
    df_full = build_combined_der_dataset_full(aggregated)
    acs, _, ghi, temp, wind_means, zip_to_utility, demand = read_or_fetch_external(args, df_full)
    build_final_analysis_dataset(df_full, acs, ghi, temp, wind_means, zip_to_utility, demand)
    LOGGER.info("Processed dataset rebuild completed.")


if __name__ == "__main__":
    main()
