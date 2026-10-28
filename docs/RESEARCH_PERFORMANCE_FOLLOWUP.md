# Research performance follow-up — protocol before execution

Status: planned, not run. This follow-up is separate from D076 and from D083's
already inspected local kernel profile. Freeze this file and the runner's
source hash before executing any new comparison. Do not edit old findings.

## Questions and boundaries

Primary engineering question: does unchanged-policy implementation reduce the
total cost of making a decision, including process startup and required analysis?
Primary research question for a later independently selected project: does the
fixed policy save total CI time while preserving its stated audit objective?
Do not conflate a faster model call with that second question.

Use the existing Java class-level Maven/JUnit domain. Keep B10/CRC thresholds,
features, seeds, chronological eligibility, mandatory test union and audit
schedule fixed. An ineligible project/change runs all tests. Do not reduce
required evidence, hide refusals or use a target outcome to choose its tests.
Model reuse must revalidate input identity and recompute each audit/threshold.

## Matched implementation comparison

Freeze the original implementation at `450e6ad` and the final D083 source hash.
Record hashes of all fixtures, history CSVs, project commits, plugin versions,
runtime/build tools and hardware. Use equal inputs, policy and process topology.
Report each topology separately: fresh CLI/API worker, and persistent MCP.
Never compare an original cold process with an optimized warmed process.

Prespecify small, medium and large eligible histories and unsupported, missing,
stale, foreign/future and all-mandatory cases. Synthetic eligibility fixtures
test engineering contracts; they are not independent failure-detection evidence.
Previously inspected real projects are explicitly exploratory/engineering data.
Do not choose cases based on which happens to yield the largest speedup.

For each case/topology, use one disclosed warm-up followed by five matched
pairs, alternating original/optimized order. Record cold first-call separately.
Report every pair plus medians/ranges, completed/failed/cancelled counts and
peak memory if actually measured. Run while idle and disclose concurrent work.
Keep datasets/repositories byte-identical; abort on changed fingerprints.

Measure wall time from the caller before process launch to received terminal
result. Record core stages and startup separately as diagnostics, never sum
nested inclusive stages. Include CSV read/hash, eligibility, feature extraction,
graphs, audit, conformal stopping, serialization and process management. Measure
project test execution separately only with explicit build consent.

Normalize only inherently variable timing fields and fixture directory prefixes
for equality checks. Require exact selected/skipped sets, mandatory tests,
probabilities, audit evidence, gate status, provenance and brake verdicts. Abort
the comparison on the first policy difference; investigate and retain failures.
Verify real worker cancellation, plugin activation/restarts and invalid-history
fallback remain correct. A fast failure is not a successful speed improvement.

## Net CI evaluation and research outcome

Choose an independently selected eligible Java target and chronological window
before observing optimized results. Reused HikariCP outcomes cannot become a
new confirmatory dataset. Freeze project/window, minimum failure evidence and
feasibility budget with the report reviewer before execution. If adequate
evidence is unavailable, publish that limitation instead of substituting a
convenient successful subset or fabricating independent labels.

Compare B0 full suite, structural-only, existing B10 and CRC under the same
environment. Execute full suites to obtain ground truth without feeding future
outcomes into prior selection. Include scheduled full audits and mandatory
tests. Preserve failing-commit and failing-test denominators separately. Report
refusal frequency, miss counts, recall, observed bounds and their assumptions.
Small failure counts limit conclusions even if all observed failures are found.

Primary cost: analysis wall time plus actually executed test wall time plus
amortized mandatory full audits and warm-up. Baseline B0 must include its own
measured launch/discovery overhead. Report observed elapsed time as well as
historical test-duration estimates; estimates are not measured CI savings.
Paired complete runs must isolate shared build/cache effects and declare how
JIT, Maven/Gradle caches, parallelism, failures, timeouts and retries are handled.
Do not infer net speedup by subtracting summed class durations from analysis.

Decision rule: unchanged policy with lower measured analysis cost supports an
engineering improvement. Net CI improvement requires lower matched total cost
and acceptable safety evidence on the preregistered target. A negative or mixed
result is retained. No parameter changes are made using this follow-up's results;
any redesign gets a new protocol and separate evaluation.

## Execution gate

Complete the D083 full Maven-inclusive suite and current frozen checks first.
Do not rerun any D076 study, download more datasets or launch lengthy target
builds merely because this protocol exists. A reproducible runner, committed
source/protocol identity and named target/window are required before a new
research execution is described as started. This document does not claim that
research performance or novelty has improved already.
