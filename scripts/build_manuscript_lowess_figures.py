#!/usr/bin/env python3
"""Rebuild only the LOWESS small-multiple figures on an opaque white canvas.

Journals expect an opaque background: a transparent PNG leaves compositing to the
renderer, which can come out black in some PDF/print pipelines. The project default
is FIGURE_BG=transparent so figures drop onto any slide or web background, and this
script leaves that default -- and every existing figure under outputs/figures/generated
and site/assets/figures/generated -- untouched. It writes white copies to
outputs/figures/manuscript/ for submission only.

Usage:  python scripts/build_manuscript_lowess_figures.py
"""
from __future__ import annotations

import os
from pathlib import Path

# Must precede the imports below: paper_figure_utils reads FIGURE_BG at import time.
os.environ["FIGURE_BG"] = "white"

import build_site_index_assets as B  # noqa: E402

MANUSCRIPT_DIR = Path(B.ROOT) / "outputs" / "figures" / "manuscript"


def main() -> None:
    assert not B.TRANSPARENT_BG, "FIGURE_BG did not take effect; figures would be transparent"

    B._OUTPUT_DIR_OVERRIDE = MANUSCRIPT_DIR
    try:
        df = B.derive_analysis_frame()
        B.build_income_small_multiples(df)
        B.build_predictor_lowess_small_multiples(
            df,
            x_col="combined_nonwhite_share",
            x_label="Combined non-white share",
            title="Descriptive DER gradients by combined non-white share",
            subtitle="Curves are deterministic LOWESS fits with seeded bootstrap 95% confidence intervals.",
            output_name="nonwhite_lowess_small_multiples.png",
            metrics_name="nonwhite_lowess_small_multiples_metrics.csv",
        )
        B.build_predictor_lowess_small_multiples(
            df,
            x_col="pct_bachelors_plus",
            x_label="Adults with bachelor's degree or higher",
            title="Descriptive DER gradients by educational attainment",
            subtitle="Curves are deterministic LOWESS fits with seeded bootstrap 95% confidence intervals.",
            output_name="education_lowess_small_multiples.png",
            metrics_name="education_lowess_small_multiples_metrics.csv",
        )
        # Same guard as build_all(): the single-family column is not always populated.
        if "pct_single_family_units" in df.columns and df["pct_single_family_units"].notna().sum() >= 10:
            B.build_predictor_lowess_small_multiples(
                df,
                x_col="pct_single_family_units",
                x_label="Single-family share of housing units",
                title="Descriptive DER gradients by single-family housing share",
                subtitle="Curves are deterministic LOWESS fits with seeded bootstrap 95% confidence intervals.",
                output_name="housing_structure_lowess_small_multiples.png",
                metrics_name="housing_structure_lowess_small_multiples_metrics.csv",
            )
    finally:
        B._OUTPUT_DIR_OVERRIDE = None

    for f in sorted(MANUSCRIPT_DIR.glob("*.png")):
        print(f"wrote {f.relative_to(B.ROOT)}")


if __name__ == "__main__":
    main()
