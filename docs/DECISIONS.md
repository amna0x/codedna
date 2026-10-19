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
