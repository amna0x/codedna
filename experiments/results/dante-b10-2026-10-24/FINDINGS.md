# DANTE-H / calibrated stopping findings — 2026-10-24

Protocol: [docs/DANTE_B10_PROTOCOL.md](../../../docs/DANTE_B10_PROTOCOL.md),
committed (205ef73) before any result was computed. **Verdict under the
pre-specified rule: inconclusive.**

DANTE-H is a history-only approximation of DANTE (no TF-IDF change/test
relevance). It is not a reproduction of DANTE.

## What ran

Four projects (the only ones with restored datasets): HikariCP, LittleProxy,
jade4j, wicket-bootstrap. Five seeds each, 20 reports. All four `dataset.csv`
digests match the original study (row-level SHA-256 as in `experiment-seed*.json`).
B10 here reproduces the transfer study's fresh within-project controls exactly
(e.g. HikariCP time 0.1333, recall 0.7273, safety 0.5, observed miss 0.035),
which checks that the pipeline is the same.

A rerun into a separate folder gave identical reports (all 20, timings excluded).

## Main evidence

| Project | Failing / test commits | D2 time | D2 safety | D1 safety at D2 time | D2 obs. miss (target 0.05) |
|---|---|---|---|---|---|
| HikariCP | 20 / 286 | 0.156 | 0.45 | 0.45 | 0.0385 ✓ |
| LittleProxy | 5 / 53 | 1.000 | 1.00 | 1.00 | 0.0 ✓ (runs everything) |
| jade4j | 2 / 63 | 0.229 | 0.50 | 0.50 | 0.0159 ✓ |
| wicket-bootstrap | 87 / 164 | 0.750 | 0.986 | 0.531 | 0.0073 ✓ |

Means over seeds; full tables in [summary.md](summary.md).

- **D2 meets the 5% observed-miss target on all four projects.** On LittleProxy
  this is trivial: it runs the full suite and saves nothing. jade4j has only two
  failing test commits, so it says almost nothing.
- **D2 − D1 at the same time:** no difference on HikariCP, LittleProxy, jade4j.
  Positive only on wicket-bootstrap (+0.455 safety, mean over seeds).
- **The wicket-bootstrap gain is a budget cliff, and it depends on the seed.**
  Per seed, D2 − D1 safety is +0.01, +0.77, +0.92, +0.59, −0.01. A fixed time
  budget around 72–79% of the suite drops commit safety to 0.06–0.41; at 88–94%
  it is 0.99. D2 reaches 0.977–1.0 safety at 69–76% mean time, because it
  spends more time on risky commits and less on safe ones. When the seed's model
  makes D2 stop later (seeds 0 and 4), the matched budget is past the cliff and
  the difference vanishes. B10 − B3 shows the same pattern (+0.34 mean).
- **The ordering barely matters once the stop is calibrated.** D2 − B10 is 0 on
  three projects; on HikariCP D2 spends 2.3 points more time for 6.6 points
  less recall. DANTE-H is not a stronger ordering than the rules here
  (D1 − B3 at D2 time: 0 or slightly negative).
- **Estimated vs observed miss:** estimated skip risk is above observed miss on
  all four (e.g. HikariCP 0.0448 vs 0.0385, wicket 0.0152 vs 0.0073). The joint
  estimate is conservative here, not exact.
- **Overhead:** DANTE-H scores for a whole dataset take 0.03–0.28 s
  (4.6k–34.8k rows); a D2 decision takes 0.09–0.41 ms per test commit.

## Verdict against the rule

- D2 − D1 safety ≥ 0 on all four: **yes**.
- Interval excludes 0 on at least two: **no**, only wicket-bootstrap.
- D2 meets the target on at least three: **yes** (four).

So **inconclusive**. The defensible statement is narrower: calibrated stopping
was never worse than a fixed budget at the same time on two history orderings,
and on the one project with many failures it avoided a budget cliff that a fixed
budget falls into. That is one project and seed-dependent, not general evidence.

## Limits

Four projects, few failures on three. Seeds change only the model, so the
seed spread shows model sensitivity, not new data. Intervals resample commits
and ignore serial correlation. "Mean interval over seeds" in the summary is a
descriptive average of per-seed intervals, not a pooled interval. DANTE's
relevance component is missing, so this does not test DANTE itself.
