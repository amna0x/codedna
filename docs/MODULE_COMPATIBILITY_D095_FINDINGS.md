# D095 findings: module-level compatibility leads

Screened all36preserved child reports from Oak3012. Nineteen complete-as-published
child reports exactly matched a single module's source-discovered default class
set, totaling485distinct module/class identities. Every child remains recorded;
no failure count or runtime influenced candidate selection.

Fresh public Jenkins metadata independently named all19modules in their URLs.
All corresponding pass/fail/skip totals matched the cached report. Metadata was
obtained later; it cannot prove historical report availability or unchanged
per-case content merely from matching totals. No model was fitted.

Seven of the19matching modules contain skipped cases. They are compatibility
leads, not complete training outcomes. Twelve have zero skipped cases on this
single build, covering269module/class identities. Historical test-universe and
completion validation is still required at each earlier commit. Preserve failures,
reruns, disappearing tests and all exclusions; never fill missing outcomes as pass.

The12zero-skipped candidates are oak-api, oak-auth-external,
oak-authorization-cug, oak-authorization-principalbased, oak-benchmarks,
oak-benchmarks-lucene, oak-http, oak-jackrabbit-api, oak-query-spi,
oak-run-elastic, oak-security-spi and oak-search. This list is identity/availability
selected and must not be narrowed by favorable failure or saving results.

Three offline tests passed in1.51seconds. They check that changing failure labels
cannot change compatibility selection and unmatched identities remain rejected.
The first script run used an incorrect Outcome field name and failed before any
result output. Corrected to complete_as_published; the corrected run finished.
No product code, safety gates or app validation result changed. The780app tests
remain a separate recorded validation; no long full-suite rerun was performed.

Next: freeze a module-scoped chronological protocol for all12zero-skipped
candidates, then check their available earlier reports and exact historical source
universes. The root archive still has only8available reports/7missing; module
compatibility cannot create the missing long history or bypass evidence floors.
Any measured module-only gain must not be presented as whole-project saving.
No selective permission, performance gain or complete research milestone is claimed.

Evidence: module-compatibility-d095-2026-10-30.json,
jenkins-child-metadata-d095-2026-10-30.json and
module-identity-check-d095-2026-10-30.json under experiments/results/.
