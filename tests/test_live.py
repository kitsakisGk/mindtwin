import math

import pytest

from mindtwin.core.fleet import Fleet
from mindtwin.core.twin import Snapshot
from mindtwin.data.cmapss import default_data_dir
from mindtwin.knowledge.graph import KnowledgeGraph
from mindtwin.knowledge.live import LiveView


@pytest.fixture
def view():
    fleet = Fleet(knowledge=KnowledgeGraph())
    for c in range(1, 13):
        readings = {"s11": 47.0 + 0.1 * c, "s7": 554.0 - 0.2 * c, "s2": 642.0, "s21": 23.4}
        fleet.ingest(Snapshot(asset_id="e1", cycle=c, readings=readings))
    return LiveView(fleet)


def test_requires_knowledge_graph():
    with pytest.raises(ValueError, match="no knowledge graph"):
        LiveView(Fleet())


def test_component_readings(view):
    assert view.component_readings("e1", "HPC") == {
        "s7": pytest.approx(551.6),
        "s11": pytest.approx(48.2),
    }
    assert view.component_readings("e1", "Fan") == {}  # no fan sensors reported
    with pytest.raises(KeyError, match="No twin"):
        view.component_readings("nope", "HPC")


def test_component_readings_before_any_data():
    fleet = Fleet(knowledge=KnowledgeGraph())
    fleet.knowledge.add_asset(fleet._asset_factory("e9"))
    fleet._create("e9")
    assert LiveView(fleet).component_readings("e9", "HPC") == {}


def test_fault_region_readings(view):
    region = view.fault_region_readings("e1", "HPCDegradation")
    assert set(region) == {"HPC", "LPT"}  # components in the region that have readings
    assert "LPC" not in region  # s2 sits upstream of the HPC
    with pytest.raises(KeyError, match="Unknown fault"):
        view.fault_region_readings("e1", "Nope")


def test_sensor_context(view):
    ctx = view.sensor_context("e1", "s11", window=5)
    assert ctx["component"] == "HPC" and ctx["symbol"] == "Ps30" and ctx["unit"] == "psia"
    assert ctx["candidate_faults"] == ["FanDegradation", "HPCDegradation"]
    assert ctx["cycle"] == 12 and ctx["value"] == pytest.approx(48.2)
    assert ctx["trend"]["slope"] == pytest.approx(0.1)
    assert ctx["trend"]["mean"] == pytest.approx(48.0)


def test_sensor_context_for_unreported_sensor(view):
    ctx = view.sensor_context("e1", "s1")
    assert math.isnan(ctx["value"]) and ctx["candidate_faults"] == ["FanDegradation"]


@pytest.mark.skipif(
    not (default_data_dir() / "test_FD001.txt").exists(), reason="C-MAPSS not downloaded"
)
@pytest.mark.integration
def test_sensor_context_on_real_failing_engine():
    """Near the end of a training run, HPC static pressure (s11) is rising."""
    from mindtwin.data.cmapss import load_cmapss
    from mindtwin.data.stream import fleet_stream

    data = load_cmapss("FD001")
    fleet = Fleet(knowledge=KnowledgeGraph())
    fleet.run(fleet_stream(data.train, "FD001", "train", units=[1]))
    ctx = LiveView(fleet).sensor_context("FD001-train-1", "s11", window=30)
    assert ctx["cycle"] == 192 and ctx["trend"]["slope"] > 0
