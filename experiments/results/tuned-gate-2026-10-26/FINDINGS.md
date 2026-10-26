# Tuned-threshold gate (B13), exploratory four

Protocol: `docs/TUNED_GATE_PROTOCOL.md`, committed (2ac7ac7) before this run;
code e508132. Command:
`OMP_NUM_THREADS=1 python scripts/run_tuned_gate_check.py <data> --out experiments/results/tuned-gate-2026-10-26`.
Inputs are the four `dataset.csv` files of the rolling-origin study (same
SHA-256 values as `config.json` records). Every number is copied from
`summary.json` or the per-project JSON. Python 3.13 in the cloud container;
the confirmatory run uses the laptop's environment.

## Results

| Project | Failing eval. commits | Gate blocks → B13 blocks | Product time / safety / miss | B13 time / safety / miss | Chosen λ per block |
|---|---|---|---|---|---|
| HikariCP | 81 | 0 → 5 | 1.000 / 1.000 / 0.000 | 0.713 / **0.914** / 0.010 | 0.02 ×5 |
| jade4j | 28 | 1 → 1 | 0.984 / 1.000 / 0.000 | 0.918 / 1.000 / 0.000 | full, full, 0.1, full, full |
| LittleProxy | 38 | 1 → 1 | 0.998 / 1.000 / 0.000 | 0.997 / 1.000 / 0.000 | full, full, full, 0.1, full |
| wicket-bootstrap | 248 | 5 → 5 | 0.941 / 0.992 / 0.005 | 0.774 / 0.976 / 0.015 | 0.05, 0.3, 0.5, 0.5, 0.2 |

(jade4j's first block could not be fitted; both policies ran the full suite.)

**B13 minus gated product**, equal project weight, 2000 draws: time
−0.130 [−0.139, −0.122], safety −0.026 [−0.042, −0.011], recall −0.008
[−0.015, −0.003]. B13's miss rate over all commits is at most 0.05 on 4 of 4
projects (needed 3). Rule outcome: **B13 saves time**.

Pooled over the 12 blocks where B13 did not run the full suite (1,181
commits): miss rate 1.10 %, one-sided Wilson upper bound 1.72 %.

## What it means

- **HikariCP shows cause 2 being fixed.** The gate rejected every block,
  because B10 at λ = 0.05 caught under 90 % of failing tests. At λ = 0.02 the
  audit passed, and B13 ran 71 % of the suite instead of 100 %.
- **wicket-bootstrap shows the other direction.** B10 was too cautious there,
  and B13 loosened λ to as much as 0.5. That cut time from 0.94 to 0.77.
- **jade4j and LittleProxy hardly change.** Most of their blocks have too few
  audit commits or too few failing ones (cause 3), so B13 runs the full suite
  there, as the gate does.
- **The catch is the same as for B12.** B13 keeps the gate's targets, but
  those targets are a miss rate over *all* commits plus test recall. On
  HikariCP that allows 8.6 % of failing commits to be missed (safety 0.914),
  where the full suite missed none. B12f (conformal control conditional on
  failure) kept safety at or above 0.95 on all four projects but saved only
  4.7 points of time. B13 saves more and protects failing commits less.

## Limits

Four previously inspected projects, exploratory. The design used the
confirmatory gate evidence, so the confirmatory rerun is exploratory too.
One fit per block. The commit bootstrap ignores serial dependence, and the
fixed-sequence guarantee assumes the audit window represents the next block.
