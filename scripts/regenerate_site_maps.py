#!/usr/bin/env python3
"""Regenerate the three spatial maps that the site's geography panel embeds.

Why this script exists
----------------------
`build_site_index_assets.build_geography_panel()` composites three PNGs from
`outputs/figures/{pv,storage,chargers}_maps/`. Those files were last written in March
2026 and **no current code path produces them**: `regression.ipynb` still defines
`make_paper_spatial_figure(...)` and still sets `RUN_MAPS = False`, but nothing reads
that flag and nothing calls that function — the calling code was removed at some point.
The result was a freshly regenerated composite figure embedding stale images built from
the pre-audit dataset.

This script renders just those three, from the current analysis dataset, using the
Model 1 baseline specification.

Drift guard
-----------
The model is refit here rather than imported from the notebook, so it could silently
diverge from the notebook's Model 1. To prevent that, every fit is checked against the
exported `outputs/standardized_tables/{outcome} | Model 1 baseline (climate
controls).csv`; a mismatch beyond tolerance aborts instead of writing a wrong map.

Usage
-----
    python scripts/regenerate_site_maps.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.append(str(Path(__file__).resolve().parent))
from paper_figure_utils import GRID, MUTED, TEXT, TRANSPARENT_BG, apply_paper_style  # noqa: E402
from model_helpers import pv_kw_per_1000  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_CSV = ROOT / "data" / "processed" / "combined_der_dataset_w_controls_predictors.csv"
ZCTA_SHP = ROOT / "data" / "raw" / "boundaries" / "tl_2023_us_zcta520" / "tl_2023_us_zcta520.shp"
COUNTY_SHP = ROOT / "data" / "raw" / "boundaries" / "tl_2023_us_county" / "tl_2023_us_county.shp"
TAB_DIR = ROOT / "outputs" / "standardized_tables"
FIG_ROOT = ROOT / "outputs" / "figures"

MIN_POP = 1000
CORE_NEEDED = ["median_household_income", "pct_black", "pct_hispanic", "pct_asian"]

# Must mirror regression.ipynb: income + race + poverty + outcome-specific climate.
INCOME = "log_median_household_income"
RACE = ["pct_black", "pct_hispanic", "pct_asian"]
COMMON = ["poverty_rate"]

TARGETS = {
    "y_pv": dict(
        climate=["ghi_mean_kwh_m2_day_2023"],
        out=FIG_ROOT / "pv_maps" / "y_pv_model_1_baseline_climate_controls_spatial_figure.png",
        label="Solar PV adoption",
    ),
    "y_storage": dict(
        climate=["cdd65_2023", "hdd65_2023"],
        out=FIG_ROOT / "storage_maps" / "y_storage_model_1_baseline_climate_controls_spatial_figure.png",
        label="Storage deployment",
    ),
    "y_chargers": dict(
        climate=["cdd65_2023", "hdd65_2023"],
        out=FIG_ROOT / "chargers_maps" / "y_chargers_model_1_baseline_climate_controls_spatial_figure.png",
        label="EV charger availability",
    ),
}


def build_analysis_frame() -> pd.DataFrame:
    df = pd.read_csv(ANALYSIS_CSV, low_memory=False)
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    df["zip_code"] = df["zip_code"].map(lambda v: pd.NA if pd.isna(v) else str(int(float(v))).zfill(5))

    zero_cols = ["PV_system_size_DC", "total_chargers", "storage_capacity_mw"]
    for c in zero_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["total_population"] = pd.to_numeric(df["total_population"], errors="coerce")
    df = df[df["total_population"].notna() & (df["total_population"] >= MIN_POP)].copy()

    pop = df["total_population"].replace(0, np.nan)
    df["y_pv"] = np.log1p(pv_kw_per_1000(df["PV_system_size_DC"], pop))
    df["y_chargers"] = np.log1p(df["total_chargers"] * 1000 / pop)
    df["y_storage"] = np.log1p(df["storage_capacity_mw"] * 100000 / pop)
    df[INCOME] = np.log(df["median_household_income"].where(df["median_household_income"] > 0))

    return df.dropna(subset=[c for c in CORE_NEEDED if c in df.columns]).copy()


def verify_against_exported(outcome: str, res) -> None:
    """Abort if this refit disagrees with the notebook's exported Model 1 table."""
    path = TAB_DIR / f"{outcome} | Model 1 baseline (climate controls).csv"
    if not path.exists():
        raise SystemExit(f"Cannot verify {outcome}: missing {path}. Run the models stage first.")
    exported = pd.read_csv(path, index_col=0)

    # The exported table is from the standardized run (predictors z-scored, outcome raw),
    # so coefficients differ by each predictor's SD. Compare t-statistics instead: they
    # are invariant to linear rescaling of a predictor.
    exp_coef, exp_se = exported["Coef."], exported["Std.Err."]
    exp_t = (exp_coef / exp_se).drop(labels=["Intercept"], errors="ignore")
    got_t = (res.params / res.bse).drop(labels=["Intercept"], errors="ignore")

    shared = [t for t in exp_t.index if t in got_t.index]
    if len(shared) < len(exp_t):
        raise SystemExit(
            f"{outcome}: term mismatch vs exported Model 1.\n"
            f"  exported: {sorted(exp_t.index)}\n  refit:    {sorted(got_t.index)}"
        )
    diff = (exp_t[shared] - got_t[shared]).abs().max()
    if diff > 0.01:
        raise SystemExit(
            f"{outcome}: refit disagrees with exported Model 1 (max |t| difference {diff:.4f}). "
            "The map spec has drifted from the notebook; fix before writing a misleading map."
        )
    print(f"    spec check OK (max |t| difference vs exported table: {diff:.2e})")


def render_map(df: pd.DataFrame, zips: gpd.GeoDataFrame, ca_outline, outcome: str, cfg: dict) -> None:
    formula = f"{outcome} ~ " + " + ".join([INCOME] + RACE + COMMON + cfg["climate"])
    res = smf.ols(formula, data=df).fit(cov_type="HC1")
    print(f"  {outcome}: N = {int(res.nobs)}, R2 = {res.rsquared:.4f}")
    verify_against_exported(outcome, res)

    used = df.loc[res.model.data.row_labels].copy()
    used["residual"] = res.resid
    used["std_residual"] = res.resid / res.resid.std(ddof=1)

    merged = zips.merge(used[["zip_code", outcome, "std_residual"]], on="zip_code", how="left")

    apply_paper_style()
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    vmax = float(np.nanpercentile(merged["std_residual"].abs(), 99)) or 1.0

    for ax, (col, cmap, title, kw) in zip(
        axes,
        [
            (outcome, "viridis", f"{cfg['label']}: observed", {}),
            ("std_residual", "coolwarm", f"{cfg['label']}: Model 1 standardized residuals",
             dict(vmin=-vmax, vmax=vmax)),
        ],
    ):
        merged.plot(column=col, cmap=cmap, linewidth=0.1, edgecolor="white", legend=True,
                    ax=ax, missing_kwds={"color": "lightgray", "label": "No data"}, **kw)
        ca_outline.plot(ax=ax, facecolor="none", edgecolor=TEXT, linewidth=1.2, zorder=10)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=8, color=TEXT)
        ax.axis("off")

    fig.text(0.5, 0.02, f"ZIP-level, N = {int(res.nobs)}. Grey = outside the analysis sample.",
             ha="center", fontsize=9, color=MUTED)
    fig.tight_layout(rect=[0, 0.04, 1, 1])

    cfg["out"].parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(cfg["out"], dpi=300, bbox_inches="tight", transparent=TRANSPARENT_BG,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"    wrote {cfg['out'].relative_to(ROOT)}")


def main() -> None:
    df = build_analysis_frame()
    print(f"Analysis sample: {len(df)} ZIPs")

    zips = gpd.read_file(ZCTA_SHP)
    zips["zip_code"] = zips["ZCTA5CE20"].astype(str).str.zfill(5)
    zips = zips[zips["zip_code"].isin(set(df["zip_code"].dropna()))][["zip_code", "geometry"]].copy()

    county = gpd.read_file(COUNTY_SHP)
    ca_outline = county[county["STATEFP"] == "06"].to_crs(zips.crs).dissolve()

    for outcome, cfg in TARGETS.items():
        render_map(df, zips, ca_outline, outcome, cfg)

    print("\nDone. Rerun scripts/build_site_index_assets.py to rebuild the geography panel.")


if __name__ == "__main__":
    main()
