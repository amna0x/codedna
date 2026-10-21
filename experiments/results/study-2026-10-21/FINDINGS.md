# Study findings — 6 RTPTorrent projects × 5 seeds (2026-10-21)

Raw numbers: `summary.md` / `summary.json` (generated) and the per-seed JSON
files. Protocol: docs/DECISIONS.md D-034. Data: RTPTorrent v1.1 (Mattis et
al., MSR 2020, CC BY 4.0). Everything below is computed from those files;
nothing is estimated by hand.

## Command

```bash
python scripts/run_study.py --out experiments/results/study-2026-10-21 --seeds 0 1 2 3 4 --workers 6 \
  hikaricp=experiments/datasets/derived/hikaricp.db littleproxy=experiments/datasets/derived/littleproxy.db \
  jade4j=experiments/datasets/derived/jade4j.db jsprit=experiments/datasets/derived/jsprit.db \
  wicket-bootstrap=experiments/datasets/derived/wicket-bootstrap.db dynjs=experiments/datasets/derived/dynjs.db
```

Run on code commit `1992e71` plus the study changes committed with these
results; 23 min 40 s on 12 logical CPUs. HikariCP's `dataset.csv` was reused
from `hikaricp-2026-10-21` (same code and data). The per-project
`dataset.csv` files (~24 MB) are not committed: rerunning the command
rebuilds them from the history databases, and each `experiment-seed*.json`
records the dataset's SHA-256 to check the rebuild is identical.

## How much evidence there is

| Project | Test commits | With failures | Failure rate (rows) |
|---|---|---|---|
| HikariCP | 286 | 20 | 2.0 % |
| LittleProxy | 53 | 5 | 0.3 % |
| jade4j | 63 | 2 | 0.1 % |
| jsprit | 52 | 7 | 0.5 % |
| wicket-bootstrap | 164 | 87 | 30.4 % |
| dynjs | 75 | 1 | 0.02 % |

Only HikariCP and wicket-bootstrap have enough failing test commits to say
anything per project. jade4j (2) and dynjs (1) are close to anecdotes. The
unweighted mean over projects ("All") gives each of them equal weight, so it
is noisy. jsprit's validation period has no failures, so its calibrator could
not be fitted and its "calibrated" policies use raw probabilities.
Seed variation is small for most policies (standard deviation ≤ 0.02), but
not for the fallback policies on small projects: on jsprit, B9r's test time
varies by ±0.26 and B9's by ±0.12 across seeds. Overall the uncertainty is
dominated by the few failures more than by model randomness.

## RQ3 — Does calibration make risk estimates more reliable?

**Mostly yes for the probabilities, not convincingly for the commit-level
risk estimate.**

- Expected Calibration Error, unweighted mean: none 0.122 → Platt 0.038 /
  isotonic 0.036. Without dynjs (whose raw model is badly over-confident, ECE
  0.45) and jsprit (not fitted): 0.066 → 0.038 (≈ −42 %). It improves or
  stays equal on every project where it could be fitted.
- Brier score: 0.116 → 0.036 (Platt) / 0.039 (isotonic); unchanged on
  HikariCP (0.020).
- Estimated skip risk vs observed miss rate, mean absolute error: B7
  (uncalibrated) 0.227 → B8 (calibrated) 0.074. **Almost all of this is
  dynjs**; without it 0.078 → 0.072. On LittleProxy the calibrated estimate
  is even further off (0.27).

## RQ4 — Does risk-based fallback improve the safety/cost trade-off?

At the default settings B9r (fallback only from the calibrated risk) looks
much safer than B8 (calibrated, no fallback): commit safety 0.59 → 0.82,
recall 0.80 → 0.89 — but it also spends more test time (0.51 → 0.64).
**Compared with B8 given the same test time** (B8's budget sweep, nearest
budget step at or below B9r's time):

| Project | B9r time | B9r safety | B8 safety at ≈ same time |
|---|---|---|---|
| HikariCP | 0.36 | 0.55 | 0.55 |
| LittleProxy | 0.82 | 0.60 | 0.60 (1.00 at 0.89) |
| jade4j | 0.86 | 1.00 | 1.00 |
| jsprit | 0.48 | 0.77 | 0.77 |
| wicket-bootstrap | 0.71 | **0.98** | 0.13 (0.63 at 0.75) |
| dynjs | 0.62 | 1.00 | 1.00 |

- On five projects, risk-based fallback is **no better than simply giving
  the calibrated selector the same time budget**.
- On **wicket-bootstrap** — the one project with frequent failures and a
  well-calibrated risk estimate (estimated 0.57 vs observed 0.50) — it is
  **much** better: near-perfect safety for ~71 % of the test time, where a
  plain budget of similar size catches only 13–63 % of failing commits.
- The simple unfamiliar-change rule alone (B9n) reaches 0.79 safety at 0.75
  time; combined with risk fallback (B9) 0.92 at 0.83.

## RQ1/RQ2 — Prediction and ordering

- No ordering consistently wins. Unweighted APFDc: shortest-first 0.72,
  recent-failures 0.72, logistic regression 0.71, random 0.67, gradient
  boosting 0.49, failure-history 0.48. Gradient boosting is worse than random
  on average (very poor on dynjs and LittleProxy).
- Ablations (PR-AUC) are dominated by wicket-bootstrap; structural (graph)
  features help on HikariCP only (0.039 vs 0.026 without them). Evidence for
  RQ5 is weak.

## Honest summary

1. **Calibration works** as a probability fix (ECE roughly halved where it
   can be fitted), but turning it into a reliable commit-level skip-risk
   estimate is not yet shown.
2. **Risk-based fallback is not a general win** over spending the same time
   budget — except when failures are frequent and the risk estimate is
   well calibrated (wicket-bootstrap), where it is a large win.
3. **ML ordering does not beat simple time-aware rules.**
4. The evidence is thin: 4 of 6 projects have ≤ 7 failing test commits.

## What would strengthen or overturn this

- More projects with more failures (RTPTorrent: Achilles, jOOQ, jcabi-github,
  graylog2-server, sling, optiq), and per-project results reported first.
- A cost-matched comparison built into the experiment (B8 at B9r's time) and
  confidence intervals by bootstrapping commits, instead of seed spread.
- Investigate wicket-bootstrap's failures (persistent/flaky tests?) before
  treating its result as evidence for fallback in general.
- Tune or replace gradient boosting (it underperforms logistic regression).
