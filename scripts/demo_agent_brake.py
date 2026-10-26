"""Demo of the test brake for AI coding agents (D-059), over real MCP stdio.

Creates a throwaway Git repository from examples/sample-java-project, makes
the kind of edit an agent might make (a wrong discount formula, left
uncommitted), then talks to ``codedna mcp`` exactly as an agent would:
``initialize``, ``tools/list``, ``codedna_plan_tests``, ``codedna_impact``
and, with ``--check``,
``codedna_check``.

``--check`` runs Maven on the demo repository this script just created, so
it needs Maven and a JDK; it is never on by default.

Usage (from the repository root):
    python scripts/demo_agent_brake.py DEST_DIR [--check] [--mvn PATH]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample-java-project"
IDENTITY = ("-c", "user.name=CodeDNA Demo", "-c", "user.email=demo@example.invalid")
CORRECT = "return amount * (1.0 - discountRate);"
WRONG = "return amount * discountRate;  // agent's edit: wrong formula"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *IDENTITY, *args], cwd=repo, capture_output=True, check=True)


def make_repo(dest: Path) -> None:
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"{dest} is not empty")
    shutil.copytree(SAMPLE, dest, dirs_exist_ok=True)
    git(dest, "init", "--quiet")
    git(dest, "add", "--all")
    git(dest, "commit", "--quiet", "-m", "sample project")
    source = dest / "src/main/java/example/PriceCalculator.java"
    text = source.read_text(encoding="utf-8")
    if CORRECT not in text:
        raise SystemExit("the sample project changed; update the demo edit")
    with open(source, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.replace(CORRECT, WRONG))


class Client:
    """Minimal MCP client: one JSON-RPC message per line on the server's stdin/stdout."""

    def __init__(self, command: list[str]):
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        text=True, encoding="utf-8")
        self.next_id = 0

    def request(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        message = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        if params is not None:
            message["params"] = params
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()
        answer = json.loads(self.process.stdout.readline())
        if "error" in answer:
            raise RuntimeError(f"{method}: {answer['error']['message']}")
        return answer["result"]

    def notify(self, method: str) -> None:
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.process.stdin.flush()

    def close(self) -> int:
        self.process.stdin.close()
        return self.process.wait(timeout=30)


def run_demo(dest: Path, check: bool, mvn: str | None) -> dict:
    make_repo(dest)
    command = [sys.executable, "-m", "codedna", "mcp", "--repo", str(dest)]
    if check:
        command.append("--allow-build")
    if mvn:
        command += ["--mvn", mvn]
    client = Client(command)
    try:
        info = client.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                             "clientInfo": {"name": "codedna-demo", "version": "1"}})
        client.notify("notifications/initialized")
        tools = [t["name"] for t in client.request("tools/list")["tools"]]
        print(f"server {info['serverInfo']['name']} {info['serverInfo']['version']}, tools: {tools}")
        plan = client.request("tools/call", {"name": "codedna_plan_tests", "arguments": {}})
        planned = plan["structuredContent"]
        print(f"\nplan: {planned['summary']}")
        for test in planned["must_run"]:
            print(f"  {test}: {'; '.join(planned['reasons'][test])}")
        impact = client.request("tools/call", {"name": "codedna_impact", "arguments": {}})
        linked = impact["structuredContent"]["candidate_tests"]
        print("\nimpact: tests linked to the change through the dependency graph:")
        for test in linked:
            print(f"  {test['type'].removeprefix('type:')}: {test['reason']}")
        result = {"tools": tools, "plan": planned, "linked_tests": linked}
        if check:
            answer = client.request("tools/call", {"name": "codedna_check", "arguments": {}})
            verdict = answer["structuredContent"]
            print(f"\ncheck: {verdict.get('verdict', 'error')}: "
                  f"{verdict.get('message', verdict.get('error'))}")
            result["check"] = verdict
    finally:
        client.close()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dest", type=Path, help="new, empty folder for the demo repository")
    parser.add_argument("--check", action="store_true",
                        help="also run the planned tests with Maven (executes the demo project)")
    parser.add_argument("--mvn", help="Maven executable for --check")
    args = parser.parse_args(argv)
    result = run_demo(args.dest, args.check, args.mvn)
    return 1 if result.get("check", {}).get("verdict") == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
