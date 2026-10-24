# Author-history-score adaptation / B10 findings — 2026-10-24

Twenty project/seed reports completed: four restored projects, five seeds each.
This is a separately fixed exploratory extension on previously inspected data.
The independent adapter uses DANTE’s history-score structure and CCH density,
but omits commit relevance, build-aligned method history and full published
selection. It is not a reproduction of DANTE or evidence of beating full DANTE.

## Main results

Calibrated stopping met the unconditional observed 5% miss target on all four
projects under both the adapted ordering and recent-failure rules. Raw stopping
failed that target on HikariCP (5.59% miss) and wicket-bootstrap (9.64% miss)
under the adapted ordering. Calibration remains relevant to the stopping decision.

| Project | Adapted-order calibrated time | Recall | Safety | Observed miss | Rules calibrated time |
|---|---|---|---|---|---|
| hikaricp | 0.2939 | 0.7190 | 0.5000 | 0.0350 | 0.1333 |
| littleproxy | 0.9834 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| jade4j | 0.2345 | 0.5000 | 0.5000 | 0.0159 | 0.2264 |
| wicket-bootstrap | 0.7760 | 0.9973 | 0.9908 | 0.0049 | 0.7513 |

At matched actual test time, adapted-order calibrated stopping minus the same-order budget baseline has pooled safety difference +0.0460, 95% hierarchical bootstrap interval [-0.05, 0.2806]. The interval crosses zero.
Pooled recall difference is {'estimate': -0.0056, 'ci': [-0.042, 0.0312]}. No general benefit is established.

HikariCP is a useful negative case: the adapted calibrated order uses 29.39% of
full test time versus rules’ 13.33%, while recall is 71.90% versus 72.73%.
This supports retaining simple recent-failure order as the live default.

## Interpretation and limits

- The stopping mechanism can be applied to another ordering, but this does not establish that it works on any ordering or outperforms established tools.
- There are only 20 / 5 / 2 / 87 failing target commits. jade4j meets 5% even if no tests run; its observed target attainment is weak evidence.
- The 50% baseline budget uses historical estimated durations. Actual runtime can differ substantially; cost-matched comparisons report residual differences.
- D1’s displayed risk is a calibrated-model diagnostic where calibration exists; it does not influence its fixed budget selection.
- Hierarchical intervals resample projects/seeds/commits, ignore serial dependence and have no multiple-comparison correction.
- Initial transition-proxy results are retained under `../dante-check-2026-10-24/`, including source snapshots. The closer adapter was fixed after retrieving author source; neither result is selected to claim a win.
- Fit/history/selection overhead is saved per run. Feature extraction, compilation and CI startup are excluded, so these results do not establish end-to-end CI speedup.
- The live 15-feature model/gate is a separate operational variant. This experiment does not validate its deployment performance or its abstention benefit.

## Reproduction

`python scripts/run_dante_check.py` uses the four restored CSVs. Config/protocol/code/input hashes protect resume. See `summary.md`, `summary.json`, `manifest.json` and `author-source-provenance.json`.

## Product implementation

Core/CLI/API and IDE now expose target-history risk validation, full-suite fallback and explicit selected Maven execution. No safety guarantee is made. See `docs/JAVA_WORKFLOW.md` and D-041. Software test/build validation is recorded separately from these research outcomes.


## Software verification

Final plugin-integrated suite: **245 passed, zero skipped**, including real Maven,
JUnit and JaCoCo, in 499.39 seconds. One existing Starlette/httpx deprecation
warning remains. `npm run build` passed the complete IDE build: native modules,
TypeScript, browser, Node backend and Electron main bundles.

Live desktop interaction on the project's disposable Java sample verified:
no target history produces risk-unvalidated/full-suite selection; explicit
execution consent precedes Maven; both recommended classes first pass. After a
deliberate discount regression, both fail and the IDE displays the real statuses,
commit SHAs, duration and log location. `validation.json` records actual reports
and source hashes. These are software/demo checks, not research accuracy results.
