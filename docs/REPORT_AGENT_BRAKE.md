# CodeDNA as a test brake for AI coding agents (report chapter draft)

Draft chapter for the FYP report, next to the evaluation chapter
([REPORT_DRAFT.md](REPORT_DRAFT.md)) and the system chapters
([REPORT_SYSTEM_DRAFT.md](REPORT_SYSTEM_DRAFT.md)). Design: D-059; study
protocol: [AGENT_BRAKE_STUDY_PROTOCOL.md](AGENT_BRAKE_STUDY_PROTOCOL.md)
(D-062); discovery fix: D-064. Every number below comes from
`experiments/results/agent-brake-swebench-2026-10-25/` (primary run) or
`experiments/results/agent-brake-swebench-2026-10-26-discovery/` (follow-up
run); the findings file there lists both. Status: draft, 2026-10-26.

## 1. Motivation

AI coding agents can edit source code and invoke developer tools. A common failure
is that the agent edits code, runs no tests or the wrong ones, and reports
the task done. The question CodeDNA answers for a person (which tests does
this change need, and what is the risk of skipping the rest) is the same
question an agent should ask before it stops. The brake makes CodeDNA's
answer available to any agent that speaks the Model Context Protocol (MCP),
the standard way agents such as Claude Code, Cursor and Codex call tools.

## 2. Design

`codedna mcp` is an MCP server on stdin/stdout. It is part of the core and
uses the installed language plugin, so it works for any language CodeDNA
supports (Java first). It has three tools:

| Tool | Runs project code | Returns |
|------|-------------------|---------|
| `codedna_plan_tests` | no | test classes the change must run, a reason for each, the skip risk |
| `codedna_impact` | no | code the change can reach: confirmed and heuristic links apart, files not analysed |
| `codedna_check` | yes (the build) | one verdict: `passed`, `blocked`, `incomplete`, `nothing_to_run`, `no_tests` |

Three rules from the rest of the project carry over unchanged:

- **Honest risk.** Without validated project history the plan is the whole
  suite (D-041). A smaller plan appears only after the project's own
  recorded runs pass the audit (D-053). The brake never claims a skip is
  safe on evidence it does not have.
- **Consent for builds.** `codedna_check` runs the project's build, which
  runs project code. It is offered only when the person starts the server
  with `--allow-build`, and it then serves that one repository (D-014,
  D-059). An agent cannot turn it on.
- **Clear verdicts.** `blocked` means a planned test failed. `incomplete`
  covers every case where the evidence is missing: tests that did not run,
  a build error or timeout, or every planned class skipped. `passed` means
  the listed tests passed, not that the change is correct.

The protocol layer is about 240 lines of plain Python (newline-delimited
JSON-RPC 2.0, with only the methods tools need), so the core gains no
dependency. A setup guide for three agents is in
[AGENT_BRAKE.md](AGENT_BRAKE.md), and `scripts/demo_agent_brake.py` shows a
full session: an agent-style wrong edit in the sample project, then plan,
impact and check over real MCP, ending in `blocked` with real Maven.

## 3. Evaluation question

The study asks, offline and without running any build, whether the brake
would have stopped real agent patches that were wrong:

- **RQ-B1.** When a public agent patch broke or failed to fix benchmark
  tests, would the plan have contained at least one failing test class?
- **RQ-B2.** How much of the suite does the plan ask for?
- **RQ-B3.** For patches that resolved the task, does the plan contain the
  tests that check the fix?

It does **not** measure whether agents finish with fewer broken changes
when they use the brake. That needs live agent runs, which are out of this
project's budget, and is future work.

## 4. Method

**Data.** SWE-bench Multilingual has 42 Java tasks from six projects (gson,
druid, lucene, lombok, RxJava, javaparser). The public
`SWE-bench/experiments` repository holds 14 submissions for it, all
mini-SWE-agent with different models. For each submission and task we
download the agent's patch and the harness report; for each task, the
harness script that holds the benchmark's test patch. All files are stored
with their SHA-256; the data is not committed.

**States.** For a task with base commit `B` and benchmark test patch `P`,
`T` is `B` with `P` applied, and `H` is `B` with the agent's patch, the files
`P` touches reset, and `P` applied, which is exactly what the harness
tested. The brake sees the change `T → H`: the agent's own edits.

**Arms.** A0: no brake (nothing runs, nothing is caught). A1: the brake's
default without history, the full discovered suite. A2: CodeDNA's
dependency selection for the change (D-010, D-058), with no history.

**Outcomes.** A failing pair is an applied patch with any failing benchmark
test in the harness report. It is caught by an arm when a failing test's
class is in the arm's selection. Benchmark test names are mapped to classes
by fixed rules; names that do not map are counted, never guessed. Catch
rates have 95 % Wilson intervals. The protocol was fixed before any result,
and every later change is logged in it with its reason.

## 5. Results

### 5.1 Primary run (pre-registered)

Of 588 pairs, 509 were analysed (62 had no patch, 3 did not apply, 14 belong
to one task without a known base commit).

- **RQ-B1.** A2 caught **47 of 143** failing pairs (32.9 %, 95 % CI
  25.7–40.9 %). A1, the full suite, caught **the same 47**.
- The plan therefore lost no catch the full suite had. Every miss came from
  tests CodeDNA did not discover: none in Lucene or lombok, and only 1 to 20
  test classes in gson versions whose tests are JUnit 3 style.

### 5.2 Follow-up run with fixed discovery (post hoc)

The primary run showed two gaps in discovery, both standard behaviour that
CodeDNA did not model: JUnit 3 tests (`public void test*()` methods in
`junit.framework.TestCase` subclasses, which Surefire runs, and Lucene's
randomizedtesting JUnit 3 provider), and Gradle test folders moved with
`test.java.srcDirs`, which Lucene sets for every module in a shared script.
Both were added with tests (D-064), and the study was run again with nothing
else changed.

| | Primary | Follow-up (post hoc) |
|---|---|---|
| Failing pairs with a mapped failing test | 143 | 149 |
| Caught by A2 (plan) | 47 (32.9 %, 25.7–40.9) | 108 (72.5 %, 65.1–79.0) |
| Caught by A1 (full suite) | 47 | 108 |
| Caught by A2, without lombok | 47 of 102 | **108 of 108 (96.6–100)** |
| Resolved pairs whose plan has every fix test, without lombok | 82 of 221 | 221 of 221 |

All 41 remaining misses are lombok, which builds with Ant and runs
data-driven tests that CodeDNA's discovery (Maven and Gradle layouts) cannot
see. This limit was stated in the protocol before the run.

**What kind of failures.** 100 failing pairs failed only the benchmark's new
tests: the agent did not fix the issue, and those tests target the code it
touched, so a dependency plan should contain them. The harder case is the
49 pairs that broke a test which passed before. Outside lombok, the plan
contained a failing test for **33 of 33** of them (follow-up) and 20 of 33
(primary).

### 5.3 Size of the plan (RQ-B2, follow-up run)

| Repository | Pairs | Discovered classes (median) | Plan (median) | Plan / suite, median (IQR) |
|------------|------:|-----:|-----:|------|
| druid | 67 | 1,890 | 342 | 18.1 % (7.2–29.7 %) |
| lucene | 123 | 1,544 | 20 | 1.3 % (0.1–99.8 %) |
| gson | 113 | 112 | 98 | 88.1 % (87.5–88.7 %) |
| javaparser | 26 | 464 | 350 | 75.4 % (52.0–98.7 %) |

Plan size follows the structure of the project. In Lucene a change to a
leaf module needs a few classes and a change to `lucene/core` needs almost
all of them. In gson nearly every test goes through the `Gson` class, so
the plan is most of a small suite. Over all analysed pairs outside lombok,
the plans hold 38.9 % of the test-class runs of the full suite; 0.6 % of
pairs fell back to retest-all because a non-Java file changed.

## 6. Discussion

The study supports a narrow claim well. On these public patches, CodeDNA's
dependency plan never dropped a failing test that the full suite would have
run (47 of 47 primary, 108 of 108 follow-up), while asking for a fraction
of the suite in the two large projects. For an agent this means the brake
can ask for a short, explained test list without losing the catches that
"run everything" gives, once discovery sees the project's tests.

The study also shows that **discovery is the weak link**, not selection.
In the primary run the brake would have answered `no_tests` for Lucene and
lombok, which is honest but stops nothing. The fix for JUnit 3 and Gradle
folders is general, and lombok shows what is still missing (Ant and
data-driven tests).

The live brake asks for the full suite until the project's own history
passes the audit (D-041, D-053). The plan sizes above describe what it can
ask for after that, not on the first day.

## 7. Threats to validity

- **Post hoc fix.** The follow-up run uses discovery changes written after
  seeing the primary run. They implement how JUnit 3 and Gradle already run
  tests and have their own tests, but the follow-up must be read as a
  follow-up; the primary number is the pre-registered result.
- **Benchmark tests only.** The harness runs only the benchmark's test
  files, so other regressions are unknown. A catch means the plan holds a
  test that showed the patch wrong, not that it finds every regression.
- **Stand-in tests.** The agents never saw the benchmark tests; they stand
  in for tests the project would have had.
- **One agent scaffold.** All submissions are mini-SWE-agent; models and
  versions differ, so per-model numbers are descriptive and not a model
  comparison.
- **Small and uneven.** 42 tasks from six projects; druid and lucene
  dominate the size results and lombok all the misses.
- **Static analysis.** Reflection, resources and generated code are not
  followed (D-058). No miss here was caused by that, but the study does not
  rule it out elsewhere.
- **No live effect.** Whether agents end with fewer broken changes when they
  use the brake is not measured.

## 8. Future work

- A live study: the same agents on the same tasks with and without the
  brake, measuring broken changes reported as done.
- Discovery for Ant builds and data-driven tests (lombok), and Gradle source
  sets declared in nested blocks.
- The same study for the implemented Python plugin, through the shared core.
  Python/mixed execution already works with conservative full-suite fallback;
  a Python risk model and agent-effectiveness claim remain unvalidated.


## Current product verification (D-068/D-070/D-071)

The live brake supports CRC as an opt-in method and returns the measured
structural dependency plan separately. Required tests include both structural
and statistical selections plus policy pins, all on the same immutable
revision. Python/mixed projects explicitly run the full suite without a guessed
risk score. A skipped required class/module leaves the verdict incomplete;
complete failing tests still block even when the build exits nonzero.

The real Maven demo exercises blocked and passed outcomes. The refreshed
frozen-core smoke also exercises actual passing and failing pytest runs through
MCP. These are integration tests, not a new empirical study of agent quality.
