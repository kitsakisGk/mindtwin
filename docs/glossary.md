# Glossary

| Term | Meaning |
|---|---|
| **Digital twin (DT)** | A virtual representation of a physical asset, kept in sync with it through data. |
| **Cognitive digital twin (CDT)** | A digital twin with cognitive capabilities: perception, memory, reasoning, prediction and decision support, usually built on semantic knowledge. |
| **Asset** | The physical thing being twinned (here: one turbofan engine). |
| **Fleet** | A group of assets of the same type (here: all engines of a subset). |
| **Snapshot** | The twin's state at one moment (here: one operating cycle). |
| **Operating cycle** | One flight or run of the engine; the time unit of C-MAPSS. |
| **Operating condition** | A combination of altitude, Mach number and throttle (the three settings). FD002/FD004 have six. |
| **Ontology** | A formal vocabulary of concepts and relations in a domain (e.g. *Sensor observes Component*). |
| **Knowledge graph (KG)** | Facts stored as a graph of entities and relations, following an ontology. |
| **Triple** | One KG fact: subject, predicate, object (e.g. `s11 —observes→ HPC`). |
| **SPARQL** | Query language for RDF knowledge graphs. |
| **RDF / OWL** | W3C standards for representing graphs (RDF) and ontologies (OWL). |
| **Prognostics** | Predicting the future health of an asset. |
| **RUL** | Remaining useful life: cycles left before failure. |
| **Piecewise-linear RUL** | RUL target capped at a constant early in life, since degradation is not yet visible. |
| **Health indicator (HI)** | A single value summarising asset health, built from sensors. |
| **PHM08 score** | Asymmetric RUL error score that penalises late predictions more than early ones. |
| **HPC / LPC** | High / low pressure compressor. |
| **HPT / LPT** | High / low pressure turbine. |
| **Fault mode** | A specific way of failing (here: HPC degradation, fan degradation). |
| **Fault signature** | The pattern a fault leaves in the sensors. |
| **Root cause analysis** | Finding which component or fault mode explains observed symptoms. |
| **Episodic memory** | The twin's record of specific events (anomalies, decisions, outcomes). |
| **Semantic memory** | General knowledge the twin has learned, stored back into the KG. |
| **Conformal prediction** | A method that turns any model's predictions into intervals with guaranteed coverage. |
| **LLM agent** | A large language model that solves tasks by calling tools in a loop. |
| **Tool** | A function the agent can call (e.g. *predict RUL of engine 42*). |
| **Grounding** | Making an agent's answers depend on real data and cite it, instead of its own memory. |
| **RAG / GraphRAG** | Retrieval-augmented generation over documents / over a knowledge graph. |
| **Hallucination** | An agent statement not supported by the data. |
| **TwinQA** | mindtwin's benchmark: questions about twin state, trends, RUL, causes and actions, with ground-truth answers computed from data. |
| **RAMI 4.0** | Reference Architecture Model Industrie 4.0, used by several CDT architectures. |
