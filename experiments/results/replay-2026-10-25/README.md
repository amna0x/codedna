# History replay traces (2026-10-25)

Seed-0 experiment reports with a per-commit `replay` trace (D-049) for the
four study11 projects whose feature datasets were available:
hikaricp, jade4j, littleproxy and wicket-bootstrap.

Made with:

```bash
python scripts/record_replays.py --study experiments/results/study11-2026-10-21 \
    --out experiments/results/replay-2026-10-25
```

The script reruns `run_experiment(..., trace=True)` on each project's
`dataset.csv` (git-ignored, rebuilt by `scripts/run_study.py`) with sweeps and
ablations skipped, and keeps a trace only if its `policies` and `per_commit`
equal `study11-2026-10-21/<project>/experiment-seed0.json`. All four matched
exactly (same dataset SHA-256; scikit-learn 1.9.1, numpy 2.5.4).
`backend/tests/test_replay.py` checks this again.

The other seven projects (achilles, dynjs, graylog2-server, jcabi-github,
jooq, jsprit, optiq) had no dataset here and replay from their compact study
reports, which have no commit SHAs, test names, seconds or per-commit
estimated risk. Rerun the command after rebuilding their datasets to add them.

Open them in the IDE with **History replay** (`Ctrl+Shift+Alt+R`), or:

```bash
codedna replay experiments/results/replay-2026-10-25/hikaricp/replay-seed0.json
codedna replay --overview experiments/results/study11-2026-10-21 experiments/results/replay-2026-10-25
```
