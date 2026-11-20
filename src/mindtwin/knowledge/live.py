"""Live view: structure from the knowledge graph joined with values from the twins.

Per ADR 0001, sensor values stay in the twins (time series) and the graph holds structure; the
two are joined at query time. This is the context the reasoning layer and the agent use, e.g.
"what does engine 42's HPC show right now, and which faults could explain it?".
"""

from __future__ import annotations

import math
from typing import Any

from mindtwin.core.fleet import Fleet
from mindtwin.data.features import DEFAULT_WINDOW, latest_features


class LiveView:
    """Read-only queries combining a fleet's knowledge graph and its twins."""

    def __init__(self, fleet: Fleet):
        if fleet.knowledge is None:
            raise ValueError(
                "The fleet has no knowledge graph (create it with Fleet(knowledge=...))"
            )
        self.fleet = fleet
        self.kg = fleet.knowledge

    def _twin(self, asset_id: str):
        if asset_id not in self.fleet:
            raise KeyError(f"No twin for asset {asset_id!r}")
        return self.fleet[asset_id]

    def component_readings(self, asset_id: str, component: str) -> dict[str, float]:
        """Latest readings of the sensors the graph says monitor ``component``."""
        state = self._twin(asset_id).state()
        if state is None:
            return {}
        sensors = self.kg.sensors_on(asset_id, component)
        return {s: state.readings[s] for s in sensors if s in state.readings}

    def fault_region_readings(self, asset_id: str, fault: str) -> dict[str, dict[str, float]]:
        """Latest readings, per component, in the structural region a fault can affect."""
        faults = self.kg.fault_modes()
        if fault not in faults:
            raise KeyError(f"Unknown fault mode {fault!r}; known: {sorted(faults)}")
        region = self.kg.affected_region(asset_id, faults[fault])
        out = {}
        for component in sorted(region):
            readings = self.component_readings(asset_id, component)
            if readings:
                out[component] = readings
        return out

    def sensor_context(
        self, asset_id: str, sensor: str, window: int = DEFAULT_WINDOW, normalizer=None
    ) -> dict[str, Any]:
        """Everything known about one sensor of one engine, right now.

        Structure (component, structural fault candidates) from the graph; value and recent
        trend (window mean, std, slope) from the twin.
        """
        twin = self._twin(asset_id)
        state = twin.state()
        value = state.readings.get(sensor, math.nan) if state is not None else math.nan
        feats = latest_features(twin, [sensor], window=window, normalizer=normalizer)
        trend = {k.split("_", 1)[1]: float(v) for k, v in feats.items()} if not feats.empty else {}
        return {
            "asset_id": asset_id,
            "sensor": sensor,
            "symbol": twin.asset.sensors[sensor].symbol,
            "unit": twin.asset.sensors[sensor].unit,
            "component": self.kg.component_of(asset_id, sensor),
            "candidate_faults": self.kg.candidate_faults(asset_id, sensor),
            "cycle": twin.cycle,
            "value": value,
            "window": window,
            "trend": trend,
        }
