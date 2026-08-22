#!/usr/bin/env python3
"""Additional analyses for the Nature Sustainability revision.

Reproduces every new number in the revised manuscript and its Supplementary
Information. Additive only: reads the processed dataset and the CEC storage
workbook, writes to ``outputs/nature_revision/``. Nothing in ``regression.ipynb``
or ``outputs/tables`` is touched.

Run from the repository root:

    python scripts/nature_revision_analysis.py

Outputs
-------
zero_shares.csv          share of ZCTAs with zero deployment, by outcome        (B2, J4, Table S17)
storage_by_sector.csv    storage models, all sectors vs residential only        (B4, Table S16)
sd_conversion.csv        predictor means and SDs for interpreting coefficients  (S1, Table S3)
ladder_c1_c5.csv         nested cumulative ladder C1..C5, S, O                  (Table S5, Fig. 2)
spec_curve_counts.csv    n/48 significant and same-signed, from spec_curve.csv  (Table 2)
ppml_negbin.csv          Poisson PML / negative binomial with pop offset        (S3, Table S10)
population_weighted.csv  population-weighted vs unweighted baselines            (S4, Table S11)
spatial_error_model.csv  ML spatial error model, 8-NN weights                   (S6, Table S9)
affordability_outliers.csv  affordability models with and without outliers      (S9, Table S12)

Dependencies beyond the project environment: libpysal, spreg (spatial error model),
openpyxl (storage workbook). The spatial step is skipped with a warning if the
spatial packages are absent.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "scripts"))
from model_helpers import common_sample_index, fit_stats, pv_kw_per_1000, run_ols  # noqa: E402

DATA = ROOT / "data/processed/combined_der_dataset_w_controls_predictors.csv"
STORAGE_XLSX = ROOT / "data/raw/storage/EnergyStorage_Cleaned_August2024_ada.xlsx"
CHARGERS = ROOT / "data/processed/ev_chargers.csv"
SPEC_CURVE = ROOT / "outputs/tables/spec_curve.csv"
OUT = ROOT / "outputs/nature_revision"

# --------------------------------------------------------------------------- spec
INCOME = "log_median_household_income"
RACE = ["pct_black", "pct_hispanic", "pct_asian"]
COMMON = ["poverty_rate"]
FOCAL = [INCOME] + RACE
CLIM_DD = ["cdd65_2023", "hdd65_2023"]
CLIM_GHI = ["ghi_mean_kwh_m2_day_2023"]
CLIM_WIND = ["wind_ws50m_mean_2023"]
SES_BACH = ["pct_bachelors_plus"]
SES_HOUSE = ["log_median_housing_value"]
HOUSING = ["pct_multifamily_units", "pct_mobile_home_units", "pct_other_housing_units"]
TENURE = ["owner_occupied_rate"]
INFRA = ["plant_mw_per_100k", "wind_mw_per_100k_ctrl", "turbines_per_100k", "storage_mw_per_100k"]

HEADLINE = ["y_pv", "y_storage", "y_chargers"]
LADDER_OUTCOMES = HEADLINE + ["y_level2_chargers", "y_dc_fast_chargers"]

# Affordability-gap outlier rule. The per-capita gap has a median near $75 and a
# maximum above $236,000; the CEC source series is the likely origin. $1,000 is
# roughly 13x the median and isolates 134 ZCTAs. Documented in Methods.
GAP_OUTLIER_THRESHOLD = 1_000.0
MIN_POP = 1_000

STANDARDIZE = [
    INCOME, "log_median_housing_value", "poverty_rate", "pct_bachelors_plus",
    "pct_black", "pct_hispanic", "pct_asian", "pct_multifamily_units",
    "pct_mobile_home_units", "pct_other_housing_units", "owner_occupied_rate",
    "cdd65_2023", "hdd65_2023", "t2m_mean_c_2023", "ghi_mean_kwh_m2_day_2023",
    "wind_ws50m_mean_2023", "log_kwh", "plant_mw_per_100k", "storage_mw_per_100k",
    "wind_mw_per_100k_ctrl", "turbines_per_100k",
]

NICE = {
    "y_pv": "Rooftop PV", "y_storage": "Battery storage", "y_chargers": "EV charging",
    "y_level2_chargers": "Level 2 chargers", "y_dc_fast_chargers": "DC fast chargers",
    "energy_burden_pct": "Energy burden", "log_energy_gap_per_capita": "Affordability gap",
    INCOME: "Log income", "pct_black": "Black share",
    "pct_hispanic": "Hispanic share", "pct_asian": "Asian share",
    "poverty_rate": "Poverty rate",
}


def climate_for(outcome: str) -> list[str]:
    """Resource control by outcome.

    Each technology takes the physical suitability measure that governs it. This is a
    modelling choice, not an inconsistency, and is defended in the Methods: holding one
    common resource control across all three would mis-specify at least two of them.
    """
    if outcome == "y_pv":
        return CLIM_GHI
    if outcome in {"y_wind_mw", "any_turbines"}:
        return CLIM_WIND
    if outcome in {"energy_burden_pct", "log_energy_gap_per_capita"}:
        return CLIM_DD + CLIM_GHI
    return CLIM_DD


def prep(df: pd.DataFrame, pop_col: str = "total_population", min_pop: int = MIN_POP) -> pd.DataFrame:
    """Per-capita and log1p outcomes; drop tiny-population ZCTAs.

    Mirrors ``prep_outcomes_per_capita`` in ``notebooks/regression.ipynb``. Kept in
    step with that function deliberately so the additional models here sit on the same
    sample as the published ones.
    """
    df = df.copy()
    df[pop_col] = pd.to_numeric(df[pop_col], errors="coerce")
    zero_fill = [
        "PV_system_size_DC", "total_chargers", "level1_chargers", "level2_chargers",
        "dc_fast_chargers", "zev_count", "plant_capacity_mw", "storage_capacity_mw",
        "wind_capacity_mw", "wind_turbine_count",
    ]
    for col in zero_fill:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df[df[pop_col].notna() & (df[pop_col] >= min_pop)].copy()

    pop = df[pop_col].replace(0, np.nan)
    df["chargers_per_1k"] = df["total_chargers"] * 1_000 / pop
    df["y_chargers"] = np.log1p(df["chargers_per_1k"])
    for level in ("level1", "level2", "dc_fast"):
        df[f"{level}_chargers_per_1k"] = df[f"{level}_chargers"] * 1_000 / pop
        df[f"y_{level}_chargers"] = np.log1p(df[f"{level}_chargers_per_1k"])
    df["pv_kw_per_1k"] = pv_kw_per_1000(df["PV_system_size_DC"], pop)
    df["y_pv"] = np.log1p(df["pv_kw_per_1k"])
    df["storage_mw_per_100k"] = df["storage_capacity_mw"] * 100_000 / pop
    df["y_storage"] = np.log1p(df["storage_mw_per_100k"])
    df["wind_mw_per_100k"] = df["wind_capacity_mw"] * 100_000 / pop
    df["y_wind_mw"] = np.log1p(df["wind_mw_per_100k"])

    df["plant_mw_per_100k"] = df["plant_capacity_mw"] * 100_000 / pop
    df["wind_mw_per_100k_ctrl"] = df["wind_capacity_mw"] * 100_000 / pop
    df["turbines_per_100k"] = df["wind_turbine_count"] * 100_000 / pop

    df[INCOME] = np.log(df["median_household_income"].where(df["median_household_income"] > 0))
    df["log_median_housing_value"] = np.log(df["median_housing_value"].where(df["median_housing_value"] > 0))
    df["energy_burden_pct"] = pd.to_numeric(df["energy_burden_pct"], errors="coerce")
    df["energy_gap_per_capita"] = df["energy_affordability_gap"] / pop
    df["log_energy_gap_per_capita"] = np.log1p(df["energy_gap_per_capita"])

    # county_geoid round-trips through CSV as a float, so a bare astype(str) yields
    # "6037.0" and turns missing counties into a "nan" level that behaves like a real
    # county in C(county_geoid) and in county-clustered SEs.
    def fips5(value):
        return pd.NA if pd.isna(value) else str(int(float(value))).zfill(5)

    county = df["county_geoid"].map(fips5)
    df["county_geoid"] = county.astype(object).where(county.notna(), np.nan)
    return df


def standardize(df: pd.DataFrame, outcome: str, include_outcome: bool = False) -> pd.DataFrame:
    """Z-score predictors (and optionally the outcome) on the frame supplied.

    The project's published ``outputs/standardized_tables`` standardize predictors only
    and leave the outcome on its log(1 + rate) scale, so a coefficient reads as the
    change in the outcome per one predictor standard deviation. ``include_outcome`` is
    used only for the ladder, where cross-outcome comparability matters more.
    """
    out = df.copy()
    cols = set(STANDARDIZE) | ({outcome} if include_outcome else set())
    for col in cols:
        if col in out.columns and pd.api.types.is_numeric_dtype(out[col]):
            sd = out[col].std()
            if sd and sd > 0:
                out[col] = (out[col] - out[col].mean()) / sd
    return out


def core_formula(outcome: str) -> str:
    return f"{outcome} ~ " + " + ".join([INCOME] + RACE + COMMON + climate_for(outcome))


# ------------------------------------------------------------------ 1. zero shares
def zero_shares(df: pd.DataFrame) -> pd.DataFrame:
    """Share of ZCTAs with no deployment, by outcome.

    Level 1 charging is zero in 97.8% of ZCTAs and wind in 97.5%. Neither supports a
    coefficient at this geography; the manuscript reports the zero share instead.
    """
    raw = {
        "y_pv": "PV_system_size_DC", "y_storage": "storage_capacity_mw",
        "y_chargers": "total_chargers", "y_level1_chargers": "level1_chargers",
        "y_level2_chargers": "level2_chargers", "y_dc_fast_chargers": "dc_fast_chargers",
        "y_wind_mw": "wind_capacity_mw",
    }
    rows = []
    for outcome, col in raw.items():
        v = df[col].fillna(0)
        rows.append({
            "outcome": outcome, "raw_var": col, "N": len(v),
            "pct_zero": round(100 * (v <= 0).mean(), 1),
            "median": round(float(v.median()), 3), "mean": round(float(v.mean()), 3),
            "max": round(float(v.max()), 1),
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------- 2. charger provenance (B1)
def charger_provenance() -> dict:
    """Confirm the charging inventory is public/shared-use only.

    The manuscript's charging claims turn on this: if every station row is flagged
    public, residential charging is unobserved and charger counts cannot be read as
    household access. The earlier draft described Level 1 units as "household outlets",
    which this contradicts.
    """
    if not CHARGERS.exists():
        return {}
    d = pd.read_csv(CHARGERS, low_memory=False)
    return {
        "access_type": d["access_type"].value_counts(dropna=False).to_dict(),
        "level1_ports": int(d["level1_chargers"].sum()),
        "level2_ports": int(d["level2_chargers"].sum()),
        "dc_fast_ports": int(d["dc_fast_chargers"].sum()),
        "station_rows": len(d),
    }


# ---------------------------------------------------------- 3. storage sector (B4)
def storage_by_sector(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Re-fit storage on all-sector and residential-only capacity.

    The CEC survey covers utility-scale alongside customer-sited systems, and the whole
    resilience argument only holds for behind-the-meter capacity. Rebuilding the ZCTA
    aggregate from the raw workbook with and without the non-residential records shows
    whether the distinction changes anything.
    """
    if not STORAGE_XLSX.exists():
        print("  ! storage workbook not found; skipping")
        return pd.DataFrame(), {}
    x = pd.read_excel(STORAGE_XLSX)
    x.columns = [c.strip() for c in x.columns]
    sectors = x["Customer Sector"].value_counts(dropna=False).to_dict()
    x["zip"] = pd.to_numeric(x["Facility Zip"], errors="coerce")
    kw = "Nameplate Capacity (in KW AC)"
    all_mw = x.groupby("zip")[kw].sum() / 1_000.0
    res = x[x["Customer Sector"].astype(str).str.strip().eq("Residential")]
    res_mw = res.groupby("zip")[kw].sum() / 1_000.0

    d = df.copy()
    d["zip"] = pd.to_numeric(d["zip_code"], errors="coerce")
    d["stor_all"] = d["zip"].map(all_mw).fillna(0)
    d["stor_res"] = d["zip"].map(res_mw).fillna(0)

    rows = []
    for col, label in [("stor_all", "all sectors"), ("stor_res", "residential only")]:
        y = f"y_{col}"
        d[y] = np.log1p(d[col] * 100_000 / d["total_population"])
        cols = [y, INCOME] + RACE + COMMON + climate_for("y_storage")
        sub = standardize(d.dropna(subset=cols).copy(), y)
        m = smf.ols(f"{y} ~ " + " + ".join([INCOME] + RACE + COMMON + climate_for("y_storage")),
                    data=sub).fit(cov_type="HC1")
        for term in FOCAL + COMMON:
            rows.append({"sample": label, "term": term, "coef": m.params[term],
                         "se": m.bse[term], "p": m.pvalues[term],
                         "N": int(m.nobs), "R2": m.rsquared})
    meta = {
        "sector_counts": sectors,
        "corr_with_processed": float(d[["storage_capacity_mw", "stor_res"]].corr().iloc[0, 1]),
    }
    return pd.DataFrame(rows), meta


# ---------------------------------------------------------------- 4. C1..C5 ladder
def ladder_formulas(outcome: str) -> dict[str, str]:
    """Nested cumulative ladder. Each rung is a strict superset of the last.

    County and utility fixed effects are not stacked with the ZCTA climate control:
    county fixed effects very nearly absorb it, so C5 drops climate. Mediators
    (electricity demand, installed infrastructure) enter only model O, which is a
    conservative lower bound rather than a headline estimate.
    """
    clim = climate_for(outcome)
    core = [INCOME] + RACE + COMMON + clim
    f = {"C1": f"{outcome} ~ " + " + ".join(core)}
    f["C2"] = f["C1"] + " + " + " + ".join(SES_BACH + SES_HOUSE)
    f["C3"] = f["C2"] + " + " + " + ".join(HOUSING + TENURE)
    f["C4"] = f["C3"] + " + C(utility)"
    base5 = [INCOME] + RACE + COMMON + SES_BACH + SES_HOUSE + HOUSING + TENURE
    f["C5"] = f"{outcome} ~ " + " + ".join(base5) + " + C(utility) + C(county_geoid)"
    infra = [c for c in INFRA if not (outcome == "y_storage" and c == "storage_mw_per_100k")]
    f["O"] = f["C5"] + " + log_kwh + " + " + ".join(infra)
    return f


def run_ladder(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome in LADDER_OUTCOMES:
        formulas = ladder_formulas(outcome)
        idx = common_sample_index(list(formulas.values()), df, cluster_col="county_geoid")
        frame = standardize(df.loc[idx].copy(), outcome, include_outcome=True)
        for rung, formula in formulas.items():
            cluster = "county_geoid" if rung in ("C5", "O") else None
            res = run_ols(formula, frame, cluster_col=cluster)
            stats = fit_stats(res)
            for term in FOCAL:
                if term in res.params.index:
                    rows.append({
                        "outcome": outcome, "rung": rung, "term": term,
                        "beta": res.params[term], "se": res.bse[term], "p": res.pvalues[term],
                        "N": stats["nobs"], "R2": stats["rsquared"],
                        "clusters": stats.get("n_clusters"),
                    })
    return pd.DataFrame(rows)


# ------------------------------------------------------------- 5. spec-curve counts
def spec_curve_counts() -> pd.DataFrame:
    """How often each focal coefficient is significant and same-signed as its median.

    Summarises the 48 confounder-block combinations already written by the robustness
    notebook. A low count means the headline table rests on which blocks happened to be
    included: aggregate charging is 0/48 on Black share.
    """
    if not SPEC_CURVE.exists():
        print("  ! spec_curve.csv not found; run the robustness notebook first")
        return pd.DataFrame()
    spec = pd.read_csv(SPEC_CURVE)
    rows = []
    for (outcome, term), g in spec.groupby(["outcome", "term"]):
        median_sign = np.sign(g["coef"].median())
        n_sig = int(((g["pval"] < 0.05) & (np.sign(g["coef"]) == median_sign)).sum())
        rows.append({"outcome": outcome, "term": term, "n_sig": n_sig, "n_total": len(g)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 6. count models
def count_models(df: pd.DataFrame) -> pd.DataFrame:
    """Poisson PML and negative binomial on raw counts with a population offset.

    OLS on log(1 + rate) with zero-inflated counts is the most predictable objection to
    this design. Fitting the counts directly handles the zeros without a transformation;
    agreement on sign and significance closes the objection.
    """
    rows = []
    targets = [
        ("total_chargers", "chargers (aggregate)", "y_chargers"),
        ("level2_chargers", "Level 2 chargers", "y_chargers"),
        ("dc_fast_chargers", "DC fast chargers", "y_chargers"),
        ("storage_capacity_mw", "storage MW", "y_storage"),
        ("PV_system_size_DC", "PV capacity", "y_pv"),
    ]
    for col, label, clim_like in targets:
        clim = climate_for(clim_like)
        need = [INCOME] + RACE + COMMON + clim + [col, "total_population"]
        d = df.dropna(subset=need).copy()
        rhs = " + ".join([INCOME] + RACE + COMMON + clim)
        offset = np.log(d["total_population"])
        families = [("PPML", sm.families.Poisson())]
        # Negative binomial needs a dispersion parameter; alpha=1 is the standard
        # starting point and is only used as a corroborating fit, never quoted alone.
        families.append(("NegBin", sm.families.NegativeBinomial(alpha=1.0)))
        for name, family in families:
            try:
                m = smf.glm(f"{col} ~ {rhs}", data=d, family=family, offset=offset).fit(cov_type="HC1")
            except Exception as exc:  # pragma: no cover
                print(f"  ! {name} failed for {label}: {exc}")
                continue
            for term in FOCAL:
                rows.append({"model": name, "outcome": label, "term": term,
                             "coef": m.params[term], "se": m.bse[term],
                             "p": m.pvalues[term], "N": int(m.nobs)})
    return pd.DataFrame(rows)


# ----------------------------------------------------------- 7. population weighting
def population_weighted(df: pd.DataFrame) -> pd.DataFrame:
    """Unweighted vs population-weighted baselines.

    The population floor is 1,000, so unweighted regressions give a 1,100-person ZCTA
    the same leverage as a 90,000-person one.
    """
    rows = []
    for outcome in HEADLINE:
        cols = [outcome, INCOME] + RACE + COMMON + climate_for(outcome) + ["total_population"]
        d = standardize(df.dropna(subset=cols).copy(), outcome)
        unweighted = smf.ols(core_formula(outcome), data=d).fit(cov_type="HC1")
        weighted = smf.wls(core_formula(outcome), data=d,
                           weights=d["total_population"]).fit(cov_type="HC1")
        for term in FOCAL:
            rows.append({
                "outcome": outcome, "term": term,
                "beta_unweighted": unweighted.params[term], "p_unw": unweighted.pvalues[term],
                "beta_weighted": weighted.params[term], "p_w": weighted.pvalues[term],
                "N": int(unweighted.nobs),
            })
    return pd.DataFrame(rows)


# ------------------------------------------------------------ 8. spatial error model
def spatial_error(df: pd.DataFrame) -> pd.DataFrame:
    """Maximum-likelihood spatial error model, eight-nearest-neighbour weights.

    Conley HAC corrects inference for spatial dependence but leaves the conditional mean
    alone, so spatially structured omitted variables — installer density, permitting
    regimes, local programme administration — still bias the coefficients. The SEM puts
    the dependence in the model instead. It reproduces the C5 ranking from a different
    direction, which is why it is reported in the main text rather than the SI alone.
    """
    try:
        from libpysal.weights import KNN
        from scipy.stats import norm
        from spreg import ML_Error
    except ImportError:
        print("  ! libpysal/spreg not installed; skipping spatial error model")
        return pd.DataFrame()

    rows = []
    for outcome in HEADLINE:
        clim = climate_for(outcome)
        cols = [outcome, INCOME] + RACE + COMMON + clim + ["lat", "lon"]
        d = standardize(df.dropna(subset=cols).copy(), outcome, include_outcome=True)
        w = KNN.from_array(d[["lon", "lat"]].values, k=8)
        w.transform = "r"
        names = [INCOME] + RACE + COMMON + clim
        try:
            m = ML_Error(d[[outcome]].values, d[names].values, w=w, name_x=names, name_y=outcome)
        except Exception as exc:  # pragma: no cover
            print(f"  ! SEM failed for {outcome}: {exc}")
            continue
        for i, term in enumerate(names):
            if term not in FOCAL:
                continue
            beta = float(m.betas[i + 1][0])
            se = float(np.sqrt(m.vm[i + 1, i + 1]))
            rows.append({"outcome": outcome, "term": term, "beta_SEM": beta, "se_SEM": se,
                         "p_SEM": 2 * (1 - norm.cdf(abs(beta / se))),
                         "lambda_": float(m.betas[-1][0]), "N": len(d)})
    return pd.DataFrame(rows)


# ---------------------------------------------------- 9. affordability-gap outliers
def affordability_outliers(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Affordability models with and without the extreme per-capita gap ZCTAs.

    The per-capita gap runs from a median near $75 to a maximum above $236,000, and the
    top 100 ZCTAs hold 92% of the statewide total — a source-data artefact rather than
    real variation. Excluding them removes a previously reported finding: the positive
    Asian-share association with the gap does not survive.
    """
    gap = df["energy_gap_per_capita"]
    diagnostics = {
        "n_nonmissing": int(gap.notna().sum()),
        "median": float(gap.median()),
        "p99": float(gap.quantile(0.99)),
        "max": float(gap.max()),
        "n_above_threshold": int((gap > GAP_OUTLIER_THRESHOLD).sum()),
        "threshold": GAP_OUTLIER_THRESHOLD,
    }
    ranked = df["energy_affordability_gap"].dropna().sort_values(ascending=False)
    diagnostics["top100_share_of_total"] = float(ranked.head(100).sum() / ranked.sum())

    df = df.copy()
    df["_gap_outlier"] = (gap > GAP_OUTLIER_THRESHOLD).fillna(False)
    rows = []
    for outcome in ["energy_burden_pct", "log_energy_gap_per_capita"]:
        clim = climate_for(outcome)
        for label, subset in [("full sample", df), ("excl. gap outliers", df[~df["_gap_outlier"]])]:
            cols = [outcome, INCOME] + RACE + COMMON + clim
            d = standardize(subset.dropna(subset=cols).copy(), outcome)
            m = smf.ols(f"{outcome} ~ " + " + ".join([INCOME] + RACE + COMMON + clim),
                        data=d).fit(cov_type="HC1")
            for term in FOCAL:
                rows.append({"outcome": outcome, "sample": label, "term": term,
                             "beta": m.params[term], "p": m.pvalues[term],
                             "N": int(m.nobs), "R2": m.rsquared})
    return pd.DataFrame(rows), diagnostics


# ------------------------------------------------------------ 10. SD conversion aid
def sd_conversion(df: pd.DataFrame) -> pd.DataFrame:
    """Predictor means and SDs, so a standardised coefficient can be read in points."""
    sd = pd.DataFrame({
        "predictor": FOCAL,
        "mean": [df[c].mean() for c in FOCAL],
        "sd": [df[c].std() for c in FOCAL],
    })
    sd["one_sd_in_pp"] = np.where(sd["predictor"] == INCOME, np.nan, sd["sd"] * 100)
    return sd


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"reading {DATA.relative_to(ROOT)}")
    df = prep(pd.read_csv(DATA, low_memory=False))
    print(f"  analysis sample: {len(df)} ZCTAs (population >= {MIN_POP:,})\n")

    def write(name: str, frame: pd.DataFrame) -> None:
        if frame.empty:
            print(f"  - {name}: skipped")
            return
        frame.to_csv(OUT / name, index=False)
        print(f"  + {name} ({len(frame)} rows)")

    print("1. zero shares")
    zs = zero_shares(df)
    write("zero_shares.csv", zs)
    print(zs[["outcome", "pct_zero"]].to_string(index=False))

    print("\n2. charger provenance (B1)")
    prov = charger_provenance()
    if prov:
        print(f"   access_type: {prov['access_type']}")
        print(f"   ports: L1 {prov['level1_ports']:,} | L2 {prov['level2_ports']:,} "
              f"| DCFC {prov['dc_fast_ports']:,} across {prov['station_rows']:,} rows")

    print("\n3. storage by customer sector (B4)")
    sector, meta = storage_by_sector(df)
    write("storage_by_sector.csv", sector)
    if meta:
        print(f"   sectors: {meta['sector_counts']}")
        print(f"   residential-only reconstruction vs processed column: "
              f"r = {meta['corr_with_processed']:.3f}")

    print("\n4. SD conversion")
    write("sd_conversion.csv", sd_conversion(df))

    print("\n5. nested cumulative ladder C1..C5")
    ladder = run_ladder(df)
    write("ladder_c1_c5.csv", ladder)
    if not ladder.empty:
        c5 = ladder[(ladder.rung == "C5") & (ladder.outcome.isin(HEADLINE)) & (ladder.term != INCOME)]
        for r in c5.itertuples():
            flag = "survives" if r.p < 0.05 else "not significant"
            print(f"   {NICE[r.outcome]:<16} {NICE[r.term]:<15} "
                  f"beta={r.beta:+.3f} p={r.p:.3f}  {flag}")

    print("\n6. specification-curve counts")
    write("spec_curve_counts.csv", spec_curve_counts())

    print("\n7. count models (PPML / negative binomial)")
    write("ppml_negbin.csv", count_models(df))

    print("\n8. population weighting")
    write("population_weighted.csv", population_weighted(df))

    print("\n9. spatial error model")
    sem = spatial_error(df)
    write("spatial_error_model.csv", sem)
    if not sem.empty:
        for outcome, g in sem.groupby("outcome"):
            print(f"   {NICE[outcome]:<16} lambda={g['lambda_'].iloc[0]:.2f}")

    print("\n10. affordability-gap outliers")
    aff, diag = affordability_outliers(df)
    write("affordability_outliers.csv", aff)
    print(f"   per-capita gap: median ${diag['median']:,.0f}, max ${diag['max']:,.0f}; "
          f"{diag['n_above_threshold']} ZCTAs above ${diag['threshold']:,.0f}; "
          f"top 100 hold {diag['top100_share_of_total']:.1%} of the total")

    print(f"\ndone -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
