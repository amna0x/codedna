# Focused Moonshot pilot — Java behavioral witnesses

Status: design before implementation. This is the optional capability approved
in MOONSHOT_SCOPE.md. Finish D083 validation and the current packaged candidate
first. The existing research and application remain independently usable.

## First bounded contract

Accept one explicitly selected public static Java method with one `int`
argument and an `int` result, present on both immutable base/head snapshots.
Compile self-contained production sources without annotation processing or
repository build scripts. Unsupported dependencies, signatures, syntax or build
layouts get a visible unsupported result. Do not silently fall back to building
an arbitrary project. No new language or runtime library is required.

Execution requires the existing explicit project-code/build consent and a JDK.
An exported checkout protects the user's files; it is not a security sandbox.
Apply time, process-tree, input-count and output-size limits. Every executable
launch belongs to an owned operation. Cancellation/timeout must stop descendants
and cannot become a successful or no-difference result. Keep repository input
out of shell commands and do not import repository Python.

The plugin owns Java parsing, compilation, harness creation and execution.
The core owns shared evidence/status, budget and export contracts, and exposes
one optional plugin capability. Start with CLI and the existing brake's evidence
contract; add an IDE control only after the pilot demonstrates useful witnesses.
Read-only recommendation jobs must never gain an execution capability.

## Output and interpretation

Compare explicit observable return values on identical inputs. A stable unequal
pair is an observed behavioral difference. It is a regression only if an
explicit applicable expectation establishes which behavior is intended. Never
assume base is correct. Exceptions, compiler errors and unstable/repeated runs
are separate observations; unsupported or inconclusive work does not pass.

Confirm a witness with fresh repeated JVM runs and an identical input. Detect
observed nondeterminism and report it; repetitions cannot prove determinism in
general. No witness within a finite budget means only that no difference was
observed for those inputs. It does not establish equivalence or validate skip
risk. Witnesses may add required tests/evidence; their absence never removes
existing structural, risk or policy requirements.

Export input, base/head identities, source hashes, method identity, observed
values, tool versions, generation seed/budget, confirmation results and an
independently runnable Java reproducer. The reproducer demonstrates inequality,
not a guessed expected answer. Avoid timestamps/paths in semantic comparison.
Include only deliberately exported evidence/source needed for reproduction;
explain contents before a user shares the bundle. Do not overwrite an export.

## Generation and reduction

Fixed candidate universe: int32 extrema and neighbors, zero, small signed values,
then deterministic seeded values. Change-guided mode additionally proposes
integer literal boundaries and their representable neighbors from the changed
method. AST provenance labels these as syntax-derived suggestions, not semantic
guarantees. Overflow is explicit and all final values remain within int32.

Freeze equal *executed input* and wall-time budgets for change-guided and simple
generation. Deduplicate values, retain generation order and report exhausted
budgets. Compilation/confirmation/reduction costs are included separately.
Reduction only runs after a confirmed witness. Try bounded smaller-magnitude
integers while preserving the observed difference, then reconfirm. Say
"smallest among candidates tried"; never claim a global minimal program/input.
Export the original and reduced witness so reduction cannot erase evidence.

## Pilot evaluation before broad claims

Use a fixed, disclosed synthetic fixture table for engineering validation:
changed arithmetic, threshold off-by-one, a negative-input case, unchanged/comment
only, intended behavior change, throws, nondeterminism, timeout/descendant,
compile failure, missing JDK, unsupported signature/dependency and cancellation.
Do not label these independent real-world research accuracy. Preserve the
original checkout and verify every emitted reproducer independently.

Compare change-guided against simple generation at equal budgets over the same
preselected fixtures and seeds. Report witnesses found, observations that are
not regressions, time to first witness, confirmation/reduction/total cost and
reproduction rate. Retain cases where simple generation wins. Existing tests
and no-witness results remain in the table. Add previously unseen real changes
only through a separate preregistered selection/labeling protocol.

The go/no-go decision concerns measured usefulness versus implementation cost.
Differential testing already exists; this pilot alone establishes no new
scientific novelty. Potential contribution is useful integration of explicit
behavioral evidence with the conservative test brake, supported by a fair
comparison and honest limits. No automatic repair or concurrency laboratory.
