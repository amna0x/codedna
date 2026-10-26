# Conformal-risk-control stopping (B12), exploratory

Protocol: `docs/CRC_STOP_PROTOCOL.md`, committed (fe8d9cf) before this run.
Command:
`OMP_NUM_THREADS=1 python scripts/run_crc_check.py <data> --out experiments/results/crc-check-2026-10-26`.
Inputs are the four `dataset.csv` files of the rolling-origin study (same
SHA-256 values). Every number is copied from `summary.json` or the
per-project JSON.

## Results

| Project | Commits (failing) | B10 time / miss | B12 time / miss | B12 safety | Gated product time / miss | Chosen λ per block |
|---|---|---|---|---|---|---|
| HikariCP | 714 (81) | 0.339 / 0.020 | 0.110 / **0.056** | 0.506 | 1.000 / 0.000 | 0.5, 0.1, 0.1, 0.2, 0.05 |
| jade4j | 157 (28) | 0.915 / 0.000 | 0.700 / 0.013 | 0.929 | 0.984 / 0.000 | full, 0.2, 0.1, 0.5, 0.5 |
| LittleProxy | 131 (38) | 0.913 / **0.084** | 0.932 / 0.000 | 1.000 | 0.998 / 0.000 | 0.005, 0.02, 0.02, 0.1, 0.5 |
| wicket-bootstrap | 410 (248) | 0.941 / 0.005 | 0.728 / 0.015 | 0.976 | 0.941 / 0.005 | 0.2, 0.3, 0.5, 0.5, 0.2 |

(jade4j's first block could not be fitted; every policy ran the full suite
there.)

**Question 1.** B12 keeps the 5 % commit-miss target on 3 of 4 projects
(HikariCP 5.6 %). B10 also keeps it on 3 of 4, but on different projects
(it fails on LittleProxy at 8.4 %, which B12 fixes). Pooled over commits,
the miss rate is 3.4 % for B12 against 2.0 % for B10.

**Question 2.** B12 minus the gated product, equal project weight, 2000
hierarchical draws: time −0.363 [−0.379, −0.348], safety −0.145
[−0.185, −0.110], recall −0.143 [−0.173, −0.104]. The protocol's rule reads
**B12 saves time**: the time interval is below 0 and the target holds on 3
of 4 projects.

## The catch

The target is a miss rate over *all* commits, and most commits have no
failure. On HikariCP only 11 % of commits fail, so a 5 % miss rate over all
commits allows about half of the failing commits to be missed: B12's
safety there is 0.506. CRC did exactly what it promises (the bound is on the
expected loss over all commits), and the promise is too weak where failures
are rare. B10's own 5 % target has the same weakness; it is less visible
only because B10 stops more conservatively.

So the time saving is real, but much of it comes from the definition of the
target, not from better stopping. The honest reading:

- CRC gives a principled, assumption-light threshold, and on these projects
  its target held about as often as B10's.
- A commit-level miss target over all commits is the wrong promise for a
  safety brake. The promise should be conditional on the commit actually
  failing (commit safety). That needs a new protocol; it is not tuned into
  this result.

## Limits

Four previously inspected projects, exploratory. Time-ordered commits are
not exchangeable. One fit per block; the commit bootstrap ignores serial
dependence.
