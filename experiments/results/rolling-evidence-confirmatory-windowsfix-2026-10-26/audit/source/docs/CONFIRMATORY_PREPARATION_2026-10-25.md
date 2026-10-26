# Confirmatory data preparation — 2026-10-25

This implementation note was written before fresh-project model fitting in this
continuation. The earlier raw-data download was already in progress.
The experimental rules in `EVIDENCE_STUDY_PROTOCOL.md` remain unchanged: nine
projects outside study11, chronological rolling blocks, the same 15 LIVE_FEATURES,
fit/calibrate/audit split, model, seeds, risk target, gate, eligibility and verdicts.
No result-dependent project selection or parameter tuning is introduced.

## Fixed project set

CloudifySource@cloudify, DSpace@DSpace, SonarSource@sonarqube, apache@sling,
deeplearning4j@deeplearning4j, eclipse@jetty.project, facebook@buck, square@okhttp,
thinkaurelius@titan. These are all projects outside study11 returned by the
RTPTorrent v1.1 archive listing. The selective download is approximately
4,396,907,906 compressed bytes and at most 6,014,109,190 raw bytes, including the
unfiltered shared map (the actual map is filtered during extraction).

## Equivalent runtime inputs, cheaper extraction

The rolling study consumes 15 LIVE_FEATURES. The three dependency-graph features
are never used by that model/order/gate. `prepare_confirmatory --no-structural`
therefore stores 16 columns (including the still-unused co_failures column),
rather than computing and storing 19. Row identity, order, labels, actual test
durations and all 15 model inputs are unchanged. It uses the existing extractor's
`structural=False` path; it does not substitute heuristics for graph values.

Before fitting fresh projects, this equality was checked row by row against all
70,485 existing rows of HikariCP, LittleProxy, jade4j and wicket-bootstrap.
`experiments/datasets/confirmatory-live-2026-10-25/live-feature-equivalence.json`
records the checks and original CSV hashes. An offline fixture also checks the
full/nonstructural equality. This is a preparation optimization, not new evidence
about model performance, and is not a change to the statistical analysis.

`preparation.json` freezes the project list, structural option and extractor hash;
resume rejects a different configuration or unfingerprinted existing datasets.
Explicit inspected projects and output-name collisions are rejected before fetch.
The raw subset has its own CRC/SHA-256 manifest. No third-party build runs.

## Reproduce

From the checkout with Git and the project environment available:

```powershell
.venv\Scripts\python scripts/continue_confirmatory.py --wait
```

Keep OMP_NUM_THREADS, OPENBLAS_NUM_THREADS and MKL_NUM_THREADS at 1. Finish all nine
preparations before evaluation; list every ineligible project or import failure.
Copy this note and the preparation/equivalence metadata into the fresh result
folder before fitting so the final output manifest includes them. Do not change
the original protocol or overwrite exploratory results.


## Reuse the existing producer

An earlier `prepare_confirmatory.py` process was found already downloading the
same nine-project raw subset under `experiments/datasets/confirmatory/raw`.
The duplicate fetch from this continuation was stopped after its first two raw
CSV files, preserving both caches. No earlier producer process was stopped.

`continue_confirmatory.py --wait` is a one-time local command, not an AI service
or recurring scheduler. It waits for all 74 preflight entries and the shared
job map (extracted last), then checks every file SHA-256. It uses the original
raw cache directly through `prepare(..., raw_dir=...)`; no network fetch or
second copy of the raw repositories is made. Databases and 16-column CSVs go
into the separate nonstructural preparation folder. All nine must be prepared
before the fixed study can run. Earlier full/structural outputs are untouched.

The continuation records its phase in
`experiments/datasets/confirmatory-live-2026-10-25/continuation-status.json`.
An OS file lock prevents two workers writing those outputs. The lock is
released automatically if the process exits. Code, Python/library versions and
the equivalence proof are frozen at queue time and checked again before
fitting. Changes cause a failure status rather than silently changing the study.
The existing download must keep running; if it stops, restart that download
before expecting the waiting continuation to advance. No result is claimed
while status is waiting or preparing. This job does not provide notifications.

For a cold setup with no other downloader active, the preparation command can
reuse the same cache explicitly:

```powershell
.venv\Scripts\python scripts/prepare_confirmatory.py --no-structural --raw-dir experiments/datasets/confirmatory/raw --out experiments/datasets/confirmatory-live-2026-10-25
```

Do not run that fetch concurrently with the existing producer. After complete
preparation, the standalone study command remains:

```powershell
.venv\Scripts\python scripts/run_rolling_evidence.py experiments/datasets/confirmatory-live-2026-10-25/datasets --out experiments/results/rolling-evidence-confirmatory-2026-10-25
```
