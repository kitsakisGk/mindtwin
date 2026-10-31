"""Turn C-MAPSS engines into twins by replaying their data cycle by cycle."""

from __future__ import annotations

from collections.abc import Iterator

import pandas as pd

from mindtwin.core.assets import asset_from_ontology
from mindtwin.core.models import Asset
from mindtwin.core.twin import DigitalTwin, Snapshot
from mindtwin.data.cmapss import SENSOR_COLS, SETTING_COLS


def engine_id(subset: str, split: str, unit: int) -> str:
    """Stable asset id, e.g. ``FD001-train-17``."""
    return f"{subset.upper()}-{split}-{unit}"


def iter_snapshots(frame: pd.DataFrame, unit: int, asset_id: str) -> Iterator[Snapshot]:
    """Snapshots of one unit in cycle order."""
    rows = frame[frame["unit"] == unit].sort_values("cycle")
    if rows.empty:
        raise KeyError(f"Unit {unit} not found")
    for row in rows.to_dict("records"):
        yield Snapshot.from_row(row, asset_id, SENSOR_COLS, SETTING_COLS)


def replay_engine(
    frame: pd.DataFrame,
    unit: int,
    subset: str,
    split: str,
    asset: Asset | None = None,
    until_cycle: int | None = None,
) -> DigitalTwin:
    """Create a twin for one engine and replay its data (optionally only up to ``until_cycle``)."""
    asset_id = engine_id(subset, split, unit)
    twin = DigitalTwin(asset or asset_from_ontology(asset_id))
    for snapshot in iter_snapshots(frame, unit, asset_id):
        if until_cycle is not None and snapshot.cycle > until_cycle:
            break
        twin.update(snapshot)
    return twin
