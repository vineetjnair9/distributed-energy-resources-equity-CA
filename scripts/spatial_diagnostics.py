#!/usr/bin/env python3
"""Moran's I on model residuals — the spatial-autocorrelation check.

`site/review_memo.md` 2.5 predicts a referee will ask for this: ZIP-level DER
deployment is spatially autocorrelated at a finer scale than counties (installer
service territories, permitting jurisdictions, neighbourhood peer effects), so
county-clustered standard errors may not be enough.

Method
------
Residuals come from `data/processed/model_outputs_by_region.csv`, which the regression
notebook already exports per region per model, so nothing is refit here.

Weights are k-nearest-neighbour on ZCTA centroids (great-circle distance),
row-standardised. k-NN rather than a distance band because ZCTA density varies by two
orders of magnitude between urban and rural California, so any fixed band leaves rural
ZIPs with no neighbours. Results are reported across k to show the conclusion is not an
artefact of one choice.

Inference is a permutation test: the statistic is recomputed on `--perms` random
reassignments of the residuals to locations, and the pseudo p-value is the share of
permutations at least as extreme. With the default 999 the smallest reportable value is
0.001, which should be read as "p < 0.001" rather than as a point estimate.

Usage
-----
    python scripts/spatial_diagnostics.py
    python scripts/spatial_diagnostics.py --k 4 8 16 --perms 4999
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "processed" / "combined_der_dataset_w_controls_predictors.csv"
RESIDUALS = ROOT / "data" / "processed" / "model_outputs_by_region.csv"
OUT_CSV = ROOT / "outputs" / "tables" / "morans_i_residuals.csv"

OUTCOMES = ["y_pv", "y_storage", "y_chargers", "y_level2_chargers",
            "energy_burden_pct", "log_energy_gap_per_capita"]
MODELS = [
    ("Model 1 baseline (climate controls)", "M1 baseline"),
    ("Model 6A lat and lon", "M6A + lat/lon"),
    ("Model 6B county fe", "M6B county FE"),
    ("Model 8 add demand proxy", "M8 + demand proxy"),
]


def zip5(v):
    return pd.NA if pd.isna(v) else str(int(float(v))).zfill(5)


def knn_weights(lat: np.ndarray, lon: np.ndarray, k: int) -> np.ndarray:
    """Row-standardised k-nearest-neighbour weights by great-circle distance."""
    la, lo = np.radians(lat), np.radians(lon)
    dlat = la[:, None] - la[None, :]
    dlon = lo[:, None] - lo[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(la)[:, None] * np.cos(la)[None, :] * np.sin(dlon / 2) ** 2
    dist = 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    np.fill_diagonal(dist, np.inf)
    idx = np.argsort(dist, axis=1)[:, :k]
    n = len(lat)
    wm = np.zeros((n, n))
    wm[np.repeat(np.arange(n), k), idx.ravel()] = 1.0
    return wm / wm.sum(axis=1, keepdims=True)


def morans_i(x: np.ndarray, wm: np.ndarray, perms: int, rng) -> tuple[float, float, float, float]:
    z = x - x.mean()
    n = len(x)
    denom = (z ** 2).sum()
    if denom == 0:
        return np.nan, np.nan, np.nan, np.nan
    scale = n / wm.sum()
    observed = scale * (z @ (wm @ z)) / denom
    sim = np.empty(perms)
    for i in range(perms):
        zp = rng.permutation(z)
        sim[i] = scale * (zp @ (wm @ zp)) / denom
    pval = (np.sum(np.abs(sim) >= abs(observed)) + 1) / (perms + 1)
    return observed, -1 / (n - 1), pval, sim.std()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, nargs="+", default=[4, 8, 16], help="Neighbour counts.")
    ap.add_argument("--perms", type=int, default=999, help="Permutations for the pseudo p-value.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    df = pd.read_csv(ANALYSIS, low_memory=False)
    df["zip_code"] = df["zip_code"].map(zip5)
    geo = df[["zip_code", "lat", "lon"]].dropna()

    res = pd.read_csv(RESIDUALS, usecols=["region_id", "outcome_name", "model_version", "residual_value"])
    res["zip_code"] = res["region_id"].map(zip5)

    rows = []
    for outcome in OUTCOMES:
        for model, short in MODELS:
            sub = res[(res.outcome_name == outcome) & (res.model_version == f"{outcome} | {model} | raw")]
            if sub.empty:
                continue
            m = sub.merge(geo, on="zip_code", how="inner").dropna(subset=["residual_value", "lat", "lon"])
            if len(m) < 50:
                continue
            lat, lon = m["lat"].to_numpy(), m["lon"].to_numpy()
            vals = m["residual_value"].to_numpy()
            for k in args.k:
                wm = knn_weights(lat, lon, k)
                i, ei, p, sd = morans_i(vals, wm, args.perms, rng)
                rows.append(dict(outcome=outcome, model=short, model_version=model,
                                 k=k, n=len(m), morans_i=i, expected_i=ei,
                                 p_value=p, perm_sd=sd))

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    star = lambda p: "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
    print(f"Moran's I on OLS residuals — row-standardised k-NN weights, {args.perms} permutations")
    print(f"(smallest reportable p is {1/(args.perms+1):.3f}; read it as p < that)\n")
    for k in args.k:
        sl = out[out.k == k]
        if sl.empty:
            continue
        print(f"--- k = {k} ---")
        piv = sl.pivot_table(index="outcome", columns="model", values="morans_i")
        cols = [c for _, c in MODELS if c in piv.columns]
        print(piv[cols].round(4).to_string())
        worst = sl.loc[sl.p_value.idxmax()]
        print(f"    largest p across this panel: {worst.p_value:.3f} "
              f"({worst.outcome} / {worst.model}){star(worst.p_value)}\n")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
