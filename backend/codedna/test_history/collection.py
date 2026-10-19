"""Fill the history store with test results.

* ``import_results`` — store existing ``results.json`` files (from
  ``codedna run-tests`` or converted from another source such as a dataset).
* ``collect_results`` — run the full test suite of every mined commit that has
  no results yet. **This executes the project's code** once per commit, so it
  needs ``allow_build=True`` (D-014) and can take hours on real projects.
"""

from __future__ import annotations

from pathlib import Path

from codedna.git_analysis.git import CodeDNAGitError
from codedna.plugins import load_plugins
from codedna.test_history.store import HistoryStore
from codedna.test_mapping.results import RESULTS_FILE, load_results


def import_results(store: HistoryStore, paths: list[str | Path], source: str = "import") -> dict:
    known = {commit.sha for commit in store.commits()}
    imported, warnings = 0, []
    for path in paths:
        path = Path(path)
        results_file = path / RESULTS_FILE if path.is_dir() else path
        run = load_results(results_file)
        if run.commit not in known:
            warnings.append(f"{results_file}: commit {run.commit[:12]} is not in the mined history")
        if not run.tests:
            warnings.append(f"{results_file}: no test results")
        imported += store.add_run(run, source)
    return {"rows": imported, "files": len(paths), "warnings": warnings}


def collect_results(repo_path: str | Path, store: HistoryStore, output_root: str | Path, *,
                    allow_build: bool, max_commits: int | None = None,
                    maven_command: list[str] | None = None, timeout: int = 1800) -> dict:
    """Run the suite for mined commits without results, oldest first."""
    if not allow_build:
        raise CodeDNAGitError("collecting results runs every commit's build; pass --allow-build")
    java = load_plugins().get("java")
    done = store.commits_with_results()
    pending = [c for c in store.commits() if c.sha not in done]
    if max_commits is not None:
        pending = pending[:max_commits]

    runs = []
    for commit in pending:
        output = Path(output_root) / f"{commit.seq:05d}-{commit.sha[:12]}"
        run, _ = java.run_tests(repo_path, commit.sha, output, allow_build=True,
                                maven_command=maven_command, timeout=timeout)
        store.add_run(run, "codedna-run")
        build_failed = any(code != 0 for code in run.exit_codes) and not run.tests
        runs.append({"commit": commit.sha, "seq": commit.seq, "tests": len(run.tests),
                     "failing": run.failing_tests, "build_failed": build_failed,
                     "duration_seconds": run.duration_seconds})
    return {"collected": len(runs), "remaining": len(store.commits()) - len(done) - len(runs),
            "runs": runs}
