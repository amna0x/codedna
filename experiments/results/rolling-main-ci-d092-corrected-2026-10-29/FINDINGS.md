# D092 corrected engineering replay

See docs/ROLLING_CI_D092_FINDINGS.md for the full method and limitations.

- Fixed genuine Oak trunk cohort: 15 source-verified completed builds.
- Decisions persisted before the current report was loaded.
- Only completed earlier observations became visible to subsequent decisions.
- Eight published reports validate after correcting aggregate child-count handling.
- Seven reports remain unavailable (original 404 responses preserved).
- Seven available reports contain failing classes; no failures were erased.
- All decisions require full suites; zero model fits or selective decisions.
- Corrected replay uses the initial run's exact cached inputs, not fresh data.
- No efficacy, calibrated-risk or measured CI-speedup claim.

The sample is sparse and too small for the intended research study. Source test
universe verification is still required before selective evaluation. Input gzip
snapshots and SHA256s are in input-manifest.json; decompress to recover the exact
original bytes. The initial run remains preserved in its separate result folder.
