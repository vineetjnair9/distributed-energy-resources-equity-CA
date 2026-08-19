import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from scripts.model_helpers import (
    common_sample_index,
    fit_stats,
    oster_delta,
    pv_kw_per_1000,
    run_ols,
    vif_from_formula,
)


def test_pv_rate_converts_mw_to_kw_per_1000_residents():
    assert pv_kw_per_1000(3.52, 56_403) == np.float64(
        3.52 * 1_000_000 / 56_403
    )


def test_vif_keeps_intercept_and_is_scale_invariant():
    rng = np.random.default_rng(42)
    frame = pd.DataFrame(
        {
            "y": rng.normal(size=200),
            "x1": rng.normal(loc=50, scale=4, size=200),
            "x2": rng.normal(loc=10_000, scale=800, size=200),
        }
    )
    raw = vif_from_formula("y ~ x1 + x2", frame).set_index("feature")["VIF"]
    standardized = frame.copy()
    standardized[["x1", "x2"]] = (
        standardized[["x1", "x2"]] - standardized[["x1", "x2"]].mean()
    ) / standardized[["x1", "x2"]].std(ddof=0)
    scaled = vif_from_formula("y ~ x1 + x2", standardized).set_index("feature")["VIF"]

    assert "Intercept" not in raw.index
    assert np.allclose(raw.sort_index(), scaled.sort_index(), atol=1e-10)
    assert raw.max() < 1.1


def test_cluster_minimum_is_local_to_clustered_specification():
    frame = pd.DataFrame(
        {
            "y": np.arange(16, dtype=float),
            "x": np.linspace(0, 1, 16),
            "county": ["small"] * 4 + ["large_a"] * 6 + ["large_b"] * 6,
        }
    )

    ordinary = run_ols("y ~ x", frame)
    clustered = run_ols("y ~ x", frame, cluster_col="county", min_cluster_size=5)

    assert ordinary.nobs == 16
    assert clustered.nobs == 12


def test_county_fixed_effect_drops_missing_without_pseudo_county():
    frame = pd.DataFrame(
        {
            "y": [1.0, 2.0, 3.0, 4.0, 5.0],
            "x": [0.0, 1.0, 0.5, 1.5, 2.0],
            "county": ["06001", "06001", "06013", "06013", np.nan],
        }
    )
    result = run_ols("y ~ x + C(county)", frame)

    assert result.nobs == 4
    assert not any("nan" in name.lower() for name in result.params.index)


def test_fit_stats_reports_n_clusters_on_clustered_fit():
    frame = pd.DataFrame(
        {
            "y": np.arange(30, dtype=float),
            "x": np.linspace(0, 1, 30),
            "county": (["a"] * 10) + (["b"] * 10) + (["c"] * 10),
        }
    )
    clustered = run_ols("y ~ x", frame, cluster_col="county", min_cluster_size=5)
    stats = fit_stats(clustered)

    assert stats["nobs"] == 30
    assert stats["cov_type"] == "cluster"
    assert stats["n_clusters"] == 3
    assert stats["rsquared"] == clustered.rsquared


def test_fit_stats_omits_n_clusters_when_not_clustered():
    frame = pd.DataFrame({"y": np.arange(10, dtype=float), "x": np.linspace(0, 1, 10)})
    ordinary = run_ols("y ~ x", frame)
    stats = fit_stats(ordinary)

    assert stats["cov_type"] == "HC1"
    assert "n_clusters" not in stats


def test_common_sample_index_returns_intersection_under_injected_nans():
    rng = np.random.default_rng(0)
    frame = pd.DataFrame(
        {
            "y": rng.normal(size=50),
            "x1": rng.normal(size=50),
            "x2": rng.normal(size=50),
        }
    )
    frame.loc[0:4, "x1"] = np.nan
    frame.loc[10:14, "x2"] = np.nan

    common = common_sample_index(["y ~ x1", "y ~ x1 + x2"], frame)

    expected = frame.dropna(subset=["x1", "x2"]).index
    assert set(common) == set(expected)


def test_common_sample_index_honors_min_cluster_size():
    frame = pd.DataFrame(
        {
            "y": np.arange(16, dtype=float),
            "x": np.linspace(0, 1, 16),
            "county": ["small"] * 4 + ["large_a"] * 6 + ["large_b"] * 6,
        }
    )

    common = common_sample_index(["y ~ x"], frame, cluster_col="county", min_cluster_size=5)

    assert len(common) == 12
    assert "small" not in frame.loc[common, "county"].unique()


def test_oster_delta_recovers_known_delta_with_planted_confound():
    # Proportional-selection design (Oster 2019's own validity check): the omitted
    # confound u and the observed control w load onto x identically, and onto y
    # identically, with x's *direct* effect on y set to exactly zero by construction
    # (the oracle regression y ~ x + w + u recovers beta_x = 0). Under equal selection
    # the true coefficient of proportionality is delta = 1, so solving for the delta
    # that zeroes the coefficient - using the oracle regression's R^2 as Rmax instead
    # of the 1.3x heuristic - must recover delta close to 1.
    rng = np.random.default_rng(7)
    n = 200_000
    w = rng.normal(size=n)
    u = rng.normal(size=n)
    x = w + u + 1.0 * rng.normal(size=n)
    y = 1.0 * w + 1.0 * u + 0.5 * rng.normal(size=n)
    frame = pd.DataFrame({"y": y, "x": x, "w": w, "u": u})

    res_restricted = smf.ols("y ~ x", data=frame).fit()
    res_full = smf.ols("y ~ x + w", data=frame).fit()
    res_oracle = smf.ols("y ~ x + w + u", data=frame).fit()

    assert np.isclose(res_oracle.params["x"], 0.0, atol=0.02)

    rmax = res_oracle.rsquared
    delta = oster_delta(res_restricted, res_full, "x", rmax_multiplier=rmax / res_full.rsquared)

    assert np.isclose(delta, 1.0, atol=0.05)


def test_oster_delta_returns_nan_when_r_squared_does_not_increase():
    rng = np.random.default_rng(1)
    frame = pd.DataFrame({"y": rng.normal(size=200), "x": rng.normal(size=200)})
    res_restricted = smf.ols("y ~ x", data=frame).fit()
    # "Full" model with the same regressor: R^2 cannot increase.
    res_full = smf.ols("y ~ x", data=frame).fit()

    assert np.isnan(oster_delta(res_restricted, res_full, "x"))
