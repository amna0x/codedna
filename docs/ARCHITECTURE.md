# CodeDNA — Architecture

## Pipeline (target)

```
Git repository / pull request
        │
        ▼
Git change extractor          ← implemented (file level)   codedna.git_analysis
        │
        ▼
Java code parser              ← Milestone 1 (next)          codedna.java_analysis
        │
        ▼
Dependency graph builder      ← Milestone 2                 codedna.dependency_graph
        │
        ▼
Change-impact analyzer        ← Milestone 2                 codedna.impact_analysis
        │
        ▼
Candidate test generator      ← Milestone 3                 codedna.test_mapping
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
├── cli.py                 argparse CLI; `analyze` sub-command
└── git_analysis/
    ├── git.py             safe Git subprocess wrapper + validation + errors
    └── changes.py         ChangedFile / ChangeReport, extract_changes()
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

## Known limitations (current)

- File level only: no class/method mapping yet.
- Rename detection uses Git's default 50 % similarity heuristic; a heavily
  edited move appears as `deleted` + `added`.
- One `git diff` subprocess per changed file — slow for diffs with thousands
  of files.
- Submodule changes appear as entries without line ranges; not specially
  handled.
- Line ranges come from Git's default diff algorithm; whitespace-only changes
  are reported as changes.
- Merge commits are compared as two trees (`base..head`), not per-parent.

## Planned module boundaries

Modules are created when their first implementation lands (see AGENTS.md).
Every stage should exchange plain dataclasses/Pydantic models serialisable to
JSON so results can be stored, diffed, inspected in tests, and fed to the UI.
