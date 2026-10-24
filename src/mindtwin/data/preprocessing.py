"""Preprocessing for multi-condition sensor data."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from mindtwin.data.cmapss import SENSOR_COLS


def operating_condition(df: pd.DataFrame) -> pd.Series:
    """Label each row with its operating condition.

    C-MAPSS operating settings take a few discrete values plus small noise, so rounding them
    (setting1 to 0 decimals, setting2 to 2, setting3 as is) identifies the condition exactly:
    one condition in FD001/FD003, six in FD002/FD004.
    """
    s1 = df["setting1"].round(0).abs()  # abs() folds -0.0 into 0.0
    s2 = df["setting2"].round(2).abs()
    s3 = df["setting3"].round(0)
    key = s1.astype(str) + "|" + s2.astype(str) + "|" + s3.astype(str)
    return key.rename("condition")


def informative_sensors(train: pd.DataFrame, tol: float = 1e-3) -> list[str]:
    """Sensors whose standard deviation within at least one condition is above ``tol``."""
    cond = operating_condition(train)
    std = train[SENSOR_COLS].groupby(cond).std().max()
    return [c for c in SENSOR_COLS if std[c] > tol]


class ConditionNormalizer:
    """Z-score each sensor using the mean and std of its operating condition.

    Fitted on training data only; conditions unseen in training fall back to global stats.
    """

    def __init__(self, columns: Sequence[str] | None = None, eps: float = 1e-8):
        self.columns = list(columns) if columns is not None else list(SENSOR_COLS)
        self.eps = eps

    def fit(self, df: pd.DataFrame) -> ConditionNormalizer:
        cond = operating_condition(df)
        grouped = df[self.columns].groupby(cond)
        self.mean_ = grouped.mean()
        self.std_ = grouped.std(ddof=0)
        self.global_mean_ = df[self.columns].mean()
        self.global_std_ = df[self.columns].std(ddof=0)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        cond = operating_condition(df)
        mean = self.mean_.reindex(cond).fillna(self.global_mean_).set_axis(df.index)
        std = self.std_.reindex(cond).fillna(self.global_std_).set_axis(df.index)
        out = df.copy()
        out[self.columns] = (df[self.columns] - mean) / (std + self.eps)
        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)
