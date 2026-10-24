# Evaluation protocol (frozen before experiments)

Written on 2026-10-25, **before any model is trained**. Changes after this date must be listed in
the changelog at the end with a reason, and reported in the paper. This prevents tuning the
protocol to the results, and addresses the inconsistent C-MAPSS evaluation practices reported by
Ramasso & Saxena (2014).

## 1. Data and splits

- Subsets: FD001, FD002, FD003, FD004, each evaluated separately. Results are reported for all
  four; no subset is dropped.
- **Test set:** the official test files. Each test engine is scored once, at its last observed
  cycle, against `RUL_FDxxx.txt`. The test set is never used for training, tuning, feature
  selection or normalisation.
- **Validation:** 20% of training **engines** (not rows) held out, chosen with seed 42. All
  hyperparameter tuning uses this split. Final models are retrained on all training engines
  with the chosen hyperparameters.
- **Seeds:** every stochastic experiment is run with 5 seeds (0–4); we report mean ± std.

## 2. Target

- Piecewise-linear RUL: `min(true_rul, 125)` for training.
- Evaluation against the **true** test RUL (which never exceeds 195 cycles).
- Sensitivity check with caps 115, 125, 130 and no cap, reported in an appendix.

## 3. Preprocessing

- Sensors: those returned by `informative_sensors(train)`; the list per subset is logged.
- Normalisation: `ConditionNormalizer` fitted on training data only (per operating condition;
  for FD001/FD003 this is plain z-scoring).
- Window length for sequence models: 30 cycles. Test engines with fewer cycles are left-padded
  with their first observation.

## 4. Metrics

| Task | Metrics |
|---|---|
| RUL prediction | RMSE (primary), PHM08 score (`mindtwin.evaluation`), MAE |
| RUL uncertainty | Empirical coverage of 80% and 90% intervals, mean interval width |
| Anomaly / early warning | Detection delay (cycles before failure), false alarm rate on the first 50 cycles |
| Root cause (E4) | Top-1 / top-3 accuracy against the known fault mode where available |
| Agent (E3, TwinQA) | Exact/numeric-tolerance accuracy, faithfulness (claims supported by tool outputs), tool-call correctness, hallucination rate |
| Maintenance (E5) | Total cost, number of in-service failures, mean wasted life |

## 5. Baselines

- RUL: constant mean, linear regression, random forest, gradient boosting, then deep models.
- Agent: (a) LLM with raw recent sensor rows in the prompt, (b) text-only RAG over documentation,
  (c) mindtwin twin-grounded agent, plus ablations (no knowledge graph, no memory, no RUL tool).

## 6. LLM experiments

- Report model name and version, temperature (0 unless stated), max tokens, prompts (in repo).
- At least one open-weight model run locally, so results can be reproduced without paid APIs.
- TwinQA answers are generated from the twin's data by code, never by an LLM.

## 7. Reporting

- All tables and figures are produced by scripts in `experiments/`, with results saved as files.
- Every result file stores the git commit, config and seed used.
- Negative results are reported.

## Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-10-25 | Initial version | – |
