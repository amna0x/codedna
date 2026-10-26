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

Most research answers the first question: it ranks or selects tests from
dependencies, coverage or failure history [2, 24]. Industrial predictive test
selection answers part of the second with an *aggregate* target, such as
"catch 95 % of failing tests across past changes" [9, 11, 12]. What is
rarely given is a risk number for *this* change, used only after the
project's own recent history shows that stopping on it keeps its target,
with the full suite recommended otherwise.

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
prioritisation, history-based ranking, probability calibration and
recall-target cutoffs are all established, and CodeDNA claims novelty for
none of them. Predictive Test Selection at Facebook [9] already combines a
learned model, a holdout and a recall target. The contribution this project
evaluates is a narrower combination:

- a **per-commit estimate of omitted-failure risk** (the probability that at
  least one skipped test fails), computed from calibrated per-test
  probabilities and used as the stopping rule on top of a simple history
  ordering (policy B10, D-036). Simple rules choose *which* tests run; the
  model chooses only *how many*;
- a **per-project validation gate** (D-041) that accepts the stopping rule
  only when, replayed on the project's recent audit history, it kept the
  miss target (one-sided 95 % Wilson upper bound on the commit miss rate at
  or below the target, at least ten failing commits, at least 90 %
  failing-test recall), and otherwise recommends the full suite with a
  reason. This is an outcome check of the target, not a calibration test of
  each estimate;
- an **open, matched-time evaluation** on public CI data that reports where
  the approach does not help, and an implementation that keeps unverified
  relationships and missing outcomes visible.

The evaluation chapter finds that the per-commit estimate is usable (with a
5 % target the observed miss rate stays within the target on ten of eleven
projects; pooled estimate 2.6 %, observed 2.8 %) but that stopping on it does not catch more failures than a well-chosen
fixed budget at the same test time: the exploratory rolling-origin
difference is −0.003 [−0.036, 0.029] in safety. The value claimed is
therefore a stated risk target that is used only where it held on the
project's recent history, and a safe refusal elsewhere, not a faster or
safer selection. Models trained on one project do not reliably transfer to
another (D-039).

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
found early; minimisation removes redundant tests [1, 2]. Static RTS follows
dependencies from changed code to tests [4]; dynamic RTS uses dependencies
recorded on an earlier run [3]. Both aim to be *safe*: never skip a test
whose outcome could change. CodeDNA implements both as baselines:
`dependency` selection from the graph and `coverage` selection from per-test
JaCoCo maps (D-015, D-016). Section 4.5 of the evaluation shows why safe
selection alone is not enough on this data: on two projects the graph
reaches almost none of the failing tests.

### 2.2 History-based and learned approaches in CI

In continuous integration, dependency analysis is often too slow or too
coarse, so selection uses test history instead. Elbaum et al. select tests
that failed recently or have not run for a while [5]. RETECS learns
prioritisation by reinforcement learning [6]. Bertolino et al. compare
learning-to-rank with ranking-to-learn on CI data [7], and Yaraghi et al.
build a 150-feature model over 25 Java projects [25]. A systematic review
lists dozens of ML-based selection and prioritisation methods [24]. A
recurring finding, which CodeDNA's evaluation repeats, is that simple
history rules are hard to beat once test duration is counted [7, 15].
CodeDNA's study models use 19 features in four groups (change, test,
structural, history; [REPORT_DRAFT.md](REPORT_DRAFT.md) section 2.2) and are
compared against random, shortest-first and history orderings (B1, B2, B3,
B5). The study data is RTPTorrent [8].

### 2.3 Predictive test selection with a target

Predictive Test Selection at Facebook [9] scores each test with a gradient
boosted model trained on past outcomes. It selects tests above a score cutoff
plus the top N, and tunes both cutoffs on a one-week holdout so that over
95 % of failing tests and over 99.9 % of faulty changes are still caught.
Each weekly model is deployed only if it keeps the selection rate under 0.3
at 90 % recall. A 2025 replication on 12 open-source Java projects confirms
the main findings but again analyses no calibration [10]. Two commercial
tools follow the same idea. Launchable's "confidence curve" is the share of
past failing sessions that a given runtime would have caught [11].
Develocity offers Conservative, Standard and Fast profiles "calibrated to
catch over 99 %" of failures, and always runs new, changed, recently failed
and flaky tests [12].

These targets are *aggregate*: they promise a catch rate over many past
changes, not a risk for the current one, and the per-test scores are not
checked as probabilities. CodeDNA differs in two narrow ways. It reports an
estimated omitted-failure risk for each change, and it uses that estimate as
a stopping rule only after a replay on the target project's recent history
kept the miss target (D-041). Its
must-run policy (D-050) plays the same role as Develocity's always-run rules.

### 2.4 Recent research closest to CodeDNA

A property-by-property comparison is kept in
[RELATED_WORK_COMPARISON.md](RELATED_WORK_COMPARISON.md). In summary:

- **Context-Aware Sequential Ranking** [13] uses the same RTPTorrent data.
  It fuses history and code-semantic scores, builds class-conditional
  conformal candidate sets (α = 0.10, with an adaptive update) and stops at a
  cost budget of 10, 25 or 50 % of the suite. Its conformal layer reorders
  tests and reports candidate coverage (0.906); it does not estimate the
  probability of missing a failure among skipped tests, and no per-project
  acceptance step was found. It also finds that history alone is close to
  its best model (0.869 against 0.884).
- **MOX** [14] optimises cost, impact, coverage and traceability on a Pareto
  front under a residual impact budget θ. The authors state that the budget
  is "not an empirically calibrated safety guarantee", and change events in
  their data are inferred from failures.
- **DANTE** [15] is a training-free history and commit-aware method that
  beats ML baselines on long-running Java suites. It is the strongest
  baseline found. CodeDNA evaluates an independently implemented,
  history-only adaptation (DANTE-H, D-040), not the full published method.
  Only DANTE's abstract was available; whether it has a stopping rule is
  unverified.
- **AutoTCP** [16] composes and tunes prioritisation workflows per build by
  grammar-guided genetic programming; it ranks tests and gives no skip risk.
- **Risk-aware batch testing** at Mozilla [17] predicts a regression
  probability per commit and flushes a batch when the probability that it
  holds a regressor passes a threshold, using the same independence
  assumption as CodeDNA's skip risk. Its scores are not calibrated.
- **Continuous test suite failure prediction** [18] predicts whether a whole
  suite run will fail, so that runs can be skipped.

### 2.5 Calibration and uncertainty

A predicted probability is calibrated when, among tests given probability p,
a fraction p actually fail. Platt scaling and isotonic regression are the
standard post-hoc methods [20]; conformal prediction gives distribution-free
coverage sets instead of probabilities [23], and conformal risk control
extends this to bounding the expected value of any monotone loss [26]. One
open-source project applies conformal risk control to the share of missed
failing tests on an industrial dataset [27]. In software engineering,
just-in-time defect predictors were found miscalibrated (ECE 7–35 %), and
post-hoc calibration did not consistently help [19]. CodeDNA fits Platt or
isotonic calibration on a held-out window and reports Brier score, expected
calibration error and reliability bins (D-025). Its evaluation shows a large
ECE drop (0.118 to 0.021), but also that much of the gain only undoes
balanced class weighting (D-037; [REPORT_DRAFT.md](REPORT_DRAFT.md)
section 4.3). The finding that matters is a different one: a model with a
low ECE can still underestimate the *summed* risk of many skipped tests, and
without calibration the stopping rule broke its target on a third of the
projects. Calibration is therefore presented as a requirement of a
risk-target stopping rule, not as an accuracy gain.

### 2.6 Test selection for AI coding agents

Coding agents now open many pull requests, and failing tests are a leading
reason they are rejected. TDAD [21] gives an agent a static code-to-test map
before it commits and reports fewer regressions on SWE-bench Verified
(6.08 % to 1.82 %, on 100 and 25 tasks). TestPrune [22] minimises the
existing regression suite so an agent can use it for reproduction and
validation. Neither states a risk for the tests left out. CodeDNA's brake
(D-059) exposes the same risk estimate and gate to agents; this report makes
no claim that it improves agents, because no paid agent runs were made.

### 2.7 Position

CodeDNA sits between safe RTS, which never skips a possibly affected test,
and predictive selection, which skips tests to meet an aggregate target. A
re-implementation of the Predictive Test Selection rule (evaluation section
4.9) neither beats nor loses to CodeDNA's stopping rule at the same test
time on four projects, but its aggregate targets held less often out of
sample. It
keeps a simple history ordering, adds a per-change risk estimate that must
pass a per-project outcome check, and falls back to the full suite when it does not.
The report never claims to be the first to do this, and section 4 shows that
the approach buys a risk target that has been shown to hold on the
project, rather than extra failures caught.

## 3. Requirements

### 3.1 Functional requirements

| ID | Requirement | Where |
|---|---|---|
| F1 | Report changed files, statuses, renames and line ranges between two revisions, including uncommitted changes (`WORKTREE`) | `git_analysis`, D-046 |
| F2 | Map changed lines to Java declarations; mark comment-only changes; record unmapped lines with a reason | `java_analysis`, D-008, D-009 |
| F3 | Build a dependency graph with confirmed / heuristic edges, evidence and unresolved names | `dependency_graph`, D-010 |
| F4 | Compute impacted types with distance, confidence and explanation path | `impact_analysis`, D-012 |
| F5 | Discover JUnit 3/4/5 test classes the build runs by default, for single and multi-module Maven and Gradle projects | `test_mapping`, D-045, D-052, D-064 |
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
`python -m pytest --run-maven` → 329 passed, 4 skipped. The skipped tests
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
- **Graph precision check (D-058).** 160 dependency edges were sampled with
  a fixed seed, 40 confirmed and 40 heuristic from each of HikariCP and
  LittleProxy, and checked against the source. All 160 were correct:
  precision 1.00, with a 95 % Wilson interval of [0.954, 1.00] for each label.
  Every unresolved name was also sorted into groups to look for missed links.
  This found four causes: `var` read as a type name, an incomplete
  `java.lang` list, member types brought in by static imports, and member
  types inherited from a superclass. One of these had silently resolved an
  inherited `Override` enum to the JDK annotation. After the fixes, the
  unresolved rate fell from 0.264 to 0.139 on HikariCP and from 0.103 to
  0.070 on LittleProxy, and no remaining unresolved name is a type the graph
  models. The labels were made by Claude while reading the source and still
  need a spot check by a student
  (`experiments/results/graph-precision-2026-10-25/FINDINGS.md`).

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
- Replace the D-041 gate with failure-conditional conformal risk control
  (B12f, D-063) if the confirmatory datasets support it, and expose its
  bound through the agent brake.
- A risk estimate that does not assume independent test failures, for
  example by grouping tests that fail together.

## References

1. G. Rothermel and M. J. Harrold. Analyzing regression test selection
   techniques. *IEEE Transactions on Software Engineering* 22(8), 1996.
2. S. Yoo and M. Harman. Regression testing minimization, selection and
   prioritization: a survey. *Software Testing, Verification and
   Reliability* 22(2), 2012.
3. M. Gligoric, L. Eloussi and D. Marinov. Practical regression test
   selection with dynamic file dependencies. *ISSTA* 2015.
4. O. Legunsen, F. Hariri, A. Shi, Y. Lu, L. Zhang and D. Marinov. An
   extensive study of static regression test selection in modern software
   evolution. *FSE* 2016.
5. S. Elbaum, G. Rothermel and J. Penix. Techniques for improving regression
   testing in continuous integration development environments. *FSE* 2014.
6. H. Spieker, A. Gotlieb, D. Marijan and M. Mossige. Reinforcement learning
   for automatic test case prioritization and selection in continuous
   integration. *ISSTA* 2017.
7. A. Bertolino, A. Guerriero, B. Miranda, R. Pietrantuono and S. Russo.
   Learning-to-rank vs ranking-to-learn: strategies for regression testing
   in continuous integration. *ICSE* 2020.
8. T. Mattis, P. Rein, F. Dürsch and R. Hirschfeld. RTPTorrent: an
   open-source dataset for evaluating regression test prioritization.
   *MSR* 2020.
9. M. Machalica, A. Samylkin, M. Porth and S. Chandra. Predictive test
   selection. *ICSE-SEIP* 2019. arXiv:1810.05286.
10. S. Aichmann. *Predictive Test Selection: A Replication Study*. Diploma
    thesis, TU Wien, 2025.
11. Launchable. How a confidence curve is generated. Product documentation,
    accessed 2026-10-25.
12. Gradle Develocity. Predictive Test Selection user manual (2026.3).
    Product documentation, accessed 2026-10-25.
13. U. Altınışık. Context-aware sequential ranking for dynamic test case
    prioritization in continuous integration. *Mathematics* 14(18):3276,
    2026.
14. M. Bădoi, A. Bărcan, A. Vultureanu-Albiși and N. Țăpuș. Multi-objective
    explainable AI for risk-aware test selection in multi-layer continuous
    integration systems. *Electronics* 15(17):3854, 2026.
15. S. Reale, E. Di Nitto, L. Baresi, M. Di Penta and G. Quattrocchi. DANTE:
    data-driven test case selection and prioritization for long-running test
    suites. *ICST* 2026, pp. 5–16.
16. J. R. Romero, A. Ramírez and C. García-Martínez. Automated machine
    learning for test case prioritisation. *Empirical Software Engineering*
    31:120, 2026.
17. A. Sayedsalehi, P. C. Rigby and G. Mierzwinski. Risk-aware batch testing
    for performance regression detection. arXiv:2604.00222, 2026.
18. C. Pan and M. Pradel. Continuous test suite failure prediction. *ISSTA*
    2021.
19. X. Shahini, J. Bartel and K. Pohl. On the calibration of just-in-time
    defect prediction. *MSR* 2025.
20. A. Niculescu-Mizil and R. Caruana. Predicting good probabilities with
    supervised learning. *ICML* 2005.
21. P. Alonso, S. Yovine and V. A. Braberman. TDAD: test-driven agentic
    development. Reducing code regressions in AI coding agents via
    graph-based impact analysis. arXiv:2603.17973, 2026.
22. Y. Chen, T. Ahmed, R. Jabbarvand and M. Hirzel. Can old tests do new
    tricks for resolving SWE issues? arXiv:2510.18270, 2025.
23. A. N. Angelopoulos and S. Bates. Conformal prediction: a gentle
    introduction. *Foundations and Trends in Machine Learning* 16(4), 2023.
24. R. Pan, M. Bagherzadeh, T. A. Ghaleb and L. Briand. Test case selection
    and prioritization using machine learning: a systematic literature
    review. *Empirical Software Engineering* 27, 2022.
25. A. S. Yaraghi, M. Bagherzadeh, N. Kahani and L. Briand. Scalable and
    accurate test case prioritization in continuous integration contexts.
    *IEEE Transactions on Software Engineering* 49(4), 2023.
26. A. N. Angelopoulos, S. Bates, A. Fisch, L. Lei and T. Schuster.
    Conformal risk control. *ICLR* 2024.
27. l-k-1-2. Predictive-test-selection: conformal risk control on the
    Enhanced Westermo dataset. GitHub repository, accessed 2026-10-26.
