"""Prepare the confirmatory set of the rolling-origin study (D-042).

Run on a machine that can reach Zenodo. Every step can be resumed: rerunning
the same command skips the work already finished.

1. List the RTPTorrent v1.1 projects and keep those outside study11.
2. Fetch only their result CSVs and bare repositories (byte ranges).
3. Import each project into its own history database.
4. Build each feature dataset (``<name>/dataset.csv``; slow, can take hours).

No project code is executed. Finally it prints the evidence-study command,
which writes into a new output folder as the protocol requires.

Usage (from the repository root):
    python scripts/prepare_confirmatory.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def short_name(project: str) -> str:
    """``brettwooldridge@HikariCP`` → ``hikaricp`` (the naming used by study11)."""
    return project.split("@", 1)[1].lower()


def new_projects(available: list[str], exploratory: set[str]) -> list[str]:
    return [p for p in available if short_name(p) not in exploratory]


def prepare(out: Path, projects: list[str], fetch) -> list[Path]:
    from codedna.test_history.features import build_dataset
    from codedna.test_history.rtptorrent import import_rtptorrent
    from codedna.test_history.store import HistoryStore

    raw = out / "raw"
    fetch(raw, projects)
    folders = []
    for project in projects:
        name = short_name(project)
        db = out / "db" / f"{name}.db"
        if not db.is_file():
            db.parent.mkdir(parents=True, exist_ok=True)
            partial = db.with_suffix(".db.partial")
            partial.unlink(missing_ok=True)
            with HistoryStore(partial) as store:
                report = import_rtptorrent(raw, project, store)
            partial.replace(db)
            (out / "db" / f"{name}-import.json").write_text(
                json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
            print(f"{name}: imported", flush=True)
        folder = out / "datasets" / name
        csv_path = folder / "dataset.csv"
        if not csv_path.is_file():
            folder.mkdir(parents=True, exist_ok=True)
            started = time.time()
            with HistoryStore(db) as store:
                dataset = build_dataset(store, structural=True)
            partial = folder / "dataset.csv.partial"
            dataset.to_csv(partial)
            partial.replace(csv_path)
            print(f"{name}: features built in {time.time() - started:.0f}s", flush=True)
        folders.append(folder)
    return folders


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("experiments/datasets/confirmatory"))
    parser.add_argument("--projects", nargs="+",
                        help="Qualified names (owner@repo); default: every project outside study11")
    parser.add_argument("--list", action="store_true", help="Only list the projects that would be used")
    args = parser.parse_args(argv)
    os.environ.setdefault("OMP_NUM_THREADS", "1")  # gradient boosting is slow when oversubscribed

    fetcher = _script("fetch_rtptorrent_subset")
    exploratory = _script("run_rolling_evidence").STUDY11
    projects = args.projects or new_projects(fetcher.remote_projects(), exploratory)
    if not projects:
        print("no RTPTorrent projects outside study11 were found", file=sys.stderr)
        return 1
    print("confirmatory projects: " + ", ".join(projects), flush=True)
    if args.list:
        return 0
    prepare(args.out, projects, fetcher.fetch)
    results = f"experiments/results/rolling-evidence-confirmatory-{date.today().isoformat()}"
    print("\nNext, run the evidence study (one worker; can take a while):\n"
          f"  python scripts/run_rolling_evidence.py {(args.out / 'datasets').as_posix()} "
          f"--out {results}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
