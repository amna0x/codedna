# Cross-project transfer findings — 2026-10-24

The tested gradient-boosting model and source-only calibrator do **not transfer
reliably enough to support a general 5% skip-risk claim**. Some pairs are useful,
but others miss failures or save almost no time. This result limits the scope of
the project claim; it does not invalidate the original within-project study.

## What ran

Four projects were selected before results: HikariCP, LittleProxy, jade4j and
wicket-bootstrap. All 12 transfer directions and four newly fitted within-project
controls ran with seeds 0–4: 80 reports. Every model trains on source history;
every cross-project calibrator uses source validation labels only. The runner
restricts source history to a prefix older than target testing using Git dates.
The target's latest 20% is held out, while earlier target history remains usable.

All 80 raw evaluations completed. Calibrated results are available for 9 of 12
transfer directions (45 runs) and all four controls (20 runs). In jade4j's three
transfer directions, the eligible source calibration window lacks both classes.
Those 15 raw runs remain reported; no target labels were used to repair calibration.

## Main evidence

- **Seven of nine** available calibrated directions meet the observed 5% miss
  target. Two fail; three other directions have no usable calibration. This is
  not a 7/12 success rate with the missing cases silently excluded.
- **HikariCP to LittleProxy:** 29.26% of test time, zero failure recall, estimated
  miss risk 4.40%, observed miss 9.43%. All five failing target commits are missed.
- **LittleProxy to wicket-bootstrap:** 70.82% time and 98.30% failure recall, but
  observed miss 16.46% against estimated 3.48%. Catching most failing classes still
  leaves at least one skipped failure on many commits; commit safety is 68.97%.
- **Wicket-bootstrap to the other projects:** 97.84–99.96% of full test time.
  The miss target holds, but these transfers save almost no execution time.
  Source calibration increases target ECE from 0.0624 to 0.3270 on HikariCP,
  0.0179 to 0.3740 on LittleProxy and 0.0379 to 0.2543 on jade4j.
- Transferred raw-model ordering beats the rules in only **3 of 12 directions**
  by mean APFDc. Source calibration worsens target ECE in **6 of 9** available
  directions compared with raw probabilities. Source calibration is not reliable
  evidence of target calibration.
- There are positive pairs: **HikariCP to wicket-bootstrap** uses 72.51% time,
  has 99.96% failure recall, 98.85% commit safety and 0.61% observed miss. Its safety
  difference versus rules at matched time is +0.1034 [0.0449, 0.1711]. LittleProxy
  to wicket-bootstrap also beats matched-time rules in safety (+0.3218
  [0.1852, 0.4598]), despite failing its risk target. These are pairwise intervals,
  with no multiple-comparison correction, not evidence of universal improvement.

The descriptive, target-weighted mean over the nine available calibrated pairs
is 73.12% time, 78.57% failure recall, 74.44% commit safety, estimated risk 2.05%
and observed miss 3.79%. That mean hides failing directions and excludes unavailable
calibration; it must not be used to claim all targets meet 5%.

## Fresh within-project controls

Means over seeds; time is a fraction of the full suite, and safety is evaluated
on commits with recorded failures.

| Project | Time | Recall | Commit safety | Observed miss |
|---|---|---|---|---|
| HikariCP | 0.1333 | 0.7273 | 0.5000 | 0.0350 |
| LittleProxy | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| jade4j | 0.2264 | 0.5000 | 0.5000 | 0.0159 |
| wicket-bootstrap | 0.7513 | 0.9971 | 0.9862 | 0.0073 |

All four controls meet the unconditional observed 5% miss target, but that alone
does not establish useful selection. LittleProxy runs everything. jade4j has only
two failing commits among 63 target commits: even running nothing would yield
3.17% unconditional miss. The risk target is not a promise to catch 95% of failures.
These controls use the current package versions and do not replace old study files.

## Meaning for CodeDNA

Keep the claim centred on target-project validation and calibrated stopping on
simple rules. Do not present one source-trained model/calibrator as a generally
reliable model for new projects. Before enabling a transferred stopping rule,
evaluate it on earlier held-out target data; without adequate evidence, retain
rules/full-suite behaviour and report that risk is unvalidated. Target calibration
or pooled training can be separate, pre-specified future studies, not fixes tuned
on this target test set. No runtime deployment or IDE behaviour changed here.

## Data and reproducibility

Four history databases and feature CSVs were rebuilt from the selectively
downloaded RTPTorrent v1.1 records and bare repositories. All four dataset digests
match the original study: 20,206 / 4,575 / 10,913 / 34,791 rows. The other seven
projects' raw/derived data are still absent. All 112 original figure-input report
hashes remain unchanged.

See [summary.md](summary.md), [summary.json](summary.json),
[data-recovery.json](data-recovery.json), [manifest.json](manifest.json), and
[the fixed protocol](../../../docs/CROSS_PROJECT_PROTOCOL.md). The manifest
records input, code and output hashes and package versions. A separate audit
verified all 80 reports, source/test SHA separation, fitting before target Git
dates, and the recorded input/code/output hashes.

## Software validation

The full local command `.venv/Scripts/python -m pytest --run-maven -q`
passed **220 tests, zero skipped**, in 363.77 seconds on Windows. This includes
real Maven/JUnit/JaCoCo integration. One existing Starlette/httpx deprecation
warning remains. Portable Temurin JDK 17.0.20+8 and Maven 3.10.0 were downloaded
and checksum-verified; no system-wide PATH change was needed. See
[validation.json](validation.json) for runtime and verification provenance.

## Limits

Four historical Java projects and fixed time windows, with only 20 / 5 / 2 / 87
failing target commits. Seeds do not create independent projects or time periods.
Directions share projects; commit bootstrap ignores serial correlation. Git dates
are not CI completion dates. Prior target outcomes are available as features, so
this is not a no-history startup test. Conclusions apply to this model/protocol;
other models and target adaptation were not tested.
