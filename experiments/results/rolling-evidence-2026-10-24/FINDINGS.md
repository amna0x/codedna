# Rolling-origin evidence study — findings (exploratory set only)

Protocol: `docs/EVIDENCE_STUDY_PROTOCOL.md`, committed (53cfb8d on branch
`claude/evidence-study`) before this run. Command:
`OMP_NUM_THREADS=1 python scripts/run_rolling_evidence.py <data> --out experiments/results/rolling-evidence-2026-10-24`.
Numbers below are copied from `summary.json` / per-project JSON.

## What was run

Only the four previously inspected projects (HikariCP, LittleProxy, jade4j,
wicket-bootstrap) were available offline; RTPTorrent's host was unreachable
from the run environment. All four are **exploratory** by protocol, so this
run gives no confirmatory verdict. The confirmatory set is empty: verdict
"inconclusive", gate "unexercised", by rule.

## Results (5 rolling blocks over the last 50% of each history)

| Project | Failing commits | Gate accepted blocks | Fit failures | B10 safety | B3 safety (matched time) | Gated product time | Gated product commit miss rate |
|---|---|---|---|---|---|---|---|
| HikariCP | 81 | 0 / 5 | 0 | 0.8272 | 0.7531 | 1.0000 | 0.0000 |
| jade4j | 28 | 1 / 5 | 1 | 1.0000 | 1.0000 | 0.9838 | 0.0000 |
| LittleProxy | 38 | 1 / 5 | 0 | 0.7105 | 0.7895 | 0.9976 | 0.0000 |
| wicket-bootstrap | 248 | 5 / 5 | 0 | 0.9919 | 1.0000 | 0.9414 | 0.0049 |

B10 minus matched B3, equal project weight, hierarchical bootstrap 2000 draws:
safety -0.0032 [-0.0362, 0.0294], recall +0.0082 [-0.0054, 0.0196],
time -0.0147 [-0.0265, -0.0035] (residual of budget matching).
Rule outcome: **no meaningful difference** (interval inside ±0.05).

Gate: accepted blocks 7 (467 commits), B10 observed commit miss rate 0.0043
(Wilson upper 0.0129); rejected blocks 12 (914 commits), 0.0274 (upper 0.0377).
Rule outcome: **gate supported**. jade4j's first block could not be fitted
("calibration data needs both failing and passing examples"); the product ran
the full suite there.

## Plain reading

- Calibrated stopping does **not** beat a well-chosen fixed budget at the same
  test time here. The earlier wicket-bootstrap gain does not replicate in
  rolling blocks.
- The gate behaves as intended: where it accepts, misses are rare; where the
  estimates are weak it falls back to the full suite. The cost is that the
  product saves little time outside wicket-bootstrap (about 6% there, 0–2%
  elsewhere). 5 of the 7 accepted blocks come from one project.
- These are previously inspected projects. Confirmation needs new RTPTorrent
  projects with ≥20 failing commits in the later half; rerun the same command
  with their datasets added and a new output folder.

## Limits

Four projects, one deterministic fit per block, commit bootstrap ignores serial
dependence, no multiplicity correction, no end-to-end CI speedup claim.
