# Methodology Report

## 1. Project overview

This project reconstructs a California ZIP-code-level dataset of distributed energy resources (DERs), merges that panel with demographic, climate, utility-territory, and electricity-demand controls, and then analyzes disparities in DER adoption and infrastructure using a sequence of regression specifications. The clearest evidence for that end-to-end workflow is in `notebooks/processing_energy_data_zip.ipynb` cells 32-39, `notebooks/adding_predictor_data.ipynb` cells 5 and 11-20, and `notebooks/regression.ipynb` cells 2-41.

Explicitly shown in the notebooks, the main modeled outcomes are `y_pv`, `y_chargers`, `y_storage`, `y_wind_mw`, and `any_turbines`, all derived from ZIP-level DER counts or capacities (`notebooks/regression.ipynb`, cell 2). The main explanatory variables are `log_median_household_income`, `pct_black`, `pct_hispanic`, `pct_asian`, and `poverty_rate`, with climate/resource controls selected by outcome (`notebooks/regression.ipynb`, cells 5-6). The interpretation markdown inside the regression notebook makes the research emphasis especially clear: the analysis is framed around how income, race/ethnicity, poverty, and environmental controls relate to solar PV, EV charging, storage, and wind deployment across ZIP codes (`notebooks/regression.ipynb`, markdown after cells 8, 11, 14, 18, 23, 26, 29, and 33).

Inferred from context rather than explicitly stated in one single notebook: the overarching research question appears to be whether DER adoption and clean-energy infrastructure are distributed unevenly across California ZIP codes after accounting for climate/resource suitability, socioeconomic controls, utility geography, and existing infrastructure. I am treating that as an inference because no notebook opens with a formal research question statement, but that framing is strongly supported by the chosen outcomes, predictors, robustness checks, and figure titles.

The notebook order that is most likely for the final ZIP-level workflow is:

1. `notebooks/processing_energy_data_zip.ipynb`
2. `notebooks/adding_predictor_data.ipynb`
3. `notebooks/plotting_data.ipynb`
4. `notebooks/regression.ipynb`
5. `notebooks/plotting_outcomes.ipynb`

That ordering is inferred from file dependencies. `processing_energy_data_zip.ipynb` creates the base DER panel and now writes `../data/processed/combined_der_dataset_full.csv` plus multiple aggregated source files (`notebooks/processing_energy_data_zip.ipynb`, cells 32-33). `adding_predictor_data.ipynb` now reads `../data/processed/combined_der_dataset_full.csv` and writes the ACS, NASA POWER, utility, and demand control files, along with an ACS-matched subset saved separately as `../data/processed/combined_der_dataset_acs_matched.csv`. Those controls later appear in `processing_energy_data_zip.ipynb` cell 39 and throughout `regression.ipynb`. `plotting_data.ipynb` reads `combined_der_dataset_w_controls_predictors.csv`, so it must come after the merged dataset exists. `regression.ipynb` reads that same final dataset and writes coefficient tables into `../outputs/tables/`. `plotting_outcomes.ipynb` then reads those exported coefficient CSVs from `../outputs/standardized_tables/` and makes publication-style summary figures.

Several other notebooks appear auxiliary or exploratory rather than part of the final California ZIP workflow. `notebooks/processing_energy_data_census.ipynb` is an unexecuted census-tract attempt. `notebooks/clustering.ipynb` performs optional unsupervised clustering after the final dataset exists. `data/mapping_files/Creating State Dataframes.ipynb`, `data/mapping_files/County Data.ipynb`, and `notebooks/data_retrieval.ipynb` belong to an earlier county-level data-catalog system rather than the final ZIP-level regression workflow.

## 2. Data and inputs

The project pulls together multiple raw DER, demographic, climate, and geography sources.

The DER source files used in the main ZIP-level build are explicit in `notebooks/processing_energy_data_zip.ipynb`. Storage comes from `../data/raw/storage/Storage_LatLong.xlsx`, renamed into a standardized schema with fields such as `utility_name`, `storage_capacity_mw`, `nameplate_capacity_kw_ac`, `fuel_type`, `zip_code`, `sector`, `latitude`, and `longitude` (`notebooks/processing_energy_data_zip.ipynb`, cell 6). Wind comes from `../data/raw/wind/USWTDB_wind_data.csv`, filtered to California and spatially joined to ZIP polygons (`notebooks/processing_energy_data_zip.ipynb`, cell 10). Power-plant data comes from `../data/raw/plants/Power_Plants.csv`, with extensive column renaming and several manual row corrections (`notebooks/processing_energy_data_zip.ipynb`, cell 14). EV cars come from `../data/raw/ev_chargers/Stock_Map_County (2)_Full Data_data.xlsx`, and EV chargers come from `../data/raw/ev_chargers/Charger_County Map_Full Data_data_zip_lat-lon.xlsx` (`notebooks/processing_energy_data_zip.ipynb`, cell 18). Solar PV installations come from `../data/raw/solar/TTS_LBNL_public_file_29-Sep-2025_all.csv` (`notebooks/processing_energy_data_zip.ipynb`, cell 30).

The demographic and control datasets are constructed in `notebooks/adding_predictor_data.ipynb`. ACS 5-year data are requested from the Census API endpoint `https://api.census.gov/data/2023/acs/acs5` for all ZCTAs nationwide, then filtered down to the ZIP codes in the analysis panel (`notebooks/adding_predictor_data.ipynb`, cell 5). The selected ACS variables explicitly include total population, median household income, median housing value, race/ethnicity counts from `B03002`, poverty counts from `B17001`, and educational attainment counts from `B15003` (`notebooks/adding_predictor_data.ipynb`, cell 5).

Climate and resource controls are fetched from NASA POWER. Wind means use `WS10M` and `WS50M` over the daily period from `20230101` to `20231231` and are saved to `../data/processed/ca_zip_wind_means_2023.csv` (`notebooks/adding_predictor_data.ipynb`, cell 11). Solar irradiance uses `ALLSKY_SFC_SW_DWN` over the same date range and is saved to `../data/processed/ca_zip_ghi_mean_2023.csv` (`notebooks/adding_predictor_data.ipynb`, cell 13). Temperature controls use `T2M`, `T2M_MAX`, and `T2M_MIN`, and derive annual means, summer means, and degree-day totals saved to `../data/processed/ca_zip_temperature_controls_2023.csv` (`notebooks/adding_predictor_data.ipynb`, cell 15).

Utility-territory mappings are generated from the ArcGIS FeatureServer `California_Electric_Utility_Service_Territory_SCOUT` and national TIGER ZCTA/state layers, then written to `../data/processed/zip_to_utility.csv` (`notebooks/adding_predictor_data.ipynb`, cell 17). Electricity-demand controls are built from quarterly utility usage files: `PGE_2023_Q{q}_ElectricUsageByZip.csv`, `SCE_2023_Q{q}_ElectricUsageByZip.xlsx`, and `SDGE-ELEC-2023-Q{q}.csv`, then collapsed into `../data/processed/demand.csv` (`notebooks/adding_predictor_data.ipynb`, cells 19-20).

Boundary files used repeatedly are `../data/raw/boundaries/tl_2023_us_zcta520/tl_2023_us_zcta520.shp` and `../data/raw/boundaries/tl_2023_us_county/tl_2023_us_county.shp` (`notebooks/processing_energy_data_zip.ipynb`, cell 39; `notebooks/regression.ipynb`, cell 36). The plotting notebook also uses `tl_2023_us_zcta520.shp` and clips it to California (`notebooks/plotting_data.ipynb`, cells 3-4).

The final processed inputs currently present on disk include:

- `data/processed/combined_der_dataset_full.csv` with 2,572 rows and 13 columns
- `data/processed/combined_der_dataset_acs_matched.csv` with 1,765 rows and 13 columns
- `data/processed/combined_der_dataset_w_controls_predictors.csv` with 2,572 rows and 44 columns
- `data/processed/acs_predictors_ca_zip.csv` with 1,752 rows and 10 columns
- `data/processed/ca_zip_wind_means_2023.csv` with 1,846 rows and 5 columns
- `data/processed/ca_zip_ghi_mean_2023.csv` with 1,846 rows and 4 columns
- `data/processed/ca_zip_temperature_controls_2023.csv` with 1,846 rows and 9 columns
- `data/processed/zip_to_utility.csv` with 1,660 rows and 6 columns
- `data/processed/demand.csv` with 1,690 rows and 4 columns

Those row counts are explicit from the current processed files and partly echoed in notebook outputs, especially the ACS and NASA POWER saves (`notebooks/adding_predictor_data.ipynb`, cells 5, 11, 13, 15, 17).

## 3. Preprocessing

The preprocessing pipeline has two layers: source-specific cleaning followed by cross-dataset merging.

For storage, the code renames columns, recomputes `storage_capacity_mw` from `nameplate_capacity_kw_ac / 1000`, filters to sectors `["Residential", "Commercial"]`, and keeps only installations with `storage_capacity_mw <= DER_THRESHOLD`, where `DER_THRESHOLD = 5` in the notebook as executed (`notebooks/processing_energy_data_zip.ipynb`, cell 6). The notebook comments indicate that `10` MW was considered as a robustness alternative, but the active threshold in code is `5`.

For wind, the code renames USWTDB fields, filters `state == "CA"`, creates a GeoDataFrame in `EPSG:4326`, reads ZCTAs, and performs a point-in-polygon spatial join using `predicate="intersects"` rather than `within`, explicitly because boundary points could be missed otherwise (`notebooks/processing_energy_data_zip.ipynb`, cell 10). It then converts `turbine_capacity_kw` into `turbine_mw` and aggregates to ZIP-level `wind_capacity_mw` and `wind_turbine_count`.

For power plants, the preprocessing is substantial. The notebook manually patches multiple row-level county, address, city, and ZIP values for known bad records, maps counties to FIPS codes, renames a large set of columns into a standardized schema, converts state names to abbreviations, keeps California only, cleans `zip_code` into five-character strings, and separates plants into two groups (`notebooks/processing_energy_data_zip.ipynb`, cell 14). The DER-like plants are defined sectorally as `Commercial Non-CHP`, `Industrial Non-CHP`, `Commercial CHP`, and `Industrial CHP`, with `plant_capacity_mw <= DER_THRESHOLD`. Separately, `power_plant_controls` keeps `"Electric Utility"` and `"IPP Non-CHP"` sectors to create ZIP-level grid-supply controls (`notebooks/processing_energy_data_zip.ipynb`, cell 14). The analysis cell that follows explicitly audits missing ZIP codes and total capacity losses from dropping `"00nan"` ZIPs (`notebooks/processing_energy_data_zip.ipynb`, cell 16).

For EV chargers, the notebook standardizes county strings, maps counties to `fips`, drops explanatory spreadsheet columns, renames charger-specific fields, zero-pads `zip_code`, then reassigns ZIP codes spatially by joining charger points to ZIP polygons (`notebooks/processing_energy_data_zip.ipynb`, cells 18 and 20). After that spatial join, the notebook makes many manual row-level ZIP corrections for specific indices, for example forcing records at indices `892`, `893`, `1934`, `1935`, `7032`-`7055`, `13076`, and `13077` to chosen ZIP codes (`notebooks/processing_energy_data_zip.ipynb`, cell 20). That is explicit, and it matters methodologically because some charger ZIP assignments are hand-corrected rather than fully automated.

For EV cars, the preprocessing is simpler: rename columns such as `MAKE`, `MODEL`, `NonZEV vs ZEV`, `CA ZIP`, and `Fuel Type ` to `make`, `model`, `nonzev_v_zev`, `zip_code`, and `fuel_type` (`notebooks/processing_energy_data_zip.ipynb`, cell 18). The notebook then uses grouped counts by `zip_code` as a measure of local ZEV prevalence (`notebooks/processing_energy_data_zip.ipynb`, cell 33).

For Tracking the Sun, the solar file is filtered to `state == "CA"` and several malformed ZIP strings are explicitly excluded: `"-0001"`, `"-01.0"`, `"000.0"`, `"2399."`, and `"831.0"` (`notebooks/processing_energy_data_zip.ipynb`, cell 30). The notebook also keeps only nonnegative `PV_system_size_DC` values before aggregation (`notebooks/processing_energy_data_zip.ipynb`, cell 33).

The ACS preprocessing in `adding_predictor_data.ipynb` is careful about denominators and sentinel values. Both the panel ZIPs and ACS ZCTA codes are normalized to five-character strings. Numeric conversion is forced for all requested ACS fields. Negative median income and housing values are set to missing because the notebook explicitly interprets them as sentinel artifacts. Zero-population ZCTAs are dropped. Shares such as `pct_black`, `pct_hispanic`, `pct_asian`, `poverty_rate`, `pct_bachelors_plus`, `pct_high_school_plus`, and `pct_some_college_plus` are constructed using denominators with zeros replaced by missing (`notebooks/adding_predictor_data.ipynb`, cell 5).

The NASA POWER preprocessing computes ZIP centroids from CA-intersecting ZCTAs by first projecting to `EPSG:3310`, finding centroids, and then transforming back to `EPSG:4326` (`notebooks/adding_predictor_data.ipynb`, cells 11, 13, and 15). This is explicitly done to avoid centroid mistakes in geographic CRS. Temperature preprocessing additionally converts Celsius to Fahrenheit for degree-day calculations and uses a base temperature of `65.0` Fahrenheit (`notebooks/adding_predictor_data.ipynb`, cell 15).

At the merge stage, the processed panel is joined leftwise with `acs`, `ghi`, `temp`, `wind`, `zip2utility`, and `demand` (`notebooks/processing_energy_data_zip.ipynb`, cell 39). Missing values in `wind_capacity_mw`, `wind_turbine_count`, and `plant_capacity_mw` are then filled with zero, duplicate merge columns are dropped, a ZIP-to-county dominant-overlap mapping is computed from ZCTA-county intersections, ZIP polygon area is merged in as `area_km2`, and `pop_density_km2` plus `log_pop_density` are derived (`notebooks/processing_energy_data_zip.ipynb`, cell 39). Counties with fewer than `min_n = 5` ZIP observations are removed before the final file is saved.

## 4. Feature engineering / variable construction

The final modeling notebook creates the outcomes and covariates used in analysis. The clearest feature-construction logic is in `notebooks/regression.ipynb` cells 2-6.

The outcome transformations are explicit. `prep_outcomes_per_capita` filters out ZIPs with `total_population < 1000`, then creates:

- `level2_chargers_per_1k` and `y_level2_chargers = np.log1p(level2_chargers_per_1k)`
- `level1_chargers_per_1k` and `y_level1_chargers = np.log1p(level1_chargers_per_1k)`
- `dc_fast_chargers_per_1k` and `y_dc_fast_chargers = np.log1p(dc_fast_chargers_per_1k)`
- `chargers_per_1k` and `y_chargers = np.log1p(chargers_per_1k)`
- `pv_kw_per_1k` and `y_pv = np.log1p(pv_kw_per_1k)`
- `storage_mw_per_100k` and `y_storage = np.log1p(storage_mw_per_100k)`
- `wind_mw_per_100k` and `y_wind_mw = np.log1p(wind_mw_per_100k)`
- `y_turbines = np.log1p(wind_turbine_count)`
- `any_turbines = (wind_turbine_count > 0).astype(int)`

These transformations establish that the study is mostly about per-capita intensity measures with `log1p` transforms, except for the binary wind-presence outcome `any_turbines` (`notebooks/regression.ipynb`, cell 2).

Income and housing are log-transformed as `log_median_household_income` and `log_median_housing_value` (`notebooks/regression.ipynb`, cell 3). Cooling and heating degree days are also manually standardized into `stand_cdd65_2023` and `stand_hdd65_2023`, though the active regression specifications shown later use the raw `cdd65_2023` and `hdd65_2023` variables rather than the standardized versions (`notebooks/regression.ipynb`, cells 3 and 5). That is explicit.

The main predictor set is defined as:

- `income = "log_median_household_income"`
- `race = ["pct_black", "pct_hispanic", "pct_asian"]`
- `controls_common = ["poverty_rate", "total_population"]`

Climate/resource controls are then chosen by outcome:

- `controls_3A = ["cdd65_2023", "hdd65_2023"]`
- `controls_3B = ["t2m_mean_c_2023"]`
- `controls_3C = ["ghi_mean_kwh_m2_day_2023"]`
- `controls_3D = ["wind_ws50m_mean_2023"]`

with `controls_cur` set dynamically based on `y` (`notebooks/regression.ipynb`, cell 5). This is one of the clearest pieces of notebook evidence for the analytical design.

Additional engineered controls include:

- `ses_bach = ["pct_bachelors_plus"]`
- `ses_house = ["log_median_housing_value"]`
- `utility_fe = "C(utility)"`
- `county_fe = "C(county_geoid)"`
- `latlon = ["lat", "lon"]`
- `demand_proxy = "log_kwh"`

(`notebooks/regression.ipynb`, cell 5)

Infrastructure-control features are built in two ways. Model 7 adds raw capacities/counts from the candidate set `["plant_capacity_mw", "storage_capacity_mw", "wind_capacity_mw", "wind_turbine_count", "PV_system_size_DC"]`, excluding the columns that directly define the current outcome (`notebooks/regression.ipynb`, cell 29). Model 7pc builds per-capita versions such as `plant_mw_per_100k`, `storage_mw_per_100k`, `wind_mw_per_100k_ctrl`, and `turbines_per_100k` (`notebooks/regression.ipynb`, cell 30).

One subtle feature-engineering detail worth noting: the `plotting_data.ipynb` notebook still references columns like `ghi_mean_kwh_m2_day_2024` and `wind_ws50m_mean_2024` in helper code, even though the actual processed files and the regression notebook use `..._2023`. That suggests the project evolved over time and some exploratory plotting code was not fully updated (`notebooks/plotting_data.ipynb`, cell 3; `notebooks/regression.ipynb`, cell 3).

## 5. Modeling and analysis

The main analytical method is OLS regression using `statsmodels.formula.api.ols`, with heteroskedasticity-robust `HC1` standard errors by default and cluster-robust standard errors in selected specifications (`notebooks/regression.ipynb`, cell 2). Each model is built from a formula string assembled by `build_formula`, which concatenates the income term, race-share terms, `controls_common`, an optional demand proxy, outcome-specific climate/resource controls, optional extra terms, and optional fixed effects while deduplicating repeated regressors (`notebooks/regression.ipynb`, cell 6).

The specification sequence is explicit and orderly.

Model 1 is the baseline climate/resource-controlled specification:

- `f1 = build_formula(y, climate_controls=controls_cur, controls_common=["poverty_rate"], fe_terms=[])`

(`notebooks/regression.ipynb`, cell 8)

Model 2 adds one socioeconomic proxy at a time:

- Model 2A adds `pct_bachelors_plus`
- Model 2B adds `log_median_housing_value`

(`notebooks/regression.ipynb`, cell 11)

Model 3 runs climate/resource robustness checks:

- Model 3A uses `["cdd65_2023", "hdd65_2023"]`
- Model 3B uses `["t2m_mean_c_2023"]`
- Model 3C uses `["ghi_mean_kwh_m2_day_2023"]`

(`notebooks/regression.ipynb`, cell 14)

For wind outcomes, the notebook separately defines `controls_3D = ["wind_ws50m_mean_2023"]` and assigns that to `controls_cur` when `y == "y_wind_mw"` or `y == "any_turbines"` (`notebooks/regression.ipynb`, cell 5). That means the wind analyses use the 50-meter mean wind-speed control in baseline and robustness models. This is explicit.

Model 4 adds centered income-by-race interaction terms. `center_cols` mean-centers `log_median_household_income`, `pct_black`, `pct_hispanic`, and `pct_asian`, then the formula includes interaction terms between centered income and each centered race-share variable (`notebooks/regression.ipynb`, cell 18). A reduced interaction variant `Model 4R` is also fit.

Model 5 adds utility fixed effects through `C(utility)`, and Model 5C re-estimates that same formula with county-clustered standard errors via `cluster_col="county_geoid"` (`notebooks/regression.ipynb`, cell 23).

Model 6 offers geography adjustments in two forms:

- Model 6A adds `lat` and `lon`
- Model 6B adds `C(county_geoid)`
- A separate clustered-SE version of Model 1 is saved as `No County FE + clustered SEs (county)`

(`notebooks/regression.ipynb`, cell 26)

Model 7 adds outcome-safe infrastructure controls, and Model 7pc repeats that with per-capita infrastructure variables (`notebooks/regression.ipynb`, cells 29-30). Model 8 adds `log_kwh` as a demand proxy (`notebooks/regression.ipynb`, cell 33). Model 9 uses alternative formulas that add `y_pv`, `y_chargers`, or both as controls to the baseline without the income and race block, despite the title string saying `"Model 1 baseline (no climate controls)"` for the first of those formulas (`notebooks/regression.ipynb`, cell 35). Because `f_base = make_formula(y, controls_cur + core_controls)`, this title is internally inconsistent with the actual code: the formula still includes `controls_cur`, so it is not literally “no climate controls.” That inconsistency should be treated as a gap in documentation rather than a modeling fact.

The notebook also includes a predictive-comparison section that is more exploratory than core. It compares:

- linear regression
- degree-2 polynomial regression
- random forest
- XGBoost

using five-fold shuffled cross-validation with median imputation inside each pipeline (`notebooks/regression.ipynb`, cell 38). The hyperparameters are explicit:

- `RandomForestRegressor(n_estimators=300, max_depth=6, random_state=42, n_jobs=-1)`
- `XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0, random_state=42, n_jobs=-1)`

The clustering notebook is a separate analytical branch, not obviously part of the main final methodology. It loads `combined_der_dataset_w_controls_predictors.csv`, converts several outcomes to per-capita rates, imputes with median values, standardizes all columns, one-hot encodes `utility_type`, and then applies PCA plus KMeans, along with optional t-SNE and UMAP projections (`notebooks/clustering.ipynb`, cells 2-7 and 10). The notebook explicitly evaluates combinations of principal-component counts and cluster counts using silhouette, Calinski-Harabasz, Davies-Bouldin, and inertia, and marks `3 PCs, 4 clusters`, `3 PCs, 5 clusters`, and `5 PCs, 5 clusters` as “Best combos” in markdown (`notebooks/clustering.ipynb`, cell 9). Because the last map-building cell fails with `NameError: name 'analysis_df' is not defined`, and because the notebook itself labels t-SNE/UMAP as “Optional clustering methods,” I would classify clustering as exploratory or secondary rather than part of the final reported pipeline.

## 6. Evaluation

The main regression evaluation strategy is inferential rather than purely predictive. Each fitted model produces:

- coefficient tables
- standard errors
- p-values
- confidence intervals
- VIF diagnostics for multicollinearity

That is explicit from `quick_print`, which writes `res.summary2().tables[1]` to CSV, and from repeated `print(vif_from_formula(...))` calls after nearly every model (`notebooks/regression.ipynb`, cell 2 and model cells 8, 11, 14, 18, 23, 26, 29, 30, 33, and 35).

Standard-error handling is also explicit. Ordinary models use `cov_type="HC1"`. Selected robustness models instead use clustered covariance with groups defined by `county_geoid`, after aligning the clustering groups to the rows actually used by the fitted model (`notebooks/regression.ipynb`, cell 2). That means the primary inferential metrics are coefficient significance and robustness across specifications rather than goodness-of-fit alone.

The predictive evaluation branch uses five-fold `KFold(n_splits=5, shuffle=True, random_state=42)` cross-validation and reports `cv_r2_mean`, `cv_r2_sd`, `cv_rmse_mean`, and `cv_rmse_sd` for each predictive model (`notebooks/regression.ipynb`, cell 38). The notebook then visualizes those results with error bars in `plot_model_comparison` (`notebooks/regression.ipynb`, cell 39). Because this section is appended after the inferential models and is not integrated into the main coefficient-figure notebook, I interpret it as an exploratory check on whether nonlinear models materially outperform simple linear ones.

The clustering branch evaluates cluster quality using `silhouette_score`, `calinski_harabasz_score`, `davies_bouldin_score`, explained variance retained in PCA, and KMeans inertia (`notebooks/clustering.ipynb`, cell 7). Those metrics are written to `../outputs/tables/gridsearch_results.csv` (`notebooks/clustering.ipynb`, cell 8).

## 7. Visualizations and outputs

The project produces three layers of visual output: exploratory EDA graphics, model-specific maps and relationship plots, and publication-style summary figures.

The exploratory plotting notebook defines missingness bars, histogram grids with optional `log1p`, correlation heatmaps, selected scatterplots, lat/lon scatterplots, and ZIP-level choropleths over California ZCTAs (`notebooks/plotting_data.ipynb`, cell 3). It reads `../data/processed/combined_der_dataset_w_controls_predictors.csv` and generates an overview through `run_eda_overview` (`notebooks/plotting_data.ipynb`, cell 4). It also exports a geometry-enriched file, `../data/processed/combined_der_dataset_w_shape.csv` (`notebooks/plotting_data.ipynb`, cell 5). The separate notebook `data/mapping_files/important_plots.ipynb` appears to be an older EDA notebook with helper functions such as `plot_missingness`, `plot_hist`, `plot_top_n`, `plot_charger_composition`, `scatter_with_fit`, `boxplot_by_presence`, and `corr_heatmap`. That notebook errors on a missing `median_household_income` column, which suggests it is exploratory and out of sync with the final processed files.

Within the regression notebook, each fitted model writes a coefficient table CSV to `../outputs/tables/` using the pattern `"{y} | {model title}.csv"` (`notebooks/regression.ipynb`, cell 2 and repeated model calls). The notebook also creates:

- LOWESS-with-bootstrap income plots saved as `../outputs/figures/{term_labels[y]}_income_lowess.png` (`notebooks/regression.ipynb`, cell 37)
- model-comparison bar charts saved as `../outputs/figures/{term_labels[y]}_model_comparison.png` (`notebooks/regression.ipynb`, cell 39)
- spatial figures for every model specification saved into `../outputs/figures/{y[2:]}_maps/` with filenames like `{outcome_col}_{safe_slug(model_name)}_spatial_figure.png` (`notebooks/regression.ipynb`, cells 40-41)

The postprocessing notebook `notebooks/plotting_outcomes.ipynb` then loads all coefficient CSVs from `../outputs/standardized_tables/`, parses filenames into outcome/model metadata, harmonizes column names like `"Coef."`, `"Std.Err."`, `"P>|z|"`, and confidence-interval bounds, and produces three figure families:

- `main_dot_whisker_across_outcomes.png`
- `{outcome}_robustness.png` for each outcome
- `coef_heatmap_appendix.png`

(`notebooks/plotting_outcomes.ipynb`, cells 1-7)

The structured processed data outputs explicitly written by the preprocessing notebooks include:

- `../data/processed/storage_der.csv`
- `../data/processed/uswtdb_wind.csv`
- `../data/processed/power_plant_der.csv`
- `../data/processed/ev_chargers.csv`
- `../data/processed/tracking_the_sun.csv`
- `../data/processed/aggregated_TTS.csv`
- `../data/processed/aggregated_ev_cars.csv`
- `../data/processed/aggregated_ev_chargers.csv`
- `../data/processed/aggregated_power_plant.csv`
- `../data/processed/aggregated_storage.csv`
- `../data/processed/aggregated_wind.csv`
- `../data/processed/combined_der_dataset_full.csv`
- `../data/processed/combined_der_dataset_acs_matched.csv`
- `../data/processed/combined_der_dataset_w_controls_predictors.csv`

(`notebooks/processing_energy_data_zip.ipynb`, cells 32-33 and 39; `notebooks/adding_predictor_data.ipynb`, cells 7, 11, 13, 15, 17, and 20)

## 8. End-to-end workflow

The clearest reconstruction of the final workflow is as follows.

First, raw California DER source files were cleaned individually. Storage rows were standardized and filtered to residential/commercial systems at or below a `DER_THRESHOLD` of 5 MW. USWTDB wind turbines were filtered to California and spatially assigned to ZIPs. Power plants were manually corrected, standardized, filtered to California, and split into DER-like behind-the-meter plants versus grid-supply controls. EV chargers were renamed, spatially assigned to ZIPs, and heavily hand-corrected for specific records. EV cars were reduced to ZIP-level counts. Tracking the Sun installations were filtered to California and invalid ZIP strings removed (`notebooks/processing_energy_data_zip.ipynb`, cells 6, 10, 14, 18, 20, and 30).

Second, those source datasets were aggregated to ZIP level. Solar PV became ZIP-level summed `PV_system_size_DC`. Chargers became ZIP-level summed `total_chargers`, `level1_chargers`, `level2_chargers`, and `dc_fast_chargers`. EV cars became ZIP-level `zev_count`. Power plants, storage, and wind were each summed to ZIP-level capacity measures, with wind also retaining `wind_turbine_count` (`notebooks/processing_energy_data_zip.ipynb`, cell 33).

Third, the aggregated datasets were outer-merged into a base panel and written to `combined_der_dataset_full.csv` (`notebooks/processing_energy_data_zip.ipynb`, cells 35-37). A later notebook then generated ACS demographic predictors, NASA POWER climate/resource controls, a ZIP-to-utility crosswalk, and an annual electricity-demand proxy, saving each to processed CSVs (`notebooks/adding_predictor_data.ipynb`, cells 5, 11, 13, 15, 17, and 20). That notebook also writes an ACS-matched subset as `combined_der_dataset_acs_matched.csv` rather than overwriting the base panel. The preprocessing notebook’s final merge stage then left-joined all those controls onto the full base panel, filled certain missing capacity values with zero, assigned each ZIP to a dominant county by overlap, computed `area_km2`, `pop_density_km2`, and `log_pop_density`, filtered out counties with fewer than five ZIPs, and wrote `combined_der_dataset_w_controls_predictors.csv` (`notebooks/processing_energy_data_zip.ipynb`, cell 39).

Fourth, the EDA notebook read the merged dataset and generated missingness plots, histograms, heatmaps, scatterplots, geographic point plots, and ZIP choropleths to inspect distributions and relationships (`notebooks/plotting_data.ipynb`, cells 3-4). This appears to be diagnostic rather than part of the final inferential pipeline.

Fifth, the regression notebook read `combined_der_dataset_w_controls_predictors.csv`, log-transformed selected predictors, filtered out ZIPs with `total_population < 1000`, created per-capita and `log1p`-transformed outcomes, and then fit a staged series of OLS models with robust or clustered standard errors (`notebooks/regression.ipynb`, cells 2-35). Those tables were exported to CSV.

Sixth, the regression notebook also created three additional output families: LOWESS income-response plots, predictive-comparison figures for linear versus nonlinear models, and a full suite of spatial observed-versus-residual maps for each fitted model (`notebooks/regression.ipynb`, cells 36-41).

Finally, the plotting-outcomes notebook gathered the exported regression CSVs into harmonized coefficient tables and generated cross-outcome dot-whisker plots, robustness trajectories, and appendix heatmaps for presentation (`notebooks/plotting_outcomes.ipynb`, cells 1-7).

### Concise step-by-step pipeline summary

1. Clean each raw DER source file at the record level.
2. Normalize ZIP codes and spatially assign point data to ZIP polygons where needed.
3. Filter to California and define which records count as DER versus control infrastructure.
4. Aggregate DER counts and capacities to ZIP-level measures.
5. Merge those aggregates into `combined_der_dataset_full.csv`.
6. Pull ACS, NASA POWER, utility-territory, and demand controls and save them as processed CSVs.
7. Optionally save the ACS-matched subset as `combined_der_dataset_acs_matched.csv`.
8. Merge all controls into the DER panel, assign counties, compute area and density variables, and save `combined_der_dataset_w_controls_predictors.csv`.
9. Transform outcomes to per-capita `log1p` measures and create demographic/resource predictors.
10. Fit staged OLS models with robustness checks, clustered SE variants, and auxiliary predictive comparisons.
11. Export coefficient tables and generate summary figures, LOWESS plots, and spatial residual maps.

## 9. Uncertainties / gaps

Several parts of the notebook set are internally inconsistent or clearly unfinished.

Historically, the biggest file-level inconsistency was that `notebooks/processing_energy_data_zip.ipynb` and `notebooks/adding_predictor_data.ipynb` overlapped in responsibility. `processing_energy_data_zip.ipynb` expected a broad base panel before controls were merged, while `adding_predictor_data.ipynb` was overwriting that same filename after restricting to ACS-matched ZIPs. That created a mismatch where the on-disk `combined_der_dataset.csv` had 1,765 rows while `combined_der_dataset_w_controls_predictors.csv` had 2,572 rows, implying the base artifact on disk no longer matched the one used to produce the final merged panel. This was a real reproducibility problem.

That issue has now been cleaned up in the workspace by separating the artifacts into `combined_der_dataset_full.csv` and `combined_der_dataset_acs_matched.csv`. One caveat remains: because the original pre-overwrite full base file was not preserved, the current `combined_der_dataset_full.csv` was reconstructed from the base columns embedded in `combined_der_dataset_w_controls_predictors.csv`. That reconstruction should be good enough for consistency going forward, but it is still a reconstructed artifact rather than the original historical one.

There is also an explicit filename/dataframe mismatch in `notebooks/processing_energy_data_zip.ipynb` cell 33. `aggregated_datasets` is ordered as `[aggregated_TTS, aggregated_ev_chargers, aggregated_ev_cars, ...]`, but `aggregated_names` is ordered as `["aggregated_TTS", "aggregated_ev_cars", "aggregated_ev_chargers", ...]`. As a result, the file `aggregated_ev_cars.csv` on disk contains charger columns, while `aggregated_ev_chargers.csv` contains `zev_count`. The current processed files confirm that swap. That is not an inference; it is directly supported by both code and file contents.

The notebook `notebooks/processing_energy_data_census.ipynb` looks like an abandoned tract-level branch. Its cells are unexecuted, it does not clearly save outputs, and it stops midstream after beginning a tract-assignment version of the storage and wind processing. I would not treat it as part of the final methodology.

The clustering notebook also appears incomplete as a final deliverable. Its last map cell fails because `analysis_df` and `cluster_z_pca` are not defined (`notebooks/clustering.ipynb`, cell 12 output summary). The notebook labels t-SNE and UMAP as optional, and nothing else in the project appears to depend on the clustering outputs except `gridsearch_results.csv`. I would characterize clustering as exploratory, not final.

The plotting notebooks contain signs of version drift. `plotting_data.ipynb` still references `ghi_mean_kwh_m2_day_2024` and `wind_ws50m_mean_2024` in helper code, and `data/mapping_files/important_plots.ipynb` errors because `median_household_income` is missing from the loaded file. Those are strong signs that the plotting code was written against earlier file versions and not fully synchronized.

The regression notebook’s naming is not always aligned with the actual formulas. In cell 35, the model labeled `"Model 1 baseline (no climate controls)"` is actually built from `controls_cur + core_controls`, so it still includes whichever climate/resource controls are in `controls_cur`. I would trust the formula code over the title string.

Finally, the research question and sample definition are not stated in a single canonical markdown introduction. I can infer the study focus from the code and interpretation text, but the notebooks do not provide one definitive prose description of the paper or project design.

## 10. Reproducibility notes

The project is reproducible in broad structure, but not yet fully reproducible in a strict sense.

The strongest reproducibility elements are that almost every processed dataset is written to disk, the major regression tables are exported as CSVs, and figure-generation code is parameterized and saves outputs into consistent folders. The source file paths are explicit, the transformation code is mostly visible, and the regression formulas are generated programmatically rather than typed ad hoc (`notebooks/processing_energy_data_zip.ipynb`, cells 32-39; `notebooks/adding_predictor_data.ipynb`, cells 5, 11, 13, 15, 17, and 20; `notebooks/regression.ipynb`, cells 2-41).

However, several issues limit exact reproducibility:

- The Census API key is hardcoded in `adding_predictor_data.ipynb` cell 5.
- The ArcGIS and NASA POWER pulls depend on live external services.
- Some charger ZIP assignments and power-plant address/ZIP corrections are hardcoded manually inside notebooks.
- the original historical full base panel was overwritten at some point and had to be reconstructed from the final merged dataset
- The aggregated EV file naming bug means some processed intermediate files are misleadingly named.
- Some notebooks rely on notebook state and execution order rather than clean, restartable top-to-bottom scripts.

### Reproducibility checklist

- Confirm which notebook is the canonical builder of `combined_der_dataset_full.csv`.
- Confirm whether the intended `DER_THRESHOLD` is 5 MW or 10 MW.
- Record the exact raw-file versions and acquisition dates for storage, power plants, chargers, EV stock, and Tracking the Sun.
- Store API query dates and service versions for ACS, NASA POWER, and SCOUT utility territories.
- Move hardcoded API keys out of notebooks.
- Preserve the manual correction lists for charger ZIPs and power-plant rows as versioned reference tables.
- Fix the `aggregated_ev_cars.csv` / `aggregated_ev_chargers.csv` filename swap.
- Keep `combined_der_dataset_full.csv` as the full outer-merged DER panel and `combined_der_dataset_acs_matched.csv` as the restricted subset.
- Add one notebook or script that rebuilds every processed file in a clean order from raw inputs.
- Add a short project-level markdown file that states the sample restrictions, unit of analysis, and final preferred regression specification.

### Questions to answer to improve the methodology description

1. Which notebook should be treated as authoritative when `processing_energy_data_zip.ipynb` and `adding_predictor_data.ipynb` disagree?
2. Was the intended study sample all California ZIPs with any DER data, only ACS-matched ZIPs, or only ZIPs retained after county-size filtering?
3. Is the final DER definition supposed to use `DER_THRESHOLD = 5` or a robustness threshold of 10 MW?
4. Are `power_plant_controls_zip` and `grid_supply_capacity_mw` meant to be merged into the final analysis, or were they exploratory only?
5. Were the manual charger ZIP fixes validated externally, or are they analyst judgments?
6. Are the county-level mapping notebooks part of this project’s methodology, or leftovers from an earlier national data-catalog effort?
7. Was clustering intended for the final paper/report, or only as exploratory segmentation?
8. Which model family should be described as the headline result: Model 1 baseline, clustered-SE models, infrastructure-adjusted models, or demand-adjusted models?
9. Should the predictive-comparison section with Random Forest and XGBoost be documented as a substantive result or as a side diagnostic?
10. Which output folder is canonical for the paper figures: `outputs/figures/`, `outputs/tables/`, or `outputs/standardized_*`?
