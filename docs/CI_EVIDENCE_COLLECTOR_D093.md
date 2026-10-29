# D093 local CI evidence collector

The collector records public Oak trunk metadata and completed reports. It never
runs builds, calls AI, trains a model, changes Jenkins, or grants skip permission.
The first run imported the inspected D092 snapshots: eight reports and seven
unavailable-report observations. A subsequent public request found all fifteen
already archived and downloaded no new reports. Imported data is not fresh evidence.

A hidden local Python collector was started on 2026-10-29, polling every six hours.
It requires this laptop and process to remain running. It does not restart after
Windows restarts. No amount of polling guarantees a sufficiently long archive.

Store: `build/d093-ci-archive/` in the core-evidence worktree (ignored by Git).
Each observation has its own event and SHA256-addressed compressed response.
Earlier failures remain preserved. Historical publication times are not inferred.
Missing reports are not passes and are not repeatedly fetched by default.

The PID is saved in the pointer workspace `.diagnostics/d093-ci-collector.pid`.
Logs are `.diagnostics/d093-ci-collector.log` and `.err` in that workspace.
Inspect that PID's command before stopping it; PIDs may be reused after exit.
Stop only this collector with PowerShell `Stop-Process -Id <verified collector PID>`.
Restart from the worktree with:

```powershell
& 'C:/Users/hp/OneDrive/Documents/GitHub/codedna/.venv/Scripts/python.exe' -u scripts/ci_evidence_archive.py --store build/d093-ci-archive --watch --interval 21600
```

This foreground command can be stopped with Ctrl+C. Existing archive events remain.
Do not run two collectors on the same store concurrently.

Validation: ten offline research tests passed in 7.56 seconds, covering immutable
archive resumption, errors/variants, bound job identity, decision-before-truth,
completion timing, failed reruns and Maven aggregate parsing. Application source
is unchanged from a02d20f and its separate recorded 780-test validation.
