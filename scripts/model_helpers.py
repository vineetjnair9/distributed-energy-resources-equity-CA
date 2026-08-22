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


def _n_clusters(res) -> int | None:
    """Number of clusters behind a cluster-robust covariance, or None if not clustered."""
    if getattr(res, "cov_type", None) != "cluster":
        return None
    cov_kwds = getattr(res, "cov_kwds", None) or {}
    n_groups = getattr(res, "n_groups", None)
    if n_groups is None:
        n_groups = cov_kwds.get("n_groups")
    if n_groups is None:
        groups = cov_kwds.get("groups")
        if groups is None:
            return None
        return int(pd.Series(np.asarray(groups).ravel()).nunique())
    # Multiway clustering reports one count per grouping dimension; the first is the
    # one this project uses (single-dimension county clusters).
    return int(np.asarray(n_groups).ravel()[0])


def fit_stats(res) -> dict:
    """Sample size and fit summary for a statsmodels result.

    ``summary2().tables[1]`` carries coefficients only, so exported tables cannot tell
    a reader whether a coefficient moved because a control was added or because the
    estimation sample changed. These are the numbers that separate the two.
    """
    stats = {
        "nobs": int(res.nobs),
        "df_resid": int(res.df_resid),
        "rsquared": float(res.rsquared),
        "rsquared_adj": float(res.rsquared_adj),
        "cov_type": str(getattr(res, "cov_type", "nonrobust")),
    }
    n_clusters = _n_clusters(res)
    if n_clusters is not None:
        stats["n_clusters"] = n_clusters
    return stats


def common_sample_index(
    formulas,
    df: pd.DataFrame,
    cluster_col: str | None = None,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
) -> pd.Index:
    """Rows usable by every one of ``formulas``, for fitting a nested ladder.

    Control blocks differ in missingness, so a cumulative ladder fitted naively loses
    observations as it climbs and coefficient movement then mixes control effects with
    sample composition. Intersecting the patsy-droppable row sets up front freezes the
    sample across every rung.

    ``cluster_col`` applies the same minimum-cluster-size rule ``run_ols`` uses, so a
    clustered rung shares the frozen sample rather than silently dropping small
    counties out from under the rungs below it.
    """
    if isinstance(formulas, str):
        formulas = [formulas]
    formulas = list(formulas)
    if not formulas:
        raise ValueError("common_sample_index requires at least one formula.")

    index: pd.Index | None = None
    for formula in formulas:
        _, design = patsy.dmatrices(
            formula,
            df,
            return_type="dataframe",
            NA_action="drop",
        )
        rows = pd.Index(design.index)
        index = rows if index is None else index.intersection(rows)

    if cluster_col is not None:
        if cluster_col not in df.columns:
            raise KeyError(f"Cluster column is missing: {cluster_col}")
        groups = df.loc[index, cluster_col].astype("string")
        groups = groups.loc[groups.notna()]
        group_sizes = groups.value_counts(dropna=True)
        eligible_groups = group_sizes[group_sizes >= min_cluster_size].index
        index = pd.Index(groups.index[groups.isin(eligible_groups)])

    # Intersect back against df so the returned index keeps the frame's row order.
    return df.index.intersection(index)
