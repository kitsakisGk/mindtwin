# ADR 0001: Storage for twin state, history, knowledge and memory

**Status:** accepted · **Date:** 2026-10-31

## Context

The twin needs to store four kinds of data:

| Data | Shape | Size (C-MAPSS) | Access pattern |
|---|---|---|---|
| Current state | One snapshot per asset | Tiny | Read constantly |
| Sensor history | Time series per asset | Largest subset FD004 train: 61k rows, ~13 MB in pandas | Append per cycle; read recent windows for models |
| Knowledge graph | RDF triples | Ontology (~350 triples) + 709 engines × 160 triples (measured 2026-11-14): ~114k triples | Graph queries (SPARQL), small writes |
| Episodic memory | Events (anomalies, prognoses, decisions) | Thousands | Append; search by asset, time, type |

Constraints from the research plan: **reproducible** (anyone can clone and run, no services to
install), **swappable** components, fast enough to replay the full test sets in experiments.

## Options considered

1. **Dedicated servers**: a time-series DB (InfluxDB/TimescaleDB) + a graph DB (Neo4j/GraphDB).
   Realistic for industry, but adds installation and Docker to every experiment, and is far
   more than the data size needs.
2. **Everything in memory, files for persistence**: pandas for history, rdflib in-memory graph
   saved as Turtle, events as JSON lines.
3. **In memory + embedded databases**: same as 2, but SQLite (Python standard library) for
   events and optional history persistence.

## Decision

Option 3, behind small interfaces so servers can be added later without changing callers.

- **State and history:** in memory inside `DigitalTwin` (list of snapshots, materialised as a
  pandas DataFrame on demand). Optional bounded history (`max_history`) for long streams.
- **Knowledge graph:** rdflib in-memory `Graph`, persisted as Turtle. SPARQL works unchanged
  if we later swap to a triple store.
- **Episodic memory:** SQLite file (no extra dependency), introduced with the memory module
  in week 8.
- **Experiment outputs:** plain files (CSV/JSON/PDF) under `experiments/results/`, as now.

## Consequences

- No services to install; `pip install` is enough to reproduce every result.
- Single-process only. Fine for a research prototype and the paper's experiments; the
  Discussion section will name scaling to real fleets (servers, streaming) as future work.
- The `KnowledgeGraph` and memory interfaces must not leak rdflib/SQLite specifics, so a
  Neo4j or TimescaleDB backend remains possible.
