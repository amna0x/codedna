# D096: module-history readiness upper bound

Checked all12D095zero-skipped candidate modules against all15retained build
metadata records:180module/build targets. Eight root reports are complete as
published. No failures or runtimes influenced module selection.

Before expensive per-commit discovery, computed an intentionally optimistic bound:
every available root report finishing before a target starts is assumed to contain
a perfect matching, usable module outcome. Unique commits are deduplicated and the
current commit excluded. All hypothetical prior commits are assigned directly to
audit, with one failure and zero misses each; none are reserved for training or
calibration. These are assumptions used to prove an upper bound, NOT observations
or fabricated training rows. Real eligible evidence can only be smaller.

Maximum optimistic prior count is8. Every one of180targets fails both unchanged
safety gates even under those assumptions. Twelve targets have a completed root
report at their BASE under this optimistic screen; that does not establish valid
module history, no skipped tests or eligible live lineage. No models were fitted
and no full historical source-universe work was performed. It cannot overcome
this count limit, so repeating expensive source discovery is deferred.

The upper-bound screen uses the actual B10 validation function, risk target.05,
and the CRC minimum resolution floor1/(n+1) with at least19audit commits. The
real chronological train/calibration/audit split and failure-bearing requirements
would reduce available evidence further. No safety rule was weakened.

Seven offline tests passed in1.69seconds across D095/D096: result-label invariance,
identity mismatch rejection, gate bounds, and exclusion of future, missing,
duplicate and current-commit evidence. Product source is unchanged; its existing
780-test validation is separate. No CI savings, recall or model performance was
estimated by this feasibility check.

Next useful step requires new evidence: a longer complete sequential main-branch
archive with exact execution profiles, or prospective user-project full-suite
history with recorded commits, completion times, test identities and all failures.
The six-hour collector gathers public evidence while running, but cannot restore
expired history or guarantee sufficient failing audits. Do not claim that waiting
a few hours will solve this. Keep full-suite fallback and report the data limit.

Files: scripts/screen_d096_history_readiness.py,
backend/tests/test_d096_history_readiness.py and
experiments/results/module-history-readiness-d096-2026-10-30.json.
