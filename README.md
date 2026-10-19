# CodeDNA

**Risk-calibrated change-impact analysis and regression test selection for
Java projects in continuous integration.** A Software Engineering Final Year
Project.

Given a Git repository and two commits, CodeDNA will eventually work out which
code changed, what it may affect, which regression tests matter, and how risky
it is to skip the rest — and explain every decision.

**Status:** Milestone 0 (bootstrap) done; Milestone 1 started.
Today CodeDNA reports **file-level** changes between two commits as JSON.
Class/method mapping, dependency graphs, test selection and ML are not
implemented yet — see [docs/ROADMAP.md](docs/ROADMAP.md).

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

## Run the tests

```bash
python -m pytest
```

## Usage

```bash
codedna analyze --repo PATH --base BASE_REV --head HEAD_REV [--output report.json]
```

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

Excerpt of real output from the demo repository:

```json
{
  "path": "src/test/java/example/OrderTotalsTest.java",
  "status": "renamed",
  "old_path": "src/test/java/example/OrderServiceTest.java",
  "similarity": 95,
  "is_java": true,
  "is_binary": false,
  "changed_lines": [[7, 7]],
  "removed_lines": [[7, 7]]
}
```

`changed_lines` are inclusive line ranges in the **head** version of a file;
`removed_lines` are inclusive ranges in the **base** version. Full field list:
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
backend/tests/            pytest suite (temporary Git repos, no network)
examples/                 sample Java/Maven project
scripts/                  helper scripts (demo repo builder)
docs/                     spec, architecture, roadmap, research, decisions
.github/workflows/ci.yml  tests on Ubuntu + Windows, Maven build of sample
AGENTS.md                 rules for contributors and AI coding agents
CODEDNA_STARTER.md        original project brief
```

## Known limitations

- File level only; no class/method mapping yet.
- Heavily edited moves (< 50 % similar) appear as delete + add.
- One `git diff` call per changed file; slow on huge diffs.
- Whitespace-only edits count as changes.
- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#known-limitations-current).

## Documentation

- [Project specification](docs/PROJECT_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Research plan](docs/RESEARCH_PLAN.md)
- [Dataset plan](docs/DATASET_PLAN.md)
- [Decision log](docs/DECISIONS.md)

## Scope

Software engineering only: no vulnerability detection or security scoring.
CodeDNA does not claim novelty for established techniques, and reports no
performance numbers until experiments have actually been run.
