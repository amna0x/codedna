# CodeDNA compared with closely related work (updated 2026-10-25)

A focused comparison, not a systematic review. It exists so the report's
claim can be checked line by line. Reference numbers match the list at the
end of [REPORT_SYSTEM_DRAFT.md](REPORT_SYSTEM_DRAFT.md).

**What was read.** "Full text" means the paper's method and evaluation
sections were read. "Abstract" means only the abstract and the publisher's
record were available; claims of absence for those works are marked
*unverified*.

## The claim being checked

CodeDNA turns calibrated per-test failure probabilities into a **per-commit
estimate of omitted-failure risk** (the probability that at least one
skipped test would fail), uses that estimate as a **stopping rule on top of
a simple history ordering** (B10, D-036), and **uses it only when a replay
on the target project's recent audit history kept the miss target**
(Wilson upper bound, at least ten failing commits, at least 90 % recall),
recommending the full suite otherwise (D-041). The gate checks outcomes
against the target; it does not test the calibration of each estimate. It evaluates this against simple rules at
matched test time and reports where it does not help.

None of the parts is new on its own. Industrial tools already stop at an
aggregate catch-rate target, conformal methods already give coverage sets,
and deployment checks on a model's recall already exist. The combination is
what the report evaluates. The report never says CodeDNA is the first to do
it.

## Comparison on the five properties that matter

| Work | Read | Per-change risk estimate shown | Probabilities calibrated / checked | How it stops | Checks itself before trusting | Falls back to full suite |
|---|---|---|---|---|---|---|
| Predictive Test Selection, Facebook [9] | Full text | No; scores are "estimated likelihood", not reported to developers | No calibration analysis | Score cutoff and count cutoff tuned on a one-week holdout so aggregate test recall > 0.95 and change recall > 0.999 | Yes, at model level: weekly retrained model is accepted only if selection rate < 0.3 at recall 0.9 | No; later stabilisation testing catches what slips |
| PTS replication, TU Wien [10] | Full text | No | Mentioned, not analysed | Cutoffs swept against STARTS | No | No |
| Launchable "confidence curve" [11] | Product docs | No; confidence is the historical share of failing sessions caught at a given runtime | Aggregate holdout curve | Runtime chosen for a target confidence (e.g. 90 %) | Holdout evaluation only | No |
| Develocity Predictive Test Selection [12] | Product docs | No | "Calibrated to catch over 99 %" in aggregate | Conservative / Standard / Fast profiles | Simulator replays past builds | No; but always runs new, changed, recently failed and flaky tests (like CodeDNA's must-run policy, D-050) |
| Context-Aware Sequential Ranking [13] | Full text (same RTPTorrent data) | No; reports candidate-set coverage | Class-conditional split conformal sets, α = 0.10, adaptive α update | Cost budget (10/25/50 % of realised duration); a pre-execution variant uses predicted durations | Prequential evaluation; no per-project acceptance step found | No; candidate sets only reorder |
| MOX [14] | Full text (sections 1–3) | No | Explicitly "not an empirically calibrated safety guarantee" | Greedy selection under a residual impact budget θ, Pareto front | No | No |
| DANTE [15] | Abstract | *Unverified*; none described | None described | Selection and prioritisation; no cutoff rule described | *Unverified* | *Unverified* |
| AutoTCP [16] | Full text | No | No | Ranking only | Per-build retraining | No |
| Risk-aware batch testing, Mozilla [17] | Full text | Commit regression probability (to flush batches) | Not evaluated; authors say scores may be miscalibrated | Batch flushed when P(batch has a regressor) passes a threshold (independence assumed) | Thresholds tuned on an evaluation split | No |
| Continuous test suite failure prediction [18] | Abstract | Predicts whether the whole suite will fail | Not reported | Skip the whole suite run | *Unverified* | *Unverified* |
| TDAD [21] | Abstract + method summary | No | No | Static code-to-test map queried by the agent | No | No |
| TestPrune [22] | Abstract | No | No | Minimised regression subset for the agent | No | No |
| Westermo CRC project [27] | README and code docs | No; bounds the expected share of missed failing tests | Conformal risk control (+ adaptive variant) | Threshold chosen by CRC at α = 0.05 / 0.10 | Marginal CRC bound; exceeded on 2 systems under drift | No |
| **CodeDNA (B10 + D-041)** | — | **Yes**, `1 − Π(1 − p)` over skipped tests, shown with reasons | Platt / isotonic on a held-out window; ECE, Brier, reliability bins | Skip-risk target on top of a rules ordering | **Yes, per project and per time block**: the stopping rule must have kept its miss target on recent audit history | **Yes**, whenever the check fails or the change is outside what was analysed |

## Where the claim is weakest

1. **Predictive Test Selection [9] is the closest prior work.** It also uses
   a learned model, a holdout and a recall target, and it gates model
   deployment. The difference is real but narrow: its targets are aggregate
   and its probabilities are not checked, while CodeDNA gives a per-commit
   number and accepts it only where stopping on it kept the target on
   that project's recent history. An examiner may call this an
   incremental refinement. That is a fair description. Measured with B11
   (D-061, exploratory): no difference in safety at matched time
   (+0.007 [−0.063, 0.091]); B11's aggregate targets held less often (test
   recall on 2 of 4 projects, change recall on none; B10's target on 3 of 4).
2. **Commercial tools [11, 12] already sell "run until X % confidence".**
   Their confidence is an aggregate historical rate, not a per-change
   estimate, and they are closed. CodeDNA's evaluation is open and
   reproducible; that is a contribution of method, not of idea.
3. **Calibration is not new and does not always work.** Calibration of JIT
   defect predictors was studied at MSR 2025 [19]: ECE of 7–35 % and
   post-hoc calibration did not consistently help. CodeDNA's ECE falls from
   0.118 to 0.021, but D-037 shows much of that only undoes balanced class
   weighting. The defensible finding is narrower: a low ECE can hide an
   underestimate of the summed risk of many skipped tests, and without
   calibration B10 broke its target on 3 of 9 projects.
4. **The independence assumption** in `1 − Π(1 − p)` is shared with the
   Mozilla batching work [17]. One fault can fail several tests, so the
   estimate is not trusted on its own: the gate accepts it only where the
   observed miss rate stayed within the target.
5. **The stopping rule does not beat a fixed budget.** In the exploratory
   rolling-origin study, B10 minus a matched fixed budget is −0.003
   [−0.036, 0.029] in safety. The value claimed is a *checked* risk number
   and an honest refusal, not more failures caught.
6. **DANTE [15] was read from the abstract only.** Its full paper should be
   checked for a stopping rule before the report states that it has none.

## Conformal risk control (D-063)

A conformal-risk-control stop was added and measured (B12, B12f). B12f
bounds misses among failing commits and kept 95 % commit safety on 4 of 4
exploratory projects, against 2 of 4 for B10. One open-source project [27]
already applies conformal risk control to test selection with a test-level
loss, so CodeDNA's claim is limited to the commit-level, failure-conditional
loss on open Java data and its use in the brake.

## Agents

The two agent works found [21, 22] choose tests for coding agents from a
static map or by minimising the suite. Neither states a risk for the tests
it leaves out. The agent study using CodeDNA's brake (D-059) has no paid
agent runs, so the report claims nothing about agents improving.

## Sources

- [9] https://arxiv.org/abs/1810.05286
- [10] https://repositum.tuwien.at/handle/20.500.12708/215633
- [11] https://help.launchableinc.com/features/predictive-test-selection/requesting-and-running-a-subset-of-tests/choosing-a-subset-optimization-target/how-a-confidence-curve-is-generated/
- [12] https://docs.develocity.ai/2026.3/guides/predictive-test-selection/
- [13] https://www.mdpi.com/2227-7390/14/18/3276
- [14] https://www.mdpi.com/2079-9292/15/17/3854
- [15] https://hdl.handle.net/11311/1309638 ; author artifact https://zenodo.org/records/18900675
- [16] https://link.springer.com/article/10.1007/s10664-026-10862-y
- [17] https://arxiv.org/abs/2604.00222
- [18] https://doi.org/10.1145/3460319.3464840
- [19] https://2025.msrconf.org/details/msr-2025-technical-papers/25/On-the-calibration-of-Just-in-time-Defect-Prediction
- [26] https://arxiv.org/abs/2208.02814
- [27] https://github.com/l-k-1-2/Predictive-test-selection
- [21] https://arxiv.org/abs/2603.17973
- [22] https://arxiv.org/abs/2510.18270


## 2026-10-27 literature update

FaithfulCut's public research artifact already studies censored/delayed feedback,
random full-suite audits, online risk control and monitoring. The author labels
it under review. Its build-escape loss differs from CodeDNA's any-omitted-failure
loss, but audits or drift monitoring alone cannot support a novelty claim.
Source: https://github.com/TheDeadcoder/FaithfulCut (reviewed revision
3e48eb578cfe11a876c7134d0e765147f073845a). No independent reproduction is claimed.
Read NOVELTY_REVIEW_2026-10-27.md for reviewed sources and DEFERRED_FEATURES.md
for proposals; no new method or superior result is claimed implemented.
