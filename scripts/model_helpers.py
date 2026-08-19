"""Shared statistical helpers used by the regression notebook and release tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import patsy
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor


DEFAULT_MIN_CLUSTER_SIZE = 5
PV_KW_PER_MW = 1_000.0
RESIDENTS_PER_THOUSAND = 1_000.0


def pv_kw_per_1000(pv_capacity_mw, population):
    """Convert aggregate PV MW to kW of capacity per 1,000 residents."""
    return (
        pv_capacity_mw
        * PV_KW_PER_MW
        * RESIDENTS_PER_THOUSAND
        / population
    )


def run_ols(
    formula: str,
    df: pd.DataFrame,
    cluster_col: str | None = None,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
):
    """Fit OLS with HC1 errors or county-clustered errors.

    The minimum-size rule applies only to clustered-inference models. Keeping this
    restriction here prevents small counties from being removed from the shared
    release dataset and from specifications that do not use clustered errors.
    """
    model_frame = df
    if cluster_col is not None:
        if cluster_col not in df.columns:
            raise KeyError(f"Cluster column is missing: {cluster_col}")

        _, design = patsy.dmatrices(
            formula,
            df,
            return_type="dataframe",
            NA_action="drop",
        )
        model_frame = df.loc[design.index].copy()
        groups = model_frame[cluster_col].astype("string")
        model_frame = model_frame.loc[groups.notna()].copy()
        groups = model_frame[cluster_col].astype("string")
        group_sizes = groups.value_counts(dropna=True)
        eligible_groups = group_sizes[group_sizes >= min_cluster_size].index
        model_frame = model_frame.loc[groups.isin(eligible_groups)].copy()

        if model_frame.empty:
            raise ValueError(
                f"No rows remain after requiring {min_cluster_size} observations "
                f"per {cluster_col} cluster."
            )
        if model_frame[cluster_col].nunique(dropna=True) < 2:
            raise ValueError("Cluster-robust covariance requires at least two clusters.")

    model = smf.ols(formula=formula, data=model_frame)
    if cluster_col is None:
        return model.fit(cov_type="HC1")

    result = model.fit()
    used_index = result.model.data.row_labels
    groups = model_frame.loc[used_index, cluster_col].astype(str)
    return model.fit(cov_type="cluster", cov_kwds={"groups": groups})


def fit_stats(res) -> dict:
    """Summarize N, degrees of freedom, fit, and covariance type for one OLS result.

    Exported alongside every coefficient table so sample composition and fit quality
    travel with the model, not just the coefficients.
    """
    stats = {
        "nobs": int(res.nobs),
        "df_resid": float(res.df_resid),
        "rsquared": float(res.rsquared),
        "rsquared_adj": float(res.rsquared_adj),
        "cov_type": res.cov_type,
    }
    if res.cov_type == "cluster":
        groups = (res.cov_kwds or {}).get("groups")
        if groups is not None:
            stats["n_clusters"] = int(pd.Series(groups).nunique())
    return stats


def common_sample_index(
    formulas: list[str],
    df: pd.DataFrame,
    cluster_col: str | None = None,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
) -> pd.Index:
    """Intersect the non-missing rows implied by every formula, plus the cluster filter.

    Fitting each rung of a cumulative ladder on its own listwise-deleted sample lets
    coefficient movement across rungs mix control effects with sample composition.
    Fitting every rung on this shared index isolates the control effect.
    """
    common_index: pd.Index | None = None
    for formula in formulas:
        _, design = patsy.dmatrices(
            formula, df, return_type="dataframe", NA_action="drop"
        )
        common_index = (
            design.index if common_index is None else common_index.intersection(design.index)
        )

    if common_index is None or common_index.empty:
        raise ValueError("No rows are common across the provided formulas.")

    if cluster_col is not None:
        if cluster_col not in df.columns:
            raise KeyError(f"Cluster column is missing: {cluster_col}")
        groups = df.loc[common_index, cluster_col].astype("string")
        common_index = common_index[groups.notna().to_numpy()]
        groups = df.loc[common_index, cluster_col].astype("string")
        group_sizes = groups.value_counts(dropna=True)
        eligible_groups = group_sizes[group_sizes >= min_cluster_size].index
        common_index = common_index[groups.isin(eligible_groups).to_numpy()]

    return common_index


def oster_delta(res_restricted, res_full, focal_term: str, rmax_multiplier: float = 1.3) -> float:
    """Oster (2019) delta: how much selection on unobservables (relative to observables)
    would be needed to drive the focal coefficient to zero.

    beta_full = beta_restricted - delta * (beta_restricted - beta_full)
                * (rmax - r2_full) / (r2_full - r2_restricted)   [rearranged for delta=0 case]

    Solving beta*(delta) = 0 for delta gives the formula below. Returns nan rather than
    a misleading number when R^2 does not increase from restricted to full, or when the
    denominator collapses (no observable selection, or r2_full already at rmax).
    """
    beta_restricted = res_restricted.params[focal_term]
    beta_full = res_full.params[focal_term]
    r2_restricted = res_restricted.rsquared
    r2_full = res_full.rsquared
    rmax = min(rmax_multiplier * r2_full, 1.0)

    if r2_full <= r2_restricted:
        return float("nan")

    denominator = (beta_restricted - beta_full) * (rmax - r2_full)
    if np.isclose(denominator, 0.0):
        return float("nan")

    return float(beta_full * (r2_full - r2_restricted) / denominator)


def vif_from_formula(
    formula: str,
    df: pd.DataFrame,
    exclude_prefixes: tuple[str, ...] = ("C(",),
) -> pd.DataFrame:
    """Return predictor VIFs while retaining the intercept in auxiliary fits.

    Dropping the intercept before calculating VIF makes raw, uncentered predictors
    appear highly collinear and causes the raw and standardized exports to disagree.
    The intercept must stay in the design matrix even though it is not itself reported.
    """
    _, design = patsy.dmatrices(formula, df, return_type="dataframe")

    if exclude_prefixes:
        keep = [
            column
            for column in design.columns
            if column == "Intercept"
            or not any(column.startswith(prefix) for prefix in exclude_prefixes)
        ]
        design = design[keep]

    design = design.replace([np.inf, -np.inf], np.nan).dropna()
    report_columns = [column for column in design.columns if column != "Intercept"]
    values = [
        variance_inflation_factor(design.values, design.columns.get_loc(column))
        for column in report_columns
    ]
    return (
        pd.DataFrame({"feature": report_columns, "VIF": values})
        .sort_values("VIF", ascending=False)
        .reset_index(drop=True)
    )
