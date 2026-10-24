# mindtwin

**An open-source framework for industrial Cognitive Digital Twins (CDTs).**

A classic digital twin mirrors the *state* of a physical asset. A **cognitive** digital twin also
*understands* it: it keeps a knowledge graph of the asset, remembers what happened, reasons about
causes, predicts what comes next, and recommends what to do.

mindtwin combines four layers in one Python package:

| Layer | What it does |
|---|---|
| **Twin core** | Asset model, live state, sensor ingestion and replay |
| **Knowledge** | Ontology + knowledge graph of components, sensors, failure modes |
| **Cognition** | Anomaly detection, remaining-useful-life (RUL) prediction, episodic memory, root-cause reasoning |
| **Agent** | LLM agent that uses the twin as tools: explains, answers questions, plans maintenance, runs what-if scenarios |

The first reference use case is the **NASA C-MAPSS turbofan engine** dataset.

## Status

Early development. See the [roadmap](docs/ROADMAP.md) for the 15-week plan and
[research notes](docs/research/literature-review.md) for background.

## Architecture

```
 Physical asset / simulator
          │  sensor streams
          ▼
 ┌──────────────────────┐
 │      Twin core       │  asset model · state store · ingestion
 └─────────┬────────────┘
           ▼
 ┌──────────────────────┐     ┌──────────────────────┐
 │      Cognition       │◄───►│   Knowledge graph    │
 │ perceive · remember  │     │ ontology · failure   │
 │ reason · predict     │     │ modes · causal links │
 └─────────┬────────────┘     └──────────────────────┘
           ▼
 ┌──────────────────────┐
 │        Agent         │  explain · plan · what-if
 └─────────┬────────────┘
           ▼
     API · Dashboard
```

More detail in [docs/architecture.md](docs/architecture.md).

## Getting started

```bash
git clone https://github.com/kitsakisGk/mindtwin.git
cd mindtwin
python -m venv .venv
.venv/Scripts/activate      # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev]"
pytest
```

## Project layout

```
src/mindtwin/
  core/        asset model, twin state
  data/        datasets and stream ingestion
  knowledge/   ontology and knowledge graph
  cognition/   perception, memory, reasoning, prediction
  agent/       LLM agent and tools
  api/         REST API
docs/          roadmap, architecture, research notes, devlog
tests/
```

## License

MIT, see [LICENSE](LICENSE).
