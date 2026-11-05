"""Trailing-window sensor features.

For each sensor, over the last ``window`` cycles of the same engine (current cycle included):

- ``<s>_mean``: average
- ``<s>_std``: standard deviation (population)
- ``<s>_slope``: least-squares slope per cycle, i.e. the local trend

Windows only look backwards, so a feature at cycle t never depends on cycles after t. The same
function works on a whole dataset (grouped by engine) and on a single twin's history, so offline
training and live inference compute identical values.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence

import numpy as np
import pandas as pd

FEATURE_KINDS = ("mean", "std", "slope")
DEFAULT_WINDOW = 10


def feature_names(sensors: Sequence[str]) -> list[str]:
    return [f"{s}_{k}" for s in sensors for k in FEATURE_KINDS]


def _window_sum(x: np.ndarray, window: int) -> np.ndarray:
    """Sum over the trailing ``window`` rows (fewer at the start), via cumulative sums."""
    c = np.cumsum(np.vstack([np.zeros((1, x.shape[1])), x]), axis=0)
    hi = np.arange(1, len(x) + 1)
    lo = np.maximum(0, hi - window)
    return c[hi] - c[lo]


def _window_features(values: np.ndarray, cycles: np.ndarray, window: int) -> np.ndarray:
    """Features for one engine. ``values``: (n, n_sensors), rows in cycle order.

    Vectorised with running sums; missing values are skipped. Values and cycles are centred on
    the engine's own means first, which keeps the sums numerically stable.
    """
    n, m = values.shape
    mask = ~np.isnan(values)
    with warnings.catch_warnings():  # all-NaN sensors: offset becomes 0 below
        warnings.simplefilter("ignore", RuntimeWarning)
        offset = np.nan_to_num(np.nanmean(values, axis=0, keepdims=True))
    y = np.where(mask, values - offset, 0.0)
    t = np.where(mask, (cycles - cycles.mean()).astype(float)[:, None], 0.0)

    cnt = _window_sum(mask.astype(float), window)
    sy, syy = _window_sum(y, window), _window_sum(y * y, window)
    st, stt, sty = _window_sum(t, window), _window_sum(t * t, window), _window_sum(t * y, window)

    with np.errstate(invalid="ignore", divide="ignore"):
        mean_c = sy / cnt
        mean_sq = syy / cnt
        var = mean_sq - mean_c**2
        # Running sums leave rounding noise around 0, which sqrt would magnify; drop it.
        var = np.where(var > 1e-12 * np.maximum(mean_sq, 1.0), var, 0.0)
        t_var = stt - st * st / cnt
        slope = np.where(t_var > 1e-12, (sty - st * sy / cnt) / t_var, 0.0)
    mean = mean_c + offset  # centring only shifts the mean; std and slope are unaffected

    out = np.stack([mean, np.sqrt(var), slope], axis=2)
    out[cnt == 0] = np.nan  # no observed values in the window
    return out.reshape(n, m * len(FEATURE_KINDS))


def rolling_features(
    frame: pd.DataFrame,
    sensors: Sequence[str],
    window: int = DEFAULT_WINDOW,
    group: str | None = "unit",
    cycle: str = "cycle",
) -> pd.DataFrame:
    """Trailing-window features for every row of ``frame``.

    ``frame`` must contain ``cycle`` (as a column or as the index) and the sensor columns; with
    ``group`` set, windows never cross engines. Returns a frame aligned with ``frame.index``.
    """
    if window < 1:
        raise ValueError("window must be at least 1")
    sensors = list(sensors)
    data = frame.reset_index() if cycle not in frame.columns else frame
    data = data.assign(_row=np.arange(len(frame)))

    names = feature_names(sensors)
    result = np.full((len(frame), len(names)), np.nan)
    groups = data.groupby(group, sort=False) if group else [(None, data)]
    for _, g in groups:
        g = g.sort_values(cycle)
        feats = _window_features(g[sensors].to_numpy(float), g[cycle].to_numpy(), window)
        result[g["_row"].to_numpy()] = feats
    return pd.DataFrame(result, index=frame.index, columns=names)
