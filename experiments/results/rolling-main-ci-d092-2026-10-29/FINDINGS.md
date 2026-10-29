# Initial D092 pilot, preserved

This is the initial engineering run on the pinned 15-build Oak trunk cohort.
Decisions were persisted before report retrieval. Eight report payloads were
downloaded and seven requests returned 404. Observed failures were retained.

Its parser required a top-level pass count that Maven aggregated reports do not
export, so it incorrectly classified the eight downloadable reports as incomplete.
Do not use that classification as a research result. The corrected cached replay
and parser consistency tests are documented separately; no original result was
overwritten or unavailable report replaced. Both runs are engineering evidence,
not independent effectiveness or CI-speedup measurements.
