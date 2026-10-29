# Experimental Moonshot: Java behavioral witnesses

This optional capability searches for an observable difference between two
versions. It supplements CodeDNA's existing test brake. The normal test-selection
and stopping methods remain the authority for required tests and skip risk.

The first pilot supports one deliberately selected **public static `int`
method with one `int` parameter**, in a public top-level class. Both versions
must compile from that single self-contained Java source file plus JDK classes.
Instance methods, other argument/result types, external dependencies and inferred
Maven/Gradle builds are unsupported. A JDK 17+ is required. This narrow domain is
an engineering pilot, not general Java behavioral equivalence.

## Use the source CLI

```powershell
python -m codedna witness --repo C:/my/project --base HEAD~1 --head HEAD --file src/main/java/example/Fee.java --symbol "example.Fee#fee(int)" --output-dir C:/my/new-witness --allow-build
```

The output folder must be new and outside the analysed repository. The JSON
report records immutable base/head identities, source fingerprints, selected
method, plugin/JDK versions, inputs, observations, budget and elapsed time.
Normal completion exits zero; this means a search completed, not that a change
passed verification. Unsupported/inconclusive searches exit one; cancellation
exits 130. Missing execution consent fails before repository inspection/export.

The product command defaults to **16 search inputs**,
eight reduction attempts, seed zero and a 30-second operation budget. Limits
are 64 search inputs, 16 reduction attempts and 120 seconds. Each tool invocation
also has a bounded step time/output. Compiler annotation processing is disabled.
Java source must be UTF-8; compilation and JVM startup file.encoding explicitly
use UTF-8, including the standalone reproducer. These controlled settings may
differ from a project runtime, so observations apply to this declared scenario.
The prespecified engineering comparison separately uses eight inputs/four
reduction attempts equally for both generation modes.

Choose `--generation guided` for integer literals and representable neighbors
from the selected method's syntax. `--generation simple` uses fixed small/extreme
integers and seeded values. Syntax guidance is a suggestion, not a guarantee
that a boundary matters. Set `--max-inputs`, `--reduce-budget`, `--seed` and
`--timeout` explicitly for reproducible comparisons.

## Use the existing agent brake

The witness tool is absent from default tool lists. Explicitly enable it only
for trusted project code:

```powershell
python -m codedna mcp --repo C:/my/project --allow-build --moonshot
```

`codedna_find_witness` requires `file`, `symbol` and `output_dir`; it also accepts
base/head, budgets, generation and optional profiling. Repository binding is the
same as consented checking. Profiling labels this `includes_project_execution`.
The normal `codedna_plan_tests`, `codedna_impact` and `codedna_check` contracts
stay available. A witness search never substitutes for `codedna_check`, removes
required tests, changes a stopping threshold or makes unsupported history valid.
Incomplete/unsupported/cancelled witness responses are tool errors.

## Interpret outcomes correctly

- `difference`: unequal normal int results matched repeated fresh JVM runs.
  Input reduction kept the difference and was reconfirmed. This is an observation;
  an applicable expectation is needed to classify a regression. Base is not an oracle.
- `no_difference_observed`: the finite search found no normal-return witness.
  This does not establish equivalence, test adequacy or a safe test-skipping rate.
- `unsupported`: the selected signature/source/JDK/dependencies do not fit this pilot.
- `inconclusive`: an exception, timeout, excess/incomplete output or unstable
  repeated result prevented acceptance. These cases do not pass.
- `cancelled`: Ctrl+C ended the owned operation. The worker and descendants are
  cleaned up; no confirmed result is accepted. If cleanup cannot be confirmed, the
  result is inconclusive and further witness execution and MCP project checking
  are blocked in that session; read-only planning remains available.

The controller uses a private consented worker protocol, distinct from read-only
analysis jobs. Project JVMs run under the existing owned process tree. Git objects
are read by the shared Git wrapper; only selected source is compiled in temporary
folders. Trusted code can have side effects; exported checkouts/containment are
not a security sandbox. Repeated observations detect some nondeterminism and do
not prove purity or general determinism.

## Export and reproduce

A confirmed difference exports the **entire selected source file** from each
version, the trusted probe, `ReproduceDifference.java`, README and hashes. Reports
may include compiler excerpts. Review files before sharing. Exports never replace
an existing directory. Reduction describes the smallest magnitude among candidates
actually tried; it does not claim a globally minimal input or reduced program.

From the export folder, with JDK 17+ and explicitly trusted source:

```text
javac -encoding UTF-8 -proc:none ReproduceDifference.java
java -Dfile.encoding=UTF-8 -cp . ReproduceDifference
```

No CodeDNA, Python, Maven or external library is needed for that reproduction.
It checks source/harness hashes and requires the recorded result pair exactly.
A changed source, different result, exception or timeout does not reproduce.
Temporary compiled files are left at the path the program prints.

## Evidence boundary

The initial 28 focused checks passed, including actual Java execution, independent
reproduction/tamper refusal, unstable observations and real JVM/descendant cleanup.
The later opt-in MCP integration passed 29 combined MCP/brake checks; four runner
guards pass; the later forced-cleanup/CLI/timeout/cancellation/runner review passed
nine checks, including the fifth duplicate-case guard. These are engineering checks. Corrected source 4d35941 subsequently passed the
full Maven-inclusive suite: 714 passed, zero skips/failures. The actual frozen
core passed 32 checks, including nine witness checks; all 1462 bundle hashes
matched. See ENGINEERING_VALIDATION_D085_2026-10-28.json and
FROZEN_CORE_VALIDATION_D085_2026-10-28.json. D085 installer packaging, embedded payload hashes and restricted-PATH unpacked
smoke subsequently passed; see RELEASE_VALIDATION_D085_2026-10-28.json. D085
full GUI/manual and clean-PC acceptance remain separate gates. Three new packaged
launch/plugin/restart checks pass.

The fixed comparison is in `experiments/moonshot-engineering-cases.json` and
`scripts/run_moonshot_pilot.py`, under MOONSHOT_PILOT_PROTOCOL.md. Eight synthetic
cases, three seeds and both generation modes give 48 serial searches. Some cases
were already inspected in unit tests; designed boundaries favor literal guidance.
This is illustrative engineering evidence, not an independently sampled research
dataset, new scientific novelty, universal superiority or improved stopping safety.
Existing D076 and nine-project findings are preserved. The D083 installer does
not include this newer experimental source.


Encoding review: the first 711-test full invocation was intentionally stopped
around 12 percent after confirming this laptop's JDK 17 defaults to Cp1252. It is
not counted as a pass. Two real regressions demonstrated misread UTF-8 literals
and acceptance of non-UTF8 source before the fix; both pass after explicit
source/compiler/runtime/reproducer encoding (13.08s). Full corrected validation
passed on corrected source (714 tests, zero skips). Source reports disclose
both encoding assumptions.


### Fixed engineering comparison completed

All 48 searches completed; all 15 exported witnesses independently reproduced.
Guided mode: 12 difference / 3 no-difference / 6 inconclusive / 3 unsupported.
Simple mode: 3 / 12 / 6 / 3. Median whole-call times were 11.234s and 10.057s,
respectively; guided mode was not faster overall. Repeated illustrative cases
are not independent bugs. Boundary construction favored guidance. Findings:
`experiments/results/moonshot-engineering-pilot-d085-2026-10-28/FINDINGS.md`.
Keep this optional narrow debugging aid; no new research/CI or skip-safety claim.


## D086 source contract (full release validation pending)

The source now accepts a public static int-return method with one or two
arguments, each int, boolean or String. Strings are bounded to 128 Unicode code
points; no null, array, object or long inputs are inferred. Pass up to three
explicit --support-file repository-relative Java paths for small helper classes.
Both revisions compile those exact sources with processors disabled; helpers
are exported and hash-checked by the standalone reproducer. Other dependencies
remain unsupported. Compilation/execution still requires explicit --allow-build.

--expectation-json accepts input, expected and requirement. Two arguments use a
two-element input array; expected is an int32 return value. This input counts
against both modes' search budgets. Conditional requirement assessment uses
confirmed observations, including the original witness when reduction changes
its input. A JUnit 5 draft asserts the supplied expectation, never the base
output; review and add it manually. No requirement is independently verified,
no witness authorizes skipping, and no-difference never establishes equivalence.

MCP codedna_check accepts shadow=true and attempts=1..3. Shadow executes the full
suite while preserving the recommendation and reporting observed failures outside
it. Every repeated failure still blocks; missing/skipped/build-error attempts
cannot become a passing verdict. Unstable or incomplete repeats are not training
history. Measured cost includes planning/execution/recording within the check,
not server startup or counterfactual selected-test savings. Default attempts=1.
