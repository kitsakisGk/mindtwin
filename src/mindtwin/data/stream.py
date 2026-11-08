"""Simulated live data: a fleet of engines streaming one cycle at a time on a shared clock.

Each engine joins the fleet at a start tick and then reports one cycle per tick until its data
ends. Items come out ordered by tick, then by unit, so the order is deterministic.

    for item in fleet_stream(data.test, "FD001", "test", units=[1, 2, 3], stagger=50, seed=0):
        twin = fleet.ingest(item.snapshot)

``paced()`` slows a stream down to a chosen number of ticks per second for demos.
"""

from __future__ import annotations

import heapq
import time
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import NamedTuple

import numpy as np
import pandas as pd

from mindtwin.core.twin import Snapshot
from mindtwin.data.cmapss import SENSOR_COLS, SETTING_COLS
from mindtwin.data.replay import engine_id


class StreamItem(NamedTuple):
    tick: int
    unit: int
    snapshot: Snapshot


def start_ticks(units: Sequence[int], stagger: int = 0, seed: int | None = 0) -> dict[int, int]:
    """Start tick per unit: 0 for all when ``stagger`` is 0, else uniform in [0, stagger]."""
    if stagger < 0:
        raise ValueError("stagger must be >= 0")
    if stagger == 0:
        return dict.fromkeys(units, 0)
    rng = np.random.default_rng(seed)
    return {u: int(t) for u, t in zip(units, rng.integers(0, stagger + 1, len(units)), strict=True)}


def fleet_stream(
    frame: pd.DataFrame,
    subset: str,
    split: str,
    units: Sequence[int] | None = None,
    stagger: int = 0,
    seed: int | None = 0,
) -> Iterator[StreamItem]:
    """Interleave the engines in ``frame`` on a shared clock.

    An engine starting at tick ``s`` reports its k-th cycle (k = 0, 1, ...) at tick ``s + k``.
    """
    if units is None:
        units = sorted(int(u) for u in frame["unit"].unique())
    missing = set(units) - set(frame["unit"].unique())
    if missing:
        raise KeyError(f"Units not in data: {sorted(missing)}")
    starts = start_ticks(units, stagger, seed)

    def engine_items(unit: int) -> Iterator[StreamItem]:
        rows = frame[frame["unit"] == unit].sort_values("cycle")
        asset_id = engine_id(subset, split, unit)
        for k, row in enumerate(rows.to_dict("records")):
            snap = Snapshot.from_row(row, asset_id, SENSOR_COLS, SETTING_COLS)
            yield StreamItem(starts[unit] + k, unit, snap)

    # Merge the per-engine streams lazily, ordered by (tick, unit).
    yield from heapq.merge(*(engine_items(u) for u in units), key=lambda it: (it.tick, it.unit))


def paced(
    items: Iterable[StreamItem],
    ticks_per_second: float,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[StreamItem]:
    """Yield items no faster than ``ticks_per_second`` (all items of one tick together)."""
    if ticks_per_second <= 0:
        raise ValueError("ticks_per_second must be > 0")
    period = 1.0 / ticks_per_second
    first_tick: int | None = None
    t0 = clock()
    for item in items:
        if first_tick is None:
            first_tick = item.tick
        due = t0 + (item.tick - first_tick) * period
        wait = due - clock()
        if wait > 0:
            sleep(wait)
        yield item


def main(argv: Sequence[str] | None = None) -> None:
    """Watch a simulated fleet: ``python -m mindtwin.data.stream --engines 5 --speed 10``."""
    import argparse
    from pathlib import Path

    from mindtwin.core.fleet import Fleet
    from mindtwin.data.cmapss import load_cmapss

    parser = argparse.ArgumentParser(prog="python -m mindtwin.data.stream")
    parser.add_argument("--subset", default="FD001")
    parser.add_argument("--split", choices=["train", "test"], default="test")
    parser.add_argument("--engines", type=int, default=5, help="first N engines")
    parser.add_argument("--stagger", type=int, default=20, help="max start delay in ticks")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--speed", type=float, default=0, help="ticks per second (0 = max)")
    parser.add_argument("--every", type=int, default=25, help="print status every N ticks")
    parser.add_argument("--sensor", default="s11", help="sensor shown in the status")
    parser.add_argument("--data-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    data = load_cmapss(args.subset, args.data_dir)
    frame = data.train if args.split == "train" else data.test
    units = sorted(int(u) for u in frame["unit"].unique())[: args.engines]
    items: Iterable[StreamItem] = fleet_stream(
        frame, args.subset, args.split, units, args.stagger, args.seed
    )
    if args.speed > 0:
        items = paced(items, args.speed)

    fleet = Fleet()

    def show(tick: int) -> None:
        cells = []
        for twin in fleet:
            value = twin.state().readings.get(args.sensor, float("nan"))
            cells.append(f"#{twin.asset.id.rsplit('-', 1)[-1]}:c{twin.cycle} {value:.2f}")
        print(f"tick {tick:>4} | {len(fleet)} engines | {args.sensor} | " + "  ".join(cells))

    last_tick = None
    for item in items:
        if last_tick is not None and item.tick != last_tick and last_tick % args.every == 0:
            show(last_tick)
        fleet.ingest(item.snapshot)
        last_tick = item.tick
    if last_tick is not None:
        show(last_tick)
    print(f"done: {len(fleet)} engines, {int(fleet.status()['updates'].sum())} snapshots")


if __name__ == "__main__":
    main()
