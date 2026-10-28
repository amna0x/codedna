# CodeDNA — Architecture

## Pipeline (target)

```
Git repository / pull request
        │
        ▼
Git change extractor          ← implemented (file level)   codedna.git_analysis
        │
        ▼
Java declaration mapper       ← implemented (method level) codedna_java.mapping (plugin)
        │
        ▼
Dependency graph builder      ← implemented (type level)   codedna_java.builder → codedna.dependency_graph schema
        │
        ▼
Change-impact analyzer        ← implemented                codedna.impact_analysis
        │
        ▼
Candidate test generator      ← implemented (baselines)    codedna_java.discovery, codedna.selection
        │
        ▼
History + feature generator   ← Milestone 4                 codedna.test_history
        │
        ▼
Failure-probability model     ← Milestone 4                 codedna.models
        │
        ▼
Probability calibration       ← Milestone 5                 codedna.calibration
        │
        ▼
Risk-aware test selector      ← Milestone 5                 codedna.selection
        │
   confidence ok? ── no ──► broaden selection / retest all
        │ yes
        ▼
Selected tests → CI execution + evaluation
        │
        ▼
Explanations (codedna.reporting) and graph UI (frontend/, Milestone 6)
```

Each stage consumes the previous stage's structured output. The graph UI reads
the same JSON the analysis produces — there is no separate graph data source.

## What exists today

```
backend/codedna/
├── __init__.py            version
├── __main__.py            `python -m codedna`
├── cli.py                 argparse CLI; `analyze` sub-command (--level)
├── git_analysis/
│   ├── git.py             safe Git subprocess wrapper + validation + errors
│   └── changes.py         ChangedFile / ChangeReport, extract_changes()
├── dependency_graph/
│   ├── model.py           shared schema: Node / Edge / Evidence / CodeGraph, merge_graphs()
│   └── cache.py           BoundedParseCache (LRU by blob SHA) any plugin can reuse
├── impact_analysis/
│   └── impact.py          seeds from analyze, reverse BFS, explanation paths
├── test_mapping/
│   └── results.py         shared results schema: TestRunResult, TestClassResult, CoverageMap
├── selection/
│   └── baselines.py       all / dependency / coverage strategies, compare
├── plugins/
│   ├── base.py            LanguagePlugin protocol (1.1 adds optional members), api_compatible()
│   ├── registry.py        entry-point plugins ("codedna.languages"), compatibility checks
│   ├── languages.py       the core's only way into a language: require(), analyze_changes(),
│   │                      build_graph(), discover_tests(), PluginMissingError
│   ├── catalogue.py       official catalogue index validator (D-047)
│   └── manager.py         install/remove from the official catalogue (D-048)
├── test_history/
│   ├── store.py           SQLite: commits, changed_files, test_results
│   ├── mining.py          first-parent history + numstat
│   ├── collection.py      import results.json / opt-in per-commit runs
│   ├── rtptorrent.py      RTPTorrent importer (real CI results, no builds)
│   ├── recording.py       full-suite runs kept as .codedna/history.csv (D-053)
│   ├── project.py         saved runs listed, imported, added to that history (D-057)
│   └── features.py        leakage-free (commit, test) rows
└── models/
    ├── metrics.py         APFD, APFDc, recall@budget, time to first failure
    ├── rankers.py         B1/B2/B3/B5 baselines, logistic regression, boosting
    ├── evaluate.py        chronological split and evaluation report
    └── experiment.py      Milestone 5 experiment: B0/B4/B6–B9, sweeps, ablations
calibration/
    ├── calibrators.py     none / Platt / isotonic
    └── metrics.py         Brier, ECE, reliability bins
selection/risk.py          risk-per-second selection, skip risk, fallback
selection/policy.py        must-run tests policy read from BASE, add-on rule hook
selection/pts.py           Predictive Test Selection baseline B11 (research only, D-061)
selection/conformal.py     conformal-risk-control stopping threshold B12/B12f (D-063; live opt-in D-068)
api/
    ├── app.py             FastAPI app: endpoints, token + Host checks, build opt-in
    └── server.py          `codedna serve` (loopback-only, prints URL + token)
agent/
    ├── brake.py           plan / check verdicts for AI coding agents (D-059)
    └── mcp_server.py      `codedna mcp`: dependency-free MCP over stdio
git_analysis/blobs.py      ls-tree + cat-file --batch readers, git archive export
```

The Java implementation is a separate distribution (D-054):

```
plugins/codedna-java/          pip install -e plugins/codedna-java
├── pyproject.toml             entry point codedna.languages: java = codedna_java:JavaPlugin
└── codedna_java/
    ├── plugin.py              JavaPlugin (the LanguagePlugin the core sees)
    ├── parser.py              Tree-sitter Java -> Declaration list, parse_java()
    ├── mapping.py             line ranges -> DeclarationChange, attach_java_declarations()
    ├── references.py          Tree-sitter walk: imports + type names per type
    ├── builder.py             read commit from Git, build nodes, resolve names
    ├── build.py               Maven/Gradle layout (modules, test roots)
    ├── discovery.py           static JUnit 3/4/5 test-class discovery
    ├── reports.py             Surefire + JaCoCo XML parsers
    ├── maven.py               opt-in Maven/Gradle runner, per-test JaCoCo, coverage mapping
    └── live.py                live risk features for risk-select (D-041)
```

Python is a second plugin, also bundled (D-060). It needs only the standard
library:

```
plugins/codedna-python/        pip install -e plugins/codedna-python
├── pyproject.toml             entry point codedna.languages: python = codedna_python:PythonPlugin
└── codedna_python/
    ├── plugin.py              PythonPlugin
    ├── parser.py              ast -> declarations (py: IDs), imports, class bases
    ├── mapping.py             line ranges -> DeclarationChange (same shape as Java's)
    ├── builder.py             module/class graph: imports, uses, extends (confirmed/heuristic)
    ├── discovery.py           pytest test modules, settings from the root config file
    └── runner.py              opt-in pytest runner (JUnit XML -> results.json)
```

### `git_analysis.git`

- `run_git(repo, *args)` runs Git with an argument list (no shell), UTF-8
  decoding, and config overrides that stop repository-local settings from
  launching helper programs (`core.fsmonitor=false`). Diff calls additionally
  pass `--no-ext-diff --no-textconv`.
- `resolve_repository(path)` → absolute top-level path, or
  `InvalidRepositoryError`.
- `resolve_commit(repo, rev)` → full SHA via
  `git rev-parse --verify --end-of-options <rev>^{commit}`, or
  `InvalidCommitError`. Revisions starting with `-` are rejected up front.
- All errors derive from `CodeDNAGitError`; the CLI catches this one type and
  prints `error: ...` to stderr with exit code 1.

### `git_analysis.changes`

1. `git diff --name-status -z -M BASE HEAD` lists changed paths. `-z` gives
   NUL-separated, unescaped paths, so spaces and quotes are safe.
2. For each path, `git diff --unified=0 -M BASE HEAD -- <old> <new>` is parsed
   for `@@ -a,b +c,d @@` hunk headers. `+c,d` becomes a `changed_lines`
   range in the head file; `-a,b` becomes a `removed_lines` range in the base
   file. Zero-length sides are omitted.
3. Binary diffs are flagged (`is_binary`) and reported in `warnings`.

One Git call per changed file is simple and robust; it may need batching for
very large diffs (see Known limitations).

### `codedna_java.parser`

`parse_java(source_bytes)` parses one file with Tree-sitter Java (D-008) and
returns a `JavaParseResult`: package, a flat list of `Declaration`s (types and
members with `id`, `kind`, `parent`, 1-based inclusive line extent, and the
declaration's own non-comment tokens), the top-level parts outside types
(package/imports/comments), lines with syntax errors, and body children it
does not understand (`unsupported`). Nothing is resolved: IDs use names and
parameter types exactly as written (D-009).

### `codedna_java.mapping`

`analyze_changes(repo, base, head)` = `extract_changes` +
`attach_java_declarations`, which sets `analysis_level = "method"` and fills
`ChangedFile.java` for each Java file:

1. Read the base version (`old_path` for renames) and head version as raw
   bytes with `git show --no-textconv SHA:path` via `run_git_bytes` — nothing
   is checked out or executed. Raw bytes keep line numbering identical to
   Git's diff (tested with CRLF files).
2. Parse both. If either has a syntax error, is binary, or is not a `.java`
   path, every range of the file goes to `unresolved` plus a warning — no
   partial guessing.
3. Attribute each head `changed_lines` line on the head parse and each base
   `removed_lines` line on the base parse to the innermost declaration
   containing it. Type-level gaps and lines outside types skip blank lines;
   non-blank lines outside every type become `outside_declarations`.
4. Match declarations across versions by ID: `added` / `deleted` /
   `modified`. `code_changed` compares non-comment token sequences.

### `dependency_graph`

`build_graph(repo, rev)` lists `.java` blobs with `git ls-tree -r -z`, reads
them all with one `git cat-file --batch` call, and parses each unique blob
once (cache keyed by blob SHA). Then:

1. **Structure** — `package:`/`file:`/`type:`/`member:` nodes and confirmed
   `contains` edges. Files and their types get `role: test|main` by path
   convention.
2. **References** (`references.py`) — every type name written inside a type
   (fields, parameters, `new X()`, generics, annotations, `extends`,
   `implements`), plus capitalised `X.member` receivers as `static_access`.
3. **Resolution** (`builder.py`, D-010, D-058) — each name becomes an edge
   (`confirmed`/`heuristic`, with `file:line` evidence, max 10 kept per edge),
   an external reference (counted), or an `unresolved` entry with a reason.

Edges are type → type; `imports` edges go from every top-level type of the
importing file. `stats.unresolved_rate` = unresolved / (resolved + unresolved)
references — the "unresolved-edge rate" metric of the research plan.

### `impact_analysis`

`compute_impact(repo, base, head)` (D-012):

1. `analyze_changes` → seeds: the owning type of each changed declaration
   with `code_changed != false`; import/package changes seed the file's
   top-level types; unresolved changes seed every type in the file. Non-Java
   files go to `unanalysed_changes`.
2. Build BASE and HEAD graphs (shared parse cache) and merge them.
3. Reverse BFS over dependency edges, confirmed edges first, optional
   `max_depth`. Each impacted type has `distance`, `confidence` (confirmed
   only if every edge on its path is) and `path` steps from the impacted type
   back to its seed.
4. `candidate_tests`: top-level test types that still exist in HEAD and are
   changed or impacted — class-level dependency-only selection (B4 preview).

### `test_mapping`

- **Discovery** (`discovery.py`): Tree-sitter scan for methods annotated
  `@Test`, `@ParameterizedTest`, `@RepeatedTest`, `@TestFactory`,
  `@TestTemplate`; `@Nested` classes fold into their top-level class;
  inherited test methods are found through the graph's `extends` edges.
  A test class is *in the universe* only if Surefire's default includes
  would run it (`src/test/java`, `Test*`/`*Test`/`*Tests`/`*TestCase`).
- **Runner** (`maven.py`, D-014): refuses without `allow_build`; exports the
  commit with `git archive` (tar `data` filter) into `OUTPUT/checkout`; runs
  `mvn -B --no-transfer-progress test -Dmaven.test.failure.ignore=true`
  (a non-zero exit therefore means a build failure, recorded as a warning).
  Logs, copied Surefire/JaCoCo XML, `results.json` and `coverage-map.json`
  stay in `OUTPUT`; the checkout is deleted unless `--keep-checkout`.
- **Per-test coverage** (D-015): for each test class, delete
  `target/jacoco.exec` and old reports, run `jacoco:prepare-agent test
  jacoco:report -Dtest=<Class>,<Class>$*`, parse `jacoco.xml`, and map covered
  lines onto declarations (innermost declaration per line) of the same
  commit → `files`, `types`, `members` per test class.

### `selection`

`select_tests` (D-016): universe = discovered tests Surefire runs by default
in HEAD. Changed test files are always selected. Non-Java changes → retest-all
unless `non_java="ignore"`. `dependency` = `impact.candidate_tests`.
`coverage` = tests covering a changed member (by ID) or changed type, tests
covering the parent type of an *added* member, tests covering a file whose
imports changed or whose changes are unresolved, and every test without
coverage data. `compare_strategies` evaluates each strategy against a
ground-truth `results.json` of HEAD: `failing_tests`, `caught`, `missed`,
`safe` (nothing missed), selection ratio, estimated time.

`selection.policy` (D-050): must-run tests from `.codedna/policy.toml` at BASE,
request patterns and add-on rules (`codedna.policies` entry points) are added
to every product selection (`select_tests`, `risk-select`); an unreadable
policy or failing rule pins everything. `compare_strategies` and the
experiments ignore it.

### `plugins`

`load_plugins()` registers every factory in the `codedna.languages`
entry-point group; there is no built-in language (D-054). Plugins whose API
major differs from `PLUGIN_API_VERSION`, whose minor is newer, that fail to
import, or that do not implement the protocol are skipped and listed in
`problems`.

`plugins.languages` is the only way the core reaches language code:
`analyze_changes` runs `extract_changes`, then each plugin's
`attach_declarations`, and sets `ChangedFile.language` to the plugin that
handles each file. Several plugins work on one repository (D-060):
`build_graph`/`commit_graph` join every plugin's graph (`union_graphs`; no
edge crosses languages), `discover_tests`/`commit_tests` return a
`CombinedDiscovery`, and `run_tests` splits the selected tests by the plugin
that discovered them (one language runs exactly as before; several write to
`OUTPUT_DIR/<language>` and are joined). Impact and selection use these, so
a change is analysed by whichever plugin handles its file; selection treats
a change in a language without tests as unanalysed (retest-all), because
cross-language dependencies are not followed. Without the Java plugin, `analyze` still lists changed files (level
`file`) and warns that `.java` files were not analysed; commands that need a
graph or test discovery raise `PluginMissingError` naming the package (CLI
exit 1, API 400). A test imports every core module with `codedna_java`,
`codedna_python` and `tree_sitter` blocked, so the core cannot start depending on them again.

`plugins.manager` installs a catalogue wheel with `pip --no-deps`, then runs
`pip check`; if the plugin's own dependencies are missing it is uninstalled
again and the missing packages are named. The API exposes this as
`GET /api/plugins/catalogue`, `POST /api/plugins/install` and
`POST /api/plugins/remove` (each needs `"confirm": true`); the IDE's
"Language plugins" view sends only a plugin id and exact version.

### `test_history` and `models` (Milestone 4)

```
history mine ──► commits + changed_files ─┐
history import / collect ──► test_results ┴─► build_dataset ─► rows (commit, test,
                                                                 label, duration, features)
                                              ─► chronological split ─► rankers ─► metrics
```

- `build_dataset` walks commits with results oldest first and emits one row
  per test that ran (skipped tests excluded) *before* adding that commit's
  outcomes to the per-test history state — the leakage guard (D-023).
- Structural features call `compute_impact(parent, commit)`; `--no-structural`
  skips them (they dominate run time).
- `evaluate` fits ML models on the train split only, reports validation and
  test splits, and adds warnings for small splits or few failures.

### Milestone 5: calibration, risk and fallback

```
train split ──► failure model ──► raw p ──► calibrator (fitted on validation)
                                                   │ calibrated p
test commit rows ──────────────────────────────────▼
           decide(rows, p, RiskPolicy) ──► selected / skipped, estimated skip risk,
                                            fallback flag + reasons
```

- `decide` orders by p / estimated cost (historical mean duration), always
  keeps changed tests, fills the time budget, then — with a risk target and
  fallback — broadens until the estimated skip risk `1 − Π(1 − p)` is at or
  below the target; unfamiliar commits (non-Java changes, mostly
  history-less tests) go straight to retest-all.
- `run_experiment` measures every policy on the test split with *real*
  durations and outcomes and reports estimated skip risk next to the observed
  miss rate, so the risk estimate itself is evaluated.
- `models.replay` (D-049) turns a saved report into a commit-by-commit
  timeline for the IDE's History replay; `run_experiment(trace=True)`
  (`history experiment --replay`) adds SHAs, test names and seconds.

### `api` (local API for the IDE, D-028)

`codedna serve` prints one JSON line (`url`, `token`, `allow_build`) and runs
uvicorn on a loopback address. Every endpoint except `GET /api/health` needs
the `X-CodeDNA-Token` header; requests whose `Host` is not a loopback name
get 403; no CORS headers are sent. Endpoints mirror the CLI and return the
same JSON:

| Method + path | CLI equivalent |
|---------------|----------------|
| `GET /api/health` | — (no token) |
| `GET /api/plugins`, `GET /api/capabilities` | `plugins` |
| `GET /api/plugins/catalogue` | `plugins catalogue` |
| `POST /api/plugins/install`, `POST /api/plugins/remove` | `plugins install ID VERSION --yes`, `plugins remove ID --yes` — need `"confirm": true` |
| `POST /api/analyze` | `analyze` |
| `POST /api/graph` | `graph` |
| `POST /api/impact` | `impact` |
| `POST /api/tests` | `tests` |
| `POST /api/select` | `select` |
| `POST /api/compare` | `compare` |
| `POST /api/run-tests` | `run-tests` — needs `serve --allow-build` **and** `"allow_build": true` |
| `POST /api/replay` | `replay REPORT` |
| `POST /api/replay/sources` | `replay --list FOLDER…` |
| `POST /api/replay/overview` | `replay --overview FOLDER… [--seed N]` |

Errors are JSON: 400 `{"error": ...}` for analysis errors, 401 bad token,
403 host/build not allowed, 422 invalid request body.

### `agent` (test brake for AI coding agents, D-059)

`codedna mcp` speaks newline-delimited JSON-RPC 2.0 (MCP `initialize`,
`ping`, `tools/list`, `tools/call`) on stdin/stdout. `codedna_plan_tests`
wraps the live recommendation (`selection.live`), `codedna_impact` the impact
report; both only read Git objects. `codedna_check` runs the planned tests
through the language plugin and maps the result to `passed` / `blocked` /
`incomplete` / `nothing_to_run` / `no_tests`; it exists only when the server was started with
`--allow-build --repo PATH` and then serves that repository only.
Plan and check take `method` (`b10` default, or `crc`: the failure-conditional
conformal stop from `selection.conformal.failing_commit_threshold`, D-068),
passed through `selection.live` to the language plugin's `risk_select`.

### `ide/` — CodeDNA IDE (Theia 1.76, Electron)

```
codedna-extension/src
├── common/codedna-protocol.ts      service interface + JSON types (from PROJECT_SPEC)
├── node/codedna-service-impl.ts    starts `codedna serve`, proxies with the token
├── node/codedna-backend-module.ts  RPC binding at /services/codedna
└── browser/
    ├── change-view-widget.tsx      "Changed code" (analyze + impact)
    ├── tests-view-widget.tsx       "Recommended tests" (select)
    ├── graph-view-widget.tsx       "Impact graph" (impact.explanation_graph, Cytoscape.js)
    ├── graph-layout.ts             package lanes x links-from-change placement (D-051)
    ├── replay-view-widget.tsx      "History replay" (replay timelines, D-049)
    ├── codedna-workspace.ts        repo path = first workspace root; open file at line
    ├── theme/codedna-theme.ts      CodeDNA Dark colour theme + shell class toggle
    └── style/codedna(.|-shell).css view and shell styling (D-030)
electron-app/package.json           product config: Theia packages, default theme
```

## Known limitations (current)

- IDE: compares commits only (no uncommitted changes yet); opens test files by
  the `src/test/java` convention; no Java language server, graph view,
  test running or risk scores yet; tested on Windows only.

- API: synchronous requests (a test run blocks that request until done); no
  progress events yet; Starlette's test client warns that `httpx` support is
  deprecated in favour of a successor package — revisit when upgrading.

- Skip risk assumes independent test failures; correlated failures make it
  optimistic or pessimistic — measured, not assumed, by the experiment.
- B4 in `history experiment` uses the `dep_reachable` feature (class-level
  static reachability), a proxy of `codedna select --strategy dependency`.

- History/ML: real RTPTorrent study reports are saved, but the raw dataset and
  derived history databases are not included in Git; first-parent history only; commits
  whose build fails produce no rows (and `collect` retries them); author
  features deliberately omitted (privacy); structural features recompute two
  graphs per commit (slow on large histories).

- Declaration IDs are syntactic: parameter types are not resolved
  (`List<String>` vs `java.util.List<String>` give different IDs), so an
  import-only rename of a parameter type looks like delete + add.
- Renaming a class changes the ID of the type, but its untouched members are
  not re-reported under the new name; only the changed header lines appear
  (as one `added` and one `deleted` type).
- A changed method signature is reported as `deleted` old + `added` new; no
  move/rename detection between declarations.
- Javadoc and comments between members count as type-level `comment` changes
  of the enclosing type, not of the following member.
- Any syntax error on either side leaves the whole file `unresolved`.
- Graph name resolution is simplified (D-010): inherited member types,
  methods and fields are not resolved; no method-level call edges.
- Impact is class-level: a change to one method impacts every dependent of
  its class, which over-approximates.
- Tests are identified by path convention; non-standard layouts are missed or
  misclassified (e.g. `Testimony.java` counts as a test).
- Reflection, dependency injection, generated code and resources create no
  edges, so dependents reached only that way are not found.
- Non-Java changes (build files, resources) are reported but not analysed;
  selection falls back to retest-all for them by default.
- `run-tests`: single-module Maven with root `pom.xml` only; no Gradle,
  TestNG, multi-module builds or custom Surefire includes. Per-test coverage
  costs one Maven start-up per test class.
- Coverage-based selection only sees code executed at BASE; reflection,
  resources and static initialisation order are not tracked, so it can miss
  failures (the `compare` command measures this rather than assuming).
- Estimated time sums Surefire class times; build start-up and compilation
  are excluded.
- Rename detection uses Git's default 50 % similarity heuristic; a heavily
  edited move appears as `deleted` + `added`.
- One `git diff` subprocess per changed file — slow for diffs with thousands
  of files.
- Submodule changes appear as entries without line ranges; not specially
  handled.
- Line ranges come from Git's default diff algorithm; whitespace-only changes
  are reported as changes.
- Merge commits are compared as two trees (`base..head`), not per-parent.

## Target product architecture (D-017 – D-020)

```
 CodeDNA IDE (Eclipse Theia, TypeScript)        Platform website (static)
   CodeDNA panels + graph view                    downloads, docs, catalogue page
   plugin manager ───────────────┐                         │
        │ HTTP/JSON (127.0.0.1)  │ reads                   │ renders
        ▼                        ▼                         ▼
 Local API (FastAPI)         Plugin catalogue index (versioned JSON + SHA-256)
        │                              │ install (pinned, checksum-verified)
        ▼                              ▼
 Analysis core (Python) ◄──── Language plugins (entry points "codedna.languages")
   git_analysis, graph model,     codedna-java (parse, resolve, discover
   impact, selection, history,    tests, run tests, coverage), codedna-python
   ML, calibration, CLI           (ast, pytest); several per repository
```

- The core never imports language-specific code; it asks the registry for
  the plugin (D-054). Java lives in `plugins/codedna-java`, Python in
  `plugins/codedna-python` (D-060).
- The IDE and website contain no analysis logic; they display core JSON.
- Locations: `backend/codedna/plugins/` (interface, registry, catalogue,
  manager), `plugins/codedna-java/` and `plugins/codedna-python/`, `ide/` (Theia
  application), `website/` (static site + catalogue index).

## Planned module boundaries

Modules are created when their first implementation lands (see AGENTS.md).
Every stage should exchange plain dataclasses/Pydantic models serialisable to
JSON so results can be stored, diffed, inspected in tests, and fed to the UI.


## Saved-study figure export (D-038)

`scripts/make_study_figures.py` reads the saved study summaries and per-seed
reports. It exports RQ1–RQ5 PNG/SVG figures and their numerical data without
loading a history database or retraining a model. Matplotlib is an optional
`plots` dependency; `--data-only` needs only the standard library.

Aggregation averages seeds within each project, then weights projects equally.
Missing metrics remain undefined. Calibration and B10 variant comparisons use
common project cohorts; pooled confidence intervals are reused from the saved
hierarchical bootstrap, not reconstructed from seed standard deviations.
The manifest fingerprints all read reports, generated artifacts, and the
exporter source with SHA-256 and records Python/Matplotlib versions.

## Project-disjoint transfer validation (D-039)

`codedna.models.transfer.fit_project` accepts only source-project data. It fits
on the source training split and calibrates on its validation split.
`evaluate_target` applies that frozen model to the target test split and records
prediction, ordering, selection and matched-cost outcomes. Missing source
calibration remains unavailable; target labels never repair it.

`scripts/run_cross_project.py` fixes the four-project, five-seed protocol,
restricts source history before the target test window using Git dates, and
reports all directions alongside fresh within-project controls. Input, code
and package fingerprints protect resumed runs from mixing incompatible fits.
The target's past test history remains available as features; this evaluates
transfer between repositories with history, rather than history-free startup.

`scripts/fetch_rtptorrent_subset.py` recovers selected public archive entries
with HTTP byte ranges. `scripts/prepare_transfer_features.py` imports recorded
outcomes, rebuilds structural/history features, and requires the original
study's dataset digest before model evaluation. Neither script builds the
analysed repositories. Raw data, SQLite histories and feature CSVs remain
outside version control.


## Live risk and selected execution (D-040/D-041)

`selection.live` provides shared audited fitting and dispatches through the
installed language plugin’s optional `risk_select` capability. The Java adapter
(`codedna_java.live`) binds CSV rows to first-parent ancestry and constructs
Java change/history features without observing target outcomes.
A separately fitted/calibrated/audited model feeds `selection.validation`'s
conservative empirical gate. Missing or inadequate evidence yields full-suite
selection with explicit unvalidated status. No serialized executable model is
loaded. Fixed 15-feature live inputs differ explicitly from the 19-feature
retrospective experiment. `models.dante_history` supplies an independently
implemented history-only CCH ordering for the exploratory stopping extension.

The authenticated local API adds risk selection and recomputed selection runs.
The IDE backend enables build permission only following explicit execution
confirmation, preserving the per-request consent check. `run_maven_tests` accepts
optional discovered test IDs, includes nested classes, and handles empty lists
without invoking Maven. The UI displays actual result statuses and evidence
without implementing model/selection logic. See JAVA_WORKFLOW.md.


## Windows desktop runtime (D-055)

The Windows installer includes the Python analysis core as a PyInstaller
one-directory bundle under Electron's `resources/core/`. The Electron main
entry resolves an explicit executable override, then that bundled executable,
then the development PATH fallback. The existing Node service still starts a
loopback-only token-authenticated API and forwards shared JSON; no analysis
moves into TypeScript. Git and Java build tools remain external.

`scripts/build_desktop_core.py` is build tooling only. Its optional `desktop`
extra is separate from application dependencies. Generated binaries, dependency
caches and core file-hash manifests are ignored; datasets are not bundled.

## Exact risk-prefix search and follow-up evidence (D-067/D-069)

Risk selection binary-searches the shortest acceptable ordered prefix using
the unchanged skip-risk calculation. Candidate inclusion is monotone; pins,
budgets and fallback semantics are preserved. No selection logic moves into
the frontend and no dependency is added. B10 remains the default; the live
failure-conditional CRC method remains opt-in (D-068), following the evidence
and limitations in D-067. The four nine-project follow-ups preserve original
reports and disclose reused/new code fingerprints in their audit manifests.

## Brake structural view and language fallback (D-070)

`agent.brake.plan` exposes the existing dependency SelectionReport under
structural_plan, then broadens required tests with it. Both reports share
immutable revisions; a later WORKTREE edit cannot mix comparisons. The
structural report has no probability and does not include request-only pins.
A retained risk estimate after broadening is identified as a conservative
model bound; no skipped tests means zero skip risk on validated plans.
`selection.live.recommend(language=None)` detects the test language and
returns an explicit full-suite fallback for missing risk capability or a
mixed-language universe. `brake.check` delegates execution to the existing
`plugins.languages.run_tests`, preserving consent and combined results.
The core imports no language-specific package for this behavior.


## Blueprint completion repairs (D-071)

`agent.brake.check` refuses a successful verdict if any required test class or
module is skipped by the build. `test_history.recording` rejects such incomplete
observations before replacing complete recorded evidence. Real failing test
results remain recordable, including Maven/Gradle's failure exit code.

`plugins.languages.commit_tests` forwards the shared parse cache when a plugin
explicitly supports the optional argument. Legacy discovery signatures continue
to work. Python pytest execution prefers the original project's `.venv`; the
frozen analysis executable cannot be used as a Python interpreter.

`scripts/pr_demo.py` and the PR-analysis workflow produce a read-only brake plan,
not a test-run verdict. Website and optional new features remain separately
tracked in the current completion ledger and deferred backlog.


## Extensions and explicit risk evidence (D-072)

The existing PluginsViewWidget is hosted inside a Theia Extensions ViewContainer
provided by extensions-widget-factory.ts. PluginsViewContribution restores it
after layout initialization without requesting editor focus. Installed language
metadata renders before the online catalogue completes. UI installation still
uses the core; website downloads do not execute local code.

Brake plans expose the any-omitted-failure objective plus the active audit's
denominator/sample/bound: B10 uses the all-audit-commit Wilson evidence screen;
CRC uses failing audit commits and its corrected expected-risk quantity. Neither
is advertised as a future guarantee. No model or stopping rule changed.


## Frozen optional plugin store (D-074)

Desktop installation dispatches to plugins/desktop_store.py after the shared
catalogue/confirmation/checksum validation. A per-user staging directory and
isolated core subprocess validate the wheel; atomic active.json replacement
commits the selection. Startup activation precedes CLI imports. Registry lookup
prefers valid optional copies and keeps bundled discovery separate because
Python metadata otherwise deduplicates distribution names. Updates/removals
require restart; bundled app files and risk logic are unchanged. Details and
release constraints: DESKTOP_PLUGIN_INSTALLATION.md.


### Decision inspection and evidence export (D-077)

The IDE uses the existing `/api/tests` response to display statically declared
checks at the selection's head commit. It rejects mismatched snapshots and
invalidates pending details when the comparison changes. Check names are
source metadata, not inferred behavioral guarantees. Source navigation opens
the working copy; the shown discovery metadata is tied to the recorded SHA.

`decision-evidence.ts` only formats existing core JSON and recovery guidance.
It performs no risk calculation or test-selection logic. The workspace's save
dialog writes a user-chosen JSON record through Theia FileService. No automatic
upload, raw logs, source text, environment capture or new API endpoint is added.


### Per-operation Git validation (D-079)

Selection, risk dispatch and brake planning share a nested, bounded validation
scope. It memoizes only successful repository resolution and exact immutable
commit-object validation; it does not cache mutable refs, index/worktree reads,
source trees, outcomes or risk acceptance. Thread ownership, Git environment keys
and finally-reset prevent reuse across independent requests. Java risk feature
extraction uses the already-selected immutable comparison, so edits during
analysis cannot switch its feature snapshot.


## Optional analysis workers (D-080)

The local API retains synchronous routes and additionally offers bounded
read-only jobs. `api.job_routes` applies existing typed models and authorization;
`api.analysis_jobs` owns the queue and terminal state; `api.owned_process`
contains each worker before input; `api.analysis_worker` invokes existing core
functions and emits bounded JSON stages/results. The frontend displays these
values without moving analysis into TypeScript. API lifespan cleanup closes
owned workers. Builds/history/plugin changes retain their separate contracts.

Only Tests recommendation currently opts into the job UI, capability-gated for
older cores. The internal desktop bootstrap pins the parent's active managed
plugin paths or bundled-fallback error before registry loading. The IDE backend
retains that snapshot across core restarts for build permission. No ordinary
analysis restart resume or cross-request model/audit cache is introduced.
See ANALYSIS_JOB_PLAN.md for measured bounds, tests and packaging limits.


D-081 extends the job UI to Changes. Change and impact are sequential so both
refer to the same immutable snapshot. Canonical-repository navigation keeps
subfolder workspaces from opening the wrong files; links still open working
files with that limitation disclosed. API-relative file paths are anchored
before a worker starts in its trusted core directory. No analysis implementation
or risk computation moves into TypeScript.

## Optional performance diagnostics and scoped reuse (D-083)

`codedna.performance` owns optional synchronous, thread/process-bound stage
records. `POST /api/analysis-jobs/{operation}?profile=true` emits measurements
before its terminal result; polling returns optional metrics. Capability
`analysis_jobs.timing_version = 1` advertises this extension. Startup measures
spawn to first worker stage and is separate from core operation time. MCP's
optional `profile: true` adds `operation_timings` and distinguishes analysis
from consented test execution. Defaults preserve operation JSON.

`dependency_graph.cache` shares a bounded immutable-blob parse cache only
inside one operation, partitioned by repository/plugin identity. `models.fit_cache`
stores only independent fitted model/calibrator copies, with bounded memory,
TTL, explicit namespace, complete dataset and implementation keys. Live Java
checks eligibility before reuse and recomputes the audit and stopping decision.
No history, audit acceptance, verdict, selected tests or mutable refs are reused.
The CSV snapshot is parsed and fingerprinted from identical bytes. See
[performance details](PERFORMANCE_ENGINEERING.md) for commands and limits.

## Optional behavioral witness execution (D-085)

`codedna.behavior` validates consent, bounded options, immutable refs and a new
external export folder, then owns a separate `behavior_worker` process. Reuse
`api.owned_process.OwnedProcess`, which is stdlib-only and does not import the
API server. The worker waits for its contained parent's request before plugin
activation; frozen workers receive the parent's pinned snapshot. Read-only
analysis jobs gain no execution capability.

The optional language-plugin `find_witness(request)` capability owns language
syntax, compilation, generation and observations. Java's `witness.py` supports
one self-contained public static int(int) method; `witness_export.py` creates
an independent JDK-only reproducer. Structured observations/source hashes cross
the core boundary; no Java parsing or analysis logic is added to the IDE/core.
The CLI witness command and opt-in MCP --moonshot expose this experimental
capability. Default MCP tools and test-brake decisions are unchanged. Controller
identity/interpretation fields cannot be supplied by a plugin. See
[behavioral witnesses](BEHAVIORAL_WITNESS.md) for limits and consent.


## D085 completed engineering evidence — 2026-10-28

Corrected source 4d35941 passed all 714 Maven-inclusive tests, zero skips/failures.
Actual frozen executable: 32 passing contracts and 1462 verified bundle files.
Installer embedded payload and restricted-PATH unpacked smoke passed; local
friend kit includes demos and manual checklist. No installation/clean-PC claim.
The unchanged D083 production frontend was reused. Three D085 packaged GUI checks
pass: isolated launch, bundled language display and tab restoration on restart.
The full D083 GUI test was not repeated; its earlier evidence remains separate.

The fixed optional Moonshot comparison completed all 48 searches. All 15 emitted
witnesses independently reproduced using only the JDK. Guided outcomes were
12 difference / 3 no-difference / 6 inconclusive / 3 unsupported, versus simple
3 / 12 / 6 / 3. Median whole-call costs were 11.234s / 10.057s. Repeated synthetic
cases, with boundaries favoring guidance, are not independent real bugs or a
net-CI speedup. A difference is not necessarily a regression; no witness does
not validate skipping. The risk policy and original mixed findings are unchanged.
See the D085 source/frozen/release/pilot evidence JSONs and pilot FINDINGS.md.
