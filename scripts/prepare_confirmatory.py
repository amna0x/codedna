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
import hashlib
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


def prepare(out: Path, projects: list[str], fetch, *, structural: bool = True,
            raw_dir: Path | None = None) -> list[Path]:
    from codedna.test_history.features import build_dataset
    from codedna.test_history.rtptorrent import import_rtptorrent
    from codedna.test_history.store import HistoryStore

    out.mkdir(parents=True, exist_ok=True)
    raw = raw_dir.resolve() if raw_dir is not None else (out / "raw").resolve()
    config = {"schema": 1, "projects": projects, "structural": structural,
              "raw_dir": str(raw),
              "extractor_sha256": hashlib.sha256(
                  (ROOT / "backend/codedna/test_history/features.py").read_bytes()).hexdigest()}
    config_path = out / "preparation.json"
    if config_path.exists():
        if json.loads(config_path.read_text(encoding="utf-8")) != config:
            raise ValueError("Preparation configuration changed; use a new output directory")
    else:
        if any(folder.exists() and any(folder.iterdir())
               for folder in (out / "db", out / "datasets")):
            raise ValueError("Existing preparation has no configuration; use a new output directory")
        partial_config = config_path.with_suffix(".json.partial")
        partial_config.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        partial_config.replace(config_path)
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
                dataset = build_dataset(store, structural=structural)
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
    parser.add_argument("--raw-dir", type=Path,
                        help="Reuse a verified raw subset in another preparation folder.")
    parser.add_argument("--no-structural", action="store_true",
                        help="Omit graph columns unused by the rolling study's 15 live features.")
    args = parser.parse_args(argv)
    os.environ.setdefault("OMP_NUM_THREADS", "1")  # gradient boosting is slow when oversubscribed
    if importlib.util.find_spec("codedna") is None or importlib.util.find_spec("sklearn") is None:
        print("codedna or scikit-learn is not installed for this Python "
              f"({sys.executable}). Use the project venv, e.g. "
              ".venv\\Scripts\\python scripts\\prepare_confirmatory.py, "
              'or install it with: pip install -e ".[ml]"', file=sys.stderr)
        return 1

    fetcher = _script("fetch_rtptorrent_subset")
    exploratory = _script("run_rolling_evidence").STUDY11
    projects = args.projects or new_projects(fetcher.remote_projects(), exploratory)
    if not projects:
        print("no RTPTorrent projects outside study11 were found", file=sys.stderr)
        return 1
    try:
        names = [short_name(p) for p in projects]
    except IndexError:
        print("Expected qualified project names such as apache@sling", file=sys.stderr)
        return 1
    inspected = sorted(set(names) & exploratory)
    if inspected:
        print("Inspected projects cannot be confirmatory: " + ", ".join(inspected), file=sys.stderr)
        return 1
    if any(not name for name in names) or len(set(names)) != len(names):
        print("Project output names must be nonempty and unique", file=sys.stderr)
        return 1
    print("confirmatory projects: " + ", ".join(projects), flush=True)
    if args.list:
        return 0
    try:
        prepare(args.out, projects, fetcher.fetch, structural=not args.no_structural,
                raw_dir=args.raw_dir)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    results = f"experiments/results/rolling-evidence-confirmatory-{date.today().isoformat()}"
    print("\nNext, run the evidence study (one worker; can take a while):\n"
          f"  python scripts/run_rolling_evidence.py {(args.out / 'datasets').as_posix()} "
          f"--out {results}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
