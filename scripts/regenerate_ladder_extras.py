#!/usr/bin/env python3
"""Figures unique to the ladder rebuild: full ten-outcome ladder panels, the C1-C5
coefficient path, and the specification curve. New script, new output filenames only -
does not modify regenerate_standardized_figures.py, build_site_index_assets.py, or any
figure path that already exists on main (see notebooks/regression_robustness_ladder.ipynb
for why: main's own notebook already owns the two-outcome ladder and the pre-existing
coefficient_path_across_models.png).

    python scripts/regenerate_ladder_extras.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paper_figure_utils import (
    GRID,
    MUTED,
    OUTCOME_DISPLAY,
    PAPER_BG,
    TERM_COLORS,
    TERM_LABELS,
    HOLLOW_FACE,
    MissingModelError,
    apply_paper_style,
    load_all_coefs,
    plot_stability_from_csvs,
    stars_from_pval,
    sync_site_figure,
)


ROOT = Path(__file__).resolve().parents[1]
TAB_DIR = ROOT / "outputs" / "standardized_tables"
RAW_TAB_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "standardized_figures"
SITE_FIG_DIR = ROOT / "site" / "assets" / "figures"

PAPER_LADDER_MODELS = [
    "Model C1 (core, common sample)",
    "Model C2 (+ education, housing value)",
    "Model C3 (+ housing structure, tenure)",
    "Model C4 (+ utility FE)",
    "Model C5 (+ county FE, county-clustered SEs)",
]

LADDER_OUTCOMES = [
    "y_pv", "y_storage", "y_chargers", "y_wind_mw", "any_turbines",
    "y_level1_chargers", "y_level2_chargers", "y_dc_fast_chargers",
    "energy_burden_pct", "log_energy_gap_per_capita",
]
LADDER_TERMS_BY_OUTCOME = {
    "y_pv": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "ghi_mean_kwh_m2_day_2023"],
    "y_chargers": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "cdd65_2023", "hdd65_2023"],
    "y_level1_chargers": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "cdd65_2023", "hdd65_2023"],
    "y_level2_chargers": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "cdd65_2023", "hdd65_2023"],
    "y_dc_fast_chargers": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "cdd65_2023", "hdd65_2023"],
    "y_storage": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "cdd65_2023", "hdd65_2023"],
    "y_wind_mw": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "wind_ws50m_mean_2023"],
    "any_turbines": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "wind_ws50m_mean_2023"],
    "energy_burden_pct": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "cdd65_2023", "hdd65_2023", "ghi_mean_kwh_m2_day_2023"],
    "log_energy_gap_per_capita": ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate", "cdd65_2023", "hdd65_2023", "ghi_mean_kwh_m2_day_2023"],
}

COEFFICIENT_PATH_OUTCOMES = {"y_pv": "Solar PV", "y_storage": "Storage", "y_chargers": "EV Chargers"}
COEFFICIENT_PATH_TERMS = ["log_median_household_income", "pct_black", "pct_hispanic", "pct_asian", "poverty_rate"]

SPEC_CURVE_OUTCOMES = ["y_pv", "y_chargers", "y_storage", "y_wind_mw"]
SPEC_CURVE_TERM = "log_median_household_income"
SPEC_CURVE_BLOCK_LABELS = {
    "education": "Education",
    "housing_value": "Housing value",
    "housing_structure": "Housing structure",
    "tenure": "Tenure",
    "utility_fe": "Utility FE",
    "county_fe": "County FE",
}


def load_coef(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path).rename(columns={
        "Unnamed: 0": "term", "Coef.": "coef", "Std.Err.": "std_err",
        "P>|z|": "pval", "P>|t|": "pval",
    })
    df["file"] = path.name
    return df


def plot_ladder_coefficient_path(save_path: Path) -> None:
    """C1-C5 coefficient path for the three headline DER outcomes.

    New filename (coefficient_path_c1_c5.png), separate from the pre-existing
    coefficient_path_across_models.png so that file - which main's own
    build_site_index_assets.py still owns and still draws an (unrelated) M1-M8
    comparison into - is never touched.
    """
    apply_paper_style()
    frames = []
    for outcome in COEFFICIENT_PATH_OUTCOMES:
        for label in PAPER_LADDER_MODELS:
            path = TAB_DIR / f"{outcome} | {label}.csv"
            df = load_coef(path)
            df = df[df["term"].isin(COEFFICIENT_PATH_TERMS)].copy()
            df["outcome"] = outcome
            df["model_short"] = label
            frames.append(df)
    all_coefs = pd.concat(frames, ignore_index=True)

    x_labels = ["C1", "C2", "C3", "C4", "C5"]
    fig, axes = plt.subplots(3, 1, figsize=(12.8, 10.6), sharex=True, facecolor=PAPER_BG)
    x = np.arange(len(PAPER_LADDER_MODELS))

    for ax, (outcome, title) in zip(axes, COEFFICIENT_PATH_OUTCOMES.items()):
        sub = all_coefs[all_coefs["outcome"] == outcome].copy()
        for term in COEFFICIENT_PATH_TERMS:
            s = sub[sub["term"] == term].copy()
            s["model_short"] = pd.Categorical(s["model_short"], categories=PAPER_LADDER_MODELS, ordered=True)
            s = s.sort_values("model_short")
            color = TERM_COLORS.get(term, "#374151")
            ax.plot(
                range(len(s)), s["coef"], marker="o", linewidth=2.1, markersize=5.8,
                color=color, label=TERM_LABELS.get(term, term),
            )
        ax.axhline(0, linestyle="--", linewidth=1.1, color=MUTED)
        ax.grid(axis="y", linestyle="-", linewidth=0.7)
        ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=8)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        ax.set_ylabel("Standardized coefficient")

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(x_labels)
    axes[-1].set_xlabel("Model ladder (C1-C5)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.955))
    fig.tight_layout(rect=[0.03, 0.06, 0.985, 0.9])

    if True:
        fig.patch.set_alpha(0)
        for ax in axes:
            ax.patch.set_alpha(0)
    fig.savefig(save_path, dpi=320, bbox_inches="tight", transparent=True)
    plt.close(fig)


def load_spec_curve(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["ci_low"] = df["coef"] - 1.96 * df["se"]
    df["ci_high"] = df["coef"] + 1.96 * df["se"]
    df["stars"] = df["pval"].map(stars_from_pval)
    return df


def plot_spec_curve(spec_curve_df: pd.DataFrame, outcome: str, term: str, save_path: Path) -> None:
    apply_paper_style()
    block_names = list(SPEC_CURVE_BLOCK_LABELS.keys())
    sub = spec_curve_df[(spec_curve_df["outcome"] == outcome) & (spec_curve_df["term"] == term)].copy()
    if sub.empty:
        raise MissingModelError(f"No spec-curve rows for {outcome} | {term}")
    sub = sub.sort_values("coef").reset_index(drop=True)
    sub["x"] = np.arange(len(sub))
    membership = {
        name: sub["blocks"].map(lambda s, name=name: name in str(s).split("+")).to_numpy()
        for name in block_names
    }

    color = TERM_COLORS.get(term, "#374151")
    sig = sub["pval"] < 0.05
    same_sign = np.sign(sub["coef"]) == np.sign(sub["coef"].median())
    n_specs = len(sub)
    n_sig_same_sign = int((sig & same_sign).to_numpy().sum())

    fig, (ax_top, ax_bottom) = plt.subplots(
        2, 1, figsize=(13.5, 8.5), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.4]}, facecolor=PAPER_BG,
    )
    ax_top.fill_between(sub["x"], sub["ci_low"], sub["ci_high"], color=color, alpha=0.15, linewidth=0)
    ax_top.plot(sub["x"], sub["coef"], color=color, lw=1.2, alpha=0.55)
    ax_top.scatter(sub.loc[sig, "x"], sub.loc[sig, "coef"], s=26, facecolor=color, edgecolor="white", linewidth=0.6, zorder=4)
    ax_top.scatter(sub.loc[~sig, "x"], sub.loc[~sig, "coef"], s=26, facecolor=HOLLOW_FACE, edgecolor=color, linewidth=1.0, zorder=4)
    ax_top.axhline(0, linestyle="--", linewidth=1.1, color=MUTED)
    ax_top.grid(axis="y", linestyle="-", linewidth=0.7)
    ax_top.spines["left"].set_color(GRID)
    ax_top.spines["bottom"].set_visible(False)
    ax_top.tick_params(axis="x", length=0, labelbottom=False)
    ax_top.set_ylabel("Coefficient")
    ax_top.set_title(
        f"{OUTCOME_DISPLAY.get(outcome, outcome)}: {TERM_LABELS.get(term, term)} - "
        f"{n_sig_same_sign}/{n_specs} specifications significant and same-signed",
        fontsize=13, fontweight="bold", loc="left", pad=10,
    )

    for i, name in enumerate(block_names):
        y = len(block_names) - 1 - i
        present = membership[name]
        ax_bottom.scatter(sub.loc[present, "x"], np.full(int(present.sum()), y), s=12, color=MUTED, marker="s")
    ax_bottom.set_yticks(range(len(block_names)))
    ax_bottom.set_yticklabels([SPEC_CURVE_BLOCK_LABELS[n] for n in reversed(block_names)], fontsize=9)
    ax_bottom.set_ylim(-0.6, len(block_names) - 0.4)
    ax_bottom.set_xlim(-0.5, n_specs - 0.5)
    ax_bottom.set_xlabel("Specification, sorted by coefficient")
    ax_bottom.spines["left"].set_visible(False)
    ax_bottom.spines["top"].set_visible(False)
    ax_bottom.tick_params(axis="x", length=0, labelbottom=False)

    fig.tight_layout(rect=[0.02, 0.02, 0.985, 0.96])
    fig.patch.set_alpha(0)
    for ax in (ax_top, ax_bottom):
        ax.patch.set_alpha(0)
    fig.savefig(save_path, dpi=320, bbox_inches="tight", transparent=True)
    plt.close(fig)


def main() -> None:
    all_coefs = load_all_coefs(TAB_DIR)
    generated = []
    skipped: list[str] = []

    available_models = set(all_coefs["model"].unique())
    if not available_models.intersection(PAPER_LADDER_MODELS):
        skipped.append("*_ladder.png: no C1-C5 specifications found - run the ladder notebook first")
    else:
        for outcome in LADDER_OUTCOMES:
            save_path = FIG_DIR / f"{outcome}_ladder.png"
            plot_stability_from_csvs(
                all_coefs=all_coefs,
                outcome=outcome,
                models_keep=PAPER_LADDER_MODELS,
                terms_keep=LADDER_TERMS_BY_OUTCOME[outcome],
                outcome_display=OUTCOME_DISPLAY,
                save_path=save_path,
            )
            generated.append(save_path)

    coef_path_path = FIG_DIR / "coefficient_path_c1_c5.png"
    plot_ladder_coefficient_path(coef_path_path)
    generated.append(coef_path_path)

    spec_curve_csv = RAW_TAB_DIR / "spec_curve.csv"
    if spec_curve_csv.exists():
        spec_curve_df = load_spec_curve(spec_curve_csv)
        for outcome in SPEC_CURVE_OUTCOMES:
            save_path = FIG_DIR / f"spec_curve_{outcome}.png"
            try:
                plot_spec_curve(spec_curve_df, outcome, SPEC_CURVE_TERM, save_path)
                generated.append(save_path)
            except MissingModelError as exc:
                skipped.append(f"spec_curve_{outcome}.png: {exc}")
    else:
        skipped.append(f"spec_curve_*.png: {spec_curve_csv} not found")

    for path in generated:
        sync_site_figure(path, SITE_FIG_DIR)

    print("Regenerated ladder-extras figures:")
    for path in generated:
        print(path.relative_to(ROOT))
    if skipped:
        print("\nSKIPPED:")
        for msg in skipped:
            print(f"  - {msg}")


if __name__ == "__main__":
    main()
