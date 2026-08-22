"""Oster (2019) delta bounds. Standalone module, not part of scripts/model_helpers.py
so it can be added without touching a file that also exists on main.
"""

from __future__ import annotations

import numpy as np


def oster_delta(res_restricted, res_full, focal_term: str, rmax_multiplier: float = 1.3) -> float:
    """Oster (2019) delta: how much selection on unobservables (relative to observables)
    would be needed to drive the focal coefficient to zero.

    Solving beta*(delta) = 0 for delta, where
        beta*(delta) = beta_full - delta * (beta_restricted - beta_full)
                       * (rmax - r2_full) / (r2_full - r2_restricted)
    gives the formula below. Returns nan rather than a misleading number when R^2 does
    not increase from restricted to full, or when the denominator collapses (no
    observable selection, or r2_full already at rmax).
    """
    beta_restricted = res_restricted.params[focal_term]
    beta_full = res_full.params[focal_term]
    r2_restricted = res_restricted.rsquared
    r2_full = res_full.rsquared
    rmax = min(rmax_multiplier * r2_full, 1.0)

    if r2_full <= r2_restricted:
        return float("nan")

    denominator = (beta_restricted - beta_full) * (rmax - r2_full)
    if np.isclose(denominator, 0.0):
        return float("nan")

    return float(beta_full * (r2_full - r2_restricted) / denominator)
