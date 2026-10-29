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
