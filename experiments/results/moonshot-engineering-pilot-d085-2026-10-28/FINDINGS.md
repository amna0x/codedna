# D085 Moonshot engineering pilot — findings

This is a fixed **synthetic engineering illustration**, not an independent
research accuracy study. Eight deliberately designed cases were repeated with
three seeds under two generation modes: 48 serial searches. Seeds do not create
independent projects or bugs. Some cases had already been inspected in tests;
boundary examples deliberately favor literal guidance. No statistical novelty,
universal superiority, regression recall or CI speedup is established here.

Implementation: source 4d359419ad68874c374a45d83732845327aeed41. Before this
comparison the full Maven-inclusive suite passed 714 tests with zero skips.
The manifest pins core/Java source, protocol, cases, dependencies and environment.
Each mode received the same eight-input, four-reduction, 30-second budget.
Mode order alternated; search, confirmation and reduction use fresh JVMs.
Every emitted reproducer was independently compiled/run with JDK only.

## All cases retained

The table reports statuses over three seeds per mode, not detection accuracy.
Costs are whole search-call medians, including startup, Git, compilation,
confirmation, reduction and export; independent reproduction costs are separate.
This laptop's foreground activity was not externally controlled; timings are
illustrative and are not matched CI savings.

| Case | Guided outcomes | Simple outcomes | Guided median s | Simple median s |
| --- | --- | --- | ---: | ---: |
| arithmetic_change | 3 difference | 3 difference | 11.069 | 9.226 |
| positive_boundary | 3 difference | 3 no_difference_observed | 12.737 | 10.825 |
| negative_boundary | 3 difference | 3 no_difference_observed | 14.190 | 13.895 |
| comment_only | 3 no_difference_observed | 3 no_difference_observed | 13.149 | 12.248 |
| intended_shipping_change | 3 difference | 3 no_difference_observed | 13.593 | 13.330 |
| exception | 3 inconclusive | 3 inconclusive | 8.233 | 7.242 |
| unstable_state | 3 inconclusive | 3 inconclusive | 9.758 | 8.619 |
| external_dependency | 3 unsupported | 3 unsupported | 3.916 | 4.181 |

## Reproduction and interpretation

There were 15 emitted witnesses across repeated case/mode/seed runs; 15/15 independently reproduced the recorded pair. These are repeated observations on the same synthetic cases, not that many
independent regressions. Source/harness hashes and per-search report hashes
were rechecked. Reproduction failures, if any, stay in results.json and must
not be hidden or called confirmed independent reproduction.

The intended shipping-threshold change is deliberately a difference, not an
automatically labelled regression. Its new business rule may be correct.
Exception and unstable-state cases cannot pass this normal-int-return pilot;
external dependencies remain unsupported. Comment-only no-witness outcomes do
not prove equivalence. All current required tests/risk gates remain separate.

## Engineering decision

Retain this as an explicitly opt-in, narrow debugging/agent capability when
the exported pair is useful to a developer. The implementation can produce
small inspectable inputs and JDK-only reproductions without paid AI. This is
an engineering benefit; it does not turn old mixed stopping results positive.
Do not generalize a boundary-oriented toy comparison to production bug finding.

Before widening the domain or making a stronger thesis claim, fix a separately
selected real-change evaluation protocol with explicit applicable expectations,
supported signatures, equal budgets, meaningful generation baselines and measured
reproduction/false-alarm costs. Existing differential testing already covers
the broad idea. Absence of a witness never authorizes skipping tests or saying
a change passed the CodeDNA brake. No old study was rerun, retuned or overwritten.

Raw evidence: manifest.json, results.json, summary.json and each search's
report.json. Confirmed exports include the full selected synthetic source,
standalone Java reproducer and reproduction.txt. Compiler output, temporary
paths and execution observations may appear in diagnostics; review before sharing.
