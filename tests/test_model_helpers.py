import numpy as np
import pandas as pd

from scripts.model_helpers import (
    common_sample_index,
    fit_stats,
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


def _ladder_frame():
    rng = np.random.default_rng(7)
    n = 60
    frame = pd.DataFrame(
        {
            "y": rng.normal(size=n),
            "x": rng.normal(size=n),
            "z": rng.normal(size=n),
            "county": ["small"] * 3 + ["large_a"] * 29 + ["large_b"] * 28,
        }
    )
    # z is missing on rows the x-only formula can still use, which is exactly the
    # drift a cumulative ladder has to freeze out.
    frame.loc[frame.index[:5], "z"] = np.nan
    return frame


def test_common_sample_index_intersects_across_formulas():
    frame = _ladder_frame()

    index = common_sample_index(["y ~ x", "y ~ x + z"], frame)

    assert len(index) == 55
    assert frame.loc[index, "z"].notna().all()
    assert run_ols("y ~ x", frame).nobs == 60
    assert run_ols("y ~ x", frame.loc[index]).nobs == 55


def test_common_sample_index_honors_min_cluster_size():
    frame = _ladder_frame()

    index = common_sample_index(
        ["y ~ x", "y ~ x + z"], frame, cluster_col="county", min_cluster_size=5
    )

    # The three "small" rows are also among the five with a missing z, so the cluster
    # filter has to be judged on what survives the intersection, not on the raw frame.
    assert set(frame.loc[index, "county"]) == {"large_a", "large_b"}
    assert len(index) == 55


def test_fit_stats_reports_clusters_only_when_clustered():
    frame = _ladder_frame()

    ordinary = fit_stats(run_ols("y ~ x", frame))
    clustered = fit_stats(run_ols("y ~ x", frame, cluster_col="county", min_cluster_size=5))

    assert ordinary["nobs"] == 60
    assert ordinary["cov_type"] == "HC1"
    assert "n_clusters" not in ordinary
    assert clustered["cov_type"] == "cluster"
    assert clustered["n_clusters"] == 2
