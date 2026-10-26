# Failure-conditional conformal stopping protocol — 2026-10-26

Status: fixed and committed before any result of this check was computed.
It follows `docs/CRC_STOP_PROTOCOL.md`, whose run
(`experiments/results/crc-check-2026-10-26/FINDINGS.md`) showed that a 5 %
miss rate over *all* commits lets about half of HikariCP's failing commits
be missed. This is a new question with its own output folder, not a re-tune
of that result.

## Question

Can the stopping threshold instead bound the miss rate **among commits that
actually fail** (one minus commit safety) at 5 %, and what does that cost in
test time compared with the gated product?

## Method (B12f)

Everything as in `docs/CRC_STOP_PROTOCOL.md` (data, blocks, fitting, order,
grid, loss, corrected bound, α = 0.05) except one change: the threshold is
tuned on the **failing audit commits only**. This is label-conditional
conformal risk control: if failing audit commits and failing future commits
are exchangeable, the expected miss rate over failing future commits is at
most α. Selection never needs to know whether the new commit fails. With
fewer than 19 failing audit commits only the full suite qualifies.

## Analyses

- Per project and pooled: B12f commit safety against 0.95, and its miss rate
  over all commits; count projects with safety ≥ 0.95.
- B12f minus the gated product in time, safety and recall, equal project
  weight, the same bootstrap. Rule: *B12f saves time* if the time interval's
  upper end is below 0 and safety ≥ 0.95 on at least 3 of 4 projects;
  *B12f costs time* if the lower end is above 0; otherwise *inconclusive*.

## Outputs

`experiments/results/crc-conditional-2026-10-26/`, same files as the
previous check, plus `FINDINGS.md` written by hand from the saved numbers.
