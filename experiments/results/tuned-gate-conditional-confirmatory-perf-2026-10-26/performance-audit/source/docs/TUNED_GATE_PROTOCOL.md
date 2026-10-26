# Tuned-threshold gate protocol — 2026-10-26

Status: fixed and committed before any result of this check was computed.
Changes after the first result need a new dated protocol and output folder;
this file is never edited to fit results. The confirmatory result in
`experiments/results/rolling-evidence-confirmatory-windowsfix-2026-10-26/`
is not changed by anything here.

## Why the gate rejects (diagnosis from the saved confirmatory numbers)

The confirmatory gate accepted 8 of 44 blocks, so the product ran the full
suite on most blocks. The saved per-block audit evidence shows three causes:

1. **B10 misses too often at its fixed 5 % estimate** (buck, deeplearning4j,
   sling, okhttp, titan): the audit miss rate is about 2–12 % and the one-sided
   Wilson bound passes 5 %. The calibrated estimate is too optimistic there,
   so stopping at an estimated 5 % skips more risk than 5 %.
2. **Failure recall below 90 %** (cloudify, sonarqube, dspace): the miss
   rate over all commits is often under 5 %, but B10 misses 13–98 % of the
   failing tests, because most failing tests have little failure history.
3. **Too few audit commits** (jetty.project, 24–44 audit commits; titan's
   first blocks): with zero misses the Wilson bound is about 2.7 / (n + 2.7),
   so fewer than about 52 audit commits can never pass 5 %.

The gate tests one threshold only (λ = 0.05) and gives up when it fails.
Causes 1 and 2 are about that threshold being wrong for the project, not
about the project being unpredictable. Cause 3 needs more history; nothing
here fixes it.

Because this diagnosis used the confirmatory outcomes, every result of this
check is **exploratory**, on the confirmatory nine as well. A confirmatory
test of B13 needs projects nobody has inspected.

## B13: tuned-threshold gate

Everything as in `docs/EVIDENCE_STUDY_PROTOCOL.md` and the D-041 gate
(data, blocks, `selection.live.fit_audited` with `plugins.java_live.LIVE_FEATURES`
fitted on the commits before each block, recent-failures order, audit
window, Wilson bound, at least 10 failing audit commits, at least 90 %
recall, target 0.05) except one change:

- **Threshold search on the audit window.** For each stopping threshold λ
  in the grid 0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05,
  0.1, 0.2, 0.3, 0.5, from the smallest (most tests run) upwards, the
  unchanged D-041 check is applied to the audit outcomes of stopping at
  estimated skip risk λ. The search stops at the first λ that fails. B13 uses
  the largest λ that passed, and the full suite if the smallest fails.
- This is fixed-sequence testing (as in Learn-then-Test, Angelopoulos et al.
  2021): each λ is tested at the same 5 % level only after every stricter one
  passed, so the chance of accepting any λ whose true miss rate is above the
  target stays at the gate's own level. It assumes, as the gate does, that the
  audit commits are representative of the next block.
- A block whose fit fails runs the full suite, as in the rolling study.

B13 can pick a λ above 0.05 where B10 is too cautious, and below 0.05 where
B10 is too optimistic. The gated product is the special case that tests 0.05
only.

## Analyses

Per set (exploratory four; confirmatory nine), never pooled across sets:

- Per project: mean time, commit safety, test recall and commit miss rate
  (over all commits) of B13 and of the gated product; blocks with λ ≠ full;
  chosen λ per block.
- B13 minus product in time, safety and recall, equal project weight, the
  rolling study's hierarchical bootstrap (2000 draws, seed 0).
- Pooled over blocks where B13 did not run the full suite: observed commit
  miss rate and its one-sided 95 % Wilson upper bound (the gate-evidence
  analysis of the evidence study, applied to B13).
- **Rule.** *B13 saves time* if the time interval's upper end is below 0,
  the safety interval's lower end is at or above −0.05, and B13's miss rate
  is at most 0.05 on at least ⌈0.75·k⌉ of the k projects. *B13 costs time* if
  the time interval's lower end is above 0. Otherwise *inconclusive*.

## Pre-registered reruns on the confirmatory nine

`docs/PTS_BASELINE_PROTOCOL.md` (B11) and `docs/CRC_CONDITIONAL_PROTOCOL.md`
(B12f) were both committed before the confirmatory results existed and say
to rerun them on the confirmatory datasets. They are rerun unchanged, with
their scripts, into `pts-check-confirmatory-2026-10-26/` and
`crc-conditional-confirmatory-2026-10-26/`. The B12f rule was written for
four projects ("at least 3 of 4"); for nine it is read proportionally as
at least ⌈0.75·9⌉ = 7 of 9 projects with safety ≥ 0.95. The script's
printed verdict uses "at least 3" and is reported next to the proportional
reading; the proportional reading is the one used in the report.

## Outputs

`experiments/results/tuned-gate-2026-10-26/` (exploratory four) and
`experiments/results/tuned-gate-confirmatory-2026-10-26/` (confirmatory
nine): `config.json` (code and input hashes), one JSON per project,
`summary.json`, `summary.md`, and `FINDINGS.md` written by hand from the
saved numbers only.
