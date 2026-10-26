"""One-time continuation: wait for the existing raw download, prepare and evaluate.

Uses no AI service, executes no third-party builds, and never starts another
network download. The source cache is read only. Run with --wait while the
existing prepare_confirmatory producer is still downloading its subset.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from importlib.metadata import version
import platform
import sys
import hashlib
import importlib.util
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ["CloudifySource@cloudify", "DSpace@DSpace", "SonarSource@sonarqube",
            "apache@sling", "deeplearning4j@deeplearning4j", "eclipse@jetty.project",
            "facebook@buck", "square@okhttp", "thinkaurelius@titan"]
EXPECTED_ENTRIES = 74
SHARED = "rtp-torrent/tr_all_built_commits.csv"


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_cache(raw):
    try:
        manifest = json.loads((raw / "rtptorrent-subset-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if set(manifest.get("projects", [])) != set(PROJECTS):
        raise ValueError("Source cache contains a different project set")
    entries = manifest.get("entries", {})
    if len(entries) > EXPECTED_ENTRIES:
        raise ValueError("Source cache has an unexpected entry count")
    return manifest


def ready(manifest):
    # The existing downloader extracts the shared map last. Requiring the
    # complete preflight entry count also prevents evaluating a partial set.
    return bool(manifest and len(manifest["entries"]) == EXPECTED_ENTRIES
                and SHARED in manifest["entries"])


def verify_cache(raw, manifest):
    if not ready(manifest):
        raise ValueError("Raw subset is incomplete")
    fetcher = script("fetch_rtptorrent_subset")
    if (manifest.get("url") != fetcher.URL
            or manifest.get("published_archive_md5") != fetcher.ARCHIVE_MD5):
        raise ValueError("Source cache is not the fixed RTPTorrent v1.1 archive")
    for name, metadata in manifest["entries"].items():
        path = fetcher.safe_target(raw, name)
        if not path.is_file() or digest(path) != metadata["sha256"]:
            raise ValueError(f"Unverified raw cache file: {name}")


def freeze(path, value):
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise ValueError(f"Provenance changed; use a new result folder: {path}")
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


@contextmanager
def output_lock(out):
    out.mkdir(parents=True, exist_ok=True)
    with (out / "continuation.lock").open("a+b") as handle:
        if os.fstat(handle.fileno()).st_size == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError("Another continuation owns this output folder") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if sys.platform == "win32":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def freeze_sources(out):
    runner = script("run_rolling_evidence")
    paths = list(dict.fromkeys([*runner.CODE, "scripts/continue_confirmatory.py",
        "scripts/prepare_confirmatory.py", "scripts/fetch_rtptorrent_subset.py",
        "backend/codedna/test_history/rtptorrent.py", "backend/codedna/test_history/store.py",
        "backend/codedna/test_history/mining.py", "backend/codedna/git_analysis/git.py",
        "backend/codedna/git_analysis/blobs.py", "backend/codedna/git_analysis/changes.py",
        "backend/codedna/test_mapping/results.py",
        "docs/CONFIRMATORY_PREPARATION_2026-10-25.md"]))
    frozen = {"code_sha256": {p: digest(ROOT / p) for p in paths},
              "python": platform.python_version(),
              "packages": {n: version(n) for n in ("scikit-learn", "numpy", "scipy")},
              "equivalence_sha256": digest(out / "live-feature-equivalence.json")}
    freeze(out / "continuation-code.json", frozen)


def continue_once(raw, out, results):
    freeze_sources(out)
    manifest = read_cache(raw)
    status(out, "verifying_raw_cache")
    verify_cache(raw, manifest)
    status(out, "preparing_databases_and_features")
    preparer = script("prepare_confirmatory")
    # Verification above replaces the fetch callback: no duplicate HTTP work.
    folders = preparer.prepare(out, PROJECTS, lambda *_: None,
                               structural=False, raw_dir=raw)
    expected = {preparer.short_name(p) for p in PROJECTS}
    inputs = {p.name: p / "dataset.csv" for p in folders}
    if set(inputs) != expected or any(not p.is_file() for p in inputs.values()):
        raise ValueError("Every fixed project must be prepared before evaluation")
    results.mkdir(parents=True, exist_ok=True)
    freeze_sources(out)  # preparation may take time: recheck before fitting
    frozen = json.loads((out / "continuation-code.json").read_text(encoding="utf-8"))
    freeze(results / "preparation-provenance.json", {
        "projects": PROJECTS, "frozen_sources": frozen,
        "raw_manifest_sha256": digest(raw / "rtptorrent-subset-manifest.json"),
        "configuration": json.loads((out / "preparation.json").read_text(encoding="utf-8")),
        "live_feature_equivalence": json.loads(
            (out / "live-feature-equivalence.json").read_text(encoding="utf-8"))})
    note = ROOT / "docs/CONFIRMATORY_PREPARATION_2026-10-25.md"
    target = results / note.name
    if target.exists() and digest(target) != digest(note):
        raise ValueError("Preparation note changed; use a new result folder")
    target.write_bytes(note.read_bytes())
    status(out, "evaluating_fixed_study", projects=len(inputs), results=str(results))
    runner = script("run_rolling_evidence")
    return runner.run(ROOT, inputs, results)


def status(out, phase, **fields):
    out.mkdir(parents=True, exist_ok=True)
    payload = {"phase": phase, "pid": os.getpid(),
               "updated_utc": datetime.now(timezone.utc).isoformat(), **fields}
    path = out / "continuation-status.json"
    temporary = path.with_suffix(".json.partial")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-raw", type=Path,
                        default=ROOT / "experiments/datasets/confirmatory/raw")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "experiments/datasets/confirmatory-live-2026-10-25")
    parser.add_argument("--results", type=Path,
                        default=ROOT / "experiments/results/rolling-evidence-confirmatory-2026-10-25")
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args(argv)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = "1"
    last_count = None
    with output_lock(args.out):
        try:
            args.out.mkdir(parents=True, exist_ok=True)
            freeze_sources(args.out)
            while True:
                manifest = read_cache(args.source_raw)
                if ready(manifest):
                    break
                count = len(manifest["entries"]) if manifest else 0
                status(args.out, "waiting_for_existing_download", verified_files=count,
                       expected_files=EXPECTED_ENTRIES, source_raw=str(args.source_raw))
                if count != last_count:
                    print(f"Existing raw download: {count}/{EXPECTED_ENTRIES} verified files", flush=True)
                    last_count = count
                if not args.wait:
                    print("Raw cache is incomplete; use --wait to continue after the existing download.")
                    return 2
                time.sleep(30)
            status(args.out, "verifying_preparing_evaluating", source_raw=str(args.source_raw))
            summary = continue_once(args.source_raw, args.out, args.results)
            status(args.out, "complete", results=str(args.results),
                   verdict=summary["sets"]["confirmatory"]["verdict"])
            print(f"Completed: {args.results / 'summary.md'}", flush=True)
            return 0
        except Exception as exc:
            status(args.out, "failed", error=f"{type(exc).__name__}: {exc}")
            raise


if __name__ == "__main__":
    raise SystemExit(main())
