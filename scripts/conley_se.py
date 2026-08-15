#!/usr/bin/env python3
"""Conley spatial HAC standard errors for the baseline DER models.

Moran's I on the residuals (scripts/spatial_diagnostics.py) is significant for every
outcome and every specification, and county fixed effects only remove about two thirds of
it. That means dependence persists below county level, so county-clustered standard
errors are correcting at too coarse a resolution. Conley (1999) standard errors allow
residuals to covary with distance directly and are the standard remedy.

Estimator
---------
    V = (X'X)^-1  [ sum_i sum_j K(d_ij) e_i e_j x_i x_j' ]  (X'X)^-1

with a Bartlett kernel K(d) = max(0, 1 - d/cutoff) over great-circle distance in km. The
Bartlett taper keeps the middle term positive semi-definite, which a uniform cutoff does
not guarantee. A finite-sample factor n/(n-k) is applied, matching the HC1 convention the
paper already uses so the two columns are comparable.

Point estimates are unchanged by construction — only the standard errors move.

Cutoff choice is a judgement call with no consensus rule, so results are reported across
several. Report the pattern, not one cutoff.

Usage
-----
    python scripts/conley_se.py
    python scripts/conley_se.py --cutoffs 10 25 50 100 200
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "processed" / "combined_der_dataset_w_controls_predictors.csv"
OUT_CSV = ROOT / "outputs" / "tables" / "conley_standard_errors.csv"

MIN_POP = 1000
CORE = ["median_household_income", "pct_black", "pct_hispanic", "pct_asian"]
RACE = ["pct_black", "pct_hispanic", "pct_asian"]
INCOME = "log_median_household_income"
CLIMATE = {"y_pv": ["ghi_mean_kwh_m2_day_2023"],
           "y_storage": ["cdd65_2023", "hdd65_2023"],
           "y_chargers": ["cdd65_2023", "hdd65_2023"]}
REPORT = [INCOME] + RACE + ["poverty_rate"]


def build_frame() -> pd.DataFrame:
    df = pd.read_csv(ANALYSIS, low_memory=False)
    for c in ["PV_system_size_DC", "total_chargers", "storage_capacity_mw"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["total_population"] = pd.to_numeric(df["total_population"], errors="coerce")
    df = df[df["total_population"].notna() & (df["total_population"] >= MIN_POP)]
    df = df.dropna(subset=CORE).copy()
    pop = df["total_population"].replace(0, np.nan)
    df["y_pv"] = np.log1p(df["PV_system_size_DC"] * 1000 / pop)
    df["y_chargers"] = np.log1p(df["total_chargers"] * 1000 / pop)
    df["y_storage"] = np.log1p(df["storage_capacity_mw"] * 100000 / pop)
    df[INCOME] = np.log(df["median_household_income"].where(df["median_household_income"] > 0))
    return df


def great_circle(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    la, lo = np.radians(lat), np.radians(lon)
    dlat = la[:, None] - la[None, :]
    dlon = lo[:, None] - lo[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(la)[:, None] * np.cos(la)[None, :] * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def conley_se(X: np.ndarray, resid: np.ndarray, dist: np.ndarray, cutoff: float) -> np.ndarray:
    n, k = X.shape
    kern = np.clip(1.0 - dist / cutoff, 0.0, None)      # Bartlett taper
    np.fill_diagonal(kern, 1.0)
    meat = X.T @ (kern * np.outer(resid, resid)) @ X
    bread = np.linalg.inv(X.T @ X)
    V = bread @ meat @ bread * (n / (n - k))
    return np.sqrt(np.clip(np.diag(V), 0, None))


def hc1_se(X: np.ndarray, resid: np.ndarray) -> np.ndarray:
    n, k = X.shape
    bread = np.linalg.inv(X.T @ X)
    meat = X.T @ (np.diag(resid ** 2)) @ X
    return np.sqrt(np.diag(bread @ meat @ bread) * (n / (n - k)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cutoffs", type=float, nargs="+", default=[25, 50, 100, 200],
                    help="Bartlett cutoff distances in km.")
    args = ap.parse_args()

    df = build_frame()
    rows = []
    for outcome, climate in CLIMATE.items():
        sub = df.dropna(subset=[outcome, INCOME, "poverty_rate", "lat", "lon"] + RACE + climate).copy()
        formula = f"{outcome} ~ " + " + ".join([INCOME] + RACE + ["poverty_rate"] + climate)
        y, X = patsy.dmatrices(formula, sub, return_type="dataframe")
        names = list(X.columns)
        Xv, yv = X.to_numpy(), y.to_numpy().ravel()
        beta = np.linalg.lstsq(Xv, yv, rcond=None)[0]
        resid = yv - Xv @ beta
        dist = great_circle(sub["lat"].to_numpy(), sub["lon"].to_numpy())
        se_hc1 = hc1_se(Xv, resid)
        ses = {f"se_conley_{int(c)}km": conley_se(Xv, resid, dist, c) for c in args.cutoffs}
        for i, nm in enumerate(names):
            if nm not in REPORT:
                continue
            rec = dict(outcome=outcome, term=nm, n=len(sub), coef=beta[i], se_hc1=se_hc1[i],
                       p_hc1=2 * (1 - stats.norm.cdf(abs(beta[i] / se_hc1[i]))))
            for key, arr in ses.items():
                rec[key] = arr[i]
                rec[key.replace("se_", "p_")] = 2 * (1 - stats.norm.cdf(abs(beta[i] / arr[i])))
            rows.append(rec)

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    star = lambda p: "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""
    cut_cols = [f"se_conley_{int(c)}km" for c in args.cutoffs]
    print("Conley spatial HAC standard errors, Bartlett kernel over great-circle distance")
    print("Point estimates are identical across columns; only the standard errors change.\n")
    for outcome in CLIMATE:
        sl = out[out.outcome == outcome]
        if sl.empty:
            continue
        print(f"--- {outcome}  (N = {int(sl.n.iloc[0])}) ---")
        hdr = f"{'term':30s}{'coef':>10s}{'HC1':>12s}" + "".join(f"{c.replace('se_conley_',''):>13s}" for c in cut_cols)
        print(hdr)
        for _, r in sl.iterrows():
            line = f"{r.term:30s}{r.coef:>10.4f}{r.se_hc1:>9.4f}{star(r.p_hc1):<3s}"
            for c in cut_cols:
                line += f"{r[c]:>10.4f}{star(r[c.replace('se_','p_')]):<3s}"
            print(line)
        infl = (sl[cut_cols[-1]] / sl.se_hc1).max()
        print(f"    largest SE inflation vs HC1 at {cut_cols[-1].replace('se_conley_','')}: {infl:.2f}x\n")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
