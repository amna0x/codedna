# Conformal risk control stopping protocol — 2026-10-26

Status: fixed and committed before any result of this check was computed.
Changes after the first result need a new dated protocol and output folder;
this file is never edited to fit results.

## Question

B10 stops at a fixed 5 % *estimated* skip risk, which assumes independent
test failures and a correct probability level. The D-041 gate then accepts
or rejects B10 per project with a Wilson bound. Conformal risk control (CRC;
Angelopoulos, Bates, Fisch, Lei and Schuster, ICLR 2024) instead picks the
stopping threshold from held-out outcomes so that the expected loss is at
most α, assuming only that held-out and new commits are exchangeable.

1. Does B12 (CRC-tuned stopping) keep the 5 % commit-miss target out of
   sample more often than B10?
2. Does B12 save more test time than the gated product (B10 where the D-041
   gate accepts, full suite elsewhere), at a comparable miss rate?

Commits are ordered in time, so exchangeability does not strictly hold.
Whether the guarantee survives that is part of what is measured.

Prior art found before this check: an open-source project applies CRC to
the *share of missed failing tests* on the industrial Westermo dataset
(github.com/l-k-1-2/Predictive-test-selection). This check uses a stricter,
commit-level loss on open Java CI history.

## Data and design

The rolling-origin design of `docs/EVIDENCE_STUDY_PROTOCOL.md`, unchanged:
the same four datasets (SHA-256 recorded), the last 50 % of commits in 5
blocks, and for each block the unchanged `selection.live.fit_audited` with
`plugins.java_live.LIVE_FEATURES` fitted on the commits before the block.
Exploratory only (previously inspected projects); the script is rerun on
the confirmatory datasets into a new folder when they exist. The scripts
frozen by the running confirmatory job are not edited.

## B12

- **Order:** recent failures first (as B10).
- **Stop:** add tests until the calibrated estimated skip risk is at most
  λ (B10 is λ = 0.05). λ = "full" runs every test.
- **Grid:** full, 0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02,
  0.05, 0.1, 0.2, 0.3, 0.5.
- **Loss** of a commit at λ: 1 if any failing test is skipped, else 0. It
  can only fall as λ falls, because the selection is a growing prefix.
- **Tuning, on the audit window of `fit_audited` only** (the last 25 % of
  history before the block; not used to fit the model or the calibrator):
  with n audit commits and empirical loss R̂(λ), choose the largest λ in the
  grid with (n·R̂(λ) + 1) / (n + 1) ≤ α, α = 0.05. If no λ qualifies, use
  full. With fewer than 19 audit commits only full can qualify.
- No other gate. A block whose fit fails runs the full suite, as in the
  rolling study, and is counted.

## Analyses

- **Question 1.** Per project and pooled over commits: observed commit miss
  rate of B12 and of B10 against 0.05. Count projects on which each keeps it.
- **Question 2.** Per project: mean time and miss rate of B12 and of the
  gated product. B12 minus product in time, pooled with equal project weight
  by the rolling study's hierarchical bootstrap (2000 draws, seed 0). Rule:
  *B12 saves time* if the time interval's upper end is below 0 and B12 keeps
  the miss target on at least 3 of 4 projects; *B12 costs time* if the lower
  end is above 0; otherwise *inconclusive*.
- Also reported: the chosen λ per block.

## Outputs

`experiments/results/crc-check-2026-10-26/`: `config.json` (code and input
hashes), one JSON per project, `summary.json`, `summary.md`, and
`FINDINGS.md` written by hand from the saved numbers only.
