import pytest
from rdflib import RDF, RDFS, Literal

from mindtwin.data.cmapss import SENSOR_COLS, SENSOR_INFO
from mindtwin.knowledge.ontology import MT, TF, load_ontology


@pytest.fixture(scope="module")
def graph():
    return load_ontology()


def _sensors(graph):
    types = {MT.Sensor, MT.ControlSignal}
    return {s for t in types for s in graph.subjects(RDF.type, t)}


def test_all_cmapss_sensors_described(graph):
    columns = {str(graph.value(s, MT.columnName)) for s in _sensors(graph)}
    assert columns == set(SENSOR_COLS)


def test_sensor_symbols_match_data_module(graph):
    for s in _sensors(graph):
        col = str(graph.value(s, MT.columnName))
        assert graph.value(s, MT.symbol) == Literal(SENSOR_INFO[col][0])


def test_each_sensor_monitors_exactly_one_thing(graph):
    components = set(graph.subjects(RDF.type, MT.Component)) | {TF.ReferenceEngine}
    for s in _sensors(graph):
        targets = list(graph.objects(s, MT.monitors))
        assert len(targets) == 1, s
        assert targets[0] in components, s


def test_engine_has_all_components(graph):
    components = set(graph.subjects(RDF.type, MT.Component))
    assert set(graph.objects(TF.ReferenceEngine, MT.hasComponent)) == components


def test_gas_path_is_acyclic_and_reaches_nozzle(graph):
    edges = {}
    for a, b in graph.subject_objects(MT.upstreamOf):
        edges.setdefault(a, set()).add(b)

    def reachable(start):
        seen, stack = set(), [start]
        while stack:
            for nxt in edges.get(stack.pop(), ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    for node in edges:
        assert node not in reachable(node), f"cycle through {node}"
    assert TF.Nozzle in reachable(TF.Fan)


def test_fault_modes_affect_components(graph):
    faults = set(graph.subjects(RDF.type, MT.FaultMode))
    assert faults == {TF.HPCDegradation, TF.FanDegradation}
    for f in faults:
        assert graph.value(f, MT.affects) is not None
        assert graph.value(f, RDFS.label) is not None


def test_no_hand_written_symptoms(graph):
    """Symptoms must be learned from data, not asserted in the ontology."""
    assert list(graph.subject_objects(MT.hasSymptom)) == []


def test_sparql_sensors_on_hpc(graph):
    rows = graph.query(
        """
        SELECT ?col WHERE {
            ?s mt:monitors tf:HPC ; mt:columnName ?col .
        } ORDER BY ?col
        """
    )
    assert sorted(str(r.col) for r in rows) == ["s11", "s17", "s3", "s7"]
