# D086: improve existing brake and witness methods

Status: implementation in progress, not a validated release. Owner authorized
the previous improvement ideas and clarified that the objective is better
measured performance of the existing features, rather than product expansion.
Website work and the D085 friend kit remain separate and unchanged.

## Work and acceptance criteria

1. Live shadow checking: retain the original recommendation, execute the full
   suite, identify observed failures outside it, retain missing/skipped/build
   outcomes and measure analysis/execution/whole-operation cost. Shadow results
   never authorize skipping and an uncommitted snapshot never becomes training
   history. Six new focused fixture checks passed; full validation pending.
2. Improve input allocation: prioritize changed boundaries instead of spending
   a small budget on unrelated unchanged constants. This is syntax guidance;
   no instrumented branch-coverage or feedback-directed-search claim is made.
   Further search/reduction changes require equal-budget comparisons.
3. Extend supported scenarios gradually, with explicit contracts, deterministic
   serialization, bounded execution and standalone reproduction. Preserve
   unsupported and inconclusive results. Do not infer purity from syntax.
4. Interpret differences only against an explicit applicable expectation.
   A JUnit draft must not silently use the base implementation as an oracle.
   Keep observed behavior separate from risk-based permission to skip tests.
5. Preserve all attempts when checking unstable outcomes. A later passing
   observation cannot erase an earlier failure. Fault-inject incomplete output,
   interruption and failed writes; uncertainty remains visible.
6. Freeze source, scenarios, seeds, budgets and outcome criteria before new
   comparisons. Existing synthetic cases are development data; never reclassify
   them as independent real-world evidence. Audit fresh real-change feasibility
   without selecting only changes with favorable observed results. Retain old
   studies and thresholds, including mixed/negative findings.

## Validation schedule

Use focused inexpensive regression checks while implementing each component.
After the complete implementation batch is stable, run one full Maven-inclusive
suite and then validate a newly built executable/installer. Do not repeat full
suites for documentation-only changes or unchanged source. A failure requires
repair and appropriate revalidation, not suppressing or relabelling the test.
Performance comparisons and real-project evaluations have separate questions
and run after their protocols and implementations are frozen. Report measured
analysis plus execution/audit costs; shadow full-suite duration alone cannot
establish counterfactual selected-run savings. No positive outcome is promised.

## Workspace

Git worktree: C:/Users/hp/OneDrive/Documents/ChatGPT/codedna/.worktrees/core-evidence
Branch: codex/core-evidence-improvements, based on merged PR #23.
Use the existing checkout's virtualenv with this worktree's backend and plugin
directories on PYTHONPATH. No new dependencies or independent implementation.
