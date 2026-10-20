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
