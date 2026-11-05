import numpy as np
import pandas as pd
import pytest

from mindtwin.core.assets import asset_from_ontology
from mindtwin.core.twin import DigitalTwin, Snapshot
from mindtwin.data.cmapss import default_data_dir
from mindtwin.data.features import feature_names, latest_features, rolling_features


def _frame():
    # unit 1: s1 rises 2 per cycle; unit 2: s1 constant. Rows deliberately shuffled.
    rows = [{"unit": 1, "cycle": c, "s1": 2.0 * c, "s2": 5.0} for c in range(1, 8)]
    rows += [{"unit": 2, "cycle": c, "s1": 3.0, "s2": float(c % 2)} for c in range(1, 6)]
    return pd.DataFrame(rows).sample(frac=1, random_state=0)


def test_feature_names():
    assert feature_names(["s1"]) == ["s1_mean", "s1_std", "s1_slope"]


def test_values_on_known_trend():
    df = _frame()
    feats = rolling_features(df, ["s1", "s2"], window=3)
    assert list(feats.index) == list(df.index)  # aligned with input, order preserved
    row = df[(df.unit == 1) & (df.cycle == 5)].index[0]
    assert feats.loc[row, "s1_mean"] == pytest.approx(8.0)  # mean of 6, 8, 10
    assert feats.loc[row, "s1_std"] == pytest.approx(np.std([6, 8, 10]))
    assert feats.loc[row, "s1_slope"] == pytest.approx(2.0)
    assert feats.loc[row, "s2_slope"] == pytest.approx(0.0)


def test_first_cycle_and_short_windows():
    df = _frame()
    feats = rolling_features(df, ["s1"], window=3)
    first = df[(df.unit == 1) & (df.cycle == 1)].index[0]
    assert feats.loc[first, "s1_mean"] == 2.0
    assert feats.loc[first, "s1_std"] == 0.0
    assert feats.loc[first, "s1_slope"] == 0.0
    second = df[(df.unit == 1) & (df.cycle == 2)].index[0]
    assert feats.loc[second, "s1_slope"] == pytest.approx(2.0)


def test_windows_do_not_cross_engines():
    df = _frame()
    feats = rolling_features(df, ["s1"], window=10)
    unit2 = df[df.unit == 2].index
    assert (feats.loc[unit2, "s1_slope"] == 0.0).all()
    assert (feats.loc[unit2, "s1_mean"] == 3.0).all()


def test_no_lookahead():
    """Features at cycle t must not change when later cycles are added."""
    df = _frame()
    full = rolling_features(df, ["s1", "s2"], window=4)
    past = df[df.cycle <= 4]
    partial = rolling_features(past, ["s1", "s2"], window=4)
    pd.testing.assert_frame_equal(full.loc[past.index], partial)


def test_cycle_as_index_and_no_group():
    df = pd.DataFrame({"cycle": [1, 2, 3], "s1": [1.0, 2.0, 4.0]}).set_index("cycle")
    feats = rolling_features(df, ["s1"], window=2, group=None)
    assert feats["s1_slope"].tolist() == pytest.approx([0.0, 1.0, 2.0])


def test_missing_values_ignored_in_mean():
    df = pd.DataFrame({"unit": 1, "cycle": [1, 2, 3], "s1": [1.0, np.nan, 3.0]})
    feats = rolling_features(df, ["s1"], window=3)
    assert feats["s1_mean"].iloc[-1] == pytest.approx(2.0)


def test_invalid_window():
    with pytest.raises(ValueError):
        rolling_features(_frame(), ["s1"], window=0)


def _reference(values, cycles, window):
    """Slow, obviously-correct version: loop over every window."""
    n, m = values.shape
    out = np.full((n, m, 3), np.nan)
    for i in range(n):
        lo = max(0, i - window + 1)
        for j in range(m):
            y = values[lo : i + 1, j]
            t = cycles[lo : i + 1].astype(float)
            ok = ~np.isnan(y)
            y, t = y[ok], t[ok]
            if len(y) == 0:
                continue
            out[i, j, 0] = y.mean()
            out[i, j, 1] = y.std()
            tc = t - t.mean()
            out[i, j, 2] = (tc * (y - y.mean())).sum() / (tc**2).sum() if len(y) >= 2 else 0.0
    return out.reshape(n, m * 3)


@pytest.mark.parametrize("window", [1, 3, 10, 50])
def test_matches_reference_on_random_data_with_gaps(window):
    rng = np.random.default_rng(window)
    n = 40
    values = 9000 + rng.normal(0, 5, (n, 3)) + np.arange(n)[:, None] * 0.3  # large offset, trend
    values[rng.random((n, 3)) < 0.2] = np.nan
    values[:, 2] = np.nan  # one sensor never observed
    df = pd.DataFrame(values, columns=["a", "b", "c"]).assign(unit=1, cycle=np.arange(1, n + 1))
    fast = rolling_features(df, ["a", "b", "c"], window=window).to_numpy()
    slow = _reference(values, df["cycle"].to_numpy(), window)
    np.testing.assert_allclose(fast, slow, rtol=1e-7, atol=1e-7)


# ---------------------------------------------------------------- live features from a twin


def test_latest_features_empty_twin():
    assert latest_features(DigitalTwin(asset_from_ontology("e"))).empty


def test_latest_features_match_offline():
    twin = DigitalTwin(asset_from_ontology("e"))
    rows = []
    for c in range(1, 16):
        readings = {"s11": 47 + 0.1 * c, "s7": 550 - 0.05 * c**1.5}
        twin.update(Snapshot(asset_id="e", cycle=c, readings=readings))
        rows.append({"unit": 1, "cycle": c, **readings})
    offline = rolling_features(pd.DataFrame(rows), ["s11", "s7"], window=5).iloc[-1]
    live = latest_features(twin, ["s11", "s7"], window=5)
    assert live.name == 15
    np.testing.assert_allclose(live.to_numpy(), offline.to_numpy(), rtol=1e-9)


requires_data = pytest.mark.skipif(
    not (default_data_dir() / "train_FD002.txt").exists(), reason="C-MAPSS not downloaded"
)


@requires_data
@pytest.mark.integration
def test_live_equals_offline_on_real_engine_with_normalisation():
    """Multi-condition subset: normalise, then live twin features == offline features."""
    from mindtwin.data.cmapss import load_cmapss
    from mindtwin.data.preprocessing import ConditionNormalizer, informative_sensors
    from mindtwin.data.replay import replay_engine

    data = load_cmapss("FD002")
    sensors = informative_sensors(data.train)
    norm = ConditionNormalizer(sensors).fit(data.train)
    offline = rolling_features(norm.transform(data.test), sensors, window=10)

    unit = int(data.test["unit"].iloc[0])
    rows = data.test[data.test["unit"] == unit].sort_values("cycle")
    for cycle in [1, 5, 10, 37, int(rows["cycle"].max())]:
        twin = replay_engine(data.test, unit, "FD002", "test", until_cycle=cycle)
        live = latest_features(twin, sensors, window=10, normalizer=norm)
        expected = offline.loc[rows.index[rows["cycle"] == cycle][0]]
        np.testing.assert_allclose(live.to_numpy(), expected.to_numpy(), rtol=1e-7, atol=1e-9)
