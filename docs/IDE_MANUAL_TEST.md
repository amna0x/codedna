# IDE acceptance script

Use a throwaway project with a known change, working Java/Maven or a Python
`.venv` containing pytest. Keep build permission off until explicit consent.
Record date, app/core versions, result and evidence for each step. A source build
is not proof that the installer works on a clean computer.

1. Launch CodeDNA; verify the workspace opens and the core starts.
2. If a workspace trust or system security prompt appears, the human owner must
   handle it. Automation must stop at that prompt.
3. Open Changes (Ctrl+Shift+Alt+D); compare the last commit and WORKTREE.
4. Verify changed methods/files and open a result at the reported file/line.
5. Open a Java symbol; verify completion and F12 go-to-definition.
6. In the throwaway Java project introduce a reversible type error; check the
   diagnostic, then remove the error and check that it clears.
7. Open Tests (Ctrl+Shift+Alt+T). Without valid history, risk selection must
   recommend the full suite with a reason and no invented probability.
8. Open an affected test. Verify its discovered path, including custom roots.
9. Start a run, cancel the confirmation, and verify no build starts.
10. Confirm a run in the throwaway project; verify progress, actual statuses,
    logs and elapsed time. A failing required test blocks the brake. A skipped
    required class/module leaves the brake incomplete.
11. Change the comparison while a recommendation/run is pending; old responses
    must not replace the new selection. Saved prior results remain inspectable.
12. Open Impact graph (Ctrl+Shift+Alt+G); verify changed nodes, explanation paths
    and confirmed/heuristic labels. Structural reachability is not certainty.
13. Open Project history (Ctrl+Shift+Alt+H); inspect passing and failing runs,
    record complete committed full runs, and verify incomplete/skipped runs are
    refused without replacing earlier complete evidence.
14. Open History replay (Ctrl+Shift+Alt+R); use saved reports, not new study runs.
    Open Language plugins; check Java/Python and cancel any installation prompt.
15. Repeat Changes, Impact and Tests in Python-only and mixed repositories.
    Python/mixed risk remains unvalidated/full suite; pytest uses the project's
    `.venv` or explicit interpreter. No interpreter means an actionable error.

## Clean Windows installation

On a separate clean Windows VM/PC without Python or CodeDNA on PATH: install the
new installer, verify bundled Java/Python analysis, repeat steps 1-4, 7-8, 12-15.
Java execution still requires a JDK/build tool; Python execution still requires
an interpreter with pytest and project dependencies. The bundled analysis core
is not a replacement for the project's build environment. Check uninstallation
and retain application logs. Do not call a restricted-PATH smoke a clean-PC test.

Actual execution status is recorded in BLUEPRINT_COMPLETION.md.


## D-073 observed desktop acceptance - 2026-10-27

The rebuilt source IDE with the frozen core was opened on C:/Users/hp/codedna-demo.
Extensions was visible after restart and listed installed Java/Python despite
the online catalogue 404. Project history loaded automatically, displayed the
canonical demo path, and selecting View results revealed and scrolled to both
classes and all six actual saved JUnit check outcomes. No project tests were
executed and no saved history was changed by this acceptance check.

History replay showed a disabled Load results for empty input. Browse opened a
folder-only native picker and populated the chosen actual path. Loading
experiments/results/study11-2026-10-21 succeeded: 55 compatible reports across
11 projects appeared. Reports without trace SHAs are labelled accordingly.
The rolling-evidence and other research summaries use a different format and
are not currently replay inputs; an existing directory alone is insufficient.
This remains a documented format limitation, not a reason to rerun studies.


### Choosing the right replay folder

Use a folder containing `<project>/experiment-seed0.json` (or replay.json /
experiment.json) with compatible `config`, `policies` and per-commit outcomes.
On the owner's laptop this working example is:
`C:/Users/hp/OneDrive/Documents/GitHub/codedna/experiments/results/study11-2026-10-21`.
Browse or paste the path, then choose Load results. A placeholder never loads
data. These older study reports are for replay demonstrations; current
confirmatory findings remain in their own reports and are not replaced by the
demo. Project history instead shows test runs saved from the open project.

## D-080/D-081 analysis-job acceptance (source; packaged check pending)

Automated source checks cover real Windows process-tree cancellation, API
ownership/queue/deadline handling, relative paths and immutable Changes inputs.
The following UI/package cases still need observation in the final rebuilt app;
this list is not evidence that they already passed.

1. Record the app/core versions and source checkpoint. A core advertising
   `analysis_jobs.version = 1` should show actual stages and elapsed seconds in
   Tests and Changes. An older D-074 core should keep synchronous behavior and
   offer no analysis Cancel button. Do not invent a percentage or an ETA.
2. Start a long recommendation, cancel it, and verify no stale recommendation
   appears. Start another operation successfully. No project tests should run,
   no saved history should change and working edits should remain intact.
3. Repeat cancellation during Changes impact. Compare the displayed immutable
   revisions: impact must use the change-analysis result's base/head. Changes
   must not publish half a comparison after cancellation or a comparison change.
4. Open a repository subfolder, inspect Changes and open a file link. Verify
   the canonical repository/file and line selection; links open working files,
   which may differ from the analysed snapshot. A missing working file should
   produce a visible explanation. Late errors must not overwrite a new view.
5. With a controlled trusted plugin fixture, queue an optional update/removal,
   cancel/restart analysis, and confirm the active plugin stays unchanged. Then
   explicitly confirm a test run that restarts the core for build permission;
   that restart must also retain activation. Only restarting the application
   should activate the pending change. Keep official installation/checksums.
6. Close the app during analysis and verify its owned worker/descendants end.
   An unrelated process must remain alive. Capture a real frozen execution
   record in the final installation batch; source entry tests are insufficient.

Ordinary analyses do not resume across an application restart. Research replay
uses its separate saved results/checkpoints. Impact graph/history/replay retain
synchronous UI and are outside this first cancellation rollout.


## D-083 packaged critical workflows — 2026-10-28

The actual isolated win-unpacked package was launched with separate user/config/
plugin stores and a disposable Java project. Measured timing and cold-history
full-suite fallback displayed. A deliberately slow trusted plugin made Cancel
testable: the GUI cancelled without a partial report and both worker/child ended.
After recovery, source-derived test-check names loaded and Read source opened the
actual file. Cancelling build consent created no saved run. Confirming the known
fixture ran real Maven: six checks/two classes, one discount check failed and was
displayed. The uncommitted result was not promoted to training history. Java and
Python remained listed despite catalogue 404; Language plugins restored on restart.
See RELEASE_VALIDATION_D083_2026-10-28.json and its hashed text/image evidence.
The installer payload was extracted and its 1458 core hashes matched. This is
not installation/clean-PC acceptance or a claim that every step above was rerun.
The standalone demo lacked target/ ignore; editor-generated binaries appeared
as warnings. Sample-project cleanup is next; conservative core rules stay intact.
