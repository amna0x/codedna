# Cancellable analysis jobs - implementation plan

Status: D-080 source integrated, 2026-10-28. Authenticated job routes and
capability-gated Tests recommendation cancellation are implemented. Other IDE
views keep their existing synchronous UI. Thirty-three integrated Python checks,
four later cleanup checks and 35 Node workflows pass; TypeScript compiles.
Full Maven-inclusive D-080 validation remains required. D-079's earlier 601-test
full run passed. No actual new frozen executable was built; that validation and
installation remain deferred. No ordinary-analysis restart resume is claimed.

## Existing boundary

The local API currently performs synchronous analysis in FastAPI worker threads.
The IDE backend forwards JSON and the frontend shows a stage label and elapsed
seconds. Aborting a fetch would stop waiting, not cancel the underlying Git or
analysis work. Killing the shared API would also disrupt unrelated requests.
Neither behavior should be presented as successful per-operation cancellation.

## Scope and contract

Add optional authenticated jobs for read-only discovery, change analysis, impact
and selection (including risk selection). Keep synchronous routes compatible.
Build/test execution, plugin changes, history import and recording remain outside
this first job API; preserve their existing explicit execution consent.

A submission validates one of the existing typed request bodies and returns a
random operation ID. A status/result request returns queued/running/completed/
failed/cancelled, actual stage name, elapsed time and the unchanged core JSON
result only after completion. A cancellation request addresses a registered
operation ID, never an externally supplied PID. All routes keep the existing
loopback-host and per-session-token protections.

Bound active work and queue size on a student laptop. Reject excess submissions
clearly rather than creating unbounded processes. Keep completed records for a
bounded session lifetime; discard expired in-memory records without removing
project history or research files. No accounts, remote queue, Redis or database.

## Worker ownership and cancellation

Run each operation in its own trusted CodeDNA worker, with argument lists and
hidden Windows windows. Source mode can launch the Python module. Frozen mode
requires a dedicated private entry switch; never assume a packaged executable
is a Python interpreter that supports `-m`.

On Windows, contain the worker and its Git descendants in a Job Object with
kill-on-close semantics before it receives its analysis request. On platforms
with process groups, isolate the worker group. Cancellation terminates only the
owned worker tree and waits for cleanup. Do not enumerate unrelated laptop
processes or terminate the shared API. If containment cannot be established,
refuse to advertise reliable cancellation for that operation.

A cancellation flag is absorbing: a late worker response cannot restore a
cancelled operation as completed. A crash or deadline expiry yields a failed
operation and bounded diagnostic detail. Closing the IDE cleans up its owned
workers. Workers never execute scripts from the repository under analysis.

## Honest progress and evidence

Report a stage only when the worker enters it. Show counts/percentages only when
both a measured completed count and a known total exist. Otherwise retain the
current stage plus elapsed time. Resolve revisions to immutable commit IDs and
include those IDs in the result. Preserve WORKTREE snapshot semantics and
existing fallback/CRC behavior. UI generation checks discard obsolete results
when the comparison changes; duplicate clicks cannot enqueue duplicate work.

Long research replay already has fingerprinted source checkpoints and its new
read-only viewer. Do not imply that ordinary analysis can resume after an IDE
restart until an input/version-bound checkpoint format exists for it.

## Cache and runtime tradeoff

The core already has a bounded blob-keyed parse cache and plugin capability
fallbacks. Reuse these contracts; do not invent another dependency graph cache.
Per-operation isolation may lose cross-request in-memory reuse. Measure cold and
warm behavior, report startup separately, and compare identical output before
adding persistent reuse. Never reuse risk acceptance across different history,
comparison, policy or code identities. Pilot wall times collected while the
full test suite runs are local feasibility observations, not CI benchmarks.

## Acceptance before enabling the UI

Use temporary Git fixtures and offline trusted sleeper helpers. Test typed-input
rejection, token/host protection, queue bounds, progress ordering, terminal-state
races, exact result equality with synchronous selection, stale UI responses and
worker crashes. On Windows verify that cancelling a worker also ends its owned
child and leaves an unrelated fixture process alive. Verify no project history
was written and a later analysis still works. Include source/frozen dispatch
checks. Run the full Maven-inclusive suite and the Node workflow suite.

The IDE should expose cancellation only when the connected core supports this
contract. An older packaged core retains the synchronous path without a fake
cancel button. Actual frozen validation and the installer refresh are deferred
to the final installation batch under the owner's latest instruction.


Worker lifecycle constraint: preserve the parent process's active language-plugin
snapshot across cancellation/restart. A pending optional-plugin update must not
become active in a replacement worker before the application's required restart.
Test this against D-074 activation and bundled-fallback semantics. If measurements
justify a persistent parse-cache worker, allow only one active operation in that
worker, bind every response to its operation ID, and kill/recreate that owned
worker on cancellation. Never cache audit acceptance across changed history.

## Implemented bounds and lifecycle

The API exposes typed submissions under `/api/analysis-jobs/{operation}` for
`tests`, `analyze`, `impact`, `select`, and `risk-select`, status by registered
ID, and POST cancellation by ID. One worker is active; at most two jobs wait.
Results expire after 600 seconds and at most eight records are retained. Each
protocol message is capped at 8 MiB, and no more than 32 worker events are read.
Queue saturation returns HTTP 429; expired/foreign IDs return 404. Completed
results keep the core JSON, including independently measured analysis time.

A contained worker waits for stdin before importing analysis/plugin code or
receiving project input. Windows uses a kill-on-close Job Object; POSIX uses an
isolated process group. Actual process-tree tests ran on Windows only. A cleanup
failure is reported, stops dispatch and never becomes successful cancellation.
Lifespan shutdown closes owned workers. A cancelled ordinary operation cannot
resume; the separate research runner's checkpoint format is unchanged.

Plugin activation is inherited from the current core's snapshot rather than
re-reading a pending active.json manifest. The IDE backend retains the snapshot
when it restarts the core after explicit build consent. The private frozen
worker switch runs before default plugin activation. Failed parent activation
preserves visible errors and bundled fallback. Invalid bootstrap paths fail
closed. No arbitrary executable/PID/path-to-plugin is accepted by job routes.

The Jobs capability is optional. New source UI with an older packaged core
falls back to synchronous analysis without advertising cancellation. Worker
startup and lost in-memory parse-cache reuse may add overhead; this work
improves responsiveness and ownership, not a claimed CI speedup. Actual new
frozen execution, clean-PC validation and installer refresh remain last.
