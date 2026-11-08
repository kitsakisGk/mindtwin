import pandas as pd
import pytest

from mindtwin.data.cmapss import SENSOR_COLS, SETTING_COLS
from mindtwin.data.stream import StreamItem, fleet_stream, paced, start_ticks


def _frame(lengths):
    rows = []
    for unit, n in lengths.items():
        for cycle in range(1, n + 1):
            row = {"unit": unit, "cycle": cycle, "rul": n - cycle}
            row.update(dict.fromkeys(SETTING_COLS, 0.0))
            row.update({c: float(unit * 100 + cycle) for c in SENSOR_COLS})
            rows.append(row)
    return pd.DataFrame(rows).sample(frac=1, random_state=1)  # shuffled on purpose


def test_start_ticks():
    assert start_ticks([1, 2, 3]) == {1: 0, 2: 0, 3: 0}
    s = start_ticks([1, 2, 3], stagger=10, seed=0)
    assert all(0 <= t <= 10 for t in s.values())
    assert s == start_ticks([1, 2, 3], stagger=10, seed=0)  # reproducible
    with pytest.raises(ValueError):
        start_ticks([1], stagger=-1)


def test_lockstep_order_and_completeness():
    items = list(fleet_stream(_frame({1: 3, 2: 2}), "FD001", "test"))
    assert [(i.tick, i.unit, i.snapshot.cycle) for i in items] == [
        (0, 1, 1),
        (0, 2, 1),
        (1, 1, 2),
        (1, 2, 2),
        (2, 1, 3),
    ]
    assert items[0].snapshot.asset_id == "FD001-test-1"
    assert items[0].snapshot.readings["s1"] == 101.0


def test_staggered_starts_keep_each_engine_in_cycle_order():
    frame = _frame({1: 5, 2: 5, 3: 5})
    items = list(fleet_stream(frame, "FD001", "train", stagger=4, seed=3))
    ticks = [i.tick for i in items]
    assert ticks == sorted(ticks)
    starts = start_ticks([1, 2, 3], 4, 3)
    for unit in (1, 2, 3):
        mine = [i for i in items if i.unit == unit]
        assert [i.snapshot.cycle for i in mine] == [1, 2, 3, 4, 5]
        assert mine[0].tick == starts[unit]


def test_unit_selection_and_missing_units():
    items = list(fleet_stream(_frame({1: 2, 2: 2, 3: 2}), "FD001", "test", units=[3]))
    assert {i.unit for i in items} == {3}
    with pytest.raises(KeyError, match="99"):
        list(fleet_stream(_frame({1: 2}), "FD001", "test", units=[99]))


def test_no_labels_in_snapshots():
    item = next(fleet_stream(_frame({1: 2}), "FD001", "test"))
    assert "rul" not in item.snapshot.readings


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(round(seconds, 6))
        self.now += seconds


def test_paced_sleeps_once_per_tick():
    items = list(fleet_stream(_frame({1: 3, 2: 3}), "FD001", "test"))
    clock = FakeClock()
    out = list(paced(items, ticks_per_second=2, clock=clock, sleep=clock.sleep))
    assert out == items
    assert clock.sleeps == [0.5, 0.5]  # ticks 1 and 2; both engines of a tick share one wait
    assert clock.now == pytest.approx(1.0)


def test_paced_does_not_sleep_when_behind():
    clock = FakeClock()
    items = [StreamItem(t, 1, None) for t in range(3)]

    def slow_consumer():
        for item in paced(items, 10, clock=clock, sleep=clock.sleep):
            clock.now += 1.0  # consumer slower than the stream
            yield item

    assert len(list(slow_consumer())) == 3
    assert clock.sleeps == []


def test_paced_rejects_bad_rate():
    with pytest.raises(ValueError):
        list(paced([], 0))
