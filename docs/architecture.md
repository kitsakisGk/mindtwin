# Architecture (v1)

This document describes the mindtwin architecture. It is the basis for Section 3 of the paper.

## 1. Design principles

1. **Closed loop.** Perceive → remember → reason → predict → recommend → learn from the outcome.
2. **Knowledge first.** All components read from and write to a shared knowledge graph, so every
   answer can be traced back to data and domain knowledge.
3. **Swappable components.** Each capability sits behind a small interface (e.g. any RUL model,
   any LLM, any graph store), so experiments can compare alternatives and ablate parts.
4. **Grounded agent.** The LLM never answers from its own memory alone. It calls twin tools and
   must cite the data it used.
5. **Reproducible.** Deterministic replay of datasets, fixed seeds, configs saved with results.

## 2. Layers

```
┌───────────────────────────────────────────────────────────────────┐
│ 6. Interface      REST API · dashboard · chat                     │
├───────────────────────────────────────────────────────────────────┤
│ 5. Agent          LLM · tools · planner · guardrails              │
├───────────────────────────────────────────────────────────────────┤
│ 4. Cognition      perception · prediction · reasoning · memory    │
├──────────────────────────────┬────────────────────────────────────┤
│ 3. Twin core                 │ 2. Knowledge                       │
│    asset model · state ·     │    ontology · knowledge graph ·    │
│    history                   │    queries                         │
├──────────────────────────────┴────────────────────────────────────┤
│ 1. Data           dataset loaders · stream replay · features      │
└───────────────────────────────────────────────────────────────────┘
               ▲ sensor data              ▼ recommendations
        Physical asset or simulator (C-MAPSS replay)
```

| Layer | Package | Responsibility |
|---|---|---|
| 1. Data | `mindtwin.data` | Load C-MAPSS, replay it as a time-ordered stream, compute features |
| 2. Knowledge | `mindtwin.knowledge` | Ontology (asset, component, sensor, failure mode, event), graph per asset, queries |
| 3. Twin core | `mindtwin.core` | `Asset` / `Component` / `Sensor` models, `DigitalTwin` state and history |
| 4. Cognition | `mindtwin.cognition` | Health indicators, anomalies, RUL with uncertainty, root cause, episodic + semantic memory |
| 5. Agent | `mindtwin.agent` | LLM client interface, tools over layers 2–4, agent loop, citation guardrails |
| 6. Interface | `mindtwin.api` | FastAPI service; dashboard (week 14) |

## 3. Main data flow

1. **Ingest.** The stream replays one cycle at a time per engine: `(unit, cycle, settings, sensors)`.
2. **Update state.** `DigitalTwin.update()` stores the new snapshot and appends it to history.
3. **Perceive.** Health indicator and anomaly detectors run on the new state. Detected anomalies
   become `Event`s.
4. **Remember.** Events go to episodic memory and are linked in the knowledge graph
   (`event —observedOn→ sensor —partOf→ component`).
5. **Predict.** The RUL model returns a prediction interval, stored as the twin's current prognosis.
6. **Reason.** When an event or a low RUL appears, the reasoner walks the graph
   (sensor → component → failure mode) and ranks likely causes.
7. **Recommend.** Policies turn prognosis + causes into actions (inspect, schedule, replace).
8. **Explain / interact.** The agent answers questions by calling tools for steps 2–7 and cites
   the nodes, events and model outputs it used.
9. **Learn.** Decisions and outcomes are written back to memory and the graph.

## 4. Core interfaces (draft)

```python
class DigitalTwin:
    def update(self, snapshot: Snapshot) -> None: ...
    def state(self) -> Snapshot: ...
    def history(self, window: int | None = None) -> pd.DataFrame: ...

class RULModel(Protocol):
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: ...
    def predict(self, X: pd.DataFrame) -> Prognosis: ...   # point + interval

class KnowledgeGraph(Protocol):
    def add(self, triple: Triple) -> None: ...
    def query(self, sparql: str) -> list[dict]: ...
    def neighbours(self, node: str, relation: str | None = None) -> list[str]: ...

class Tool(Protocol):
    name: str
    description: str
    def __call__(self, **kwargs) -> ToolResult: ...         # result carries citations

class LLMClient(Protocol):
    def chat(self, messages: list[Message], tools: list[Tool]) -> Message: ...
```

## 5. Technology choices (initial)

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.10+ | ML ecosystem |
| Data | pandas, numpy | Standard |
| Knowledge graph | rdflib (RDF/OWL, SPARQL) | Standards-based, no server needed; Neo4j possible later |
| ML | scikit-learn, PyTorch | Baselines + deep RUL models |
| Uncertainty | Conformal prediction / MC dropout | Model-agnostic intervals |
| LLM | Provider-agnostic client; one open-weight model (e.g. via Ollama) + one API model | Reproducibility + strong baseline |
| API | FastAPI | Typed, async |
| Config | pydantic | Validation |

## 6. Mapping to CDT capabilities

| CDT capability (literature) | mindtwin component |
|---|---|
| Perception | `cognition.perception` |
| Memory | `cognition.memory` + knowledge graph |
| Reasoning | `cognition.reasoning` + agent |
| Prediction | `cognition.prediction` |
| Decision / autonomy | policies + agent planner |
| Semantic interoperability | `knowledge` ontology |
| Lifecycle learning | write-back of decisions and outcomes |

## 7. Open questions

- One graph per engine, or one fleet graph? (Start per engine, merge for fleet queries.)
- How much of the ontology to reuse from existing standards (e.g. SOSA/SSN for sensors)?
- Streaming speed for experiments: real time vs accelerated replay.
