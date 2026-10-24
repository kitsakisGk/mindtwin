"""Prognostic metrics for RUL prediction."""

from __future__ import annotations

import numpy as np


def rmse(y_true, y_pred) -> float:
    """Root mean squared error."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_pred - y_true) ** 2)))


def phm08_score(y_true, y_pred) -> float:
    """Scoring function of the PHM08 challenge (Saxena et al. 2008). Lower is better.

    With error ``d = predicted - true``, each engine scores ``exp(-d/13) - 1`` if the prediction
    is early (``d < 0``) and ``exp(d/10) - 1`` if it is late. Late predictions cost more because
    they risk a failure in service.
    """
    d = np.asarray(y_pred, dtype=float) - np.asarray(y_true, dtype=float)
    scores = np.where(d < 0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
    return float(np.sum(scores))
