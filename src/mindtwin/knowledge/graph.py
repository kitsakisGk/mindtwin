"""Fleet knowledge graph: the ontology plus one set of individuals per asset.

One graph holds the whole fleet (ADR 0001). Each asset gets its own individuals, linked to the
template they come from with ``mt:basedOn``::

    inst:E1      a tf:TurbofanEngine ; mt:basedOn tf:ReferenceEngine ;
                 mt:hasComponent inst:E1/HPC ; mt:hasSensor inst:E1/s11 .
    inst:E1/HPC  a mt:Component ; mt:basedOn tf:HPC ; mt:upstreamOf inst:E1/Combustor .
    inst:E1/s11  a mt:Sensor ; mt:basedOn tf:s11 ; mt:monitors inst:E1/HPC .

The public API uses plain strings (asset ids, component ids, sensor column names) so callers do
not depend on rdflib.
"""

from __future__ import annotations

from pathlib import Path

from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef

from mindtwin.core.models import ASSET_LEVEL, Asset
from mindtwin.knowledge.ontology import MT, SOSA, TF, load_ontology

INST = Namespace("https://kitsakisgk.github.io/mindtwin/instance/")


class KnowledgeGraph:
    """Ontology + asset individuals, with simple string-based queries."""

    def __init__(self, graph: Graph | None = None):
        self._g = graph if graph is not None else load_ontology()
        self._g.bind("inst", INST)

    # ------------------------------------------------------------------ uris

    @staticmethod
    def asset_uri(asset_id: str) -> URIRef:
        return INST[asset_id]

    @staticmethod
    def part_uri(asset_id: str, part_id: str) -> URIRef:
        return INST[f"{asset_id}/{part_id}"]

    # ------------------------------------------------------------------ building

    def add_asset(self, asset: Asset, template: URIRef = TF.ReferenceEngine) -> URIRef:
        """Add an asset's individuals (idempotent). Returns the asset URI."""
        g, a = self._g, self.asset_uri(asset.id)
        if (a, MT.basedOn, None) in g:
            return a
        g.add((a, RDF.type, g.value(template, RDF.type) or MT.Asset))
        g.add((a, MT.basedOn, template))
        g.add((a, RDFS.label, Literal(asset.id)))

        for cid, comp in asset.components.items():
            c = self.part_uri(asset.id, cid)
            g.add((c, RDF.type, MT.Component))
            g.add((c, MT.basedOn, TF[cid]))
            g.add((a, MT.hasComponent, c))
            g.add((c, MT.partOf, a))
            for nxt in comp.upstream_of:
                g.add((c, MT.upstreamOf, self.part_uri(asset.id, nxt)))
            for other in comp.coupled_to:
                g.add((c, MT.mechanicallyCoupledTo, self.part_uri(asset.id, other)))

        for sid, sensor in asset.sensors.items():
            s = self.part_uri(asset.id, sid)
            g.add((s, RDF.type, MT.ControlSignal if sensor.is_control else MT.Sensor))
            g.add((s, MT.basedOn, TF[sid]))
            g.add((s, MT.columnName, Literal(sid)))
            g.add((a, MT.hasSensor, s))
            target = (
                a if sensor.component == ASSET_LEVEL else self.part_uri(asset.id, sensor.component)
            )
            g.add((s, MT.monitors, target))
        return a

    # ------------------------------------------------------------------ inspection

    def has_asset(self, asset_id: str) -> bool:
        return (self.asset_uri(asset_id), MT.basedOn, None) in self._g

    def assets(self) -> list[str]:
        """Ids of all asset individuals in the graph."""
        ids = []
        for a in self._g.subjects(MT.hasComponent, None, unique=True):
            if str(a).startswith(str(INST)):
                ids.append(str(a)[len(str(INST)) :])
        return sorted(ids)

    def __len__(self) -> int:
        return len(self._g)

    def query(self, sparql: str) -> list[dict[str, str]]:
        """Run SPARQL (prefixes mt, tf, inst, sosa, rdfs pre-declared); values as strings."""
        prefixes = {"mt": MT, "tf": TF, "inst": INST, "sosa": SOSA, "rdfs": RDFS}
        result = self._g.query(sparql, initNs=prefixes)
        return [{str(k): str(v) for k, v in row.asdict().items()} for row in result]

    # ------------------------------------------------------------------ structural queries

    def _require(self, asset_id: str) -> URIRef:
        if not self.has_asset(asset_id):
            raise KeyError(f"Unknown asset {asset_id!r}")
        return self.asset_uri(asset_id)

    def _local(self, asset_id: str, uri: URIRef) -> str:
        """Instance URI -> component/sensor id; the asset itself -> ASSET_LEVEL."""
        if uri == self.asset_uri(asset_id):
            return ASSET_LEVEL
        return str(uri).rsplit("/", 1)[-1]

    def _sensor(self, asset_id: str, sensor: str) -> URIRef:
        a = self._require(asset_id)
        s = self.part_uri(asset_id, sensor)
        if (a, MT.hasSensor, s) not in self._g:
            raise KeyError(f"Asset {asset_id!r} has no sensor {sensor!r}")
        return s

    def sensors_on(self, asset_id: str, component: str) -> list[str]:
        """Sensor column names that monitor ``component`` of ``asset_id``."""
        a = self._require(asset_id)
        target = a if component == ASSET_LEVEL else self.part_uri(asset_id, component)
        cols = [
            str(self._g.value(s, MT.columnName))
            for s in self._g.subjects(MT.monitors, target)
            if (a, MT.hasSensor, s) in self._g
        ]
        return sorted(cols, key=lambda c: (len(c), c))

    def component_of(self, asset_id: str, sensor: str) -> str:
        """Component monitored by ``sensor`` (``ASSET_LEVEL`` for whole-engine sensors)."""
        return self._local(asset_id, self._g.value(self._sensor(asset_id, sensor), MT.monitors))

    def downstream_of(self, asset_id: str, component: str) -> set[str]:
        """Components reachable from ``component`` along the flow path (transitive)."""
        self._require(asset_id)
        start = self.part_uri(asset_id, component)
        return {
            self._local(asset_id, c) for c in self._g.transitive_objects(start, MT.upstreamOf)
        } - {component}

    def affected_region(self, asset_id: str, component: str) -> set[str]:
        """Where a fault in ``component`` can show up, by structure alone.

        The component itself, everything downstream of it in the flow path, and the shafts
        mechanically coupled to any of those. Coupling is followed one hop only (to the shaft,
        not back through it), otherwise every component would reach every other one.
        """
        region = {component} | self.downstream_of(asset_id, component)
        shafts = set()
        for cid in region:
            c = self.part_uri(asset_id, cid)
            for other in self._g.objects(c, MT.mechanicallyCoupledTo):
                shafts.add(self._local(asset_id, other))
            for other in self._g.subjects(MT.mechanicallyCoupledTo, c):
                shafts.add(self._local(asset_id, other))
        return region | shafts

    def fault_modes(self) -> dict[str, str]:
        """All fault modes and the (template) component each one affects."""
        return {
            str(f).rsplit("#", 1)[-1]: str(self._g.value(f, MT.affects)).rsplit("#", 1)[-1]
            for f in self._g.subjects(RDF.type, MT.FaultMode)
        }

    def candidate_faults(self, asset_id: str, sensor: str) -> list[str]:
        """Fault modes that could, by structure, explain unusual readings on ``sensor``.

        This is a structural prior only. Fault signatures learned from data (``mt:hasSymptom``)
        will refine it, since real faults can also show up outside their structural region.
        """
        target = self.component_of(asset_id, sensor)
        faults = self.fault_modes()
        if target == ASSET_LEVEL:  # whole-engine sensor: any fault can show up
            return sorted(faults)
        return sorted(
            f for f, comp in faults.items() if target in self.affected_region(asset_id, comp)
        )

    # ------------------------------------------------------------------ persistence

    def save(self, path: str | Path) -> None:
        """Write the graph as Turtle."""
        self._g.serialize(destination=str(path), format="turtle", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> KnowledgeGraph:
        g = Graph()
        g.parse(str(path), format="turtle")
        return cls(g)
