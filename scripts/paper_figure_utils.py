from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


TERM_LABELS = {
    "Intercept": "Intercept",
    "log_median_household_income": "Log median income",
    "log_median_housing_value": "Log housing value",
    "log_pop_density": "Log population density",
    "poverty_rate": "Poverty rate",
    "pct_bachelors_plus": "% Bachelor's+",
    "pct_black": "% Black",
    "pct_hispanic": "% Hispanic",
    "pct_asian": "% Asian",
    "cdd65_2023": "Cooling degree days",
    "hdd65_2023": "Heating degree days",
    "ghi_mean_kwh_m2_day_2023": "Solar irradiance (GHI)",
    "wind_ws10m_mean_2023": "Wind speed (10m)",
    "wind_ws50m_mean_2023": "Wind speed (50m)",
    "log_kwh": "Log annual electricity demand",
    "y_pv": "Solar PV adoption",
    "y_chargers": "EV charger adoption",
}


OUTCOME_DISPLAY = {
    "y_pv": "Solar PV",
    "y_chargers": "EV Chargers",
    "y_storage": "Storage",
    "y_wind_mw": "Wind MW",
    "any_turbines": "Any turbines",
}


OUTCOME_COLORS = {
    "y_pv": "#B45309",
    "y_chargers": "#0F766E",
    "y_storage": "#7C3AED",
    "y_wind_mw": "#2563EB",
    "any_turbines": "#4B5563",
}


TERM_COLORS = {
    "log_median_household_income": "#1D4ED8",
    "pct_black": "#7C3AED",
    "pct_hispanic": "#C2410C",
    "pct_asian": "#0F766E",
    "poverty_rate": "#B45309",
    "ghi_mean_kwh_m2_day_2023": "#D97706",
    "cdd65_2023": "#DC2626",
    "hdd65_2023": "#2563EB",
    "wind_ws50m_mean_2023": "#0284C7",
}


PAPER_BG = "#F8F5EF"
PANEL_BG = "#FFFDF8"
GRID = "#D9D4C7"
TEXT = "#1F2933"
MUTED = "#52606D"


def apply_paper_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": PAPER_BG,
            "axes.facecolor": PANEL_BG,
            "savefig.facecolor": PAPER_BG,
            "font.family": "DejaVu Serif",
            "font.size": 11,
            "axes.titlesize": 14,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "text.color": TEXT,
            "axes.labelcolor": TEXT,
            "axes.edgecolor": GRID,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "grid.color": GRID,
            "grid.alpha": 0.55,
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.hashsalt": "der-paper-figures",
        }
    )


def stars_from_pval(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    if p < 0.10:
        return "·"
    return ""


def parse_filename(path: str | Path) -> tuple[str, str]:
    fname = os.path.basename(str(path)).replace(".csv", "")
    if " | " in fname:
        outcome, model = fname.split(" | ", 1)
    else:
        outcome, model = fname, "Unknown"
    return outcome.strip(), model.strip()


def load_coef_csv(path: str | Path, term_labels: dict[str, str] | None = None) -> pd.DataFrame:
    outcome, model = parse_filename(path)
    df = pd.read_csv(path)

    first_col = df.columns[0]
    if first_col == "Unnamed: 0":
        df = df.rename(columns={"Unnamed: 0": "term"})
    elif first_col != "term":
        df = df.rename(columns={first_col: "term"})

    rename_map = {
        "Coef.": "coef",
        "Std.Err.": "std_err",
        "P>|z|": "pval",
        "P>|t|": "pval",
        "[0.025": "conf_low",
        "0.025": "conf_low",
        "0.975]": "conf_high",
        "0.975": "conf_high",
    }
    df = df.rename(columns=rename_map)
    keep = ["term", "coef", "std_err", "pval", "conf_low", "conf_high"]
    df = df[keep].copy()
    labels = term_labels or TERM_LABELS
    df["outcome"] = outcome
    df["model"] = model
    df["term_label"] = df["term"].map(lambda x: labels.get(x, x))
    df["stars"] = df["pval"].map(stars_from_pval)
    return df


def load_all_coefs(tab_dir: str | Path) -> pd.DataFrame:
    tab_dir = Path(tab_dir)
    frames = []
    for path in sorted(tab_dir.glob("*.csv")):
        try:
            frames.append(load_coef_csv(path))
        except Exception:
            continue
    if not frames:
        raise FileNotFoundError(f"No coefficient tables loaded from {tab_dir}")
    return pd.concat(frames, ignore_index=True)


def _finish_figure(fig: plt.Figure, save_path: str | Path | None = None) -> None:
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=320, bbox_inches="tight")
        if save_path.suffix.lower() != ".svg":
            fig.savefig(save_path.with_suffix(".svg"), bbox_inches="tight", metadata={"Date": None})


def plot_dot_whisker_from_csvs(
    all_coefs: pd.DataFrame,
    main_models: dict[str, str],
    terms_keep: list[str],
    outcome_display: dict[str, str] | None = None,
    save_path: str | Path | None = None,
) -> plt.Figure:
    apply_paper_style()
    outcome_display = outcome_display or OUTCOME_DISPLAY
    outcomes = list(main_models.keys())
    fig, axes = plt.subplots(len(outcomes), 1, figsize=(10.6, 12.8), sharex=True)
    if len(outcomes) == 1:
        axes = [axes]

    xmins: list[float] = []
    xmaxs: list[float] = []

    for ax, outcome in zip(axes, outcomes):
        model = main_models[outcome]
        sub = all_coefs[
            (all_coefs["outcome"] == outcome)
            & (all_coefs["model"] == model)
            & (all_coefs["term"].isin(terms_keep))
        ].copy()
        sub["term"] = pd.Categorical(sub["term"], categories=terms_keep, ordered=True)
        sub = sub.sort_values("term")
        y = np.arange(len(sub))[::-1]
        ax.set_facecolor(PANEL_BG)

        for yi, (_, row) in zip(y, sub.iterrows()):
            color = TERM_COLORS.get(row["term"], OUTCOME_COLORS.get(outcome, "#374151"))
            ax.hlines(yi, row["conf_low"], row["conf_high"], color=color, lw=2.6, alpha=0.95)
            ax.plot(row["coef"], yi, "o", color=color, ms=7.5, mec="white", mew=0.9, zorder=3)
            if row["stars"]:
                ax.text(
                    row["conf_high"] + 0.015,
                    yi,
                    row["stars"],
                    va="center",
                    ha="left",
                    fontsize=10,
                    color=TEXT,
                    fontweight="bold",
                )
            xmins.append(float(row["conf_low"]))
            xmaxs.append(float(row["conf_high"]))

        ax.axvline(0, linestyle="--", linewidth=1.2, color=MUTED, alpha=0.9)
        ax.grid(axis="x", linestyle="-", linewidth=0.7)
        ax.set_yticks(y)
        ax.set_yticklabels(sub["term_label"])
        ax.set_title(
            outcome_display.get(outcome, outcome),
            loc="left",
            color=OUTCOME_COLORS.get(outcome, TEXT),
            fontweight="bold",
            pad=8,
        )
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(GRID)

    xmin = min(xmins) - 0.05
    xmax = max(xmaxs) + 0.08
    for ax in axes:
        ax.set_xlim(xmin, xmax)

    axes[-1].set_xlabel("Standardized coefficient estimate")
    fig.suptitle(
        "How the baseline equity relationships differ across DER outcomes",
        fontsize=17,
        y=0.992,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.965,
        "Points show standardized coefficients; horizontal lines show 95% confidence intervals.",
        ha="center",
        va="top",
        fontsize=10.5,
        color=MUTED,
    )
    fig.text(
        0.5,
        0.012,
        "Significance: *** p < 0.001, ** p < 0.01, * p < 0.05, · p < 0.10",
        ha="center",
        fontsize=9.5,
        color=MUTED,
    )
    fig.tight_layout(rect=[0.07, 0.04, 0.98, 0.962])
    _finish_figure(fig, save_path)
    return fig


def plot_stability_from_csvs(
    all_coefs: pd.DataFrame,
    outcome: str,
    models_keep: list[str],
    terms_keep: list[str],
    outcome_display: dict[str, str] | None = None,
    save_path: str | Path | None = None,
) -> plt.Figure:
    apply_paper_style()
    outcome_display = outcome_display or OUTCOME_DISPLAY
    sub = all_coefs[
        (all_coefs["outcome"] == outcome)
        & (all_coefs["model"].isin(models_keep))
        & (all_coefs["term"].isin(terms_keep))
    ].copy()
    sub["model"] = pd.Categorical(sub["model"], categories=models_keep, ordered=True)

    fig, axes = plt.subplots(len(terms_keep), 1, figsize=(12.6, 1.9 * len(terms_keep) + 1.7), sharex=True)
    if len(terms_keep) == 1:
        axes = [axes]

    x = np.arange(len(models_keep))

    for ax, term in zip(axes, terms_keep):
        s = sub[sub["term"] == term].copy().sort_values("model")
        s["x"] = s["model"].map({model: i for i, model in enumerate(models_keep)})
        color = TERM_COLORS.get(term, OUTCOME_COLORS.get(outcome, "#374151"))
        ax.fill_between(
            s["x"].to_numpy(),
            s["conf_low"].to_numpy(),
            s["conf_high"].to_numpy(),
            color=color,
            alpha=0.15,
            linewidth=0,
        )
        ax.plot(s["x"], s["coef"], color=color, lw=2.2, marker="o", ms=6.8, mec="white", mew=0.8)
        sig = s["pval"] < 0.05
        ax.scatter(
            s.loc[sig, "x"],
            s.loc[sig, "coef"],
            s=70,
            facecolor=color,
            edgecolor="white",
            linewidth=1.2,
            zorder=4,
        )
        ax.scatter(
            s.loc[~sig, "x"],
            s.loc[~sig, "coef"],
            s=70,
            facecolor=PANEL_BG,
            edgecolor=color,
            linewidth=1.6,
            zorder=4,
        )
        ax.axhline(0, linestyle="--", linewidth=1.1, color=MUTED, alpha=0.9)
        ax.grid(axis="y", linestyle="-", linewidth=0.7)
        ax.set_ylabel(TERM_LABELS.get(term, term), rotation=0, ha="right", va="center", labelpad=55)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(models_keep, rotation=28, ha="right")
    axes[-1].set_xlabel("Specification")
    fig.suptitle(
        f"Coefficient stability across specifications: {outcome_display.get(outcome, outcome)}",
        fontsize=16,
        y=0.995,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.968,
        "Filled markers indicate p < 0.05; hollow markers indicate p ≥ 0.05.",
        ha="center",
        va="top",
        fontsize=10.25,
        color=MUTED,
    )
    fig.tight_layout(rect=[0.08, 0.04, 0.985, 0.955])
    _finish_figure(fig, save_path)
    return fig


def plot_heatmap_from_csvs(
    all_coefs: pd.DataFrame,
    outcomes_keep: Iterable[str],
    models_keep: Iterable[str],
    terms_keep: list[str],
    outcome_display: dict[str, str] | None = None,
    save_path: str | Path | None = None,
) -> plt.Figure:
    apply_paper_style()
    outcome_display = outcome_display or OUTCOME_DISPLAY
    sub = all_coefs[
        (all_coefs["outcome"].isin(outcomes_keep))
        & (all_coefs["model"].isin(models_keep))
        & (all_coefs["term"].isin(terms_keep))
    ].copy()

    sub["col_label"] = sub["outcome"].map(lambda x: outcome_display.get(x, x)) + "\n" + sub["model"]
    coef_mat = sub.pivot_table(index="term", columns="col_label", values="coef").reindex(terms_keep)
    pval_mat = sub.pivot_table(index="term", columns="col_label", values="pval").reindex(terms_keep)

    vmax = np.nanmax(np.abs(coef_mat.values))
    vmax = 1.0 if np.isnan(vmax) or vmax == 0 else float(vmax)

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "paper_diverging", ["#1D4ED8", "#F8F5EF", "#B45309"], N=256
    )
    fig, ax = plt.subplots(figsize=(15.5, 8.8))
    im = ax.imshow(
        coef_mat.values,
        aspect="auto",
        cmap=cmap,
        norm=mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax),
    )

    ax.set_xticks(np.arange(coef_mat.shape[1]))
    ax.set_xticklabels(coef_mat.columns, rotation=35, ha="right")
    ax.set_yticks(np.arange(coef_mat.shape[0]))
    ax.set_yticklabels([TERM_LABELS.get(t, t) for t in coef_mat.index])

    for i in range(coef_mat.shape[0]):
        for j in range(coef_mat.shape[1]):
            coef = coef_mat.iloc[i, j]
            p = pval_mat.iloc[i, j]
            if pd.isna(coef):
                continue
            stars = stars_from_pval(p)
            label = f"{coef:.2f}"
            if stars:
                label = f"{label}\n{stars}"
            ax.text(j, i, label, ha="center", va="center", fontsize=9, color=TEXT)

    cbar = plt.colorbar(im, ax=ax, shrink=0.92, pad=0.015)
    cbar.set_label("Standardized coefficient", color=TEXT)
    cbar.outline.set_edgecolor(GRID)

    ax.set_title("Coefficient heatmap across outcomes and specifications", fontsize=16, pad=14, fontweight="bold")
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)

    fig.text(
        0.5,
        0.02,
        "Cells show standardized coefficients, with significance markers inside each cell.",
        ha="center",
        fontsize=9.5,
        color=MUTED,
    )
    fig.tight_layout(rect=[0.02, 0.04, 0.985, 0.965])
    _finish_figure(fig, save_path)
    return fig


def plot_charger_subtype_comparison(
    table_dir: str | Path,
    save_path: str | Path | None = None,
) -> plt.Figure:
    apply_paper_style()
    table_dir = Path(table_dir)
    files = {
        "Aggregate chargers": table_dir / "y_chargers | Model 1 baseline (CDD+HDD).csv",
        "Level 1 chargers": table_dir / "y_level1_chargers | Model 1 baseline (CDD+HDD).csv",
        "Level 2 chargers": table_dir / "y_level2_chargers | Model 1 baseline (CDD+HDD).csv",
        "DC fast chargers": table_dir / "y_dc_fast_chargers | Model 1 baseline (CDD+HDD).csv",
    }
    var_order = [
        "log_median_household_income",
        "poverty_rate",
        "pct_black",
        "pct_hispanic",
        "pct_asian",
    ]

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.2), sharex=True)
    axes = axes.flatten()
    xmins: list[float] = []
    xmaxs: list[float] = []

    for ax, (title, path) in zip(axes, files.items()):
        df = load_coef_csv(path)
        df = df[df["term"].isin(var_order)].copy()
        df["term"] = pd.Categorical(df["term"], categories=var_order, ordered=True)
        df = df.sort_values("term")
        y = np.arange(len(df))[::-1]

        for yi, (_, row) in zip(y, df.iterrows()):
            color = TERM_COLORS.get(row["term"], "#374151")
            ax.hlines(yi, row["conf_low"], row["conf_high"], color=color, lw=2.4, alpha=0.95)
            ax.plot(row["coef"], yi, "o", color=color, ms=7.3, mec="white", mew=0.9)
            if row["pval"] < 0.05:
                ax.plot(row["coef"], yi, "o", ms=10.5, mfc="none", mec=color, mew=1.5)
            xmins.append(float(row["conf_low"]))
            xmaxs.append(float(row["conf_high"]))

        ax.axvline(0, color=MUTED, lw=1.1, ls="--")
        ax.grid(axis="x", linestyle="-", linewidth=0.7)
        ax.set_title(title, fontsize=13, pad=10, fontweight="bold")
        ax.set_yticks(y)
        ax.set_yticklabels([TERM_LABELS.get(t, t) for t in df["term"]])
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)

    xmin = min(xmins) - 0.15
    xmax = max(xmaxs) + 0.18
    for ax in axes:
        ax.set_xlim(xmin, xmax)

    fig.suptitle(
        "Baseline standardized coefficients across EV charger outcomes",
        fontsize=16,
        y=0.985,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.04,
        "Open circles indicate p < 0.05; horizontal lines show 95% confidence intervals.",
        ha="center",
        fontsize=9.5,
        color=MUTED,
    )
    fig.tight_layout(rect=[0.03, 0.065, 0.985, 0.955])
    _finish_figure(fig, save_path)
    return fig


def sync_site_figure(src: str | Path, site_fig_dir: str | Path) -> Path:
    src = Path(src)
    site_fig_dir = Path(site_fig_dir)
    site_fig_dir.mkdir(parents=True, exist_ok=True)
    dst = site_fig_dir / src.name
    dst.write_bytes(src.read_bytes())
    svg_src = src.with_suffix(".svg")
    if svg_src.exists():
        (site_fig_dir / svg_src.name).write_bytes(svg_src.read_bytes())
    return dst


def sync_site_tree(src_dir: str | Path, site_dir: str | Path, patterns: Iterable[str] = ("*.png", "*.svg")) -> list[Path]:
    src_dir = Path(src_dir)
    site_dir = Path(site_dir)
    site_dir.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for pattern in patterns:
        for src in sorted(src_dir.glob(pattern)):
            dst = site_dir / src.name
            dst.write_bytes(src.read_bytes())
            copied.append(dst)
    return copied
