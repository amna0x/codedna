# Friend handoff — 2026-10-30

Use branch `codex/core-evidence-improvements`. This contains the current core and
research work; main does not yet contain these commits. Create your UI branch
from this branch, not from an older installer or main. Do not force-push or merge
other branches just to start UI work.

## Your task

The owner wants you to make the desktop UI clearer and visually polished.
Start with Changes, Tests to run, Impact graph, Project history and Language
plugins. Make the workflow understandable to someone who does not read Java:
what changed, why tests are suggested, what each test checks and what results mean.
Keep analysis logic in the Python core. Preserve explicit build consent,
cancellation, failure visibility and conservative full-suite fallback.

UI sources are in `ide/codedna-extension/src/browser/`; desktop packaging lives
under `ide/electron-app/`. Follow `ide/README.md` for prerequisites/build/run and
`docs/IDE_MANUAL_TEST.md` for affected-screen acceptance. Read AGENTS.md first.
The website is separate; do not replace its independent work with this branch.

## Already completed

Validated application commit a02d20f4d36b451dd80b2948d5bdcc0a6620ecd7 passed780source
tests with Maven/Gradle and no failures/skips. Later commits are research,
validation and handoff work, not new product features. D098 rebuilt that core;
32executable regression checks passed for plugins/restarts, cancellation, brake
Maven execution, witness reproduction and process cleanup. See
CORE_CANDIDATE_D098_2026-10-30.json. The generated executable is local build output,
not included in Git and not a final installer.

Research expansion is closed. Moonshot has two successful controlled benchmark
programs, with unsupported cases retained. AI-brake savings remain unproven in
new sparse-history studies. Do not relabel this as universal success or weaken
risk/history gates. See RESEARCH_CLOSURE_D097.md and REPORT_DRAFT.md.

## After UI polish

Run relevant UI/type/runtime checks and the manual affected-screen workflow.
Then build the final installer using the current core and your verified UI.
Older D085/D086installation kits do not contain the final core improvements.
Final installer extraction/hash checks and clean-PC acceptance remain open.
Follow CLEAN_PC_ACCEPTANCE.md and return the smoke JSON plus observations.
Do not mark the whole release complete based only on source or development-PC
checks. Research datasets, dependency caches, local paths and build outputs may
not exist on your machine; do not substitute invented data.

No new features/languages or further research tuning are requested. Both original
stashes and the private-email backup branch are unrelated to this handoff: never
apply, commit or publish them. See MEMORY.md for detailed evidence/history.
