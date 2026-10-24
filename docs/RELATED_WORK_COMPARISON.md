# CodeDNA comparison with recent work — 2026-10-24

This is a focused comparison, not a systematic review or proof of novelty.
Working claim: evaluate calibrated stopping on history-based test orders, with
measured target-project validation and explicit failure cases. Supervisor review
remains pending; no claim that CodeDNA is the first or generally superior.

| Work | Supported purpose | Relationship and limits |
|---|---|---|
| DANTE (ICST 2026) | Training-free history and commit-aware selection/prioritization | Strong baseline; our DANTE-H adaptation omits published components and is not full reproduction. Check whether stopping adds value over both strong rules and this adaptation. |
| MOX (Electronics 2026) | Pareto cost/impact/coverage/traceability optimization | Paper distinguishes residual-impact budget from calibrated safety. Historical change events are inferred from failures; compare prospective information assumptions rather than treating its score as a calibrated probability. |
| Context-Aware Sequential Ranking (Mathematics 2026) | RTPTorrent history/semantic risk, conformal candidate sets, candidate gating and sequential ranking | Has formal stopping rules and budgeted evaluation. Distinguish its candidate coverage and budget termination from CodeDNA's estimated aggregate omitted-test failure risk. It cannot be dismissed as only ranking without stopping. |
| AutoTCP (Empirical Software Engineering 2026) | Automatically compose/tune predictive workflows for prioritization | Compares prediction/ranking and includes overhead; no verified claim here that it implements CodeDNA's aggregate-risk stopping. Detailed absence claims require full algorithm review. |

Sources:
- DANTE: https://doi.org/10.1109/ICST69053.2026.00080 ; author artifact https://zenodo.org/records/18900675
- MOX: https://www.mdpi.com/2079-9292/15/17/3854
- Context-Aware: https://www.mdpi.com/2227-7390/14/18/3276 (especially conformal candidate sets and sequential stopping)
- AutoTCP: https://link.springer.com/article/10.1007/s10664-026-10862-y

Research evidence already exists for matched-time comparisons, D-037 class-weight
ablation, B10 and transfer failure. This extension builds on those results. It
does not restart the original research or add more classifiers. Java remains the
implemented language; the owner has deferred additional languages until the
software workflow is complete. Deadline is approximately May/June, not November.
