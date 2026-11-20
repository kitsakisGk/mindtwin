"""Preprocessing for multi-condition sensor data."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from mindtwin.data.cmapss import SENSOR_COLS


def operating_condition(df: pd.DataFrame) -> pd.Series:
    """Label each row with its operating condition.

    C-MAPSS operating settings take a few discrete values plus small noise, so rounding them
    (setting1 to 0 decimals, setting2 to 2, setting3 as is) identifies the condition exactly:
    one condition in FD001/FD003, six in FD002/FD004.
    """
    s1 = np.abs(np.round(df["setting1"].to_numpy(float), 0))  # abs() folds -0.0 into 0.0
    s2 = np.abs(np.round(df["setting2"].to_numpy(float), 2))
    s3 = np.round(df["setting3"].to_numpy(float), 0)
    triples = zip(s1.tolist(), s2.tolist(), s3.tolist(), strict=True)
    keys = [f"{a!r}|{b!r}|{c!r}" for a, b, c in triples]
    return pd.Series(keys, index=df.index, name="condition", dtype=object)


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
        # Plain arrays for transform(): pandas reindex/fillna cost ~10 ms even on 10 rows,
        # which dominated live feature computation.
        self._row = {key: i for i, key in enumerate(self.mean_.index)}
        self._mean = self.mean_.to_numpy(float)
        self._std = self.std_.to_numpy(float)
        self._gmean = self.global_mean_.to_numpy(float)
        self._gstd = self.global_std_.to_numpy(float)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        rows = np.array([self._row.get(k, -1) for k in operating_condition(df)], dtype=int)
        seen = (rows >= 0)[:, None]
        mean = np.where(seen, self._mean[rows], self._gmean)  # rows == -1 is masked out
        std = np.where(seen, self._std[rows], self._gstd)
        mean = np.where(np.isnan(mean), self._gmean, mean)  # same as the former fillna
        std = np.where(np.isnan(std), self._gstd, std)
        pos = df.columns.get_indexer(self.columns)
        if (pos < 0).any():
            missing = [c for c, p in zip(self.columns, pos, strict=True) if p < 0]
            raise KeyError(f"Columns missing from data: {missing}")
        if all(dt == np.float64 for dt in df.dtypes):
            # Fast path (e.g. twin histories): rebuild one float array instead of assigning
            # columns one by one, which costs ~1.7 ms per call in pandas.
            values = df.to_numpy(float, copy=True)
            values[:, pos] = (values[:, pos] - mean) / (std + self.eps)
            return pd.DataFrame(values, index=df.index, columns=df.columns)
        out = df.copy()
        out[self.columns] = (df[self.columns].to_numpy(float) - mean) / (std + self.eps)
        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)
