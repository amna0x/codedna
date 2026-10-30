# D099 catalogue endpoint correction — 2026-10-30

The app's official catalogue URL omitted the published website subdirectory.
Verified the old /codedna/catalogue/index.json returns404, while
/codedna/website/catalogue/index.json returns200. Corrected only
OFFICIAL_CATALOGUE in backend/codedna/plugins/manager.py. The production catalogue
fetch/validation succeeds and lists bundled Java/Python. No wheel releases are
published in that index; a reachable catalogue does not imply extra downloadable
language plugins exist. Official-release URL checks, checksum verification and
installation confirmation remain unchanged.

The running development IDE still uses the original checkout; the correction is
on codex/core-evidence-improvements. Pull/use this branch for source development,
or include the correction in the final package after UI polish. Restarting an
old binary alone does not change its embedded URL. D098core candidate predates
this one-line fix; its32executable checks are historical and not a validation of
the updated packaged URL. Final package needs fresh affected endpoint/payload checks.

During live support the visible blank Changes list was the editor's Source
Control view. Opened actual CodeDNA Changes viaCtrl+Shift+Alt+D, selected My last
commit and pressed Show changes. It displayed4files/6codeelements/2possibly
affected classes, including PriceCalculator.applyDiscount(). No files edited or
tests executed through that UI. Friend UI task: distinguish these two Changes
views and make the first-run action clear.

Validation: python -m pytest backend/tests/test_plugin_manager.py -q completed
18passed/0failed in146.51seconds, with one existing Starlette/httpx deprecation
warning. No full source suite or rebuilt package is claimed for this small fix.
