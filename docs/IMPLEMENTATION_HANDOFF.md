# Java workflow handoff

## Current review — 2026-10-25

The checkout now contains merged impact-graph, history-replay, multi-module
build, WORKTREE, static website/catalogue and Windows launcher changes. HEAD
at the start of this review was `97c3be7`. The older sections below describe
the 2026-10-24 implementation batch, rather than the complete current scope.
Use `docs/ROADMAP.md` for milestone status.

Replay input validation now rejects malformed traces, inconsistent lengths,
non-finite or out-of-range metrics, impossible test counts and invalid missed
test names. Discovery skips malformed/unreadable reports so one corrupt file
does not prevent loading valid studies. The API returns a clear 400 error.
Saved experiment files are unchanged. IDE extension compilation passed.
Full suite with `--run-maven`: 315 passed, 1 skipped (Gradle initially absent),
1 existing Starlette/httpx warning, 690.91 seconds. The skipped test passed
separately after Gradle installation, covering all 316 collected tests.
Portable Gradle 8.14.3 is now checksum-verified under
`C:/Users/hp/.codex/tools/gradle/`; its real multi-project integration test
passed separately (193.76 seconds). Runtime metadata and the official source
URL/checksum are in that folder's `runtime.json`.

GitHub authentication worked on retry on 2026-10-24. Claude's changes and later
work have since been merged into this checkout; the authentication failure
below is historical. This review does not publish new commits or claim current
remote CI results. See the standalone desktop continuation below for packaging
validation and its remaining interactive/clean-machine checks. Final report and
supervisor review still need attention.

## Standalone desktop continuation — 2026-10-25

- D-050: build-only PyInstaller 6.22.0 extra; Windows onedir Python/ML/API core,
  file-hash/version manifest, Electron resources integration, explicit executable
  override before bundled-core lookup, normal PATH fallback for source builds.
- The first broad scientific-package collection was stopped because it dragged
  in dependency test suites. The verified build uses the standard runtime hooks
  instead; no GPU libraries or scientific test suites are intentionally required.
- `npm run package --workspace electron-app -- --config.directories.output=...`
  passed: freezer, TypeScript, native rebuild, pinned extension deployment,
  production frontend/backend/Electron bundles, NSIS installer and block map.
  For this local build `ELECTRON_BUILDER_COMPRESSION_LEVEL=3` was used, with
  output staged outside OneDrive to reduce sync overhead.
- Installer: `ide/electron-app/dist/CodeDNA IDE Setup 0.1.0.exe`, 339,622,119 bytes,
  SHA-256 `88d486030d66a450edd1763df68f611aaa8806104a9ec92dd6fabc6f96140f93`.
  It is not code-signed. `7za t` found the embedded payload intact; it also
  reports trailing data from the NSIS wrapper. All 1,354 packaged-core files
  matched the bundle manifest. `dist/validation.json` records local evidence.
- Both standalone and exact packaged-core smoke checks passed with Python,
  virtualenv and source import paths removed from the child environment:
  version, Java analysis/discovery, synthetic model/calibration fitting, API
  graph/risk fallback and real sample Maven execution. Proof:
  `build/desktop-core/packaged-smoke-validation.json`. Synthetic fitting is a
  packaging check and adds no research-performance evidence.
- The packaged Electron app reached the ready workbench state and deployed both
  Java extensions. A fresh profile took about 100 seconds during concurrent
  builds/tests; this is not a controlled startup benchmark. The app is left open
  on a disposable demo. Interactive controls, Java completion and progress were
  not accepted: window capture repeatedly reported minimization, and activation
  recovery returned `user input was detected in this window`.
- Computer Use's `SKILL.md` points to its guidance, which requires refreshing
  selection and retrying once, then says to "report the exact error if recovery
  fails". UI input stopped after that recovery failed. CLI/API and build
  validation continued. No Windows security/privacy settings were changed.
- `start.bat` now finds the installed portable Gradle and reuses its cache while
  preserving an explicit GRADLE_USER_HOME. Metadata reads use literal env paths;
  the misleading no-JDK/no-Java-completion warning was corrected. Six launcher
  tests passed, including paths with spaces and a custom Gradle cache.
- Final full validation: `python -m pytest --run-maven -q`, with Git/JDK/Maven/
  Gradle on PATH and OMP/OPENBLAS/MKL thread counts set to 1: **322 passed,
  zero skipped**, 814.16 seconds, one existing Starlette/httpx warning. Three
  Node runtime tests passed. Graphify final AST refresh: 2,102 nodes, 5,270
  edges, 129 communities. Documents were not semantically re-extracted.
- No commits, pushes, publication or clean-machine installation were performed.

## Original implementation batch — 2026-10-24

## Latest status — 2026-10-25

Full local suite after all changes: **334 passed, zero skipped**, 897.94 seconds,
with real Maven/Gradle and one existing Starlette/httpx warning. Three Node
runtime tests passed. Installer source builds/production bundling passed.
The exact shipped core detected a deliberate regression in a disposable repo
while running exactly the requested Maven class. Both pinned VSIX archives
were downloaded and SHA-256 recorded; 577 shipped files matched byte-for-byte.
One `.d.ts` file is omitted by Electron Builder's production filters. Full
local evidence is `ide/electron-app/dist/validation.json`.

A tested one-time fresh-project continuation is running, waiting on the earlier
nine-project raw downloader; it does not start another network download. It
will verify the complete 74-file cache, build all nine history DBs and projected
feature CSVs, then evaluate the fixed study. See the status JSON under
`experiments/datasets/confirmatory-live-2026-10-25/` and the log
`build/confirmatory-continuation.log`. At queue time 41/74 raw entries (~2.5 GB)
were verified. No new confirmatory verdict is claimed. Preserve the existing
producer and the continuation's frozen code/protocol/library set. D-051 and the
dated preparation note document row-level input equivalence and cache reuse.

The installer is unsigned; clean-machine installation and interactive Java
editor/progress acceptance remain unverified. Computer Use's
[SKILL.md](C:/Users/hp/.codex/plugins/cache/openai-bundled/computer-use/26.1021.31345/skills/computer-use/SKILL.md)
refers to [recovery guidance](C:/Users/hp/.codex/plugins/cache/openai-bundled/computer-use/26.1021.31345/docs/guidance.md),
which says to "report the exact error if recovery fails" after retry. The
observed errors were `window is minimized` and
`user input was detected in this window` after fresh selection/recovery. No
further UI input was attempted; build/API validation continued.

No source commit, push, PR publication or deployment was performed.

## Decision against original scope

Completing this work is aligned with CODEDNA_STARTER.md sections 2, 8, 11 and 19:
calibrated risk, broader/full-suite fallback, explanation, baseline evaluation and
an end-to-end demonstration. Additional languages remain deferred at the owner's
request. This does not declare every original FYP milestone complete.

## Completed

- Focused four-paper comparison, working claim and fixed experiment protocol.
- Initial independent history proxy preserved with source snapshots; separately
  fixed closer adaptation after retrieving the author artifact. Four projects ×
  five seeds, raw/calibrated stopping, actual-time matching, intervals and hashes.
- Final calibrated adaptation meets all four observed 5% targets; its pooled
  safety gain +0.0460 [-0.0500, 0.2806] is not statistically established. Simple
  rules remain the live default. No full-DANTE/universal/superiority claim.
- Target-bound 50/25/25 train/calibrate/audit gate, with conservative evidence
  checks and full-suite fallback. Shared audit logic stays in core; Java inputs
  stay behind the existing plugin's additive optional `risk_select` hook.
- CLI/API and IDE risk status, explicit build consent, recomputed immutable
  selection, real selected Maven execution and actual result display.
- Full test suite: 245 passed, zero skipped, 499.39 seconds. Full IDE build passed.
  Live sample passed; deliberate regression then produced two failing classes
  shown in the IDE. Actual JSON evidence is saved in the final study validation.
- Graphify code graph refreshed: 1,539 nodes, 4,043 edges. AST-only refresh;
  changed documents have not been semantically re-extracted.

## Environment repaired

Installed Microsoft's signature-verified Visual Studio Build Tools 17.14.42 and
Windows SDK 10.0.26100 for native Electron modules; no restart performed.
Installed the lockfile-pinned IDE dependencies and Electron 42.8.1; built the
host-side `@theia/ffmpeg` addon omitted by script-free install. Existing portable
JDK/Maven metadata remains at `~/.codex/tools/java-maven.json`. The IDE demo is
running against a disposable sample, not the CodeDNA source repository.

## Review and publication limits

The private Git remote rejected the saved credentials. Claude's remote branch
could not be recovered, and no PR was opened. No commit or push was made in this
source checkout. Existing earlier uncommitted work was preserved. Restore GitHub
authentication before remote review/publication; do not claim CI passed.
Supervisor sign-off and a full prior-art novelty assessment remain outstanding.

## Remaining original scope

Interactive graph view, Java editor language support, long-job progress,
uncommitted-change analysis, packaging/installers, and final report/defence
review remain roadmap work. The website/catalogue and further languages are
later work. No paid LLM API is required by the analysis/selection engine.

## Start/use

See JAVA_WORKFLOW.md for preparation, risk rules and CLI execution; ide/README.md
for build/start. New risk defaults require genuine target full-suite history;
there is no automatic universal pretrained model or fabricated onboarding data.
