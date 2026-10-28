"""Produce a read-only AI-brake plan for a PR; this never runs project tests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from codedna.agent.brake import plan


def write_report(repo: Path, base: str, head: str, output: Path) -> dict:
    planned = plan(repo, base=base, head=head)
    output.mkdir(parents=True, exist_ok=True)
    (output / "plan.json").write_text(json.dumps(planned, indent=2) + "\n", encoding="utf-8")
    lines = ["# CodeDNA PR analysis", "", "Analysis only. Project tests have not been executed.", "",
             f"BASE: `{planned['base_commit']}`", f"HEAD: `{planned['head_commit']}`", "",
             f"Risk status: **{planned['risk']['status']}**.", planned["summary"], "",
             "Structural relationships are analysis evidence, not a probability guarantee.", "",
             "## Required tests", ""]
    lines += [f"- `{test}`" for test in planned["must_run"]] or ["No runnable tests discovered; no change has been verified."]
    lines += ["", "## Limitations", ""]
    # JSON quoting keeps repository-controlled messages out of Markdown/HTML syntax.
    lines += ["- " + json.dumps(reason, ensure_ascii=True).replace("<", "&lt;").replace(">", "&gt;")
              for reason in [*planned["risk"]["reasons"], *planned["warnings"]]]
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return planned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    write_report(args.repo, args.base, args.head, args.out)
    print(f"Analysis saved to {args.out}; tests were not executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
