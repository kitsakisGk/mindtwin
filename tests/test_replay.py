import pandas as pd
import pytest

from mindtwin.data.cmapss import SENSOR_COLS, SETTING_COLS, SUBSETS, default_data_dir, load_cmapss
from mindtwin.data.replay import engine_id, iter_snapshots, replay_engine
from mindtwin.knowledge.ontology import default_ontology, load_ontology


def _frame():
    rows = []
    for unit, n in [(1, 5), (2, 3)]:
        for cycle in range(n, 0, -1):  # deliberately out of order
            row = {"unit": unit, "cycle": cycle, "rul": n - cycle}
            row.update(dict.fromkeys(SETTING_COLS, 0.0))
            row.update({c: float(cycle) for c in SENSOR_COLS})
            rows.append(row)
    return pd.DataFrame(rows)


def test_engine_id():
    assert engine_id("fd001", "train", 17) == "FD001-train-17"


def test_iter_snapshots_in_cycle_order():
    snaps = list(iter_snapshots(_frame(), 1, "x"))
    assert [s.cycle for s in snaps] == [1, 2, 3, 4, 5]
    assert set(snaps[0].readings) == set(SENSOR_COLS)
    assert "rul" not in snaps[0].readings  # labels never leak into the twin
    with pytest.raises(KeyError):
        list(iter_snapshots(_frame(), 99, "x"))


def test_replay_engine_and_until_cycle():
    twin = replay_engine(_frame(), 1, "FD001", "train")
    assert twin.asset.id == "FD001-train-1" and twin.cycle == 5
    partial = replay_engine(_frame(), 1, "FD001", "train", until_cycle=3)
    assert partial.cycle == 3 and len(partial) == 3


def test_default_ontology_is_cached_and_load_is_fresh():
    assert default_ontology() is default_ontology()
    assert load_ontology() is not load_ontology()


# ---------------------------------------------------------------- real data

requires_data = pytest.mark.skipif(
    not (default_data_dir() / "train_FD001.txt").exists(),
    reason="C-MAPSS not downloaded (python -m mindtwin.data.cmapss download)",
)


@requires_data
@pytest.mark.integration
@pytest.mark.parametrize("subset", SUBSETS)
def test_replay_real_engines(subset):
    data = load_cmapss(subset)
    for split, frame in [("train", data.train), ("test", data.test)]:
        unit = int(frame["unit"].iloc[0])
        twin = replay_engine(frame, unit, subset, split)
        rows = frame[frame["unit"] == unit]
        assert len(twin) == len(rows)
        assert twin.cycle == rows["cycle"].max()
        last = rows.sort_values("cycle").iloc[-1]
        assert twin.state().readings["s11"] == pytest.approx(last["s11"])


@requires_data
@pytest.mark.integration
def test_twin_sees_degradation_fd001():
    """HPC static pressure (s11) rises from the first to the last 20 cycles in most engines."""
    data = load_cmapss("FD001")
    rising = 0
    units = sorted(data.train["unit"].unique())[:20]
    for unit in units:
        s11 = replay_engine(data.train, int(unit), "FD001", "train").sensor_history("s11")
        rising += s11.tail(20).mean() > s11.head(20).mean()
    assert rising >= 18
