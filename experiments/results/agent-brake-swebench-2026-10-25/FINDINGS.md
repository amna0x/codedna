# Agent brake on public SWE-bench Java patches: findings, 2026-10-26

Protocol: [AGENT_BRAKE_STUDY_PROTOCOL.md](../../../docs/AGENT_BRAKE_STUDY_PROTOCOL.md)
(D-062). Two runs, same data and the same script:

| Run | Folder | CodeDNA commit | Status |
|-----|--------|----------------|--------|
| Primary | `agent-brake-swebench-2026-10-25/` | `dc5339c` | pre-registered result |
| Follow-up | `agent-brake-swebench-2026-10-26-discovery/` | `5aae3f9` | **post hoc**: discovery fixed (D-064) after seeing the primary run |

Data: `SWE-bench/experiments` commit `40f164d5b8f1d249bf95a6df8b74b577fd8e519d`,
manifest SHA-256 `5c4d8c5f…10ee` (in `summary.json`). 42 Java instances ×
14 mini-SWE-agent submissions = 588 pairs: 509 analysed, 62 without a patch,
3 patches `git apply` rejected, 14 pairs of one lombok instance
(lombok-3009) whose base commit is in no log. Same counts in both runs. No
project code was run.

## Short answer

- **Primary run.** The dependency plan (A2) caught **47 of 143** failing
  pairs with a mapped failing test (32.9 %, 95 % Wilson 25.7–40.9 %). The
  full suite (A1) caught exactly the same 47. So the plan lost no catch that
  running everything would have had; every miss was a test **CodeDNA did not
  discover**. Discovery found no tests in Lucene and lombok, and only 1–20 of
  gson's ~100 test classes in older gson versions.
- **Follow-up run (post hoc).** The gaps were standard JUnit 3 tests
  (`TestCase` subclasses, and Lucene's JUnit 3 method provider) and Lucene's
  Gradle test folder `src/test`, set in a shared script. With those read
  (D-064), the plan caught **108 of 149** failing pairs (72.5 %, 65.1–79.0 %),
  again exactly as many as the full suite. All 41 misses are lombok, whose
  Ant build and data-driven tests CodeDNA cannot read. **Without lombok: 108
  of 108 (96.6–100 %).**
- **Size of the plan** depends on where the change is, so per-repository
  medians are the honest summary (follow-up run):

  | Repository | Pairs | Discovered classes (median) | Plan (median) | Plan / suite, median (IQR) |
  |------------|------:|-----:|-----:|------|
  | druid | 67 | 1,890 | 342 | 18.1 % (7.2–29.7 %) |
  | lucene | 123 | 1,544 | 20 | 1.3 % (0.1–99.8 %) |
  | gson | 113 | 112 | 98 | 88.1 % (87.5–88.7 %) |
  | javaparser | 26 | 464 | 350 | 75.4 % (52.0–98.7 %) |

  Lucene is bimodal: a change in a leaf module selects a handful of classes,
  a change in `lucene/core` selects nearly all 1,500. gson is small and
  almost every test uses `Gson` itself. Summed over all analysed pairs
  outside lombok, the plans hold 38.9 % of the test-class runs the full suite
  would make. Only 0.6 % of pairs fell back to retest-all for a non-Java
  change.
- **Reach (RQ-B3).** For resolved pairs outside lombok, the plan contained
  every mapped `FAIL_TO_PASS` class in **221 of 221** (follow-up) and 82 of
  221 (primary; again discovery gaps).

## What the catches mean, and what they do not

- 100 of the 149 failing pairs failed only `FAIL_TO_PASS` tests: the agent
  did not fix the issue, and the failing test is the benchmark's new test
  for the code the agent touched. Catching those is expected from a
  dependency plan. The stronger case is the **49 pairs that broke a test
  that passed before** (`PASS_TO_PASS` failure): the plan caught 33 of the
  33 outside lombok (follow-up), 20 of 33 in the primary run.
- The harness runs only the benchmark's test files, so other regressions
  are unknown, and "caught" means the plan holds a test that showed the patch
  wrong, not that it finds every regression.
- The agents never saw these tests; they stand in for tests the project
  would have had.
- The follow-up result is post hoc. The fix is not tuned to the data (it
  implements how JUnit 3 and Gradle already run tests, and it has its own
  tests), but it was written after seeing which tests were missing, so it
  must be reported as a follow-up and not replace the primary number.
- Per-submission figures in `summary.json` are descriptive only. Models and
  agent versions differ, and with 2–18 failing pairs per submission the
  intervals overlap widely; this is not a model comparison.
- With no validated project history the live brake asks for the full suite
  (D-041), which here catches the same failures. The plan's size column is
  what the brake would ask for once the project's own runs pass the audit
  (D-053), not what it asks for on day one.
- A Wilson lower bound printed as `-0.0` in `summary.json` (lombok) is a
  rounding artefact of 0.

## Files

- `summary.json`, `pairs.csv` in both folders (one row per submission ×
  instance; `a1_caught`, `a2_caught`, `a2_ratio`, `a2_reach`, notes).
- Not committed: downloaded data (`experiments/datasets/swebench-multilingual/`)
  and per-instance checkpoints (`partial/`), which `run` rebuilds.

Reproduce: `python scripts/swebench_brake_study.py fetch --data DIR`, then
`python scripts/swebench_brake_study.py run --data DIR --work WORK --out OUT --jobs 3`
at the commit named above.
