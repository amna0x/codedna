# Complete Java recommendation/execution workflow

The Python engine runs locally without an LLM or paid API. Java/Maven/JUnit is
the supported execution ecosystem. The IDE displays core results; no model or
selection logic lives in TypeScript. Additional languages are deferred at the
owner's request until the software workflow is complete.

## First use: no history

Open a Java Git repository, choose the comparison, and open **Tests to run**.
The default **Validated risk stopping** strategy reports **Risk unvalidated**
and recommends all discovered Surefire test classes when target evidence is
missing or insufficient. It does not invent a calibrated risk percentage.
**Affected tests only** remains an explicit structural alternative with no
validated omission probability.

Choose **Run recommended test classes** and confirm execution of project code
and Maven plugins. The server starts with builds disabled and is restarted with
permission only after this action. Each execution request also requires consent.
Selection is recomputed on the immutable base/head SHAs before execution.

The commit is exported into an isolated checkout. The runner validates requested
IDs against discovered classes, includes nested tests, refuses unknown/wildcard
filters, and never turns an empty selection into an accidental full-suite run.
Results include actual statuses, failing classes, duration, warnings and logs.
Output is stored in `REPO/.codedna/runs/<unique-id>/`; the source checkout is not
built or edited. Add `.codedna/` to the analysed project's ignore rules.

## Prepare trustworthy target history

Prefer existing full-suite CI reports; do not rerun years of third-party builds
unless deliberately authorised. Test-class results must cover the current test
universe in the audit window; selected-only reports are insufficient evidence.
The existing history import/collect commands can build the database. For example,
for a repository you trust (replace paths and BASE):

```powershell
codedna history mine --repo PATH --rev BASE --db PATH/.codedna/history.db
# Import full-suite results already recorded at these commits:
codedna history import --db PATH/.codedna/history.db RUN_DIRECTORY_1 RUN_DIRECTORY_2
codedna history evaluate --db PATH/.codedna/history.db --repo PATH --no-structural --rankers recent_failures --dataset-csv PATH/.codedna/history.csv --output PATH/.codedna/history-evaluation.json
codedna risk-select --repo PATH --base BASE --head HEAD
```

`history collect` is available for deliberately authorised builds, requires
`--allow-build`, and can take hours; it is not run automatically by analysis.
Use the IDE's optional history-file field to choose another exported CSV.

## What risk validation means

The live 15-feature predictor uses only change, changed-test and historical
features available before execution. It excludes structural/co-failure features
requiring historical graph replay. This is an operational variant with its own
audit, not the original 19-feature model silently reused under different inputs.

First 50% of prior target commits train balanced gradient boosting; next 25%
calibrate with isotonic regression; latest 25% independently audit the frozen
model and recent-failure/B10 stopping rule. No current target label fits the
model, and the model is not refitted after the audit. History is tied to actual
first-parent ancestors, must end at BASE, and cannot contain HEAD or unrelated
project commits. Operational use supports the next first-parent Java change.

The fixed gate needs an observed-miss one-sided 95% Wilson upper bound no larger
than the selected target (default 5%), at least ten failing audit commits and
at least 90% failing-test recall. Audit commits must record every current class.
Unsupported changes, stale/invalid data, absent calibration or failed evidence
keep the full-suite recommendation. The proposed subset risk remains distinct
from the chosen full-suite fallback; unvalidated numbers are not presented as
trusted probabilities.

The screen assumes representative history and its confidence bound treats
commits as independent. Real histories violate these assumptions, so acceptance
is not a future safety guarantee. Periodic full-suite audits must refresh data;
selected-only runs cannot reveal omitted failures. The app never silently
replaces the user's base snapshot with future outcomes.

## Direct selected execution

```powershell
codedna run-tests --repo PATH --rev HEAD --output-dir NEW_OUTPUT --tests example.PriceCalculatorTest --allow-build
```

The command executes project code only with the explicit flag. Empty `--tests`
means no Maven invocation; omitting `--tests` means the full suite.

## Remaining original scope

The code graph is available through the CLI/API; an interactive IDE graph view,
Java editor language support and distributable installers remain roadmap work.
The new workflow completes the risk display/selected execution slice; it does
not declare all original FYP milestones complete or establish general model
superiority. Closest-work comparison and supervisor sign-off remain necessary.
