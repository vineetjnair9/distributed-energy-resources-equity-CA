import numpy as np
import pandas as pd

from scripts.model_helpers import run_ols, vif_from_formula


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
