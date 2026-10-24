# mindtwin roadmap (15 weeks)

**Start:** Sat 24 Oct 2026 · **Target v1.0:** Fri 5 Feb 2027
**Rhythm:** work every day, at least 3 meaningful commits per day (feature, test, docs).

Legend: ☐ todo · ☑ done

---

## Phase 0: Research and foundations (weeks 1–2)

### Week 1 · 24 Oct – 30 Oct: kick-off
- ☑ Create repo, license, README
- ☑ Roadmap and literature review v1
- ☑ Package scaffold, tests, CI
- ☐ Architecture document v1 (layers, interfaces, data flow)
- ☐ C-MAPSS download script + data card
- ☐ Exploratory data analysis notebook (sensors, degradation trends)
- ☐ Glossary of CDT terms

### Week 2 · 31 Oct – 6 Nov: design
- ☐ Read and summarise 10 core papers (see literature review)
- ☐ Turbofan ontology draft (components, sensors, failure modes)
- ☐ Decide storage: time-series store + graph store
- ☐ Config system (pydantic settings), logging
- ☐ Pre-commit hooks, coverage in CI

## Phase 1: Twin core (weeks 3–5)

### Week 3 · 7 Nov – 13 Nov: asset model
- ☐ `Asset`, `Component`, `Sensor` data models
- ☐ `DigitalTwin` class with state snapshot + history
- ☐ Unit tests for state updates

### Week 4 · 14 Nov – 20 Nov: data ingestion
- ☐ C-MAPSS dataset loader (FD001–FD004)
- ☐ Stream simulator (replay engine data in real time)
- ☐ Ingestion pipeline: stream → twin state
- ☐ Feature engineering (rolling stats, normalisation per operating condition)

### Week 5 · 21 Nov – 27 Nov: knowledge graph
- ☐ Ontology in code (RDF / OWL with rdflib)
- ☐ Build knowledge graph per engine instance
- ☐ Link live sensor state to graph nodes
- ☐ Graph queries (SPARQL helpers)

## Phase 2: Cognition (weeks 6–9)

### Week 6 · 28 Nov – 4 Dec: perception
- ☐ Health indicator construction
- ☐ Anomaly detection baselines (z-score, isolation forest)
- ☐ Evaluation harness + metrics

### Week 7 · 5 Dec – 11 Dec: prediction
- ☐ RUL baselines (linear, random forest, gradient boosting)
- ☐ Deep RUL model (LSTM / 1D-CNN)
- ☐ Standard C-MAPSS scoring (RMSE + PHM08 score)

### Week 8 · 12 Dec – 18 Dec: memory and uncertainty
- ☐ Episodic memory: store events, anomalies, decisions
- ☐ Semantic memory: facts learned back into the knowledge graph
- ☐ Uncertainty in RUL (MC dropout or conformal prediction)

### Week 9 · 19 Dec – 25 Dec: reasoning
- ☐ Root-cause reasoning over knowledge graph
- ☐ Rule engine for maintenance policies
- ☐ What-if simulation (forecast under scenarios)

## Phase 3: Agent (weeks 10–12)

### Week 10 · 26 Dec – 1 Jan: agent foundations
- ☐ Pluggable LLM client interface
- ☐ Tools: query twin state, query graph, predict RUL, search memory
- ☐ Agent loop with tool calling

### Week 11 · 2 Jan – 8 Jan: knowledge-grounded answers
- ☐ RAG over maintenance docs + knowledge graph (GraphRAG)
- ☐ Explanations: "why is engine 42 degrading?"
- ☐ Guardrails: answers must cite twin data

### Week 12 · 9 Jan – 15 Jan: autonomy
- ☐ Maintenance planning (schedule optimisation)
- ☐ Closed-loop: perceive → reason → recommend → log decision
- ☐ Agent evaluation set (questions with expected answers)

## Phase 4: Interface and release (weeks 13–15)

### Week 13 · 16 Jan – 22 Jan: API
- ☐ FastAPI service (twins, state, predictions, agent chat)
- ☐ Docker image + docker-compose

### Week 14 · 23 Jan – 29 Jan: dashboard
- ☐ Web dashboard (fleet view, engine detail, graph view, chat)
- ☐ End-to-end demo scenario

### Week 15 · 30 Jan – 5 Feb: release
- ☐ Benchmarks and results write-up
- ☐ Documentation site
- ☐ v1.0.0 release + demo video
- ☐ Technical report / paper draft (arXiv)

---

## Milestones

| Milestone | Week | Deliverable |
|---|---|---|
| M0 Foundations | 2 | Scaffold, CI, data, design docs |
| M1 Twin core | 5 | Live twin of a turbofan with knowledge graph |
| M2 Cognition | 9 | Anomalies, RUL with uncertainty, memory, root cause |
| M3 Agent | 12 | LLM agent that reasons with the twin |
| M4 v1.0 | 15 | API, dashboard, benchmarks, release |
