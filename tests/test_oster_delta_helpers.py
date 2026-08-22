import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from scripts.oster_delta_helpers import oster_delta


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


def test_oster_delta_returns_nan_when_denominator_collapses():
    # rmax_multiplier = 1.0 forces rmax = r2_full exactly, so (rmax - r2_full) = 0 and
    # the denominator collapses regardless of how beta moves - a deterministic way to
    # exercise that guard without depending on a particular DGP's noise draw.
    rng = np.random.default_rng(3)
    n = 500
    x = rng.normal(size=n)
    w = rng.normal(size=n)
    y = 2.0 * x + 0.5 * w + 0.05 * rng.normal(size=n)
    frame = pd.DataFrame({"y": y, "x": x, "w": w})

    res_restricted = smf.ols("y ~ x", data=frame).fit()
    res_full = smf.ols("y ~ x + w", data=frame).fit()
    assert res_full.rsquared > res_restricted.rsquared

    assert np.isnan(oster_delta(res_restricted, res_full, "x", rmax_multiplier=1.0))
