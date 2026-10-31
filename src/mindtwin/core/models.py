"""Asset model: what the twin is a twin of.

An :class:`Asset` holds its :class:`Component` parts and :class:`Sensor` set, with the
structural relations needed for reasoning (flow order, mechanical coupling, sensor location).
Assets are normally built from the ontology with :func:`mindtwin.core.assets.asset_from_ontology`.
"""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

ASSET_LEVEL = "engine"
"""Component id used for sensors that monitor the whole asset rather than one part."""


class Component(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    label: str
    upstream_of: tuple[str, ...] = ()
    coupled_to: tuple[str, ...] = ()


class Sensor(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Column name in the data, e.g. 's11'")
    symbol: str
    label: str
    unit: str
    component: str = Field(description=f"Monitored component id, or '{ASSET_LEVEL}'")
    is_control: bool = Field(False, description="Recorded set-point, not a measurement")


class Asset(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    type: str
    components: Mapping[str, Component]
    sensors: Mapping[str, Sensor]

    @model_validator(mode="after")
    def _check_references(self) -> Asset:
        known = set(self.components)
        for c in self.components.values():
            missing = (set(c.upstream_of) | set(c.coupled_to)) - known
            if missing:
                raise ValueError(f"Component {c.id} refers to unknown components {missing}")
        for s in self.sensors.values():
            if s.component != ASSET_LEVEL and s.component not in known:
                raise ValueError(f"Sensor {s.id} monitors unknown component {s.component}")
        return self

    def sensors_on(self, component: str) -> list[str]:
        """Sensor ids that monitor ``component``."""
        return sorted(
            (s.id for s in self.sensors.values() if s.component == component), key=_natural
        )

    def downstream_of(self, component: str) -> set[str]:
        """All components reachable from ``component`` along the flow path."""
        seen: set[str] = set()
        stack = [component]
        while stack:
            for nxt in self.components[stack.pop()].upstream_of:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    def coupled_with(self, component: str) -> set[str]:
        """Components mechanically coupled to ``component`` (relation is symmetric)."""
        direct = set(self.components[component].coupled_to)
        reverse = {c.id for c in self.components.values() if component in c.coupled_to}
        return direct | reverse

    def measurement_sensors(self) -> list[str]:
        """Sensor ids that are physical measurements (control signals excluded)."""
        return sorted((s.id for s in self.sensors.values() if not s.is_control), key=_natural)


def _natural(sensor_id: str) -> tuple[str, int]:
    """Sort 's2' before 's10'."""
    head = sensor_id.rstrip("0123456789")
    tail = sensor_id[len(head) :]
    return head, int(tail) if tail else -1
