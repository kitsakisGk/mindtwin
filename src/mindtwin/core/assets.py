"""Build :class:`Asset` objects from the ontology."""

from __future__ import annotations

from rdflib import RDF, RDFS, Graph, URIRef

from mindtwin.core.models import ASSET_LEVEL, Asset, Component, Sensor
from mindtwin.knowledge.ontology import MT, TF, load_ontology


def local_name(uri: URIRef) -> str:
    """``https://.../turbofan#HPC`` -> ``HPC``."""
    text = str(uri)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def asset_from_ontology(
    asset_id: str,
    template: URIRef = TF.ReferenceEngine,
    graph: Graph | None = None,
) -> Asset:
    """Create an asset (e.g. one C-MAPSS engine) from a template individual in the ontology."""
    graph = graph if graph is not None else load_ontology()

    component_uris = sorted(graph.objects(template, MT.hasComponent), key=str)
    if not component_uris:
        raise ValueError(f"Template {template} has no components in the ontology")

    components = {}
    for uri in component_uris:
        cid = local_name(uri)
        components[cid] = Component(
            id=cid,
            label=str(graph.value(uri, RDFS.label) or cid),
            upstream_of=tuple(sorted(local_name(o) for o in graph.objects(uri, MT.upstreamOf))),
            coupled_to=tuple(
                sorted(local_name(o) for o in graph.objects(uri, MT.mechanicallyCoupledTo))
            ),
        )

    component_set = set(component_uris)
    sensors = {}
    for sensor_type, is_control in ((MT.Sensor, False), (MT.ControlSignal, True)):
        for uri in graph.subjects(RDF.type, sensor_type):
            target = graph.value(uri, MT.monitors)
            if target == template:
                component = ASSET_LEVEL
            elif target in component_set:
                component = local_name(target)
            else:
                continue  # sensor of another asset type
            sid = str(graph.value(uri, MT.columnName))
            sensors[sid] = Sensor(
                id=sid,
                symbol=str(graph.value(uri, MT.symbol)),
                label=str(graph.value(uri, RDFS.label)),
                unit=str(graph.value(uri, MT.unit)),
                component=component,
                is_control=is_control,
            )

    asset_type = graph.value(template, RDF.type)
    return Asset(
        id=asset_id,
        type=local_name(asset_type) if asset_type else "Asset",
        components=components,
        sensors=sensors,
    )
