#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from paper_figure_utils import (
    OUTCOME_DISPLAY,
    load_all_coefs,
    plot_charger_subtype_comparison,
    plot_dot_whisker_from_csvs,
    plot_heatmap_from_csvs,
    plot_stability_from_csvs,
    sync_site_figure,
)


ROOT = Path(__file__).resolve().parents[1]
TAB_DIR = ROOT / "outputs" / "standardized_tables"
FIG_DIR = ROOT / "outputs" / "standardized_figures"
SITE_FIG_DIR = ROOT / "site" / "assets" / "figures"


PAPER_MAIN_MODELS = {
    "y_pv": "Model 1 baseline (climate controls)",
    "y_chargers": "Model 1 baseline (climate controls)",
    "y_storage": "Model 1 baseline (climate controls)",
    "y_wind_mw": "Model 1 baseline (climate controls)",
    "any_turbines": "Model 1 baseline (climate controls)",
}

PAPER_ROBUSTNESS_MODELS = [
    "Model 1 baseline (climate controls)",
    "Model 2 (add bachelors)",
    "Model 2 (add housing value)",
    "Model 4 interactions (centered)",
    "Model 5C clustered SEs by county",
    "Model 7 (infrastructure controls, outcome-safe)",
    "Model 8 add demand proxy",
]

TERMS_MAIN = [
    "log_median_household_income",
    "pct_black",
    "pct_hispanic",
    "pct_asian",
    "poverty_rate",
]

HEATMAP_OUTCOMES = ["y_pv", "y_chargers", "y_storage", "y_wind_mw", "any_turbines"]
HEATMAP_MODELS = ["Model 1 baseline (climate controls)"]
TERMS_HEATMAP = TERMS_MAIN

ROBUSTNESS_TERMS_BY_OUTCOME = {
    "y_pv": [
        "log_median_household_income",
        "pct_black",
        "pct_hispanic",
        "poverty_rate",
        "ghi_mean_kwh_m2_day_2023",
    ],
    "y_chargers": [
        "log_median_household_income",
        "pct_black",
        "pct_hispanic",
        "poverty_rate",
        "cdd65_2023",
        "hdd65_2023",
    ],
    "y_storage": [
        "log_median_household_income",
        "pct_black",
        "pct_hispanic",
        "poverty_rate",
        "cdd65_2023",
        "hdd65_2023",
    ],
    "y_wind_mw": [
        "log_median_household_income",
        "pct_black",
        "pct_hispanic",
        "poverty_rate",
        "wind_ws50m_mean_2023",
    ],
    "any_turbines": [
        "log_median_household_income",
        "pct_black",
        "pct_hispanic",
        "poverty_rate",
        "wind_ws50m_mean_2023",
    ],
}


def main() -> None:
    all_coefs = load_all_coefs(TAB_DIR)

    generated = []

    generated.append(
        FIG_DIR / "main_dot_whisker_across_outcomes.png"
    )
    plot_dot_whisker_from_csvs(
        all_coefs=all_coefs,
        main_models=PAPER_MAIN_MODELS,
        terms_keep=TERMS_MAIN,
        outcome_display=OUTCOME_DISPLAY,
        save_path=generated[-1],
    )

    for outcome in HEATMAP_OUTCOMES:
        save_path = FIG_DIR / f"{outcome}_robustness.png"
        plot_stability_from_csvs(
            all_coefs=all_coefs,
            outcome=outcome,
            models_keep=PAPER_ROBUSTNESS_MODELS,
            terms_keep=ROBUSTNESS_TERMS_BY_OUTCOME[outcome],
            outcome_display=OUTCOME_DISPLAY,
            save_path=save_path,
        )
        generated.append(save_path)

    heatmap_path = FIG_DIR / "coef_heatmap_appendix.png"
    plot_heatmap_from_csvs(
        all_coefs=all_coefs,
        outcomes_keep=HEATMAP_OUTCOMES,
        models_keep=HEATMAP_MODELS,
        terms_keep=TERMS_HEATMAP,
        outcome_display=OUTCOME_DISPLAY,
        save_path=heatmap_path,
    )
    generated.append(heatmap_path)

    subtype_path = FIG_DIR / "charger_subtype_comparison.png"
    plot_charger_subtype_comparison(TAB_DIR, save_path=subtype_path)
    generated.append(subtype_path)

    for path in generated:
        sync_site_figure(path, SITE_FIG_DIR)

    print("Regenerated paper-style figures:")
    for path in generated:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
