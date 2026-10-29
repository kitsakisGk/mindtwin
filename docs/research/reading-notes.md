# Reading notes

One entry per paper: what it does, what we take from it, how mindtwin differs.
Status: ✅ abstract + metadata verified · 📖 full text read.

---

## Concepts and architectures

### Zheng, Lu, Kiritsis (2022). *The emergence of cognitive digital twin: vision, challenges and opportunities.* IJPR 60(24), 7610–7632. ✅
- Reviews CDT-related work, collects definitions and key features, and proposes a reference
  architecture based on RAMI 4.0. Discusses enabling technologies, scenarios and open challenges.
- **Take:** our working definition of a CDT and the capability list (perception, memory,
  reasoning, …) that the architecture maps to.
- **Differs:** conceptual; no implementation or quantitative evaluation.

### Abburu et al. (2020). *COGNITWIN – Hybrid and Cognitive Digital Twins for the Process Industry.* IEEE ICE/ITMC, 1–8. doi:10.1109/ICE/ITMC49519.2020.9198403 ✅
- Distinguishes digital, hybrid and cognitive twins; proposes an architecture for a CDT toolbox
  for process-industry operations and maintenance. Often cited for describing cognitive twins
  as self-learning and proactive, combining AI analytics with expert knowledge (the exact
  wording needs checking in the full text).
- **Take:** the digital → hybrid → cognitive progression for the paper's background section.
- **Differs:** process industry; architecture-level.

### Zhou et al. (2026). *Digital Twin AI: Opportunities and Challenges from Large Language Models to World Models.* arXiv:2601.01321 ✅
- Survey. Four-stage framework for AI across the DT lifecycle: model the physical twin, mirror it
  in real time, intervene (prediction, anomaly detection, optimisation), and manage it autonomously
  with LLMs, foundation models and agents. Reviews 11 domains. Challenges: scalability,
  explainability, trustworthiness.
- **Take:** mindtwin sits at stages 3–4; cite for the "LLMs make twins proactive" trend and
  for trust/explainability as open problems (our grounding + citation design targets this).

## Ontologies and knowledge graphs

### Karabulut, Pileggi, Groth, Degeler (2024). *Ontologies in Digital Twins: A Systematic Literature Review.* FGCS. arXiv:2308.15168, doi:10.1016/j.future.2023.12.013 ✅
- SLR of 82 articles using ontologies in DTs, analysed against a reference DT architecture and by
  application domain (manufacturing, infrastructure, …). Uses "cognitive twins" for DTs built
  on semantic web technology. Identifies open issues and research directions.
- **Take:** justification for an ontology-based knowledge layer and for reusing standards (SOSA).
- **Differs:** review; mindtwin evaluates whether the KG actually helps (RQ3).

### Shi, Li, Meyer, Bauernhansl (2025). *Enhancing retrieval-augmented generation for interoperable industrial knowledge representation and inference toward cognitive digital twins.* Computers in Industry 171, 104330. ✅ (authors from catalogue; confirm on DOI page)
- RAG with LLMs over industrial knowledge (asset administration shell, entity matching) as a
  step towards CDTs.
- **Take:** RAG over industrial knowledge is an active direction → our text-RAG baseline.
- **Differs:** knowledge representation/interoperability; no prognostics or live twin state.

## LLM agents and digital twins

### Lou, Tan, Zhou, Lv (2025). *A Cognitive Digital Twin for Industry 5.0 Based on a Large Language Model Agent.* IEEE ICHMS, 223–228. doi:10.1109/ICHMS65439.2025.11154278 ✅
- Five-dimensional CDT framework with an LLM agent at its core. RAG over tool libraries and
  industrial knowledge graphs turns human commands into function-call sequences; in-context
  learning for new tasks. Demonstrated on a lab-scale manufacturing unit (valid task plans,
  handling of dynamic incidents).
- **Take:** closest architectural precedent (LLM agent + KG + tools inside a CDT).
- **Differs:** demonstration, no public benchmark or quantitative comparison with baselines;
  no prognostics.

### Gill, Vyas, Markaj, Gehlhoff, Mercangöz (2025). *Leveraging LLM Agents and Digital Twins for Fault Handling in Process Plants.* arXiv:2505.02076 ✅
- LLM agents interpret plant state and take corrective control actions. The DT is both a
  knowledge repository for prompting and a simulator to verify actions before applying them.
  Mixing module case study: mitigates a pipe clogging with few reprompts.
- **Take:** "verify actions in the twin before acting" → our what-if tool and closed loop.
- **Differs:** control of a process plant; single case study.

### Hasan, Ghanta, Sarkar, Guin (2026). *AgenticTwin: An Agentic LLM Framework Integrated with Digital Twin for Anomaly Detection.* arXiv:2608.11679 ✅
- LLM explanations grounded in a DT-driven anomaly classifier; operators ask natural-language
  questions; benchmark-style pipeline generating controlled operator queries over synthetic
  anomalies injected into a weather sensor dataset; evaluates lightweight open-source LLMs.
- **Take:** closest to TwinQA in spirit; cite and compare.
- **Differs:** anomalies only, synthetic anomalies on weather data; no knowledge graph, no RUL,
  no causal/fault-mode questions. TwinQA uses a public PHM benchmark with ground truth computed
  from data, and covers state, trend, RUL, cause and action questions.

## Prognostics

### Saxena, Goebel, Simon, Eklund (2008). *Damage propagation modeling for aircraft engine run-to-failure simulation.* PHM08. ✅
- Origin of C-MAPSS and the PHM08 scoring function. Sensor list used in our ontology.

### Ramasso, Saxena (2014). *Performance benchmarking and analysis of prognostic methods for CMAPSS datasets.* IJPHM. ✅
- Over 70 publications use C-MAPSS; evaluation practices are inconsistent, so results are hard
  to compare. → our frozen evaluation protocol.

### Ma, Flanigan, Bergés (2026). *Grounding Time-Series Foundation Models in Digital Twin Topology for Predictive Maintenance.* arXiv:2609.40071 ✅
- Benchmarks five frozen time-series foundation models for RUL on C-MAPSS; multivariate models
  win under varying conditions. Uses asset topology from the DT's information models to
  constrain cross-attention between channels. Pretraining, adaptation and DT-derived
  representations are complementary; topology constraints help by a small margin; competitive
  with state of the art.
- **Take:** independent evidence that twin structure helps prognostics on C-MAPSS; strong
  related work for RQ3; possible RUL baseline.
- **Differs:** structure used inside a predictor; no explanation, root-cause reasoning, memory
  or agent. mindtwin uses structure for reasoning and explanation and learns fault signatures.

---

## Positioning (updated 2026-10-29)

Close work exists on each piece: CDT architectures (Zheng; Abburu), LLM agents in CDTs (Lou;
Gill), grounded LLM explanations with a query benchmark (AgenticTwin), and DT topology for RUL
(Ma). **No work we found combines** a live twin, an ontology-based KG with learned fault
signatures, uncertainty-aware prognostics and a tool-using LLM agent in one open system, **and**
evaluates the agent quantitatively against baselines on a public prognostics benchmark with
computed ground truth. That combination, and TwinQA, are mindtwin's claims. We avoid claiming
"first CDT with LLMs".

## To read next
- [ ] Full texts of Lou et al. 2025, AgenticTwin 2026, Ma et al. 2026 (📖)
- [ ] Toward Autonomous LLM-Based AI Agents for Predictive Maintenance (Applied Sciences 15(21) 11515, 2025): survey, confirm details
- [ ] Agentic AI-enabled semantic commissioning of a CDT (arXiv:2609.09503)
- [ ] Conformal prediction for RUL
- [ ] GraphRAG
