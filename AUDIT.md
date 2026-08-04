# Repository audit — DER_data_UROP

Audit date: 2026-08-01. Scope: statistical/methodological validity, data-pipeline
correctness, code quality/reproducibility, repo hygiene and security.

Every finding below was verified by executing code against the actual data in this
repo, not inferred from reading. Reproduction commands are given where useful.

This audit is code- and data-level. It complements `site/review_memo.md`, which is a
manuscript-level review. Where the two overlap it is noted explicitly — in two cases
(§1.3 and §2.1 of that memo) the code-level evidence resolves an open question there.

---

## Severity 1 — affects published results

### 1.1 The housing-structure robustness check silently does nothing

`Model 2C (add housing structure)` is **byte-identical to `Model 1`** for every
outcome. Verified:

```
y_pv:       Model1 == Model2C  ->  True
y_chargers: Model1 == Model2C  ->  True
y_storage:  Model1 == Model2C  ->  True
```

Cause chain:

1. `pct_single_family_units`, `pct_multifamily_units`, `pct_mobile_home_units` are
   **100% NaN** in `data/processed/combined_der_dataset_w_controls_predictors.csv`
   (2552 of 2552 rows).
2. They are NaN because `rebuild_processed_data.py:1020-1026` (the `--skip-external`
   path) *creates the columns filled with `pd.NA`* when they are absent from
   `acs_predictors_ca_zip.csv`, then writes that file back to disk. The live ACS path
   computes them correctly; the skip path fabricates empty ones and persists them.
3. `regression.ipynb` guards with
   `if c in df_model.columns and df_model[c].nunique(dropna=True) > 1`. An all-NaN
   column has `nunique() == 0`, so all three are dropped **silently** and the formula
   collapses to Model 1.

Why this matters most: `site/review_memo.md` §2.1 calls housing structure/tenure
"the highest-value single revision in this memo" and assumes it is absent from the
code. It is not absent — it is implemented, wired into the model ladder, and
silently inert. The exported table `Model 2C (add housing structure).csv` reads as
evidence that the check was run and the race coefficients survived it. They were
never tested.

**Fix:** rerun `rebuild_processed_data.py` with a live Census key so B25024 is
actually pulled, then rerun the notebook. The audit patch below makes the skip path
fail loudly instead of fabricating empty columns, so this cannot recur.

### 1.2 `Model 4` and `Model 4R` are the same regression

The two formulas differ only in how the poverty control is spelled:

- `f4`  hardcodes `"poverty_rate"` (regression.ipynb, cell 6)
- `f4r` uses `list(controls_common)`, and `controls_common = ["poverty_rate"]`

Verified: `y_pv | Model 4 interactions (centered).csv` and
`y_pv | Model 4R interactions (centered).csv` are identical, coefficient for
coefficient. Two rows of the robustness ladder are one model shown twice. Whatever
`4R` was intended to vary (a restricted control set, judging by the name) never got
implemented.

### 1.3 The cluster analysis is largely a missing-data artifact

`clustering.ipynb` reads the **unfiltered** 2,552-row file, applies
`SimpleImputer(strategy='median')`, and clusters. It does not apply the
`min_pop >= 1000` filter or the ACS-completeness filter that the regression sample
uses (N = 1,386). Cross-tabulating the published cluster assignments against
missingness:

| cluster | n | % with no ACS data | % with no geographic match | % in regression sample |
|---|---|---|---|---|
| 0 | 317 | 2.5 | 0.0 | 44.8 |
| **1** | **1142** | **69.0** | **68.0** | **24.5** |
| 2 | 463 | 1.7 | 0.0 | 94.0 |
| 3 | 366 | 2.2 | 0.0 | 79.8 |
| 4 | 264 | 0.4 | 0.0 | 89.8 |

Cluster 1 is the largest cluster (45% of all ZIPs) and is **69% ZIPs that have no
ACS data at all**. Median imputation pushed those rows to the centroid of every
predictor, and k-means duly grouped them. It is a "rows with no data" cluster being
reported as a substantive socio-technical typology. 1,166 of the 2,552 clustered
ZIPs are not in the regression sample.

This resolves `site/review_memo.md` §1.3 (Table 2 N=1,386 vs Table 6 summing to
~2,560): it is the first branch the memo proposed — clustering runs on a different,
pre-filter sample. It is not a stale table. The memo's §1.4 (prose describes k=3,
table shows k=5) is a separate and also real issue.

**Fix required before this figure/table can be published:** cluster on the analysis
sample, or drop rows with missing predictors rather than median-imputing them.
Median-imputing a row where *every* predictor is missing manufactures a data point.

### 1.4 `y_wind_mw` and `y_level1_chargers` are ~98% structural zeros

Zero shares in the analysis sample (N = 1,386):

| outcome | % zero | max |
|---|---|---|
| y_pv | 4.7% | 142.1 |
| y_storage | 5.2% | 8.2 |
| y_chargers | 18.1% | 800 |
| y_level2_chargers | 21.4% | 768 |
| y_dc_fast_chargers | 43.0% | 235 |
| **y_wind_mw** | **97.5%** | 1542.5 |
| **y_level1_chargers** | **97.8%** | 52 |
| plant_capacity_mw *(used as a control)* | 92.1% | 14.5 |

OLS with HC1 errors on `log1p` of a variable that is zero for 97.5% of observations
is fitting a rare-event indicator with a linear model. These two outcomes
nevertheless get the full 18-model ladder, exported tables, and a robustness figure
(`outputs/standardized_figures/y_wind_mw_robustness.png`) presented on equal footing
with `y_pv`. Either model them as a binary (`any_turbines`, which the repo evidently
did at some point — see §3.4) or drop them.

### 1.5 `wind_capacity_mw` is utility-scale, not distributed

`DER_THRESHOLD = 5` MW is applied to storage (`rebuild_processed_data.py:336`) and
to power plants (`:444`), but **not to wind** (`build_wind_zip`, `:370-373`). The
resulting per-ZIP values run to **1,542 MW in a single ZIP** — that is the Tehachapi
wind complex, not a distributed energy resource. 22 of the 42 non-zero ZIPs exceed
the 5 MW DER threshold that the other technologies are held to.

Labelling this "Wind capacity" in a DER paper alongside rooftop PV is a definitional
inconsistency a referee will catch. Either apply the DER threshold for consistency
(which will leave almost nothing) or state plainly that wind is included as
utility-scale context, not as a DER outcome.

### 1.6 Utility fixed effects rest on a 3-utility crosswalk that omits LADWP and SMUD

`data/processed/zip_to_utility.csv` contains exactly three utilities — PG&E (959),
SCE (576), SDG&E (125) — all typed `IOU`. LADWP, SMUD, Imperial Irrigation District
and every other publicly owned utility are absent from
`data/raw/boundaries/ca_utility_territories.geojson`.

Two consequences:

- **Silent sample loss.** `utility` is NaN for 100 of the 1,386 analysis ZIPs, so
  `Model 5 utility FE` (`C(utility)`) drops them without comment. The notebook fills
  `utility_type` with `"POU"` as a guess, but `utility_type` is never used — the FE
  is on `utility`.
- **Misassignment.** The crosswalk assigns each ZIP the utility with the largest area
  overlap, regardless of how small that overlap is. `overlap_share_of_zip` is
  computed and stored but never used as a quality filter. **81 ZIPs are assigned a
  utility covering less than 20% of their area.** ZIP 90008 (Baldwin Hills, mostly
  LADWP) is labelled Southern California Edison on a **9.4%** overlap; 90002 on 34%.

The same gap hits the demand control: `build_demand_controls` reads only PG&E, SCE
and SDG&E files, so `log_kwh` is missing for 12.1% of the analysis sample and 53 of
84 LA-area ZIPs. `Model 8 add demand proxy` therefore drops much of Los Angeles.

**Minimum fix:** report the utility-FE and demand-proxy sample sizes, drop
assignments below a stated overlap threshold, and state in the methods that POU
territories are unobserved.

---

## Severity 2 — pipeline correctness

### 2.1 Coordinate columns are triplicated by a merge collision

`build_final_analysis_dataset` (`:955-959`) merges `ghi`, `temp` and `wind_means`
in sequence on `zip_code`. All three carry `lat` and `lon`. Pandas suffixes the
collisions, producing six coordinate columns in the final dataset:
`lat_x, lon_x, lat_y, lon_y, lat, lon`.

Verified the values are identical (max pairwise difference 0.0 across 1,775 rows),
so `Model 6A lat and lon` — which uses the unsuffixed `lat`/`lon` — is not wrong.
But four junk columns ship in the published analysis file, and the next person to
add a lat/lon-bearing control will get `lat_z` and no warning. Fixed in the patch
below.

### 2.2 Missing counties are treated as a county

`rebuild_processed_data.py:997-1000` runs
`df["county_geoid"].astype(str)` before the `min_n = 5` filter. `astype(str)` turns
NaN into the **string** `"nan"`, which then has a count of 777 — far above the
threshold — so the filter keeps it as if it were a real county.

Result: **777 rows (30.4% of the file) with no ZCTA match at all** survive into
`combined_der_dataset_w_controls_predictors.csv` carrying no county, no area, no
climate data and no NASA controls. `regression.ipynb` cell 5 repeats the same
`astype(str)`, so `Model 6B county fe` estimates a fixed effect for a pseudo-county
named `"nan"`, and `Model 5C`/`No County FE + clustered SEs` cluster all of those
rows together as one group.

The regression's `core_needed` dropna removes them from the estimation sample by
side effect, so published coefficients are not wrong — but the clustering notebook
(§1.3) consumes them directly, and the FE/cluster structure is not what the
methods section describes. Fixed in the patch below.

### 2.3 Row-index fixes can silently invent rows

`POWER_PLANT_FIXES` is applied at `:383-385` with a bare
`power_plant.loc[idx, col] = val`. If a raw-file update shifts row order or shortens
the file, `.loc` on a missing label **creates a new row** rather than raising. The
EV-charger equivalent at `:516-518` is correctly guarded with
`if idx in ev_chargers.index`; the power-plant one is not. Both fix tables are keyed
to positional row numbers in a raw file that is not version-pinned. Guard added in
the patch below; keying on `plant_code` would be the durable fix.

### 2.4 Dead ZIP-exclusion filter in Tracking the Sun

`build_tracking_the_sun` (`:536-539`) calls `clean_zip()` and *then* filters against
`bad = {"-0001", "-01.0", "000.0", "2399.", "831.0"}`. Those are raw, uncleaned
strings — after `clean_zip` they have already become `NA`, `"00000"` or `"00831"`,
so **the set never matches anything**. The filter has never removed a row. Downstream
`is_valid_zip` and `startswith("9")` happen to catch these cases, so nothing is
wrong in the output, but the code documents a data-quality step that does not run.
Fixed in the patch below.

### 2.5 Customer-months are tripled

`annualize_utility` (`:879`) computes `out[f"{util}_cust_months"] = 3 * cust_q_sum`.
The quarterly raw files are **monthly** (verified: PGE Q1 has 7,529 rows across
months 1, 2, 3), and `groupby("zip_code").sum()` has already summed over those
months — so `cust_q_sum` is already customer-months. The `3 *` triples it and
`kwh_per_cust_month` is 1/3 of its true value.

No published result is affected: `build_demand_controls` writes only `zip_code`,
`kwh_annual_total` and `log_kwh` to `demand.csv`. It is a latent bug that will bite
whoever uses the per-customer intensity measure. Fixed in the patch below.

### 2.6 The rebuild script cannot actually rebuild

Two of its inputs were unavailable. One has since been recovered:

- `data/raw/solar/TTS_LBNL_public_file_21-Aug-2024_all.csv` had been deleted from the
  working tree, so `build_tracking_the_sun` was falling back to reading
  `data/processed/tracking_the_sun.csv` — **its own output**. **Resolved:** the file
  was only deleted from the worktree, never from git. Its LFS pointer is intact in
  HEAD and the 1.65 GB object was present in the local LFS cache, so
  `git restore data/raw/solar/TTS_LBNL_public_file_21-Aug-2024_all.csv` recovered it
  byte-for-byte. No re-download was needed and no release-vintage drift was
  introduced. The circular fallback path is no longer being exercised.

  Verified the processed file is a clean derivative, not a corrupted one: raw is
  3,427,100 rows across 27 states; the CA slice is 1,921,220 rows; the processed file
  is 1,893,021 CA rows — i.e. the CA subset less the ~1.5% removed by the ZIP and
  negative-size filters. All 81 raw columns are preserved and `PV_system_size_DC` is
  in identical units (max 12532.24 in both), so repeated round-tripping through the
  fallback path did **not** compound the `/1000` conversion — that division happens on
  a local copy inside `aggregate_sources` and is never written back. The only residue
  is two accumulated index columns (`Unnamed: 0`, `Unnamed: 0.1`) from
  `write_csv(index=True)` round-trips.

  One latent gap remains: `build_tracking_the_sun` applies **no installation-date
  filter**, despite the module docstring stating the rebuild "is intended to be
  2023-aligned". Currently immaterial — the Aug-2024 TTS release has a reporting lag,
  so only 77 of 1.89M CA rows are post-2023 installs (0.004%). But nothing in code
  enforces the alignment, so a newer TTS release would silently contaminate a
  cross-section that is otherwise matched to ACS 2023 and NASA POWER 2023.

- `energy_burden.csv` — the source of `energy_burden_pct` and
  `energy_affordability_gap`, which are 2 of the 9 modelled outcomes — is **only**
  produced by `notebooks/adding_predictor_data.ipynb`. `rebuild_processed_data.py`
  merely reads it (`read_energy_burden`, `:1005-1010`) and warns if absent.

The README calls this a "single script to rebuild processed data in a clean order
from raw inputs". It is not, for these two sources. Either restore the TTS raw file
and fold the energy-burden build into the script, or amend the README.

---

## Severity 3 — reproducibility and code quality

### 3.1 The declared environment does not exist on this machine

`requirements.txt` and `environment.yml` pin `numpy==1.26.4`. The kernel
`regression.ipynb` is configured to use (`myenv` → `/opt/anaconda3/bin/python`) has
**numpy 2.3.5** with pandas, shapely and geopandas compiled against numpy 1.x. Every
import fails:

```
AttributeError: _ARRAY_API not found
ImportError: numpy.core.multiarray failed to import
```

No notebook or script in this repo currently runs on the interpreter the notebooks
point at. This audit had to build a separate venv to verify anything. Nothing in the
repo pins the interpreter — `environment.yml` exists but no environment was created
from it.

### 3.2 About a quarter of the exported tables are orphans

`outputs/tables/` holds 369 model tables and `outputs/standardized_tables/` 372, but
the current notebook produces only 9 outcomes × 18 models. Tables that **no current
code path can generate**:

- an entire outcome family: `any_turbines` (25 tables in each directory)
- model labels from earlier notebook versions: `Model 1 baseline (CDD+HDD)`,
  `Model 1 baseline (no climate controls)`, `Model 8E energy burden extension`,
  `Model 9 + charger control`, `Model 9 + charger + pv control`, `+ pv`,
  `+ chargers`, `+ pv + chargers`, `baseline`,
  `Model 5 utility fe with ders and race predictors`, `Model 9 (predicting burden)`

Roughly 90 stale tables per directory, sitting in the same folder as current results
with no timestamp, no run ID and no way to tell them apart. Anything citing a number
out of `outputs/tables/` risks citing a superseded run. Add a run manifest, or clear
the directory at the start of each run.

### 3.3 No tests

`tests/` exists and is empty. For a pipeline whose correctness rests on ZIP
normalization, spatial joins and seven sequential merges, there is no assertion
anywhere that a merge did not drop rows, that ZIP codes are 5 digits, or that a
column is not entirely NaN. Findings 1.1, 2.1 and 2.2 would each have been caught by
a single assertion.

Highest-value first tests: assert no all-NaN columns in the final dataset; assert
row count is preserved across each left merge; assert `zip_code` matches `^\d{5}$`
everywhere; assert every column named in the model formulas exists and has
`nunique() > 1`.

### 3.4 Duplicated logic

`clean_zip` / `is_valid_zip` and the outcome-construction logic exist in
`rebuild_processed_data.py`, `processing_energy_data_zip.ipynb` and
`adding_predictor_data.ipynb` in parallel copies. `prep_outcomes_per_capita` is
defined in `regression.ipynb` and re-derived in `clustering.ipynb`. The
`DER_ZERO_COLUMNS` list appears in both the script and the notebook. These have
already drifted — the notebook's cell 3 renames `*_2024` columns to `*_2023`, a
compatibility shim for a schema the script no longer emits.

Extract the shared helpers into a `derdata/` package that both the script and the
notebooks import.

### 3.5 Smaller items

- `backend/api/api.py`: `with sqlite3.connect(...)` commits but **does not close**
  the connection — file handles leak on every request. Fixed in the patch below.
- `backend/api/api.py:152` `/compare` with an empty `region_ids` builds `IN ()`,
  a SQL syntax error rather than an empty result.
- `datetime.utcnow()` (deprecated in 3.12) in `generate_summaries.py:369` and
  `populate_tables.py:450`. Fixed in the patch below.
- `regression.ipynb` cell 1: leftover module-level `y = "energy_burden_pct"`, unused.
- `rebuild_processed_data.py:1013-1016`: return type annotates a 7-tuple; the
  function returns 8 values. Fixed in the patch below.
- `write_csv` defaults to `index=True`, so most processed CSVs carry an unnamed
  index column that every reader then has to strip as `Unnamed: 0`.
- `standardize_model_frame` standardizes predictors on the full frame *before*
  statsmodels drops per-model NaN rows, so the standardization base differs from
  each model's estimation sample. Also, the outcome is deliberately left unstandardized,
  which makes "standardized" coefficients semi-standardized — worth stating explicitly
  in the methods.
- `log1p` per-capita scaling is inconsistent across outcomes (per-1k for PV and
  chargers, per-100k for storage and wind). `log1p` is not scale-invariant, so the
  transform is doing something different for each outcome and cross-outcome
  coefficient comparisons in the dot-whisker figure are not on a common footing.
- ~150 regressions are estimated and exported with no multiple-comparison
  adjustment and no pre-registration of the primary specification.

---

## Severity 4 — repo hygiene and security

**Security: clean.** `.env` contains one key (`OPENAI_API_KEY`) and was **never
committed** — `git log --all -- .env` is empty. No hardcoded credentials in any
tracked `.py` or `.ipynb`. `backend/api/api.py` uses parameterized queries
throughout; no SQL injection.

Hygiene issues:

- **`.gitignore` contradicts reality.** It lists `data/` and `outputs/`, but both are
  tracked deliberately via Git LFS (`.gitattributes` has LFS filters for
  `data/raw/**` and `data/processed/*.csv`). The entries do nothing for existing
  files and will silently swallow *new* ones — a newly generated processed CSV would
  never be picked up by `git add`. Fixed in the patch below.
- **7 files tracked that `.gitignore` claims to exclude:** four `.DS_Store`, two
  `.pyc` under `scripts/__pycache__/`, and `site/index.docx.bak` (22 MB). Untracked
  in the patch below.
- **`.git` is 11 GB.** Driven by LFS-tracked large binaries that are also
  *regenerated* on every pipeline run — `data/processed/tracking_the_sun.csv` alone
  is 960 MB and is rewritten by `build_tracking_the_sun` every time. Each rerun
  commits a fresh 960 MB LFS object. Consider not versioning regenerable processed
  outputs.
- **123 uncommitted changes**, including modifications to the final analysis dataset
  and to 60+ result tables. The committed state of the repo does not match the
  outputs on disk, so `git log` cannot tell you which data produced which table.
- **`p.py`** in the repo root is an unrelated LeetCode exercise (merging binary trees
  of bakery cookie orders). It is untracked, so it is not in git history — left in
  place rather than deleted, since deletion would be unrecoverable. Safe to remove.
- `site/` holds three near-identical 18–22 MB `.docx` snapshots
  (`index.docx`, `index.docx.bak`, `index_backup_20260703_151243.docx`). Version
  control already does this job.
- `DER_data_UROP.wiki/` is an empty directory.

---

## What was changed

Applied in this pass (each is a mechanical correctness fix; no model results were
regenerated):

| File | Change |
|---|---|
| `scripts/rebuild_processed_data.py` | Drop `lat`/`lon` from GHI/temp/wind before merging — removes the `lat_x/lat_y/lon_x/lon_y` duplicates (§2.1) |
| `scripts/rebuild_processed_data.py` | County filter no longer treats missing counties as a `"nan"` county (§2.2) |
| `scripts/rebuild_processed_data.py` | `POWER_PLANT_FIXES` guarded so a stale index cannot invent rows (§2.3) |
| `scripts/rebuild_processed_data.py` | Tracking-the-Sun bad-ZIP filter runs before `clean_zip`, so it actually filters (§2.4) |
| `scripts/rebuild_processed_data.py` | Removed the spurious `3 *` in customer-months (§2.5) |
| `scripts/rebuild_processed_data.py` | `--skip-external` now fails loudly instead of fabricating all-NaN housing-structure columns (§1.1 root cause) |
| `scripts/rebuild_processed_data.py` | Corrected the 7-tuple return annotation to 8 |
| `backend/api/api.py` | Connections are now closed; `/compare` rejects an empty `region_ids` (§3.5) |
| `backend/schemas/generate_summaries.py`, `populate_tables.py` | `datetime.utcnow()` → timezone-aware `datetime.now(timezone.utc)` (§3.5) |
| `.gitignore` | Removed the misleading `data/` and `outputs/` entries; added `*.bak` (§4) |
| git index | Untracked 4 `.DS_Store`, 2 `.pyc`, and `site/index.docx.bak` (§4) |
| `data/raw/solar/` | Restored the deleted 1.65 GB raw Tracking the Sun file from local LFS, ending the circular read of the pipeline's own output (§2.6) |

**Deliberately not changed** — these need your judgement, not a patch:

- §1.1 requires a live-Census rerun of the pipeline and then the notebook.
- §1.2 — only you know what `Model 4R` was supposed to restrict.
- §1.3 — whether to cluster on the analysis sample or drop incomplete rows is a
  methods decision.
- §1.4, §1.5 — dropping or reframing outcomes is a paper-level call.
- §1.6 — sourcing POU territories and demand data is new data work.
- §2.6 — folding the energy-burden build into the rebuild script. (The TTS raw file
  *was* restored — see the table above.)
- §3.2 — clearing ~90 stale tables per directory would destroy the only copy of
  results from earlier runs.

---

# Rerun results — 2026-08-02

The pipeline was rebuilt with a live ACS pull and every model refit. Pre-rerun results
are frozen in `outputs/archive/pre-rerun-2026-08-02/`.

Reproduce with:

```bash
CENSUS_API_KEY=... python scripts/run_all.py
```

## Pipeline fixes confirmed in the rebuilt data

| Fix | Before | After |
|---|---|---|
| §1.1 housing-structure columns | 0 non-null | 1,710 non-null; 1,386/1,386 in the analysis sample |
| §2.1 duplicate coordinates | `lat_x, lat_y, lon_x, lon_y` | removed (53 → 49 columns) |
| §2.2 pseudo-county | `"nan"` treated as a county | 777 rows genuinely NA; 56 real counties |
| §2.6 TTS date alignment | no filter | 77 post-2023 installs dropped (1,893,021 → 1,892,944) |

The analysis sample is **unchanged at N = 1,386**, so coefficient movement is
attributable to specification changes rather than a shifting sample.

## New finding: the housing-structure controls were a compositional trap

With Model 2C finally estimating, its first fit returned VIFs of **1258 / 1077 / 199**.
The three housing shares sum to 1 by construction (857 of 1,386 rows sum to exactly
1.0), so entering all three alongside an intercept is a dummy-variable trap and the
individual coefficients were not interpretable. `pct_single_family_units` is now the
omitted reference. **Max VIF in Model 2C is now 3.9.**

## The identification check the review memo asked for

`site/review_memo.md` §2.1 called housing tenure/structure "the highest-value single
revision in this memo". Result, race coefficients from Model 1 → Model 2C:

| Outcome | % Black | % Hispanic | % Asian |
|---|---|---|---|
| Solar PV | −0.049\*\*\* → **−0.024\*\*\*** (−51%) | 0.003 → 0.009 (n.s. both) | −0.082\*\*\* → **−0.050\*\*\*** (−40%) |
| Storage | −0.106\*\*\* → **−0.054\*\*** (−49%) | −0.145\*\*\* → **−0.174\*\*\*** | −0.252\*\*\* → **−0.175\*\*\*** (−31%) |
| EV chargers | −0.001 → −0.036 (n.s. both) | −0.097\*\*\* → **−0.064\*\*** | **0.058\*\* → −0.003 (n.s.)** |

Housing share coefficients (relative to single-family): multifamily is
**−0.106\*\*\*** for PV, **−0.354\*\*\*** for storage, **+0.310\*\*\*** for chargers.

Two things follow:

1. **The headline survives.** Race coefficients for PV and storage remain significant
   at p < 0.001 after housing structure, attenuating 30–50%. Roughly half the raw gap
   is housing composition; the rest is not. The mechanism is visible and sensible —
   you cannot roof-mount PV or site a home battery on a unit you do not control.
2. **The `pct_asian` charger anomaly was a housing artifact.** It was the one
   coefficient that ran opposite to the paper's framing (§2.2 of the memo called it
   "the paper's weakest link"), and it collapses from +0.058\*\* to −0.003 once
   multifamily share is controlled. Chargers track apartment density and commercial
   corridors. This is now demonstrated rather than speculated, and it strengthens the
   charger-composition argument the memo recommends promoting (§2.7).

## Other model changes

- **Model 4R** is now the restricted counterpart it was always named for: it drops
  `poverty_rate`, testing whether the income-by-race interactions survive without the
  collinear poverty control. Exported as
  `Model 4R interactions (centered, no poverty control)` so it cannot be confused with
  the archived tables, where 4R was byte-identical to Model 4.
- **`any_turbines` restored** as a binary presence/absence wind outcome (2.6% base
  rate), the honest specification for what was a 97.5%-zero `y_wind_mw`. It is kept
  off the shared-axis dot-whisker and the heatmap: it is a linear probability model, so
  its coefficients are on a probability scale and cannot share an axis or colour scale
  with the log1p outcomes.
- **Clustering** now runs on the regression sample (1,386, was 2,552). The grid search
  selects **k = 4** (was 5), with sizes 332 / 338 / 478 / 238. The old k=5 solution's
  largest cluster (1,142 ZIPs, 45% of the sample) was 69% rows with no ACS data at all;
  no cluster now exceeds 478. Table 6 and §5.7 of the manuscript must be rewritten
  against this solution.

## Figures

- Background is now controlled by `FIGURE_BG` (`white` default for journals,
  `transparent` for the web) instead of being unconditionally transparent.
- **Every figure now carries a legend.** This was not only cosmetic: the stability and
  ladder plots encode significance as filled vs hollow markers, and the charger panel
  uses a ring, none of which was stated anywhere on the figure.
- Vector **PDF** output added alongside PNG/SVG, with `pdf.fonttype 42` so text stays
  editable for typesetting.
- New figure `housing_structure_attenuation.png` showing the before/after race
  coefficients above — the memo's §2.1 check as a single display item.
- Housing shares were removed from the stability panels (they appear in only one
  specification, so a "stability across specifications" row for them was a single
  point in an empty panel).

## Scripts

- `scripts/run_all.py` — one entrypoint for `data → models → clustering → figures`,
  with `--only`, `--skip-*`, `--full-external`, and a startup check that fails with a
  clear message when `CENSUS_API_KEY` is missing.
- `scripts/run_notebook.py` — generic notebook runner, so clustering is scriptable
  rather than hand-run in Jupyter.
- `rebuild_processed_data.py --reuse-nasa` — pull ACS live while reusing the fixed 2023
  NASA POWER files, cutting a full rebuild from ~75 min to ~15 min with identical
  climate values.
- `build_site_index_assets.py` was drawing its M1 column from
  `"Model 1 baseline (CDD+HDD)"`, an orphaned label no current code produces;
  repointed to `Model 1 baseline (climate controls)`.

## XGBoost restored to the model comparison

`import xgboost` was failing with `XGBoostError` because the macOS OpenMP runtime
(`libomp.dylib`) was absent — pip cannot ship it. `plotting_outcomes.ipynb` caught the
failure with a bare `except: XGBRegressor = None`, so XGBoost was dropped from every
model comparison and the bar simply never appeared. Fixed with `brew install libomp`;
the dependency is now recorded in `requirements.txt` and `environment.yml`, and the
import failure warns loudly instead of vanishing.

Cross-validated R² (5-fold, N = 1,386 except energy burden at 1,370). Full table in
`outputs/standardized_tables/model_comparison_linear_vs_nonlinear.csv`, which did not
previously exist — the numbers lived only inside the PNGs.

| Outcome | Linear | Poly deg 2 | Random Forest | XGBoost |
|---|---|---|---|---|
| Solar PV adoption | 0.174 | 0.221 | 0.281 | **0.355** |
| Storage deployment | 0.265 | 0.243 | 0.304 | **0.354** |
| EV charger availability | 0.176 | 0.160 | 0.183 | **0.194** |
| Energy burden | 0.806 | 0.833 | 0.818 | **0.849** |
| Log affordability gap | 0.311 | 0.320 | 0.337 | **0.348** |
| Wind capacity | **−0.020** | −0.163 | −0.220 | −0.180 |

Two things worth acting on:

**Substantial nonlinearity in PV and storage.** XGBoost roughly doubles the linear R²
for PV (0.174 → 0.355) and adds a third for storage. This does not invalidate the OLS
ladder — it is estimating interpretable conditional associations, not maximising
prediction — but the linear functional form is a choice the paper should defend rather
than assume, and this is cheap evidence for that discussion.

**Wind capacity has negative cross-validated R² under every model.** A negative CV R²
means the models do worse than predicting the sample mean. This is independent
confirmation of §1.4: `y_wind_mw` is 97.5% structural zeros and is not a predictable
outcome at ZIP level. The nonlinear models are *more* negative because they overfit the
handful of non-zero ZIPs. Reporting an 18-model OLS ladder for it is not defensible.

## Possible circularity in the energy-burden outcomes (new, unresolved)

Energy burden's R² of 0.81 from demographic predictors is far above every other
outcome, which prompted a check:

- `corr(energy_burden_pct, log median household income)` = **−0.746**
- `corr(energy_burden_pct, 1 / median household income)` = **+0.734**
- log income **alone** yields R² = **0.556**; race and poverty without income yield 0.451

Energy burden is conventionally defined as annual energy cost divided by household
income. If that holds for this source, then regressing `energy_burden_pct` on
`log_median_household_income` is substantially mechanical — income sits in the
outcome's denominator — and the high R² is partly tautological rather than a finding.

This is flagged rather than fixed, because it depends on the source definition, which
is not documented in the repo. The three metrics are pulled from Tableau CSV exports by
**positional column labels** (`EB.2`, `EA.7`, `EA Gap.3`) in
`adding_predictor_data.ipynb`, so the definitions are not recoverable from the code and
a re-export with different column ordering would silently substitute a different metric.
Confirm the denominator with the data provider before interpreting the energy-burden
coefficients, and record it in `data/raw/SOURCES.md`.

## Output hygiene and figure changes (2026-08-03, later pass)

- **212 orphaned files** moved to `outputs/archive/orphans/` (86 tables, 88 standardized
  tables, 36 individual LOWESS figures, 2 composites). Live directories now contain only
  what current code regenerates. Nothing deleted.
- **Spatial maps**: `RUN_MAPS` is a dead flag and `make_paper_spatial_figure` was never
  called — the maps were unreachable, not merely switched off. The three the site's
  geography panel embeds are now regenerated from current data by
  `scripts/regenerate_site_maps.py`, which verifies its refit against the exported
  Model 1 table (agreement to ~1e-13) so the spec cannot drift. The remaining ~85 stale
  maps carry a README in each directory marking them historical.
- **Model 9 (predicting burden) restored.** `energy_burden_der_m9.png` had been drawn
  from an orphaned table; the specification is now back in `regression.ipynb` and
  reproduces the archived coefficients exactly. Income and poverty are deliberately
  excluded — see the circularity note above.
- **Figures**: overall/figure-level titles removed (captions carry them); per-panel
  category titles kept. PNG only — SVG/PDF output dropped, and 77 vector files removed
  from live `outputs/` (the archive keeps its copies). New figure
  `housing_structure_across_outcomes.png`; the housing shares were removed from the
  robustness panels, where they appeared in only one specification and rendered as a
  single point in an otherwise empty row.
- **Site**: 19 `.svg` references in `paper.html`/`home.html` switched to `.png`, and six
  repo-relative `outputs/standardized_figures/...` paths repointed to
  `./assets/figures/...` so they resolve from a served page.
- Figures that require an absent model now raise `MissingModelError` and are reported
  under a `SKIPPED` heading rather than silently rendering an empty or stale panel.

## Interpreting the housing result: structure and tenure

B25003 (tenure) was added alongside B25024 (units in structure) in a later pass, giving
three specifications to compare:

| | controls added |
|---|---|
| **Model 1** | income, race, poverty, climate |
| **Model 2C** | + housing structure (multifamily, mobile-home; single-family reference) |
| **Model 2D** | + housing structure **and** tenure (owner share; renter reference) |

Owner share only — owner and renter sum to 1, so entering both would repeat the
compositional trap that produced VIFs above 1000 in the first 2C fit. Max VIF is 3.42
(2C) and 5.29–5.42 (2D), comfortably below the conventional threshold of 10.

### Race coefficients

| Outcome | Term | M1 | 2C | 2D |
|---|---|---|---|---|
| Solar PV | % Black | −0.049\*\*\* | −0.024\*\*\* | −0.024\*\*\* |
| Solar PV | % Asian | −0.082\*\*\* | −0.050\*\*\* | −0.051\*\*\* |
| Storage | % Black | −0.106\*\*\* | −0.054\*\* | −0.057\*\* |
| Storage | % Hispanic | −0.145\*\*\* | −0.174\*\*\* | −0.144\*\*\* |
| Storage | % Asian | −0.252\*\*\* | −0.175\*\*\* | −0.171\*\*\* |
| EV Chargers | % Hispanic | −0.097\*\*\* | −0.064\*\* | −0.085\*\*\* |
| EV Chargers | % Asian | +0.058\*\* | −0.003 | −0.007 |

**Tenure adds essentially nothing to the attenuation**: every race coefficient moves
less than 5% between 2C and 2D. Structure had already absorbed the shared variance —
owner share correlates +0.79 with single-family share and −0.83 with multifamily. The
race findings for PV and storage survive the fuller specification unchanged.

### The substantive result: PV and storage are gated by different barriers

Model 2D coefficients:

| Outcome | multifamily | mobile home | owner-occupied |
|---|---|---|---|
| Solar PV | −0.142\*\*\* | 0.016 | **−0.047 (n.s.)** |
| Storage | −0.203\*\*\* | 0.004 | **+0.204\*\*** |
| EV Chargers | +0.208\*\*\* | 0.053\* | **−0.138\*** |
| EV Chargers (L2) | +0.218\*\*\* | 0.047\* | −0.096 |
| EV Chargers (DC fast) | 0.042 | 0.032 | −0.075 |

- **PV is gated by structure, not ownership.** Owner share is null, while multifamily
  *strengthens* from −0.106 (2C) to −0.142\*\*\* (2D) once tenure is held constant —
  suppression. The binding constraint is the shared roof, not the lease.
- **Storage is gated by ownership.** Owner share is +0.204\*\*, and multifamily halves
  from −0.354 to −0.203\*\*\*. Much of "apartments have less storage" was really
  "apartment dwellers rent."
- **Chargers invert on both**, consistent with siting following density.

This supports a policy distinction the manuscript does not currently make: third-party
ownership and financing reforms address the storage constraint but do nothing for a
household with no roof; community solar addresses the structural constraint but not the
tenure one. Two barriers, two interventions.

### Cautions for the write-up

1. **Housing composition is plausibly a mediator, not a confounder.** If segregation and
   housing policy shape who lives in multifamily housing, these variables lie on the
   causal path from race to DER access. Model 1 estimates the **total** disparity and
   2C/2D the **direct** disparity net of housing; the ~50% attenuation at 2C locates a
   mechanism rather than explaining the disparity away. Framing the controlled estimate
   as the more trustworthy one would understate the disparity. Report both and name
   them.
   *Qualification added after the tenure run:* this audit predicted that adding tenure
   would attenuate the race coefficients further, on the reasoning that homeownership is
   heavily racially stratified. It did not — the movement is under 5%. The mediator
   concern still applies to the M1→2C step, which is where the attenuation actually
   happens, but there is no additional tenure-driven attenuation to worry about.
2. **`pct_hispanic` is the unstable term.** It moves non-monotonically across
   specifications (storage −0.145 → −0.174 → −0.144; chargers −0.097 → −0.064 → −0.085)
   and flips sign for PV without ever reaching significance. Report the instability
   rather than the most convenient value.
3. **Ecological inference.** ZIP-level shares cannot establish that Black or Hispanic
   *households* have less PV, only that ZIPs with more Black or Hispanic residents do.
   The housing result sharpens this: within a mixed ZIP the PV may sit entirely on the
   single-family homes, and these data cannot rule that out.

Model 9 (predicting burden) additionally regresses affordability outcomes on the DER
outcomes themselves. Those are downstream of the same demographic predictors, so the
coefficients are descriptive associations and should not be read causally.

## Still open after this rerun

- §1.6 the LADWP/SMUD gap — unchanged, still needs either POU data or an explicit
  statement of the restriction.
- §3.2 the ~90 orphaned tables per directory — now copied into the archive, but the
  live directories still contain them.
- §3.1 the broken conda environment — the repo still does not run on the interpreter
  the notebooks point at. This rerun used a separate pinned venv.
- §3.3 no tests.
- **Cluster count is unstable.** The grid search has selected k = 5, then 4, then 6
  across successive runs as the feature set changed (the last shift came from adding
  tenure). Nothing is wrong with the procedure, but a partition that moves with each
  added control should not carry interpretive weight. Treat the clustering as
  descriptive texture and avoid claims that depend on a specific k.
- Manuscript work in `site/review_memo.md` is untouched: §5.7 needs rewriting against a
  six-cluster solution (it already did not match the five it was written against), and
  Table 2 vs Table 6 now agree at N = 1,386.
- The energy-burden denominator question (see the circularity section) is still
  unresolved and should be confirmed with the data provider.

## Suggested order

Items 1 and 2 of the original list are now **done** (housing structure is real and the
clustering runs on the analysis sample). What remains, in priority order:

1. **Write up the structure/tenure decomposition.** This is the strongest new result and
   it is already computed — PV limited by structure, storage by ownership, with the
   policy implication that follows. Figure:
   `outputs/standardized_figures/housing_structure_across_outcomes.png`.
2. **Fix the mediator framing** wherever the attenuation is discussed. Report total and
   direct disparities as answering different questions.
3. **Decide §1.4 / §1.5** — drop or reframe `y_wind_mw` (negative cross-validated R²
   under every model) and `y_level1_chargers` (97.8% zeros), and settle whether wind
   belongs in a DER paper at all. `any_turbines` is restored as the binary alternative.
4. **Resolve the energy-burden denominator** before interpreting those coefficients.
5. **Document §1.6** — report utility-FE and demand-proxy sample sizes and the POU gap.
6. **Rewrite §5.7** of the manuscript against the current cluster solution, and say
   plainly that k is sensitive to the control set.
7. **Fix §3.1** — build the pinned environment so the repo runs without a separate venv.
8. **Add the four assertions in §3.3** — cheap, and they cover the three worst bugs found.
