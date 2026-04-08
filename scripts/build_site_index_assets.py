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
SITE_FIGURES = ROOT / "site" / "assets" / "figures"
GENERATED = SITE_FIGURES / "generated"


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

    df["y_chargers"] = np.log1p(df["chargers_per_1k"])
    df["y_level1_chargers"] = np.log1p(df["level1_chargers_per_1k"])
    df["y_level2_chargers"] = np.log1p(df["level2_chargers_per_1k"])
    df["y_dc_fast_chargers"] = np.log1p(df["dc_fast_chargers_per_1k"])
    df["y_pv"] = np.log1p(df["pv_kw_per_1k"])
    df["y_storage"] = np.log1p(df["storage_mw_per_100k"])
    return df


def _save(fig: plt.Figure, name: str) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    fig.savefig(GENERATED / name, dpi=320, bbox_inches="tight")
    plt.close(fig)


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
        ("pv_kw_per_1k", "Solar PV (kW per 1,000 residents)", TERM_COLORS["log_median_household_income"], "#B45309"),
        ("storage_mw_per_100k", "Storage (MW per 100,000 residents)", "#7C3AED", "#7C3AED"),
        ("chargers_per_1k", "Chargers (per 1,000 residents)", "#0F766E", "#0F766E"),
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
        y = sub[col]
        y_std = (y - y.mean()) / y.std(ddof=0)
        transformed[col] = (sub["median_household_income"] / 1000.0, y_std)
        standardized_ranges.append(np.nanpercentile(y_std, [1, 99]))

    y_min = min(r[0] for r in standardized_ranges)
    y_max = max(r[1] for r in standardized_ranges)

    for ax, (col, title, line_color, scatter_color) in zip(axes, panels):
        x, y_std = transformed[col]
        ax.scatter(x, y_std, s=10, alpha=0.12, color=scatter_color, edgecolors="none")
        smooth = lowess(y_std, x, frac=0.22, return_sorted=True)
        ax.plot(smooth[:, 0], smooth[:, 1], color=line_color, linewidth=3)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=8)
        ax.grid(axis="y", linestyle="-", linewidth=0.7)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        ax.set_xlabel("Median household income ($ thousands)")
        ax.set_xlim(x_limits)
        ax.set_ylim(y_min, y_max)

    axes[0].set_ylabel("Standardized outcome level")
    fig.suptitle("Figure B. Adoption intensity rises with income, but not equally across technologies", fontsize=17, fontweight="bold", y=0.99)
    fig.text(
        0.5,
        0.94,
        "Points are ZIP/ZCTAs; curves are LOWESS fits. Outcomes are standardized within technology so the vertical scale is directly comparable across panels.",
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
            path = OUTPUT_TABLES / f"{outcome} | {label}.csv"
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
        ax.set_ylabel("Coefficient")

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([m[0] for m in model_map])
    axes[-1].set_xlabel("Model ladder")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.955))
    fig.suptitle("Figure C. Core disparity coefficients across the model ladder", fontsize=17, fontweight="bold", y=0.99)
    fig.text(
        0.5,
        0.885,
        "The same five predictors are traced from the baseline through richer socioeconomic, geographic, and infrastructure specifications.",
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
    build_coefficient_path()


if __name__ == "__main__":
    main()
