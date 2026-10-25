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
  is private (D-048).
- **Manager:** catalogue wheels are installed with `--no-deps`, so the manager
  runs `pip check` afterwards. If the plugin's own dependencies are missing it
  is uninstalled again and the missing packages are named. An unreachable
  catalogue is a normal `CatalogueError`, not a crash.
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

