# HikariCP — first real evaluation (2026-10-21)

First run of CodeDNA's Milestone 4/5 evaluation on real CI data. **One
project only**: treat every number here as preliminary, not as a finding.

## Data

- RTPTorrent v1.1 (Zenodo 4046180, CC BY 4.0; Mattis, Rein, Dürsch,
  Hirschfeld, *RTPTorrent: An Open-source Dataset for Evaluating Regression
  Test Prioritization*, MSR 2020, doi:10.1145/3379597.3387458),
  `rtp-torrent-v11.zip`, md5 `1f7fa822b0cf155bd007a94d1a24a336`.
- Project `brettwooldridge@HikariCP`. Import (see `run.log` of the import in
  docs/DATASET_PLAN.md): 1,662 jobs, 1,577 imported, 1,427 tested commits,
  123 with at least one failing test class, 23 test classes.
- History database `experiments/datasets/derived/hikaricp.db`
  (git-ignored), sha256
  `8b6d1c56bdabb89d5bc8a79598288ac283d344c0d54cc8aa56cdf0806fc9c638`.

## Environment

- CodeDNA commit `29f6da24138f765d2f99a7d39fed4cb876b1f489` plus the
  tree-sitter pin (`<0.26`, D-033) made during this run.
- Python 3.12.0, scikit-learn 1.9.1, numpy 2.5.4, tree-sitter 0.25.2,
  tree-sitter-java 0.23.5, Windows 11, 12 logical CPUs.

## Commands (run from the repository root)

```bash
codedna history import-rtptorrent --dataset experiments/datasets/raw/rtp-torrent --project brettwooldridge@HikariCP --db experiments/datasets/derived/hikaricp.db
codedna history evaluate --db experiments/datasets/derived/hikaricp.db --seed 0 --dataset-csv experiments/results/hikaricp-2026-10-21/dataset.csv --output experiments/results/hikaricp-2026-10-21/evaluate.json
codedna history experiment --db experiments/datasets/derived/hikaricp.db --model gradient_boosting --calibration isotonic --budget 0.5 --risk-target 0.05 --seed 0 --output experiments/results/hikaricp-2026-10-21/experiment.json
```

## Files

| File | Content |
|------|---------|
| `evaluate.json` | Orderings (random, shortest-first, recent failures, failure history, logistic regression, gradient boosting) on validation/test splits |
| `experiment.json` | Calibration, policies B0/B4/B6–B9, risk–coverage sweeps, ablations, reproducibility block |
| `dataset.csv` | The (commit, test class) feature rows used (derived from RTPTorrent, CC BY 4.0) |
| `run.log` | Console output and timings |

## Results (test split: 286 commits, 20 with failures; seed 0)

All numbers are from `evaluate.json` / `experiment.json`. One project, one
seed, 20 failing commits: differences of a few points are within noise.

Failure base rate (share of failing rows): train 1.5 %, validation 0.8 %,
test 2.0 %. Failing test commits break ~6 test classes on average versus ~1.6
before, and the suite grew from ~10 to ~21 classes per run — a distribution
shift between training and test.

**Ordering (`evaluate.json`, test split).** Time-aware metrics favour simple
rules: "recently failed first" APFDc 0.75 and "shortest first" 0.73 versus
logistic regression 0.52 and gradient boosting 0.53. Logistic regression has
the best plain APFD (0.67). PR-AUC: logistic regression 0.057, gradient
boosting 0.039 (base rate 0.020).

**Calibration (RQ3).** Gradient boosting raw: Brier 0.0204, ECE 0.0201 —
close to always predicting ≈0. Isotonic/Platt: Brier ≈0.020, ECE 0.0137
(ECE −32 %, Brier essentially unchanged). Estimated skip risk vs observed miss
rate per commit: uncalibrated 0.001 vs 0.035 (≈35× too optimistic),
calibrated 0.015 vs 0.032 (≈2× too optimistic).

**Selection policies (RQ2/RQ4), time budget 50 %:**

| Policy | Time | Failing-test recall | Missed | Commit safety | Fallback |
|---|---|---|---|---|---|
| B0 retest all | 1.00 | 1.00 | 0 | 1.00 | – |
| B4 dependency only | 0.49 | 0.66 | 41 | 0.65 | – |
| B6 change-only ML | 0.35 | 0.81 | 23 | 0.55 | – |
| B7 ML uncalibrated | 0.39 | 0.81 | 23 | 0.50 | – |
| B8 ML calibrated | 0.36 | 0.81 | 23 | 0.55 | – |
| B9 calibrated + fallback | 0.64 | 0.88 | 15 | 0.70 | 44 % |

B9's fallback fired on 44 % of test commits, almost all because a non-Java
file changed (43 % of test commits; 8 of the 20 failing commits). Its gain
therefore comes mainly from the *non-Java → retest-all* rule, not from the
calibrated risk estimate; the risk-target sweep is flat above 0.02.
Against B8 at a similar time cost (budget 0.8: time 0.76, recall 0.93,
safety 0.60), B9 has higher commit safety (0.70) but lower recall.

**Ablations (RQ1/RQ5).** PR-AUC drops most without history features
(0.039 → 0.021) and without structural features (→ 0.026); removing change
features does not hurt (0.040). Selection metrics at the budget barely move.

## Reading

- Pipeline works end to end on real CI data; no research claim yet.
- ML ordering does not beat simple time-aware rules here.
- Calibration makes the *risk estimate* much less over-optimistic, but it is
  still ≈2× too low (independence assumption, shift).
- Fallback improves safety mainly via the non-Java rule; a version without
  that rule is needed to test the calibrated-risk fallback itself.
- Needed before conclusions: more projects, several seeds, and an
  ablation of the fallback triggers.
