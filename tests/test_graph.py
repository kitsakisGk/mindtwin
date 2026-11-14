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
