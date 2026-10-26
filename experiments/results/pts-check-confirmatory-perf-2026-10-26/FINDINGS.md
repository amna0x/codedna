# Findings: pts-check-confirmatory-perf-2026-10-26

All nine projects are eligible. Fixed seeds, chronological windows, inputs and model settings are recorded in config.json. Original raw reports and machine verdicts are preserved.

## Interpretation

The saved machine verdict is `harms`, but the attempted cost match failed. It is not evidence of a same-time comparison.

B10 minus the attempted matched B11: recorded time -31.10 percentage points (95% interval -32.51 to -29.73); safety -16.13 percentage points (95% interval -19.03 to -13.12); recall -20.40 percentage points (95% interval -22.69 to -18.31).

All nine project-level test-recall cutoffs reached the 0.0001 tuning floor, and residual test-time differences remain substantial. The B11 change-recall constraint still forces a large suite. Report the resource/safety trade-off and residuals rather than calling these policies equally expensive.

At its stated targets, pooled B11 test-time fraction is 84.22%, safety 94.14%, and failing-test recall 95.94%. This adaptation is not an industrial PTS reproduction.

## Per-project evidence

| Project | B10 time | B11 attempted-match time | Residual B10 - B11 | B10 safety | B11 safety |
|---|---:|---:|---:|---:|---:|
| buck | 7.34% | 33.92% | -26.58 pp | 87.57% | 91.12% |
| cloudify | 4.75% | 62.01% | -57.26 pp | 46.62% | 94.59% |
| deeplearning4j | 51.88% | 72.61% | -20.73 pp | 91.71% | 88.78% |
| dspace | 47.36% | 63.90% | -16.54 pp | 9.38% | 59.38% |
| jetty.project | 59.42% | 88.93% | -29.51 pp | 91.86% | 95.35% |
| okhttp | 40.01% | 78.16% | -38.15 pp | 84.87% | 93.28% |
| sling | 59.92% | 61.47% | -1.55 pp | 89.47% | 96.49% |
| sonarqube | 21.10% | 93.30% | -72.20 pp | 58.62% | 95.69% |
| titan | 77.12% | 94.51% | -17.39 pp | 96.23% | 86.79% |

## Provenance and limitations

1 fitting failure(s) are recorded (DSpace calibration lacks both label classes). B12f/B13/B13f use full-suite fallback for that block; the PTS comparison excludes the unfit block. No failure is silently converted to a successful fit.

The optimized risk selector preserves the original formula and selection semantics. Exact tests, the full Maven-inclusive validation, and a complete real-project replay are archived in performance-audit/. B13 reused seven byte-identical original reports and evaluated the remaining two with the optimized implementation; performance-resume-provenance.json distinguishes those code versions. Other folders use the recorded optimized code throughout.

Test-time fractions are historical test-execution cost, not measured CI wall time. Existing bootstrap limitations (serial dependence, no multiplicity correction) remain. CRC assumes exchangeability of failing commits; chronological CI histories need not satisfy it. No model, threshold grid, split, seed, or success rule was retuned after these outcomes.

## Frozen output hashes

```json
{
  "buck.json": "a0e21f1ef9edf29d3a25da11c45800c92144195928ebdba0777c851d6ce4bed4",
  "cloudify.json": "b985d9cca29beb5018a9994bb0d37a1d15417017ab833c3592440dfe9397fb80",
  "config.json": "8ce7697ccccd5f2bf4e93c64997095939d67387d0ecf943054883e6698a5bbc8",
  "deeplearning4j.json": "c1cb472a2a5db808e4d4d63f94a1e81192faa688cef1f79edc61c42eca7f6bd6",
  "dspace.json": "2be27a6506605f6c5af84e2b67e9f78a2acfc4d0abec3933c4d1c370be5c8e61",
  "jetty.project.json": "3c1ccad2c24222a5d17822d667a2b44442545b8d3add2f0d136ba3921f363b2e",
  "okhttp.json": "167220505b753d9f53fd137a92aa0927ada8d4a518cfd1c9b27b21f68e1d12bd",
  "sling.json": "d8fb0d0827e0bee75ce09caab8ba2a1bc2b5a7dceced70fb919c3686617af89d",
  "sonarqube.json": "f3b2f051ba715ada8d8b0159a6c0f8d32042a17af9499b59a3f3a0f40bd4e985",
  "summary.json": "67b6f68a0e27f3692ab1fc8a5b994a9db5e72a6ece3957ddfebf094a899ebca2",
  "summary.md": "7be572a74098f3d2f38820e5f63eb88309d5e6cc02248eb7ff8e4a20afeecc46",
  "titan.json": "3082f7be7332b3cafd101cc027e7eae5ae7866195ac2e9c5ca57c5ee25dbb2e7"
}
```
