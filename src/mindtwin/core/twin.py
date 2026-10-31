"""The digital twin of one asset: current state, history and change notifications."""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Callable, Iterable, Mapping

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from mindtwin.core.models import Asset
from mindtwin.log import get_logger

log = get_logger(__name__)


class Snapshot(BaseModel):
    """State of an asset at one operating cycle."""

    model_config = ConfigDict(frozen=True)

    asset_id: str
    cycle: int = Field(ge=0)
    settings: Mapping[str, float] = Field(default_factory=dict)
    readings: Mapping[str, float] = Field(default_factory=dict)

    @classmethod
    def from_row(
        cls,
        row: Mapping[str, object],
        asset_id: str,
        sensor_cols: Iterable[str],
        setting_cols: Iterable[str] = (),
    ) -> Snapshot:
        """Build a snapshot from one data row (e.g. a C-MAPSS DataFrame row)."""
        return cls(
            asset_id=asset_id,
            cycle=int(row["cycle"]),
            settings={c: float(row[c]) for c in setting_cols},
            readings={c: float(row[c]) for c in sensor_cols},
        )


Subscriber = Callable[["DigitalTwin", Snapshot], None]


class DigitalTwin:
    """Twin of one asset.

    >>> twin = DigitalTwin(asset)
    >>> twin.update(snapshot)
    >>> twin.state().readings["s11"]
    """

    def __init__(self, asset: Asset, max_history: int | None = None):
        if max_history is not None and max_history < 1:
            raise ValueError("max_history must be at least 1")
        self.asset = asset
        self._history: deque[Snapshot] = deque(maxlen=max_history)
        self._subscribers: list[Subscriber] = []
        self._frame_cache: pd.DataFrame | None = None
        self._updates = 0

    # ------------------------------------------------------------------ updates

    def update(self, snapshot: Snapshot) -> None:
        """Ingest a new snapshot, then notify subscribers."""
        self._validate(snapshot)
        self._history.append(snapshot)
        self._frame_cache = None
        self._updates += 1
        for callback in list(self._subscribers):
            try:
                callback(self, snapshot)
            except Exception:  # a broken subscriber must not break the twin
                log.exception(
                    "Subscriber %r failed on %s cycle %s", callback, self.asset.id, snapshot.cycle
                )

    def update_many(self, snapshots: Iterable[Snapshot]) -> None:
        for snapshot in snapshots:
            self.update(snapshot)

    def _validate(self, snapshot: Snapshot) -> None:
        if snapshot.asset_id != self.asset.id:
            raise ValueError(
                f"Snapshot for {snapshot.asset_id!r} sent to twin of {self.asset.id!r}"
            )
        last = self.cycle
        if last is not None and snapshot.cycle <= last:
            raise ValueError(f"Cycle {snapshot.cycle} is not after current cycle {last}")
        unknown = set(snapshot.readings) - set(self.asset.sensors)
        if unknown:
            raise ValueError(f"Unknown sensors for {self.asset.id}: {sorted(unknown)}")
        bad = [k for k, v in snapshot.readings.items() if math.isinf(v)]
        if bad:
            raise ValueError(f"Infinite readings for {sorted(bad)}")

    # ------------------------------------------------------------------ subscriptions

    def subscribe(self, callback: Subscriber) -> Callable[[], None]:
        """Call ``callback(twin, snapshot)`` after every update. Returns an unsubscribe function."""
        self._subscribers.append(callback)

        def unsubscribe() -> None:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        return unsubscribe

    # ------------------------------------------------------------------ queries

    @property
    def cycle(self) -> int | None:
        """Current cycle, or ``None`` before the first update."""
        return self._history[-1].cycle if self._history else None

    @property
    def n_updates(self) -> int:
        """Total snapshots received (can exceed ``len(self)`` when history is bounded)."""
        return self._updates

    def __len__(self) -> int:
        return len(self._history)

    def state(self) -> Snapshot | None:
        """Latest snapshot, or ``None`` before the first update."""
        return self._history[-1] if self._history else None

    def history(self, window: int | None = None) -> pd.DataFrame:
        """History as a DataFrame indexed by cycle (last ``window`` cycles if given)."""
        if self._frame_cache is None:
            rows = [{"cycle": s.cycle, **s.settings, **s.readings} for s in self._history]
            frame = pd.DataFrame(rows)
            self._frame_cache = frame.set_index("cycle") if rows else frame
        frame = self._frame_cache
        return frame.tail(window).copy() if window is not None else frame.copy()

    def sensor_history(self, sensor: str, window: int | None = None) -> pd.Series:
        if sensor not in self.asset.sensors:
            raise KeyError(f"Unknown sensor {sensor!r}")
        frame = self.history(window)
        if sensor not in frame:
            return pd.Series(dtype=float, name=sensor)
        return frame[sensor]

    def component_state(self, component: str) -> dict[str, float]:
        """Latest readings of the sensors that monitor ``component``."""
        state = self.state()
        if state is None:
            return {}
        return {
            s: state.readings[s] for s in self.asset.sensors_on(component) if s in state.readings
        }

    def __repr__(self) -> str:
        return f"DigitalTwin(asset={self.asset.id!r}, cycle={self.cycle}, history={len(self)})"
