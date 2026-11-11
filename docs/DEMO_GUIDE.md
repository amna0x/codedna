# CodeDNA: teachable demo

## Say this first

“When code changes, running every test can take time. CodeDNA shows what changed,
what else might be affected, and which existing tests to run. It explains its
recommendation. If earlier project history cannot justify skipping tests, it
keeps the full suite.”

Regression testing means checking that a new change did not break behavior
that worked before. CodeDNA selects tests already written in the project;
it does not generate those tests.

## How the project works

1. **Git comparison:** read two saved versions, or compare the latest commit
   with saved file edits. Unsaved editor text is not included.
2. **Language plugin:** parse changed Java or Python code and map edits to
   classes, methods or functions. Java uses Tree-sitter; Python uses its AST.
3. **Impact:** follow reverse dependency links to code and tests that might
   depend on changed code. Confirmed and heuristic links remain distinct;
   missing or unresolved links are recorded, not guessed.
4. **Recommendation:** use the selected policy. The default uses earlier
   project history only when its audit supports risk-based skipping; otherwise
   run all discovered tests. Structural selection follows code links and has
   no validated failure probability.
5. **Execution:** after the user confirms, run project tests in an isolated
   export. Display actual outcomes and logs. Eligible complete committed runs
   can contribute to project history; uncommitted or partial runs cannot be
   treated as complete training evidence.

The Theia/Electron IDE displays results. Its Node backend talks to the Python
core's loopback API. Analysis lives in Python; Java and Python details live
in their language plugins. Saved research results are separate from live runs.

## Prepare the demo

From the repository root, create a demo in a folder that does not yet exist:

```powershell
.venv\Scripts\python.exe scripts\make_demo_repo.py build\beginner-demo
.\start.bat build\beginner-demo
```

If the demo already exists, launch it with the second command. First launch
after a pull may need an IDE rebuild. Running Java tests requires a JDK and
Maven. If the launcher does not find them, set `JAVA_HOME` and `MAVEN_HOME` to
their installation directories before running `start.bat`.

## Five-minute demo
1. **Explain the problem** using the opening sentence above.
2. Open **Changes** with `Ctrl+Shift+Alt+D`. Choose **My last commit**, then
   **Show changes**. A commit is a saved version in Git.
3. Show `PriceCalculator.applyDiscount()`: it now rounds discounted prices
   through a new `Rounding` class. Also show the renamed test and README edit.
4. Explain the dependency example: `OrderService` uses `PriceCalculator`, so
   it might be affected. Open the source from its result row.
5. Open **Tests to run** with `Ctrl+Shift+Alt+T`. Keep the recommended method;
   click **Suggest tests**. This does not execute project code.
6. Expect **2 of 2 test classes**: `OrderTotalsTest` and `PriceCalculatorTest`.
   The verified cold-history response says **No target-project test history is
   available**, with no invented risk percentage. The README change also makes
   the structural policy conservative. Recommending everything here is expected.
7. Use **Explain this test** to inspect source-discovered check names, and
   open its source. These names are not execution results.
8. If Maven/JDK are ready, the human user can choose **Run 2 recommended tests**
   and approve execution. Explain actual statuses only after a completed run.
   Otherwise finish with recommendations and disclose that execution is unverified.

Optional: open **Impact graph** (`Ctrl+Shift+Alt+G`) to show the same links.
Leave History replay, plugin management and custom history files out of the
first walkthrough; introduce them after the basic flow is understood.

## Useful answers

| Question | Answer |
|---|---|
| Does “affected” mean broken? | No. It means a dependency path was found. Run tests to observe failures. |
| Why recommend every test? | Evidence is insufficient, changes exceed supported analysis, or project rules require it. Expand recommendation evidence for the actual reason. |
| Does one passing run make skipping safe? | No. Earlier history needs enough relevant evidence and a separate audit. |
| What does the model do? | Estimate test-failure probabilities from earlier changes/results; calibration and an audit check whether they support stopping. No guarantee for an individual change. |
| Does ML always beat simple rules? | No. Existing studies have mixed results; learned ordering did not beat simple rules in the original study. |
| Can I demonstrate partial selection? | Use a separate prepared history-backed demo. `demo_brake_end_to_end.py` uses explicitly synthetic history, so its numbers are mechanism illustrations, not research findings. |

## Verification for this checkout

Read-only CLI checks on the prepared demo found four changed files, two impacted
types, and two recommended test classes out of two. Risk status was unvalidated,
with estimated skip risk absent. No demo project code was executed.

Source checks: `npm run build:extension` passed; `npm test --workspace
codedna-extension` passed all 51 tests. `python -m pytest --run-maven` was
attempted: first collection failed until the newly separated plugins were
installed, then a full run remained incomplete after the 10% progress line.
No complete backend-suite result is claimed. A separate explicit check,
`python -m pytest --run-maven -q backend/tests/test_maven_integration.py`,
failed once with `Maven (mvn) not found on PATH`. These are historical failed
attempts, not the current validation result.

2026-11-02: after configuring supplied Maven, fixing Windows launcher discovery
(D-087), and installing missing declared test dependencies, the complete run
`.venv\Scripts\python.exe -u -m pytest --run-maven -q
--junitxml=build/maven-verified-20261102.xml` passed: **717 passed, 1 skipped**,
one existing warning, 586.82 seconds. Gradle was the only skip (not installed).
Real Maven coverage, multi-module execution and brake-demo tests passed in
disposable test fixtures. Log: `build/maven-verified-20261102.log`.
Full source IDE build also passed after the optional Windows certificate-addon
fix. Packaged-app rebuild and visual acceptance of these UI edits remain separate.
