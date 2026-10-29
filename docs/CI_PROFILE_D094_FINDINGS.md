# D094: explain the CI execution-profile mismatch

Read-only source inspection at Oak commit
52f2591e8b6b7f75218ec153e52379b6046c49e8 explains why default Java source discovery
cannot be treated as this CI job's execution universe. No analysed code was built
or executed. No application, model or safety-gate changes were made.

Confirmed source facts:

- Jenkinsfile line29 selects `-PintegrationTesting`; line71 collects both Surefire
  and Failsafe reports. This is source configuration, not proof that the historical
  Jenkins build used an identical job definition/environment.
- Of420report-only classes,134have exact FQCN Java paths in this revision;
  97ofthose names end in IT. The other286have no exact FQCN source path. That
  absence does not prove their external/generated origin.
- oak-jcr/pom.xml line415 declares jackrabbit-jcr-tests as a test dependency.
  External suites therefore need explicit dependency/source provenance rather
  than being silently discarded or assigned guessed structural scores.
- Of29source-only classes,28belong to oak-exercise, whose pom.xml line44 explicitly
  sets Surefire skip=true. Source discovery alone cannot infer their CI execution.
- The remaining source-only RevisionGCTest is parameterized. Its absence remains
  unresolved; being parameterized is not sufficient evidence of why it is absent.

The first investigation output is preserved; v2 adds pinned Jenkinsfile and parent
POM excerpts with line numbers and decoded-text hashes. Both outputs retain every
unmatched identity. The research script refuses overwriting an existing output.

This is progress on dataset compatibility, not a new brake-performance result.
A correct solution must capture effective execution profile, external suite
identities, skips and parameterization for each historical commit. Exact coverage
must be checked before use. Until then, no selective replay is authorized on this
job. The live brake continues requiring the full suite when evidence is missing.
The six-hour archiver preserves future observations but cannot reconstruct missing
historical reports or guarantee sufficient first-parent history.

Next: validate a module-scoped complete report/source pair, preserving all other
modules as required full-suite work. Any module-scoped study must be declared as
such before inspecting outcomes; its savings cannot be reported as whole-project
savings. Do not fit a model from the current mismatched union or retune old studies.

Evidence: scripts/investigate_d094_ci_profile.py and the D094 JSON files under
experiments/results/. Existing application validation remains780tests; D093's
10offline research tests are separate. No full-suite rerun was necessary for this
read-only investigation script and documentation.
