# CodeDNA — Decision Log

Short records of important choices. Add a new entry instead of editing old
ones when a decision changes.

## D-001 — Python 3.11+ with setuptools, package under `backend/`

`pyproject.toml` at the repository root; `backend/codedna` is the import
package (`[tool.setuptools.packages.find] where = ["backend"]`). One editable
install (`pip install -e ".[dev]"`) gives both `import codedna` and the
`codedna` command. Setuptools is the most familiar build backend for students.

## D-002 — No runtime dependencies yet (argparse, dataclasses)

The starter stack lists FastAPI, Pydantic, NetworkX, etc. None are needed for
file-level change extraction, so they are **not** installed yet. The CLI uses
`argparse` and the data model uses `dataclasses`. FastAPI/Pydantic arrive with
the API milestone, NetworkX with the dependency graph. Only `pytest` is a dev
dependency.

*Needs human review:* if the team prefers Pydantic models from the start
(for JSON schema export), switch `ChangedFile`/`ChangeReport` before the
format is consumed by other modules.

## D-003 — Git CLI via subprocess, not PyDriller/GitPython

The Git CLI is already required, has exact, documented output formats
(`--name-status -z`, `--unified=0`), and avoids an extra dependency.
PyDriller may be reconsidered for history mining in Milestone 4.

Safety rules: argument lists only (never `shell=True`); revisions validated,
rejected if they start with `-`, and passed after `--end-of-options`;
`--no-ext-diff --no-textconv` and `core.fsmonitor=false` so repository-local
config cannot launch programs during analysis.

## D-004 — Line-range convention

`changed_lines` are inclusive ranges in the head file; `removed_lines` are
inclusive ranges in the base file. This keeps pure deletions visible (they
have no head-side lines) and gives the future method mapper both sides:
head-side ranges map to methods in the new file, base-side ranges to methods
that were deleted or replaced.

## D-005 — Report all changed files, flag Java ones

Non-Java files (e.g. `pom.xml`, resources) are kept in the output with
`is_java: false` because build/config changes can affect tests. Later stages
decide how to treat them.

## D-006 — Directories created on demand

Following the brief, empty placeholder packages (`api/`, `models/`, ...) and
top-level folders (`adapters/`, `experiments/`, `frontend/`) are not created
until their first real implementation.

## D-007 — Maven not required locally for Milestone 0

Maven was not installed on the bootstrap machine. The sample project is built
with `mvn verify` in GitHub Actions; locally its main sources were compiled
with `javac`. Installing Maven locally becomes required in Milestone 3.

## D-008 — Tree-sitter Java for syntax-level declaration extraction

Milestone 1 needs Java declarations (types, methods, constructors, fields)
with exact line ranges. Chosen: **`tree-sitter` 0.26.x + `tree-sitter-java`
0.23.x** (Python bindings), pinned to `tree-sitter>=0.25,<0.27` and
`tree-sitter-java>=0.23.5,<0.24`.

Checked on 2026-10-19 against PyPI:

| Package | Version | Licence | Windows wheels |
|---------|---------|---------|----------------|
| `tree-sitter` | 0.26.0 | MIT | cp310–cp314, win_amd64 + win_arm64 |
| `tree-sitter-java` | 0.23.5 | MIT | cp39-abi3, win_amd64 + win_arm64 |

Both ship prebuilt wheels (Linux/macOS too), so no C compiler is needed, and
the grammar is compiled into the wheel: once installed, parsing works fully
offline. Verified by installing into the project's Python 3.12 venv and
parsing sample sources.

Why Tree-sitter rather than JavaParser / Eclipse JDT:

- Pure `pip install`; no JVM process or Java build needed just to parse.
- Error-tolerant: a file with syntax errors still yields a tree, and
  `has_error` tells us so we can report the file as `unresolved` instead of
  guessing.
- Exact byte/row positions for every node, which is what line-range mapping
  needs.

Limitations accepted for now: Tree-sitter is syntax-only. Types are recorded
**as written** (`List<String>`, not `java.util.List<java.lang.String>`), so
declaration IDs are "fully-qualified-ish": package + enclosing types + member
name + source-text parameter types. No symbol or type resolution is done.
JavaParser (with its symbol solver) or Eclipse JDT may be evaluated in
Milestone 2 when the dependency graph needs resolved references.

## D-009 — Declaration IDs and change attribution rules

- Type: `pkg.Outer.Inner`. Method: `pkg.Type#name(T1,T2)`. Constructor:
  `pkg.Type#<init>(T1)`. Field / enum constant / annotation element:
  `pkg.Type#name`. Initializer blocks: `pkg.Type#<clinit>[n]` (static) and
  `pkg.Type#<init-block>[n]` (instance), `n` = 1-based order in the type.
  Whitespace is removed from parameter types; C-style array dimensions on the
  parameter name are moved onto the type; varargs keep `...`.
- Each changed line is attributed to the **innermost** declaration containing
  it. Members (methods, constructors, fields, initializers, enum constants)
  are leaves: anonymous/local classes and lambdas inside a method body are
  attributed to that method.
- Lines in a type body but outside every member belong to the type itself
  (annotations, header, comments between members). Lines outside every type
  (package, imports, file comments) are reported in `outside_declarations`.
  Blank lines in these gap regions are ignored because they carry no code.
- Head-side `changed_lines` are mapped on the head parse; base-side
  `removed_lines` on the base parse. A declaration whose ID only exists in
  head is `added`, only in base `deleted`, in both `modified`. A changed
  signature therefore appears as one `deleted` + one `added` entry.
- `code_changed` compares the declaration's non-comment tokens in base and
  head (for types: only the type's own tokens, not its members). `false` means
  only comments/formatting changed. It is `null` when not comparable.
- If either side of a Java file has a syntax error, nothing in that file is
  mapped: all its ranges go to `unresolved` with a warning. Unknown node
  types inside a type body are also reported as `unresolved`.

## D-010 — Simplified Java name resolution with confidence labels

The graph resolves type *names* written in a file to types declared in the
repository, in this order (a subset of JLS §6.4 / §7.5):

1. Type parameters in the file (`<T>`) are skipped — not references.
2. The enclosing types and their member types (`Inner` inside `Outer`).
3. Single-type imports (`import x.Money;`). An import of a non-repository
   type makes the name **external**.
4. Top-level types of the same package.
5. `java.lang` names from a fixed list (`String`, `Override`, ...) are
   external.
6. On-demand imports (`import x.*;`): one matching repository type gives a
   **heuristic** edge (a library package could declare the same name);
   several matches are **unresolved** (ambiguous).
7. Anything else is **unresolved**, with a reason, and never becomes an edge.

Qualified names (`a.b.C`, `Outer.Inner`) resolve their first segment by the
same rules; package-qualified names outside repository packages are external.

`Foo.bar()` / `Foo.BAR` with a capitalised `Foo` gives a `static_access` edge
that is always **heuristic** (it could be a variable). Duplicate type IDs
(same FQN in two files) and files with syntax errors downgrade their edges to
heuristic. Not handled: member types inherited from supertypes, method/field
resolution, and calls between methods — so there are no method-level call
edges yet. Revisit with JavaParser's symbol solver if method-level impact is
needed (RQ5).

## D-011 — Plain dictionaries, not NetworkX, for the graph

The graph only needs node/edge dictionaries and a breadth-first search, which
are a few dozen lines of plain Python that every team member can read.
NetworkX is not added yet. If graph metrics (centrality, PageRank) are needed
as ML features in Milestone 4/5, export `CodeGraph` to NetworkX at that point.

## D-012 — Impact on the union of BASE and HEAD graphs, confirmed-first

`impact` builds both graphs (sharing parses of unchanged files by blob SHA)
and merges them; every node/edge records `versions: ["base", "head"]`. Using
the union means a dependency that the change *removed* is still followed —
conservative, which is the safe direction for test selection. The BFS runs
twice: first over confirmed edges only, then (unless `--confirmed-only`)
over all edges for types not yet reached, so every impacted type gets a
confirmed explanation path when one exists. Comment/formatting-only changes
(`code_changed: false`) produce no seeds.

## D-013 — Java only (scope)

The brief defines Path A as Java (Maven, JUnit 5, JaCoCo). Git change
extraction is already language-independent, and the graph schema
(package/file/type/member nodes, typed edges with confidence) does not assume
Java, but parsing, name resolution, test discovery and coverage are all
language-specific and would multiply the work. Non-Java changes are therefore
listed as `unanalysed_changes` with a warning rather than silently ignored.
Supporting another language later means adding a parser + resolver that emit
the same graph schema. *Needs human review if the team wants to change scope.*

## D-014 — Running builds is opt-in and isolated

Running a project's tests executes its code and Maven plugins, which the brief
forbids doing automatically. So:

- `run-tests` refuses to start unless `--allow-build` is given, and prints a
  warning when it does start. All other commands never build or execute.
- The commit is exported with `git archive` into the output directory (tar
  extraction with the `data` filter rejects absolute paths, `..` and unsafe
  links). The user's working tree, index and `pom.xml` are never modified.
- JaCoCo is attached on the command line
  (`org.jacoco:jacoco-maven-plugin:0.8.12:prepare-agent ... :report`), so no
  build file is edited. Test class names passed to `-Dtest` must match a
  Java-name pattern.
- `-Dmaven.test.failure.ignore=true` lets failing tests produce reports; a
  non-zero exit is then a build failure and is recorded as a warning.

This is *isolation from the user's files*, not a security sandbox: the build
can still access the network and the user's account. Only run it on projects
you trust; use a container/VM for third-party projects (DATASET_PLAN.md).

The Maven adapter lives in `backend/codedna/test_mapping/maven.py` rather than
the brief's top-level `adapters/java_maven/`, because it is ordinary Python
imported by the CLI; a separate top-level folder would need its own packaging
for no benefit yet.

## D-015 — Per-test coverage by one Maven run per test class

JaCoCo records one execution data file per JVM, not per test. The simplest
exact way to get per-test-class coverage is to run each class separately with
a fresh `jacoco.exec`. Cost: roughly *test classes × Maven start-up*, which is
fine for the sample project and small/medium study subjects but slow for big
suites. Alternatives for later: a JUnit listener that dumps JaCoCo sessions
between classes (one JVM), or Ekstazi-style class-file dependencies.

Covered lines are mapped onto declarations of the **same commit** with the
Milestone 1 parser, giving member IDs that match `analyze` output exactly.

## D-016 — Selection rules chosen for safety

- Changed or new test classes are always selected.
- In `coverage`, tests without coverage data are selected (unknown ≠ safe).
- A new member selects tests that cover its class (overloads/overrides can
  change behaviour of existing calls).
- Non-Java changes trigger retest-all by default (`--non-java ignore` to
  override, which is recorded as a warning).
- Only test classes that Surefire runs by default form the universe; others
  are listed in warnings.

Measured safety comes from `compare` against real full-suite runs, never from
these rules alone.

## D-017 — Product direction: platform, own IDE, website (Java first)

Decided by the team on 2026-10-20. CodeDNA becomes a **platform**: an analysis
core, downloadable **language plugins**, the **CodeDNA IDE**, and a
**platform website** from which users download the IDE and plugins (plugins
can also be installed from inside the IDE).

Priorities and limits:

- Java remains the only analysed language until Milestone 5 is complete;
  D-013 still holds for *what is analysed*, but the architecture now
  anticipates more languages through plugins.
- The research contribution (Milestones 4–5) has priority; product work runs
  alongside (mainly Student C) and must not delay it.
- The title, brief and examiners' expectations describe a research tool. The
  wider scope **needs supervisor approval** before the final proposal, and the
  report must state clearly which parts are research and which are product.

## D-018 — Language-plugin interface

The core (Git changes, graph model, impact traversal, selection, history, ML,
calibration, CLI/API) stays language-neutral. Everything language-specific
moves behind one interface, provided by each plugin:

| Capability | Java plugin today |
|------------|-------------------|
| `file_patterns` / `applies_to(path)` | `*.java` |
| `parse(source) -> declarations` | `java_analysis.parser` |
| `extract_references(source)` + `resolve(...) -> edges/unresolved` | `dependency_graph.references` / `builder` |
| `discover_tests(commit) -> tests` | `test_mapping.discovery` |
| `run_tests(...)` / `import_coverage(...)` (opt-in, D-014) | `test_mapping.maven` |

Plugins are ordinary Python packages (e.g. `codedna-java`) registered under
the entry-point group `codedna.languages`, discovered with
`importlib.metadata.entry_points`. The plugin API is versioned
(`api_version`); the core refuses plugins with an incompatible major version.
Every plugin must emit the shared graph schema (node IDs, edge kinds,
confirmed/heuristic labels, unresolved list) — that is what keeps the IDE,
selection and ML language-neutral.

Refactor plan: first add the interface and registry in
`backend/codedna/plugins/`, then move the Java code behind it **without
behaviour change** (the existing test suite is the check). The Java plugin
stays in this repository until the catalogue (Milestone 7) exists.
Files no installed plugin handles are reported as `unanalysed_changes`, as
today.

## D-019 — CodeDNA IDE built on Eclipse Theia, talking to a local API

Writing an editor from scratch is out of reach for an FYP, so "our own IDE"
means a **branded IDE built on an existing open-source IDE framework**.

- **Chosen: Eclipse Theia.** It is designed for building custom IDE products,
  runs as a desktop app (Electron) or in a browser, and supports VS Code
  extensions, so Java editing can use existing open-source Java extensions.
- Rejected: a fork of VS Code (Code - OSS) — heavy to build and to keep up to
  date; Electron + Monaco from scratch — file tree, terminal, debugging and
  Java support would all have to be rebuilt.
- The IDE talks to the Python core through a **local API** (FastAPI, from the
  brief's stack) on `127.0.0.1` only, returning the same JSON as the CLI. No
  accounts or authentication (brief: no auth infrastructure).
- CodeDNA features appear as IDE panels/views (TypeScript, Cytoscape.js for
  the graph). The Milestone 6 React dashboard is replaced by these panels.

*To verify before starting Milestone 6:* current Theia version, its licence
(and the licences of any bundled Java extensions) for redistribution, Node.js
requirements, and build size/time on student laptops.

## D-020 — Platform website and plugin distribution

- **Website:** a static site (e.g. GitHub Pages) — no server, no accounts, no
  payments. It hosts IDE downloads, docs and the plugin catalogue page.
- **Catalogue:** one versioned JSON index (plugin id, name, versions,
  supported core/plugin API versions, download URL, SHA-256 checksum,
  licence, source repository). The website renders it; the IDE reads it.
  Plugin files are published as GitHub Release assets.
- **In-app installation** (and the website) must follow these rules, because
  plugins are code that runs with the user's permissions:
  - install only from the official catalogue URL, never arbitrary URLs;
  - verify the SHA-256 checksum before installing (pip hash-checking mode);
  - pin exact versions; updates are explicit, never silent;
  - show the plugin's licence and source link before installing;
  - plugins are installed into CodeDNA's own Python environment, not the
    user's system Python.

These are ordinary distribution-hygiene rules, not security research, so the
project stays within Path A. Code signing can be added later if time allows.

## D-021 — SQLite (standard library) for history and results

One database file per studied repository, via Python's built-in `sqlite3`:
no server, works on every laptop, easy to copy alongside an experiment.
Tables: `commits` (first-parent, `seq` = chronological index),
`changed_files` (numstat, renames as delete + add), `test_results` (per
commit, test class and source; a failure in any source wins when merged),
`meta`. No author names or e-mails are stored. PostgreSQL only if a real need
appears.

## D-022 — scikit-learn for the first models

Logistic regression (standardised features, balanced class weights) and
`HistGradientBoostingClassifier` (balanced class weights) from scikit-learn
cover the brief's "logistic regression baseline" and "gradient-boosted
model" without adding XGBoost or LightGBM; switch only if experiments show a
clear benefit. scikit-learn is an optional extra (`pip install -e ".[ml]"`,
also in `dev`) so analysis-only users do not need it. Fixed `random_state`
for reproducibility. No LLMs are used for prediction.

## D-023 — Feature, leakage and evaluation protocol

- Unit of prediction: (commit, test class) for commits with stored results;
  label = failed or error at that commit; skipped tests are excluded.
- History features use only results of *earlier* commits: the per-test state
  is updated after a commit's rows are emitted. The test's duration at the
  commit itself is used only as evaluation cost (APFDc, budgets).
- Features: change size (files, Java files, test files, lines ±), test file
  changed, structural (`impact`: reachable, distance, confirmed-only path),
  history (past runs/failures, failure rate, failures in last 5 runs, failed
  last run, commits since last failure, mean/last duration, co-failures with
  the files changed now).
- Split: chronological by commit, 60 % train / 20 % validation / 20 % test
  (validation reserved for calibration in Milestone 5). No shuffling.
- Metrics per commit with ≥ 1 failing test, averaged: APFD, APFDc, recall at
  25 % and 50 % of total time, time to first failure; per split: PR-AUC and
  Brier score for ML models.
- Fewer than 10 failing commits → warning; results are not to be reported as
  findings until enough real failures exist.

## D-024 — Plugin refactor, step 1

The `LanguagePlugin` protocol, the registry and a built-in `JavaPlugin` are in
`backend/codedna/plugins/`. The Java code itself stays in `java_analysis`,
`dependency_graph`, `test_mapping` for now; `JavaPlugin` is the entry point
the core uses (impact, selection, history collection). Moving it into a
separately installable `codedna-java` distribution waits for the plugin
catalogue (Milestone 7), to avoid packaging work before it is needed.
`analyze` still decides "is Java" by file suffix, which matches the plugin's
`handles()`.

## D-025 — Calibration methods and where they are fitted

Platt scaling (logistic regression on the log-odds of the raw score) and
isotonic regression, both from scikit-learn, plus "none" as the control.
Calibrators are fitted **only on the validation split** (the 20 % after
training, D-023) and evaluated on the test split, so calibration never sees
test data. Quality is reported as Brier score, Expected Calibration Error
(10 equal-width bins) and reliability-diagram bins. With few failures in the
validation split isotonic regression can overfit; Platt is the safer default
for small data, isotonic for larger — the experiment reports both.

## D-026 — Risk-aware selection and fallback rules

- Order candidates by `p / estimated cost` (cost = historical mean duration;
  tests without history get the median), always keep changed test classes.
- Time budget = fraction of the *estimated* total time.
- Estimated skip risk = `1 − Π(1 − p)` over skipped tests, i.e. the chance at
  least one skipped test fails, **assuming independent failures**; the
  experiment compares it with the observed miss rate rather than trusting it.
- Fallback (B9): broaden beyond the budget until skip risk ≤ target; go
  straight to retest-all when non-Java files changed or more than half of
  the candidate tests have no history. Every decision lists its reasons.
- No guarantee of catching all regressions is claimed.

## D-027 — Experiment protocol for Milestone 5

`history experiment` trains one model on train (B7), calibrates on
validation (B8/B9), trains a change-features-only model (B6), and compares
B0, B4, B6–B9 on test commits using real outcomes and durations. B4 here is
the `dep_reachable` / `test_file_changed` feature proxy for static
dependency selection. Sweeps: budget 10–100 % for B8, risk target
0.01–0.3 for B9. Ablations retrain without the change, structural or history
feature group. Every report carries a dataset SHA-256, seed and package
versions; results for the thesis go to `experiments/results/` together with
the database version and the exact command.

## D-028 — Local API: FastAPI on loopback with a session token

The IDE needs the core's results over a stable interface; FastAPI (from the
brief's stack) gives typed request models (Pydantic), JSON errors and
OpenAPI docs the TypeScript side can be generated from. It is an optional
extra (`[api]`: `fastapi`, `uvicorn`; tests also use `httpx`).

A server on localhost can be reached by any local process and, indirectly,
by web pages in the user's browser, so:

- `codedna serve` refuses non-loopback addresses;
- a random per-session token (32 bytes, `secrets.token_urlsafe`) is
  required in `X-CodeDNA-Token` on every endpoint except `/api/health`,
  compared in constant time; the IDE can supply its own via
  `CODEDNA_API_TOKEN` (environment, not a command-line argument visible in
  process lists);
- requests whose `Host` header is not `127.0.0.1`, `localhost` or `[::1]`
  are rejected (DNS-rebinding defence); no CORS headers are sent, so
  browsers cannot attach the custom header cross-site;
- `/api/run-tests` executes project code, so it needs the server started
  with `--allow-build` **and** `"allow_build": true` in the request.

No user accounts or remote access — consistent with the brief's "no
authentication infrastructure" and Path A scope.

## D-029 — IDE skeleton: Theia 1.76.0, Electron, backend proxy

Verified on 2026-10-19 (npm registry): `@theia/core`, `@theia/electron`,
`@theia/cli` **1.76.0**, licence **EPL-2.0 OR GPL-2.0-only WITH
Classpath-exception-2.0**; Electron **42.8.1** (peer dependency). Theia's
contributor docs recommend Node ≥ 24 for developing Theia itself; the app
builds and runs with Node 22.21 here. Windows needs Visual Studio Build Tools
("Desktop development with C++") for native modules (node-pty, keytar,
drivelist, ffmpeg). All Theia packages are pinned to the exact version.

*Licence note (needs human review):* EPL-2.0 is weak copyleft — using and
redistributing unmodified Theia packages is fine, but modified EPL files must
stay available under EPL. CodeDNA itself has no licence file yet; choose one
before publishing the IDE or website.

Layout: `ide/` npm workspace with `codedna-extension` (Theia extension,
TypeScript/React) and `electron-app` (the product). The extension's backend
module starts `codedna serve` on a free loopback port with a random token in
`CODEDNA_API_TOKEN` and proxies the views' JSON-RPC calls to it, so the token
never reaches the renderer and no CORS is needed. The executable is `codedna`
on PATH or `CODEDNA_EXECUTABLE`. Views only analyse; no build is triggered.

Build note: if `NODE_USE_SYSTEM_CA=1` is set and the Windows store lacks
ISRG Root X2, Node rejects `artifacts.electronjs.org` (Let's Encrypt "Root
YE" chain); build with that variable unset.

## D-030 — Visual design: CodeDNA Dark + glass shell

Requested by the team (2026-10-20): reference shots of dark, translucent
IDE/assistant UIs, the team's FreshOptimizer app, and the apple-design rules.

- A registered Theia colour theme `codedna-dark` (default via the app's
  `preferences` config, because Theia's built-in preference default would
  otherwise win) with translucent surfaces, a teal → indigo accent and a calm
  syntax palette.
- A shell stylesheet, active only with that theme, that turns the side
  panels, editor and bottom panel into floating glass cards over an aurora
  wallpaper (gaps via transparent borders that Lumino's layout measures),
  an icon rail with an accent pill + bar, pill tabs, heavier glass for menus
  and overlays.
- FreshOptimizer's vocabulary in the views: inset cards, uppercase
  micro-labels, tinted chips, accent-gradient primary buttons with
  press-scale; heuristic links always dashed + warning colour.
- Accessibility: `prefers-reduced-transparency` → solid surfaces,
  `prefers-reduced-motion` → no press/scale/progress animation,
  `prefers-contrast: more` → strong borders and full-contrast text. Other
  themes keep Theia's normal layout; the views stay readable in them.

## D-031 — Newcomer-friendly wording and a calmer look (revises D-030)

Decided by the team on 2026-10-20: anyone, including beginners, should be
able to use CodeDNA, and the teal/indigo glow look read as generic "AI".
**The analysis and its results are unchanged** — only presentation.

- **Look:** neutral graphite surfaces, warm off-white text, no accent hue,
  no glows, gradients, wallpaper or blur. Colour only carries meaning:
  green = new, amber = changed / "likely", red = removed / error. Primary
  buttons are plain off-white with dark text. Muted, warm syntax colours.
  Panels still float as solid cards with small gaps.
- **Type:** Geist and Geist Mono (SIL OFL 1.1, bundled via
  `@fontsource-variable/*`) instead of Inter / system fonts; sentence-case
  headings, no uppercase micro-labels.
- **Wording:** views renamed "Changes" and "Tests to run"; a "Compare"
  picker (My last commit / My last 5 commits / Choose commits…) instead of
  raw Base/Head boxes, shared by both views; "Show changes" and "Suggest
  tests"; New / Changed / Removed and Direct / Likely instead of
  added/modified/deleted and confirmed/heuristic (a "Likely" link is still
  never presented as certain); a one-sentence summary on top; the core's
  reasons and warnings rephrased as sentences (unknown messages shown
  as-is); errors say what to do, with the raw details one click away; a
  three-step first-run guide.
- **Motion** (Emil Kowalski's rules): 160 ms press scale with a strong
  ease-out, transitions on specific properties only, results fade in with a
  30 ms stagger, hover effects only for real pointers, no animation on
  keyboard actions, reduced motion → opacity only.
- **Layout:** names get a full row (chip + details underneath) and wrap
  after dots instead of mid-word; side panels start at 24 % width for new
  users (Theia default 19 %).
- **Theme cache:** Theia restores parsed themes from IndexedDB after
  extensions register theirs, which would bring back an old version of the
  theme after an update; the theme is registered again on start-up.

## D-032 — RTPTorrent as the primary study dataset, imported without builds

Approved by the team on 2026-10-21 (supervisor confirmation still
recommended). RTPTorrent **v1.1** (Zenodo record 4046180, published
2020-09-23, CC BY 4.0, `rtp-torrent-v11.zip`, md5
`1f7fa822b0cf155bd007a94d1a24a336`; v1.1 replaced the `deeplearning4j`
repository with a complete fork). Cite Mattis et al., MSR 2020,
doi:10.1145/3379597.3387458.

Why: real CI outcomes at test-class level (CodeDNA's selection granularity),
linked to commits, with bare Git repositories included — every CodeDNA
feature (changes, graph, impact) can be computed **without building or
executing third-party code**.

Import rules (`history import-rtptorrent`, `test_history/rtptorrent.py`):

- Column names from the dataset's readme and files:
  `tr_all_built_commits.csv` = `tr_job_id, git_commit_id` (n:m);
  `<project>.csv` = `travisJobId, testName, index, duration, count,
  failures, errors, skipped`.
- Tested commit of a job = the single tip of its built commits
  (`git merge-base --independent`); jobs with commits missing from the
  repository, several tips, or no built-commit row are skipped and counted.
- History order = order of the first job that tested each commit (Travis job
  ids increase over time); change base = first-parent ancestor just before the
  whole push, so multi-commit pushes are fully covered.
- One result row per (commit, test class, job) with source `travis:<job>`;
  failed if failures + errors > 0, skipped if every method skipped; negative
  durations clamped to 0 and counted. Failures in any job win (D-021).
- A job may run the same class several times (e.g. once per Maven module);
  those runs are **merged first** (counts and durations summed), so a
  failure in any run counts. Without this, HikariCP's import lost failures
  in 63 (job, class) pairs and showed 101 instead of 123 failing commits.
- The core accepts **bare repositories** (`resolve_repository`), since all
  analysis reads Git objects.

Known limitations: RTPTorrent ends in 2016; its projects use Maven, Gradle and
Buck, so `run-tests` cannot reproduce them — we only use the recorded
outcomes. Jobs of one build ran concurrently; CodeDNA aggregates per commit
and orders commits by their first job, which never lets a later build inform
an earlier one.

## D-033 — Pin tree-sitter below 0.26 (native crash)

Found on 2026-10-21 while computing structural features on RTPTorrent's
HikariCP history: `tree-sitter` **0.26.0** (newest release, 2026-06-30) crashes
the Python process with an access violation while CodeDNA walks the tree of an
ordinary 15 KB file (`HikariConfig.java`); just before the crash a node
reports position row −1, i.e. it reads freed memory. Reproduced in a separate
process, without forced garbage collection, on Python 3.12.0 and 3.14.0.
With **0.25.2** the same file parses 30× without error, and all 3,413
distinct Java file versions in HikariCP's history (112,530 declarations)
parse without a crash.

Decision: `tree-sitter>=0.25,<0.26` in `pyproject.toml`, plus a test that
fails if 0.26 is installed. Re-check when a newer release appears, using the
same whole-history parse as the acceptance test.

## D-034 — Study protocol: six projects, five seeds, separated fallback triggers

After the first HikariCP run showed that B9's gain came mostly from the
non-Java → retest-all rule, the experiment adds two variants:

- **B9r** — calibrated model, time budget, fallback **only** from the
  estimated skip risk (unfamiliar-change rule off);
- **B9n** — calibrated model, time budget plus **only** the unfamiliar-change
  rule (non-Java files changed, or mostly history-less tests), no risk target.

B9 keeps both. RQ4 (does *risk-based* fallback help?) is answered by B8 vs
B9r; B9n measures the simple rule on its own.

Study (`scripts/run_study.py`): RTPTorrent projects HikariCP, LittleProxy,
jade4j, jsprit, wicket-bootstrap, dynjs; seeds 0–4; gradient boosting,
isotonic calibration, budget 0.5, risk target 0.05 (defaults). The feature
dataset is built once per project and reused for all seeds
(`--from-dataset` / `dataset.csv`). Seeds only change model randomness — the
chronological split is fixed — so seed spread shows model stability, not
data variation. Results are reported per project and as an **unweighted mean
of project means** (each project counts once, so a large project cannot
dominate). wicket-bootstrap (~40 % failing commits) is reported but its
behaviour should be discussed separately.

## D-035 — Cost-matched comparisons, bootstrap intervals, shared parse cache

The six-project study showed that a fallback policy "wins" partly by running
more tests. From now on every fallback policy (B9, B9r, B9n) is also
compared with the calibrated selector **B8 at the budget that spends the same
real test time**, found by bisection over the budget (`models/uncertainty.py`).
That paired difference — not the default-setting comparison — answers RQ4.

Uncertainty: percentile bootstrap over **test commits** (1,000 resamples per
experiment, seed = run seed), with paired resampling for differences.
Studies add a **stratified paired bootstrap** across projects (2,000
resamples): commits are resampled within each project and project
differences are averaged with equal weight. Limitations: commits are treated
as independent (neighbouring commits are correlated, so intervals are
somewhat optimistic), and the split is fixed, so intervals do not cover
"another time period". Experiments keep compact per-commit outcomes
(`per_commit`: time ratio, failing, missed) so pooled analyses need no rerun.

Revision (2026-10-22): intervals that used one seed's outcomes were
misleading where policies are seed-sensitive (wicket-bootstrap: the matched
difference is ≈0 in seed 0 and ≈+0.9 in seeds 1–4). Study intervals now use a
**hierarchical bootstrap** — pick a seed, then resample that seed's test
commits — and point estimates are means over seeds; pooled results state how
many projects contribute to each metric.

Data quality (RTPTorrent): graylog2-server and jOOQ have no failing commits
in their test periods because their CI logs record far fewer test classes
there (~1 and ~7 per commit); they are kept but contribute no recall/safety.

Performance: structural features now share one bounded LRU parse cache
(4,000 blobs) across all commits of a dataset instead of re-parsing every
file for every commit; LittleProxy's dataset is byte-identical and builds in
145 s instead of 267 s.

## D-036 — Hybrid policy B10: rules order, calibrated stopping

The eleven-project study showed two things: simple rules (recent failures
first, then shortest) order tests better than the learned models, while the
calibrated model gives the most reliable *risk estimates*. B10 combines the
two: tests are taken in the B3 rule order, and the calibrated probabilities
only decide where to stop — tests are added until the estimated skip risk is
at most the risk target (default 0.05). There is no time budget and no
unfamiliar-change rule, so the comparison isolates "rules + calibrated
stopping".

`decide()` gains an optional `order` argument (changed test classes are
still always run). The experiment adds B3 (rules order, plain budget) and
B10, and compares B10 at the same real test time with both B8 (calibrated
ML at a matched budget) and B3 (rules at a matched budget). Cost-matched
entries now name their baseline (`baseline`, `baseline_budget`,
`baseline_same_time`); the study runner lists every comparison as
policy − baseline. A risk-target sweep for B10 is part of `risk_coverage`.

Result (study11, 2026-10-23): at the same test time B10 − B3 safety +0.075
[−0.001, 0.202] and B10 − B8 +0.075 [−0.055, 0.224] (n = 9); B10 is never
lower than B3 in safety on any project, and with target 0.05 its observed
miss rate stays within the target on 10 of 11 projects. See
`experiments/results/study11-2026-10-21/FINDINGS.md`.

## D-037 — Class-weight check as a stricter RQ3 baseline

The study's models use balanced class weights, which inflate raw
probabilities, so "uncalibrated vs calibrated" partly measures undoing that
choice. `MLRanker` gains a `class_weight` option (default unchanged,
"balanced"), and `class_weight_check()` with `scripts/class_weight_check.py`
trains the full model with and without class weights on each study dataset
(test split, 5 seeds) and reports PR-AUC, raw and calibrated Brier/ECE, and
the commit-level skip-risk gap of the 50 % budget policy.

Result (study11, same 9 projects): ECE balanced raw 0.118, balanced
isotonic 0.021, unweighted raw 0.030, unweighted isotonic 0.021; skip-risk
gap 0.306 / 0.067 / 0.054 / 0.071; PR-AUC balanced 0.138, unweighted 0.103.
Most of the calibration gain undoes class weighting; calibration adds a clear
further gain only on the high-failure projects (wicket-bootstrap,
HikariCP). The thesis claim is reworded accordingly: reliable risk
estimates, not calibration per se. The selection experiments keep the
balanced, calibrated model.

Addendum (2026-10-24): the check also runs B10 per variant with raw and
isotonic probabilities, compared with B3 at the same time. On the same 9
projects, B10 with the unweighted raw model stops too early (time 0.26,
safety 0.46, observed miss 4.4 % vs estimated 1.8 %, target held on 6 of
9); with the unweighted model calibrated it matches the study's model
(time 0.35, safety 0.68, observed 3.1 %, target held on 8 of 9). Low ECE
does not imply a usable stopping rule; held-out calibration does. The claim
is reworded again: calibration matters for decisions, not for the ECE drop.


## D-038 — Reproducible figures from saved study reports

The next Milestone 4–5 reporting step uses `scripts/make_study_figures.py`.
The exporter reads saved `summary.json`, `class-weight-summary.json`, and
per-project experiment/class-weight seed reports. It does not rerun models,
rebuild feature datasets, or change study results. Matplotlib (`plots` extra,
`>=3.8`) is optional tooling for PNG and vector SVG figures, not a core
analysis dependency; data-only export uses the standard library.

Budget curves average seeds within each project, then weight projects equally.
Undefined recall and safety remain null rather than becoming zero. Raw and
calibrated variants use common available project cohorts, with contributing
project counts shown. Target attainment is counted per project rather than
inferred from the pooled miss rate. The saved hierarchical bootstrap supplies
the cost-matched intervals; no intervals are invented from seed spread.

`figure-data.json` records the plotted numbers. `manifest.json` records SHA-256
hashes of every read report, every generated artifact, and the exporter source,
plus tool versions, so report figures can be tied to a specific saved snapshot.
The exporter rejects missing seed reports, inconsistent budget grids, differing
risk targets and empty comparison cohorts rather than silently dropping runs.


## D-039 — Pre-specified project-disjoint transfer check

The owner requested testing whether a model trained on one project works on
another (2026-10-24), with permission to download/rebuild the missing feature
CSVs and history databases. The primary transfer study uses HikariCP,
LittleProxy, jade4j and wicket-bootstrap, chosen before inspecting transfer
results because they have recorded failures and fit the available disk space.
All twelve source-target directions and four within-project controls use seeds
0–4, gradient boosting, balanced weights, source-only isotonic calibration,
a 50% time budget and the B10 5% risk target. See CROSS_PROJECT_PROTOCOL.md.

For cross-project runs, source history is conservatively restricted to a
chronological prefix older than the target test window's earliest Git committer
date. The source's oldest 60% trains the model and next 20% calibrates it;
source labels never come from the target. Target testing uses its latest 20%,
with previously recorded target history available as features. Git dates are a
proxy for time, not CI completion timestamps. This does not test a repository
with no prior history. Missing or single-class calibration is reported as
unavailable rather than relabelled raw probabilities.

RTPTorrent v1.1 is fetched by HTTP byte ranges because a full 5 GB download
would exceed the available space. Only four project CSVs, their bare Git
repositories and the shared job-to-commit map are needed. The map is filtered
while streaming to the selected projects' job IDs. Each ZIP entry is CRC-checked;
SHA-256 hashes and transformations are recorded. The whole-archive MD5 is
explicitly not claimed verified by this partial download. No project is built.
Rebuilt feature tables must match the original study's dataset hashes before
running transfer models. Raw data, databases and feature CSVs remain git-ignored.

D-039 results (2026-10-24): all 80 raw runs completed. Source calibration is
available in nine transfer directions; seven meet the observed 5% miss target.
HikariCP to LittleProxy misses every recorded failing target commit (9.43% miss),
and LittleProxy to wicket-bootstrap misses at least one failure on 16.46% of
commits. Wicket-bootstrap transfers spend 97.84–99.96% of full test time. Source
calibration worsens target ECE in six of nine directions; raw ML ordering beats
rules in three of twelve. Some pairs help, but general model/risk transfer is
not established. Target-project validation remains necessary before trusting
transferred risk. No production default or IDE behaviour changed. Full evidence:
`experiments/results/cross-project-2026-10-24/FINDINGS.md`.


## D-040 — Fixed history-order stopping extension

The owner asked to complete the interrupted research/IDE work, deferring more
languages. The original scope explicitly includes calibration, fallback,
explanations and baseline evaluation, so this extends Milestones 5–6 directly.
See RELATED_WORK_COMPARISON.md and DANTE_B10_PROTOCOL.md. An initial independent
transition proxy is archived with its source snapshot; after retrieving the
DANTE artifact, a separately fixed second run implements a closer history-only
CCH score adaptation. No author source is copied, no full-DANTE reproduction or
universal-ordering claim is made, and no model/threshold tuning uses the results.
Both are exploratory extensions on previously inspected windows. GitHub auth
failed, so protocols were fixed locally with hashes rather than publicly pushed.

## D-041 — Target evidence gate and explicit selected execution

Live risk uses a separately audited 15-feature GB/isotonic variant: 50% older
training, 25% calibration, 25% independent audit. It excludes structural and
co-failure features that cannot be reproduced from a CSV alone for a live commit.
The frozen engineering gate requires a one-sided 95% Wilson miss-rate upper
bound <= target, >=10 failing audit commits and >=90% failing-test recall.
It also checks target ancestry, fresh BASE history, complete current-test audit
coverage and supported changes. These checks yield an evidence screen, not a
formal safety guarantee; periodic full-suite audits remain required.

`risk-select`, `/api/risk-select` and `/api/run-selection` expose core JSON.
The IDE starts with builds disabled; explicit user confirmation enables the
server and each request. Selection is recomputed at immutable revisions, then
only validated discovered test-class filters are passed to Maven in an isolated
export. Empty selections execute nothing. No pickled model is loaded and no new
core dependency is added. Full details: JAVA_WORKFLOW.md.

D-041 boundary: shared audited fitting/gating stays in `selection.live` and
`selection.validation`. Java live feature construction is in `plugins.java_live`,
reached through the existing Java plugin’s additive optional `risk_select` hook.
New selected execution also goes through the plugin runner. This preserves the
language boundary without implementing a second language or changing API major.

D-040 final result: all four calibrated observed miss targets hold with the closer
history-score adapter; matched-time pooled safety +0.0460 [-0.0500, 0.2806] and
recall -0.0056 [-0.0420, 0.0312] do not establish a benefit. Raw stopping violates
the target on two projects. Retain recent-failure order for live use; preserve
both exploratory studies rather than selecting the more favourable adapter.
Evidence: `experiments/results/dante-history-check-2026-10-24/FINDINGS.md`.

## D-042 — Rolling-origin evidence study with pre-fixed rules

Step 2 of the final plan. Rules in `docs/EVIDENCE_STUDY_PROTOCOL.md` were
committed before results: five rolling blocks over each project's later half,
the unchanged D-041 live fit/gate refitted on all prior commits per block, B10
versus same-order budget B3 at matched time, and a separate gate check. Only
RTPTorrent projects outside study11 count towards the verdict; study11
projects are replication only. Runner: `scripts/run_rolling_evidence.py`.

First run (four inspected projects only, data host unreachable): safety
difference -0.0032 [-0.0362, 0.0294], "no meaningful difference"; gate
accepted 7 of 19 fitted blocks with observed commit miss 0.0043 versus 0.0274
on rejected blocks. The confirmatory verdict stays open until new projects are
added. Evidence: `experiments/results/rolling-evidence-2026-10-24/FINDINGS.md`.

## D-043 — Impact graph view (Cytoscape.js)

The IDE gets an "Impact graph" main-area view (Ctrl/Cmd+Alt+G): changed code →
parts that may be affected → related tests. The core adds `explanation_graph`
to the impact JSON (`impact_analysis.explanation_graph`): nodes by category
(changed / impacted / test / unanalysed), only the edges on each node's
shortest explanation path, each labelled confirmed or heuristic; non-Java
changes are `unresolved` nodes with no edges. The view only draws this JSON
(no analysis in TypeScript); clicking a node highlights its path and lists each
step with its evidence line. Edge ids include the edge kind
(`A->B:uses`), since two types can be linked by several kinds. A list under
the graph selects the same paths from the keyboard. New frontend dependency: `cytoscape@3.30.4`
(MIT, pinned) plus `@types/cytoscape` for compilation; named for this view in
Milestone 6. Additive JSON field, so no API version change.

## D-044 — Java editing, progress notifications and Windows installer

Step 4 of the final plan. (1) Java editing: add `@theia/plugin-ext` and
`@theia/plugin-ext-vscode` 1.76.0 and two pinned Open VSX extensions,
`vscode.java` 1.95.3 (grammar) and `redhat.java` 1.36.0 win32-x64 (language
server with embedded JRE). These are editor features only; CodeDNA analysis
stays in the Python core. They are build-time downloads at fixed versions, not
CodeDNA plugins, so the D-020 catalogue rule does not apply; record their
SHA-256 after the first verified build. (2) Long core calls show a Theia
progress notification with stage text and elapsed seconds; no fake
percentages, because the core reports no intermediate steps. (3)
`electron-builder` 26.0.12 builds a per-user NSIS installer for the IDE. The
Python core is not bundled yet; bundling it (e.g. PyInstaller) is left open.

## D-045 — Multi-module Maven and Gradle test discovery and runs

`test_mapping.build.detect_build` reads the committed build files only: Maven
`<modules>` recursively plus each module's own Surefire `<includes>` and
`<excludes>` (parent inheritance and profiles are not resolved; modules inside
profiles and module paths leaving the repository are warned about, not
followed), or Gradle `include` statements in `settings.gradle(.kts)`, also
spread over several lines (syntactic, comments removed, with a warning). Discovery records each
test's module and whether the build runs it by default. Gradle runs every class
in a module's `src/test/java`, so no name filter applies. `run-tests` runs the
Maven reactor from the root (`failIfNoSpecifiedTests=false` across modules) or
the system `gradle` (never the repository's `gradlew`) with our own init script.
That script sets `ignoreFailures` and `failOnNoMatchingTests=false`. Reports
are collected from every module. Per-test JaCoCo coverage stays single-module
Maven and is refused otherwise rather than guessed.

## D-046 — Uncommitted changes through a WORKTREE snapshot commit

Every command and API call that takes a revision also accepts `WORKTREE`, and
the IDE compare picker offers "My uncommitted changes" (`HEAD` → `WORKTREE`).
`git_analysis.git.snapshot_worktree` copies the real index to a temporary
file (HEAD's tree when there is no index; the copy keeps the stat cache, so
unchanged files are not hashed again), runs `git add -A` into it (so `.gitignore` applies), and writes the tree plus
an unreferenced commit with fixed identity and dates. The same working tree
therefore always gives the same SHA. The real index, refs and files are not
touched; the extra objects are ordinary unreachable objects that `git gc`
removes. Because `git add` would run a configured clean/process filter
program, repositories whose attributes name any filter driver (such as LFS)
are refused with an explanation, and so are edits inside a submodule whose
commit did not change (the parent records only that commit, so the edits
would vanish silently). Every later step reuses the commit-based
pipeline unchanged.

## D-047 — Static website and validated catalogue index

`website/` is plain HTML/CSS plus one small script that renders
`catalogue/index.json`. There is no framework, build step, account or tracking,
so GitHub Pages can serve the folder as is. The page only displays the
catalogue; it never installs anything. The catalogue schema (version 1)
follows D-020. `codedna.plugins.catalogue` rejects unpinned versions, missing
or malformed SHA-256 checksums, and any download URL outside the official
repository's GitHub Releases. The future in-app plugin manager reuses that
validator. Java is listed as a built-in version with no download until it
moves into its own package. No licence is claimed because the repository has
none yet.

## D-048 — Plugin install and remove through the official catalogue

`codedna.plugins.manager` and `codedna plugins catalogue | install ID VERSION
--yes | remove ID --yes`. The catalogue is fetched only from the fixed
official URL and validated (D-047); the caller names a plugin and an exact
version and cannot pass a URL or file. Catalogue entries with a download gain
a pip `package` name. Install order: compatibility (plugin API major), explicit
confirmation (the CLI first prints the plugin's licence and source, even with
`--yes`), wheel file name must be that package at that exact version, download (50 MB
cap), SHA-256 compared before pip sees the file, then `python -m pip install
--no-index --no-deps` of that one wheel into CodeDNA's own interpreter. Remove
needs confirmation, refuses built-ins and plugins that are not installed, and
runs `pip uninstall`. Installed plugins are found by the existing entry-point
registry, which reports a plugin that fails to load instead of breaking the
core. `--no-deps` means a plugin must not need extra packages. Tests are
offline: fakes for the rule checks plus one real pip install and removal of a
generated wheel in a throwaway virtual environment.

Limit: the repository is private, so the official catalogue URL (GitHub Pages)
and release assets are not publicly downloadable yet. Until a public host is
chosen, install works only against a reachable copy, which the code does not
allow by design.

## D-049 — History replay from experiment reports

The IDE's **History replay** view (`Ctrl+Shift+Alt+R`) plays a project's test
split back commit by commit: per commit, the test time each policy spent and
whether it skipped a failing test, with running totals, against the risk
target. It is built only from saved experiment reports, so it shows the
study's own measurements and never retrains or runs code.

- `codedna.models.replay.replay_timeline` turns a report into a timeline. A
  compact report (the `per_commit` triples every report keeps) gives time and
  miss curves; a report written with `history experiment --replay`
  (`run_experiment(trace=True)`) also records each commit's SHA, test names,
  suite seconds, and per policy the tests run, seconds, missed test names,
  estimated skip risk and fallback flag. The trace uses the experiment's own
  policy functions; `--replay` leaves every other part of the report
  unchanged (tested).
- Shown policies: run everything (B0), dependency only (B4), simple rules at
  CodeDNA's mean time (B3 at the cost-matched budget from `cost_matched`), and
  CodeDNA (B10). All running totals are computed in Python; the view only
  indexes them (no analysis in TypeScript, D-019).
- Every timeline is checked against the report's `policies` summary and the
  result is shown (`checks`, `notes`). All 55 study11 reports match.
  `replay_overview` (mean over seeds, then over projects) reproduces the
  study's `summary.json` pooled means.
- `scripts/record_replays.py` re-runs the experiment with `trace=True` for
  projects whose `dataset.csv` is present and keeps a trace only if its
  `policies` and `per_commit` equal the study report. Traces for hikaricp,
  jade4j, littleproxy and wicket-bootstrap (seed 0) are committed in
  `experiments/results/replay-2026-10-25/`; the other seven projects replay
  from their compact reports until their datasets are rebuilt.
- API: `POST /api/replay`, `/api/replay/sources`, `/api/replay/overview`
  (token-protected, read-only). `start.bat` sets `CODEDNA_REPLAY_FOLDERS` to
  the study folders in the checkout.

Limitation: the replay is a simulation on recorded history (what each policy
would have run, given the recorded test outcomes), not a live run; it cannot
show effects such as tests that would have behaved differently if run alone.

## D-050 — Must-run (pinned) tests policy

Some tests must run on every change whatever the risk estimate says (smoke
tests, release checks, later security checks). A project lists them in
`.codedna/policy.toml` as `[[must_run]]` groups with `tests` (test IDs or
case-sensitive `fnmatch` patterns) and an optional `reason`; the CLI
(`--must-run PATTERN`, repeatable) and API (`must_run`) add patterns for one
request. Implemented in the language-neutral `codedna.selection.policy`.

- **Read from BASE**, never from HEAD or the working tree, so a change (for
  example from an AI agent) cannot loosen its own checks. A change that edits
  the policy is analysed under the old one, with a warning.
- **Fail safe:** a malformed or unreadable policy, or a failing add-on rule,
  pins every test. A pattern matching no test is reported as a warning.
- **Only adds tests.** `select_tests` adds pinned tests to every strategy;
  `risk-select` passes them to `decide(always=...)`, which counts them as run
  when computing the skip risk. The audit gate is evaluated without pins;
  pins can only lower the miss rate it measures.
- **Research numbers unchanged:** `compare_strategies` and all experiments
  ignore the policy.
- **Extension hook:** add-on rules register in the `codedna.policies` entry-point
  group (zero-argument factory returning an object with `name` and
  `pinned(context) -> {test_id: reason}`; `context` has repo, BASE, HEAD, test
  IDs and changed paths). Rules come only from installed packages, never from
  the analysed repository. This is the place for the post-defence security
  rules (for example "changes under `auth/` pin the security suite").

Limitation: patterns match test IDs as the plugin reports them (Java: test
classes); a pinned test that Surefire does not run by default stays outside
the universe and is not added.

## D-051 — Impact graph: package lanes, highlighted change, depth controls

On a real project (HikariCP) a typical one-commit impact graph has about 60
nodes in 9 packages; the D-043 drawing (one breadth-first tree) was too
crowded to read. Changes:

- **Core:** `explanation_graph` adds each node's `package` (`""` = default
  package, `null` for files outside the graph), a `packages` list (label,
  whether it holds changed code, counts per category) and a `summary` of
  counts. Additive JSON fields; no API version change.
- **IDE layout:** a "lane" layout (`graph-layout.ts`, pure placement of core
  data): one horizontal band per package, columns by the core's `distance`
  (links from the change), bands with changed code first. Package boxes are
  drawn when the change spans more than one package. Cytoscape's force layout
  (`cose`) was tried with package boxes and produced overlapping boxes on the
  HikariCP graphs, so it was rejected.
- **Changed code stands out:** larger, outlined nodes with bold labels;
  package boxes that contain changed code have a coloured border. A one-line
  summary gives the counts per category and packages.
- **Controls:** "Follow" (all links, or 1/2/3 links from the change) and
  "Confirmed links only" (drops heuristic links; depth is set separately) pass the existing `max_depth` / `confirmed_only` options
  to the core; no filtering happens in TypeScript.

Checked by rendering the compiled layout with Cytoscape in headless Chromium
on HikariCP commits 086bf183 (13 nodes, 4 packages) and 93c71780 (63 nodes,
9 packages); not yet checked inside the packaged Windows app.

## D-052 — Real-project demo, two discovery fixes and what the live gate does on public CI history

**Demo.** `scripts/make_hikaricp_demo.py DEST` clones HikariCP from the
RTPTorrent bare repository, checks out a real tested change (default
dd7c9a9a, chosen from `--list` for the demonstration, not as evidence),
writes `.codedna/history.csv` with the study's rows for tested commits on
BASE's first-parent line up to BASE (nothing from the change or later), and
`.codedna/demo.json` with CodeDNA's dependency selection and risk
recommendation next to RTPTorrent's CI record of the change. `.codedna/` is
added to `.git/info/exclude`. No project code is built or run.

**Discovery fixes found on the way** (both made the test universe smaller
than what CI ran, so even "run everything" missed failures):

- build-helper-maven-plugin `add-test-source` folders and a module's own
  `<testSourceDirectory>` are now test roots (`BuildLayout.test_roots`).
  HikariCP 2.x shares `hikaricp-common/src/test/java` between two modules;
  before the fix 2 of its 21 CI test classes were discovered. A folder shared
  by several modules belongs to the first in sorted order. Property
  (`${...}`) paths and paths outside the repository are reported, not followed.
- Surefire include/exclude patterns ending in `.class` are treated like
  `.java` (Surefire's rule). wicket-bootstrap's core module includes
  `**/*.class`; before the fix none of its tests ran by default.

Study numbers are unaffected: the study uses RTPTorrent's recorded tests,
not discovery.

**Live gate on public CI history (finding, not changed).** HikariCP has 89
consecutive tested first-parent pairs whose CI run failed; every Java-only one
was run through `risk-select` with history up to its BASE, as were the failing
Java-only changes on wicket-bootstrap's master line. The D-041 gate never
accepted. HikariCP's audit windows always contain a commit
whose CI record lacks a current test class (for example TestMetrics missing
at 8a20f775), and the gate requires complete outcomes. Dropping incomplete
commits would leave too few failing audit commits and the gate still refuses
(upper bound above target, recall below 90%). wicket-bootstrap's CI records
cover 41 of the 72 test classes its build runs. The gate behaves as designed:
without complete evidence it recommends the full suite. The gate was not
loosened for the demo; the calibrated stopping is shown in the History replay
view instead. A product change for this (for example, always run tests
without history and validate the rest) would need its own pre-registered
check.

## D-053 — Record full-suite runs as project history ("record as you go")

**Why.** D-052 showed the live gate (D-041) never turns on from public CI
records, because they are incomplete. A project using CodeDNA can build
complete records itself: every whole-suite run CodeDNA starts is a full,
labelled outcome of one commit.

**What.** `test_history/recording.py` `record_run(repo, run, expected_tests)`
stores the run in `.codedna/history.db` (first-parent history mined again,
source `codedna-run`) and rebuilds `.codedna/history.csv` from it
(`structural=False`; the live predictor does not use those features). The
CSV is written to a `.partial` file and then replaced. Used by
`/api/run-selection` (IDE) when nothing was skipped, and by
`codedna history record --repo PATH RESULTS` for a saved run, whose expected
tests are the classes the build runs by default at that commit.

**Refused, with a reason, never guessed:**

- selected (partial) runs: a skipped test's outcome is unknown and the gate
  audits complete outcomes;
- runs where an expected test class has no result (the build stopped early);
- commits not on HEAD's first-parent line (working-tree snapshots, other
  branches);
- a `history.csv` CodeDNA did not write (no database, or its SHA-256 differs
  from the one stored after the last recording), e.g. the HikariCP demo or a
  hand-edited file.

A second run of the same commit replaces that commit's earlier result.

**Git hygiene.** A self-ignoring `.codedna/.gitignore` (only if none exists)
ignores `runs/` and the history files; a committed `policy.toml` is
unaffected. `snapshot_worktree` also leaves those paths out, for run folders
created before the ignore file existed.

**What it does not do.** It does not loosen the gate. With the default 5%
target the gate needs at least 10 failure-bearing audit commits (the last 25%
of recorded commits) and a Wilson upper bound at or under 5%, so in practice
a few hundred recorded commits. A synthetic check (240 commits, one test failing every
third commit, scratch script only, not evidence) reached `validated_history`
from recorded runs alone; real projects will differ.

## D-054 — Java as a separate plugin package (`codedna-java`) and the plugin manager view

The Java implementation moves out of the core into `plugins/codedna-java`, a
separate distribution registered under the `codedna.languages` entry point
(`java = codedna_java:JavaPlugin`). This finishes the refactor planned in
D-018/D-024: the core has no built-in language and no Tree-sitter dependency.

- **What moved:** the Java parser and change mapping (`java_analysis`), the
  graph builder and reference walker, build-layout detection, JUnit
  discovery, Surefire/JaCoCo parsers, the Maven/Gradle runner, the Java plugin
  class and the live risk adapter (`plugins.java_live` → `codedna_java.live`).
- **What stays in the core:** the shared schemas (`dependency_graph.model`,
  `test_mapping.results` including `TestClassResult` and `ReportError`), the
  generic `BoundedParseCache`, and everything language-neutral.
- **One way in:** `codedna.plugins.languages` (`require`, `analyze_changes`,
  `build_graph`, `discover_tests`, `type_kinds`). Plugin API 1.1 adds two
  optional members, `type_kinds` and `attach_declarations`, read with
  `getattr`, so a 1.0 plugin still loads (its changes stay at file level).
  A plugin with a newer minor than the core is refused, because it may rely
  on members the core lacks. A test imports every core module with `codedna_java` and
  `tree_sitter` blocked.
- **Without the Java plugin** `analyze` still lists changed files and warns
  which `.java` files were not analysed. Commands that need a graph or test
  discovery fail with `PluginMissingError`, which names the install command
  (CLI exit 1, API 400). Nothing guesses.
- **JSON is unchanged:** `is_java` and `java` stay in the change report so the
  IDE and saved reports keep working. Renaming them would be a format change
  for a later decision.
- **Installing:** developers and `start.bat` run
  `pip install -e plugins/codedna-java` (start.bat does it once for an
  existing `.venv`). The catalogue lists Java as bundled (`builtin: true`,
  package `codedna-java`, API 1.1); no wheel is published while the repository
  is private (D-048). This is not a D-020 catalogue install: the plugin's
  code comes from the checked-out repository itself, like `pip install -e
  backend`, and its dependencies (Tree-sitter) are resolved from PyPI by pip
  exactly as the core's own are, pinned by `pyproject.toml` ranges but not by
  hash. D-020's checksum and exact-version rules apply to wheels fetched from
  the catalogue, which is the only path that downloads plugin code.
- **Manager:** catalogue wheels are installed with `--no-deps`. Before the
  real install the manager runs a `pip install --dry-run --no-index` of the
  verified wheel; if the plugin's dependencies are not already installed it
  stops there, names them and changes nothing. After installing it still runs
  `pip check`: a fresh install with unmet dependencies is uninstalled again,
  but an update is never rolled back by uninstalling, because that would also
  remove the version that worked; the error says so. Python cannot reload a
  plugin module safely, so an update or removal returns
  `restart_required: true` and the IDE asks for a restart of the CodeDNA
  server. An unreachable catalogue is a normal `CatalogueError`, not a crash.
- **Review fixes (PR #16):** an API 1.0 plugin reports no type kinds, so
  impact marks its changed files as not analysed and `dependency` selection
  falls back to retest-all instead of silently picking no tests; a plugin
  without `attach_declarations` adds a warning; `require` only shows load
  problems of the requested language's entry point; the catalogue endpoint
  adds `compatible` to each version so the IDE no longer re-implements the
  API check; and `dependency` selection reuses the change report instead of
  analysing the commits twice.
- **API and IDE:** `GET /api/plugins/catalogue`, `POST /api/plugins/install`
  and `POST /api/plugins/remove`. Install and remove need `"confirm": true`,
  and versions must be exact. The IDE's "Language plugins" view shows
  installed plugins and load problems, and the catalogue with licence and
  source. Install, update and remove each ask for confirmation. The view
  sends only a plugin id and version; the URL and checksum come from the
  official catalogue inside the core.
- **Research reproducibility:** `docs/EVIDENCE_STUDY_PROTOCOL.md` is frozen
  and keeps its old module name (`plugins.java_live`). The fingerprint list in
  `scripts/run_rolling_evidence.py` now points at
  `plugins/codedna-java/codedna_java/live.py`, so a rolling-evidence run
  started before this change will not resume after it; restart it instead.
  The module's code is unchanged.

## D-055 — Bundle the Python core in the Windows desktop installer

The desktop installer must support analysis without a separate Python/CodeDNA
installation. A build-only `desktop` extra pins PyInstaller 6.22.0; the installed
analysis runtime gains no new dependency. `scripts/build_desktop_core.py` builds
a console-mode, one-directory executable with the Java parser, SQLite history,
ML/calibration and local API dependencies. The IDE hides its console and keeps
the existing stdout/token handshake and explicit build-consent flow.

Electron Builder copies that generated folder into `resources/core`. The main
entry chooses an explicit `CODEDNA_EXECUTABLE` override first, then the bundled
core, then `codedna` on PATH for development. Generated executables and caches
are ignored. Each bundle records Python/package versions and SHA-256 hashes of
its files; no saved datasets, credentials, historical model files or developer
configuration are included intentionally. Git and project build tools remain
external prerequisites. Packaging stays Windows x64; this is not a cross-platform
installer or an in-app plugin installation mechanism.

## D-056 — Confirmatory preparation skips unused graph work, guards data identity

The existing `structural=False` extraction path is exposed as an explicit
`prepare_confirmatory --no-structural` option, with full extraction still the
default. Before preparing new projects, all 70,485 existing four-project rows
were checked to retain identical identities, labels, durations and the 15 live
model inputs. Only the three unused graph columns are omitted. Experimental
rules/model/gate remain D-042; this does not change the statistical analysis.

Preparation records project names, extraction option and extractor SHA-256 and
refuses mixed or unfingerprinted resume data. The CLI refuses previously
inspected projects and output-name collisions. The dated preparation note fixes
the full nine-project set before fresh results. No old report is overwritten.

The one-time `continue_confirmatory.py --wait` command reuses an existing active
raw-subset producer. It verifies complete-cache hashes before importing and
never starts a network download. A `raw_dir` option separates shared raw inputs
from projected CSV/DB outputs. Queue-time code/library/equivalence fingerprints,
a single-worker OS lock, a full-set check and local phase status guard unattended
execution. No paid AI calls, notifications or recurring scheduler are used.

## D-057 — Saved runs join the one recorded history (finishing the Codex draft)

**Why.** Codex (2026-10-25, laptop) drafted `test_history/project.py`: list the
saved runs under `.codedna/runs/`, import a clone's `results.json`, and build
history from saved runs. The draft had no tests and three problems against
D-053: it wrote a second history (`.codedna/history-exports/…`) and then
overwrote `.codedna/history.csv`, so the next D-053 recording refused that
file as foreign; it excluded every run with a non-zero build exit code,
which drops all runs with a failing test (Maven/Gradle exit 1 then), so the
history would have held passes only; and it edited `.git/info/exclude` in the
user's repository.

**What.** One history, one set of rules. `recording.py` gains
`record_runs(repo, [(run, expected_tests), …])` (one rebuild for many runs,
oldest first; `record_run` is now the one-run case) and `refusal()`, the D-053
rules on their own. `project.py` uses them:

- `list_runs` shows every saved run, newest first, with `candidate` and the
  refusal reason (unreadable file, another repository, off the first-parent
  line, an expected test class without a result);
- `record_saved_runs` adds every eligible saved run to `.codedna/history.db`
  and rebuilds `history.csv` like D-053 (a CSV CodeDNA did not write is still
  left unchanged); recording twice is idempotent;
- `import_run` copies a clone's `results.json` into `.codedna/runs/` bound to
  this repository, only if its commit exists here, keeping the source path and
  SHA-256 in `record.json`; it does not record by itself;
- `run_detail` returns one saved run and its log files.

Expected tests per commit come from the language plugin
(`plugins.languages.discover_tests`, D-054). Failing runs are evidence;
partial runs never are. API: `/api/project-history` (read-only),
`/record`, `/import`, `/run`. Outputs stay ignored through
`.codedna/.gitignore` (D-053); nothing is written inside `.git`.

**IDE.** A **Project history** view (Ctrl+Shift+Alt+H, or "Open project
history" in Tests to run) lists the saved runs with their reasons, opens a
run's outcomes and logs, imports a `results.json` and adds saved runs to the
history. Codex drafted the view on the laptop; it was moved onto this API (no
BASE picker: eligibility follows the current branch, as in D-053).

**Not decided here.** The gate (D-041) still decides whether the history is
good enough.


**Fix (with D-059).** Once `.codedna/.gitignore` existed, a worktree
snapshot failed: Git refuses an `:(exclude)` pathspec that names an ignored
path. The snapshot now excludes only outputs that `git ls-files` actually
lists (outputs from before the ignore file existed).

## D-058 — Graph precision check and four resolution fixes

(D-054 to D-057 are taken by open branches: the `codedna-java` plugin split
and the project-history fixes.)

**Check (M2).** 160 dependency edges (40 confirmed + 40 heuristic from each
of HikariCP a4d93f4f and LittleProxy 70edbe1c, seed 0) were labelled against
the source: 160 correct, so precision is 1.00 with a 95 % Wilson interval of
[0.954, 1.00] for each label. Missed references were found by sorting every
unresolved name into groups. Method, data and the AI-made labels (to be
spot-checked by a student) are in
`experiments/results/graph-precision-2026-10-25/`; tools are
`scripts/sample_graph_edges.py` and `scripts/score_graph_sample.py`.

**Fixes to D-010 found by the check** (`dependency_graph/builder.py`):

- `var` is skipped. It infers a local variable's type and names no type; it
  was 260 of HikariCP's 546 unresolved references.
- `java.lang` is the full list of public top-level types in JDK 21 (107
  names) instead of 42, so names like `ClassNotFoundException` count as
  external, not unresolved.
- Static imports bring member types: `import static a.T.*` makes `T`'s
  member types candidates on the same footing as type wildcards (heuristic);
  `import static a.T.Nested` resolves `Nested` like a single-type import
  (confirmed).
- Member types inherited from repository supertypes are in scope, after the
  type's own members, at each enclosing level, transitively; generic
  arguments are ignored and cycles stop. These edges are heuristic because
  hiding rules and library supertypes are not checked. As in Java, an
  inherited member type shadows a `java.lang` name. HikariCP's
  `SQLExceptionOverride.Override` was silently resolved to the JDK annotation
  before.

Review follow-ups (same PR): a single static import of a library name
(`import static java.util.Map.Entry`) can shadow a same-package type, so that
edge is heuristic, not confirmed; and the `java.lang` names added after Java 8
(`Record`, `Module`, `StackWalker`, ...) give way to a single wildcard-imported
repository type of the same name (heuristic), because on Java 8 that is what
the code means.

Effect: the unresolved rate goes from 0.264 to 0.139 (HikariCP) and from
0.103 to 0.070 (LittleProxy), and dependency edges go from 668 to 676 and
from 479 to 502. Structural features (`dep_reachable`, `dep_distance`,
`dep_confirmed`) of datasets built from now on can differ slightly from the
saved study datasets. The saved study results and the live risk gate are
unaffected: the gate uses no structural features (D-041). Local classes stay
unresolved by design (D-009).

## D-059 — Test brake for AI coding agents (`codedna mcp`)

**What.** `codedna mcp` is a Model Context Protocol server on stdin/stdout,
so coding agents (Claude Code, Cursor, Codex and others) can ask CodeDNA
before they say a change is done. Tools:

- `codedna_plan_tests` — the tests that must run for BASE..HEAD (default:
  uncommitted changes), a reason for each, and the skip risk. It is the live
  recommendation (D-041) with the must-run policy (D-050): without validated
  history it lists every test, so the brake never skips on a guess.
- `codedna_impact` — the impact report with confirmed and heuristic links
  apart and the changed files CodeDNA cannot analyse.
- `codedna_check` — runs the planned tests and gives one verdict: `passed`,
  `blocked` (a listed test failed), `incomplete` (a listed test has no
  result, the build exited with an error or timed out, or every listed test
  was skipped), `nothing_to_run` (validated history says no test needs to
  run) or `no_tests` (the build runs no tests). A whole-suite check
  of a commit on the first-parent line is recorded as history (D-053);
  uncommitted states never are.

**Consent.** `plan` and `impact` read Git objects only. `check` executes the
project's build, so it is listed only when the person starts the server with
`--allow-build --repo PATH`, and it then serves that one repository whatever
path the agent sends. `brake.check` itself also refuses to run without
`allow_build=True`, so other callers cannot skip the consent. An agent cannot turn it on (same rule as D-014).

**No dependency.** Only the part of MCP that tools need is implemented
(`initialize` with version negotiation, `ping`, `tools/list`, `tools/call`;
newline-delimited JSON-RPC 2.0), so the core needs no MCP SDK. Errors in a
tool come back as tool results with `isError`, protocol errors as JSON-RPC
errors. Logs go to stderr.

**Limits.** The verdict covers the listed test classes only; `passed` with
unvalidated history means the whole suite passed, not that the change is
correct. The brake is language-neutral and uses the installed language
plugin (Java first). Whether agents finish with fewer broken changes when
they use it is a research question still to be measured (planned SWE-bench
Java study); no result is claimed here.

## D-060 — Python as the second language plugin (`codedna-python`), several plugins per repository

`plugins/codedna-python` adds Python (`python = codedna_python:PythonPlugin`,
plugin API 1.1). It uses only the standard library's `ast`, so it adds no
dependency. The core now runs every installed plugin on one repository, so a
mixed Java + Python project is analysed by both at once.

- **Rule conflict, on purpose:** AGENTS.md says no second language plugin
  before Milestone 5 is complete. The owners approved the remaining-work plan
  (step 8) with this plugin in it on 2026-10-25, ahead of that milestone. The
  Java research track is untouched: `codedna_java/live.py`, the study scripts
  and the frozen protocol do not change, and nothing Java selects changes in
  a repository without Python files.
- **IDs and graph (shared schema):** every Python ID starts with `py:` so it
  cannot collide with Java's. A module is `type:py:<module>` (kind `module`,
  parent `file:<path>`), a class `type:py:<module>.<Class>`, a function
  `member:py:<module>#f()`, a method `member:py:<module>.<Class>#m()`. Module
  names come from the path, with a leading `src/` dropped. Type kinds are
  `module` and `class`, so a changed function seeds its module and a changed
  method seeds its class. The test unit is the test module (`py:tests.test_x`),
  as the JUnit class is for Java.
- **Edges:** `imports` (module → module), `uses` (module → class imported by
  name; module → each class it defines, so importers of the module reach the
  class) and `extends`. *Confirmed* when the import names a repository
  module exactly (relative imports resolved first) or the base class is in
  the same module or imported by name; *heuristic* when a module matches only
  as a dotted suffix (the source root is not the repository root or `src/`)
  or a base class only by a unique simple name. Standard-library and other
  outside imports are counted as external. A relative import above the
  top-level package and an ambiguous base name are kept as unresolved.
  Dynamic imports, `sys.path` changes, re-exports through `__init__` and
  attribute use of imported modules are not followed.
- **Change mapping:** same algorithm and result shape as Java (D-008), stored
  in `ChangedFile.analysis`; `ChangedFile.language` names the plugin that
  handled each file (null at `--level file` or when no plugin handles it).
  `code_changed` compares `ast.dump`, so comment/formatting-only edits are
  ignored; docstrings count as code. A syntax error (judged by the Python
  that runs CodeDNA, 3.11+) leaves the file unresolved, and impact treats the
  whole file as changed.
- **No cross-language edges.** A Python change never reaches Java tests
  through the graph, and the other way round. To stay safe, selection treats
  a changed file of a language with **no tests in the universe** as
  unanalysed, so it falls back to retest-all exactly like a build file
  (a Python release script in a Java project keeps today's behaviour).
  `non_java="ignore"` keeps its name and now means "unanalysed files".
- **Discovery:** pytest's own settings from the root config (`pytest.ini`, `.pytest.ini`,
  `pyproject.toml`, `tox.ini`, `setup.cfg`, in pytest's order):
  `python_files`, `python_classes`, `python_functions`, `testpaths` and
  `norecursedirs`. Tests outside `testpaths` are listed but do not run by
  default. `unittest.TestCase` subclasses count. Inherited test methods from
  other files and conftest hooks are not seen.
- **Running (only with `--allow-build`, D-014):** the commit is exported and
  `python -m pytest -p no:cacheprovider --junitxml=…` runs there, with the
  interpreter from `--python` (default `python3`/`python` on PATH, which needs
  pytest and the project's dependencies; CodeDNA installs nothing into it).
  Selected tests are passed as file paths after `--`, never as expressions.
  Results are kept per test module. Per-test coverage stays Java-only.
- **Several plugins at once (`codedna.plugins.languages`):** `build_graph`,
  `discover_tests` and impact join every plugin's graph and tests
  (`union_graphs`, `CombinedDiscovery`; JSON adds `language` per test and a
  `languages` summary). `run_tests` splits selected tests by the plugin that
  discovered them; with one language it runs exactly as before, with several
  each writes to `OUTPUT_DIR/<language>` and the results are joined into
  `OUTPUT_DIR/results.json` (tool e.g. `maven+pytest`). Plugins ignore run
  options meant for others. A shared parse cache is safe: Python keys its
  entries `("py", blob, path)`.
- **Risk-based selection stays Java-only (D-041):** in a mixed repository its
  universe includes the Python tests, and any Python change makes it fall
  back to the full suite.
- **Installing:** `start.bat`, CI and the developer setup install both plugins;
  the catalogue lists Python as bundled. The PyInstaller desktop bundle (PR
  #17) has to include `codedna_python` too.

## D-061 — Predictive Test Selection baseline (B11)

(D-060 is not used; the agent brake study is D-062.)

**Why.** The closest prior work, Predictive Test Selection at Facebook
(Machalica et al., ICSE-SEIP 2019), also uses a learned model, a holdout and
a recall target. The report's difference from it (a per-commit risk target
checked per project, against aggregate recall targets) had only been argued.

**What.** `codedna.selection.pts` implements the published rule: tests with
an uncalibrated score at or above a score cutoff, plus the N highest-scoring
tests, plus changed test classes. The cutoffs are tuned on the calibration
window to test recall 0.95 and change recall 0.999. `scripts/run_pts_check.py`
runs it inside the rolling-origin design without editing the scripts frozen
by the confirmatory job. The rules were fixed in
`docs/PTS_BASELINE_PROTOCOL.md` before the run.

**Result (exploratory, four inspected projects).** B10 minus time-matched B11
safety is +0.007 [−0.063, 0.091]: inconclusive. B10 is cheaper and safer on
HikariCP (where B11 cannot be made as cheap); B11 is safer on LittleProxy.
B11 kept its test-recall target on 2 of 4 projects and its change-recall
target on none; B10 kept its miss target on 3 of 4. Details:
`experiments/results/pts-check-2026-10-25/FINDINGS.md`.

**Not changed.** B11 is a research baseline only. The live product keeps
B10 with the D-041 gate.

## D-062 — Agent brake study on public SWE-bench Java patches

**What.** An offline check of the brake (D-059) on agent patches that are
already public: the SWE-bench Multilingual Java instances (gson, druid,
lucene, lombok, RxJava, javaparser) of every submission in
`SWE-bench/experiments` (14 mini-SWE-agent runs with different models). For
each patch the harness applied, CodeDNA computes the test plan for the
agent's change and checks whether it contains the benchmark test classes the
harness saw fail. Protocol fixed before results:
[AGENT_BRAKE_STUDY_PROTOCOL.md](AGENT_BRAKE_STUDY_PROTOCOL.md); tool:
`scripts/swebench_brake_study.py`.

**Why this way.** It needs no paid API and no build: patches and harness
reports are public, and CodeDNA reads Git objects only (`eval.sh` is parsed
as text, never run). Paying for our own agent runs is out of budget.

**What it cannot show.** Whether agents end with fewer broken changes when
they use the brake; the harness runs only the benchmark's test files, so
other regressions are unknown. Downloaded data stays out of Git
(`experiments/datasets/swebench-multilingual/`); every file's SHA-256 and
the `SWE-bench/experiments` commit are recorded.

## D-063 — Conformal risk control for the stopping threshold (B12, B12f)

**Why.** B10's fixed 5 % estimated risk assumes independent failures and a
correct probability level, and the D-041 gate that guards it is a
hand-picked rule. Conformal risk control (Angelopoulos et al., ICLR 2024)
picks the threshold from held-out outcomes with a bound that needs only
exchangeability.

**What.** `codedna.selection.conformal.threshold` chooses the largest
stopping threshold λ on a fixed grid with `(n·R̂ + 1)/(n + 1) ≤ α`, scanning
upwards and stopping at the first violation. `scripts/run_crc_check.py`
tunes it on `fit_audited`'s audit window inside the rolling-origin design.
B12 uses every audit commit (`docs/CRC_STOP_PROTOCOL.md`). B12f
(`--conditional`, `docs/CRC_CONDITIONAL_PROTOCOL.md`) uses only failing audit
commits, so the bound is on misses among failing commits. Both protocols
were committed before their runs.

**Result (exploratory, four inspected projects).** B12 saved 36 % of test
time against the gated product. Its target (5 % of *all* commits) still
let half of HikariCP's failing commits be missed: the target was too weak,
not the method. B12f kept commit safety ≥ 0.95 on 4 of 4 projects (B10 2 of
4). It used 4.7 % [4.0, 5.4] less time than the gated product, almost all on
wicket-bootstrap. Details are in `experiments/results/crc-check-2026-10-26/`
and `crc-conditional-2026-10-26/`.

**Not changed yet.** The live product keeps B10 with the D-041 gate.
Replacing the gate with B12f needs the confirmatory datasets first;
`run_crc_check.py --conditional` is ready to rerun on them.

**Prior art.** An open-source project applies conformal risk control to the
share of missed failing tests on the industrial Westermo dataset
(github.com/l-k-1-2/Predictive-test-selection). B12f differs in its loss
(commit-level, conditional on failure), its data (open Java CI history) and
its use as the brake's rule. It is not claimed as the first use of
conformal risk control for test selection.

## D-064 — JUnit 3 tests and moved Gradle test folders in discovery

**What.** Test discovery (`test_mapping/discovery.py`) also finds JUnit 3
style tests: in a class that extends `junit.framework.TestCase` (imported,
by wildcard, or fully qualified), or whose repository ancestor does, every
`public void test*()` method without parameters, not static or abstract, is
a test method. The same holds below a repository base class annotated
`@TestMethodProviders` with a JUnit 3 method provider (randomizedtesting,
which Lucene uses). Such classes get framework `junit3` unless their file
uses JUnit 4/5 annotations. The Gradle layout (`test_mapping/build.py`) reads
`test.java.srcDirs = [...]`, `+= [...]` and `test.java.srcDir(...)` from the
`.gradle` scripts: in a module's own build script for that module, in any
other script for every module, with a warning that the reading is syntactic.

**Why.** The agent brake study (D-062) showed that every catch the plan
missed was a test CodeDNA did not see, not a wrong selection: gson's tests
before 2023 are JUnit 3, and Lucene's tests use JUnit 3 naming under
`src/test` set by a shared Gradle script, so discovery found 1 to 20 gson
classes and no Lucene classes. Surefire and Gradle run these tests by
default, so the plan and the full-suite fallback (D-041) left them out.

**Limits.** Syntactic, like the rest of discovery: a `TestCase` imported
from elsewhere under the same name is not told apart from a same-package
class of that name; Gradle source sets set programmatically or inside
`sourceSets { test { java { ... } } }` blocks are not read. Results computed
before this change (the D-062 primary run records its CodeDNA commit) keep
the old discovery; the study's follow-up run is labelled as post hoc.

## D-065 — Windows-safe RTPTorrent ancestry queries and audited resume

An RTPTorrent push can list enough commits to exceed Windows CreateProcess's
command-line limit. `_tips` previously sent every SHA to `merge-base
--independent`, unlike the importer's other bounded Git requests. Windows raised
FileNotFoundError/WinError 206; the Git wrapper incorrectly reported missing Git.

Keep the normal independent-tip query up to the existing 400-SHA limit. Above
that limit, pass the revisions on stdin to `rev-list --parents --stdin`. Among
the supplied candidates, exactly those never named as a parent in the complete
reachable ancestry are independent. Walking all ancestors covers gaps between
candidate commits and merge branches. This preserves the tested-commit rule;
naively calculating independent tips separately per chunk would not preserve it.
The Git wrapper distinguishes oversized requests, missing Git, missing working
directories and other operating-system failures, retaining the original cause.

Offline regression tests cover a real 1,000-commit import with bounded argv,
branch/merge/gapped/duplicate inputs compared to Git's ordinary independent-tip
query, and Windows/POSIX launch-error classification. No dependency or statistical
rule changes. The fixed feature generator, model, gate, project set and protocol
remain unchanged.

The failed output folder and frozen sources remain intact. Resume into
`experiments/datasets/confirmatory-windowsfix-2026-10-26` with results destined for
`experiments/results/rolling-evidence-confirmatory-windowsfix-2026-10-26`.
Copy and SHA-256-verify the three completed DB/CSV pairs (Cloudify, DSpace,
SonarQube), configuration and feature-equivalence proof. `resume-provenance.json`
records parent fingerprints, the two source changes and every reused file hash;
`resume-code-change.patch` records the technical fix. The continuation creates new
fingerprints and re-verifies the existing raw cache. No downloads or completed
feature extractions are repeated. Partial Sling data is not treated as complete.

Written by Codex on the laptop as "D-054"; renumbered because D-054 is the
Java plugin split and D-058 to D-064 are taken by open PRs.

## D-066 — Use discovered test files and discard obsolete IDE responses

Recommended-test links now request the existing `/api/tests` JSON at the
selection's immutable HEAD and open its reported file relative to the canonical
repository. The frontend caches discovery for that selection. It never derives
a source path from a package name: module layouts, Gradle projects, custom file
locations and workspaces opened below the Git root must work. Missing locations
produce an explanation rather than opening an invented path.

A comparison/input generation prevents late recommendation, execution and file
lookup responses from restoring results for an obsolete comparison, including
switching away and back. Completed older executions remain available in Project
History; the view reports where to find them. Consent is checked again against
the same selection before execution. Build wording now covers Maven and Gradle.

Eight offline Node tests exercise the actual TypeScript widget methods, with a
throwaway Git repository and mocked core/progress/editor boundaries. They cover
file navigation, missing paths, obsolete responses, pending consent and duplicate
analysis clicks. CI runs them after extension compilation. No new dependency,
core API, language plugin, model or fixed-study change is introduced.


Written by Codex on the laptop as "D-053" (renumbered, see D-065).

## D-067 - Nine-project follow-ups reviewed; keep the default conservative

All four laptop follow-ups completed on 2026-10-26; artifacts and findings
are in `experiments/results/*confirmatory-perf-2026-10-26/` (report 4.12).
B12f meets 95% conditional commit safety on 8/9 projects (required 7),
saves 16.20 recorded-time points against the gated product, but lowers
mean safety by 1.79 points [0.84, 2.72]. Cloudify safety is 87.84%.
The nine-project addendum was not committed before the runs, and no
pre-specified pooled absolute-safety lower interval was recorded. Do not
retroactively call these prerequisites satisfied. B10 remains the default;
CRC remains opt-in under D-068. B13f is exploratory, not a replacement default.
The PTS cost match failed and is reported as a trade-off, not equal-time evidence.
No threshold, model or result has been retuned to improve this verdict.

## D-068 — Conformal stop (B12f) as an opt-in method in the live brake

The live risk recommendation and the agent brake take `method="b10"`
(default, unchanged: calibrated stop behind the D-041 Wilson gate) or
`method="crc"` (failure-conditional conformal risk control, D-063). With
`crc` the product uses the same 50/25/25 fit/calibrate/audit split; on the
**failing** audit commits it picks the largest stopping value whose
corrected bound `(n·R̂ + 1)/(n + 1)` stays at or below the risk target. The
function is `selection/conformal.failing_commit_threshold`, and
`scripts/run_crc_check.py` now uses the same `conformal.stopper`, so the
study and the product pick the same threshold on the same data (tested).

Fewer than 19 failing audit commits, or no value passing the bound, gives
the full suite with that reason. Must-run policy tests are always kept. The
response carries `risk.method`, and for `crc` a `risk.conformal` block
(`alpha`, `threshold`, `failing_audit_commits`, `audit_miss_rate`,
`corrected_bound`) plus the note that the bound assumes exchangeable failing
commits and is not a guarantee.

Exposed as `codedna risk-select --method`, `POST /api/risk` `method`, and the
MCP tools' `method` argument. `scripts/demo_brake_end_to_end.py` shows the
whole path over MCP on a synthetic history: a partial plan, `blocked` for a
breaking edit and `passed` for a harmless one (real Maven, tested under
`--run-maven`).

**Why opt-in:** whether B12f becomes the default is the pre-registered
decision D-067, which waits for the B12f result on the nine confirmatory
projects (7-of-9 rule). Until then the default stays B10 and no report text
may say the product uses conformal control by default. No new dependency.

## D-069 - Preserve risk decisions while removing quadratic prefix work

The target-only risk loop now binary-searches the shortest acceptable
ordered prefix. Adding candidates cannot increase skip risk. Each probe
calls the original risk arithmetic in the same probability order, preserving
floating-point threshold behavior, pins, budgets, partial/duplicate orders,
fallbacks and report fields. This uses O(log n) full risk scans rather than
one per selected test. There is no model or protocol change.
Exact randomized/boundary parity tests and a complete real-project replay
passed. The 4,000-test benchmark improved from 6.62s to 0.030s (221x for
that benchmark only). The study-worktree full suite passed 405 tests with
Maven and zero skips; integration validation is recorded separately.
Original outputs stay immutable. B13's seven reused reports are byte-identical,
and new folders disclose both fingerprints and portable source snapshots.
The result paths are marked -text to preserve their SHA-256 bytes on every OS.

## D-070 - Return the structural plan and fail safe across brake languages

The brake returns `structural_plan`, the existing dependency selection at the
risk recommendation's immutable BASE/HEAD, labelled `structural only, no
probability`. Requested extra pins stay in must_run, not in this independent
structural view. Required tests are the union of the risk plan, structural
selection and existing policy pins. Structural evidence never authorizes
skipping without validated project history. When this broadens a partial
risk plan, the original model estimate is explicitly labelled a conservative
bound; selecting every discovered test makes skip risk zero. This does not
turn the model estimate into a guarantee of real-world safety.

The brake detects the installed test language rather than assuming Java.
Python has no risk selector, so it returns an unvalidated full-suite plan
with a clear reason and no invented probability. Mixed test universes also
fall back to all discovered tests because there is no joint validated
selector. Unknown plugins, invalid methods and invalid targets still error.
`check` dispatches through the existing language-neutral runner, splitting
Java/Python tests and joining actual results. Consent, immutable snapshots,
missing-result verdicts and history recording remain enforced. The direct
Python API accepts an explicit python_command; MCP keeps server-side build
consent and cannot grant it from tool arguments.

No dependency, model, research threshold, or CRC default changes. Regression
coverage uses temporary Git repositories and includes real passing/failing
pytest runs, mixed fake-Maven/real-pytest execution, MCP, pins, immutable
snapshots, and conservative partial-plan estimates. Main's prior merge and
post-pull validation are separate from validation of this feature branch.

D-070 validation also caught the old two-test demo assuming that a dependency
test could be skipped. The demo now adds a genuinely unrelated third test;
required dependency tests remain in the plan. The history is still labelled
synthetic. MCP startup accepts --python for the project's interpreter, without
changing build consent or allowing an agent to override the interpreter.

Final D-070 local validation: `python -m pytest --run-maven -q`:
554 passed, zero failed/skipped, 1953.04s; 1 existing warning(s).
Runtime and test file hashes match the recorded final-source snapshot.
The branch remains local because automatic approval review rejected the
private-source push without explicit payload/destination approval. No new
feature PR or CI result is claimed. Main's separately verified #21 merge
and the preserved stash remain unchanged.


## D-071 - Complete the existing blueprint before extra features (2026-10-27)

Owner asks to finish existing functionality and verify the AI brake, while
deferring the proposed replay/UI/audit features until a later explicit request.
PR #22 is already merged (45821b4); historical publication restrictions are
superseded by the completed authorized merge.

Fix the false pass when a required test was skipped; reject such incomplete
evidence before it replaces complete history. Preserve genuine failing-run
evidence (including Maven/Gradle exit 1). Share Python discovery parses by
optional capability, preserving legacy plugins. Prefer a project's .venv for
pytest; a frozen core without an external interpreter gives an actionable error.
Complete the existing read-only PR demo and add a tiny CRC CLI regression smoke.
Keep B10 default, CRC opt-in, and all existing research outputs unchanged.
Do not implement a Java risk model for Python without validation.

The completion ledger records tests and remaining manual/external evidence.
No clean-PC, student labeling, supervisor approval or public hosting is claimed
without the corresponding evidence.

D-071 verification: 562 passed, zero failed/skipped, Maven/Gradle enabled,
1513.49 s. IDE compile plus 8 workflow and 3 runtime tests passed. Frozen-core
MCP Python passing/blocked and missing-interpreter cases passed. All 1,389
packaged core hashes verified; new installer SHA-256
e1120f72bca9fedd61e4f459eb70790a946ee543fd88684b4b49a1b430228200.
Java diagnostics and mixed-language IDE analysis verified; clean-PC installation
remains separate. See RELEASE_VALIDATION_2026-10-27.json.


## D-072 - Evidence clarity and visible language acquisition (2026-10-27)

After the D-071 batch passed 562 tests, the owner requested brake improvements,
a detailed website blueprint, website plugin acquisition and visible Language
plugins in Extensions on next launch. Research findings are not rewritten.
The brake exposes method-specific audit semantics without changing selection
rules or the B10 default. Proposed fresh evaluation is in BRAKE_IMPROVEMENT_PLAN.

Use one Theia Extensions container holding the existing plugin widget, restored
for fresh/saved layouts without stealing editor focus. Installed languages are
displayed before a slow/offline catalogue finishes. No new marketplace library.
Website acquisition reads the existing catalogue, offers only pinned official
optional wheel URLs with full hashes/commands, and distinguishes bundled and
unpublished releases. Public hosting/anonymous downloads and frozen-desktop
optional installation remain release gates, not invented as complete.

The clean-PC verifier and supervisor review pack prepare external checks; they
do not constitute clean-machine provenance, human labels or supervisor approval.

D-072 startup acceptance exposed sensitivity to a slow cold core during heavy
local builds. The IDE now allows a bounded 60-second announcement (formerly
15 seconds); tests simulate a successful 20-second handshake and verify an
unresponsive child is killed after the deadline. Fourteen IDE workflow tests
pass, alongside thirteen website acquisition tests. Final packaging/validation
remains separate from these focused results.


## D-073 - Test and history UX without weaker risk checks (2026-10-27)

The owner found test-class names unexplained, saved-history clicks unclear,
and the research replay placeholder easy to mistake for an entered path.
Render the existing runner's individual cases (with an older-result fallback),
keep raw risk refusal reasons and explain chronological leakage, reveal and
announce the selected saved run, show its project, and provide a folder picker
for real research reports. Never turn passing demo tests into validated skip
risk. Selection/core behaviour, target and thresholds remain unchanged.
Four focused UI tests join the regular IDE suite: 18 pass, zero skipped.


## D-074 - Transactional optional plugins in the frozen desktop (2026-10-27)

Owner explicitly requested this fix before the research follow-up. A frozen
core cannot use itself as `python -m pip`. Use a per-user immutable wheel store,
bundled PyPA installer 0.7.0 and packaging validation, isolated factory probing,
atomic manifest activation and restart-only import snapshots. Preserve pinned
official downloads, full SHA-256 and explicit confirmation. Reject unavailable
dependencies before activation; do not fetch arbitrary dependency packages.
Optional updates override bundled languages only when they load successfully;
separate bundled metadata lookup permits recovery from a damaged override.
Removal affects only the override, with bundled restoration after restart.
Inactive versions remain rollback cache rather than deleting loaded Windows
native files. The source environment retains its existing pip path.

The small installer/packaging requirements belong to desktop and dev extras;
the minimal analysis core remains without mandatory third-party dependencies.
See DESKTOP_PLUGIN_INSTALLATION.md. Full/frozen validation is in progress.


D-074 final full-suite and installer validation is complete. The authoritative
dated counts, checksum, signature status and friend kit are recorded in
RELEASE_VALIDATION_D074_2026-10-27.json. Clean-PC acceptance and public catalogue
delivery remain separate; previous in-progress notes above are historical.


## D-075 - Bounded claims, report consistency and input feasibility (2026-10-27)

After D-074 completed, the owner authorized report corrections and a feasibility
check. Use the dated release validation record, attribute graph judgements to
AI, separate safety endpoints and describe cost/feedback limits. No original
study results are altered. Four old structural datasets support development;
the nine confirmatory CSVs have no graph columns. Three code-only HikariCP
probes establish a small extraction/mapping proof, not a selector experiment.
Proceed protocol-first with a bounded pilot; do not call reused cohorts fresh
confirmation. The stronger partial-feedback claim needs new evaluation, while
the bounded retrospective system claim does not depend on a positive study.
Details: REPORT_REVISION_NOTES_D075.md and PARTIAL_FEEDBACK_FEASIBILITY.md.


## D-076 - Observation-isolated development pilot (2026-10-27)

The effective protocol was frozen as v2 in 1965665 before real evaluation.
Source checkpoint 72e6043 implements independent policy factories, observed-only
history features, ancestry-scoped complete fit/calibration/audit data, frozen
decision-time features and exact reference/source universe checks. Audits have a
fixed schedule and replace reduced execution rather than double-counting cost.
The runner checkpoints source plans with input/protocol/source hashes and stops
on mapping mismatches. Fifteen offline kernel/runner tests pass. Real pilot and
the required full Maven-inclusive suite remain in progress. This reused-data
pilot is descriptive development evidence, not independent confirmation or a
product-policy change. See PARTIAL_FEEDBACK_PILOT_PROTOCOL.md.

## D-077 - Explain existing decisions and export bounded evidence (2026-10-27)

The owner authorized engineering improvements after asking how to strengthen
the novelty feature. Reuse the existing static test-discovery endpoint to show
declared check names, framework, language and source path at the selected
commit. Do not generate semantic claims from names or treat static discovery
as execution. Discard stale responses and reject another commit's details.

Evidence health presents the core's refusal, comparison SHAs and available
history fingerprint, with recovery guidance rather than weaker gates or a
promise that more passing tests will validate risk. An explicit save dialog
exports a versioned, allowlisted decision record containing comparison,
selection, risk and actual execution statuses. It omits source, environment,
raw logs and per-case failure messages; local paths and names remain disclosed.
Canceling the dialog writes nothing. No backend behavior or dependency changes.

TypeScript compilation passed; 26 Node UI/workflow tests pass. The workflow
test exercises real view methods against a contract fixture, not a real Maven
build or a clean-PC install. Full Python validation is running against the
unchanged D-076 backend. Installer rebuilding is deferred by owner instruction.
Per-operation core cancellation and broader progress/caching improvements are
still pending; the existing elapsed-time notification is not a percentage.


## D-078 - Truthful read-only pilot progress (2026-10-27)

The owner previously found a process-detection viewer confusing. Provide a
small PowerShell viewer for the current research runner's actual checkpoints.
Its bar counts source snapshots only; replay has no fabricated percentage.
Show checkpoint age without claiming that an OS process is alive or stuck.
Display stop diagnostics and require a results file before showing completion.
The viewer never mutates study files or starts/stops a process. Six offline
checks pass in a temporary Git fixture, including preservation of progress
bytes and refusal of completion without results. This is research progress
visibility; per-operation IDE cancellation remains a separate pending task.
