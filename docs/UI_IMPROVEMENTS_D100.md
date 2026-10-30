# D100: clearer workflow, themes and before/after comparisons

Implemented owner-requested UI improvements on codex/core-evidence-improvements.
No independent uncommitted UI edits were found in the original development
checkout before copying changed sources there. Old copies were backed up in the
core-evidence .diagnostics/d100-original-ui-backup directory. Demo project files
were not edited; no project test builds were run for this UI work.

## Behaviour

- CodeDNA's sidebar tab is now Code changes, distinct from Source Control Changes.
- Labelled Review changes / Check tests / Impact map / Past runs / Languages
  navigation is available across CodeDNA panels. Stable open commands reveal a
  view rather than toggling it shut. Keyboard shortcuts remain available.
- Appearance selector offers Graphite dark, Ocean dark, Clear light and High
  contrast, using Theia's persisted theme service.
- First-run instructions explain the workflow and what a test means.
- File cards offer Compare before / after and a separate Open current file.
  Clicking changed methods opens the before/after editor. Added/removed/renamed
  files use the correct snapshot sides, including removed methods.
- Historical contents come from exact immutable SHA/path pairs, loaded into
  built-in read-only Theia resources. Working files are not overwritten. The
  Node service reads Git text with no shell, external diff or textconv; it
  rejects traversal/non-SHA revisions, binary NUL contents, >1MB output and
  operations exceeding15seconds. Errors remain visible, never empty success.
- A comparison completing after the selection changes is not opened.

## Verification and limits

TypeScript noEmit passed. All48existing UI checks passed in4.86seconds;10new
checks passed in2.85seconds. New tests use a real temporary Git repository to
check immutable reads, invalid paths/revisions and missing files, plus actual
widget methods for added/deleted/renamed/stale handling, theme registration and
stable navigation. Initial sandbox temp-Git failure was rerun with normal temp
access; it was not an application failure. An initial local source-writing
encoding error was corrected before successful type/build checks.

Original development copy extension compilation and Theia browser/node/electron
build completed with0errors. Nonfatal optional react-dom/windows-ca-certs notices
remain. Source code and automated tests are verified. GUI navigation, visual theme
contrast and the actual diff editor were NOT verified interactively: the app was
closed and current computer-use session did not successfully relaunch it. Open
start.bat in the original checkout for manual acceptance. Do not call this a GUI
pass or final packaged release. Old installers and D098core were not rebuilt.

The original checkout now has the corresponding uncommitted UI source changes,
plus the already-applied catalogue endpoint fix. Do not discard these when your
friend changes branches; the same authored UI changes are committed on the shared
handoff branch. UI test helper gained extra tests after the original copy was
synced; the committed helper is authoritative.

## Manual acceptance

1. Open the normal start.bat and the demo project.
2. Ctrl+Shift+Alt+D opens Code changes. Confirm labelled navigation appears.
3. Choose My last commit, Show changes, then PriceCalculator.applyDiscount().
4. Confirm Before/After panes show removed/added lines and are read-only. Open
   current file should still open the editable working file separately.
5. Choose Check tests, verify suggestions and conservative risk explanations.
6. Try each Appearance option, keyboard focus and restart persistence.
7. Confirm Languages refresh uses corrected published catalogue path.
8. Report any missing resource resolver/diff editor/theme issues; do not hide them.

Core selection/research safety rules and build confirmation remain unchanged.
Research is still closed under D097. Complete visual acceptance before installer
packaging and friend clean-PC acceptance.
