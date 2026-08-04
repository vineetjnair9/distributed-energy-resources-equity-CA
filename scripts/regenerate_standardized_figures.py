#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from paper_figure_utils import (
    OUTCOME_DISPLAY,
    MissingModelError,
    load_all_coefs,
    plot_charger_subtype_comparison,
    plot_dot_whisker_from_csvs,
    plot_energy_burden_der_m9_from_csvs,
    plot_energy_burden_model_ladder_from_csvs,
    plot_heatmap_from_csvs,
    plot_housing_structure_across_outcomes,
    plot_housing_structure_attenuation,
    plot_stability_from_csvs,
    sync_site_figure,
)


ROOT = Path(__file__).resolve().parents[1]
TAB_DIR = ROOT / "outputs" / "standardized_tables"
FIG_DIR = ROOT / "outputs" / "standardized_figures"
SITE_FIG_DIR = ROOT / "site" / "assets" / "figures"


# any_turbines is deliberately absent here and from HEATMAP_OUTCOMES. It is a linear
# probability model, so its coefficients are on a probability scale (~0.01-0.03) while
# every other outcome is log1p-scaled (~0.1-0.4). Sharing an x-axis or a diverging
# colour scale across those units makes the binary panel unreadable and the comparison
# meaningless. It keeps its own robustness figure instead.
PAPER_MAIN_MODELS = {
    "y_pv": "Model 1 baseline (climate controls)",
    "y_chargers": "Model 1 baseline (climate controls)",
    "y_storage": "Model 1 baseline (climate controls)",
    "y_wind_mw": "Model 1 baseline (climate controls)",
}

PAPER_ROBUSTNESS_MODELS = [
    "Model 1 baseline (climate controls)",
    "Model 2 (add bachelors)",
    "Model 2 (add housing value)",
    "Model 2C (add housing structure)",
    "Model 2D (add housing structure and tenure)",
    "Model 4 interactions (centered)",
    "Model 5C clustered SEs by county",
    "Model 7 (infrastructure controls, outcome-safe)",
    "Model 8 add demand proxy",
]

ROBUSTNESS_MODELS_BY_OUTCOME = {
    "y_storage": PAPER_ROBUSTNESS_MODELS + ["Model 9 + pv control (most controlled)"],
}

TERMS_MAIN = [
    "log_median_household_income",
    "pct_black",
    "pct_hispanic",
    "pct_asian",
    "poverty_rate",
]

HEATMAP_OUTCOMES = ["y_pv", "y_chargers", "y_storage", "y_wind_mw"]
ROBUSTNESS_OUTCOMES = HEATMAP_OUTCOMES + ["any_turbines"]
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
# Note: the housing-structure shares are intentionally absent from every list above.
# They enter only in Model 2C, so a "stability across specifications" panel for them
# would be a single point in an otherwise empty row. They get their own dedicated
# before/after figure instead (plot_housing_structure_attenuation).


def main() -> None:
    all_coefs = load_all_coefs(TAB_DIR)

    generated = []
    skipped: list[str] = []

    generated.append(
        FIG_DIR / "baseline_der_outcomes_dot_whisker.png"
    )
    plot_dot_whisker_from_csvs(
        all_coefs=all_coefs,
        main_models=PAPER_MAIN_MODELS,
        terms_keep=TERMS_MAIN,
        outcome_display=OUTCOME_DISPLAY,
        save_path=generated[-1],
    )

    for outcome in ROBUSTNESS_OUTCOMES:
        save_path = FIG_DIR / f"{outcome}_robustness.png"
        plot_stability_from_csvs(
            all_coefs=all_coefs,
            outcome=outcome,
            models_keep=ROBUSTNESS_MODELS_BY_OUTCOME.get(outcome, PAPER_ROBUSTNESS_MODELS),
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

    housing_path = FIG_DIR / "housing_structure_attenuation.png"
    plot_housing_structure_attenuation(all_coefs=all_coefs, save_path=housing_path)
    generated.append(housing_path)

    housing_across_path = FIG_DIR / "housing_structure_across_outcomes.png"
    plot_housing_structure_across_outcomes(all_coefs=all_coefs, save_path=housing_across_path)
    generated.append(housing_across_path)

    subtype_path = FIG_DIR / "charger_subtype_comparison.png"
    plot_charger_subtype_comparison(TAB_DIR, save_path=subtype_path)
    generated.append(subtype_path)

    burden_der_path = FIG_DIR / "energy_burden_der_m9.png"
    try:
        plot_energy_burden_der_m9_from_csvs(all_coefs=all_coefs, save_path=burden_der_path)
        generated.append(burden_der_path)
    except MissingModelError as exc:
        # Skip loudly rather than aborting the whole figure run or emitting a stale panel.
        skipped.append(f"energy_burden_der_m9.png: {exc}")

    burden_ladder_path = FIG_DIR / "energy_burden_model_ladder.png"
    plot_energy_burden_model_ladder_from_csvs(all_coefs=all_coefs, save_path=burden_ladder_path)
    generated.append(burden_ladder_path)

    for path in generated:
        sync_site_figure(path, SITE_FIG_DIR)

    print("Regenerated paper-style figures:")
    for path in generated:
        print(path.relative_to(ROOT))
    if skipped:
        print("\nSKIPPED (not silently - these need a decision):")
        for msg in skipped:
            print(f"  - {msg}")


if __name__ == "__main__":
    main()
