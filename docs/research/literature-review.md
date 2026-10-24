# Literature review (v1)

Working notes on Cognitive Digital Twins (CDTs) for industrial systems. Updated as reading progresses.

## 1. What is a Cognitive Digital Twin?

A digital twin (DT) is a virtual representation of a physical asset, kept in sync with it through
data. A **cognitive** digital twin adds capabilities usually associated with cognition:

- **Perception**: turning raw sensor data into meaningful states and events
- **Memory**: keeping history and learned knowledge across the asset lifecycle
- **Reasoning**: explaining causes, using domain knowledge (ontologies, knowledge graphs)
- **Prediction**: forecasting future states, e.g. remaining useful life
- **Decision support / autonomy**: recommending or taking actions, learning from outcomes

Zheng, Lu and Kiritsis (2022) describe the CDT as a DT augmented with semantic capabilities,
built around knowledge graphs, and propose a reference architecture based on RAMI 4.0.

A 2026 view (Akyildiz and Bilen) separates a true cognitive twin, a closed loop that integrates
perception, memory, reasoning and communication, from "an LLM with external memory".
mindtwin follows the closed-loop view.

## 2. Key themes

| Theme | Why it matters for mindtwin |
|---|---|
| Ontologies / knowledge graphs | The semantic backbone: components, sensors, failure modes, causal links |
| Prognostics (RUL) | The main "prediction" capability on turbofan data |
| LLM agents in DTs | Newest direction (2025–26); natural-language interface and tool-based reasoning |
| Uncertainty quantification | Maintenance decisions need confidence, not point estimates |
| Lifecycle / memory | CDTs should accumulate knowledge over time |

## 3. Gap

Most CDT work is conceptual (architectures, visions) or closed industrial platforms. There is
little **open-source, end-to-end, reproducible** implementation that connects a live twin, a
knowledge graph, prognostic models and an LLM agent, evaluated on a public benchmark.
**mindtwin aims to fill that gap.**

## 4. Reading list

Core
- [ ] Zheng, Lu, Kiritsis (2022). *The emergence of cognitive digital twin: vision, challenges and opportunities.* Int. J. Production Research.
- [ ] Karabulut et al. (2024). *Ontologies in Digital Twins: A Systematic Literature Review.* Future Generation Computer Systems. arXiv:2308.15168
- [ ] *Digital Twin AI: Opportunities and Challenges from Large Language Models to World Models* (2026). arXiv:2601.01321
- [ ] *A Cognitive Digital Twin for Industry 5.0 based on a Large Language Model* (2025, IEEE)
- [ ] Akyildiz, Bilen (2026). Cognitive twin definitions, ITU Journal.
- [ ] Apanovich (2025). *Modern industrial applications of knowledge graphs.* System Informatics.

Prognostics / data
- [ ] Saxena et al. (2008). *Damage propagation modeling for aircraft engine run-to-failure simulation* (C-MAPSS origin)
- [ ] Ramasso, Saxena (2014). *Performance benchmarking and analysis of prognostic methods for C-MAPSS datasets.* (warns about inconsistent evaluation protocols)

To find
- [ ] GraphRAG for industrial knowledge
- [ ] Conformal prediction for RUL
- [ ] Agentic predictive maintenance benchmarks

## 5. Datasets

| Dataset | Use | Notes |
|---|---|---|
| NASA C-MAPSS (FD001–FD004) | Primary: RUL + degradation | 70+ papers use it; evaluation protocols differ, so we document ours exactly |
| NASA N-CMAPSS | Later: more realistic flights | Larger |
| Tennessee Eastman Process | Possible second use case: process fault detection | To verify availability |

## 6. Sources

- https://research.buaa.edu.cn/en/publications/the-emergence-of-cognitive-digital-twin-vision-challenges-and-opp/
- https://arxiv.org/abs/2308.15168
- https://arxiv.org/pdf/2601.01321
- https://researchwith.njit.edu/en/publications/a-cognitive-digital-twin-for-industry-50-based-on-a-large-languag/
- https://www.itu.int/dms_pub/itu-s/opb/jnl/S-JNL-VOL7.ISSUE2-2026-A14-PDF-E.pdf
- https://system-informatics.iis.nsk.su/en/article/418
- https://ntrs.nasa.gov/api/citations/20150007677/downloads/20150007677.pdf
