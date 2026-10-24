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

## D-040 — DANTE-H baseline and calibrated stopping across orderings

To test whether B10's calibrated stopping helps beyond one ordering, a
history-only approximation of DANTE (ICST 2026) is added:
`codedna.selection.dante` (THFR + Wilson-weighted "stickiness" over windows
1–10, × recent failures ÷ mean duration). DANTE's TF-IDF change/test
relevance is **not** implemented, so it is called DANTE-H everywhere.
`codedna.models.dante_check` and `scripts/dante_check.py` compare D2
(DANTE-H order, calibrated stop at 5 %) with D1 (DANTE-H, fixed budget) at
the same real time, plus B10 / B3. The protocol and decision rule were
committed before any result (`docs/DANTE_B10_PROTOCOL.md`).

Result on the four restored projects × 5 seeds: **inconclusive** under the
pre-specified rule. D2 meets the 5 % target on all four and is never worse
than D1 at the same time, but the gain shows only on wicket-bootstrap and is
a seed-dependent budget cliff. Ordering matters little once the stop is
calibrated. See `experiments/results/dante-b10-2026-10-24/FINDINGS.md` and
the provisional `docs/RELATED_WORK_COMPARISON.md`.

## D-041 — Target-validation gate before any calibrated skip

Following D-039 (transfer is unreliable), runtime selection with risk
estimates is gated (`codedna.selection.gate`): train/calibrate/validate on
the project's own earlier history (60/20/20, chronological), replay B10 on
the newest slice, and pass only with enough failing commits in calibration
and validation (≥ 3 each, ≥ 20 validation commits), observed miss ≤ target
and its 95 % Wilson upper bound ≤ 0.10. Otherwise, or when more than 50
commits passed since the last recorded full-suite run, or non-Java files
changed, the full suite is recommended with the reason. Thresholds are
design choices, not tuned on results. Exposed as `codedna history risk`,
`POST /api/risk` (gate cached per database version) and the IDE's "Learned
from test history" mode in *Tests to run*. History features for an untested
change come from `features.change_rows`; `build_dataset` was refactored to
share the per-row code; its output is unchanged (identical row digest on
LittleProxy without structural features, and the existing tests pass).

On the four restored datasets the gate passes for HikariCP, LittleProxy and
wicket-bootstrap and fails for jade4j (2 failing validation commits). This
offline check reuses the study's test split, so it is not an independent
evaluation of the gate.

Addendum (review): a decision for `base → head` uses only `base` and its
ancestors as history, for both the gate and the features, so results stored
for the change itself or later commits never leak in. Candidates are the
tests Maven runs by default at `head` (history tests if none are found), and
test classes without history always run.
