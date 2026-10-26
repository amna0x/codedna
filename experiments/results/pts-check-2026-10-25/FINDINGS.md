# B10 against a Predictive Test Selection baseline (B11), exploratory

Protocol: `docs/PTS_BASELINE_PROTOCOL.md`, committed (1a7a287) before this
run. Command:
`OMP_NUM_THREADS=1 python scripts/run_pts_check.py <data> --out experiments/results/pts-check-2026-10-25`.
Inputs are the four `dataset.csv` files of the rolling-origin study (same
SHA-256 values, `config.json`). Every number below is copied from
`summary.json` or the per-project JSON.

**Reproducibility check.** B10's per-block outcomes are identical to those
stored in `rolling-evidence-2026-10-24/` for all 20 blocks.

**Fit and tuning failures.** jade4j's first block could not be fitted (no
failing calibration rows), as in the rolling study, so it is left out of both
policies. B11 could be tuned in every other block.

## Question 1: same test time

| Project | B10 time | B10 safety | B11 matched time | B11 matched safety | Residual time (B10 − B11) |
|---|---|---|---|---|---|
| HikariCP | 0.339 | 0.827 | 0.757 | 0.704 | −0.418 |
| jade4j | 0.915 | 1.000 | 0.911 | 0.875 | +0.004 |
| LittleProxy | 0.913 | 0.711 | 0.913 | 0.947 | 0.000 |
| wicket-bootstrap | 0.941 | 0.992 | 0.912 | 0.976 | +0.029 |

Pooled B10 minus matched B11, equal project weight, 2000 hierarchical draws:
safety +0.007 [−0.063, 0.091], recall +0.025 [−0.023, 0.101], time −0.096
[−0.111, −0.081]. Rule outcome: **inconclusive**: the interval crosses both
0 and the ±0.05 margin.

**Matching failed on HikariCP.** B11's count cutoff, tuned to 0.999 change
recall, already selects 10 to 20 tests per commit, so no test-recall target
brings B11 below 0.757 of the suite's time. B10 used 0.339. On HikariCP, B10
is both cheaper and safer; the pooled time difference comes from this
project. On LittleProxy, B11 is clearly safer at the same time (0.947 against
0.711). jade4j has only 8 failing commits in the compared blocks.

## Question 2: does each method keep the target it states?

| Project | B11 test recall (target 0.95) | B11 change recall (target 0.999) | B11 time | B10 commit miss rate (target 0.05) |
|---|---|---|---|---|
| HikariCP | 0.949 | 0.951 | 0.973 | 0.020 |
| jade4j | 0.875 | 0.875 | 0.706 | 0.000 |
| LittleProxy | 0.985 | 0.947 | 0.916 | 0.084 |
| wicket-bootstrap | 0.951 | 0.996 | 0.833 | 0.005 |

B11 keeps its test-recall target on 2 of 4 projects (HikariCP misses by
0.001) and its change-recall target on none. B10 keeps its miss target on 3
of 4 (LittleProxy breaks it). Pooled over commits (dominated by
wicket-bootstrap): B11 at its paper targets spends 0.902 of the time for
recall 0.952 and safety 0.920; B10 spends 0.625 for recall 0.995 and safety
0.928.

## Question 3: does CodeDNA's risk estimate warn about B11's misses?

| Project | B11 commits missing a failure | Mean estimated skip risk of B11's selection | AUC of the estimate for a miss |
|---|---|---|---|
| HikariCP | 0.013 | 0.003 | 0.82 |
| jade4j | 0.008 | 0.163 | 0.56 |
| LittleProxy | 0.015 | 0.105 | 0.64 |
| wicket-bootstrap | 0.044 | 0.175 | 0.90 |

The estimate ranks B11's risky commits above its safe ones on all four
projects, strongly on HikariCP and wicket-bootstrap. Its level is wrong for
these selections: it is far too high on three projects and too low on
HikariCP. The calibrated probabilities are therefore informative as a
ranking of commit risk but not a trustworthy risk level outside the
operating point B10 was checked at.

## Plain reading

- The PTS-style baseline does not beat B10, and B10 does not beat it. The
  result depends on the project: B10 is much cheaper and safer on HikariCP,
  B11 is much safer on LittleProxy.
- Aggregate recall targets tuned on a short holdout did not hold out of
  sample on these small histories; change recall 0.999 was never reached.
  B10's per-commit target held more often (3 of 4), but not always.
- The measured difference is in **what is promised and how often it holds**,
  not in failures caught at equal time.

## Limits

Four previously inspected projects, exploratory only. One deterministic fit
per block. The commit bootstrap ignores serial dependence. B11 follows the
published method but omits Facebook's deployment check and uses CodeDNA's 15
live features, not Facebook's. Matching could not reach B10's time on
HikariCP.
