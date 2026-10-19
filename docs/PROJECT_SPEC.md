# CodeDNA — Project Specification

**Working title:** CodeDNA: Risk-Calibrated Change-Impact Analysis and
Intelligent Regression Test Selection for Continuous Integration

**Type:** Software Engineering Final Year Project (Path A — no security scope)
**Team:** 2–3 BSCS students · **Duration:** 6–9 months
**Analysed language:** Java (Maven, JUnit 5) · **Implementation:** Python 3.11+

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
8. An interactive graph view built from the same analysis data.
9. Evaluation against established baselines (see RESEARCH_PLAN.md).

## Current scope (implemented)

`codedna analyze --repo PATH --base REV --head REV` prints JSON describing every
file changed between two commits: status (added / modified / deleted / renamed /
copied / type_changed), old path for renames, whether it is a Java file, binary
detection, and changed line ranges on both sides of the diff.

### JSON output contract (v0, file level)

| Field | Meaning |
|-------|---------|
| `repository` | Absolute path of the repository top level |
| `base_commit`, `head_commit` | Full 40-char SHAs the revisions resolved to |
| `analysis_level` | `"file"` for now; later `"method"` |
| `changed_files[].path` | Path in the head commit (or the deleted path) |
| `changed_files[].status` | `added`, `modified`, `deleted`, `renamed`, `copied`, `type_changed` |
| `changed_files[].old_path` | Previous path for renames/copies, else `null` |
| `changed_files[].similarity` | Git rename similarity percentage, else `null` |
| `changed_files[].is_java` | `true` if the old or new path ends in `.java` |
| `changed_files[].is_binary` | `true` if Git reports a binary diff |
| `changed_files[].changed_lines` | Inclusive `[start, end]` ranges in the **head** file (added/modified lines) |
| `changed_files[].removed_lines` | Inclusive `[start, end]` ranges in the **base** file (deleted/replaced lines) |
| `warnings` | Human-readable notes about things that could not be analysed |

Exit codes: `0` success, `1` analysis error (bad repo, bad commit, Git
failure), `2` invalid command-line usage.

## Non-goals

- Vulnerability detection, penetration testing, security scoring.
- Using an LLM as the core regression-test predictor.
- Microservices, Kubernetes, authentication, multi-tenant hosting.
- Claiming novelty for established techniques (changed-file detection,
  dependency graphs, affected-test selection, ML prioritisation,
  history-based ranking).

## Quality requirements

- Never invent dependency relationships, test outcomes or results.
- Every important behaviour has automated tests using temporary Git
  repositories, runnable offline.
- Runs on an ordinary student laptop (Windows, macOS, Linux).
- Analysis never executes code from the analysed repository.
