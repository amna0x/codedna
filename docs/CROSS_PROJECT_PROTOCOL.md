# Cross-project transfer protocol

Status: fixed before transfer results were inspected, 2026-10-24 (D-039).

## Question and scope

Can a failure model trained and calibrated on one Java project rank tests and
give usable stopping-risk estimates on another project, without fitting to
that target's outcomes?

Pre-selected projects: HikariCP, LittleProxy, jade4j and wicket-bootstrap.
They have recorded failures and small enough archives for this laptop. Run
every ordered source-target pair (12 directions), plus four within-project
controls, with seeds 0, 1, 2, 3 and 4. The projects are not selected based on
which transferred models look best. This is a four-project extension, not a
claim about all eleven original projects or all Java repositories.

## Data recovery

Source: RTPTorrent v1.1, Zenodo record 4046180, Mattis et al., MSR 2020,
doi:10.1145/3379597.3387458, CC BY 4.0.

`fetch_rtptorrent_subset.py` reads the public archive by HTTP byte ranges.
It extracts each selected project's recorded outcomes and bare repository,
omits Git hooks, and filters the shared job/commit map to the selected jobs.
The selected entries' ZIP CRCs are verified at EOF; SHA-256 hashes and the
map transformation are recorded in a local manifest. This does not verify
the published MD5 of the complete 5 GB ZIP.

`prepare_transfer_features.py` rebuilds history databases with the existing
importer and extracts the same 19 features as the original study. Recovered
feature tables must reproduce the existing study's dataset hashes before
model tests run. Data remain git-ignored. No analysed project is built or
executed.

## Training and evaluation

1. Fix the target test period to its latest 20% of commits, matching the
   existing chronological study split.
2. For cross-project fitting, retain a chronological source prefix strictly
   older than the earliest Git committer date in the target test period.
   Stop at the first excluded source commit; do not skip it and then admit
   later feature rows whose history could include it.
3. Split that eligible source history chronologically: oldest 60% for
   training, next 20% for calibration, final 20% unused for fitting.
4. Fit balanced-weight histogram gradient boosting and source-only isotonic
   calibration. If the source lacks sufficient classes, record unavailable
   models/calibration; do not silently calibrate on the target.
5. Apply the frozen source model/calibrator to target test commits. Target
   outcomes score predictions and decisions only. Target features may use
   observations from earlier target commits, as in the original study.
6. Fit within-project controls afresh with the same library versions and
   normal 60/20/20 split. Check their fitting dates also precede their target
   test window. Do not compare new transfer fits with old-version saved fits.

Git dates are a timing proxy. CI completion times are unavailable. This is
not a test of a new repository with no historical test outcomes.

## Measures and decision rules

- Prediction: PR-AUC alongside the target failure rate and within-project
  control. A high score on one target does not establish general transfer.
- Ordering: raw ML APFDc versus recent-failure/shortest rules on the same
  target commits.
- Calibration: raw and source-calibrated Brier/ECE on the held-out target.
- Selection: actual time, failure recall, commit safety, estimated skip risk
  and observed miss rate for 50%-budget policies and B10 at a 5% risk target.
- Risk target: report whether the mean-over-seeds observed miss rate stays
  within 5% for each source-target direction. A pooled mean cannot establish
  that every target direction met the target.
- Fair cost: compare B10 with rules at matched actual test time. Pairwise
  hierarchical bootstrap resamples a seed, then target commits. Intervals
  crossing zero do not establish a safety gain. Matching is approximate.
- Report unavailable directions and all pre-selected directions. Do not
  choose the best source or tune thresholds using target test results.

For descriptive transfer averages, average sources within each target, then
weight targets equally. The twelve directions share four projects and are
not twelve independent projects. No pooled significance claim is planned.
Small numbers of failing commits, fixed time windows and correlated commits
limit the conclusions. Universal transfer requires evidence beyond this pilot.

## Commands

From the project root, with the development environment active:

```powershell
python scripts/fetch_rtptorrent_subset.py
python scripts/prepare_transfer_features.py --workers 2
python scripts/run_cross_project.py
```

Results go under `experiments/results/cross-project-2026-10-24/`, with every
pair/seed report, raw and calibrated variants, within-project controls,
summary tables and input/code/output fingerprints. Original study results
remain unchanged.
