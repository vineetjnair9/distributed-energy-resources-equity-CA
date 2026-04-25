#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
from statsmodels.nonparametric.smoothers_lowess import lowess

from paper_figure_utils import (
    GRID,
    MUTED,
    PANEL_BG,
    PAPER_BG,
    TERM_COLORS,
    TERM_LABELS,
    TEXT,
    apply_paper_style,
)


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "processed" / "combined_der_dataset_w_controls_predictors.csv"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
STANDARDIZED_TABLES = ROOT / "outputs" / "standardized_tables"
OUTPUT_FIGURES = ROOT / "outputs" / "figures"
SITE_FIGURES = ROOT / "site" / "assets" / "figures"
GENERATED = OUTPUT_FIGURES / "generated"
SITE_GENERATED = SITE_FIGURES / "generated"
LOWESS_SEED = 42
LOWESS_FRAC = 0.35
LOWESS_BOOTSTRAPS = 300
LOWESS_GRID_SIZE = 200
LOWESS_METRIC_PERCENTILES = (5, 95)


def derive_analysis_frame() -> pd.DataFrame:
    df = pd.read_csv(DATASET).copy()
    df = df[df["total_population"].fillna(0) >= 1000].copy()

    pop = df["total_population"].replace(0, np.nan)
    df["log_median_household_income"] = np.log1p(df["median_household_income"])

    df["chargers_per_1k"] = (df["total_chargers"].fillna(0) * 1000.0) / pop
    df["level1_chargers_per_1k"] = (df["level1_chargers"].fillna(0) * 1000.0) / pop
    df["level2_chargers_per_1k"] = (df["level2_chargers"].fillna(0) * 1000.0) / pop
    df["dc_fast_chargers_per_1k"] = (df["dc_fast_chargers"].fillna(0) * 1000.0) / pop
    df["pv_kw_per_1k"] = (df["PV_system_size_DC"].fillna(0) * 1000.0) / pop
    df["storage_mw_per_100k"] = (df["storage_capacity_mw"].fillna(0) * 100000.0) / pop
    df["wind_mw_per_100k"] = (df["wind_capacity_mw"].fillna(0) * 100000.0) / pop

    df["y_chargers"] = np.log1p(df["chargers_per_1k"])
    df["y_level1_chargers"] = np.log1p(df["level1_chargers_per_1k"])
    df["y_level2_chargers"] = np.log1p(df["level2_chargers_per_1k"])
    df["y_dc_fast_chargers"] = np.log1p(df["dc_fast_chargers_per_1k"])
    df["y_pv"] = np.log1p(df["pv_kw_per_1k"])
    df["y_storage"] = np.log1p(df["storage_mw_per_100k"])
    df["y_wind_mw"] = np.log1p(df["wind_mw_per_100k"])
    df["combined_nonwhite_share"] = df[["pct_black", "pct_hispanic", "pct_asian"]].sum(axis=1, min_count=1)
    return df


def _save(fig: plt.Figure, name: str) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    path = GENERATED / name
    fig.savefig(path, dpi=320, bbox_inches="tight")
    if path.suffix.lower() != ".svg":
        fig.savefig(path.with_suffix(".svg"), bbox_inches="tight", metadata={"Date": None})
    SITE_GENERATED.mkdir(parents=True, exist_ok=True)
    (SITE_GENERATED / path.name).write_bytes(path.read_bytes())
    svg_path = path.with_suffix(".svg")
    if svg_path.exists():
        (SITE_GENERATED / svg_path.name).write_bytes(svg_path.read_bytes())
    plt.close(fig)


def lowess_with_bootstrap_ci(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    *,
    frac: float = LOWESS_FRAC,
    n_boot: int = LOWESS_BOOTSTRAPS,
    grid_size: int = LOWESS_GRID_SIZE,
    seed: int = LOWESS_SEED,
) -> pd.DataFrame:
    d = df[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna().copy()
    d = d.sort_values([x_col, y_col], kind="mergesort")
    x = d[x_col].to_numpy(dtype=float)
    y = d[y_col].to_numpy(dtype=float)
    x_grid = np.linspace(float(x.min()), float(x.max()), grid_size)

    fit = sm.nonparametric.lowess(y, x, frac=frac, return_sorted=True)
    y_hat = np.interp(x_grid, fit[:, 0], fit[:, 1])

    rng = np.random.default_rng(seed)
    boot_preds = np.zeros((n_boot, grid_size))
    n = len(d)
    for idx_boot in range(n_boot):
        idx = rng.integers(0, n, n)
        xb = x[idx]
        yb = y[idx]
        order = np.lexsort((yb, xb))
        fit_b = sm.nonparametric.lowess(yb[order], xb[order], frac=frac, return_sorted=True)
        boot_preds[idx_boot, :] = np.interp(x_grid, fit_b[:, 0], fit_b[:, 1])

    return pd.DataFrame(
        {
            "x_grid": x_grid,
            "lowess": y_hat,
            "ci_low": np.percentile(boot_preds, 2.5, axis=0),
            "ci_high": np.percentile(boot_preds, 97.5, axis=0),
        }
    )


def summarize_lowess_gradient(lowess_df: pd.DataFrame, predictor: str, outcome: str) -> dict[str, float | str]:
    low, high = np.percentile(lowess_df["x_grid"], LOWESS_METRIC_PERCENTILES)
    y_low = float(np.interp(low, lowess_df["x_grid"], lowess_df["lowess"]))
    y_high = float(np.interp(high, lowess_df["x_grid"], lowess_df["lowess"]))
    endpoint_change = y_high - y_low
    span = high - low
    return {
        "predictor": predictor,
        "outcome": outcome,
        "endpoint_change": endpoint_change,
        "average_slope_mid90": endpoint_change / span if span else np.nan,
    }


def build_geography_panel() -> None:
    apply_paper_style()
    sources = [
        (
            ROOT / "outputs" / "figures" / "pv_maps" / "y_pv_model_1_baseline_climate_controls_spatial_figure.png",
            "Solar PV",
        ),
        (
            ROOT / "outputs" / "figures" / "storage_maps" / "y_storage_model_1_baseline_climate_controls_spatial_figure.png",
            "Storage",
        ),
        (
            ROOT / "outputs" / "figures" / "chargers_maps" / "y_chargers_model_1_baseline_climate_controls_spatial_figure.png",
            "EV Chargers",
        ),
    ]

    fig = plt.figure(figsize=(14.8, 10.2), facecolor=PAPER_BG)
    grid = GridSpec(2, 2, figure=fig, height_ratios=[1, 1.02], hspace=0.18, wspace=0.08)
    axes = [
        fig.add_subplot(grid[0, 0]),
        fig.add_subplot(grid[0, 1]),
        fig.add_subplot(grid[1, :]),
    ]

    for ax, (path, title) in zip(axes, sources):
        ax.imshow(plt.imread(path))
        ax.set_title(title, fontsize=15, fontweight="bold", pad=8)
        ax.set_facecolor(PANEL_BG)
        ax.axis("off")

    fig.suptitle("Figure A. California ZIP/ZCTA geography of baseline DER outcomes", fontsize=18, fontweight="bold", y=0.985)
    fig.text(
        0.5,
        0.952,
        "Baseline spatial figures for rooftop PV, storage, and EV charging show that deployment is not evenly distributed across the state.",
        ha="center",
        va="top",
        fontsize=10.5,
        color=MUTED,
    )
    fig.subplots_adjust(left=0.03, right=0.97, bottom=0.04, top=0.88, hspace=0.18, wspace=0.08)
    _save(fig, "california_outcome_geography_panel.png")


def build_income_small_multiples(df: pd.DataFrame) -> None:
    apply_paper_style()
    panels = [
        ("y_pv", "Solar PV", TERM_COLORS["log_median_household_income"], "#B45309"),
        ("y_storage", "Storage", "#7C3AED", "#7C3AED"),
        ("y_chargers", "EV Chargers", "#0F766E", "#0F766E"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.8), facecolor=PAPER_BG)
    x_all = df["median_household_income"].dropna() / 1000.0
    x_limits = (
        float(np.nanpercentile(x_all, 2)),
        float(np.nanpercentile(x_all, 98)),
    )
    standardized_ranges = []
    transformed = {}

    for col, *_ in panels:
        sub = df[["median_household_income", col]].dropna().copy()
        transformed[col] = (sub["median_household_income"] / 1000.0, sub[col])
        standardized_ranges.append(np.nanpercentile(sub[col], [1, 99]))

    y_min = min(r[0] for r in standardized_ranges)
    y_max = max(r[1] for r in standardized_ranges)

    for ax, (col, title, line_color, scatter_color) in zip(axes, panels):
        x, y = transformed[col]
        ax.scatter(x, y, s=10, alpha=0.12, color=scatter_color, edgecolors="none")
        smooth = lowess(y, x, frac=0.22, return_sorted=True)
        ax.plot(smooth[:, 0], smooth[:, 1], color=line_color, linewidth=3)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=8)
        ax.grid(axis="y", linestyle="-", linewidth=0.7)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        ax.set_xlabel("Median household income ($ thousands)")
        ax.set_xlim(x_limits)
        ax.set_ylim(y_min, y_max)

    axes[0].set_ylabel("Outcome, log(1 + rate)")
    fig.suptitle("Figure B. Adoption intensity rises with income, but not equally across technologies", fontsize=17, fontweight="bold", y=0.99)
    fig.text(
        0.5,
        0.94,
        "Points are ZIP/ZCTAs; curves are LOWESS fits. Outcomes use the same log-transformed deployment variables reported in the regressions.",
        ha="center",
        va="top",
        fontsize=10.25,
        color=MUTED,
    )
    fig.tight_layout(rect=[0.02, 0.05, 0.985, 0.9])
    _save(fig, "income_lowess_small_multiples.png")


def build_eda_panel(df: pd.DataFrame) -> None:
    apply_paper_style()
    panels = [
        ("pv_kw_per_1k", "PV deployment"),
        ("storage_mw_per_100k", "Storage deployment"),
        ("chargers_per_1k", "EV charging deployment"),
        ("median_household_income", "Median household income"),
        ("poverty_rate", "Poverty rate"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(15.4, 8.4), facecolor=PAPER_BG)
    axes = axes.flatten()

    for ax, (col, title) in zip(axes, panels):
        s = df[col].dropna().astype(float)
        upper = float(np.nanpercentile(s, 98))
        clipped = s.clip(upper=upper)
        ax.hist(clipped, bins=28, color="#C9733D", edgecolor="#fffdf8", alpha=0.9)
        ax.axvline(float(s.median()), color="#17202A", linestyle="--", linewidth=1.6)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=8)
        ax.grid(axis="y", linestyle="-", linewidth=0.7)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        if col == "median_household_income":
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
        elif col == "poverty_rate":
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0%}"))

    axes[0].set_ylabel("ZIP/ZCTA count")
    axes[3].set_ylabel("ZIP/ZCTA count")
    axes[5].axis("off")
    fig.suptitle("Descriptive distributions for DER deployment and neighborhood conditions", fontsize=17, fontweight="bold", y=0.99)
    fig.text(
        0.5,
        0.945,
        "Histograms use clipped upper tails at the 98th percentile for readability; dashed lines mark medians.",
        ha="center",
        va="top",
        fontsize=10.25,
        color=MUTED,
    )
    fig.tight_layout(rect=[0.02, 0.04, 0.985, 0.92])
    _save(fig, "eda_distribution_panel.png")


def build_predictor_lowess_small_multiples(
    df: pd.DataFrame,
    *,
    x_col: str,
    x_label: str,
    title: str,
    subtitle: str,
    output_name: str,
    metrics_name: str,
) -> None:
    apply_paper_style()
    panels = [
        ("y_pv", "Solar PV", "#B45309"),
        ("y_storage", "Storage", "#7C3AED"),
        ("y_chargers", "EV Chargers", "#0F766E"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.9), facecolor=PAPER_BG)
    metric_rows = []
    smooths = {}
    y_ranges = []

    for y_col, _, _ in panels:
        smooth = lowess_with_bootstrap_ci(df, x_col, y_col)
        smooths[y_col] = smooth
        metric_rows.append(summarize_lowess_gradient(smooth, x_col, y_col))
        y_ranges.append(np.nanpercentile(smooth[["ci_low", "ci_high"]].to_numpy(), [1, 99]))

    y_min = min(r[0] for r in y_ranges)
    y_max = max(r[1] for r in y_ranges)
    x_values = df[x_col].replace([np.inf, -np.inf], np.nan).dropna()
    x_limits = (
        float(np.nanpercentile(x_values, 1)),
        float(np.nanpercentile(x_values, 99)),
    )

    for ax, (y_col, panel_title, color) in zip(axes, panels):
        sub = df[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna().sort_values([x_col, y_col])
        smooth = smooths[y_col]
        ax.scatter(sub[x_col], sub[y_col], s=10, alpha=0.12, color=color, edgecolors="none")
        ax.plot(smooth["x_grid"], smooth["lowess"], color=color, linewidth=3)
        ax.fill_between(smooth["x_grid"], smooth["ci_low"], smooth["ci_high"], color=color, alpha=0.18, linewidth=0)
        ax.set_title(panel_title, fontsize=13, fontweight="bold", pad=8)
        ax.grid(axis="y", linestyle="-", linewidth=0.7)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        ax.set_xlabel(x_label)
        ax.set_xlim(x_limits)
        ax.set_ylim(y_min, y_max)
        if x_values.max() <= 1.5:
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0%}"))

    axes[0].set_ylabel("Outcome, log(1 + rate)")
    fig.suptitle(title, fontsize=17, fontweight="bold", y=0.99)
    fig.text(0.5, 0.94, subtitle, ha="center", va="top", fontsize=10.25, color=MUTED)
    fig.tight_layout(rect=[0.02, 0.05, 0.985, 0.9])
    _save(fig, output_name)

    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(metric_rows).to_csv(OUTPUT_TABLES / metrics_name, index=False)


def load_coef(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path).rename(columns={"Unnamed: 0": "term", "Coef.": "coef", "Std.Err.": "std_err", "P>|z|": "pval", "P>|t|": "pval"})
    df["file"] = path.name
    return df


def build_coefficient_path() -> None:
    apply_paper_style()
    model_map = [
        ("M1", "Model 1 baseline (CDD+HDD)"),
        ("M2", "Model 2 (add bachelors)"),
        ("M3", "Model 3B (temp only)"),
        ("M4", "Model 4R interactions (centered)"),
        ("M5", "Model 5 utility FE"),
        ("M6", "Model 6B county fe"),
        ("M7", "Model 7 (infrastructure controls, outcome-safe)"),
        ("M8", "Model 8 add demand proxy"),
    ]
    outcomes = {
        "y_pv": "Solar PV",
        "y_storage": "Storage",
        "y_chargers": "EV Chargers",
    }
    terms = [
        "log_median_household_income",
        "pct_black",
        "pct_hispanic",
        "pct_asian",
        "poverty_rate",
    ]

    frames = []
    for outcome in outcomes:
        for short, label in model_map:
            path = STANDARDIZED_TABLES / f"{outcome} | {label}.csv"
            df = load_coef(path)
            df = df[df["term"].isin(terms)].copy()
            df["outcome"] = outcome
            df["model_short"] = short
            frames.append(df)
    all_coefs = pd.concat(frames, ignore_index=True)

    fig, axes = plt.subplots(3, 1, figsize=(12.8, 10.6), sharex=True, facecolor=PAPER_BG)
    x = np.arange(len(model_map))

    for ax, (outcome, title) in zip(axes, outcomes.items()):
        sub = all_coefs[all_coefs["outcome"] == outcome].copy()
        for term in terms:
            s = sub[sub["term"] == term].copy()
            s["model_short"] = pd.Categorical(s["model_short"], categories=[m[0] for m in model_map], ordered=True)
            s = s.sort_values("model_short")
            x_positions = [i for i, short in enumerate([m[0] for m in model_map]) if short in set(s["model_short"].astype(str))]
            color = TERM_COLORS.get(term, "#374151")
            ax.plot(
                x_positions,
                s["coef"],
                marker="o",
                linewidth=2.1,
                markersize=5.8,
                color=color,
                label=TERM_LABELS.get(term, term),
            )
        ax.axhline(0, linestyle="--", linewidth=1.1, color=MUTED)
        ax.grid(axis="y", linestyle="-", linewidth=0.7)
        ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=8)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        ax.set_ylabel("Standardized coefficient")

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([m[0] for m in model_map])
    axes[-1].set_xlabel("Model ladder")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.955))
    fig.suptitle("Figure C. Core disparity coefficients across the model ladder", fontsize=17, fontweight="bold", y=0.99)
    fig.text(
        0.5,
        0.885,
        "The same five predictors are traced from the standardized baseline through richer socioeconomic, geographic, and infrastructure specifications.",
        ha="center",
        va="top",
        fontsize=10.25,
        color=MUTED,
    )
    fig.tight_layout(rect=[0.03, 0.06, 0.985, 0.84])
    _save(fig, "coefficient_path_across_models.png")


def main() -> None:
    df = derive_analysis_frame()
    build_geography_panel()
    build_eda_panel(df)
    build_income_small_multiples(df)
    build_predictor_lowess_small_multiples(
        df,
        x_col="combined_nonwhite_share",
        x_label="Combined non-white share",
        title="Descriptive DER gradients by combined non-white share",
        subtitle="Curves are deterministic LOWESS fits with seeded bootstrap 95% confidence intervals.",
        output_name="nonwhite_lowess_small_multiples.png",
        metrics_name="nonwhite_lowess_small_multiples_metrics.csv",
    )
    build_predictor_lowess_small_multiples(
        df,
        x_col="pct_bachelors_plus",
        x_label="Adults with bachelor's degree or higher",
        title="Descriptive DER gradients by educational attainment",
        subtitle="Curves are deterministic LOWESS fits with seeded bootstrap 95% confidence intervals.",
        output_name="education_lowess_small_multiples.png",
        metrics_name="education_lowess_small_multiples_metrics.csv",
    )
    build_coefficient_path()


if __name__ == "__main__":
    main()
