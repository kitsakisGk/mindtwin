"""Ontology files and helpers to load them.

``mindtwin.ttl`` holds the domain-independent core; ``turbofan.ttl`` specialises it for the
C-MAPSS engine.
"""

from __future__ import annotations

from importlib import resources

from rdflib import Graph, Namespace

MT = Namespace("https://kitsakisgk.github.io/mindtwin/ontology#")
TF = Namespace("https://kitsakisgk.github.io/mindtwin/turbofan#")
SOSA = Namespace("http://www.w3.org/ns/sosa/")

ONTOLOGY_FILES = {"core": "mindtwin.ttl", "turbofan": "turbofan.ttl"}


def load_ontology(*names: str) -> Graph:
    """Load one or more ontologies into a single graph (default: core + turbofan)."""
    names = names or tuple(ONTOLOGY_FILES)
    graph = Graph()
    graph.bind("mt", MT)
    graph.bind("tf", TF)
    graph.bind("sosa", SOSA)
    for name in names:
        source = resources.files(__name__).joinpath(ONTOLOGY_FILES[name])
        graph.parse(data=source.read_text(encoding="utf-8"), format="turtle")
    return graph
