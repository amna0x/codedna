# CodeDNA vs the closest 2026 work

Status: **provisional** (2026-10-24). Built from the papers' abstracts and the
parts of the full texts we could read, not from a systematic review. Re-check
each row against the full paper before the final report. Do not write "first"
anywhere.

## Working claim

> CodeDNA evaluates whether calibrated stopping improves the testing
> trade-off across history-based test orderings, and identifies when its risk
> estimates cannot be trusted.

What this claim does **not** say: that the stopping rule works on any ordering,
that the 5% target is a guarantee, or that ML ordering beats simple rules
(our own study says it does not, D-036).

Calibrated per-test probabilities do not automatically give an accurate joint
skip risk: `1 − Π(1 − p)` assumes independent failures, and one bug often
fails several tests. Every result must report estimated against observed miss.

## Comparison table

| | MOX (2026) | Context-Aware Sequential Ranking (2026) | DANTE (ICST 2026) | AutoTCP (EMSE 2026) | CodeDNA |
|---|---|---|---|---|---|
| Task | Selection + ordering | Ordering (dynamic TCP) | Selection + ordering | Ordering | Ordering + stopping (selection) |
| Ordering signal | Pareto over cost, impact, coverage, traceability score | History + code-change/test similarity, DQN over 6 ranking operators | Training-free history "stickiness" + TF-IDF change/test relevance, ÷ time | AutoML-chosen pipeline | Simple rules (recent failures, then shortest); ML only for probabilities |
| Probabilities calibrated? | No: impact score is a heuristic relevance measure | Yes: class-conditional split conformal (α = 0.10), ACI-style adaptive variant | No explicit probability; Wilson confidence used to weight history windows | Not the focus | Yes: isotonic / Platt fitted on a validation split |
| What stops execution | Configurable impact budget / risk threshold θ (default 0.10) on **residual heuristic impact** | **Cost budget** β ∈ {0.05, 0.10, 0.25, 0.50}: stop at first prefix whose estimated cost reaches β. Conformal candidates are a soft prioritisation layer; "candidate-first gating" is a DQN ablation. No miss-rate target found as a stopping criterion | Time budget (2–30% of suite) | Not applicable | **Estimated joint skip-risk target** (default 5%): add tests until `1 − Π(1 − p_skipped) ≤ target`, no budget |
| Safety claim | Retention of recorded failures under budget; no calibrated-safety claim | Explicitly no new conformal-validity theorem; no arbitrary-shift guarantee | None | None | Measured observed miss vs estimated risk; no guarantee |
| Data | 2 ABB industrial logs (iofrol, paintcontrol). **No code changes**: change events inferred from failing tests | **RTPTorrent**, 4 Java projects (same dataset family as ours), strict pre-build history | LRTS, 10 projects (9 Java), long-running suites | 25 open-source systems | RTPTorrent, 11 Java projects; real Git changes + static dependency graph |
| Cost-matched comparison | Not reported in the abstract | Fixed budgets | Fixed budgets | — | Yes: every policy compared with rules / B8 at the same real time (D-035) |
| Transfer to new projects | — | — | Training-free, adapts per project | — | Tested (D-039): **not reliable**; target validation required |

## Where CodeDNA is different (provisional)

1. **Stopping criterion.** The other systems stop on a cost budget (CASR,
   DANTE) or a residual heuristic-impact budget (MOX). CodeDNA stops on an
   estimated probability that a skipped test fails, built from calibrated
   per-test probabilities, and then reports how well that estimate matches the
   observed miss rate. We must still compare the exact stopping criteria in the
   full texts. CASR's formal "stopping rules" section is a budget-crossing
   stopping time, as far as we can read.
2. **Ordering-agnostic test.** The stopping rule sits on top of a simple order.
   We test it across several history-based orderings (rules, DANTE-style). That
   supports broader usefulness, not universal reliability.
3. **Knowing when not to trust the estimate.** Cross-project transfer failed in
   2 of 9 calibrated directions and 3 directions had no usable calibration
   (D-039). CodeDNA turns this into a validation gate: no adequate, recent,
   earlier target evidence means "risk unvalidated, run the full suite".

## Threats to this claim

- CASR already combines calibration and stopping on the same dataset family.
  If its full text includes a miss-rate-driven stop, difference (1) shrinks to
  "joint skip risk vs per-test conformal set", and the claim must narrow.
- B10's pooled gain over rules at the same time is not significant
  (+0.075 [−0.001, 0.202]). The claim is about trade-off evidence and honest
  risk reporting, not a clear win.
- Few failing commits on some projects (jade4j: 2 in the transfer target window).

## Sources

- MOX: <https://www.mdpi.com/2079-9292/15/17/3854>
- Context-Aware Sequential Ranking: <https://www.mdpi.com/2227-7390/14/18/3276>
- DANTE: <https://conf.researchr.org/details/icst-2026/icst-2026-research/44/DANTE-Data-Driven-Test-Case-Selection-and-Prioritization-for-Long-Running-Test-Suite>
- AutoTCP: <https://link.springer.com/article/10.1007/s10664-026-10862-y>
