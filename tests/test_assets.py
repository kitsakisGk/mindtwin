import pytest
from pydantic import ValidationError

from mindtwin.core.assets import asset_from_ontology
from mindtwin.core.models import ASSET_LEVEL, Asset, Component, Sensor
from mindtwin.data.cmapss import SENSOR_COLS, SENSOR_INFO


@pytest.fixture(scope="module")
def engine():
    return asset_from_ontology("FD001-unit-1")


def test_engine_from_ontology(engine):
    assert engine.id == "FD001-unit-1"
    assert engine.type == "TurbofanEngine"
    assert len(engine.components) == 10
    assert set(engine.sensors) == set(SENSOR_COLS)


def test_sensor_metadata_matches_data_module(engine):
    for sid, (symbol, label, unit) in SENSOR_INFO.items():
        s = engine.sensors[sid]
        assert (s.symbol, s.label, s.unit) == (symbol, label, unit)


def test_sensor_locations(engine):
    assert engine.sensors_on("HPC") == ["s3", "s7", "s11", "s17"]
    assert engine.sensors_on(ASSET_LEVEL) == ["s10"]
    assert engine.sensors["s18"].is_control
    assert "s18" not in engine.measurement_sensors()
    assert len(engine.measurement_sensors()) == 19


def test_structure_queries(engine):
    assert engine.downstream_of("Fan") == {
        "LPC",
        "HPC",
        "Combustor",
        "HPT",
        "LPT",
        "Nozzle",
        "BypassDuct",
    }
    assert engine.downstream_of("Nozzle") == set()
    assert engine.coupled_with("HPC") == {"HPShaft"}
    assert engine.coupled_with("HPShaft") == {"HPC", "HPT"}


def test_fan_fault_signature_sensors_are_downstream_of_fan(engine):
    """The sensors that lose RUL correlation under the fan fault (data card) sit downstream."""
    downstream = engine.downstream_of("Fan")
    for sid in ["s7", "s12", "s15", "s20", "s21"]:
        assert engine.sensors[sid].component in downstream


def test_asset_is_immutable(engine):
    with pytest.raises(ValidationError):
        engine.id = "other"


def test_invalid_references_rejected():
    comp = Component(id="A", label="A", upstream_of=("Missing",))
    with pytest.raises(ValidationError, match="unknown components"):
        Asset(id="x", type="T", components={"A": comp}, sensors={})
    sensor = Sensor(id="s1", symbol="T", label="t", unit="K", component="Nope")
    with pytest.raises(ValidationError, match="unknown component"):
        Asset(id="x", type="T", components={}, sensors={"s1": sensor})


def test_unknown_template_rejected():
    from mindtwin.knowledge.ontology import TF

    with pytest.raises(ValueError, match="no components"):
        asset_from_ontology("x", template=TF.DoesNotExist)
