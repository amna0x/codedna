# Findings: tuned-gate-confirmatory-perf-2026-10-26

All nine projects are eligible. Fixed seeds, chronological windows, inputs and model settings are recorded in config.json. Original raw reports and machine verdicts are preserved.

## Interpretation

**Exploratory**: the design used the already inspected B10 confirmatory gate evidence. Do not relabel it as independently confirmatory.

Stored verdict: `inconclusive`. B13 minus gated product: recorded time -23.36 percentage points (95% interval -23.99 to -22.77); safety -4.17 percentage points (95% interval -5.34 to -3.10); recall -3.12 percentage points (95% interval -3.97 to -2.35).

The all-commit miss target is reached on 9/9 projects, but failing-commit safety >=0.95 holds on only 4/9. Those are different denominators. Its safety-loss interval crosses the -5-point non-inferiority margin, yielding the saved inconclusive verdict despite lower test time.

## Per-project evidence

| Project | Method test time | Method safety | Product test time | Product safety |
|---|---:|---:|---:|---:|
| buck | 39.53% | 97.04% | 100.00% | 100.00% |
| cloudify | 55.44% | 87.16% | 100.00% | 100.00% |
| deeplearning4j | 77.34% | 95.61% | 88.39% | 98.54% |
| dspace | 61.27% | 91.53% | 97.63% | 98.31% |
| jetty.project | 100.00% | 100.00% | 100.00% | 100.00% |
| okhttp | 47.66% | 87.82% | 69.10% | 91.18% |
| sling | 73.71% | 94.39% | 91.19% | 97.89% |
| sonarqube | 81.79% | 94.83% | 100.00% | 100.00% |
| titan | 96.05% | 98.11% | 96.72% | 98.11% |

## Provenance and limitations

1 fitting failure(s) are recorded (DSpace calibration lacks both label classes). B12f/B13/B13f use full-suite fallback for that block; the PTS comparison excludes the unfit block. No failure is silently converted to a successful fit.

The optimized risk selector preserves the original formula and selection semantics. Exact tests, the full Maven-inclusive validation, and a complete real-project replay are archived in performance-audit/. B13 reused seven byte-identical original reports and evaluated the remaining two with the optimized implementation; performance-resume-provenance.json distinguishes those code versions. Other folders use the recorded optimized code throughout.

Test-time fractions are historical test-execution cost, not measured CI wall time. Existing bootstrap limitations (serial dependence, no multiplicity correction) remain. CRC assumes exchangeability of failing commits; chronological CI histories need not satisfy it. No model, threshold grid, split, seed, or success rule was retuned after these outcomes.

## Frozen output hashes

```json
{
  "buck.json": "46ddc76197e1499cbeec0d64728acec3bd3a2220af5e142048f01e9fda5445d0",
  "cloudify.json": "38c8b9d7d878ea6bf85755e67ef1ddbb5ac55d3e5277789be9fb8ac9163f55fa",
  "config.json": "31b63c7eff83779f21785f8c99c5639b6bbdf387ebaa6421770826a8300c2b0f",
  "deeplearning4j.json": "e1e4f3b1e9a1fd04c005daca52aad6a21eb1b6ccfeff8be2d1e4f199a253cf2b",
  "dspace.json": "2c1eeccc6e8d2b965abdac339c47a174ad576cbe746cc30ad965b302e7bf9527",
  "jetty.project.json": "614b94b3274e9fe42ef705f9b6192e906745f313b9e43c3fb11298c07b2e1214",
  "okhttp.json": "226931d2b68d99cbd22093bf0eea320ba9db05290fc9944a8d417c24fbdc92af",
  "original-config.json": "00245516991cb2b07ef6abf66baa1e4e70e04408752bef38c0076fafdd9fabbd",
  "performance-resume-provenance.json": "f6525c9680df2f9317f44f468c9ea49680aadc562994315cb58668946b8b07e5",
  "sling.json": "63f1cee00861be57df6efcf83b7da3dc4be081a8259791cac1a63612b60eedc6",
  "sonarqube.json": "11dd370b20945d4a84b298c3a96a0a6b76e2259c13574e65e5eeed9cd42ae0d3",
  "summary.json": "9ea72bf35d9c74bca2492c88743348f98da6e3a6718e41dade112f4e9a4823c9",
  "summary.md": "aae85099b5780d1be67aab98dd4925a9dc7bac8e7d3ca372e8c72b53873382a2",
  "titan.json": "1a8c4ef9fb2c85999969dad3cd53b27ea0466121f81bc3bf8eeee77c68c491d1"
}
```
