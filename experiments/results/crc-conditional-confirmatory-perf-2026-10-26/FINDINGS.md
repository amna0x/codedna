# Findings: crc-conditional-confirmatory-perf-2026-10-26

All nine projects are eligible. Fixed seeds, chronological windows, inputs and model settings are recorded in config.json. Original raw reports and machine verdicts are preserved.

## Interpretation

B12f reaches commit safety >= 0.95 on **8/9 projects**, exceeding the handoff rule of ceil(0.75 x 9) = 7. The stored script still uses >=3; this interpretation applies 7, without rewriting its output.

B12f minus the gated B10 product:

- Recorded test time: -16.20 percentage points (95% interval -16.87 to -15.53).
- Commit safety: -1.79 percentage points (95% interval -2.72 to -0.84).
- Failing-test recall: -1.73 percentage points (95% interval -2.53 to -0.95).

Pooled B12f safety is 95.88%; this weights commits differently from the equal-project differences above. Cloudify safety is 87.84%, below the target. The gate therefore does not establish a universal or per-project guarantee.

The time-saving condition and 7-of-9 count pass, but there is also a measurable safety decrease relative to the gated product. The separately requested nine-project CRC/PTS addendum was not committed before this continuation, and no pre-specified pooled absolute-safety confidence bound was recorded. Describe this as a fixed-method follow-up on the confirmatory datasets, not an unqualified preregistered product-switch decision. Keep B10 default and CRC opt-in (D-067/D-068).

## Per-project evidence

| Project | Method test time | Method safety | Product test time | Product safety |
|---|---:|---:|---:|---:|
| buck | 43.44% | 97.04% | 100.00% | 100.00% |
| cloudify | 68.84% | 87.84% | 100.00% | 100.00% |
| deeplearning4j | 77.89% | 95.12% | 88.39% | 98.54% |
| dspace | 95.89% | 100.00% | 97.63% | 98.31% |
| jetty.project | 82.41% | 98.84% | 100.00% | 100.00% |
| okhttp | 62.72% | 96.22% | 69.10% | 91.18% |
| sling | 77.76% | 96.49% | 91.19% | 97.89% |
| sonarqube | 92.23% | 98.28% | 100.00% | 100.00% |
| titan | 96.05% | 98.11% | 96.72% | 98.11% |

## Provenance and limitations

1 fitting failure(s) are recorded (DSpace calibration lacks both label classes). B12f/B13/B13f use full-suite fallback for that block; the PTS comparison excludes the unfit block. No failure is silently converted to a successful fit.

The optimized risk selector preserves the original formula and selection semantics. Exact tests, the full Maven-inclusive validation, and a complete real-project replay are archived in performance-audit/. B13 reused seven byte-identical original reports and evaluated the remaining two with the optimized implementation; performance-resume-provenance.json distinguishes those code versions. Other folders use the recorded optimized code throughout.

Test-time fractions are historical test-execution cost, not measured CI wall time. Existing bootstrap limitations (serial dependence, no multiplicity correction) remain. CRC assumes exchangeability of failing commits; chronological CI histories need not satisfy it. No model, threshold grid, split, seed, or success rule was retuned after these outcomes.

## Frozen output hashes

```json
{
  "buck.json": "a90b1fa2e5f86d566e531a0c544eff463ace784014ca571be1f3b3cee58eefb2",
  "cloudify.json": "dcc6405a1b6049d4cd476b94ba544723183db47daa0a9617633f109bd3d0c5b4",
  "config.json": "025ac3f112058ea53537d83f1c9267a3d2ff23b5083b91a058da97856d785fe3",
  "deeplearning4j.json": "2cbed831379e1eb183967ab6a20d702b2cc4184b3b5cfd38201f4b14dc7e56d3",
  "dspace.json": "f72e9a89b379b14340aa386360687d657f61de19672c525529a93f7637b4672a",
  "jetty.project.json": "e8609b60c0d51765ccdc51f09634669654f55a786718148774102172df219611",
  "okhttp.json": "adb9c319db04105eaa058788f3d63681a054150d601c277e581d2c4139ec9649",
  "sling.json": "3d06cf81cff96e2bccb8366c779bdbdb046e51ac4df80061a7a4034eb5c79ede",
  "sonarqube.json": "15a588a76ff9ff0cecec3541da8106c5fc615f5a790b309dbb6c5f73c111e8f9",
  "summary.json": "939cb7740d27af65e0a7b0cfc028b15d2451d52ad7c7a5cdd67c707f88beb05c",
  "summary.md": "6bcb5bd2c79bd1ba211a9a1411a1675c7bd5c0471202cee1e6004db383187f25",
  "titan.json": "fc4ce9821e4707e6e5ae5eed6654f5ac0104674e044d1b030a9d066088e2983c"
}
```
