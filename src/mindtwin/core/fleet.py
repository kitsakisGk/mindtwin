"""A fleet of digital twins: routes incoming snapshots to the right twin."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator

import pandas as pd

from mindtwin.core.assets import asset_from_ontology
from mindtwin.core.models import Asset
from mindtwin.core.twin import DigitalTwin, Snapshot, Subscriber


class _Subscription:
    """One fleet-level subscription and the per-twin unsubscribe functions it created."""

    __slots__ = ("callback", "undo")

    def __init__(self, callback: Subscriber, undo: list[Callable[[], None]]):
        self.callback = callback
        self.undo = undo


class Fleet:
    """Twins of many assets of the same type.

    A twin is created automatically the first time a snapshot for a new asset arrives.
    Fleet-level subscribers are attached to every twin, including twins created later.
    """

    def __init__(
        self,
        asset_factory: Callable[[str], Asset] = asset_from_ontology,
        max_history: int | None = None,
    ):
        self._asset_factory = asset_factory
        self._max_history = max_history
        self._twins: dict[str, DigitalTwin] = {}
        self._subscriptions: list[_Subscription] = []

    # ------------------------------------------------------------------ routing

    def ingest(self, snapshot: Snapshot) -> DigitalTwin:
        """Send a snapshot to its asset's twin (creating the twin if needed)."""
        twin = self._twins.get(snapshot.asset_id)
        if twin is None:
            twin = self._create(snapshot.asset_id)
        twin.update(snapshot)
        return twin

    def run(self, items: Iterable) -> int:
        """Ingest a stream of snapshots or stream items (anything with ``.snapshot``)."""
        count = 0
        for item in items:
            self.ingest(getattr(item, "snapshot", item))
            count += 1
        return count

    def _create(self, asset_id: str) -> DigitalTwin:
        twin = DigitalTwin(self._asset_factory(asset_id), max_history=self._max_history)
        for sub in self._subscriptions:
            sub.undo.append(twin.subscribe(sub.callback))
        self._twins[asset_id] = twin
        return twin

    # ------------------------------------------------------------------ subscriptions

    def subscribe(self, callback: Subscriber) -> Callable[[], None]:
        """Attach ``callback(twin, snapshot)`` to all current and future twins.

        Each call is an independent subscription, even for the same callback.
        """
        sub = _Subscription(callback, [t.subscribe(callback) for t in self._twins.values()])
        self._subscriptions.append(sub)

        def unsubscribe() -> None:
            if sub in self._subscriptions:
                self._subscriptions.remove(sub)
                for undo in sub.undo:
                    undo()

        return unsubscribe

    # ------------------------------------------------------------------ queries

    def __getitem__(self, asset_id: str) -> DigitalTwin:
        return self._twins[asset_id]

    def __contains__(self, asset_id: object) -> bool:
        return asset_id in self._twins

    def __iter__(self) -> Iterator[DigitalTwin]:
        return iter(self._twins.values())

    def __len__(self) -> int:
        return len(self._twins)

    def status(self) -> pd.DataFrame:
        """One row per twin: current cycle and number of updates received."""
        rows = [{"asset_id": t.asset.id, "cycle": t.cycle, "updates": t.n_updates} for t in self]
        return pd.DataFrame(rows, columns=["asset_id", "cycle", "updates"]).set_index("asset_id")

    def __repr__(self) -> str:
        return f"Fleet(twins={len(self)})"
