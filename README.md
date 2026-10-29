# CodeDNA

**Risk-calibrated change-impact analysis and regression test selection for
Java projects in continuous integration.** A Software Engineering Final Year
Project.

Given a Git repository and two commits, CodeDNA reports changed code, follows
its potential dependencies and recommends regression tests with reasons. Its
Java risk-stopping path requires prior target-project evidence; insufficient
evidence keeps the full-suite fallback. Java and Python language plugins exist.

**Where it is heading:** a platform — the Python analysis core, downloadable
language plugins (Java first), the **CodeDNA IDE** built on Eclipse Theia,
and a platform website with a plugin catalogue. The core and desktop IDE exist;
public plugin hosting remains pending. Current engineering status: [handoff](docs/HANDOFF.md#05-start-here---current-continuation-2026-10-27); see [docs/ROADMAP.md](docs/ROADMAP.md) and decisions D-017 – D-020 in
[docs/DECISIONS.md](docs/DECISIONS.md).

**Status:** Milestones 0–3 are complete. Milestones 4–5 have saved results from
eleven RTPTorrent projects and five seeds; the evaluation report is in progress.
Learned ordering does not beat simple rules on this study. See
[findings](experiments/results/study11-2026-10-21/FINDINGS.md) and
[reproducible figures](experiments/results/study11-2026-10-21/figures/FIGURES.md).
The [four-project transfer check](experiments/results/cross-project-2026-10-24/FINDINGS.md)
does not establish reliable general transfer; target-project validation remains necessary.
Today CodeDNA can:

- report changes between two commits: files, line ranges, and the Java
  **classes, methods, constructors and fields** they touch (`analyze`);
- export a **code dependency graph** of any commit, with every edge labelled
  `confirmed` or `heuristic` and unresolved names listed separately (`graph`);
- list types **potentially impacted** by a change, each with an explanation
  path, plus the test classes that depend on them (`impact`);
- discover JUnit 3/4/5 test classes statically (`tests`);
- run a commit's Maven test suite in an isolated export, optionally with
  **per-test JaCoCo coverage** (`run-tests`, only with `--allow-build`);
- select tests with three baselines — retest-all, dependency-only and
  coverage-based — and compare them against a full run (`select`, `compare`).

Analysis commands parse code with Tree-sitter and never build or execute it;
only `run-tests` executes the project, and only when you pass `--allow-build`.
History mining, predictive ranking, calibration and the hybrid B10 experiment
are implemented; see [docs/ROADMAP.md](docs/ROADMAP.md).

## Prerequisites

| Tool | Version | Needed for |
|------|---------|-----------|
| Python | 3.11 or newer | CodeDNA itself |
| Git | 2.24 or newer | Change extraction |
| Java (JDK) | 17 | `run-tests` and the sample project |
| Maven | 3.9+ | `run-tests` on Maven projects (everything else works without it) |
| Gradle | 8+ (optional) | `run-tests` on Gradle projects; the repository's `gradlew` is never run |

## Setup

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pip install -e plugins/codedna-java -e plugins/codedna-python
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pip install -e plugins/codedna-java -e plugins/codedna-python
```

Java support is a separate plugin, `plugins/codedna-java` (D-054). Without it
CodeDNA still lists changed files but says that Java files were not analysed.
Installing the plugin needs internet once (it downloads the `tree-sitter` and
`tree-sitter-java` wheels, which include the compiled Java grammar). After
that, analysis and tests run fully offline. `start.bat` installs the plugin by
itself if it is missing.

Python support is the `plugins/codedna-python` plugin (D-060). It needs only
the standard library. Both plugins can work on one repository: in a mixed
Java + Python project each analyses its own files, their graphs and tests
are joined, and `run-tests` runs Maven/Gradle and pytest and joins the
results. Dependencies between the two languages are not followed, so a
change in a language that has no tests falls back to running everything.

## Run the tests

```bash
python -m pytest
```

One end-to-end test runs real Maven + JaCoCo on the sample project. It is
skipped by default because it needs Maven, a JDK and internet access (Maven
downloads plugins); CI runs it. To run it locally:

```bash
python -m pytest -m maven --run-maven
```

To validate the entire suite including Maven, run:

```bash
python -m pytest --run-maven
```

## Usage

```bash
# HEAD_REV may be WORKTREE: uncommitted edits and new (non-ignored) files
codedna analyze --repo PATH --base BASE_REV --head HEAD_REV [--level method|file] [--output FILE]
codedna graph   --repo PATH [--rev REV] [--no-members] [--output FILE]
codedna impact  --repo PATH --base BASE_REV --head HEAD_REV [--max-depth N] [--confirmed-only] [--output FILE]
codedna tests   --repo PATH [--rev REV] [--output FILE]
codedna run-tests --repo PATH [--rev REV] --output-dir DIR --allow-build [--per-test-coverage] [--mvn PATH] [--gradle PATH] [--timeout S]
codedna select  --repo PATH --base BASE_REV --head HEAD_REV --strategy all|dependency|coverage [--coverage-map F] [--durations F] [--non-java retest-all|ignore] [--must-run PATTERN ...]
codedna risk-select --repo PATH --base BASE_REV --head HEAD_REV [--history-csv F] [--risk-target F] [--must-run PATTERN ...]
codedna compare --repo PATH --base BASE_REV --head HEAD_REV --ground-truth F [--coverage-map F] [--non-java retest-all|ignore]
codedna plugins                                     # installed plugins and load problems
codedna plugins catalogue                           # the official catalogue
codedna plugins install ID VERSION --yes            # exact version, SHA-256 checked first
codedna plugins remove ID --yes
codedna serve   [--host 127.0.0.1] [--port 8765] [--allow-build]
codedna mcp     [--repo PATH] [--allow-build] [--mvn PATH] [--gradle PATH]
codedna history mine     --repo PATH --db FILE [--rev REV] [--max-commits N]
codedna history import   --db FILE RESULTS [RESULTS ...] [--source NAME]
codedna history collect  --repo PATH --db FILE --output-dir DIR --allow-build [--max-commits N]
codedna history status   --db FILE
codedna history record   --repo PATH RESULTS
codedna history evaluate --db FILE [--repo PATH] [--rankers ...] [--no-structural] [--dataset-csv F]
codedna history import-rtptorrent --dataset DIR (--list | --project NAME --db FILE) [--max-commits N]
codedna history experiment --db FILE [--repo PATH] [--model M] [--calibration none|platt|isotonic] [--budget F] [--risk-target F] [--replay]
codedna replay  REPORT [--output FILE]
codedna replay  (--list | --overview) FOLDER [FOLDER ...] [--seed N]
```

- `analyze --level method` (default) adds a `java` object to every changed
  Java file; `--level file` skips Java parsing.
- `graph` exports packages, files, types and members of one commit (default
  `HEAD`) with `contains`, `extends`, `implements`, `uses`, `imports` and
  `static_access` edges. `--no-members` leaves out method/field nodes.
- `impact` follows dependency edges backwards from the changed types.
  `--max-depth` limits the number of hops; `--confirmed-only` ignores
  heuristic edges.
- `tests` lists JUnit test classes and whether Surefire runs them by default.
- `run-tests` **executes the project's code and build plugins**, so it refuses
  to start without `--allow-build`. It exports the commit with `git archive`
  into `DIR/checkout` (your working tree and `pom.xml` are never touched),
  runs `mvn test`, and writes `DIR/results.json`. `--per-test-coverage` runs
  every test class separately under JaCoCo and also writes
  `DIR/coverage-map.json` (slow: one Maven run per test class).
- `select` picks tests for a change: `all` (retest-all), `dependency` (static
  graph) or `coverage` (needs a coverage map recorded at BASE). Changed tests
  are always selected; a changed file no plugin analyses (or one in a language
  with no tests) falls back to retest-all unless `--non-java ignore`. `--durations` adds a time estimate.
- `compare` runs all strategies against a full run of HEAD (`--ground-truth`)
  and reports selection ratio, estimated time, and failing tests caught/missed.
  Files and run directories are both accepted for `--coverage-map`,
  `--durations` and `--ground-truth`.
- `plugins` lists installed language plugins (Java comes from `plugins/codedna-java`,
  Python from `plugins/codedna-python`).
- `serve` starts the **local API for the CodeDNA IDE** (needs
  `pip install -e ".[api]"`, included in `.[dev]`). It listens on loopback
  only and prints one JSON line with the URL and a session token
  (`CODEDNA_API_TOKEN` overrides it); every request except
  `/api/health` needs the `X-CodeDNA-Token` header. Endpoints mirror the CLI
  (`/api/analyze`, `/api/graph`, `/api/impact`, `/api/tests`, `/api/select`,
  `/api/compare`, `/api/run-tests`, `/api/replay`, `/api/replay/sources`,
  `/api/replay/overview`); `/api/run-tests` additionally needs
  `--allow-build` on the server and `"allow_build": true` in the request.
  Interactive docs: `http://127.0.0.1:8765/docs`.
- `history` builds a per-repository SQLite database: `mine` stores the
  first-parent commits, `import` stores `results.json` files, `collect`
  runs the full suite of each mined commit (**executes project code**, needs
  `--allow-build`, slow), and `evaluate` builds leakage-free features and
  compares orderings (random, shortest-first, recent failures, failure
  history, logistic regression, gradient boosting) on a chronological
  60/20/20 split. ML needs scikit-learn (`pip install -e ".[ml]"`; included
  in `.[dev]`).
- `history import-rtptorrent` fills a history database from the
  [RTPTorrent](https://zenodo.org/records/4046180) dataset (real Travis CI
  test results for 20 Java projects, CC BY 4.0; Mattis et al., MSR 2020)
  without building anything; `--list` shows the projects.
- `history experiment` is the Milestone 5 study: train on the oldest 60 %,
  calibrate on the next 20 %, then compare retest-all (B0), dependency (B4),
  change-only ML (B6), uncalibrated ML (B7), calibrated ML (B8) and
  calibrated ML with risk target + fallback (B9) on the latest 20 %, plus
  calibration quality, budget/risk sweeps and feature ablations. The report
  includes a dataset hash, seed and package versions for reproducibility.
  `--replay` also records each test commit's SHA, test names and seconds for
  `replay`.
- `replay` turns a saved experiment report into a commit-by-commit timeline
  (what each policy ran and missed, with running totals checked against the
  report) for the IDE's **History replay** view; `--list` finds reports in
  study folders and `--overview` gives per-project results and the mean over
  projects. It reads saved results only. Detailed traces for four study
  projects are in `experiments/results/replay-2026-10-25/`
  (`scripts/record_replays.py` makes more when a project's dataset is present).

`BASE_REV`/`HEAD_REV` can be full or short SHAs, branches, tags or expressions
like `HEAD~1`. They are resolved to full SHAs in the output.
`python -m codedna ...` works too.

Exit codes: `0` success · `1` bad repository / unknown commit / Git error ·
`2` invalid command-line arguments.

## Demo: analyse a real change

`scripts/make_demo_repo.py` copies the sample Java project into a new Git
repository, commits it, then makes a second commit that modifies a method,
adds a class, renames a test and edits a README.

```bash
python scripts/make_demo_repo.py ../codedna-demo
```

It prints the two SHAs and the exact command to run, for example:

```bash
codedna analyze --repo ../codedna-demo --base <BASE_SHA> --head <HEAD_SHA>
```

Excerpt of real output from the demo repository (line ranges compacted onto
one line for readability):

```json
{
  "path": "src/main/java/example/PriceCalculator.java",
  "status": "modified",
  "old_path": null,
  "similarity": null,
  "is_java": true,
  "is_binary": false,
  "changed_lines": [[23, 24]],
  "removed_lines": [[23, 23]],
  "java": {
    "package": "example",
    "declarations": [
      {
        "id": "example.PriceCalculator#applyDiscount(double)",
        "kind": "method",
        "change": "modified",
        "code_changed": true,
        "parent": "example.PriceCalculator",
        "head_lines": [22, 25],
        "base_lines": [22, 24],
        "changed_lines": [[23, 24]],
        "removed_lines": [[23, 23]],
        "parts": []
      }
    ],
    "outside_declarations": [],
    "unresolved": []
  }
}
```

The new `Rounding.java` file lists `example.Rounding` (class),
`example.Rounding#<init>()` and `example.Rounding#toCents(double)`, all
`"change": "added"`. The renamed test file shows the class rename as
`example.OrderTotalsTest` added + `example.OrderServiceTest` deleted.

Impact for the same change (`codedna impact`, excerpt of real output):

```json
"impacted": [
  {
    "node": "type:example.OrderService",
    "distance": 1,
    "confidence": "confirmed",
    "seed": "type:example.PriceCalculator",
    "path": [{"dependent": "type:example.OrderService", "depends_on": "type:example.PriceCalculator",
              "kind": "uses", "confidence": "confirmed",
              "evidence": "src/main/java/example/OrderService.java:12"}]
  },
  ...
],
"candidate_tests": [
  {"type": "type:example.OrderTotalsTest", "reason": "test class changed", ...},
  {"type": "type:example.PriceCalculatorTest",
   "reason": "depends on changed type:example.PriceCalculator (distance 1)", ...}
],
"unanalysed_changes": [{"path": "README.md", "reason": "non-Java file; impact not analysed", ...}]
```

The graph labels `PriceCalculator → Rounding` as `static_access` /
`heuristic`: `Rounding.toCents(...)` is *probably* a static call, but a
variable named `Rounding` would look the same, so CodeDNA does not claim it.

`changed_lines` are inclusive line ranges in the **head** version of a file;
`removed_lines` are inclusive ranges in the **base** version. Inside `java`,
`code_changed: false` means only comments or formatting changed, and
`unresolved` lists lines that could not be mapped (e.g. syntax errors) —
CodeDNA never guesses. Full field list:
[docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md).

## Demo: test selection with real Maven

Needs Maven and a JDK. Using the demo repository from above:

```bash
codedna run-tests --repo ../codedna-demo --rev <BASE_SHA> --output-dir ../runs/base --per-test-coverage --allow-build
codedna run-tests --repo ../codedna-demo --rev <HEAD_SHA> --output-dir ../runs/head --allow-build
codedna compare --repo ../codedna-demo --base <BASE_SHA> --head <HEAD_SHA> --ground-truth ../runs/head --coverage-map ../runs/base --non-java ignore
```

The demo change also edits `README.md`; without `--non-java ignore` every
strategy falls back to retest-all. The real Maven/JUnit/JaCoCo integration
flow in `test_maven_integration.py` passed on the Windows development laptop
on 2026-10-24 with the portable JDK and Maven runtime.

## CodeDNA IDE

`ide/` contains the desktop IDE (Eclipse Theia 1.76 + Electron) with the
**Changes** and **Tests to run** views, written so newcomers can use them,
and the calm CodeDNA Dark theme. See [ide/README.md](ide/README.md) for prerequisites and
`npm install && npm run build && npm start`. On Windows, double-click
`start.bat` in the repository root: it installs and builds the IDE on first
run, points it at the `.venv` core and the JDK, and opens a demo project
(`start.bat C:\path\to\repo` opens another folder).

### Demo on a real project (HikariCP)

With the RTPTorrent HikariCP data in `experiments/` (see DATASET_PLAN.md):

```bat
.venv\Scripts\python scripts\make_hikaricp_demo.py %USERPROFILE%\codedna-hikaricp
start.bat %USERPROFILE%\codedna-hikaricp
```

The folder's last commit is a real HikariCP change (dd7c9a9a) whose CI run
failed 17 of 21 test classes; `.codedna/history.csv` holds the project's
recorded test history up to the commit before it, and `.codedna/demo.json`
puts CodeDNA's answers next to the real CI outcome. Dependency selection picks
19 of 21 classes and catches all 17 failures in 24% of the CI test time; the
risk view falls back to the full suite because the history fails the gate
(D-052). The commit was picked for the demonstration (`--list` shows the
others); it is not evidence.

![CodeDNA IDE](docs/ide-screenshot.png)

## Sample Java project

`examples/sample-java-project` is a tiny Maven + JUnit 5 project
(`OrderService`, `PriceCalculator` and their tests). With Maven installed:

```bash
cd examples/sample-java-project
mvn verify
```

## Repository layout

```
backend/codedna/          Python package
  cli.py                  `codedna` command
  git_analysis/           Git wrapper + file-level change extraction
  dependency_graph/       shared code-graph schema (any language plugin)
  impact_analysis/        reverse-dependency traversal with explanation paths
  test_mapping/           shared test-results and coverage-map schema
  selection/              retest-all / dependency / coverage baselines, compare
  plugins/                language-plugin interface, registry, catalogue, plugin manager
  test_history/           SQLite history store, mining, result collection, features
  models/                 ranking baselines, ML models, metrics, evaluation, experiment
  calibration/            Platt / isotonic calibration, Brier, ECE, reliability
  api/                    local FastAPI server for the CodeDNA IDE
plugins/codedna-java/     Java plugin: Tree-sitter parser, change mapping, graph builder,
                          JUnit discovery, Maven/Gradle runner, Surefire/JaCoCo parsers
plugins/codedna-python/   Python plugin: ast parser, change mapping, import graph,
                          pytest discovery and runner
ide/                      CodeDNA IDE (Theia + Electron, TypeScript)
backend/tests/            pytest suite (temporary Git repos, no network)
examples/                 sample Java/Maven project
scripts/                  helper scripts (demo repo builder)
docs/                     spec, architecture, roadmap, research, decisions
.github/workflows/ci.yml  tests on Ubuntu + Windows, Maven build, real-Maven integration
AGENTS.md                 rules for contributors and AI coding agents
CODEDNA_STARTER.md        original project brief
```

## Known limitations

- Declaration IDs are syntactic (parameter types as written, not resolved).
- A syntax error in either version leaves that file `unresolved`.
- Class renames and signature changes appear as delete + add.
- Heavily edited moves (< 50 % similar) appear as delete + add.
- One `git diff` call per changed file; slow on huge diffs.
- Whitespace-only edits count as changes.
- Name resolution is a simplified subset of Java's rules: no inherited member
  types, no method-call resolution; unresolvable names are listed, not guessed.
- Graph roles use path conventions; `tests`/`select` use JUnit annotations
  plus Surefire's *default* includes — custom Surefire configuration is not
  read.
- Selection is at test-class level. `run-tests` supports single-module Maven
  projects with `pom.xml` at the root; no Gradle, TestNG or multi-module yet.
- Per-test coverage costs one Maven run per test class.
- Only Java is analysed; other changed files are listed as `unanalysed_changes`.
- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#known-limitations-current).

## Documentation

- [Project specification](docs/PROJECT_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Research plan](docs/RESEARCH_PLAN.md)
- [Dataset plan](docs/DATASET_PLAN.md)
- [Decision log](docs/DECISIONS.md)

## Scope

Java (Maven/Gradle, JUnit) and Python (pytest), each a language plugin
(D-013, D-018, D-054, D-060); the research track is Java only. Other files
are reported, not analysed. Software engineering only: no vulnerability detection
or security scoring.
CodeDNA does not claim novelty for established techniques, and reports no
performance numbers until experiments have actually been run.


## Reproduce the study figures

The saved study reports are sufficient; no raw dataset, history database,
model training, or third-party project build is needed.

```powershell
python -m pip install -e ".[plots]"
python scripts/make_study_figures.py --study experiments/results/study11-2026-10-21
```

This writes five PNG/SVG figures, their exact values, and a SHA-256 provenance
manifest under the study's `figures/` directory. Use `--data-only` to export
values and provenance without Matplotlib, or `--out PATH` for another output
directory. Missing reports and inconsistent seed/budget grids stop the export.


## Reproduce the cross-project transfer check

The four-project protocol is fixed in [CROSS_PROJECT_PROTOCOL.md](docs/CROSS_PROJECT_PROTOCOL.md).
Install the `ml` extra, then recover the public recorded data and run:

```powershell
python scripts/fetch_rtptorrent_subset.py
python scripts/prepare_transfer_features.py --workers 2
python scripts/run_cross_project.py
```

Recovery downloads only the selected RTPTorrent archive entries and rebuilds
four history databases and feature CSVs. Feature digests must match the original
study. No analysed repository is built. Results, within-project controls and
provenance go to `experiments/results/cross-project-2026-10-24/`. Training and
calibration use the source only; past target history remains available.


## Target-validated risk and execution

The IDE's **Tests to run** view now supports target-validated stopping, explicit
full-suite fallback and execution of recommended test classes after confirmation.
Use `codedna risk-select --repo PATH --base BASE --head HEAD` for the same core
recommendation. Without adequate history, risk stays unvalidated and all tests
are recommended. See [Java workflow](docs/JAVA_WORKFLOW.md) for history preparation,
validation limits, selected Maven execution and the IDE workflow.
`--method crc` uses the failure-conditional conformal stop instead of the
default calibrated stop (opt-in, D-068); it needs at least 19 failing audit
commits and otherwise recommends the full suite.

### Must-run tests

Tests listed in `.codedna/policy.toml` are never skipped by `select` or
`risk-select` (D-050):

```toml
[[must_run]]
tests = ["example.OrderServiceTest", "example.security.*"]
reason = "checkout and security checks run on every change"
```

The file is read from the BASE commit, so a change cannot loosen its own
policy; a broken file makes every test run. `--must-run PATTERN` adds
patterns for one run.

### History builds up as you use it

Every run of the whole suite that CodeDNA starts (IDE **Run**, when nothing
is skipped) is saved in `.codedna/history.db` and `.codedna/history.csv`
(D-053). `codedna history record --repo PATH RESULTS` adds a saved
`results.json`; `--saved` instead adds every eligible run under `.codedna/runs`,
for example selected or older IDE runs (D-057). Partial runs, other branches and
uncommitted states are not
recorded, and a `history.csv` you supplied is never overwritten. Risk
selection turns on only when this history passes the audit, which takes many
recorded commits with failures; until then it recommends the full suite.

### Test brake for AI coding agents

`codedna mcp` is an MCP server (stdin/stdout) that coding agents call before
they say a change is done (D-059). `codedna_plan_tests` lists the tests the
change must run, with reasons and the skip risk; `codedna_impact` shows what
the change can affect. Neither runs project code. With Claude Code:

```bash
claude mcp add codedna -- codedna mcp --repo /path/to/project
```

`codedna_check` also runs those tests and answers `passed`, `blocked`,
`incomplete` or `no_tests`. It executes the project's build, so it is only
offered when **you** start the server with `--allow-build --repo PATH`, and
then only for that repository. Without validated history the plan is the
whole suite.
Setup for Cursor and Codex, the agent instruction to add, and a demo
(`python scripts/demo_agent_brake.py DEST [--check]`) are in
[docs/AGENT_BRAKE.md](docs/AGENT_BRAKE.md).

The [fixed DANTE-H/B10 extension protocol](docs/DANTE_B10_PROTOCOL.md) and
[related-work comparison](docs/RELATED_WORK_COMPARISON.md) describe the independent
history-only adaptation; it is not a reproduction of published full DANTE.

### Brake structural feedback and Python fallback

The MCP plan returns a labelled structural_plan alongside the mandatory
union of risk, structural and policy tests. Structural evidence alone is
not a probability and never permits skipping without validated history.
Python and mixed-language projects safely receive a full-suite plan while
risk selection is unsupported; execution uses the existing Java/Python
plugin dispatcher. See [the brake guide](docs/AGENT_BRAKE.md).


## Current completion and language plugins

Open **Extensions → Language plugins** (Ctrl+Shift+X) in the IDE. Java and Python
are bundled; analysis plugins are distinct from editor completion/debugging
extensions. The activity tab is restored for existing as well as new layouts.
Installed languages remain usable when the official catalogue is unavailable.

- [Current completion ledger](docs/BLUEPRINT_COMPLETION.md)
- [Website implementation blueprint](docs/WEBSITE_BLUEPRINT.md)
- [Clean Windows acceptance and friend-PC test](docs/CLEAN_PC_ACCEPTANCE.md)
- [Independent graph review guide](docs/graph-human-review/REVIEW_GUIDE.md)
- [Supervisor review pack](docs/SUPERVISOR_REVIEW.md)

The website renders official optional-plugin downloads, full checksums and exact
install commands; current Java/Python entries are bundled. The D-074 candidate
supports transactional optional installation in the frozen executable; actual
restricted-PATH installation/restart/update/removal checks passed. See
[desktop plugin installation](docs/DESKTOP_PLUGIN_INSTALLATION.md). Public
catalogue/release hosting and clean-PC acceptance remain separate gates.
The brake reports its exact audit objective/denominator and does not promise
future safety. Existing mixed research results are preserved.

## Cancellable analysis (source development build)

The Tests to run and Changes views show core stages, elapsed time and Cancel
analysis when the connected core advertises analysis jobs. Older packaged cores retain the
synchronous path. Analysis cancellation never runs or cancels project builds.
The API also offers typed read-only jobs for test discovery, change analysis,
impact and selection; see [the job contract](docs/ANALYSIS_JOB_PLAN.md).

The isolated D083 desktop candidate contains these changes. Its embedded core
hashes and critical GUI workflows were verified; see
[preceding D083 release evidence](docs/RELEASE_VALIDATION_D083_2026-10-28.json).
The existing installed app was not replaced. Clean-PC installation remains open.

## Performance diagnostics (D-083)

Tests and Changes can show measured analysis timing in collapsed details.
The optional job query `?profile=true` and MCP argument `"profile": true`
return bounded stage timings. MCP checking still requires explicit build
consent. Nested stages overlap; worker startup is reported separately.

Immutable parsing and fitted-model reuse avoid duplicate work where safe.
Each decision still checks current evidence and recomputes its audit. An
entirely mandatory suite bypasses unnecessary fitting and remains a full-suite
recommendation. See [measurement scope and examples](docs/PERFORMANCE_ENGINEERING.md).
These improvements are included in the validated D083 candidate. D082's
earlier evidence remains tied to its preceding source checkpoint.

## Experimental Moonshot witness (D-085)

An optional Java capability compares bounded inputs on two versions of one
self-contained public method with bounded numeric/boolean/String/array inputs
and int/long/int-array results. Instance methods require a public no-argument
constructor and receive a fresh object per JVM invocation. A confirmed difference exports
source and a standalone JDK-only reproducer. It requires explicit project-code
consent. It does not classify a regression automatically or change required tests.

Use `python -m codedna witness --help`, or explicitly enable
`python -m codedna mcp --repo PATH --allow-build --moonshot`. The extra witness
tool is absent by default. See [scope, commands and evidence](docs/BEHAVIORAL_WITNESS.md).
The isolated D085 installer includes this optional capability; D083 remains
preserved. Source validation passed 714 tests with Maven and zero skips. Actual
frozen validation passed 32 checks. Installer payload hashes and restricted-PATH
unpacked smoke passed; no D085 installation or clean-PC acceptance is claimed.
See [release evidence](docs/RELEASE_VALIDATION_D085_2026-10-28.json).

The fixed 48-search synthetic comparison independently reproduced all 15 emitted
witnesses. Its constructed cases favor guidance and show no overall speedup;
they do not establish independent real-world accuracy or improved skip safety.
The prepared local friend kit includes Java demos and an acceptance checklist.
