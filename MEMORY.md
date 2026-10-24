# MEMORY.md: handoff notes for the next agent

Read this first, then AGENTS.md (rules), docs/ROADMAP.md (status) and
docs/DECISIONS.md (D-001 to D-037, why things are the way they are).
Last updated: 2026-10-24 (after the B10 class-weight run).

## What the project is

CodeDNA is a university Final Year Project (software engineering only, no
security scope). It analyses Java code changes, estimates their impact,
selects and orders regression tests, and estimates the risk of skipping the
rest. Research track (Python core + experiments) has priority over the
product track (Theia IDE in `ide/`, later a website and plugin catalogue).
Target: finish by the end of November 2026.

## How the owner works

- Commit and push **only when the user asks**. After every push, check CI
  (`gh run list` / `gh run watch <id>`) and report the job results.
- Git identity is repo-local: mohibk0004-del. Remote: github.com/mohibk0004-del/codedna (private).
  Commit messages end with a `Co-Authored-By:` line for the AI model used.
- Never fabricate numbers. Every result must come from files under
  `experiments/results/`. Report negative results honestly.
- Run `python -m pytest` before claiming completion (currently 198 passed,
  1 skipped locally; the skipped Maven test runs in CI).
- Update FINDINGS / DECISIONS / ROADMAP / report draft when results change.
- `docs/PROGRESS_REPORT.md` and `.pdf` are a plain-language report the user
  forwards. They are **local only** (listed in `.git/info/exclude`); keep
  them in sync with findings but never commit them.

## Environment (Windows 11)

- Python 3.12 venv at `.venv` (`.venv/Scripts/python`). Install:
  `pip install -e ".[ml,api,dev]"`.
- Set `PYTHONIOENCODING=utf-8` when scripts print "−" or "Δ".
- In Git Bash, heredocs containing apostrophes sometimes fail ("unexpected
  EOF"); write a Python script to a file and run it instead.
- tree-sitter is pinned `>=0.25,<0.26`: 0.26.0 crashes (D-033).
- IDE builds need `env -u NODE_USE_SYSTEM_CA` (certificate issue).
- Markdown to PDF: render HTML with the `markdown` package, then
  `chrome.exe --headless=new --no-pdf-header-footer --print-to-pdf=...`.

## Data

- RTPTorrent v1.1 in `experiments/datasets/raw/` (git-ignored, 5 GB).
- Per-project history DBs in `experiments/datasets/derived/*.db`
  (git-ignored), built with `codedna history import-rtptorrent`.
- Study folder: `experiments/results/study11-2026-10-21/` holds per-project
  `dataset.csv` (git-ignored, slow to rebuild: up to 2 h per project),
  `evaluate-seed*.json`, `experiment-seed*.json`, `class-weight-seed*.json`,
  `summary.md/json`, `class-weight-summary.md/json`, `FINDINGS.md`.
- Projects: graylog2-server, jooq, jcabi-github, optiq, achilles, hikaricp,
  littleproxy, jade4j, jsprit, wicket-bootstrap, dynjs. graylog2-server and
  jOOQ have no failing test commits (CI recording gaps), so recall/safety
  pool over 9 projects.

## Key commands

```bash
python -m pytest
python scripts/run_study.py --out experiments/results/study11-2026-10-21 --seeds 0 1 2 3 4 --workers 6 name=experiments/datasets/derived/name.db ...
python scripts/class_weight_check.py --out experiments/results/study11-2026-10-21 --seeds 0 1 2 3 4 --workers 6 graylog2-server jooq ...
```

`run_study.py` reuses `dataset.csv` and skips report files that exist;
delete `experiment-seed*.json` to rerun experiments. Rerunning reproduces
earlier numbers exactly (fixed seeds, chronological split).

## Results so far (study11, 11 projects x 5 seeds)

- RQ1: features predict failures above chance (pooled PR-AUC 0.138), mostly
  via history; ML ordering does **not** beat simple rules (APFDc: recent
  failures 0.76, shortest 0.74, random 0.65, LR 0.64, GB 0.58).
- RQ2: B8 needs ~60 % of test time for 90 % recall, ~82 % for 0.91 safety.
- RQ3: calibrating the class-weighted model cuts ECE 0.118 to 0.021, but an
  unweighted model is already at 0.030 (D-037), so the ECE drop mostly
  undoes class weighting. However, B10 with the unweighted *raw* model
  stops too early (target held on 6 of 9 projects); calibrated, 8 of 9.
  Calibration matters for decisions, not for the ECE number.
- RQ4: fallback (B9/B9r/B9n) gives no reliable gain at the same test time.
  Hybrid B10 (rules order + calibrated stopping at 5 % risk, D-036) is never
  less safe than rules at the same time and meets its target on 10 of 11
  projects; pooled gain +0.075 [-0.001, 0.202], not significant.
- RQ5: dependency graph helps on jsprit/HikariCP/optiq, blind on
  jcabi-github/wicket-bootstrap.
- Thesis claim: calibrated, checked risk estimates used as a stopping rule
  on a simple ordering, evaluated at equal test time. Not "ML beats rules";
  calibration's value is in the decision, not in the ECE drop.

## In progress / next

1. Done 2026-10-24: B10 needs calibration (see RQ3 above).
   `graphify-out/` (a local knowledge graph of the repo, made with the
   graphify skill) is intentionally neither committed nor git-ignored.
2. Freeze results, make figures, finish `docs/REPORT_DRAFT.md` (evaluation
   chapter RQ1 to RQ5); user to check the claim with the supervisor.
3. Rest of the report.
4. Minimal IDE demo: B10 risk number in "Tests to run", run selected tests,
   Windows installer; then a simple static website page.
5. Optional: Defects4J check, manual graph-precision check.
