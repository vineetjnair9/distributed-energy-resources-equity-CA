# DER Data UROP

## Project goal

This project builds a California ZIP-code-level dataset of distributed energy resources and related controls, then uses that dataset to study how DER adoption and infrastructure vary across places with different demographic, socioeconomic, climate, utility, and demand characteristics.

In practice, the project:

- cleans and aggregates raw DER source files for solar PV, EV chargers, EV stock, storage, wind, and small power plants
- merges those ZIP-level outcomes with ACS, NASA POWER, utility-territory, and electricity-demand controls
- produces a final analysis file, `data/processed/combined_der_dataset_w_controls_predictors.csv`
- uses that file for exploratory plots, regression models, robustness checks, and figure generation

## Repository navigation

The main places to look are:

- [scripts/run_all.py](scripts/run_all.py): canonical release pipeline and stage order
- [scripts/rebuild_processed_data.py](scripts/rebuild_processed_data.py): canonical processed-data builder
- [notebooks/processing_energy_data_zip.ipynb](notebooks/processing_energy_data_zip.ipynb): historical, annotated reference for the core DER cleaning
- [notebooks/adding_predictor_data.ipynb](notebooks/adding_predictor_data.ipynb): historical, annotated reference for external predictors
- [notebooks/plotting_data.ipynb](notebooks/plotting_data.ipynb): exploratory data analysis and choropleths
- [notebooks/regression.ipynb](notebooks/regression.ipynb): main regression specifications, robustness checks, LOWESS plots, and model-comparison figures
- [notebooks/plotting_outcomes.ipynb](notebooks/plotting_outcomes.ipynb): publication-style coefficient summary figures
- `data/raw/`: raw source files
- `data/processed/`: processed intermediate and final analysis files
- `outputs/`: exported tables, figures, and the methodology report
- `outputs/executed_notebooks/`: executed notebook copies produced by the rerun scripts

For most analysis work, the key final dataset is:

- `data/processed/combined_der_dataset_w_controls_predictors.csv`

## Processed data structure

The cleaned workflow now uses separate processed files for distinct stages:

- `data/processed/combined_der_dataset_full.csv`: full ZIP-level DER base panel before ACS matching
- `data/processed/combined_der_dataset_acs_matched.csv`: subset of the base panel restricted to ZIPs matched in ACS
- `data/processed/combined_der_dataset_w_controls_predictors.csv`: final merged analysis dataset used by the regression and plotting notebooks

The script also rewrites the main aggregated intermediate files and controls:

- `data/processed/aggregated_TTS.csv`
- `data/processed/aggregated_ev_chargers.csv`
- `data/processed/aggregated_ev_cars.csv`
- `data/processed/aggregated_power_plant.csv`
- `data/processed/aggregated_storage.csv`
- `data/processed/aggregated_wind.csv`
- `data/processed/acs_predictors_ca_zip.csv`
- `data/processed/ca_zip_wind_means_2023.csv`
- `data/processed/ca_zip_ghi_mean_2023.csv`
- `data/processed/ca_zip_temperature_controls_2023.csv`
- `data/processed/zip_to_utility.csv`
- `data/processed/demand.csv`

## Release quick start

Create the pinned Python 3.11 environment, run the complete release pipeline, and
execute the release checks:

```bash
conda env create -f environment.yml
conda activate der-data-urop
set -a; source .env; set +a
python scripts/fetch_exact_public_data.py
python scripts/run_all.py
pytest -q
```

The fetch step is required on a fresh clone. The Census TIGER/Line boundary files are
~950 MB and are re-downloadable byte-for-byte, so they are not version-controlled;
`fetch_exact_public_data.py` retrieves them along with the interconnection archive, the
wind turbine database, and the utility service territories. It also prints manual
acquisition steps for Tracking the Sun, which has no stable download URL.

`CENSUS_API_KEY` is needed for the live ACS pull. The default pipeline reuses the
fixed 2023 NASA POWER files, avoiding thousands of redundant network requests. Use
`python scripts/run_all.py --skip-data` to refit models and redraw figures without
rebuilding processed data.

The database is deterministic except for five optional LLM summaries and is not
version-controlled. Rebuild it with `python scripts/run_all.py --only database`;
without `OPENAI_API_KEY`, the schema and source-backed tables are still generated.

## Rebuilding processed data

This repository includes a single rebuild script that recreates the processed California ZIP-level analysis files in a clean order from raw inputs:

- [scripts/rebuild_processed_data.py](scripts/rebuild_processed_data.py)

The script is the release authority. It consolidates logic that was previously split
across the two reference notebooks:

- [notebooks/processing_energy_data_zip.ipynb](notebooks/processing_energy_data_zip.ipynb)
- [notebooks/adding_predictor_data.ipynb](notebooks/adding_predictor_data.ipynb)

### How to run

To rebuild everything, including live ACS and NASA POWER pulls:

```bash
CENSUS_API_KEY=your_key_here python scripts/rebuild_processed_data.py
```

To rebuild using the existing external-derived processed files already on disk:

```bash
python scripts/rebuild_processed_data.py --skip-external
```

### Notes

- The script preserves the manual row-level fixes currently embedded in the notebooks for power plants and EV charger ZIP assignments.
- The script uses the local file `data/raw/boundaries/ca_utility_territories.geojson` for the ZIP-to-utility crosswalk.
- Housing structure comes from all eleven B25024 categories. Models 2C and 2D omit
  single-family housing as the reference and include multifamily, mobile-home, and
  boat/RV/van/other shares; Model 2D additionally includes B25003 owner occupancy
  with renter occupancy as the reference.
- All valid ZIP/ZCTAs remain in the shared analysis file. The minimum-five-observation
  county rule is applied only to specifications requesting county-clustered errors.
- A live ACS rebuild stores exact B25024/B25003 estimates and margins of error plus a
  credential-free query manifest under `data/raw/acs/`.
- The final analysis notebooks read `data/processed/combined_der_dataset_w_controls_predictors.csv`.
- `data/processed/combined_der_dataset_full.csv` in the current workspace is a reconstructed base artifact derived from the base columns embedded in `combined_der_dataset_w_controls_predictors.csv`, because the earlier historical full-base file had been overwritten before this cleanup.

## Rerunning models and figures

To rerun the main regression notebook and refresh the figures in one step:

```bash
python scripts/run_all.py --only models figures
```

This:

- executes `notebooks/regression.ipynb`
- saves an executed copy to `outputs/executed_notebooks/regression.executed.ipynb`
- regenerates the standardized figures under `outputs/standardized_figures/`
- rebuilds the presentation panels and mirrors everything into `site/assets/figures/`

If you only want to redraw the figures without refitting the models:

```bash
python scripts/run_all.py --only figures
```

The figures stage runs two steps in order. `regenerate_standardized_figures.py` draws the
coefficient figures from the standardized tables, then `build_site_index_assets.py --sync`
builds the descriptive panels, LOWESS gradients and coefficient paths and mirrors the PNGs
into the site assets folder. Only the first is needed to reproduce the results, so if you
want the analysis output without the presentation assets:

```bash
python scripts/run_all.py --only figures --skip-assets
```

`build_site_index_assets.py` is also runnable on its own, and `--sync-only` mirrors
existing figures without rebuilding them.

To rerun only some outcomes, or to execute a single notebook without running a stage:

```bash
python scripts/run_all.py --only models --outcomes y_pv y_storage
python scripts/run_all.py --run-notebook plotting_outcomes
```

### Model taxonomy: ladder vs. control-block sensitivity

`notebooks/regression.ipynb` produces two different kinds of robustness evidence per
outcome, and the two should not be conflated:

- **Models C1-C5 are the genuinely nested cumulative ladder.** Each rung's formula is
  a strict superset of the previous rung's (core -> + education/housing value -> +
  housing structure/tenure -> + utility FE -> + county FE in place of climate), and all
  five are fit on one frozen common sample (`common_sample_index` in
  `scripts/model_helpers.py`) so coefficient movement across rungs reflects added
  controls, not a shifting sample. **Model S (saturated confounders)** is the same
  specification as C5, reported under its own label. **Model O (over-controlled)** adds
  the demand proxy and infrastructure-capacity controls on top of C5 - those sit on the
  causal path from income/race to DER adoption, so Model O is a deliberately
  conservative **lower bound** on the effect, not a preferred specification.
- **Models 1-9 (and 2C/2D/3A-3D/4/4R/5C/6A/6B/7/7pc/9A) are control-block sensitivity
  analyses, not a ladder.** Each varies exactly one block relative to the Model 1
  baseline - swapping the climate control (3A/3B/3C), dropping climate for geography
  (6A/6B), adding one SES block at a time - so the blocks are not cumulative with each
  other, and reading across them left-to-right is not "adding more controls." They
  remain valuable for asking which single block moves a coefficient, which the C-ladder
  cannot show on its own.

Two supporting artifacts sit alongside the ladder:

- `outputs/tables/spec_curve.csv` - a specification curve over every combination of the
  six confounder blocks (`CONFOUNDER_BLOCKS`), reporting only the focal terms
  (income, `pct_black`, `pct_hispanic`, `pct_asian`). Skip it during quick iteration
  with `RUN_SPEC_CURVE=0`.
- `outputs/tables/oster_delta.csv` - Oster (2019) delta bounds comparing Model C1 to
  Model S for each focal term, i.e. how much selection on unobservables (relative to
  the observed confounders) would be needed to explain away the estimated effect.

## Recommended workflow

If you want to understand the project from start to finish, the most useful order is:

1. Run or inspect [scripts/run_all.py](scripts/run_all.py)
2. Review the canonical builder, [scripts/rebuild_processed_data.py](scripts/rebuild_processed_data.py)
3. Use the two data-construction notebooks only as annotated source-cleaning references
4. Use [notebooks/plotting_data.ipynb](notebooks/plotting_data.ipynb) for exploratory checks
5. Use [notebooks/regression.ipynb](notebooks/regression.ipynb) for the main models
6. Use [notebooks/plotting_outcomes.ipynb](notebooks/plotting_outcomes.ipynb) for summary figures

## Legacy background

This repository started partly as a broader DER data catalog and county-level mapping effort. The notebooks under `data/mapping_files/` reflect that earlier structure and are useful background, but they are not part of the main final California ZIP-level regression workflow.

## Licensing

The code in this repository -- the pipeline, scripts, notebooks, and tests -- is
released under the MIT License; see [LICENSE](LICENSE).

The dataset is released separately under CC-BY-4.0 as a Zenodo record, built by
`scripts/make_zenodo_bundle.py` from the metadata in `release/zenodo/`.

Raw third-party inputs are neither redistributed nor relicensed here. They remain
under their own terms and carry their own citation requirements -- notably LBNL
*Tracking the Sun*, the USGS US Wind Turbine Database, CaliforniaDGStats, NASA POWER,
and the US Census Bureau. `data/raw/SOURCES.md` documents each with a retrieval URL.
