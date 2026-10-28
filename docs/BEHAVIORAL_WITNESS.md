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
  cleaned up; no confirmed result is accepted.

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
javac -proc:none ReproduceDifference.java
java -cp . ReproduceDifference
```

No CodeDNA, Python, Maven or external library is needed for that reproduction.
It checks source/harness hashes and requires the recorded result pair exactly.
A changed source, different result, exception or timeout does not reproduce.
Temporary compiled files are left at the path the program prints.

## Evidence boundary

The initial 28 focused checks passed, including actual Java execution, independent
reproduction/tamper refusal, unstable observations and real JVM/descendant cleanup.
The later opt-in MCP integration passed 29 combined MCP/brake checks; four runner
guards pass. These are engineering checks. Full source validation and actual new
frozen validation are still required before calling this source a release.

The fixed comparison is in `experiments/moonshot-engineering-cases.json` and
`scripts/run_moonshot_pilot.py`, under MOONSHOT_PILOT_PROTOCOL.md. Eight synthetic
cases, three seeds and both generation modes give 48 serial searches. Some cases
were already inspected in unit tests; designed boundaries favor literal guidance.
This is illustrative engineering evidence, not an independently sampled research
dataset, new scientific novelty, universal superiority or improved stopping safety.
Existing D076 and nine-project findings are preserved. The D083 installer does
not include this newer experimental source.
