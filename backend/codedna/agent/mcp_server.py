"""``codedna mcp``: the test brake as a Model Context Protocol server over stdio (D-059).

Coding agents (Claude Code, Cursor, Codex and others) start this process and
exchange newline-delimited JSON-RPC 2.0 messages on stdin/stdout. Only the
small part of MCP that tools need is implemented (``initialize``, ``ping``,
``tools/list``, ``tools/call``), so no extra dependency is required. Logs go
to stderr; stdout carries protocol messages only.

Safety:

* ``plan`` and ``impact`` read Git objects only; no project code runs.
* ``check`` runs the project's build. It is offered only when the person
  started the server with ``--allow-build`` and ``--repo``. It then works for
  that one repository, whatever path the agent sends.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import IO, Any

from codedna import __version__
from codedna.git_analysis.git import WORKTREE, resolve_repository

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")

_CHANGE = {
    "repo": {"type": "string", "description": "Path of the Git repository (default: the server's --repo)."},
    "base": {"type": "string", "description": "Base revision (default HEAD)."},
    "head": {"type": "string", "description": "Changed revision; WORKTREE (default) means uncommitted changes."},
}
_RISK = {
    "risk_target": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1,
                    "description": "Highest accepted chance that a skipped test would fail (default 0.05)."},
    "must_run": {"type": "array", "items": {"type": "string"},
                 "description": "Extra test IDs or patterns that may never be skipped."},
}

TOOLS = {
    "codedna_plan_tests": {
        "description": (
            "Before finishing a code change, ask which test classes must run for it. "
            "Returns the tests, a reason for each, and the risk of skipping the rest. "
            "Without validated project history it lists every test. Runs no code."),
        "inputSchema": {"type": "object", "properties": {**_CHANGE, **_RISK},
                        "additionalProperties": False},
    },
    "codedna_impact": {
        "description": (
            "Show which code a change can affect through dependencies, with confirmed and "
            "heuristic links kept apart, plus the changed files CodeDNA cannot analyse. Runs no code."),
        "inputSchema": {"type": "object", "properties": {
            **_CHANGE, "max_depth": {"type": "integer", "minimum": 1}},
            "additionalProperties": False},
    },
    "codedna_check": {
        "description": (
            "Run the planned tests and get one verdict: passed, blocked (a test failed), "
            "incomplete (missing results, a build error or timeout, or every test skipped), "
            "nothing_to_run (validated history: no test needed) or no_tests. "
            "Do not report the change as done unless the verdict is passed. "
            "Executes the project's build."),
        "inputSchema": {"type": "object", "properties": {
            **_CHANGE, **_RISK, "timeout": {"type": "integer", "minimum": 1,
                                            "description": "Build timeout in seconds (default 1800)."}},
            "additionalProperties": False},
    },
}


class ToolError(Exception):
    """A tool call that cannot be served; reported to the agent as a tool error."""


class BrakeServer:
    def __init__(self, *, repo: Path | None = None, allow_build: bool = False,
                 build_options: dict | None = None):
        if allow_build and repo is None:
            raise ValueError("--allow-build needs --repo: builds run for one repository only")
        self.repo = resolve_repository(repo) if repo is not None else None
        self.allow_build = allow_build
        self.build_options = build_options or {}

    # --- protocol ---------------------------------------------------------------

    def handle(self, message: Any) -> dict | None:
        """Answer one JSON-RPC message; ``None`` for notifications."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" \
                or not isinstance(message.get("method"), str):
            return _error(message.get("id") if isinstance(message, dict) else None,
                          -32600, "invalid request")
        method, ident = message["method"], message.get("id")
        if "id" not in message:
            return None  # notification (e.g. notifications/initialized): no answer
        params = message.get("params") or {}
        if not isinstance(params, dict):
            return _error(ident, -32602, "params must be an object")
        if method == "initialize":
            requested = params.get("protocolVersion")
            version = requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
            return _result(ident, {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "codedna", "version": __version__},
                "instructions": ("Call codedna_plan_tests after editing code, and codedna_check "
                                 "before saying the change is done (when it is available)."),
            })
        if method == "ping":
            return _result(ident, {})
        if method == "tools/list":
            return _result(ident, {"tools": [{"name": name, **spec}
                                             for name, spec in TOOLS.items()
                                             if name != "codedna_check" or self.allow_build]})
        if method == "tools/call":
            return self._call(ident, params)
        return _error(ident, -32601, f"method not found: {method}")

    def _call(self, ident, params: dict) -> dict:
        name, arguments = params.get("name"), params.get("arguments") or {}
        if not isinstance(name, str) or name not in TOOLS or (name == "codedna_check" and not self.allow_build):
            return _error(ident, -32602, f"unknown tool: {name}")
        if not isinstance(arguments, dict):
            return _error(ident, -32602, "arguments must be an object")
        allowed = set(TOOLS[name]["inputSchema"]["properties"])
        unknown = sorted(set(arguments) - allowed)
        if unknown:
            return _error(ident, -32602, f"unknown arguments: {unknown}")
        try:
            data = self._run(name, arguments)
        except ToolError as exc:
            return _result(ident, _content({"error": str(exc)}, error=True))
        except Exception as exc:  # analysis errors go back to the agent, not a crash
            print(traceback.format_exc(), file=sys.stderr)
            return _result(ident, _content({"error": f"{type(exc).__name__}: {exc}"}, error=True))
        return _result(ident, _content(data))

    # --- tools ------------------------------------------------------------------

    def _repo(self, arguments: dict) -> Path:
        given = arguments.get("repo")
        if given is None:
            if self.repo is None:
                raise ToolError("give 'repo' (the server was started without --repo)")
            return self.repo
        repo = resolve_repository(given)
        if self.repo is not None and repo != self.repo:
            raise ToolError(f"this server serves {self.repo} only")
        return repo

    def _run(self, name: str, arguments: dict) -> dict:
        from codedna.agent import brake

        repo = self._repo(arguments)
        base, head = arguments.get("base", "HEAD"), arguments.get("head", WORKTREE)
        if not isinstance(base, str) or not isinstance(head, str):
            raise ToolError("base and head must be strings")
        risk = {"risk_target": _risk_target(arguments), "must_run": _patterns(arguments)}
        if name == "codedna_plan_tests":
            return brake.plan(repo, base=base, head=head, **risk)
        if name == "codedna_impact":
            return _impact(repo, base, head, arguments.get("max_depth"))
        timeout = arguments.get("timeout", 1800)
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
            raise ToolError("timeout must be a positive integer")
        return brake.check(repo, base=base, head=head, timeout=timeout, **risk,
                           allow_build=self.allow_build, **self.build_options)

    # --- loop -------------------------------------------------------------------

    def serve(self, stdin: IO[str], stdout: IO[str]) -> int:
        for line in stdin:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                answer = _error(None, -32700, "parse error")
            else:
                answer = self.handle(message)
            if answer is not None:
                stdout.write(json.dumps(answer) + "\n")
                stdout.flush()
        return 0


def _impact(repo: Path, base: str, head: str, max_depth) -> dict:
    from codedna.impact_analysis.impact import compute_impact

    if max_depth is not None and (not isinstance(max_depth, int) or max_depth < 1):
        raise ToolError("max_depth must be a positive integer")
    report = compute_impact(repo, base, head, max_depth=max_depth).to_dict()
    keep = ("base_commit", "head_commit", "seeds", "impacted", "candidate_tests",
            "ignored_changes", "unanalysed_changes", "warnings")
    return {key: report[key] for key in keep if key in report}


def _risk_target(arguments: dict) -> float:
    value = arguments.get("risk_target", 0.05)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value < 1:
        raise ToolError("risk_target must be a number strictly between 0 and 1")
    return float(value)


def _patterns(arguments: dict) -> list[str] | None:
    value = arguments.get("must_run")
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise ToolError("must_run must be a list of non-empty strings")
    return value


def _content(data: dict, *, error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}],
            "structuredContent": data, "isError": error}


def _result(ident, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": ident, "result": result}


def _error(ident, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": ident, "error": {"code": code, "message": message}}


def main(repo: str | None, allow_build: bool, build_options: dict | None = None) -> int:
    try:
        server = BrakeServer(repo=Path(repo) if repo else None, allow_build=allow_build,
                             build_options=build_options)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if allow_build:
        print(f"warning: codedna_check will run the build of {server.repo} when an agent "
              "asks; only use this on projects you trust", file=sys.stderr)
    return server.serve(sys.stdin, sys.stdout)
