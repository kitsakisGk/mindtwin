import math

import pytest

from mindtwin.core.assets import asset_from_ontology
from mindtwin.core.twin import DigitalTwin, Snapshot


@pytest.fixture(scope="module")
def engine():
    return asset_from_ontology("e1")


def snap(cycle, asset_id="e1", **readings):
    readings = readings or {"s11": 47.0 + cycle * 0.01, "s7": 550.0}
    return Snapshot(asset_id=asset_id, cycle=cycle, settings={"setting1": 0.0}, readings=readings)


def test_empty_twin(engine):
    twin = DigitalTwin(engine)
    assert twin.state() is None and twin.cycle is None and len(twin) == 0
    assert twin.history().empty
    assert twin.component_state("HPC") == {}


def test_update_and_state(engine):
    twin = DigitalTwin(engine)
    twin.update_many([snap(1), snap(2), snap(3)])
    assert twin.cycle == 3 and len(twin) == 3
    assert twin.state().readings["s11"] == pytest.approx(47.03)
    assert twin.component_state("HPC") == {"s7": 550.0, "s11": pytest.approx(47.03)}


def test_history_frame_and_window(engine):
    twin = DigitalTwin(engine)
    twin.update_many(snap(c) for c in range(1, 11))
    hist = twin.history()
    assert list(hist.index) == list(range(1, 11))
    assert set(hist.columns) == {"setting1", "s11", "s7"}
    assert list(twin.history(window=3).index) == [8, 9, 10]
    assert list(twin.sensor_history("s11", window=2).index) == [9, 10]
    assert twin.sensor_history("s4").empty  # known sensor, never reported


def test_history_copy_is_independent(engine):
    twin = DigitalTwin(engine)
    twin.update(snap(1))
    copy = twin.history()
    copy["s11"] = 0.0
    assert twin.history()["s11"].iloc[0] != 0.0


def test_history_cache_refreshes_after_update(engine):
    twin = DigitalTwin(engine)
    twin.update(snap(1))
    assert len(twin.history()) == 1
    twin.update(snap(2))
    assert len(twin.history()) == 2


def test_bounded_history(engine):
    twin = DigitalTwin(engine, max_history=5)
    twin.update_many(snap(c) for c in range(1, 21))
    assert len(twin) == 5 and twin.n_updates == 20
    assert list(twin.history().index) == [16, 17, 18, 19, 20]
    with pytest.raises(ValueError):
        DigitalTwin(engine, max_history=0)


@pytest.mark.parametrize(
    "bad, match",
    [
        (snap(5, asset_id="other"), "sent to twin"),
        (snap(2), "not after"),
        (snap(3), "not after"),
        (snap(4, s99=1.0), "Unknown sensors"),
        (snap(4, s11=math.inf), "Infinite"),
    ],
)
def test_invalid_snapshots_rejected(engine, bad, match):
    twin = DigitalTwin(engine)
    twin.update(snap(3))
    with pytest.raises(ValueError, match=match):
        twin.update(bad)
    assert twin.cycle == 3 and len(twin) == 1  # state unchanged


def test_missing_values_allowed(engine):
    twin = DigitalTwin(engine)
    twin.update(snap(1, s11=math.nan))
    assert math.isnan(twin.state().readings["s11"])


def test_subscribers_notified_and_unsubscribe(engine):
    twin = DigitalTwin(engine)
    seen = []
    unsubscribe = twin.subscribe(lambda t, s: seen.append((t.asset.id, s.cycle)))
    twin.update(snap(1))
    unsubscribe()
    unsubscribe()  # second call is harmless
    twin.update(snap(2))
    assert seen == [("e1", 1)]


def test_failing_subscriber_does_not_break_twin(engine, caplog):
    twin = DigitalTwin(engine)
    calls = []

    def broken(t, s):
        raise RuntimeError("boom")

    twin.subscribe(broken)
    twin.subscribe(lambda t, s: calls.append(s.cycle))
    twin.update(snap(1))
    assert twin.cycle == 1 and calls == [1]
    assert "failed" in caplog.text


def test_snapshot_from_row():
    row = {"unit": 1, "cycle": 7, "setting1": 0.1, "s1": 518.67, "s2": 642.0, "rul": 100}
    s = Snapshot.from_row(row, "e1", sensor_cols=["s1", "s2"], setting_cols=["setting1"])
    assert s.cycle == 7 and s.readings == {"s1": 518.67, "s2": 642.0}
    assert s.settings == {"setting1": 0.1}


def test_repr(engine):
    twin = DigitalTwin(engine)
    twin.update(snap(1))
    assert repr(twin) == "DigitalTwin(asset='e1', cycle=1, history=1)"
