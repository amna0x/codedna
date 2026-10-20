# CodeDNA — Dataset Plan

> Facts below were checked on 2026-10-20/21 (GitHub API, Zenodo API, the
> RTPTorrent paper and readme). **Downloaded:** RTPTorrent v1.1 into
> `experiments/datasets/raw/` (git-ignored) — see D-032 for version and
> checksum.

## Recommendation (needs team / supervisor approval)

1. **Primary: RTPTorrent** for Milestones 4–5 (history, prediction,
   calibration, fallback). It provides *real* CI test outcomes at test-class
   level for 20 Java projects, already linked to Git commits, with the Git
   repositories included — CodeDNA can compute every feature without
   building or executing third-party code.
2. **Secondary: Defects4J** for a controlled "does selection catch real
   faults?" check (RQ2/RQ4) on bugs in projects such as Commons Lang, Csv and
   jsoup. Needs Perl + SVN + Java 11; awkward on Windows (use WSL or a
   container).
3. **Self-collected (small): Apache Commons CSV** to validate the end-to-end
   `history collect` + coverage pipeline on a modern JUnit 5 project. Runs the
   project's build (`--allow-build`), so only a bounded number of commits.

## Candidate sources

| Source | What it gives | Licence | Status |
|--------|---------------|---------|--------|
| `examples/sample-java-project` | Unit tests, demos | (ours) | ✅ in repo |
| **RTPTorrent v1.1** — Mattis, Rein, Dürsch, Hirschfeld, MSR 2020, [Zenodo 4046180](https://zenodo.org/records/4046180) | 20 Java projects, 2007–2016, >100k Travis CI build jobs; per job and per test **class**: run/failed/errored/skipped method counts, duration, run index; job → commit SHA; bare Git repositories; per-commit changed files; baseline orderings | CC BY 4.0 (cite the paper) | ✅ downloaded (5.0 GB, md5 verified), importer `history import-rtptorrent` |
| **Defects4J** 3.0.1 — [rjust/defects4j](https://github.com/rjust/defects4j) | 854 active real bugs in 17 projects, each with fault-revealing tests (e.g. Lang 61, Jsoup 93, Csv 16, Cli 39, Math 106) | MIT | ⏳ needs Perl, SVN, Java 11 (WSL/container on Windows) |
| **Apache Commons CSV** | ~3.3k commits, single-module Maven, JUnit 5, Java 8 target, active CI | Apache-2.0 | ⏳ self-collect a bounded window |
| **Apache Commons Lang** | ~10k commits, single-module Maven, JUnit 5 (+ junit-pioneer), active | Apache-2.0 | candidate (larger; slower suite) |
| **jsoup** | ~2.6k commits, single-module Maven, JUnit 5 (parallel execution configured), active | MIT | candidate |
| LRTS | Long-running test-selection dataset | — | not checked yet |

RTPTorrent project list (paper, Table 2): Achilles, DSpace, HikariCP,
LittleProxy, buck, cloudify, deeplearning4j, dynjs, graylog2-server, jOOQ,
jade4j, jcabi-github, jetty.project, jsprit, okhttp, optiq, sling, sonarqube,
titan, wicket-bootstrap. Smaller projects with frequent failures are the best
first targets (e.g. HikariCP, LittleProxy, jade4j, jsprit, wicket-bootstrap,
dynjs, Achilles).

### How RTPTorrent maps onto CodeDNA

| RTPTorrent (paper, Fig. 1) | CodeDNA history store |
|---------------------------|-----------------------|
| `<project>/<project>.csv`: travisJobId, testName (class), index, duration, count, failures, errors, skipped | `test_results`: one row per (commit, test class, source = `travis:<job>`); failed if failures+errors > 0, skipped if all skipped |
| `tr_all_built_commits.csv`: tr_job_id, git_commit_id (n:m) | tested commit = tip of the job's commits; change base = state before the push |
| bare Git repository `repo/<project>` | `commits` / `changed_files` + graph/impact features (no build) |
| `<project>-patches.csv`, `-offenders.csv`, `-pr.csv`, `baseline/` | not imported yet (baselines useful for comparison later) |

Caveats from the paper, to handle in the importer and report honestly:

- A build can cover several commits and several jobs (e.g. per platform);
  results are recorded per job, so CodeDNA keeps one row per job as the
  `source` and treats a failure in any job as a failure (D-021).
- Durations below the timer resolution are 0.0 s (~9 % of rows) and a few
  are negative; clamp to 0 and report the count.
- Some original repositories moved; the dataset archives a fork that
  contains the built commits. A few commits (41 in the paper) are missing
  from the repositories — skip and report them.
- Results are class-level (method-level results are not in Travis logs),
  which matches CodeDNA's class-level selection.
- A job can list the same class more than once (one run per module); the
  importer merges these runs (sums counts and durations, any failure wins).

### Imported so far

| Project | Jobs | Jobs imported | Tested commits | Failing commits | Test classes | Notes |
|---------|------|---------------|----------------|-----------------|--------------|-------|
| brettwooldridge@HikariCP | 1,662 | 1,577 | 1,427 | 123 | 23 | 85 jobs without built commits skipped; 21,803 repeated in-job runs merged; 0 negative durations (2026-10-21) |

Derived databases live in `experiments/datasets/derived/` (git-ignored) and
are rebuilt with `codedna history import-rtptorrent`.
- Column names were confirmed against the dataset's readme and files (the
  readme calls the commit column `sha`; the file header is `git_commit_id`).

## Selection criteria for self-collected projects

- Java 8–17, Maven build, JUnit 4/5, single module at the repository root
  (current `run-tests` limitation).
- Builds and runs tests offline after dependency download.
- Enough history (hundreds of commits) and some real test failures.
- Permissive licence that allows analysis and publication of derived data.

## Storage rules

- Raw downloads go in `experiments/datasets/raw/` (git-ignored).
- Private or licence-restricted data goes in `experiments/datasets/private/`
  (git-ignored).
- Commit only scripts that reproduce the dataset, plus small derived summaries
  whose licence allows it (RTPTorrent: CC BY 4.0, attribution required).
- Record for every dataset: source URL, version/commit, download date, licence,
  checksum, and the script that produced each derived file.

## Running third-party builds

Collecting test outcomes requires running other projects' Maven builds, which
executes their code. Do this only for projects chosen deliberately by the team,
ideally inside a container or VM, never automatically on arbitrary input.
RTPTorrent avoids this entirely: its outcomes were recorded by the projects'
own CI.
