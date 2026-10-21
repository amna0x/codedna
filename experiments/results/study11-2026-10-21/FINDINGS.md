# Study findings — 11 RTPTorrent projects × 5 seeds (2026-10-21/22)

Generated numbers: `summary.md` / `summary.json`; per-seed reports in each
project folder. Protocol: docs/DECISIONS.md D-034, D-035. Data: RTPTorrent
v1.1 (Mattis et al., MSR 2020, CC BY 4.0). Every number below comes from those
files.

## Command

```bash
python scripts/run_study.py --out experiments/results/study11-2026-10-21 --seeds 0 1 2 3 4 --workers 6 \
  graylog2-server=experiments/datasets/derived/graylog2-server.db jooq=experiments/datasets/derived/jooq.db \
  jcabi-github=experiments/datasets/derived/jcabi-github.db optiq=experiments/datasets/derived/optiq.db \
  achilles=experiments/datasets/derived/achilles.db hikaricp=experiments/datasets/derived/hikaricp.db \
  littleproxy=experiments/datasets/derived/littleproxy.db jade4j=experiments/datasets/derived/jade4j.db \
  jsprit=experiments/datasets/derived/jsprit.db wicket-bootstrap=experiments/datasets/derived/wicket-bootstrap.db \
  dynjs=experiments/datasets/derived/dynjs.db
```

Code: commit `de24a4e` plus the cost-matching / bootstrap / parse-cache
changes committed with these results. The six projects of the previous study
reused their identical `dataset.csv`. Feature builds took 2 h 8 min each for
graylog2-server and jOOQ, 16–34 min for the others. The session ended after
`summary.md` was written but before the final timing line; all 110 reports
are complete. `summary.*` were then regenerated with the hierarchical
bootstrap (no experiment was re-run).

## Data quality — read this first

| Project | Test commits | With failures | Note |
|---|---|---|---|
| graylog2-server | 879 | **0** | CI logs record ~1 test class per commit for ~30 % of history, then 100–170 classes with no failures; last failing commit 2015-11 |
| jOOQ | 258 | **0** | recorded test classes per commit drop from ~34 to ~7 in the last 30 % (CI change); last failing commit 2016-01 |
| jcabi-github | 118 | 52 | |
| optiq | 91 | 4 | |
| Achilles | 101 | 1 | no failures in validation → calibrator not fitted |
| HikariCP | 286 | 20 | |
| LittleProxy | 53 | 5 | |
| jade4j | 63 | 2 | |
| jsprit | 52 | 7 | no failures in validation → calibrator not fitted |
| wicket-bootstrap | 164 | 87 | ~30 % failing rows; a persistently failing, expensive test |
| dynjs | 75 | 1 | |

graylog2-server and jOOQ contribute nothing to recall/safety (undefined
without failures); pooled comparisons therefore use **n = 9** projects.
Their recording gaps are properties of the RTPTorrent logs, not of
CodeDNA's import (stored and derived failure counts agree).

## RQ3 — Calibration: **robust improvement**

- ECE on the 9 projects where a calibrator could be fitted: uncalibrated
  0.118 → isotonic 0.021 (Platt 0.022). Better on 8 of 9, equal on jade4j.
  Without the two extreme projects (graylog2-server 0.23, dynjs 0.45 raw):
  0.055 → 0.023 (≈ −58 %).
- Brier (pooled): 0.075 uncalibrated (11 projects) vs 0.021–0.022 calibrated
  (9 projects).
- Commit-level skip-risk estimate, |estimated − observed miss rate|: 0.274
  (B7, uncalibrated) → 0.078 (B8, calibrated); better on 7 of 11 projects,
  worse on LittleProxy (0.22 → 0.27), unchanged where no calibrator could be
  fitted.

## RQ4 — Fallback versus the same test time: **no reliable general gain**

Each fallback policy is compared with B8 given the budget that spends the
same real test time; differences are policy − B8; 95 % intervals from a
hierarchical bootstrap (seed, then test commits); pooled = projects weighted
equally.

| Comparison | Pooled safety Δ [95 % CI] | Pooled recall Δ [95 % CI] | Where it differs |
|---|---|---|---|
| B9r (risk fallback) − B8 | +0.074 [0.000, 0.149] | +0.003 [−0.005, 0.013] | only wicket-bootstrap (+0.66 [0.00, 0.98]); exactly 0 on the other 8 |
| B9n (unfamiliar-change rule) − B8 | −0.006 [−0.109, 0.109] | −0.018 [−0.114, 0.092] | helps jcabi-github (+0.15 [0.02, 0.27]) and HikariCP (+0.15 [0.00, 0.32]); hurts wicket-bootstrap (−0.30 [−0.41, −0.18]) |
| B9 (both) − B8 | +0.048 [−0.032, 0.146] | +0.009 [−0.067, 0.096] | jcabi-github +0.15 [0.02, 0.28] |

- The calibrated risk estimate rarely triggers fallback on low-failure
  projects, so B9r usually *equals* B8 — neither helps nor hurts.
- On wicket-bootstrap, a persistently failing expensive test makes B8's
  safety jump from ~0.06 to ~0.99 only past ≈ 80 % test time. B9r spends its
  extra time on the risky commits and reaches ~0.97 safety at 0.64–0.72 time
  in 4 of 5 seeds; in seed 0 it ran past the cliff and matched B8. Hence the
  wide interval.
- The simple non-Java rule is not reliably better than spending the same
  time on the budget either; its effect changes sign between projects.

At default settings (not cost-matched) fallback looks much better (pooled
safety: B8 0.68, B9r 0.84, B9n 0.85, B9 0.93), but it also spends more time
(0.50 → 0.61 / 0.77 / 0.82). The cost-matched comparison shows most of that
gain is bought with test time, not with better decisions.

## RQ1/RQ2 — Ordering: **ML does not beat simple rules**

Pooled APFDc: recent-failures 0.76, shortest-first 0.74, random 0.65,
logistic regression 0.64, gradient boosting 0.58, failure-history 0.48.
Recall at 50 % of test time: recent-failures 0.71, shortest-first 0.70,
random 0.63, logistic regression 0.62, gradient boosting 0.53. Both ML
models are at or below random on average.

## Honest summary

1. **Calibration works** and is the most solid result: probability
   calibration error drops by roughly 60–80 % across projects, and the
   commit-level risk estimate becomes several times closer to reality.
2. **Risk-based fallback does not reliably beat spending the same time**
   on the budget. It is neutral on most projects and large on one
   (wicket-bootstrap) where failures are frequent and concentrated in an
   expensive test; the pooled interval just touches 0.
3. **ML ordering is not better than simple time-aware rules** (or random).
4. Two of eleven projects carry no evaluable failures; several others very
   few. The evidence is about *these* projects and periods (2012–2016).

## What this means for the claim

A defensible thesis claim is about **reliable risk estimates** (RQ3) and a
careful, cost-matched evaluation showing **when** fallback helps (frequent,
concentrated failures) and when it does not — not that CodeDNA's ML selects
tests better than simple rules. Overturning that would need projects where
learned models clearly beat recent-failures ordering, which this data does
not show.
