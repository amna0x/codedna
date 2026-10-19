# CodeDNA — Project Specification

**Working title:** CodeDNA: Risk-Calibrated Change-Impact Analysis and
Intelligent Regression Test Selection for Continuous Integration

**Type:** Software Engineering Final Year Project (Path A — no security scope)
**Team:** 2–3 BSCS students · **Duration:** 6–9 months
**Analysed language:** Java (Maven, JUnit 5) — the first language plugin; more
languages later through plugins (D-013, D-018) · **Implementation:** Python 3.11+
core; TypeScript IDE (Eclipse Theia) and static website

## Product vision (D-017)

CodeDNA is delivered as a platform:

1. **Analysis core** (Python) — change extraction, code graph, impact,
   test selection, history/ML risk estimation, calibration; CLI + local API.
2. **Language plugins** — one per language behind a common interface (D-018).
   Java is the first and, until Milestone 5 is complete, the only one.
3. **CodeDNA IDE** — a branded IDE built on Eclipse Theia with CodeDNA
   panels: changed methods, impacted code, recommended tests with risk,
   run-selected-tests, interactive code graph (D-019).
4. **Platform website** — downloads, documentation and a plugin catalogue;
   plugins can also be installed from inside the IDE (D-020).

The research contribution (calibrated, explainable regression test selection
for Java) remains the priority and the basis of the evaluation; items 2–4 are
the product around it.

## Problem

Running a full regression suite on every change is slow. Running too few tests
lets regressions slip through. Developers need to know *which* tests a change
is likely to affect and *how risky* it is to skip the others.

## Inputs

- A local Git repository
- A base commit and a target (head) commit or pull request
- Optionally, a test-execution budget (time or count)

## Eventual outputs

1. Changed files, classes, methods and line ranges.
2. A code dependency graph with typed, labelled edges
   (confirmed / heuristic / unresolved).
3. Potentially impacted components, with explanation paths.
4. Candidate regression tests mapped to impacted code.
5. Per-test failure-probability estimates, calibrated.
6. A ranked, budgeted test selection, with fallback to a broader or full suite
   when confidence is insufficient.
7. A human-readable explanation of each decision.
8. An interactive graph view built from the same analysis data, inside the
   CodeDNA IDE.
9. Evaluation against established baselines (see RESEARCH_PLAN.md).

## Current scope (implemented)

`codedna analyze --repo PATH --base REV --head REV [--level method|file]`
prints JSON describing every file changed between two commits: status (added /
modified / deleted / renamed / copied / type_changed), old path for renames,
whether it is a Java file, binary detection, and changed line ranges on both
sides of the diff. At the default `--level method`, every Java file also lists
the classes, methods, constructors, fields and other declarations those lines
touch.

### JSON output contract (v1)

| Field | Meaning |
|-------|---------|
| `repository` | Absolute path of the repository top level |
| `base_commit`, `head_commit` | Full 40-char SHAs the revisions resolved to |
| `analysis_level` | `"method"` (default) or `"file"` (`--level file`) |
| `changed_files[].path` | Path in the head commit (or the deleted path) |
| `changed_files[].status` | `added`, `modified`, `deleted`, `renamed`, `copied`, `type_changed` |
| `changed_files[].old_path` | Previous path for renames/copies, else `null` |
| `changed_files[].similarity` | Git rename similarity percentage, else `null` |
| `changed_files[].is_java` | `true` if the old or new path ends in `.java` |
| `changed_files[].is_binary` | `true` if Git reports a binary diff |
| `changed_files[].changed_lines` | Inclusive `[start, end]` ranges in the **head** file (added/modified lines) |
| `changed_files[].removed_lines` | Inclusive `[start, end]` ranges in the **base** file (deleted/replaced lines) |
| `changed_files[].java` | Declaration mapping (below) for Java files at method level; `null` for non-Java files or `--level file` |
| `warnings` | Human-readable notes about things that could not be analysed |

`changed_files[].java` (method level):

| Field | Meaning |
|-------|---------|
| `package` | Package of the head version (base version for deleted files), `null` for the default package or when unparsed |
| `declarations[].id` | `pkg.Type`, `pkg.Outer.Inner`, `pkg.Type#method(T1,T2)`, `pkg.Type#<init>(T1)` (constructor), `pkg.Type#field`, `pkg.Type#<clinit>[n]` / `#<init-block>[n]` (initializers). Parameter types as written in the source, not resolved |
| `declarations[].kind` | `class`, `interface`, `enum`, `record`, `annotation_type`, `method`, `constructor`, `field`, `enum_constant`, `annotation_element`, `initializer` |
| `declarations[].change` | `added` (ID only in head), `deleted` (ID only in base), `modified` (in both) |
| `declarations[].code_changed` | `false` when only comments/formatting differ (non-comment tokens identical); `null` if not comparable |
| `declarations[].parent` | ID of the enclosing type, `null` for top-level types |
| `declarations[].head_lines`, `base_lines` | Extent `[start, end]` of the declaration in each version, `null` where it does not exist |
| `declarations[].changed_lines`, `removed_lines` | The file's head/base ranges that fall in this declaration |
| `declarations[].parts` | Types only: which parts of the type itself changed (`annotation`, `modifiers`, `header`, `body`, `comment`); members are reported as their own entries |
| `outside_declarations[]` | Changed lines outside every type: `side` (`head`/`base`), `lines`, `parts` (`package`, `import`, `comment`, ...), `code_changed` |
| `unresolved[]` | Lines that were **not** mapped: `side`, `lines`, `reason` (syntax error, binary file, non-`.java` side, unsupported syntax). Each also produces a top-level warning |

A line is attributed to the innermost declaration containing it; methods,
constructors, fields and initializers are leaves (code in anonymous/local
classes belongs to the enclosing member). Blank lines between members or
outside types are ignored. Full rules: DECISIONS.md D-008/D-009.

Exit codes: `0` success, `1` analysis error (bad repo, bad commit, Git
failure), `2` invalid command-line usage.

### `codedna graph` JSON (v1)

| Field | Meaning |
|-------|---------|
| `repository`, `commit` | Repository path and analysed commit SHA |
| `stats` | Node counts by kind, edge counts by kind × confidence, `resolved_references`, `unresolved_references`, `external_references`, `unresolved_rate` |
| `nodes[]` | `id` (`package:p`, `file:path`, `type:p.T`, `member:p.T#m(int)`), `kind`, `label`, `file`, `lines`, `package`, `parent`, `role` (`test`/`main` by path convention), `has_syntax_errors`, `versions` (merged graphs only) |
| `edges[]` | `source`, `target`, `kind` (`contains`, `extends`, `implements`, `uses`, `imports`, `static_access`), `confidence` (`confirmed`/`heuristic`), `evidence[]` (`file`, `line`, `confidence`, `note`; at most 10), `evidence_count` |
| `unresolved[]` | `source` type, `name` as written, first `file`/`line`, `reason`, `count` — never turned into edges |
| `warnings` | Duplicate type IDs, files with syntax errors |

### `codedna impact` JSON (v1)

| Field | Meaning |
|-------|---------|
| `seeds[]` | Changed types: `node`, `file`, `in_head` (false if deleted), `reasons` |
| `impacted[]` | `node`, `kind`, `file`, `role`, `distance` (hops), `confidence`, `seed`, `path[]` (`dependent`, `depends_on`, `kind`, `confidence`, `evidence` as `file:line`) |
| `impacted_files[]` | Files of seeds (`reason: changed`) and of impacted types |
| `candidate_tests[]` | Test classes (path convention) existing in HEAD that are changed or impacted |
| `ignored_changes[]` | Comment/formatting-only changes that produced no seed |
| `unanalysed_changes[]` | Non-Java changed files (impact unknown) |
| `graph_stats`, `warnings` | Stats of the merged graph; analysis warnings |

"Impacted" means *reachable through dependency edges*, not "behaves
differently". Rules: DECISIONS.md D-010 – D-012.

### Test mapping and selection JSON (v1)

- `codedna tests`: `tests[]` with `id` (top-level class = graph type ID),
  `file`, `framework` (`junit5`/`junit4`/`unknown`), `methods`,
  `inherited_from`, `in_test_sources`, `matches_surefire_defaults`,
  `runs_by_default`; `warnings`.
- `results.json` (`run-tests`): `commit`, `tool`, `commands`, `exit_codes`,
  `duration_seconds`, `per_test_coverage`, `tests[]` (`id`, `status`
  `passed`/`failed`/`error`/`skipped`, `time`, `cases[]`), `failing_tests`,
  `warnings`.
- `coverage-map.json`: `commit`, `tool: "jacoco"`, `tests{id: {files{path:
  ranges}, types[], members[]}}`, `warnings`.
- `codedna select`: `strategy`, `total_tests`, `selected[]` (`test`,
  `reasons[]`), `selected_count`, `skipped[]`, `selection_ratio`,
  `estimated_time` (`selected_seconds`, `all_seconds`, `saved_ratio`,
  `tests_without_duration`) or `null`, `warnings`.
- `codedna compare`: `ground_truth` (`commit`, `failing_tests`),
  `strategies[]` (`strategy`, `selected`, `total`, `selection_ratio`,
  `estimated_time`, `failing_tests`, `caught`, `missed`, `safe`), `warnings`.

Single commit pairs only; aggregate evaluation over a history is
`history evaluate` (below).

### History and evaluation (Milestone 4)

- `codedna plugins`: `api_version`, `plugins[]` (`name`, `display_name`,
  `version`, `api_version`, `file_suffixes`), `problems[]`.
- `history mine|import|status`: store summary — `commits`,
  `commits_with_results`, `commits_with_failures`, `test_classes`.
- `history collect`: `collected`, `remaining`, `runs[]` (`commit`, `seq`,
  `tests`, `failing`, `build_failed`, `duration_seconds`).
- `history evaluate`: `protocol` (`splits`, `split_fractions`, `seed`,
  `features`, `rows`), `results.{validation,test}` (`commits`,
  `commits_with_failures`, `rankers.{name}` with `mean_apfd`, `mean_apfdc`,
  `mean_ttff`, `mean_recall_at_25pct_time`, `mean_recall_at_50pct_time`,
  `evaluated_commits`, and for ML `pr_auc`, `brier`, `positive_rate`),
  `warnings`. `--dataset-csv` writes the rows.
- `history experiment`: `config`, `reproducibility` (`dataset_sha256`,
  `rows`, `commits`, first/last commit, `seed`, `python`, `packages`),
  `calibration` (`methods.{none,platt,isotonic}` → `brier`, `ece`,
  `reliability[]`), `policies.{B0…B9}` (`mean_selection_ratio`,
  `mean_time_ratio`, `failing_test_recall`, `missed_failures`,
  `commit_safety_rate`, `fallback_rate`, `mean_estimated_skip_risk`,
  `observed_miss_rate`), `risk_coverage` (budget and risk-target sweeps),
  `ablations` (`pr_auc`, `brier`, recall and safety at the budget per feature
  group removed), `warnings`.

## Non-goals

- Vulnerability detection, penetration testing, security scoring.
- Using an LLM as the core regression-test predictor.
- Microservices, Kubernetes, authentication, multi-tenant hosting.
- Writing a text editor / IDE from scratch (the IDE is built on Eclipse Theia).
- User accounts, payments, ratings or third-party uploads on the website.
- Installing plugins from anywhere other than the official catalogue.
- Additional language plugins before the Java research track (Milestone 5)
  is complete.
- Claiming novelty for established techniques (changed-file detection,
  dependency graphs, affected-test selection, ML prioritisation,
  history-based ranking).

## Quality requirements

- Never invent dependency relationships, test outcomes or results.
- Every important behaviour has automated tests using temporary Git
  repositories, runnable offline.
- Runs on an ordinary student laptop (Windows, macOS, Linux).
- Analysis never executes code from the analysed repository.
