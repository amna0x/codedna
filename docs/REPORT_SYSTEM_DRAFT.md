# CodeDNA: system chapters (draft)

Draft of the report chapters other than the evaluation (which is in
[REPORT_DRAFT.md](REPORT_DRAFT.md)): introduction, background, requirements,
design, implementation, testing, limitations and future work. Every claim
points to a decision record (`D-0xx` in [DECISIONS.md](DECISIONS.md)), a
source file or a saved result. Status: first full draft, 2026-10-25. Numbers
not yet measured are marked *to be filled*, never estimated.

## 1. Introduction

### 1.1 Problem

Continuous integration runs the regression suite on every change. On large
projects the full suite takes long enough that developers wait, batch their
changes or skip tests. Running only some tests is faster, but a skipped test
may be exactly the one that would have failed. Developers therefore need two
answers for each change: *which* tests the change is likely to affect, and
*how risky* it is to skip the others.

Most existing work answers the first question: it ranks or selects tests from
dependencies, coverage or failure history. Fewer tools give a stated,
checked risk for the tests they leave out, and fewer still refuse to skip
tests when that risk cannot be checked on the project at hand.

### 1.2 Aim

CodeDNA analyses Java code changes in a Git repository, explains their
impact through a labelled dependency graph, selects regression tests, and
estimates the probability that a skipped test would have failed. When that
estimate has not been validated on the project's own history, CodeDNA says so
and recommends the full suite.

### 1.3 Objectives

1. Extract changed files, declarations and line ranges between two commits
   without running project code (D-003, D-008, D-009).
2. Build a type-level dependency graph whose edges are labelled
   confirmed / heuristic, with unresolved names recorded rather than guessed
   (D-010).
3. Compute the change impact with explanation paths and candidate tests
   (D-012).
4. Map tests to code by dependency and by per-test coverage, and compare
   selection strategies against real outcomes (D-014 to D-016).
5. Learn failure probabilities from the project's test history without
   leakage from future commits, calibrate them and turn them into a stopping
   rule with an omitted-failure risk target (D-023, D-025 to D-027, D-036).
6. Evaluate the approach against established baselines at equal test time on
   real CI data (RTPTorrent), and report where it fails
   ([REPORT_DRAFT.md](REPORT_DRAFT.md)).
7. Deliver it as a usable platform: a CLI, a loopback API, the CodeDNA IDE
   built on Eclipse Theia, and a plugin interface for further languages
   (D-017 to D-020).

### 1.4 Contribution and its limits

Changed-file detection, dependency graphs, affected-test selection, learned
prioritisation and history-based ranking are established techniques, and
CodeDNA does not claim novelty for them. The contribution this project
evaluates is narrower:

- a calibrated stopping rule (a target for the probability that a skipped
  test fails) applied on top of a simple history ordering (policy B10,
  D-036), evaluated against the alternatives at matched test time;
- a target-project validation gate (D-041) that recommends the full suite
  whenever the project's own recent history does not support the risk
  estimate;
- an implementation that keeps every unverified relationship and every
  missing outcome visible to the user instead of hiding it.

Section 4 of the evaluation chapter reports that B10 is at least as safe as
the rules at the same test time on the nine projects where safety is defined
(two projects have no failing test commits), but that its pooled advantage is
not statistically clear, and that models trained on one project do not
reliably transfer to another (D-039).

### 1.5 Report structure

Chapter 2 places CodeDNA among related work. Chapter 3 lists the
requirements. Chapter 4 describes the design and chapter 5 the
implementation. Chapter 6 explains how the software was tested. The
evaluation chapter follows ([REPORT_DRAFT.md](REPORT_DRAFT.md)), and chapter 7
closes with limitations and future work.

## 2. Background and related work

### 2.1 Regression test selection and prioritisation

Regression test selection (RTS) runs a subset of tests that may be affected
by a change; test case prioritisation (TCP) orders tests so failures are
found early. Static RTS follows dependencies from changed code to tests;
dynamic RTS uses coverage collected on an earlier run. CodeDNA implements
both as baselines: `dependency` selection from the graph and `coverage`
selection from per-test JaCoCo maps (D-015, D-016).

### 2.2 History-based and learned approaches

History-based methods rank tests by recent failures, failure rate or time
since the last failure. Learned methods combine such features with change
and code features in a classifier. CodeDNA's study models use 19 features in
four groups (change, test, structural, history; [REPORT_DRAFT.md](REPORT_DRAFT.md)
section 2.2) and are compared against random, shortest-first and
history orderings (B1, B2, B3, B5).

### 2.3 Recent work closest to CodeDNA

A focused comparison is kept in
[RELATED_WORK_COMPARISON.md](RELATED_WORK_COMPARISON.md). In summary:

- **DANTE** (ICST 2026) is a training-free history and commit-aware method
  and the strongest baseline found. CodeDNA evaluates an independently
  implemented, history-only adaptation (DANTE-H, D-040); it is not a
  reproduction of the full published method.
- **MOX** (Electronics 2026) optimises cost, impact, coverage and
  traceability on a Pareto front; its impact score is not a calibrated
  probability.
- **Context-Aware Sequential Ranking** (Mathematics 2026) uses the same
  RTPTorrent data, conformal candidate sets and sequential stopping on a cost
  budget. Its stopping rule must be compared in detail before any difference
  from CodeDNA's omitted-failure risk target is claimed.
- **AutoTCP** (Empirical Software Engineering 2026) composes and tunes
  prioritisation workflows automatically; it ranks tests and does not, as far
  as checked, give an aggregate skip risk.

The open space CodeDNA occupies is therefore a calibrated stopping rule with
a per-project validation gate, evaluated honestly against simple rules. The
report never claims to be the first to do this.

### 2.4 Calibration

A predicted probability is calibrated when, among tests given probability p,
a fraction p actually fail. CodeDNA fits Platt scaling or isotonic regression
on a held-out window and reports Brier score, expected calibration error and
reliability bins (D-025). The evaluation shows that much of the
calibration gain only undoes balanced class weighting
(D-037; [REPORT_DRAFT.md](REPORT_DRAFT.md) section 4.3).

## 3. Requirements

### 3.1 Functional requirements

| ID | Requirement | Where |
|---|---|---|
| F1 | Report changed files, statuses, renames and line ranges between two revisions, including uncommitted changes (`WORKTREE`) | `git_analysis`, D-046 |
| F2 | Map changed lines to Java declarations; mark comment-only changes; record unmapped lines with a reason | `java_analysis`, D-008, D-009 |
| F3 | Build a dependency graph with confirmed / heuristic edges, evidence and unresolved names | `dependency_graph`, D-010 |
| F4 | Compute impacted types with distance, confidence and explanation path | `impact_analysis`, D-012 |
| F5 | Discover JUnit 4/5 test classes the build runs by default, for single and multi-module Maven and Gradle projects | `test_mapping`, D-045, D-052 |
| F6 | Select tests by strategy (all, dependency, coverage, risk) and compare strategies against real outcomes | `selection`, D-016 |
| F7 | Never skip tests the project marks as must-run | `selection/policy.py`, D-050 |
| F8 | Store commit history and test outcomes; build leakage-free feature rows | `test_history`, D-021 to D-023 |
| F9 | Train, calibrate and evaluate failure models; run the study policies B0 to B10 | `models`, `calibration`, D-022, D-025 to D-027, D-034 to D-037 |
| F10 | Give a live risk recommendation only after a target-project audit, otherwise the full suite | `selection/live.py`, `plugins/java_live.py`, D-041 |
| F11 | Run the selected tests only after explicit consent, and keep complete runs as project history | `test_mapping/maven.py`, D-014, D-053 |
| F12 | Show changes, impact graph, tests to run with risk, and history replay in an IDE | `ide/`, D-019, D-043, D-049, D-051 |
| F13 | Accept further languages as plugins behind a fixed interface | `plugins/`, D-018, D-024 |

### 3.2 Non-functional requirements

- **Honesty of output.** No invented dependency, outcome or number; unknown
  results are recorded as unknown (AGENTS.md; D-010, D-041).
- **Safety of analysis.** Analysis never executes code from the analysed
  repository. Git is called with argument lists only, with settings that stop
  repository-local helpers from running. Tests run only with an explicit
  `--allow-build` or IDE confirmation (D-014).
- **Reproducibility.** Fixed seeds, chronological splits, recorded dataset
  hashes and package versions in every experiment report (D-027, D-038).
- **Laptop scale.** Runs on an ordinary Windows, macOS or Linux laptop; no
  GPU, cluster or service.
- **Local only.** The API listens on 127.0.0.1 with a per-session token; there
  are no accounts (D-028).
- **Testability.** Every feature has offline tests on temporary Git
  repositories.

### 3.3 Out of scope

Vulnerability detection and security scoring, an LLM as the predictor,
hosted multi-user services, a custom editor written from scratch, and
installing plugins from anywhere but the official catalogue
([PROJECT_SPEC.md](PROJECT_SPEC.md), "Non-goals"). Security checks are planned
as future work through the policy hook (section 7.2).

## 4. Design

### 4.1 Pipeline

CodeDNA is a pipeline in which each stage consumes the previous stage's JSON
([ARCHITECTURE.md](ARCHITECTURE.md)):

```
Git change extractor → Java declaration mapper → dependency graph →
change impact → candidate tests → history features → failure model →
calibration → risk-aware selection (or full suite) → execution → explanation
```

The IDE and the website only display this JSON. No analysis logic exists in
TypeScript, so the same result is available from the CLI, the API and the
IDE.

### 4.2 Platform structure (D-017, D-018)

- **Core** (Python): Git access, graph schema, impact, selection, history,
  models, calibration, policy, API.
- **Language plugins**: language-specific parsing, test discovery, test
  execution and live features sit behind the `LanguagePlugin` protocol with a
  versioned API (`PLUGIN_API_VERSION`). Java is built in; other plugins are
  found through the `codedna.languages` entry-point group. A plugin with the
  wrong API version or a broken import is skipped and reported, not loaded
  half-way (D-024).
- **IDE**: a Theia application with a CodeDNA extension that talks to the
  local API (D-019).
- **Website and catalogue**: static pages and a catalogue index that pins
  plugin versions and SHA-256 checksums (D-020, D-047).

### 4.3 Graph model and confidence labels (D-010)

Nodes are packages, files, types and members. Edges are `contains`,
`extends`, `implements`, `uses`, `imports` and `static_access`, each with a
confidence:

- **confirmed** when the name resolves unambiguously (same package, explicit
  import, nested type);
- **heuristic** when resolution depends on an assumption, such as a wildcard
  import or a capitalised receiver read as a type;
- names that cannot be resolved become **unresolved** entries with a reason
  and never become edges.

Impact follows edges backwards from changed types; an impacted type is
confirmed only if every edge on its path is. This keeps the explanation
honest: the user sees which links CodeDNA is sure about.

### 4.4 Learning and risk design

Rows are (commit, test class) pairs. Features of a commit use only outcomes
of earlier commits (D-023). The study uses a fixed chronological split; the
live predictor uses 15 features available for a new change and a separate
50/25/25 fit / calibrate / audit split of the project's own history (D-041).

The skip risk of a selection is the probability that at least one skipped
test fails, computed from calibrated per-test probabilities as
`1 − Π(1 − p)`, which assumes independent failures (D-026). B10
orders tests by a simple history rule and stops adding tests once that risk
falls below the target (D-036).

The live gate accepts a recommendation only if the audit window shows a
one-sided 95 % Wilson upper bound on the miss rate at or below the target, at
least ten failure-bearing audit commits and at least 90 % failure recall
(`selection/validation.py`). It also checks that the history belongs to the
target branch, is chronological, ends at BASE, covers every current test
class and excludes the requested change. Any failed check gives the full
suite and a reason.

### 4.5 Must-run policy (D-050)

`.codedna/policy.toml` lists tests that may never be skipped. It is read
from the BASE commit, so a change cannot weaken its own checks. A malformed
policy or a failing add-on rule pins every test (fail-safe). Add-on rules
plug in through the `codedna.policies` entry-point group, which is the
intended hook for later security checks. Research comparisons ignore the
policy so study numbers are unaffected.

### 4.6 Building history while in use (D-053)

Because the gate needs complete outcomes and public CI records are
incomplete (D-052), every run of the whole suite that CodeDNA starts is kept
as project history. Only complete runs at commits on the current branch are
recorded, and a history file CodeDNA did not write is never overwritten. The
gate itself is not loosened.

### 4.7 Security of the local tool

The tool analyses untrusted repositories, so its design limits what a
repository can make it do (this is engineering hygiene, not a security
feature of the product):

- Git runs without a shell, with external diff and text-conversion drivers
  disabled and `core.fsmonitor=false`.
- Working-tree snapshots refuse repositories that use filter drivers such as
  Git LFS, because `git add` would run the driver.
- The runner exports a commit with `git archive` into a separate folder and
  runs the build only after consent.
- The API checks a token and the `Host` header and listens only on loopback.

## 5. Implementation

### 5.1 Technology choices

| Part | Choice | Reason |
|---|---|---|
| Core language | Python 3.11+ | Data and ML libraries; quick to test (D-001) |
| Java parsing | Tree-sitter Java | Error-tolerant, no JDK needed, exact line extents (D-008, D-033) |
| Storage | SQLite | One file per project, no server (D-021) |
| Models | scikit-learn logistic regression and gradient boosting | Standard, laptop-friendly (D-022) |
| API | FastAPI on 127.0.0.1 | Typed requests, same JSON as the CLI (D-028) |
| IDE | Eclipse Theia + TypeScript extension, Cytoscape graph | Full editor without writing one (D-019, D-029, D-043) |
| Packaging | Electron app with an NSIS installer for Windows | Ordinary desktop install (D-044) |

### 5.2 Core modules

- `git_analysis`: safe Git calls, change extraction, blob readers,
  working-tree snapshots (D-046).
- `java_analysis`: Tree-sitter parse and line-to-declaration mapping.
- `dependency_graph`: one `git cat-file --batch` read per commit, parse cache
  by blob SHA, reference resolution with evidence.
- `impact_analysis`: merged BASE/HEAD graph, reverse BFS, explanation graph
  with package grouping and summary counts (D-051).
- `test_mapping`: build layout detection (Maven reactor, Gradle,
  `testSourceDirectory`, build-helper test folders, Surefire includes),
  test discovery, opt-in runner, JaCoCo per-test coverage.
- `selection`: strategies, comparison, risk decision, policy, live gate.
- `test_history`, `models`, `calibration`: history store, dataset builder,
  rankers, experiment runner, calibrators and metrics; `recording.py` keeps
  full-suite runs (D-053).
- `api`: FastAPI endpoints mirroring the CLI, with build permission needed
  both at server start and per request.

### 5.3 CodeDNA IDE

The extension adds these views to Theia:

- **Changes**: changed files and declarations for "my last commit", a chosen
  range or uncommitted changes.
- **Impact graph**: one lane per package, columns by distance from the
  change, changed code outlined, controls for depth and confirmed links only
  (D-051). The layout was checked by rendering real HikariCP graphs in
  headless Chromium; Cytoscape's force layout with package boxes overlapped
  and was rejected.
- **Tests to run**: the recommendation with risk status, audit evidence and
  reasons for each test; a confirmed run of the selected tests with real
  statuses and logs; whether the run was kept as history (D-041, D-053).
- **History replay**: the study's test commits played back one by one,
  CodeDNA against run-everything, dependency selection and simple rules,
  with running totals checked against the saved reports (D-049).
- Java editing support and progress notifications (D-044).

### 5.4 Real-project demonstration (D-052)

`scripts/make_hikaricp_demo.py` builds a HikariCP working copy at a real
tested change (dd7c9a9a) with the project's recorded history up to BASE, and
writes CodeDNA's answers next to the real CI outcome from RTPTorrent. On
that change 17 of 21 test classes failed in CI; dependency selection picked
19 of 21 classes and caught all 17 in 24 % of the CI test time. The risk view
honestly stays unvalidated on this history (section 4.8 of the evaluation).
The commit was picked for the demonstration and is not evidence.

## 6. Testing and verification

### 6.1 Automated tests

The pytest suite builds temporary Git repositories for every scenario; the
default run needs no network. The Maven integration tests (`--run-maven`)
also need a JDK, Maven and network access while Maven downloads its plugins
and JUnit. Areas covered include renames, CRLF files, syntax errors,
binary files, multi-module and Gradle layouts, graph resolution and labels,
impact paths, selection strategies, history leakage, calibration, the live
gate's refusal cases, the must-run policy, recording, the API's token and
`Host` checks, and the IDE start script on Windows.

A fake `mvn` script (`backend/tests/fake_mvn.py`) writes Surefire and JaCoCo
files so runner logic is tested without Java. One integration test runs the
real Maven build of `examples/sample-java-project` with JaCoCo; the project
rule is that it must not be silently skipped (`--run-maven`).

Latest full local run (2026-10-25, Linux, Python 3.13, Maven included):
`python -m pytest --run-maven` → 325 passed, 4 skipped. The skipped tests
are the Windows-only `start.bat` checks.

### 6.2 Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every pull request:

- the Python suite on Ubuntu and Windows with Python 3.11 and 3.12, plus a
  CLI smoke test;
- the sample Java project with Maven and JUnit 5;
- the IDE extension type-check and compile;
- CodeDNA with real Maven and JaCoCo (integration).

### 6.3 Manual checks

- IDE build and start on the Windows laptop (PR #10, #11). The installer
  build depends on native modules and Visual Studio Build Tools; its status
  is recorded in [IMPLEMENTATION_HANDOFF.md](IMPLEMENTATION_HANDOFF.md).
- Impact graph layout rendered on real HikariCP graphs (D-051).
- Test discovery on HikariCP 688d1911 matches the 21 classes CI ran (D-052).
- **Graph precision check (open).** A manual check of a sample of graph
  edges against the source is still needed before the report can state how
  often confirmed and heuristic edges are correct. *To be filled.*

## 7. Limitations and future work

### 7.1 Limitations

- **Java only.** Other languages need plugins; none exists yet.
- **Type-level graph.** Calls between methods are not resolved, so impact is
  coarser than the change.
- **Class-level outcomes.** History and selection work per test class, not
  per test method.
- **Evidence needs time.** The live gate needs many recorded commits with
  failures before it trusts the risk estimate; on public CI histories it never
  accepted, because the records were incomplete (D-052). Until then the
  product recommends the full suite, which is safe but saves no time.
- **No transfer.** Models trained on one project are not reliable on another
  (D-039).
- **Data age.** The study projects are open-source Java projects from 2007 to
  2016 on Travis CI; modern or industrial CI may behave differently.
- **Confirmatory study pending.** The pre-registered rolling-origin study
  on new RTPTorrent projects (D-042) is being prepared. *Results to be
  filled from `experiments/results/rolling-evidence-confirmatory-*`.*

### 7.2 Future work

- Security checks as add-on policy rules (`codedna.policies`), for example
  always running tests of changed authentication code, after the defence.
- The `codedna-java` package split and an in-IDE plugin manager installing
  from the official catalogue (D-020).
- A second language plugin.
- Method-level call edges in the graph.
- A guard for AI coding agents: an interface through which an agent asks
  CodeDNA which tests must run before accepting its change.
