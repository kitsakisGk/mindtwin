import pytest

from mindtwin.core.assets import asset_from_ontology
from mindtwin.knowledge.graph import KnowledgeGraph


@pytest.fixture
def kg():
    kg = KnowledgeGraph()
    kg.add_asset(asset_from_ontology("FD001-test-1"))
    kg.add_asset(asset_from_ontology("FD001-test-2"))
    return kg


def test_assets_registered(kg):
    assert kg.assets() == ["FD001-test-1", "FD001-test-2"]
    assert kg.has_asset("FD001-test-1") and not kg.has_asset("FD001-test-3")


def test_add_asset_is_idempotent(kg):
    n = len(kg)
    kg.add_asset(asset_from_ontology("FD001-test-1"))
    assert len(kg) == n


def test_instances_link_to_templates(kg):
    rows = kg.query(
        """
        SELECT ?col WHERE {
            inst:FD001-test-1 mt:hasSensor ?s .
            ?s mt:monitors ?c ; mt:columnName ?col .
            ?c mt:basedOn tf:HPC .
        } ORDER BY ?col
        """
    )
    assert sorted(r["col"] for r in rows) == ["s11", "s17", "s3", "s7"]


def test_engines_do_not_share_individuals(kg):
    rows = kg.query(
        """
        SELECT ?s WHERE { inst:FD001-test-2 mt:hasSensor ?s . ?s mt:columnName "s11" . }
        """
    )
    assert len(rows) == 1 and rows[0]["s"].endswith("FD001-test-2/s11")


def test_engine_type_from_template(kg):
    rows = kg.query("SELECT ?t WHERE { inst:FD001-test-1 a ?t . }")
    assert [r["t"].rsplit("#", 1)[-1] for r in rows] == ["TurbofanEngine"]


def test_ontology_still_has_no_hand_written_symptoms(kg):
    assert kg.query("SELECT ?f WHERE { ?f mt:hasSymptom ?s . }") == []


def test_save_and_load_roundtrip(kg, tmp_path):
    path = tmp_path / "fleet.ttl"
    kg.save(path)
    again = KnowledgeGraph.load(path)
    assert len(again) == len(kg)
    assert again.assets() == kg.assets()


# ---------------------------------------------------------------- structural queries


def test_sensors_on_and_component_of(kg):
    assert kg.sensors_on("FD001-test-1", "HPC") == ["s3", "s7", "s11", "s17"]
    assert kg.sensors_on("FD001-test-1", "engine") == ["s10"]
    assert kg.component_of("FD001-test-1", "s21") == "LPT"
    assert kg.component_of("FD001-test-1", "s10") == "engine"


def test_unknown_asset_or_sensor(kg):
    with pytest.raises(KeyError, match="Unknown asset"):
        kg.sensors_on("nope", "HPC")
    with pytest.raises(KeyError, match="no sensor"):
        kg.component_of("FD001-test-1", "s99")


def test_downstream_matches_asset_model(kg):
    asset = asset_from_ontology("FD001-test-1")
    for comp in asset.components:
        assert kg.downstream_of("FD001-test-1", comp) == asset.downstream_of(comp)


def test_affected_region_follows_flow_then_one_shaft_hop(kg):
    region = kg.affected_region("FD001-test-1", "HPC")
    assert region == {"HPC", "Combustor", "HPT", "LPT", "Nozzle", "HPShaft", "LPShaft"}
    assert "Fan" not in region and "LPC" not in region  # upstream of HPC
    assert kg.affected_region("FD001-test-1", "Nozzle") == {"Nozzle"}


def test_fault_modes(kg):
    assert kg.fault_modes() == {"HPCDegradation": "HPC", "FanDegradation": "Fan"}


@pytest.mark.parametrize(
    "sensor, expected",
    [
        ("s11", ["FanDegradation", "HPCDegradation"]),  # HPC: own fault + fan upstream
        ("s21", ["FanDegradation", "HPCDegradation"]),  # LPT: downstream of both
        ("s8", ["FanDegradation", "HPCDegradation"]),  # LP shaft: driven by LPT
        ("s1", ["FanDegradation"]),  # fan inlet: upstream of the HPC
        ("s2", ["FanDegradation"]),  # LPC outlet: upstream of the HPC
        ("s15", ["FanDegradation"]),  # bypass duct: fed by the fan only
        ("s10", ["FanDegradation", "HPCDegradation"]),  # whole-engine ratio
    ],
)
def test_candidate_faults(kg, sensor, expected):
    assert kg.candidate_faults("FD001-test-1", sensor) == expected
