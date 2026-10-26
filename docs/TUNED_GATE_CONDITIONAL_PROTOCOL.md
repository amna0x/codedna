# Failure-conditional tuned gate protocol (B13f) — 2026-10-26

Status: fixed and committed before any result of this check was computed.
It follows `docs/TUNED_GATE_PROTOCOL.md`. On the exploratory four, B13 kept
the gate's targets but let 8.6 % of HikariCP's failing commits through
(`experiments/results/tuned-gate-2026-10-26/FINDINGS.md`), because a 5 %
miss rate over *all* commits is a weak promise where few commits fail. The
same lesson led from B12 to B12f. This is a new question with its own output
folders, not a re-tune of B13.

## Question

If the threshold search checks the miss rate **among failing audit commits**
instead of among all audit commits, does it keep 95 % commit safety while
still saving time against the gated product?

## Method (B13f)

Everything as in `docs/TUNED_GATE_PROTOCOL.md` (data, blocks, fitting,
order, grid, fixed-sequence search from the strictest λ upwards, full suite
when the strictest fails) except one change: the unchanged D-041 check is
applied to the outcomes of the **failing audit commits only**. Its Wilson
bound is then a bound on one minus commit safety; the at-least-10 failing
commits and 90 % recall rules are unchanged. Selection never needs to know
whether the new commit fails.

With zero misses the bound passes 5 % only from about 52 failing audit
commits, so B13f will run the full suite more often than B13. That cost is
part of what is measured.

## Analyses

As for B13, per set (exploratory four; confirmatory nine), never pooled
across sets, and every result exploratory:

- Per project: time, commit safety, test recall and commit miss rate of B13f
  and of the gated product; blocks with λ ≠ full; chosen λ per block.
- B13f minus product in time, safety and recall, equal project weight, the
  same hierarchical bootstrap (2000 draws, seed 0).
- Pooled over blocks where B13f did not run the full suite: commit safety and
  the Wilson upper bound on one minus safety.
- **Rule.** *B13f saves time* if the time interval's upper end is below 0,
  the safety interval's lower end is at or above −0.05, and B13f's commit
  safety is at least 0.95 on at least ⌈0.75·k⌉ of the k projects. *B13f costs
  time* if the time interval's lower end is above 0. Otherwise
  *inconclusive*.

## Outputs

`experiments/results/tuned-gate-conditional-2026-10-26/` (exploratory four)
and `experiments/results/tuned-gate-conditional-confirmatory-2026-10-26/`
(confirmatory nine), same files as the B13 check, plus `FINDINGS.md`
written by hand from the saved numbers only.
