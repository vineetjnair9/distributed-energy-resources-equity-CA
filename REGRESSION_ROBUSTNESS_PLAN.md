# Implementation plan: nested control ladder, saturated model, spec curve, Oster bounds

**Repo:** `distributed-energy-resources-equity-CA` · branch `main`
**Status:** approved plan, not yet implemented. Written for a fresh session — no prior
conversation context required.

---

## 1. Context: what the code actually does today

The paper presents its regressions as a "model ladder" that becomes more rigorous from
left to right. **The code does not implement a ladder.** Every specification in
`notebooks/regression.ipynb` (`run_outcome_suite`, ~line 636) is built off one fixed
core via `build_formula` (~line 396):

```
y ~ log_median_household_income + pct_black + pct_hispanic + pct_asian
    + poverty_rate + <outcome-specific climate control>
```

and then varies **exactly one block**. The existing models are siblings, not rungs:

| Model | Deviation from the core |
|---|---|
| M1 | core |
| M2 / M2C / M2D | + bachelors *or* + housing value *or* + structure shares *or* + structure & tenure (mutually exclusive arms) |
| M3A / M3B / M3C | climate control **swapped** (HDD+CDD / temp / GHI) — adds nothing to M1 |
| M4 / M4R | + centered income×race interactions; **4R drops** `poverty_rate` |
| M5 / M5C | + utility FE; 5C = same formula with county-clustered SEs |
| M6A / M6B | climate **dropped**, replaced by lat+lon or county FE |
| M7 / M7pc | + infrastructure capacity (levels / per-capita) |
| M8 | + `log_kwh` demand proxy |
| M9 | the only stacked model — and only for `y_storage` |

The non-nesting is most visible in `build_coefficient_path`
(`scripts/build_site_index_assets.py:352`), which plots M1→M8 as a left-to-right
coefficient path, and in `PAPER_ROBUSTNESS_MODELS`
(`scripts/regenerate_standardized_figures.py:40`).

### Three consequences

1. **Framing risk.** A referee who checks nesting finds none; the "increasingly
   rigorous" claim fails outright at M3 (a swap) and M6 (a removal).
2. **No joint test.** One-at-a-time blocks cannot detect that education + housing value
   + tenure *jointly* absorb an income or race effect that none kills alone. Nine of ten
   outcomes have no all-controls specification.
3. **Sample drift is invisible.** `export_result_table` writes
   `res.summary2().tables[1]` only — coefficients, no N, no R². Blocks differ in
   missingness, M4/M4R fit on `df_int`, and M5C drops counties with fewer than 5 ZIPs
   (`DEFAULT_MIN_CLUSTER_SIZE`, `scripts/model_helpers.py:13`). Coefficient movement
   across the ladder therefore mixes control effects with sample composition, and
   nothing in the exported CSVs lets a reader separate the two.

### Intended outcome

Keep the existing block-sensitivity fan — it is the more informative design for "which
control absorbs what" — relabel it honestly, and add alongside it: a genuinely nested
cumulative ladder on a frozen sample, a saturated confounders-only model per outcome, an
explicitly over-controlled mediator model as a lower bound, a specification curve over
all block combinations, and Oster (2019) δ bounds on the headline coefficients.

---

## 2. Design decisions (do not silently deviate)

**Confounders vs mediators.** The saturated model must not be a kitchen sink. `log_kwh`
(demand proxy, M8) and the infrastructure capacity blocks (M7, M7pc) sit on the causal
path from income/race to DER adoption — conditioning on them estimates a direct effect,
not the total effect the paper reports. They go into a *separate* over-controlled model
framed as a conservative lower bound, never into the headline saturated column.

**Climate vs county FE.** County FE (58 CA counties) very nearly absorbs ZIP-level
climate. The top cumulative rung uses county FE and drops the climate control, with
county-clustered SEs; the rung below keeps climate + utility FE. Do not stack county FE,
utility FE, and climate in one design matrix.

**Frozen sample.** All cumulative rungs fit on the intersection sample — rows non-missing
on every variable used anywhere in the ladder, plus the `min_cluster_size` county filter
so the clustered rung shares it. Movement across rungs then reflects controls only.

**Interactions stay out** of the cumulative ladder; M4/M4R remain their own arm.

---

## 3. Changes

### 3.1 `scripts/model_helpers.py` — new helpers (unit-tested)

- `fit_stats(res) -> dict`: `nobs`, `df_resid`, `rsquared`, `rsquared_adj`, `cov_type`,
  and `n_clusters` when clustered.
- `common_sample_index(formulas, df, cluster_col=None, min_cluster_size=DEFAULT_MIN_CLUSTER_SIZE) -> pd.Index`:
  intersect `patsy.dmatrices(..., NA_action="drop")` row indices across every formula,
  then apply the same cluster-size filter `run_ols` uses. Reuse the existing patsy path
  inside `run_ols` rather than reimplementing NA handling.
- `oster_delta(res_restricted, res_full, focal_term, rmax_multiplier=1.3) -> float`:
  Oster (2019) δ for β = 0, with `rmax = min(rmax_multiplier * res_full.rsquared, 1.0)`.
  Return `nan` when R² is non-increasing or the denominator collapses — do not emit a
  misleading number.

### 3.2 `notebooks/regression.ipynb` — block registry and new specifications

Add near the existing control-set definitions (~line 310), reusing `ses_bach`,
`ses_house`, `housing_structure`, `tenure`, `utility_fe`, `county_fe`, `infra*`,
`demand_proxy`:

```python
CONFOUNDER_BLOCKS = {           # pre-treatment / non-mediating
    "education": ses_bach,
    "housing_value": ses_house,
    "housing_structure": housing_structure,
    "tenure": tenure,
    "utility_fe": [utility_fe],
    "county_fe": [county_fe],
}
MEDIATOR_BLOCKS = {"demand": [demand_proxy], "infrastructure": <infra, outcome-safe>}
```

Inside `run_outcome_suite`, after the existing M1–M9 block, add:

| Label | RHS |
|---|---|
| `Model C1 (core, common sample)` | core |
| `Model C2 (+ education, housing value)` | C1 + bachelors + housing value |
| `Model C3 (+ housing structure, tenure)` | C2 + structure shares + owner share |
| `Model C4 (+ utility FE)` | C3 + `C(utility)` |
| `Model C5 (+ county FE, county-clustered SEs)` | C4 minus climate, plus `C(county_geoid)`, `cluster_col="county_geoid"` |
| `Model S (saturated confounders)` | = C5 |
| `Model O (over-controlled: + demand and infrastructure)` | C5 + `MEDIATOR_BLOCKS` |

All seven fit on `df_model.loc[common_sample_index([...])]`. Reuse `store_result` and
`export_vif_table` so the coefficient tables, the VIF exports, and
`model_outputs_by_region.csv` pick them up automatically. Keep the
`"{outcome} | {label}"` filename convention — downstream `load_coef` in
`build_site_index_assets.py` matches on it.

Also amend `export_result_table` to append `fit_stats` as trailing rows (or as a
companion `... fit stats.csv`) so N and R² travel with **every** model, old and new.
Confirm `backend/schemas/populate_tables.py` tolerates the extra rows before choosing
which form.

### 3.3 Specification curve (SI)

New cell after the suite, gated by
`RUN_SPEC_CURVE = os.environ.get("RUN_SPEC_CURVE", "1") == "1"`: enumerate all 2⁶ = 64
subsets of `CONFOUNDER_BLOCKS`, fit each on the frozen sample, and write only the focal
terms (`log_median_household_income`, `pct_black`, `pct_hispanic`, `pct_asian`) to
`outputs/tables/spec_curve.csv` with columns
`outcome, blocks, term, coef, se, pval, nobs, rsquared`. 64 × 10 outcomes = 640 fits;
run raw mode only (skip `standardized_flag=True`) to keep it to a few minutes. Drop
`county_fe` + `utility_fe` co-occurrence, and force climate off whenever `county_fe` is
on, per §2.

### 3.4 Oster δ

After the ladder, compute `oster_delta(res_C1, res_S, term)` for each focal term and
each outcome; write `outputs/tables/oster_delta.csv` with
`outcome, term, beta_restricted, beta_full, r2_restricted, r2_full, rmax, delta`.

### 3.5 Figures and framing

- `scripts/regenerate_standardized_figures.py:40` — add the C1–C5 rungs to
  `PAPER_ROBUSTNESS_MODELS` (or a new `PAPER_LADDER_MODELS` used by a dedicated panel),
  keeping the existing sibling arms in a separate "control-block sensitivity" panel.
- `scripts/build_site_index_assets.py:352` — `build_coefficient_path`'s `model_map`
  currently orders M1→M8 as if nested. Repoint it at C1–C5 so the left-to-right reading
  is true, and move M3B / M6B into the sensitivity panel.
- New SI figure: the spec curve (sorted coefficient with CI, block-membership matrix
  below), drawn with `apply_paper_style` from `scripts/paper_figure_utils.py`.
- Prose (README and manuscript): call the sibling arms "control-block sensitivity
  analyses," reserve the word "ladder" for C1–C5, and state explicitly that Model O is
  over-controlled and bounds the effect from below.

### 3.6 Tests — `tests/test_model_helpers.py`

- `oster_delta` recovers a known δ on synthetic data with a planted omitted variable,
  and returns `nan` when R² does not increase.
- `common_sample_index` returns the intersection under injected NaNs and honors
  `min_cluster_size`.
- `fit_stats` reports `n_clusters` on a clustered fit and omits it otherwise.

---

## 4. Verification

```bash
python -m pytest tests/test_model_helpers.py -q
```

```bash
python scripts/run_all.py --skip-data --only models --outcomes y_pv y_storage
```

Then check:

1. `outputs/tables/` contains `y_pv | Model C1 … C5`, `Model S`, `Model O` plus their
   VIF companions, and every model's table now carries N and R².
2. **All C-rungs report identical `nobs`** — that is the frozen-sample invariant. If they
   differ, `common_sample_index` is not being applied.
3. `Model C5` reports `cov_type = cluster` with a plausible county count (≤ 58).
4. VIF for `Model S` — flag any focal term above ~10 in the manuscript text, since
   inflated SEs there mean non-significance is not evidence of no effect.
5. `outputs/tables/spec_curve.csv` has 64 rows per outcome per focal term; the share of
   specifications with the focal coefficient significant and same-signed is the number
   to quote in the paper.
6. `outputs/tables/oster_delta.csv` — δ > 1 for the headline income/race coefficients is
   the reportable result.
7. `python scripts/run_all.py --skip-data --only figures`, then visually confirm the
   coefficient-path panel's rungs are now genuinely nested.

Note: `data/processed/` is not version-controlled. If it is absent, run the data stage
first (`CENSUS_API_KEY=... python scripts/run_all.py --only data`) or use
`--skip-data` against an existing build.
