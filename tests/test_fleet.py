import pandas as pd
import pytest

from mindtwin.core.fleet import Fleet
from mindtwin.core.twin import Snapshot
from mindtwin.data.cmapss import SENSOR_COLS, SETTING_COLS, default_data_dir
from mindtwin.data.stream import fleet_stream


def snap(asset_id, cycle):
    return Snapshot(asset_id=asset_id, cycle=cycle, readings={"s11": 47.0 + cycle})


def test_ingest_creates_twins_on_demand():
    fleet = Fleet()
    fleet.ingest(snap("a", 1))
    fleet.ingest(snap("b", 1))
    fleet.ingest(snap("a", 2))
    assert len(fleet) == 2 and "a" in fleet and "c" not in fleet
    assert fleet["a"].cycle == 2 and fleet["b"].cycle == 1
    assert {t.asset.id for t in fleet} == {"a", "b"}


def test_invalid_snapshot_still_rejected_by_twin():
    fleet = Fleet()
    fleet.ingest(snap("a", 2))
    with pytest.raises(ValueError, match="not after"):
        fleet.ingest(snap("a", 1))


def test_subscribers_reach_existing_and_future_twins():
    fleet = Fleet()
    fleet.ingest(snap("a", 1))
    seen = []
    unsubscribe = fleet.subscribe(lambda t, s: seen.append((s.asset_id, s.cycle)))
    fleet.ingest(snap("a", 2))  # existing twin
    fleet.ingest(snap("b", 1))  # twin created after subscribing
    unsubscribe()
    unsubscribe()  # harmless twice
    fleet.ingest(snap("a", 3))
    fleet.ingest(snap("c", 1))
    assert seen == [("a", 2), ("b", 1)]


def test_status_and_bounded_history():
    fleet = Fleet(max_history=2)
    for c in range(1, 6):
        fleet.ingest(snap("a", c))
    status = fleet.status()
    assert status.loc["a", "cycle"] == 5 and status.loc["a", "updates"] == 5
    assert len(fleet["a"]) == 2
    assert Fleet().status().empty
    assert repr(fleet) == "Fleet(twins=1)"


def test_run_accepts_stream_items_and_snapshots():
    rows = []
    for unit, n in [(1, 4), (2, 3)]:
        for cycle in range(1, n + 1):
            row = {"unit": unit, "cycle": cycle}
            row.update(dict.fromkeys(SETTING_COLS, 0.0))
            row.update(dict.fromkeys(SENSOR_COLS, 1.0))
            rows.append(row)
    frame = pd.DataFrame(rows)
    fleet = Fleet()
    assert fleet.run(fleet_stream(frame, "FD001", "test", stagger=2, seed=1)) == 7
    assert fleet.status()["cycle"].to_dict() == {"FD001-test-1": 4, "FD001-test-2": 3}
    assert Fleet().run([snap("x", 1), snap("x", 2)]) == 2


@pytest.mark.skipif(
    not (default_data_dir() / "test_FD001.txt").exists(), reason="C-MAPSS not downloaded"
)
@pytest.mark.integration
def test_whole_fd001_test_fleet_streams_correctly():
    from mindtwin.data.cmapss import load_cmapss

    data = load_cmapss("FD001")
    fleet = Fleet()
    n = fleet.run(fleet_stream(data.test, "FD001", "test", stagger=100, seed=0))
    assert n == len(data.test) and len(fleet) == 100
    last = data.test.groupby("unit")["cycle"].max()
    status = fleet.status()
    for unit, cycle in last.items():
        assert status.loc[f"FD001-test-{unit}", "cycle"] == cycle


def test_same_callback_subscribed_twice_is_two_subscriptions():
    fleet = Fleet()
    fleet.ingest(snap("a", 1))
    calls = []

    def cb(t, s):
        calls.append(s.cycle)

    first = fleet.subscribe(cb)
    second = fleet.subscribe(cb)
    fleet.ingest(snap("a", 2))
    fleet.ingest(snap("b", 1))
    assert calls == [2, 2, 1, 1]
    first()
    fleet.ingest(snap("a", 3))
    assert calls[-1:] == [3] and len(calls) == 5  # one subscription left
    second()
    fleet.ingest(snap("a", 4))
    fleet.ingest(snap("c", 1))
    assert len(calls) == 5
