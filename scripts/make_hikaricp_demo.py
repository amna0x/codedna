"""Create a demo workspace from HikariCP's real history (RTPTorrent).

The toy sample project shows the views but not a real decision. This script
builds a working copy of HikariCP whose last commit is a real change that CI
tested, with the project's own recorded test history up to the commit before
it, so the IDE (and ``codedna risk-select``) can make a target-validated
recommendation and the presenter can compare it with what CI really saw.

1. Clone the RTPTorrent bare repository into DEST and check out the demo
   commit on a ``codedna-demo`` branch (HEAD~1 = BASE, HEAD = the change).
2. Write ``DEST/.codedna/history.csv``: the study's feature rows for tested
   commits on BASE's first-parent line, up to and including BASE (no row of
   the demo commit or later is written).
3. Write ``DEST/.codedna/demo.json``: CodeDNA's dependency selection and its
   risk recommendation for the change, next to the real CI outcome of the
   demo commit taken from RTPTorrent.

The default commit (dd7c9a9a, a ConcurrentBag change whose CI run failed 17
of 21 test classes) was picked from ``--list``, which shows every Java-only
tested change with a failing CI run: it is a picked example for the
demonstration, not evidence. The study results are the evidence. On this
history the risk gate refuses (CI records sometimes lack a test class), so
the risk view honestly recommends the full suite; the replay view shows the
calibrated stopping on the same project.

No project code is built or run. Usage (from the repository root):

    python scripts/make_hikaricp_demo.py DEST
    python scripts/make_hikaricp_demo.py --list
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codedna.git_analysis.git import run_git
from codedna.selection import select_tests
from codedna.test_history.features import Dataset

ROOT = Path(__file__).resolve().parents[1]
BARE = ROOT / "experiments/datasets/raw/rtp-torrent/repo/brettwooldridge@HikariCP"
DATASET = ROOT / "experiments/results/study11-2026-10-21/hikaricp/dataset.csv"
DEMO_COMMIT = "dd7c9a9add9ce9d091bdcbbbe38946e245dde5a0"


def first_parents(repo: Path, rev: str) -> list[str]:
    return run_git(repo, "rev-list", "--first-parent", "--reverse", rev).split()


def candidates(dataset: Dataset, repo: Path) -> list[tuple[str, str]]:
    """(BASE, HEAD): consecutive tested commits where BASE is HEAD's first parent."""
    order = {c: i for i, c in enumerate(first_parents(repo, "HEAD"))}
    return [(b, h) for b, h in zip(dataset.commits, dataset.commits[1:])
            if b in order and h in order and order[h] == order[b] + 1]


def prior_history(dataset: Dataset, repo: Path, base: str) -> Dataset:
    """Rows of tested commits on BASE's first-parent line up to BASE; nothing later."""
    line = set(first_parents(repo, base))
    commits = [c for c in dataset.commits[:dataset.commits.index(base) + 1] if c in line]
    keep = set(commits)
    return Dataset([r for r in dataset.rows if r.commit in keep], dataset.feature_names, commits)


def real_outcome(dataset: Dataset, head: str) -> dict:
    rows = dataset.rows_by_commit()[head]
    return {"commit": head, "tests": len(rows),
            "failing_tests": sorted(r.test_id for r in rows if r.label),
            "seconds": {r.test_id: r.duration for r in rows},
            "source": "RTPTorrent v1.1 CI record of this commit"}


def scored(selected: set[str], real: dict) -> dict:
    """What a selection would have caught in the real CI run, and its CI time share."""
    failing = set(real["failing_tests"])
    seconds = sum(real["seconds"].get(t, 0.0) for t in selected)
    total = sum(real["seconds"].values())
    return {"selected": len(selected), "caught": sorted(failing & selected),
            "missed": sorted(failing - selected),
            "unrecorded_selected": sorted(selected - set(real["seconds"])),
            "share_of_ci_test_time": round(seconds / total, 4) if total else None}


def evaluate(dataset: Dataset, repo: Path, base: str, head: str, history_csv: Path) -> dict:
    from codedna.selection.live import recommend
    prior_history(dataset, repo, base).to_csv(history_csv)
    real = real_outcome(dataset, head)
    dependency = select_tests(repo, base, head, "dependency")
    risk = recommend(repo, base, head, history_csv=history_csv)
    return {
        "base": base, "head": head,
        "changed_files": run_git(repo, "diff", "--name-only", base, head).split(),
        "real": {k: v for k, v in real.items() if k != "seconds"},
        "dependency": {**scored(dependency.selected_ids, real), "total": dependency.total_tests},
        "risk": {**scored({t["test"] for t in risk["selected"]}, real),
                 "status": risk["risk"]["status"], "reasons": risk["risk"]["reasons"],
                 "estimated_skip_risk": risk["risk"]["estimated_skip_risk"]},
        "note": "A picked demonstration commit, not evidence; see the study results.",
    }


def bare_repository(path: Path) -> Path:
    if not (path / "objects").is_dir():
        raise SystemExit(f"no RTPTorrent repository at {path}; run scripts/fetch_rtptorrent_subset.py")
    # The selective download keeps files only; Git needs these (empty) folders.
    for name in ("refs/heads", "refs/tags"):
        (path / name).mkdir(parents=True, exist_ok=True)
    return path


def list_candidates(dataset: Dataset, bare: Path) -> None:
    rows = dataset.rows_by_commit()
    for base, head in candidates(dataset, bare):
        failing = {r.test_id for r in rows[head] if r.label}
        names = run_git(bare, "diff", "--name-only", base, head).split()
        if not failing or not names or not all(n.endswith(".java") for n in names):
            continue
        result = scored(select_tests(bare, base, head, "dependency", policy=False).selected_ids,
                        real_outcome(dataset, head))
        print(f"{head[:8]}  dependency {result['selected']:>2} classes  "
              f"caught {len(result['caught'])}/{len(failing)}  "
              f"CI time {result['share_of_ci_test_time']:.0%}  {names[0]}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dest", type=Path, nargs="?", help="Folder to create (must not exist)")
    parser.add_argument("--repo", type=Path, default=BARE, help="RTPTorrent bare repository")
    parser.add_argument("--dataset", type=Path, default=DATASET, help="Study dataset.csv")
    parser.add_argument("--commit", default=DEMO_COMMIT, help="Demo change (a tested commit)")
    parser.add_argument("--list", action="store_true", help="List candidate commits and exit")
    args = parser.parse_args(argv)
    bare = bare_repository(args.repo)
    dataset = Dataset.from_csv(args.dataset)
    if args.list:
        list_candidates(dataset, bare)
        return 0
    if args.dest is None:
        parser.error("give DEST or --list")
    if args.dest.exists():
        parser.error(f"{args.dest} already exists; choose a new folder")
    head = run_git(bare, "rev-parse", "--verify", args.commit + "^{commit}").strip()
    pairs = dict((h, b) for b, h in candidates(dataset, bare))
    if head not in pairs:
        parser.error(f"{head[:12]} is not a tested commit whose first parent was also tested")
    base = pairs[head]

    dest = args.dest.resolve()
    run_git(dest.parent, "clone", "--quiet", "--no-checkout", str(bare.resolve()), str(dest))
    run_git(dest, "checkout", "--quiet", "-B", "codedna-demo", head)
    folder = dest / ".codedna"
    folder.mkdir()
    with open(dest / ".git/info/exclude", "a", encoding="utf-8") as handle:
        handle.write(".codedna/\n")  # keeps the demo files out of "uncommitted changes"
    summary = evaluate(dataset, dest, base, head, folder / "history.csv")
    (folder / "demo.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    real, dep, risk = summary["real"], summary["dependency"], summary["risk"]
    print(f"Demo project: {dest}  (compare 'My last commit': {base[:8]}..{head[:8]})")
    print(f"Real CI run: {len(real['failing_tests'])} of {real['tests']} test classes failed.")
    print(f"Dependency selection: {dep['selected']} of {dep['total']} classes, caught "
          f"{len(dep['caught'])}, missed {len(dep['missed'])}, "
          f"{dep['share_of_ci_test_time']:.0%} of the CI test time.")
    print(f"Risk recommendation: {risk['status']}"
          + (f" ({risk['reasons'][0]})" if risk["reasons"] else ""))
    print(f"Details: {folder / 'demo.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
