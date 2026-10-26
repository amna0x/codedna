# Failure-conditional tuned gate (B13f), exploratory four

Protocol: `docs/TUNED_GATE_CONDITIONAL_PROTOCOL.md`, committed (cf7b017)
before this run; code b8a5175. Command:
`OMP_NUM_THREADS=1 python scripts/run_tuned_gate_check.py <data> --conditional`.
Same four `dataset.csv` inputs as B13 (SHA-256 in `config.json`). Every
number is copied from `summary.json` or the per-project JSON. The default
(B13) mode of the edited script was rerun into a scratch folder and gave
byte-identical per-project JSON to `tuned-gate-2026-10-26/`.
(In `summary.md` the column "B13 blocks" counts B13f's tuned blocks.)

## Results

| Project | Product time / safety | B13f time / safety | B13f λ per block |
|---|---|---|---|
| HikariCP | 1.000 / 1.000 | 1.000 / 1.000 | full ×5 |
| jade4j | 0.984 / 1.000 | 1.000 / 1.000 | full ×5 |
| LittleProxy | 0.998 / 1.000 | 1.000 / 1.000 | full ×5 |
| wicket-bootstrap | 0.941 / 0.992 | 0.796 / 0.984 | full, 0.3, 0.5, 0.5, 0.02 |

**B13f minus gated product**, equal project weight, 2000 draws: time
−0.032 [−0.037, −0.027], safety −0.002 [−0.007, 0.003], recall −0.0002
[−0.0006, 0.0001]. Safety is at least 0.95 on 4 of 4 projects (needed 3).
Rule outcome: **B13f saves time**.

Pooled over the 4 tuned blocks (328 commits, 205 failing): commit safety
0.980, Wilson upper bound on one minus safety 4.3 %.

## What it means

- B13f fixes B13's safety problem on HikariCP, but only by giving up: no
  HikariCP audit window has enough failing commits for the bound to pass,
  so it runs every test there. B13f is also stricter than the plain gate on
  jade4j and LittleProxy, where it runs the full suite in the one block the
  gate accepted.
- The whole time saving comes from wicket-bootstrap, the one project with
  plenty of failing history (248 failing evaluation commits).
- So it is a trade-off: B13 saves 13 points but lets HikariCP's commit safety
  fall to 0.914; B13f keeps safety but saves 3 points, less than B12f's
  4.7. A strict promise about failing commits needs many failing commits
  in the audit window. That is a data limit, not a tuning problem.

## Limits

As for B13: four previously inspected projects, exploratory, one fit per
block, and the commit bootstrap ignores serial dependence.
