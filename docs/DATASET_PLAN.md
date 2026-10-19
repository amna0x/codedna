# CodeDNA — Dataset Plan

> Nothing has been downloaded yet. Before using any dataset, verify its
> current URL, licence, and Java/tool versions, and record them here.

## Candidate sources

| Source | Use | Status |
|--------|-----|--------|
| `examples/sample-java-project` | Unit tests, demos | ✅ in repo |
| Defects4J | Real Java faults + triggering tests; controlled evaluation | ⏳ verify licence/setup |
| RTPTorrent | Historical CI test results for prioritisation studies | ⏳ verify availability |
| LRTS | Long-running test-selection dataset | ⏳ verify availability |
| Selected open-source Maven projects | Full-suite outcomes per commit (self-collected) | ⏳ choose projects |

## Selection criteria for self-collected projects

- Java 8–17, Maven build, JUnit 4/5.
- Builds and runs tests offline after dependency download.
- Enough history (hundreds of commits) and some real test failures.
- Permissive licence that allows analysis and publication of derived data.

## Storage rules

- Raw downloads go in `experiments/datasets/raw/` (git-ignored).
- Private or licence-restricted data goes in `experiments/datasets/private/`
  (git-ignored).
- Commit only scripts that reproduce the dataset, plus small derived summaries
  whose licence allows it.
- Record for every dataset: source URL, version/commit, download date, licence,
  and the script that produced each derived file.

## Running third-party builds

Collecting test outcomes requires running other projects' Maven builds, which
executes their code. Do this only for projects chosen deliberately by the team,
ideally inside a container or VM, never automatically on arbitrary input.
