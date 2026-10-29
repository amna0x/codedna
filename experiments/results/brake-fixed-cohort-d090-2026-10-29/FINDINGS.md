# AI brake: fixed-cohort evidence-gate replay

Frozen application a02d20f; unchanged target 0.05. Used all 75 fixed evaluation
heads from the D089 ActiveMQ/main cohort, its verified Git ancestry and raw
unfiltered class inventories. Evaluation labels were read only after saving
every gate decision in decisions-before-evaluation-labels.json.

Each target has 100–101 known prior training/audit ancestors. Applying the live
50/25/25 historical split leaves 25–26 audit commits, including six failing
commits. Even zero audit misses would yield a one-sided Wilson upper bound of
9.43–9.77 percent, above the fixed five-percent target. B10 also lacks the required
ten failure-bearing audit commits. CRC has six failing audit commits, below its
nineteen-commit minimum at this target; its zero-miss correction is 1/7, about
14.29 percent. Neither method can authorize skipping, regardless of model fit.

Consequently all 75 decisions require the full suite. Recorded full-suite
outcomes contain 27 failing commits and 39 failing-class occurrences. Fallback
retains every recorded failure and offers no test-selection saving. Zero misses
here follows from running everything; it is not evidence of predictive ability
or a future-risk guarantee. No probabilities, features or model fits were
fabricated for a gate that cannot pass.

Historical class-duration sum is 1,469,989.694 seconds. Fallback retains that
entire estimate, before analysis overhead. This is not elapsed CI time: parallel
classes, build startup, audits and environment costs are not measured by this
sum. The preflight runner took 9.461 seconds and the whole replay 12.850 seconds;
these are audit-runner timings, not live-brake latency or new CI execution.

This concludes the evidence-gate feasibility replay with no demonstrated saving
on this cohort. A fitted-model discrimination comparison, structural/simple
baseline execution, independent fresh builds and matched net-CI wall-time study
were not performed. They must not be described as completed. The fixed-gate
result already rules out skipping gains here; further fitting cannot overcome
the evidence floor without more qualifying history or a different validated
method. Safety thresholds and failure labels were not weakened.

The evaluation is now inspected. Do not change its windows or retune policy on
these outcomes and relabel another run as independent confirmation.
