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

- [notebooks/processing_energy_data_zip.ipynb](/DER_data_UROP/notebooks/processing_energy_data_zip.ipynb): builds the core ZIP-level DER panel and the final merged analysis dataset
- [notebooks/adding_predictor_data.ipynb](/DER_data_UROP/notebooks/adding_predictor_data.ipynb): builds ACS, NASA POWER, utility, and demand control files
- [notebooks/plotting_data.ipynb](/DER_data_UROP/notebooks/plotting_data.ipynb): exploratory data analysis and choropleths
- [notebooks/regression.ipynb](/DER_data_UROP/notebooks/regression.ipynb): main regression specifications, robustness checks, LOWESS plots, and model-comparison figures
- [notebooks/plotting_outcomes.ipynb](/DER_data_UROP/notebooks/plotting_outcomes.ipynb): publication-style coefficient summary figures
- [scripts/rebuild_processed_data.py](/DER_data_UROP/scripts/rebuild_processed_data.py): single script to rebuild processed data in a clean order from raw inputs
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

## Rebuilding processed data

This repository includes a single rebuild script that recreates the processed California ZIP-level analysis files in a clean order from raw inputs:

- [scripts/rebuild_processed_data.py](/DER_data_UROP/scripts/rebuild_processed_data.py)

The script consolidates logic that was previously split across:

- [notebooks/processing_energy_data_zip.ipynb](/DER_data_UROP/notebooks/processing_energy_data_zip.ipynb)
- [notebooks/adding_predictor_data.ipynb](/DER_data_UROP/notebooks/adding_predictor_data.ipynb)

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
- The final analysis notebooks read `data/processed/combined_der_dataset_w_controls_predictors.csv`, so if that file is unchanged, previously generated regression results should remain unchanged.
- `data/processed/combined_der_dataset_full.csv` in the current workspace is a reconstructed base artifact derived from the base columns embedded in `combined_der_dataset_w_controls_predictors.csv`, because the earlier historical full-base file had been overwritten before this cleanup.

## Rerunning models and syncing figures

To rerun the main regression notebook and refresh the saved figure assets in one step:

```bash
python scripts/run_regression_notebook.py
```

This script:

- executes `notebooks/regression.ipynb`
- saves an executed copy to `outputs/executed_notebooks/regression.executed.ipynb`
- regenerates the standardized paper figures
- mirrors figure outputs into `site/assets/figures/` so they remain easy to access later

If you only want to refresh the figure copies under the site assets folder without rerunning models:

```bash
python scripts/sync_figure_assets.py
```

## Recommended workflow

If you want to understand the project from start to finish, the most useful order is:

1. Rebuild or inspect the processed data with [scripts/rebuild_processed_data.py](/DER_data_UROP/scripts/rebuild_processed_data.py)
2. Review [notebooks/processing_energy_data_zip.ipynb](/DER_data_UROP/notebooks/processing_energy_data_zip.ipynb)
3. Review [notebooks/adding_predictor_data.ipynb](/DER_data_UROP/notebooks/adding_predictor_data.ipynb)
4. Use [notebooks/plotting_data.ipynb](/DER_data_UROP/notebooks/plotting_data.ipynb) for exploratory checks
5. Use [notebooks/regression.ipynb](/DER_data_UROP/notebooks/regression.ipynb) for the main models
6. Use [notebooks/plotting_outcomes.ipynb](/DER_data_UROP/notebooks/plotting_outcomes.ipynb) for summary figures

## Legacy background

This repository started partly as a broader DER data catalog and county-level mapping effort. Some notebooks under `data/mapping_files/` and `notebooks/data_retrieval.ipynb` reflect that earlier structure and are useful background, but they are not part of the main final California ZIP-level regression workflow.
