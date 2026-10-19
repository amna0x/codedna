# CodeDNA — Architecture

## Pipeline (target)

```
Git repository / pull request
        │
        ▼
Git change extractor          ← implemented (file level)   codedna.git_analysis
        │
        ▼
Java declaration mapper       ← implemented (method level) codedna.java_analysis
        │
        ▼
Dependency graph builder      ← implemented (type level)   codedna.dependency_graph
        │
        ▼
Change-impact analyzer        ← implemented                codedna.impact_analysis
        │
        ▼
Candidate test generator      ← implemented (baselines)    codedna.test_mapping, .selection
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
├── java_analysis/
│   ├── parser.py          Tree-sitter Java -> Declaration list, parse_java()
│   └── mapping.py         line ranges -> DeclarationChange, analyze_changes()
├── dependency_graph/
│   ├── model.py           Node / Edge / Evidence / CodeGraph, merge_graphs()
│   ├── references.py      Tree-sitter walk: imports + type names per type
│   └── builder.py         read commit from Git, build nodes, resolve names
├── impact_analysis/
│   └── impact.py          seeds from analyze, reverse BFS, explanation paths
├── test_mapping/
│   ├── discovery.py       static JUnit 4/5 test-class discovery
│   ├── reports.py         Surefire + JaCoCo XML parsers
│   ├── results.py         results.json / coverage-map.json models
│   └── maven.py           opt-in Maven runner, per-test JaCoCo, coverage mapping
└── selection/
    └── baselines.py       all / dependency / coverage strategies, compare
git_analysis/blobs.py      ls-tree + cat-file --batch readers, git archive export
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

### `java_analysis.parser`

`parse_java(source_bytes)` parses one file with Tree-sitter Java (D-008) and
returns a `JavaParseResult`: package, a flat list of `Declaration`s (types and
members with `id`, `kind`, `parent`, 1-based inclusive line extent, and the
declaration's own non-comment tokens), the top-level parts outside types
(package/imports/comments), lines with syntax errors, and body children it
does not understand (`unsupported`). Nothing is resolved: IDs use names and
parameter types exactly as written (D-009).

### `java_analysis.mapping`

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
3. **Resolution** (`builder.py`, D-010) — each name becomes an edge
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

## Known limitations (current)

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
   git_analysis, graph model,     codedna-java (first; parse, resolve,
   impact, selection, history,    discover tests, run tests, coverage)
   ML, calibration, CLI           [future: other languages]
```

- The core never imports language-specific code directly once the plugin
  refactor lands; it asks the registry for the plugin that handles a file.
- The IDE and website contain no analysis logic; they display core JSON.
- Planned locations: `backend/codedna/plugins/` (interface + registry),
  `ide/` (Theia application), `website/` (static site + catalogue index).
  Each is created when its first implementation lands.

## Planned module boundaries

Modules are created when their first implementation lands (see AGENTS.md).
Every stage should exchange plain dataclasses/Pydantic models serialisable to
JSON so results can be stored, diffed, inspected in tests, and fed to the UI.
