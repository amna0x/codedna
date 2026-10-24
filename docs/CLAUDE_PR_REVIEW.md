# Recovered Claude work and next priorities — 2026-10-24

GitHub access succeeded on retry. The earlier response was an authentication
failure, not a code rejection; its exact credential cause was not reported.
No credential values were logged or stored in this review.

Existing PR: https://github.com/mohibk0004-del/codedna/pull/1
Branch: `claude/dante-b10-stopping`; reviewed head
`c9d81829d28ea6939dfa5238a23cf3b9a1446fd4`. PR is open, not merged. Seven
reported CI checks all succeeded: Python 3.11/3.12 on Windows/Ubuntu, IDE
extension compilation, sample Java and real Maven/JaCoCo integration.
Those checks cover Claude's branch, not the newer unpushed local implementation.

## Reconciliation needed

Claude completed a protocol, DANTE-H experiment, target gate and risk view;
its code/results now exist remotely. The earlier local reconstruction happened
while private remote access failed. Both implementations should be reviewed and
consolidated, not blindly merged or maintained as competing runtime paths.

Verified differences include: Claude uses a 60/20/20 gate and defaults to a
10% Wilson upper-bound allowance for a 5% observed target, with three failing
validation commits. Local code uses a separate 15-feature 50/25/25 gate,
upper bound <= the selected target, ten failing audit commits and >=90% recall,
plus strict history freshness/completeness checks. Local Java-specific features
stay behind the existing plugin; selected execution is live-verified in the IDE.
These policy/model differences require deliberate reconciliation rather than
comparing headline study numbers as if the methods/environments were identical.

No source files were overwritten by fetching the remote branch. No merge, source
commit, push, PR edit or review message was sent in this retry.

## What uncertainty means

The final local DANTE-history adaptation's mean same-cost safety differences are:
HikariCP 0.0000, LittleProxy 0.0000, jade4j 0.0000, wicket-bootstrap +0.1839.
The pooled point is +0.0460, with 95% interval [-0.0500, 0.2806]. This is not
consistent evidence of an advantage across projects. Test failure counts are
20 / 5 / 2 / 87; additional seeds do not create more independent projects.
See the study's `uncertainty-audit.json` for saved-report hashes and calculations.

Software checks are separate: 245 local tests passed without skips; the full
native IDE build and real passing/failing sample execution passed. This supports
working software, not guaranteed prediction accuracy or a new research theorem.

## Next order of work

1. Reconcile Claude's PR with the tested local implementation, review one coherent
   change set and publish it. Do not merge an older duplicate implementation
   simply because its CI is green.
2. Pre-specify broader independent projects and time windows, adequate failure
   evidence, strong baselines and correlation-aware analysis. Keep existing
   negative results. More evidence may show benefit, no benefit or harm; do not
   tune until significant or promise certainty in advance.
3. Complete the original interactive graph view: changed/impacted nodes,
   confirmed/heuristic/unresolved evidence, related tests and explanation paths.
4. Add Java editor language support, long-run progress and usable packaging.
5. Finish report/defence review alongside development. Additional languages stay
   deferred until the Java workflow is complete.

C++ prerequisites are installed: signed Microsoft Build Tools 17.14.42 and
Windows SDK 10.0.26100. The desktop application built and ran; this is resolved.
