# Devlog

## 2026-10-24 · Day 1
- Project kick-off: industrial Cognitive Digital Twin framework, first use case NASA C-MAPSS.
- Repo, license, README.
- Roadmap (15 weeks) and literature review v1.
- Python package scaffold, tests and CI.
- Turned the project into a research project: research plan (RQ1–RQ4, experiments E1–E5,
  TwinQA benchmark), LaTeX paper skeleton with automatic PDF build, roadmap updated with paper work.
- Architecture document v1.

## 2026-10-25 · Day 2
- C-MAPSS downloader (checksum verified) and loader with RUL labels; PHM08 score and RMSE.
- Found an erratum in the official readme: FD004 has 249 train / 248 test engines (swapped).
- Operating-condition detection and per-condition normalisation. In FD002 the strongest
  sensor–RUL rank correlation goes from 0.25 (raw) to 0.71 (normalised).
- Exploratory analysis with four paper figures. Key finding: the fan fault in FD003 removes the
  RUL correlation of s7, s12, s15, s20, s21, so faults have distinct sensor signatures. This is
  the motivation for knowledge-graph reasoning (RQ3).
- Data card, frozen evaluation protocol, glossary; paper dataset subsection.

## 2026-10-29 · Day 3
- Core + turbofan ontologies (SOSA-aligned): 10 components, gas path, shafts, 21 sensor
  locations, 2 fault modes. Fault symptoms are deliberately left to be learned from data.
  The sensors that lose RUL correlation under the fan fault sit downstream of the fan.
- Reading notes on 11 papers and a full Related Work draft. Found close 2025–26 work
  (Lou et al. 2025; Gill et al. 2025; AgenticTwin 2026; Ma et al. 2026) and narrowed the novelty
  claim: the combination of KG with learned signatures + uncertainty-aware prognostics +
  tool-using agent, evaluated quantitatively on a public benchmark (TwinQA).
- Settings (TOML + env) and logging; pre-commit config; coverage gate (85%, currently 99%);
  format check in CI; LF line endings.
- Updated git 2.30 → 2.56 (pre-commit 4.x needs git >= 2.31) and enabled the pre-commit hooks.
- EDA outputs are now byte-reproducible (LF line endings, no PDF timestamps).

## 2026-10-31 · Day 4
- ADR 0001: in-memory state/history, rdflib graph as Turtle, SQLite for episodic memory later;
  no external services so every result is reproducible from `pip install`.
- `Asset` / `Component` / `Sensor` models built from the ontology (single source of truth),
  with structure queries (downstream components, coupling, sensors per component).
- `DigitalTwin`: validated updates (asset id, increasing cycles, known sensors, no inf),
  current state, history as DataFrame, bounded history, subscribers isolated from failures.
- Replay of real C-MAPSS engines into twins. Caching the parsed ontology made replay 3x faster:
  all 249 FD004 training engines (61,249 cycles) in 2.9 s, ~21k snapshots/s.
- CI now downloads C-MAPSS (checksum verified, cached) and runs integration tests on real data.
- Paper: Implementation section for the knowledge layer and twin core.

## 2026-11-05 · Day 5
- Trailing-window features per sensor: mean, std and slope over the last N cycles, never
  looking ahead (tested: adding future cycles does not change past features).
- First version looped over windows: 13 s on FD004. Rewritten with running sums: 0.6 s
  (about 20x faster), checked against the slow version kept in the tests as a reference.
- A 10-cycle mean of s11 tracks capped RUL better than the best single normalised reading
  on FD004 (|rank corr| 0.74 vs 0.71).
- `latest_features(twin)`: the twin computes the same features live from its own history;
  tested equal to offline features on a real FD002 engine with per-condition normalisation.
