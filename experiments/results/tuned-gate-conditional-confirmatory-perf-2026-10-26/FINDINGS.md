# Findings: tuned-gate-conditional-confirmatory-perf-2026-10-26

All nine projects are eligible. Fixed seeds, chronological windows, inputs and model settings are recorded in config.json. Original raw reports and machine verdicts are preserved.

## Interpretation

**Exploratory**: the design used the already inspected B10 confirmatory gate evidence. Do not relabel it as independently confirmatory.

Stored verdict: `B13f saves time`. B13f minus gated product: recorded time -3.61 percentage points (95% interval -4.14 to -3.08); safety +0.54 percentage points (95% interval -0.25 to +1.42); recall +0.53 percentage points (95% interval -0.26 to +1.53).

Failure-conditional target is reached on 8/9 projects (required 7); Cloudify falls below 0.95 safety. The safety-difference interval includes zero, so do not claim a reliable safety improvement. This is promising follow-up evidence, not grounds to deploy B13f as the default.

## Per-project evidence

| Project | Method test time | Method safety | Product test time | Product safety |
|---|---:|---:|---:|---:|
| buck | 76.52% | 98.82% | 100.00% | 100.00% |
| cloudify | 83.65% | 94.59% | 100.00% | 100.00% |
| deeplearning4j | 80.83% | 97.07% | 88.39% | 98.54% |
| dspace | 100.00% | 100.00% | 97.63% | 98.31% |
| jetty.project | 100.00% | 100.00% | 100.00% | 100.00% |
| okhttp | 74.21% | 98.74% | 69.10% | 91.18% |
| sling | 95.71% | 99.65% | 91.19% | 97.89% |
| sonarqube | 99.63% | 100.00% | 100.00% | 100.00% |
| titan | 100.00% | 100.00% | 96.72% | 98.11% |

## Provenance and limitations

1 fitting failure(s) are recorded (DSpace calibration lacks both label classes). B12f/B13/B13f use full-suite fallback for that block; the PTS comparison excludes the unfit block. No failure is silently converted to a successful fit.

The optimized risk selector preserves the original formula and selection semantics. Exact tests, the full Maven-inclusive validation, and a complete real-project replay are archived in performance-audit/. B13 reused seven byte-identical original reports and evaluated the remaining two with the optimized implementation; performance-resume-provenance.json distinguishes those code versions. Other folders use the recorded optimized code throughout.

Test-time fractions are historical test-execution cost, not measured CI wall time. Existing bootstrap limitations (serial dependence, no multiplicity correction) remain. CRC assumes exchangeability of failing commits; chronological CI histories need not satisfy it. No model, threshold grid, split, seed, or success rule was retuned after these outcomes.

## Frozen output hashes

```json
{
  "buck.json": "9ec76d446151ea4f0cf659391e61651ccc355c72ee5a4f7addecff36145260a0",
  "cloudify.json": "8be59e4159dea6d986d23f547fd6053770451b4332398cf762cf690446f8d130",
  "config.json": "0672e95bfeb91dc22ec809ea5046313d03afbc101efddd3dc03e97aaed2f48d6",
  "deeplearning4j.json": "9c84693cb73d32b826e8488d678fb74d8a3d170d85da6b80509a07c0776a04cc",
  "dspace.json": "f5eb4c3d6ba311e035dd8187e816735ab8881364f0e7473eabd0917a2917e105",
  "jetty.project.json": "956b4dace22cb3ce9b5b93b08417e935eff9b3e29e28b535c711b3d5f5d5722a",
  "okhttp.json": "3043ac77ac015ded4506ec632cd9e1bd6b593ff5abbab96b46466f5139491b55",
  "sling.json": "2b6cb8b6af7e1d6ebf1cd333568827277dfc84b2bdcbee937570bfd34fa6c803",
  "sonarqube.json": "ca52efd0aa988fae55e82240912e628cf642173bd48fd776667e241e40d76a4b",
  "summary.json": "1d38072fcb51ca806d2062f8bac7bb95bf4890fbe734f90f31082bb95db109c1",
  "summary.md": "c58aef7e1499dcef0b564e96c03453b064a46aad3d48576bd3fc91bb5fb7d0a1",
  "titan.json": "466ef73c2155074436d0cb10b8facb5a2a7affac108435e0be34ee9443d71f93"
}
```
