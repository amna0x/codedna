"""Rebuild four transfer-study history databases and verify feature CSV hashes.

Run fetch_rtptorrent_subset.py first. No analysed project is built or executed.
Only git-ignored raw/derived data and missing dataset.csv caches are written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

PROJECTS = {
    "hikaricp": "brettwooldridge@HikariCP",
    "littleproxy": "adamfisk@LittleProxy",
    "jade4j": "neuland@jade4j",
    "wicket-bootstrap": "l0rdn1kk0n@wicket-bootstrap",
}


def prepare(name: str, root: str) -> dict:
    from codedna.models.experiment import _reproducibility
    from codedna.git_analysis.git import resolve_repository, run_git
    from codedna.test_history.features import Dataset, build_dataset
    from codedna.test_history.rtptorrent import import_rtptorrent
    from codedna.test_history.store import HistoryStore

    root = Path(root)
    study = root / "experiments/results/study11-2026-10-21"
    target = study / name / "dataset.csv"
    database = root / f"experiments/datasets/derived/{name}.db"
    import_path = database.with_suffix(".import.json")
    started = time.monotonic()
    repository = root / "experiments/datasets/raw/rtp-torrent/repo" / PROJECTS[name]
    resolved = resolve_repository(repository)
    if resolved != repository.resolve() or run_git(resolved, "rev-parse", "--is-bare-repository").strip() != "true":
        raise RuntimeError(f"Downloaded bare repository is incomplete: {repository}")
    if (not database.exists() or not target.exists()) and shutil.disk_usage(root).free < 400 * 1024**2:
        raise RuntimeError("Less than 400 MiB free; data preparation stopped")
    with HistoryStore(database) as store:
        if not import_path.exists() or store.get_meta("rtptorrent_project") != PROJECTS[name]:
            print(f"{name}: importing recorded CI outcomes", flush=True)
            imported = import_rtptorrent(root / "experiments/datasets/raw", PROJECTS[name], store)
            import_path.write_text(json.dumps(imported.to_dict(), indent=2) + "\n", encoding="utf-8")
        if not target.exists():
            print(f"{name}: computing structural and historical features", flush=True)
            dataset = build_dataset(store, structural=True)
            temporary = target.with_suffix(".csv.part")
            dataset.to_csv(temporary)
            temporary.replace(target)
    dataset = Dataset.from_csv(target)
    actual = _reproducibility(dataset, 0)
    expected = json.loads((study / name / "experiment-seed0.json").read_text(encoding="utf-8"))["reproducibility"]
    result = {"project": name, "database": database.relative_to(root).as_posix(),
              "dataset": target.relative_to(root).as_posix(), "rows": len(dataset.rows),
              "commits": len(dataset.commits), "dataset_sha256": actual["dataset_sha256"],
              "expected_dataset_sha256": expected["dataset_sha256"],
              "matches_original_study": actual["dataset_sha256"] == expected["dataset_sha256"],
              "csv_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
              "seconds": round(time.monotonic() - started, 2), "packages": actual["packages"]}
    report = root / f"experiments/datasets/derived/{name}.features.json"
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: {len(dataset.rows)} rows; original hash match={result['matches_original_study']}", flush=True)
    if not result["matches_original_study"]:
        raise RuntimeError(f"{name}: rebuilt features differ from the original study; inspect {report}")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--projects", nargs="+", choices=list(PROJECTS), default=list(PROJECTS))
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args(argv)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(prepare, args.projects, [str(args.root.resolve())] * len(args.projects)))
    out = args.root / "experiments/datasets/derived/transfer-preparation.json"
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(results)} feature datasets against the original study", flush=True)


if __name__ == "__main__":
    main()
