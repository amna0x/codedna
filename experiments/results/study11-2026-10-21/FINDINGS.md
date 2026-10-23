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

## RQ3 — Calibration: **large gain, but mostly undoing class weights**

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

### Class-weight check (added 2026-10-23, D-037)

The study's models are trained with **balanced class weights**, which
up-weight the rare failing rows and push raw probabilities up. To see how
much of the gain above only undoes that, the same gradient-boosting model
was trained without class weights (`scripts/class_weight_check.py`;
`class-weight-summary.md`; 5 seeds; same 9 projects with a calibrator):

| Same 9 projects | Balanced, raw | Balanced, isotonic | Unweighted, raw | Unweighted, isotonic |
|---|---|---|---|---|
| ECE | 0.118 | 0.021 | 0.030 | 0.021 |
| Brier | 0.090 | 0.022 | 0.029 | 0.023 |
| Skip-risk gap (50 % budget policy) | 0.306 | 0.067 | **0.054** | 0.071 |
| PR-AUC (pooled, n = 9) | 0.138 | | 0.103 | |

- **Most of the calibration gain undoes the class weights.** A model
  trained on the natural failure rate is already well calibrated (ECE
  0.030). Calibrating it lowers ECE to 0.021 on average, but helps on only
  5 of 9 projects and hurts on 4. The clear exceptions are the projects
  with the most failures: wicket-bootstrap (0.171 → 0.102) and HikariCP
  (0.020 → 0.013).
- At commit level, the unweighted raw model's skip-risk estimate is as
  close to reality as any calibrated variant (gap 0.054 against 0.067
  and 0.071); calibration does not improve it further.
- Balanced weights do help ranking (pooled PR-AUC 0.138 against 0.103,
  mostly through optiq, 0.357 against 0.050, which has 4 failing test
  commits). "Balanced weights + calibration" therefore keeps the better
  ranking *and* calibrated probabilities, but the unweighted model is an
  equally honest risk estimator.

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

## Hybrid B10 — rules order, calibrated stopping (added 2026-10-23, D-036)

B10 takes tests in the B3 rule order (recent failures, then shortest) and
uses the calibrated probabilities only to decide where to stop: tests are
added until the estimated skip risk is at most 0.05. The experiments were
rerun with `run_study.py` (same command; `rerun-hybrid.log`); every
earlier policy, calibration and ablation number reproduced exactly.

| Pooled (mean of project means) | Time | Recall (n = 9) | Safety (n = 9) | Est. skip risk | Observed miss rate |
|---|---|---|---|---|---|
| B3 rules, 50 % budget | 0.52 | 0.85 | 0.67 | 0.142 | 0.073 |
| B8 calibrated ML, 50 % budget | 0.50 | 0.84 | 0.68 | 0.120 | 0.074 |
| B10 hybrid, target 0.05 | 0.39 | 0.83 | 0.76 | 0.026 | 0.028 |

At the same test time (hierarchical bootstrap):

| Comparison | Safety Δ [95 % CI] | Recall Δ [95 % CI] |
|---|---|---|
| B10 − B8 | +0.075 [−0.055, 0.224] | +0.012 [−0.086, 0.074] |
| B10 − B3 (rules) | +0.075 [−0.001, 0.202] | +0.017 [−0.012, 0.063] |

- Against the rules at the same time, B10's safety is higher on 4 projects
  (wicket-bootstrap +0.34, optiq +0.25, HikariCP +0.05, jcabi-github +0.03)
  and equal on the other 5; it is lower on none. Recall is lower only on
  jsprit (−0.04). The pooled interval still touches 0, and wicket-bootstrap
  again contributes most.
- **B10 keeps its promise.** With a 5 % target, the observed share of
  commits where it missed a failure is at most 5 % on 10 of 11 projects
  (pooled 2.8 %, estimated 2.6 %). The exception is jcabi-github (observed
  20 %, estimated 4.4 %). With stricter targets (1–2 %) the estimate is too
  optimistic on 4 of 11 projects.
- B10 needs no time budget: it spends little where the model sees little
  risk (HikariCP 0.13, jade4j 0.23) and much where it sees more
  (wicket-bootstrap 0.75, LittleProxy 1.00). On jade4j this cost one of its
  two failing commits.

Reading: using the model to decide **how many** tests to run, and simple
rules to decide **which**, is at least as good as either alone on every
project here and gives a risk statement that mostly holds. The gain over
the same-time baselines is not statistically clear.

## RQ1/RQ2 — Ordering: **ML does not beat simple rules**

Pooled APFDc: recent-failures 0.76, shortest-first 0.74, random 0.65,
logistic regression 0.64, gradient boosting 0.58, failure-history 0.48.
Recall at 50 % of test time: recent-failures 0.71, shortest-first 0.70,
random 0.63, logistic regression 0.62, gradient boosting 0.53. Both ML
models are at or below random on average.

## Dependency graph: **small, project-dependent signal**

Source: "Dependency-graph signal" in `summary.md`. Three views of what
the change-impact graph contributes:

1. **Ablation** (gradient boosting, uncalibrated, mean over 5 seeds):
   removing the three structural features (`dep_reachable`,
   `dep_distance`, `dep_confirmed`) lowers PR-AUC on jcabi-github (−0.072,
   4/5 seeds), optiq (−0.080, 5/5) and HikariCP (−0.013, 5/5); elsewhere the
   change is within ±0.001. Recall/safety at budget 0.5 barely move: HikariCP
   recall +0.017, jade4j +0.5 (one of its two failing commits),
   jcabi-github slightly *worse* with the graph (−0.009 recall). History
   features matter far more (pooled PR-AUC 0.138 with all features vs 0.080
   without history, 0.119 without structural).
2. **Does the graph point at failing tests?** On the test split, compare the
   share of failing (commit, test) rows whose test the graph reaches from the
   change with the share of all rows. Projects with ≥ 20 failing rows:
   jsprit 0.96 vs 0.21 (lift 4.6), HikariCP 0.66 vs 0.49 (1.4),
   wicket-bootstrap 0.04 vs 0.04 (0.9), jcabi-github 0.05 vs 0.16 (**0.3**,
   failures occur in tests the graph does *not* reach). The other projects
   have 1–7 failing rows, too few to read.
3. **Graph-only selection (B4)** versus calibrated ML (B8), test time /
   recall / safety: jsprit 0.41 / 0.96 / 0.86 vs 0.35 / 0.92 / 0.71; Achilles
   reaches the same full safety with less time (0.33 vs 0.46); but on
   jcabi-github (0.16 / 0.05 / 0.06) and wicket-bootstrap (0.05 / 0.04 / 0.04)
   B4 runs almost nothing relevant. On graylog2-server and jOOQ the graph
   reaches almost no recorded test (B4 time ≈ 0), consistent with their
   sparse test recording.

Reading: where failures come from code the change touches (jsprit,
HikariCP), the graph is a real, cheap signal. Where failures come from
long-running or environment-dependent tests unrelated to the change
(wicket-bootstrap's persistent failure; jcabi-github's failures, whose cause
we have not inspected), the graph cannot see them and history features carry the
model. The graph is a useful *component*, not a decisive one, on this
data. Caveats: class-level results only, class-level (not method-level)
edges, and no type resolution (D-010).

## Honest summary

1. **Reliable risk estimates are achievable, but calibration is not the
   main reason.** Calibrating the class-weighted model cuts its
   calibration error by ~80 % and brings its commit-level risk estimate
   several times closer to reality; a model trained without class weights
   is nearly as well calibrated without any calibrator (D-037).
   Calibration adds a clear further gain only on the projects with the
   most failures (wicket-bootstrap, HikariCP).
2. **Risk-based fallback does not reliably beat spending the same time**
   on the budget. It is neutral on most projects and large on one
   (wicket-bootstrap) where failures are frequent and concentrated in an
   expensive test; the pooled interval just touches 0.
3. **ML ordering is not better than simple time-aware rules** (or random).
   Combining them works better: the hybrid B10 (rules order, calibrated
   stopping) is never worse than rules or ML at the same time, meets its
   5 % miss target on 10 of 11 projects, but its pooled gain is not
   statistically clear.
4. **The dependency graph helps on some projects** (jsprit, HikariCP,
   optiq) and is blind on others (jcabi-github, wicket-bootstrap); history
   features carry most of the model's signal.
5. Two of eleven projects carry no evaluable failures; several others very
   few. The evidence is about *these* projects and periods (2012–2016).

## What this means for the claim

A defensible thesis claim is that CodeDNA gives **honest, checked risk
estimates** for skipping tests (whether by training on the natural failure
rate or by calibrating a class-weighted model), used as a **stopping rule
on top of simple ordering** (B10), with a careful, cost-matched evaluation
showing **when** extra safety measures help (frequent, concentrated
failures) and when they do not. It is not that CodeDNA's ML selects tests
better than simple rules, nor that calibration by itself is the key
ingredient. Overturning that would need projects where
learned models clearly beat recent-failures ordering, which this data does
not show.
