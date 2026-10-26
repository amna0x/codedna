# Agent brake study on public SWE-bench Java patches — protocol

Fixed on 2026-10-25, before any result was computed. Changes after that date
are listed at the end with their reason. Decision: D-062.

## Question

AI coding agents often stop after a change without running the tests that
would show it is wrong. The CodeDNA brake (D-059) tells an agent which test
classes a change must run. This study asks, **offline and without running any
build**:

- **RQ-B1.** When a public agent patch broke or failed to fix benchmark
  tests, would the brake's plan have contained at least one of the test
  classes that failed?
- **RQ-B2.** How much of the test suite does the plan ask for?
- **RQ-B3.** For patches that did resolve the task, does the plan contain the
  test classes that check the fix?

It does **not** measure whether agents finish with fewer broken changes when
they use the brake. That needs live agent runs and is future work.

## Data

- SWE-bench Multilingual, Java instances only: repositories `google/gson`,
  `apache/druid`, `apache/lucene`, `projectlombok/lombok`,
  `ReactiveX/RxJava` and `javaparser/javaparser` (instance ids with those
  prefixes in each submission's `per_instance_details.json`).
- Submissions: every submission folder under `evaluation/multilingual/` of
  `github.com/SWE-bench/experiments` (14 on 2026-10-25, all mini-SWE-agent with
  different models). The commit of that repository is recorded.
- Per submission and instance: the agent's `patch.diff` and the harness's
  `report.json`, from the public log location named in the submission's
  `metadata.yaml` (a public S3 bucket, or a public GitHub repository).
- Per instance: the harness's `eval.sh` (it holds the benchmark's test patch)
  and the start of `test_output.txt` (it names the base commit), from the
  first submission that has them.
- Every downloaded file is stored with its SHA-256 in a manifest. Downloaded
  data is not committed (`experiments/datasets/swebench-multilingual/`).
- No credentials, no paid API, no project code is executed. `eval.sh` is
  read as text only.

## Repository states

For each instance with base commit `B` and benchmark test patch `P_test`:

- `T` = `B` + `P_test`, committed. These stand for the project's tests.
- For each agent patch `P_agent`: `H` = `B` + `P_agent`, then the files that
  `P_test` touches are restored to `B` and `P_test` is applied, committed.
  This is the state the harness tested.

The change the brake sees is `T..H`: the agent's edits outside the
benchmark's test files. A patch that `git apply` cannot apply is recorded as
`not_applied` and excluded.

## Arms

- **A0 no brake** — the agent runs nothing. It catches nothing by definition.
- **A1 brake default** — with no validated history the brake asks for the
  whole suite (D-041, D-059): every test class CodeDNA discovers that the
  build runs by default.
- **A2 dependency plan** — `select_tests(T, H, "dependency")`: test classes
  that the change reaches through the dependency graph (D-010, D-058),
  changed test classes, and retest-all when a non-Java file changed (the
  default rule). No history and no must-run policy.

## Outcomes

A benchmark test is mapped to its test class:

- `pkg.Cls#method` → `pkg.Cls`;
- `Cls > method` or `Cls` → the single discovered test class with simple name
  `Cls` (at `H`); several or none → `unmapped`;
- `data(pkg.Cls)` (lombok) → `pkg.Cls`.

Unmapped tests are counted and reported, never guessed.

- **Failing pair**: an applied patch with at least one test in
  `FAIL_TO_PASS.failure` or `PASS_TO_PASS.failure` (the harness's own report).
- **RQ-B1 catch**: a failing pair is caught by an arm when at least one
  failing test's class is in the arm's selection. Primary result: catch rate
  of A2 over failing pairs with at least one mapped failing class, with a
  95 % Wilson interval. A1's catch rate is reported too; a miss by A1 is a
  test-discovery gap.
- **RQ-B2 size**: selected classes / discovered classes for A2, over all
  applied pairs: median and interquartile range, and the share of pairs that
  fell back to retest-all because of a non-Java change.
- **RQ-B3 reach**: for resolved pairs, the share where every mapped
  `FAIL_TO_PASS` class is in A2's selection.
- Per repository and per submission figures are descriptive only.

## Exclusions

Pairs with no patch, `patch_is_None`, a patch the harness could not apply,
an infrastructure failure, or a patch `git apply` rejects here. Instances
whose base commit cannot be fetched. All exclusions are counted.

## Known limits (stated in advance)

- The harness runs only the benchmark's test files, so `PASS_TO_PASS` covers
  few classes and other regressions are unknown. A catch means "the plan
  contains a test that showed the patch wrong", not "the plan finds every
  regression".
- The agents never saw the benchmark tests; here they stand in for tests the
  project would have.
- lombok builds with Ant and runs data-driven tests; CodeDNA's discovery reads
  Maven and Gradle layouts only, so lombok may show discovery gaps. It stays
  in the study and is reported separately.
- Static analysis only: reflection, resources and generated code are not
  followed.
- One run per instance per model (as published). Models and agent versions
  differ between submissions; this is not a model comparison.

## Changes after fixing the protocol

- 2026-10-25, after smoke runs on three instances (gson-2311, gson-1014,
  javaparser-4538) and before the full run: for 11 instances the S3
  harness logs do not name the base commit (the test patch only adds files).
  For those, the base commit is read from the `git diff <base>` line in the
  test output of the submission whose logs are on GitHub. This changes the
  data source only, not the design. An instance still without a base commit
  is excluded as planned.
- 2026-10-25, same time: the first run stopped on a CodeDNA bug (a recursion
  limit on deeply nested Java expressions). It was fixed in the parser with a
  regression test, and the run was restarted from scratch. Parse reuse
  between the pairs of one instance and parallel workers were added for speed;
  a test checks that results are the same with and without reuse.
- 2026-10-25, during the second full run (35 of 42 instances done, no summary
  computed): a code review found two name-resolution cases in D-058 and
  verdict gaps in D-059. They were fixed, everything was committed, and the
  run was restarted from scratch on that commit, which `summary.json`
  records (`codedna_commit`).
