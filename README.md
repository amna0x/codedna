# CodeDNA

**Risk-calibrated change-impact analysis and regression test selection for
Java projects in continuous integration.** A Software Engineering Final Year
Project.

Given a Git repository and two commits, CodeDNA will eventually work out which
code changed, what it may affect, which regression tests matter, and how risky
it is to skip the rest — and explain every decision.

**Status:** Milestones 0, 1 and 2 done.
Today CodeDNA can:

- report changes between two commits: files, line ranges, and the Java
  **classes, methods, constructors and fields** they touch (`analyze`);
- export a **code dependency graph** of any commit, with every edge labelled
  `confirmed` or `heuristic` and unresolved names listed separately (`graph`);
- list types **potentially impacted** by a change, each with an explanation
  path, plus the test classes that depend on them (`impact`).

Code is parsed with Tree-sitter, never built or executed. Test execution,
history mining and ML are not implemented yet — see
[docs/ROADMAP.md](docs/ROADMAP.md).

## Prerequisites

| Tool | Version | Needed for |
|------|---------|-----------|
| Python | 3.11 or newer | CodeDNA itself |
| Git | 2.24 or newer | Change extraction |
| Java (JDK) | 17 | Sample project (optional for now) |
| Maven | 3.9+ | Sample project build (optional for now; required from Milestone 3) |

## Setup

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Installing needs internet once (it downloads the `tree-sitter` and
`tree-sitter-java` wheels, which include the compiled Java grammar). After
that, analysis and tests run fully offline.

## Run the tests

```bash
python -m pytest
```

## Usage

```bash
codedna analyze --repo PATH --base BASE_REV --head HEAD_REV [--level method|file] [--output FILE]
codedna graph   --repo PATH [--rev REV] [--no-members] [--output FILE]
codedna impact  --repo PATH --base BASE_REV --head HEAD_REV [--max-depth N] [--confirmed-only] [--output FILE]
```

- `analyze --level method` (default) adds a `java` object to every changed
  Java file; `--level file` skips Java parsing.
- `graph` exports packages, files, types and members of one commit (default
  `HEAD`) with `contains`, `extends`, `implements`, `uses`, `imports` and
  `static_access` edges. `--no-members` leaves out method/field nodes.
- `impact` follows dependency edges backwards from the changed types.
  `--max-depth` limits the number of hops; `--confirmed-only` ignores
  heuristic edges.

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
  java_analysis/          Tree-sitter Java parser + line-to-declaration mapping
  dependency_graph/       code graph model, reference extraction, name resolution
  impact_analysis/        reverse-dependency traversal with explanation paths
backend/tests/            pytest suite (temporary Git repos, no network)
examples/                 sample Java/Maven project
scripts/                  helper scripts (demo repo builder)
docs/                     spec, architecture, roadmap, research, decisions
.github/workflows/ci.yml  tests on Ubuntu + Windows, Maven build of sample
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
- Tests are recognised by path convention (`src/test/`, `*Test.java`), and
  candidate tests are class-level and dependency-only (no coverage yet).
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

Java only (Maven/JUnit), per the FYP brief: method mapping, graph and test
mapping are Java-specific. Other files are reported, not analysed — see
docs/DECISIONS.md D-013. Software engineering only: no vulnerability detection
or security scoring.
CodeDNA does not claim novelty for established techniques, and reports no
performance numbers until experiments have actually been run.
