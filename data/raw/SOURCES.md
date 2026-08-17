# Raw Data Provenance

This project mixes three kinds of raw inputs for a 2023-aligned rebuild:

1. Exact public snapshots that can be downloaded reproducibly.
2. Public sources that are available, but not yet pinned here to the exact historical file used in the repo.
3. Local or hand-cleaned exports that still need a provenance pass.

The fetch script below only covers category 1:

```bash
python scripts/fetch_exact_public_data.py
```

The ACS housing snapshot is created by the canonical data rebuild rather than the
download script because it is an API response filtered to the DER panel:

```bash
CENSUS_API_KEY=your_key python scripts/rebuild_processed_data.py --reuse-nasa
```

## Exact public snapshots covered by the script

- `data/raw/interconnection/PGE_Interconnected_Project_Sites_2023-12-31.csv`
- `data/raw/interconnection/SCE_Interconnected_Project_Sites_2023-12-31.csv`
- `data/raw/interconnection/SDGE_Interconnected_Project_Sites_2023-12-31.csv`
  Source: CaliforniaDGStats monthly interconnection archive.
  Public page: https://www.californiadgstats.ca.gov/downloads/
  Scripted download: `Interconnected_Project_Sites_2023-12-31.zip`, then extract the three utility CSVs.

- `data/raw/wind/USWTDB_wind_data.csv`
  Source: USGS USWTDB CSV zip.
  Public page: https://energy.usgs.gov/uswtdb/data/

- `data/raw/boundaries/tl_2023_us_county/*`
- `data/raw/boundaries/tl_2023_us_zcta520/*`
  Source: Census TIGER/Line shapefile zips.

- `data/raw/boundaries/ca_utility_territories.geojson`
  Source: California Electric Utility Service Territory SCOUT ArcGIS FeatureServer.

- `data/raw/acs/acs_2023_5yr_housing_ca_zcta.csv`
- `data/raw/acs/acs_2023_5yr_housing_query_manifest.json`
  Source: 2023 ACS five-year detailed-table API, ZCTA geography.
  Tables: B25024 (units in structure) and B25003 (tenure).
  Coverage: B25024_001 through B25024_011 and B25003_001 through B25003_003,
  with both estimates (`E`) and margins of error (`M`). The CSV is filtered to
  ZIP/ZCTAs in the DER panel. The manifest records the endpoint, exact variable
  lists, retrieval timestamp, row count, and SHA-256 checksum; it never stores the
  Census API key.
  API endpoint: https://api.census.gov/data/2023/acs/acs5

## 2023-aligned but not yet scripted exactly

- `data/raw/solar/TTS_LBNL_public_file_21-Aug-2024_all.csv`
  The rebuild uses this file because it is the first public Tracking the Sun release that covers data through the end of 2023.
  Public page: https://emp.lbl.gov/tracking-the-sun
  Download route: https://bit.ly/trackingthesun2024, which redirects to Google Drive file
  `1Wpkzx2fe3syIcwMeKo2GPCBxWxOqpDpA`.

  There is no direct LBNL file URL to pin. Every edition is distributed as a bit.ly
  shortener onto Google Drive, so the route is recorded rather than automated: a mutable
  redirect onto a file that can be replaced in place could silently hand back a different
  vintage than the published results were built on. `fetch_exact_public_data.py` prints
  these steps and stops, and will verify a SHA-256 once `TTS_SHA256` is filled in there.

## Source page documented, exact export not yet reproducible

Each of these has a known origin, recorded in the markdown cells of
`notebooks/processing_energy_data_zip.ipynb` and the loader cells of
`notebooks/adding_predictor_data.ipynb`. What is still missing is a stable direct
download: the files are dashboard exports, so the source page is citable but the exact
workbook cannot yet be re-fetched by URL and checksummed.

- `data/raw/storage/Storage_LatLong.xlsx`
- `data/raw/storage/EnergyStorage_Cleaned_August2024_ada.xlsx`
  Source: California Energy Commission, California Energy Storage System Survey.
  Public page: https://www.energy.ca.gov/data-reports/energy-almanac/california-electricity-data/california-energy-storage-system-survey
  Granularity: ZIP code, with customer sector and nameplate capacity in kW AC.

- `data/raw/ev_chargers/Charger_County Map_Full Data_data_zip_lat-lon.xlsx`
- `data/raw/ev_chargers/Stock_Map_County (2)_Full Data_data.xlsx`
  Source: California Energy Commission, Zero Emission Vehicle and Infrastructure
  Statistics collection.
  Public page: https://www.energy.ca.gov/data-reports/energy-almanac/zero-emission-vehicle-and-infrastructure-statistics-collection/electric
  The charger file carries the Level 1 / Level 2 / DC fast split the paper relies on;
  the stock file is EV registrations.

- `data/raw/plants/Power_Plants.csv`
  Source: U.S. Energy Information Administration, Power Plants feature layer, filtered
  to California.
  Public page: https://atlas.eia.gov/datasets/eia::power-plants/explore
  Historical series: https://www.eia.gov/electricity/data/eia860/

- `data/raw/energy_burden/EB_data.csv`, `EAI_data.csv`, `EA Gap_data.csv`
  Source: California Energy Commission, Energy Equity Indicators dashboard collection,
  Deep Dive Energy.
  Public page: https://www.energy.ca.gov/data-reports/data-exploration-tools/energy-equity-indicators-dashboard-collection/deep-dive-energy
  Exports are UTF-16 tab-separated despite the `.csv` extension.

- `data/raw/demand/PGE_2023_Q*.csv`, `SCE_2023_Q*.xlsx`, `SDGE-ELEC-2023-Q*.csv`
  Source: the three investor-owned utilities' public quarterly electric usage by ZIP
  code. All four quarters are present for each utility, so demand coverage is statewide
  across PG&E, SCE and SDG&E rather than a single territory.
  Public pages, also recorded in `backend/schemas/populate_tables.py`:
  - PG&E:  https://pge-energydatarequest.com/public_datasets
  - SCE:   https://www.sce.com/regulatory/regulatory-information/energy-data-reports-compliances
  - SDG&E: https://energydata.sdge.com
  Each portal publishes per-quarter files; the 2023 Q1-Q4 sets are the ones used here.

Note: `notebooks/processing_energy_data_zip.ipynb` is marked non-canonical and reads
`TTS_LBNL_public_file_29-Sep-2025_all.csv`, a later Tracking the Sun release than the
`21-Aug-2024` file the release pipeline uses. The pipeline file is the correct one for a
2023-aligned build; the notebook reference is stale.

Two directories are leftovers that no script or notebook reads, so they are not inputs to
the current pipeline:

- `data/raw/demographics/` (`Education.xlsx`, `PopulationEstimates.xlsx`) is from the
  earlier county-level effort. Education now comes from ACS B15003 in
  `adding_predictor_data.ipynb`.
- `data/raw/natural/` holds earlier NASA POWER pulls of irradiance and wind speed at
  county and ZIP level. The pipeline now fetches NASA POWER itself into
  `data/processed/ca_zip_ghi_mean_2023.csv` and the temperature control files.

Neither is redistributed in the Zenodo record.

If you want full reproducibility for the entire rebuild pipeline, the next step is to convert the remaining category-2 and category-3 files into either:

- exact pinned downloads with checksums, or
- documented manual acquisition steps plus a local normalization script
