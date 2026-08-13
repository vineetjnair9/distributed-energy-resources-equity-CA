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
  The rebuild uses this file because it is the first subsequent public Tracking the Sun release that covers data through the end of 2023.
  Public page: https://emp.lbl.gov/tracking-the-sun/
  The exact stable direct-download URL still needs to be pinned before it is safe to automate in `fetch_exact_public_data.py`.

## Public but not yet pinned to the exact historical file

These are publicly available, but the exact historical workbook or export used in this repo is not yet fully resolved:

- `data/raw/storage/Storage_LatLong.xlsx`
- `data/raw/ev_chargers/Stock_Map_County (2)_Full Data_data.xlsx`
- `data/raw/ev_chargers/Charger_County Map_Full Data_data_zip_lat-lon.xlsx`
- `data/raw/plants/Power_Plants.csv`
- `data/raw/demand/*`

In several cases the repo contains dashboard-export filenames that do not map cleanly to a stable permanent URL without an additional archival pass.

## Current nearest public sources

These links are useful for reconstructing those families of data, but they should not yet be treated as the exact files used in the current 2023-aligned repo state.

- California Energy Storage System Survey:
  https://www.energy.ca.gov/data-reports/energy-almanac/california-electricity-data/california-energy-storage-system-survey

- ZEV and Infrastructure Stats Data:
  https://www.energy.ca.gov/files/zev-and-infrastructure-stats-data

- U.S. Power Plants:
  https://atlas.eia.gov/datasets/bf5c5110b1b944d299bb683cdbd02d2a_0/explore

If you want full reproducibility for the entire rebuild pipeline, the next step is to convert the remaining category-2 and category-3 files into either:

- exact pinned downloads with checksums, or
- documented manual acquisition steps plus a local normalization script
