"""Agent brake study on public SWE-bench Multilingual Java patches (D-062).

Protocol: docs/AGENT_BRAKE_STUDY_PROTOCOL.md (fixed before any result).

Two steps:

    python scripts/swebench_brake_study.py fetch --data experiments/datasets/swebench-multilingual
    python scripts/swebench_brake_study.py run --data experiments/datasets/swebench-multilingual \
        --work WORKDIR --out experiments/results/agent-brake-swebench-DATE

``fetch`` downloads the public agent patches and harness reports (no
credentials) and records each file's SHA-256. ``run`` fetches each base
commit of the six Java projects (depth 1), builds the repository states the
harness tested, and asks CodeDNA which test classes each change must run.
No build or project script is run; ``eval.sh`` is read as text only.
"""

from __future__ import annotations

import argparse
import csv
import functools
import gzip
import hashlib
import json
import os
import re
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.request
from math import sqrt
from pathlib import Path

from codedna.git_analysis.git import GitCommandError, run_git

EXPERIMENTS = "https://github.com/SWE-bench/experiments.git"
SPLIT = "evaluation/multilingual"
JAVA_PREFIXES = ("google__gson-", "apache__druid-", "apache__lucene-", "projectlombok__lombok-",
                 "ReactiveX__RxJava-", "javaparser__javaparser-")
REPO_URL = "https://github.com/{owner}/{name}.git"
IDENTITY = ("-c", "user.name=codedna-study", "-c", "user.email=codedna-study@invalid",
            "-c", "commit.gpgsign=false")
Z = 1.959963984540054
FIELDS = ["submission", "instance", "repository", "status", "resolved", "failing",
          "failing_classes", "unmapped_tests", "f2p_classes", "total_tests", "a2_selected",
          "a2_ratio", "a2_retest_all", "a1_caught", "a2_caught", "a2_reach", "note"]


# --- fetch ------------------------------------------------------------------------


def fetch(data: Path) -> None:
    data = data.resolve()
    data.mkdir(parents=True, exist_ok=True)
    clone = data / "experiments"
    if not clone.exists():
        _git(data, "clone", "--quiet", "--filter=blob:none", "--no-checkout", "--depth", "1",
             EXPERIMENTS, str(clone))
    if Path(_git(clone, "rev-parse", "--show-toplevel").strip()).resolve() != clone:
        raise SystemExit(f"{clone} is not a clone of {EXPERIMENTS}")
    commit = _git(clone, "rev-parse", "HEAD").strip()
    submissions = _git(clone, "ls-tree", "-d", "--name-only", "HEAD", f"{SPLIT}/").split()
    manifest = {"experiments_commit": commit, "fetched": time.strftime("%Y-%m-%d"),
                "submissions": {}, "files": {}}
    context = ssl.create_default_context()
    for folder in submissions:
        name = folder.rsplit("/", 1)[-1]
        meta = _git(clone, "show", f"HEAD:{folder}/metadata.yaml")
        details = json.loads(_git(clone, "show", f"HEAD:{folder}/per_instance_details.json"))
        logs = log_base_url(meta)
        instances = sorted(i for i in details if i.startswith(JAVA_PREFIXES))
        manifest["submissions"][name] = {"logs": logs, "instances": instances}
        for instance in instances:
            for file in ("patch.diff", "report.json"):
                _download(f"{logs}/{instance}/{file}", data / "submissions" / name / instance / file,
                          manifest, data, context)
    for instance in sorted({i for s in manifest["submissions"].values() for i in s["instances"]}):
        target = data / "instances" / instance
        for name, sub in manifest["submissions"].items():
            if instance not in sub["instances"] or "amazonaws" not in sub["logs"]:
                continue
            eval_ok = _download(f"{sub['logs']}/{instance}/eval.sh", target / "eval.sh",
                                manifest, data, context)
            head_ok = _download(f"{sub['logs']}/{instance}/test_output.txt",
                                target / "test_output_head.txt", manifest, data, context,
                                limit=65536)
            if eval_ok and head_ok:
                break
        # The S3 harness logs do not show the base commit when the test patch only adds
        # files; the newer harness behind the GitHub-hosted logs prints `git diff <base>`.
        known = target / "test_output_head.txt"
        script = _read_exact(target / "eval.sh") if (target / "eval.sh").exists() else ""
        try:
            base_commit(script, known.read_text(encoding="utf-8", errors="replace")
                        if known.exists() else "")
        except ValueError:
            for name, sub in manifest["submissions"].items():
                if instance in sub["instances"] and "githubusercontent" in sub["logs"] and _download(
                        f"{sub['logs']}/{instance}/test_output.txt.gz",
                        target / "test_output_alt.txt.gz", manifest, data, context):
                    break
    (data / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"{len(manifest['files'])} files recorded in {data / 'manifest.json'}")


def log_base_url(metadata: str) -> str:
    """HTTPS base URL of a submission's public logs, from its metadata.yaml."""
    match = re.search(r"^\s*logs:\s*(\S+)\s*$", metadata, re.MULTILINE)
    if not match:
        raise ValueError("metadata.yaml names no logs location")
    url = match.group(1)
    if url.startswith("s3://"):
        bucket, _, prefix = url[5:].partition("/")
        return f"https://{bucket}.s3.amazonaws.com/{prefix.rstrip('/')}"
    github = re.fullmatch(r"https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+)", url)
    if github:
        owner, name, ref, path = github.groups()
        return f"https://raw.githubusercontent.com/{owner}/{name}/{ref}/{path.rstrip('/')}"
    raise ValueError(f"unsupported logs location: {url}")


def _download(url: str, target: Path, manifest: dict, data: Path, context, limit=None) -> bool:
    key = target.relative_to(data).as_posix()
    if target.exists():
        manifest["files"][key] = {"url": url, "sha256": _sha256(target.read_bytes())}
        return True
    request = urllib.request.Request(url, headers={"Range": f"bytes=0-{limit - 1}"} if limit else {})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=60, context=context) as response:
                body = response.read()
            break
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                manifest["files"][key] = {"url": url, "missing": exc.code}
                return False
            if attempt == 3:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
        time.sleep(2 ** (attempt + 1))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    manifest["files"][key] = {"url": url, "sha256": _sha256(body)}
    return True


# --- parsing ----------------------------------------------------------------------


def test_patch(eval_script: str) -> str:
    """The benchmark test patch: the heredoc fed to ``git apply`` in eval.sh."""
    match = re.search(r"git apply [^\n]*<<'(EOF_\w+)'\n(.*?)^\1$", eval_script,
                      re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError("eval.sh has no git apply heredoc")
    return match.group(2)


def base_commit(eval_script: str, test_output_head: str) -> str:
    """Base commit: eval.sh resets test files from it, or test_output shows the diff from it."""
    for text, pattern in ((eval_script, r"^git checkout ([0-9a-f]{40}) "),
                          (test_output_head, r"git -c core\.fileMode=false diff ([0-9a-f]{40})")):
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1)
    raise ValueError("base commit not found")


def patch_paths(patch: str) -> list[str]:
    """Paths a unified diff touches (both sides of renames)."""
    paths = []
    for old, new in re.findall(r"^diff --git a/(\S+) b/(\S+)$", patch, re.MULTILINE):
        paths += [p for p in (old, new) if p not in paths]
    return paths


def test_class(test: str, by_simple_name: dict[str, list[str]]) -> str | None:
    """Benchmark test name -> test class ID, or None when it cannot be mapped."""
    data_driven = re.fullmatch(r".*\(([\w.$]+)\)", test)
    if data_driven:
        return data_driven.group(1)
    name = test.split("#", 1)[0].split(" > ", 1)[0].strip()
    if "." in name:
        return name
    matches = by_simple_name.get(name, [])
    return matches[0] if len(matches) == 1 else None


def wilson(hits: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    p = hits / total
    centre = (p + Z * Z / (2 * total)) / (1 + Z * Z / total)
    half = Z * sqrt(p * (1 - p) / total + Z * Z / (4 * total * total)) / (1 + Z * Z / total)
    return [round(centre - half, 4), round(centre + half, 4)]


# --- run --------------------------------------------------------------------------


def run(data: Path, work: Path, out: Path, repo_url: str = REPO_URL,
        only: list[str] | None = None, jobs: int = 1) -> dict:
    """Analyse every pair; resumable (one checkpoint file per finished instance).

    Instances of one project share a clone, so they run in order in one
    worker; ``jobs`` workers handle different projects at the same time.
    """
    data, work, out = data.resolve(), work.resolve(), out.resolve()
    if (out / "summary.json").exists():
        raise SystemExit(f"{out} already has results; results are never overwritten")
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    work.mkdir(parents=True, exist_ok=True)
    (out / "partial").mkdir(parents=True, exist_ok=True)
    instances = sorted({i for s in manifest["submissions"].values() for i in s["instances"]})
    if only:
        instances = [i for i in instances if i in only]
    groups: dict[str, list[str]] = {}
    for instance in instances:
        groups.setdefault(instance.rsplit("-", 1)[0], []).append(instance)
    tasks = [(data, work, out, repo_url, manifest, group) for group in groups.values()]
    if jobs > 1:
        import multiprocessing
        with multiprocessing.get_context("spawn").Pool(jobs) as pool:
            for _ in pool.imap_unordered(_run_group, tasks):
                pass
    else:
        for task in tasks:
            _run_group(task)
    rows = []
    for instance in instances:
        rows += json.loads((out / "partial" / f"{instance}.json").read_text(encoding="utf-8"))
    summary = summarise(rows)
    summary["experiments_commit"] = manifest["experiments_commit"]
    summary["manifest_sha256"] = _sha256((data / "manifest.json").read_bytes())
    here = Path(__file__).resolve().parent
    summary["codedna_commit"] = _git(here, "rev-parse", "HEAD").strip()
    summary["codedna_worktree_clean"] = not _git(here, "status", "--porcelain", "--", "../backend",
                                                 "../scripts").strip()
    with open(out / "pairs.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _run_group(task) -> None:
    data, work, out, repo_url, manifest, group = task
    for instance in group:
        checkpoint = out / "partial" / f"{instance}.json"
        if checkpoint.exists():
            continue
        rows = _run_instance(data, work, repo_url, manifest, instance)
        partial = checkpoint.with_suffix(".json.partial")
        partial.write_text(json.dumps(rows, indent=1), encoding="utf-8")
        partial.replace(checkpoint)


def _run_instance(data, work, repo_url, manifest, instance) -> list[dict]:
    from codedna.selection.baselines import select_tests
    from codedna_java.discovery import discover_tests_for_commit

    owner, rest = instance.split("__", 1)
    name = rest.rsplit("-", 1)[0]
    repository = f"{owner}/{name}"
    submissions = sorted(s for s, v in manifest["submissions"].items() if instance in v["instances"])
    try:
        folder = data / "instances" / instance
        script = _read_exact(folder / "eval.sh")
        head = (folder / "test_output_head.txt").read_text(encoding="utf-8", errors="replace")
        if (folder / "test_output_alt.txt.gz").exists():
            head += gzip.decompress((folder / "test_output_alt.txt.gz").read_bytes()).decode(
                "utf-8", "replace")
        base, tests_patch = base_commit(script, head), test_patch(script)
        repo = _project(work, owner, name, repo_url)
        _git(repo, "fetch", "--quiet", "--depth", "1", "origin", base)
        t_commit = _state(repo, base, None, tests_patch, f"{instance} tests")
    except (OSError, ValueError, GitCommandError) as exc:
        print(f"{instance}: {exc}", file=sys.stderr, flush=True)
        return [_row(s, instance, repository, "instance_error", note=str(exc)[:200])
                for s in submissions]
    cache: dict = {}  # parses by blob SHA; the pairs of one instance share almost all files
    discovery = discover_tests_for_commit(repo, t_commit, cache=cache)
    by_simple: dict[str, list[str]] = {}
    for test in discovery.tests:
        by_simple.setdefault(test.id.rsplit(".", 1)[-1], []).append(test.id)
    rows = []
    for submission in submissions:
        started = time.time()
        rows.append(_pair(data, repo, submission, instance, repository, base, t_commit,
                          tests_patch, by_simple,
                          functools.partial(select_tests, cache=cache)))
        print(f"{instance} {submission}: {rows[-1]['status']} ({time.time() - started:.0f}s)",
              file=sys.stderr, flush=True)
    return rows


def _pair(data, repo, submission, instance, repository, base, t_commit, tests_patch,
          by_simple, select_tests) -> dict:
    folder = data / "submissions" / submission / instance
    report_file, patch_file = folder / "report.json", folder / "patch.diff"
    if not report_file.exists() or not patch_file.exists():
        return _row(submission, instance, repository, "no_patch")
    report = json.loads(report_file.read_text(encoding="utf-8")).get(instance, {})
    patch = _read_exact(patch_file)
    if (report.get("patch_is_None") or not report.get("patch_successfully_applied")
            or report.get("infra_failure") or not patch.strip()):
        return _row(submission, instance, repository, "excluded_by_harness")
    status = report.get("tests_status", {})
    failed = (status.get("FAIL_TO_PASS", {}).get("failure", [])
              + status.get("PASS_TO_PASS", {}).get("failure", []))
    f2p = (status.get("FAIL_TO_PASS", {}).get("success", [])
           + status.get("FAIL_TO_PASS", {}).get("failure", []))
    try:
        h_commit = _state(repo, base, patch, tests_patch, f"{instance} {submission}")
    except GitCommandError as exc:
        return _row(submission, instance, repository, "not_applied", note=str(exc)[:200])
    selection = select_tests(repo, t_commit, h_commit, "dependency", policy=False)
    universe = set(selection.selected_ids) | set(selection.skipped)
    selected = selection.selected_ids
    failing_classes = {test_class(t, by_simple) for t in failed}
    f2p_classes = {test_class(t, by_simple) for t in f2p}
    unmapped = sum(test_class(t, by_simple) is None for t in failed + f2p)
    failing_classes.discard(None)
    f2p_classes.discard(None)
    retest_all = any("falling back to retest-all" in r for s in selection.selected for r in s.reasons)
    row = _row(submission, instance, repository, "analysed",
               resolved=bool(report.get("resolved")), failing=bool(failed),
               failing_classes=";".join(sorted(failing_classes)), unmapped_tests=unmapped,
               f2p_classes=";".join(sorted(f2p_classes)), total_tests=selection.total_tests,
               a2_selected=len(selected), a2_ratio=selection.selection_ratio,
               a2_retest_all=retest_all)
    if failing_classes:
        row["a1_caught"] = bool(failing_classes & universe)
        row["a2_caught"] = bool(failing_classes & selected)
    if report.get("resolved") and f2p_classes:
        row["a2_reach"] = f2p_classes <= selected
    return row


def _project(work: Path, owner: str, name: str, repo_url: str) -> Path:
    repo = work / f"{owner}__{name}"
    if not (repo / ".git").exists():
        repo.mkdir(parents=True, exist_ok=True)
        _git(repo, "init", "--quiet")
        _git(repo, "remote", "add", "origin", repo_url.format(owner=owner, name=name))
    if Path(_git(repo, "rev-parse", "--show-toplevel").strip()).resolve() != repo.resolve():
        raise ValueError(f"{repo} is not its own Git repository")
    return repo


def _state(repo: Path, base: str, agent_patch: str | None, tests_patch: str, message: str) -> str:
    """Commit B (+ agent patch, test files reset) + benchmark test patch; return its SHA."""
    _git(repo, "checkout", "--quiet", "--force", "--detach", base)
    _git(repo, "clean", "--quiet", "-fdx")
    patches = repo / ".git" / "codedna-study"
    patches.mkdir(exist_ok=True)
    if agent_patch is not None:
        (patches / "agent.diff").write_bytes(agent_patch.encode("utf-8", "surrogateescape"))
        _git(repo, "apply", "--whitespace=nowarn", str(patches / "agent.diff"))
        for path in patch_paths(tests_patch):
            if _git(repo, "ls-tree", "--name-only", base, "--", path).strip():
                _git(repo, "checkout", base, "--", path)
            elif (repo / path).exists():
                (repo / path).unlink()
    (patches / "tests.diff").write_bytes(tests_patch.encode("utf-8", "surrogateescape"))
    _git(repo, "apply", "--whitespace=nowarn", str(patches / "tests.diff"))
    _git(repo, "add", "-A")
    _git(repo, *IDENTITY, "commit", "--quiet", "--no-verify", "--allow-empty", "-m", message)
    return _git(repo, "rev-parse", "HEAD").strip()


def _row(submission, instance, repository, status, **values) -> dict:
    row = {field: "" for field in FIELDS}
    row.update(submission=submission, instance=instance, repository=repository, status=status,
               **values)
    return row


def summarise(rows: list[dict]) -> dict:
    analysed = [r for r in rows if r["status"] == "analysed"]
    statuses: dict[str, int] = {}
    for row in rows:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1

    def block(group: list[dict]) -> dict:
        failing = [r for r in group if r["a2_caught"] != ""]
        reach = [r for r in group if r["a2_reach"] != ""]
        ratios = [r["a2_ratio"] for r in group if r["total_tests"]]
        quartiles = statistics.quantiles(ratios, n=4) if len(ratios) >= 2 else None
        a1 = sum(r["a1_caught"] is True for r in failing)
        a2 = sum(r["a2_caught"] is True for r in failing)
        hit = sum(r["a2_reach"] is True for r in reach)
        return {
            "pairs": len(group),
            "failing_pairs": sum(r["failing"] is True for r in group),
            "failing_pairs_mapped": len(failing),
            "a1_catch": [a1, len(failing)], "a1_catch_ci": wilson(a1, len(failing)),
            "a2_catch": [a2, len(failing)], "a2_catch_ci": wilson(a2, len(failing)),
            "a2_ratio_median": round(statistics.median(ratios), 4) if ratios else None,
            "a2_ratio_iqr": [round(q, 4) for q in (quartiles[0], quartiles[2])] if quartiles else None,
            "a2_retest_all_share": round(sum(r["a2_retest_all"] is True for r in group) / len(group), 4)
            if group else None,
            "pairs_without_tests": sum(not r["total_tests"] for r in group),
            "a2_reach": [hit, len(reach)], "a2_reach_ci": wilson(hit, len(reach)),
            "unmapped_tests": sum(r["unmapped_tests"] or 0 for r in group),
        }

    return {
        "statuses": statuses,
        "all": block(analysed),
        "by_repository": {repo: block([r for r in analysed if r["repository"] == repo])
                          for repo in sorted({r["repository"] for r in analysed})},
        "by_submission": {s: block([r for r in analysed if r["submission"] == s])
                          for s in sorted({r["submission"] for r in analysed})},
    }


def _read_exact(path: Path) -> str:
    """File text with line endings and undecodable bytes kept, so patches apply as published."""
    return path.read_bytes().decode("utf-8", "surrogateescape")


def _git(repo: Path, *args: str) -> str:
    return run_git(repo, *args)


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fetch", help="download public patches and reports")
    f.add_argument("--data", type=Path, required=True)
    r = sub.add_parser("run", help="compute the brake's plans for every applied patch")
    r.add_argument("--data", type=Path, required=True)
    r.add_argument("--work", type=Path, required=True, help="folder for project clones")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--instance", action="append", help="limit to these instance ids (smoke test)")
    r.add_argument("--jobs", type=int, default=1, help="projects analysed at the same time")
    args = parser.parse_args(argv)
    if args.command == "fetch":
        fetch(args.data)
    else:
        summary = run(args.data, args.work, args.out, only=args.instance, jobs=args.jobs)
        print(json.dumps(summary["all"], indent=2))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")
    sys.exit(main())
