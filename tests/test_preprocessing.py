import numpy as np
import pandas as pd
import pytest

from mindtwin.data.cmapss import SENSOR_COLS
from mindtwin.data.preprocessing import (
    ConditionNormalizer,
    informative_sensors,
    operating_condition,
)


def _frame(settings, sensor_values):
    rows = []
    for (a, b, c), v in zip(settings, sensor_values, strict=True):
        rows.append({"setting1": a, "setting2": b, "setting3": c, **dict.fromkeys(SENSOR_COLS, v)})
    return pd.DataFrame(rows)


def test_operating_condition_rounds_noise_and_negative_zero():
    df = _frame([(0.0012, -0.0003, 100), (-0.0007, 0.0004, 100), (42.003, 0.8401, 100)], [1, 1, 1])
    cond = operating_condition(df)
    assert cond.iloc[0] == cond.iloc[1]
    assert cond.nunique() == 2


def test_condition_normalizer_removes_condition_offset():
    rng = np.random.default_rng(0)
    settings = [(0, 0, 100)] * 50 + [(42, 0.84, 100)] * 50
    values = np.r_[rng.normal(10, 1, 50), rng.normal(500, 1, 50)]
    df = _frame(settings, values)
    out = ConditionNormalizer().fit_transform(df)
    by_cond = out["s1"].groupby(operating_condition(df))
    assert by_cond.mean().abs().max() == pytest.approx(0, abs=1e-9)
    assert by_cond.std(ddof=0).tolist() == pytest.approx([1, 1])


def test_unseen_condition_uses_global_stats():
    train = _frame([(0, 0, 100)] * 3, [1.0, 2.0, 3.0])
    test = _frame([(20, 0.7, 100)], [2.0])
    out = ConditionNormalizer().fit(train).transform(test)
    assert out["s1"].iloc[0] == pytest.approx(0.0)


def test_informative_sensors_drops_flat_ones():
    df = _frame([(0, 0, 100)] * 4, [1.0] * 4)
    df["s2"] = [1.0, 2.0, 3.0, 4.0]
    assert informative_sensors(df) == ["s2"]
