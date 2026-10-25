"""Record history-replay traces for a finished study (D-049).

For every project folder in the study that still has its ``dataset.csv``
(git-ignored; rebuilt by ``scripts/run_study.py``), rerun the experiment with
``trace=True`` and write ``<out>/<project>/replay-seed<N>.json``. Sweeps and
ablations are skipped: they do not change the policies.

Each trace is kept only if its ``policies`` and ``per_commit`` equal the
study's own ``experiment-seed<N>.json``; otherwise the project is reported as
a mismatch and nothing is written for it. Projects without a dataset are
listed as skipped (their compact reports still replay without SHAs).

Usage (from the repository root):
    python scripts/record_replays.py --study experiments/results/study11-2026-10-21 \\
        --out experiments/results/replay-2026-10-25 [--seed 0] [project ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def record(study: Path, out: Path, seed: int, projects: list[str] | None = None) -> dict:
    from codedna.models.experiment import run_experiment
    from codedna.test_history.features import Dataset

    result: dict[str, list[str]] = {"written": [], "skipped": [], "mismatch": [], "exists": []}
    names = projects or sorted(p.name for p in study.iterdir()
                               if (p / f"experiment-seed{seed}.json").is_file())
    for name in names:
        folder = study / name
        report_file, dataset_file = folder / f"experiment-seed{seed}.json", folder / "dataset.csv"
        target = out / name / f"replay-seed{seed}.json"
        if target.is_file():
            result["exists"].append(name)
            continue
        if not report_file.is_file() or not dataset_file.is_file():
            result["skipped"].append(name)
            continue
        study_report = json.loads(report_file.read_text(encoding="utf-8"))
        config = study_report["config"]
        report = run_experiment(Dataset.from_csv(dataset_file), model=config["model"],
                                calibration=config["calibration"], budget=config["budget"],
                                risk_target=config["risk_target"], seed=seed,
                                sweeps=False, ablations=False, trace=True)
        if (report["policies"] != study_report["policies"]
                or report["per_commit"] != study_report["per_commit"]):
            result["mismatch"].append(name)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        result["written"].append(name)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--study", required=True, help="Study folder (one subfolder per project).")
    parser.add_argument("--out", required=True, help="Folder for the replay traces.")
    parser.add_argument("--seed", type=int, default=0, help="Seed to replay (default: 0).")
    parser.add_argument("projects", nargs="*", help="Only these projects (default: all).")
    args = parser.parse_args(argv)
    result = record(Path(args.study), Path(args.out), args.seed, args.projects or None)
    print(json.dumps(result, indent=2))
    if result["skipped"]:
        print("skipped projects have no dataset.csv; rebuild it with scripts/run_study.py",
              file=sys.stderr)
    return 1 if result["mismatch"] else 0


if __name__ == "__main__":
    sys.exit(main())
