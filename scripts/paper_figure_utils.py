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
    "pct_single_family_units": "% single-family units",
    "pct_multifamily_units": "% multifamily units",
    "pct_mobile_home_units": "% mobile-home units",
    "pct_other_housing_units": "% boat/RV/van/other units",
    "owner_occupied_rate": "% owner-occupied",
    "cdd65_2023": "Cooling degree days",
    "hdd65_2023": "Heating degree days",
    "ghi_mean_kwh_m2_day_2023": "Solar irradiance (GHI)",
    "wind_ws10m_mean_2023": "Wind speed (10m)",
    "wind_ws50m_mean_2023": "Wind speed (50m)",
    "log_kwh": "Log annual electricity demand",
    "y_pv": "Solar PV adoption",
    "y_storage": "Storage deployment",
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
    "log_median_household_income": "#0072B2",
    "pct_black": "#7A3E9D",
    "pct_hispanic": "#E69F00",
    "pct_asian": "#009E73",
    # Was #D55E00 (vermillion), which sits in the same hue range as % Hispanic
    # (#E69F00) - the pair a reviewer flagged as indistinguishable, and the two whose
    # divergence carries the EV-charging argument. Achromatic, so it cannot collide
    # with any hue under colour-vision deficiency (deltaE 33 -> 48 vs its nearest).
    "poverty_rate": "#333333",
    "pct_single_family_units": "#2F6F4E",
    "pct_multifamily_units": "#5B6C99",
    "pct_mobile_home_units": "#A15C38",
    "pct_other_housing_units": "#9B59B6",
    "owner_occupied_rate": "#1B7F79",
    "ghi_mean_kwh_m2_day_2023": "#D97706",
    "cdd65_2023": "#DC2626",
    "hdd65_2023": "#2563EB",
    "wind_ws50m_mean_2023": "#0284C7",
    "y_pv": "#8C6D1F",
    "y_storage": "#CC79A7",
    "y_chargers": "#008B8B",
}


ENERGY_BURDEN_OUTCOME_LABELS = {
    "energy_burden_pct": "Energy burden",
    "log_energy_gap_per_capita": "Log affordability gap",
}


ENERGY_BURDEN_LADDER_MODELS = [
    ("Model 1 baseline (climate controls)", "M1\nBaseline"),
    ("Model 2 (add bachelors)", "M2\n+ Education"),
    ("Model 2 (add housing value)", "M2\n+ Housing"),
    ("Model 5C clustered SEs by county", "M5C\nCounty SEs"),
    ("Model 7 (infrastructure controls, outcome-safe)", "M7\nInfrastructure"),
    ("Model 8 add demand proxy", "M8\nDemand"),
    ("Model 9A (predicting burden)", "M9A\nDER terms"),
]


# Figure background. Transparent by default, per the collaborators' preference so
# figures drop onto any page or slide background. Set FIGURE_BG=white for submission
# to a journal that requires an opaque canvas.
_BG_CHOICE = os.environ.get("FIGURE_BG", "transparent").strip().lower()
TRANSPARENT_BG = _BG_CHOICE in {"none", "transparent"}
PAPER_BG = "none" if TRANSPARENT_BG else "white"
PANEL_BG = PAPER_BG
# Face colour for "not significant" hollow markers. On a white canvas this is white so
# the marker reads as an open circle; on a transparent canvas it stays see-through.
HOLLOW_FACE = "none" if TRANSPARENT_BG else "white"
GRID = "#D9D4C7"
TEXT = "#1F2933"
MUTED = "#52606D"

SIG_NOTE = "Significance:  *** p < 0.001    ** p < 0.01    * p < 0.05    · p < 0.10"


class MissingModelError(RuntimeError):
    """A figure requires a model specification that the current tables do not contain."""


def apply_paper_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": PAPER_BG,
            "axes.facecolor": PANEL_BG,
            "savefig.facecolor": PAPER_BG,
            "savefig.transparent": TRANSPARENT_BG,
            "legend.frameon": False,
            "legend.fontsize": 9.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
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


def term_color_handles(terms: Iterable[str], labels: dict[str, str] | None = None) -> list[Line2D]:
    """Legend handles mapping each term to the colour used for it."""
    labels = labels or TERM_LABELS
    return [
        Line2D([0], [0], color=TERM_COLORS.get(t, "#374151"), lw=3, label=labels.get(t, t))
        for t in terms
    ]


def significance_marker_handles() -> list[Line2D]:
    """Legend handles for the filled/hollow marker convention used on the ladder plots."""
    return [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=MUTED,
               markeredgecolor="white", markeredgewidth=1.0, markersize=8, label="p < 0.05"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=HOLLOW_FACE,
               markeredgecolor=MUTED, markeredgewidth=1.6, markersize=8, label="p ≥ 0.05"),
    ]


def ci_handle(label: str = "95% confidence interval") -> Line2D:
    return Line2D([0], [0], color=MUTED, lw=2.6, alpha=0.45, label=label)


def add_figure_legend(fig, handles, *, ncol: int = 4, y: float = 0.015, note: str | None = None):
    """Place one shared legend along the bottom of the figure, with an optional note."""
    leg = fig.legend(
        handles=handles, loc="lower center", ncol=ncol, frameon=False,
        bbox_to_anchor=(0.5, y), handletextpad=0.7, columnspacing=1.8,
    )
    if note:
        fig.text(0.5, max(y - 0.032, 0.002), note, ha="center", va="center",
                 fontsize=9, color=MUTED)
    return leg


def _finish_figure(fig: plt.Figure, save_path: str | Path | None = None) -> None:
    if TRANSPARENT_BG:
        fig.patch.set_alpha(0)
        for ax in fig.axes:
            ax.patch.set_alpha(0)
    else:
        fig.patch.set_facecolor(PAPER_BG)
        for ax in fig.axes:
            ax.patch.set_facecolor(PANEL_BG)
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        # PNG only. Vector copies (SVG/PDF) were previously written alongside every
        # figure; they tripled the file count in outputs/ for no current consumer.
        common = dict(bbox_inches="tight", transparent=TRANSPARENT_BG, facecolor=fig.get_facecolor())
        fig.savefig(save_path, dpi=320, **common)


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
    fig.tight_layout(rect=[0.07, 0.10, 0.98, 0.985])
    add_figure_legend(
        fig,
        term_color_handles(terms_keep) + [ci_handle()],
        ncol=3,
        y=0.052,
        note=SIG_NOTE + "   (stars shown to the right of each interval)",
    )
    _finish_figure(fig, save_path)
    return fig


def _canonical_ladder_term(term: str, terms_keep: Iterable[str]) -> str:
    """Map a centered main effect back to its base term for the stability ladders.

    Centered specifications (Model 4) suffix main effects with "_c". Because the model
    is mean-centered, that coefficient is the effect at the mean of the interacting
    variable, which is the quantity the uncentered specifications report. Without this
    alias the race rows have no estimate at Model 4 and the ladder interpolates across
    the gap. Interaction terms keep their own names and are never plotted as main effects.
    """
    if ":" in term:
        return term
    if term.endswith("_c") and term[:-2] in set(terms_keep):
        return term[:-2]
    return term


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
    ].copy()
    sub["term"] = sub["term"].map(lambda t: _canonical_ladder_term(t, terms_keep))
    sub = sub[sub["term"].isin(terms_keep)].copy()

    collisions = sub.duplicated(subset=["model", "term"]).sum()
    if collisions:
        raise ValueError(
            f"{outcome}: {collisions} model/term collisions after centering aliases; "
            "a specification reports both the centered and uncentered form of a term."
        )

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
        # Line only, no marker. The two scatters below draw a marker at every point, and a
        # marker here would sit underneath them in solid colour: on a transparent canvas
        # HOLLOW_FACE is "none", so it showed through and every point read as filled.
        ax.plot(s["x"], s["coef"], color=color, lw=2.2)
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
            facecolor=HOLLOW_FACE,
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
    # No figure-level title: the caption carries it. Per-panel titles are kept
    # elsewhere because a caption cannot label individual panels.
    fig.tight_layout(rect=[0.08, 0.10, 0.985, 0.985])
    add_figure_legend(
        fig,
        significance_marker_handles() + [ci_handle("95% CI band")],
        ncol=3,
        y=0.038,
        note=SIG_NOTE,
    )
    _finish_figure(fig, save_path)
    return fig


def plot_energy_burden_der_m9_from_csvs(
    all_coefs: pd.DataFrame,
    save_path: str | Path | None = None,
) -> plt.Figure:
    apply_paper_style()
    outcomes = list(ENERGY_BURDEN_OUTCOME_LABELS)
    terms_keep = ["y_pv", "y_storage", "y_chargers"]
    model = "Model 9A (predicting burden)"
    # This figure needs a model the current notebook does not emit. It used to be drawn
    # from an orphaned table left over from an older notebook version, which meant it
    # displayed results that could not be reproduced. Fail with an actionable message
    # rather than silently rendering an empty or stale panel.
    if not (all_coefs["model"] == model).any():
        raise MissingModelError(
            f'"{model}" is not present in the coefficient tables. No current code path '
            "produces it (see outputs/archive/orphans/). Either restore that "
            "specification in regression.ipynb or drop this figure."
        )

    fig, axes = plt.subplots(len(outcomes), 1, figsize=(9.8, 6.8))
    if len(outcomes) == 1:
        axes = [axes]

    for ax, outcome in zip(axes, outcomes):
        sub = all_coefs[
            (all_coefs["outcome"] == outcome)
            & (all_coefs["model"] == model)
            & (all_coefs["term"].isin(terms_keep))
        ].copy()
        sub["term"] = pd.Categorical(sub["term"], categories=terms_keep, ordered=True)
        sub = sub.sort_values("term")
        y = np.arange(len(sub))[::-1]

        xmins: list[float] = []
        xmaxs: list[float] = []
        for yi, (_, row) in zip(y, sub.iterrows()):
            color = TERM_COLORS.get(row["term"], "#374151")
            ax.hlines(yi, row["conf_low"], row["conf_high"], color=color, lw=2.7, alpha=0.95)
            ax.plot(row["coef"], yi, "o", color=color, ms=8, mec="white", mew=0.9, zorder=3)
            if row["stars"]:
                span = max(float(row["conf_high"] - row["conf_low"]), 1e-9)
                ax.text(
                    row["conf_high"] + span * 0.08,
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

        margin = max((max(xmaxs) - min(xmins)) * 0.16, 1e-6)
        ax.set_xlim(min(xmins) - margin, max(xmaxs) + margin)
        ax.axvline(0, linestyle="--", linewidth=1.2, color=MUTED, alpha=0.9)
        ax.grid(axis="x", linestyle="-", linewidth=0.7)
        ax.set_yticks(y)
        ax.set_yticklabels([TERM_LABELS.get(t, t) for t in sub["term"]])
        ax.set_title(ENERGY_BURDEN_OUTCOME_LABELS[outcome], loc="left", fontweight="bold", pad=8)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(GRID)

    axes[-1].set_xlabel("Coefficient estimate")
    fig.tight_layout(rect=[0.08, 0.13, 0.98, 0.98])
    add_figure_legend(
        fig,
        term_color_handles(terms_keep) + [ci_handle()],
        ncol=4,
        y=0.058,
        note=SIG_NOTE,
    )
    _finish_figure(fig, save_path)
    return fig


def plot_energy_burden_model_ladder_from_csvs(
    all_coefs: pd.DataFrame,
    save_path: str | Path | None = None,
) -> plt.Figure:
    apply_paper_style()
    outcomes = list(ENERGY_BURDEN_OUTCOME_LABELS)
    # Restrict the ladder to specifications that actually exist in the tables. The
    # configured list still names "Model 9A (predicting burden)", which no current code
    # path emits; keeping it would add an empty rung to the figure.
    available = set(all_coefs["model"].unique())
    ladder = [(m, l) for m, l in ENERGY_BURDEN_LADDER_MODELS if m in available]
    dropped = [m for m, _ in ENERGY_BURDEN_LADDER_MODELS if m not in available]
    if dropped:
        print(f"    note: energy-burden ladder skipping absent specification(s): {dropped}")
    if not ladder:
        raise MissingModelError("No energy-burden ladder specifications found in the tables.")
    models_keep = [model for model, _ in ladder]
    model_labels = [label for _, label in ladder]
    terms_keep = [
        "log_median_household_income",
        "poverty_rate",
        "pct_black",
        "pct_hispanic",
        "pct_asian",
        "y_pv",
        "y_storage",
        "y_chargers",
    ]

    sub = all_coefs[
        (all_coefs["outcome"].isin(outcomes))
        & (all_coefs["model"].isin(models_keep))
        & (all_coefs["term"].isin(terms_keep))
    ].copy()
    sub["model"] = pd.Categorical(sub["model"], categories=models_keep, ordered=True)
    sub["term"] = pd.Categorical(sub["term"], categories=terms_keep, ordered=True)

    fig, axes = plt.subplots(len(outcomes), 1, figsize=(12.4, 8.2), sharex=True)
    if len(outcomes) == 1:
        axes = [axes]
    x = np.arange(len(models_keep))
    model_to_x = {model: idx for idx, model in enumerate(models_keep)}

    for ax, outcome in zip(axes, outcomes):
        outcome_sub = sub[sub["outcome"] == outcome].copy()
        for term in terms_keep:
            s = outcome_sub[outcome_sub["term"] == term].copy().sort_values("model")
            if s.empty:
                continue
            s["x"] = s["model"].map(model_to_x).astype(float)
            color = TERM_COLORS.get(term, "#374151")
            ax.vlines(s["x"], s["conf_low"], s["conf_high"], color=color, alpha=0.22, linewidth=2)
            # Line only; see the note in plot_stability_from_csvs. A solid marker here
            # showed through the transparent face of the "not significant" scatter.
            ax.plot(s["x"], s["coef"], color=color, lw=2.1, label=TERM_LABELS.get(term, term))
            sig = s["pval"] < 0.05
            ax.scatter(s.loc[sig, "x"], s.loc[sig, "coef"], s=60, facecolor=color, edgecolor="white", linewidth=1, zorder=4)
            ax.scatter(
                s.loc[~sig, "x"],
                s.loc[~sig, "coef"],
                s=60,
                facecolor=HOLLOW_FACE,
                edgecolor=color,
                linewidth=1.5,
                zorder=4,
            )

        ax.axhline(0, linestyle="--", linewidth=1.1, color=MUTED, alpha=0.9)
        ax.grid(axis="y", linestyle="-", linewidth=0.7)
        ax.set_title(ENERGY_BURDEN_OUTCOME_LABELS[outcome], loc="left", fontweight="bold", pad=8)
        ax.set_ylabel("Coefficient estimate")
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(model_labels)
    axes[-1].set_xlabel("Specification")
    fig.tight_layout(rect=[0.055, 0.17, 0.985, 0.985])
    handles, labels = axes[0].get_legend_handles_labels()
    seen: set[str] = set()
    uniq = [h for h, l in zip(handles, labels) if not (l in seen or seen.add(l))]
    add_figure_legend(
        fig,
        uniq + significance_marker_handles(),
        ncol=5,
        y=0.075,
        note=SIG_NOTE,
    )
    _finish_figure(fig, save_path)
    return fig


def plot_housing_structure_attenuation(
    all_coefs: pd.DataFrame,
    outcomes: dict[str, str] | None = None,
    race_terms: Iterable[str] = ("pct_black", "pct_hispanic", "pct_asian"),
    baseline_model: str = "Model 1 baseline (climate controls)",
    structure_model: str = "Model 2D (add housing structure and tenure)",
    save_path: str | Path | None = None,
) -> plt.Figure:
    """Race coefficients before and after adding housing-structure controls.

    This is the identification check the project's review memo called the highest-value
    revision: rooftop PV and home storage require a roof and a unit you control, and
    housing structure is correlated with race independently of income. Showing the
    before/after pair makes plain how much of each race coefficient is housing
    composition and how much survives it.
    """
    apply_paper_style()
    outcomes = outcomes or {"y_pv": "Solar PV", "y_storage": "Storage", "y_chargers": "EV Chargers"}
    race_terms = list(race_terms)

    fig, axes = plt.subplots(1, len(outcomes), figsize=(13.4, 5.4), sharey=True)
    if len(outcomes) == 1:
        axes = [axes]

    offset = 0.17
    for ax, (outcome, label) in zip(axes, outcomes.items()):
        for i, term in enumerate(race_terms):
            y0 = len(race_terms) - 1 - i
            color = TERM_COLORS.get(term, "#374151")
            for model, dy, filled in ((baseline_model, offset, False), (structure_model, -offset, True)):
                row = all_coefs[
                    (all_coefs["outcome"] == outcome)
                    & (all_coefs["model"] == model)
                    & (all_coefs["term"] == term)
                ]
                if row.empty:
                    continue
                r = row.iloc[0]
                ax.hlines(y0 + dy, r["conf_low"], r["conf_high"], color=color, lw=2.4, alpha=0.9)
                ax.plot(
                    r["coef"], y0 + dy, "o", ms=8,
                    markerfacecolor=color if filled else HOLLOW_FACE,
                    markeredgecolor=color, markeredgewidth=1.7, zorder=3,
                )
                if r["stars"]:
                    ax.text(r["conf_high"], y0 + dy + 0.10, r["stars"], fontsize=9,
                            ha="left", va="bottom", color=TEXT, fontweight="bold")

        ax.axvline(0, linestyle="--", linewidth=1.2, color=MUTED, alpha=0.9)
        ax.grid(axis="x", linestyle="-", linewidth=0.7)
        ax.set_yticks(np.arange(len(race_terms))[::-1])
        ax.set_yticklabels([TERM_LABELS.get(t, t) for t in race_terms])
        ax.set_ylim(-0.6, len(race_terms) - 0.4)
        ax.set_title(label, loc="left", color=OUTCOME_COLORS.get(outcome, TEXT), fontweight="bold", pad=8)
        ax.set_xlabel("Standardized coefficient")
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)

    fig.tight_layout(rect=[0.01, 0.16, 0.99, 0.985])
    handles = [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=HOLLOW_FACE,
               markeredgecolor=MUTED, markeredgewidth=1.7, markersize=8,
               label=f"Baseline ({baseline_model.split(' (')[0]})"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=MUTED,
               markeredgecolor=MUTED, markersize=8, label="+ structure & tenure (Model 2D)"),
        ci_handle(),
    ]
    add_figure_legend(
        fig, handles, ncol=3, y=0.075,
        note=SIG_NOTE + "   ·   exhaustive structure shares vs single-family; tenure is owner share (renters omitted)",
    )
    _finish_figure(fig, save_path)
    return fig


def plot_housing_structure_across_outcomes(
    all_coefs: pd.DataFrame,
    outcomes: dict[str, str] | None = None,
    housing_terms: Iterable[str] = (
        "pct_multifamily_units",
        "pct_mobile_home_units",
        "pct_other_housing_units",
        "owner_occupied_rate",
    ),
    model: str = "Model 2D (add housing structure and tenure)",
    save_path: str | Path | None = None,
) -> plt.Figure:
    """Housing-structure coefficients across every outcome.

    The housing shares enter Model 2C and Model 2D, so their cross-outcome pattern is
    more informative than isolated points inside the main robustness panels.
    """
    apply_paper_style()
    outcomes = outcomes or {
        "y_pv": "Solar PV",
        "y_storage": "Storage",
        "y_chargers": "EV Chargers (all)",
        "y_level2_chargers": "EV Chargers (Level 2)",
        "y_dc_fast_chargers": "EV Chargers (DC fast)",
        "any_turbines": "Any turbines",
    }
    housing_terms = list(housing_terms)

    rows = list(outcomes.items())
    fig, ax = plt.subplots(figsize=(10.6, 0.92 * len(rows) + 3.0))
    spread = 0.19

    for i, (outcome, label) in enumerate(rows):
        y0 = len(rows) - 1 - i
        for k, term in enumerate(housing_terms):
            dy = spread * (len(housing_terms) - 1) / 2 - k * spread
            r = all_coefs[
                (all_coefs["outcome"] == outcome)
                & (all_coefs["model"] == model)
                & (all_coefs["term"] == term)
            ]
            if r.empty:
                continue
            r = r.iloc[0]
            color = TERM_COLORS.get(term, "#374151")
            ax.hlines(y0 + dy, r["conf_low"], r["conf_high"], color=color, lw=2.5, alpha=0.9)
            sig = pd.notna(r["pval"]) and r["pval"] < 0.05
            ax.plot(r["coef"], y0 + dy, "o", ms=8.2, zorder=3,
                    markerfacecolor=color if sig else HOLLOW_FACE,
                    markeredgecolor=color, markeredgewidth=1.7)
            if r["stars"]:
                ax.text(r["conf_high"], y0 + dy + 0.09, r["stars"], fontsize=9,
                        ha="left", va="bottom", color=TEXT, fontweight="bold")

    ax.axvline(0, linestyle="--", linewidth=1.2, color=MUTED, alpha=0.9)
    ax.grid(axis="x", linestyle="-", linewidth=0.7)
    ax.set_yticks(np.arange(len(rows))[::-1])
    ax.set_yticklabels([label for _, label in rows])
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("Standardized coefficient")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)

    fig.tight_layout(rect=[0.01, 0.13, 0.99, 0.985])
    add_figure_legend(
        fig,
        term_color_handles(housing_terms) + significance_marker_handles() + [ci_handle()],
        ncol=4,
        y=0.055,
        note=SIG_NOTE + "   ·   structure shares vs single-family; tenure is owner share vs renter",
    )
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

    # Single-axes figure, so its axes title was the figure's overall title. Removed;
    # the column headers already identify each outcome and specification.
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)

    fig.tight_layout(rect=[0.02, 0.07, 0.985, 0.985])
    # The colourbar encodes magnitude; the cell annotations encode significance, so the
    # star convention still needs stating explicitly.
    fig.text(0.5, 0.028, SIG_NOTE + "   ·   cell values are standardized coefficients",
             ha="center", va="center", fontsize=9.5, color=MUTED)
    _finish_figure(fig, save_path)
    return fig


def plot_charger_subtype_comparison(
    table_dir: str | Path,
    save_path: str | Path | None = None,
) -> plt.Figure:
    apply_paper_style()
    table_dir = Path(table_dir)
    files = {
        "Aggregate chargers": table_dir / "y_chargers | Model 1 baseline (climate controls).csv",
        "Level 1 chargers": table_dir / "y_level1_chargers | Model 1 baseline (climate controls).csv",
        "Level 2 chargers": table_dir / "y_level2_chargers | Model 1 baseline (climate controls).csv",
        "DC fast chargers": table_dir / "y_dc_fast_chargers | Model 1 baseline (climate controls).csv",
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
            # Same convention as the coefficient ladders: filled means p < 0.05, hollow
            # means p >= 0.05. This figure previously filled every marker and added an
            # outer ring for significance, which read as the opposite of the ladders.
            # Draw one marker only, so a hollow face is not backed by a solid one.
            if row["pval"] < 0.05:
                ax.plot(row["coef"], yi, "o", ms=7.3, mfc=color, mec="white", mew=0.9)
            else:
                ax.plot(row["coef"], yi, "o", ms=7.3, mfc=HOLLOW_FACE, mec=color, mew=1.6)
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
    for ax in axes[2:]:
        ax.set_xlabel("Standardized coefficient estimate")

    fig.tight_layout(rect=[0.03, 0.13, 0.985, 0.985])
    add_figure_legend(
        fig,
        term_color_handles(var_order) + [ci_handle()] + significance_marker_handles(),
        ncol=4,
        y=0.058,
        note=SIG_NOTE,
    )
    _finish_figure(fig, save_path)
    return fig


def sync_site_figure(src: str | Path, site_fig_dir: str | Path) -> Path:
    src = Path(src)
    site_fig_dir = Path(site_fig_dir)
    site_fig_dir.mkdir(parents=True, exist_ok=True)
    dst = site_fig_dir / src.name
    dst.write_bytes(src.read_bytes())
    return dst


def sync_site_tree(src_dir: str | Path, site_dir: str | Path, patterns: Iterable[str] = ("*.png",)) -> list[Path]:
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
