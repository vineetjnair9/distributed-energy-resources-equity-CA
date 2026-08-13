# California ZIP/ZCTA Distributed Energy Resource Equity Dataset (2023)

A ZIP/ZCTA-level dataset for California that integrates rooftop solar PV, battery
storage, EV charging, wind, and power-plant capacity with demographic, climate,
utility, demand, and energy-burden context, assembled so that equity questions can be
asked across several DER types under comparable outcomes and controls.

Distributed energy resource data is fragmented across technologies, agencies, and
geographies. Assembling it into one consistent panel is the point of this release.

## The headline file

`combined_der_dataset_w_controls_predictors.csv` — **2,549 ZIP/ZCTAs × 50 columns**.
This is the analysis-ready panel; the other files are the inputs and intermediates
behind it, published so results can be traced rather than taken on trust.

Geography is the 2023 Census ZIP Code Tabulation Area, keyed by `zip_code` as a
five-digit string. **Preserve the leading zero convention when loading**: read
`zip_code` as text, not as an integer.

```python
import pandas as pd
df = pd.read_csv("combined_der_dataset_w_controls_predictors.csv",
                 dtype={"zip_code": "string", "county_geoid": "string"})
```

Column groups:

| Group | Examples |
|---|---|
| DER outcomes | `PV_system_size_DC`, `storage_capacity_mw`, `total_chargers`, `level1_chargers`, `level2_chargers`, `dc_fast_chargers`, `wind_capacity_mw` |
| Demographics (ACS 2023 5-year) | `median_household_income`, race and ethnicity shares, `poverty_rate`, educational attainment |
| Housing structure and tenure | `pct_single_family_units`, `pct_multifamily_units`, `pct_mobile_home_units`, `pct_other_housing_units`, `owner_occupied_rate` |
| Climate (NASA POWER 2023) | `ghi_mean_kwh_m2_day_2023`, `cdd65_2023`, `hdd65_2023`, temperature and wind means |
| Institutional and demand | `utility`, `utility_type`, `overlap_share_of_zip`, `kwh_annual_total`, `log_kwh` |
| Energy burden | `energy_burden_pct`, `energy_affordability_index`, `energy_affordability_gap` |
| Geography | `county_geoid`, `county_name`, `area_km2`, `pop_density_km2` |

The four housing-structure shares are exhaustive and sum to 1 within floating-point
tolerance, with single-family as the natural omitted reference in regression use.
Structure is complete for 1,717 ZIP/ZCTAs and owner occupancy for a similar count;
coverage is not universal, so expect missingness on those columns.

## Scope

Every record is a California ZCTA. ZIPs outside California's 90001–96162 range are
excluded from both this dataset and any derived cluster assignments, and that
exclusion is enforced by a test in the accompanying repository rather than left as a
convention.

## What is not in this record, and why

Raw third-party inputs are **not** redistributed here. They are public, and
`SOURCES.md` cites each with a retrieval URL; `scripts/fetch_exact_public_data.py`
in the repository downloads the pinned snapshots.

`tracking_the_sun.csv` is also excluded. It is a California-filtered copy of Lawrence
Berkeley National Laboratory's *Tracking the Sun* dataset — 927 MB, and better cited
from LBNL than mirrored here. The pipeline regenerates it from the raw source.

One exception is included deliberately: `acs_2023_5yr_housing_ca_zcta.csv` is the
exact Census API response for the B25024 housing-structure and B25003 tenure tables,
with `acs_2023_5yr_housing_query_manifest.json` recording the endpoint, the variable
list, the retrieval timestamp, the row count, and a SHA-256 of the response. The
Census API serves current vintages rather than historical snapshots, so preserving
this response is what makes the housing results reproducible.

## Verifying this record

`CHECKSUMS.sha256` covers every data file in the bundle:

```bash
shasum -a 256 -c CHECKSUMS.sha256
```

## Reproducing it

The pipeline, notebooks, tests, and manuscript live in the accompanying repository.

```bash
conda env create -f environment.yml
conda activate der-data-urop
python scripts/fetch_exact_public_data.py
CENSUS_API_KEY=your_key python scripts/rebuild_processed_data.py
pytest tests/
```

The test suite checks the data contracts this release depends on: exhaustive housing
shares summing to one, small-county ZCTAs retained, no non-California ZIPs, and the
ACS snapshot matching its manifest hash.

## Citation

If you use this dataset, please cite both this record and the accompanying paper,
*The Unequal Energy Transition: Racial and Socioeconomic Disparities in Distributed
Energy Resource Adoption Across California*.

Underlying sources retain their own citation requirements — in particular LBNL
*Tracking the Sun*, the USGS US Wind Turbine Database, CaliforniaDGStats
interconnection archives, NASA POWER, and the US Census Bureau. `SOURCES.md`
lists them.
