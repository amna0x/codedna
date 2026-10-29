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
* ``--moonshot`` additionally exposes bounded Java behavioral witnesses with
  that same consent/repository binding. It never replaces the test brake.
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
    "profile": {"type": "boolean", "description": "Include measured operation timings; a check includes test execution."},
    "repo": {"type": "string", "description": "Path of the Git repository (default: the server's --repo)."},
    "base": {"type": "string", "description": "Base revision (default HEAD)."},
    "head": {"type": "string", "description": "Changed revision; WORKTREE (default) means uncommitted changes."},
}
_RISK = {
    "risk_target": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1,
                    "description": "Highest accepted chance that a skipped test would fail (default 0.05)."},
    "must_run": {"type": "array", "items": {"type": "string"},
                 "description": "Extra test IDs or patterns that may never be skipped."},
    "method": {"type": "string", "enum": ["b10", "crc"],
               "description": ("How the stop is chosen on validated history: b10 (default) stops at "
                               "risk_target estimated skip risk behind the history audit; crc picks "
                               "the stop by conformal risk control so that at most risk_target of "
                               "past failing commits would have missed a failure.")},
}

TOOLS = {
    "codedna_plan_tests": {
        "description": (
            "Before finishing a code change, ask which tests must run for it. "
            "Returns required tests, reasons, skip risk, and a separate structural_plan "
            "labelled structural only, no probability. Structural tests are always required. "
            "Without validated risk support/history it lists every test, including Python "
            "and mixed-language suites. Runs no code."),
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
            **_CHANGE, **_RISK,
            "shadow": {"type": "boolean", "description": "Observe the recommendation but run the full suite; does not authorize skipping."},
            "attempts": {"type": "integer", "minimum": 1, "maximum": 3,
                         "description": "Bounded stability observations. Any failed attempt still blocks. Default 1."},
            "timeout": {"type": "integer", "minimum": 1,
                                            "description": "Build timeout in seconds (default 1800)."}},
            "additionalProperties": False},
    },

    "codedna_find_witness": {
        "description": (
            "Experimental Moonshot: execute a public Java int/long/int[] method with one or two bounded numeric/boolean/String arguments. Instance calls construct a fresh public no-argument receiver. "
            "on both versions with bounded inputs. Export a confirmed behavioral difference and standalone "
            "reproducer to a new folder outside the repository. A difference is not automatically a regression. "
            "No witness does not establish equivalence or justify skipping tests. Still call codedna_check. "
            "Executes trusted project code; offered only with --moonshot --allow-build --repo."),
        "inputSchema": {"type": "object", "properties": {
            **_CHANGE, "file": {"type": "string"}, "symbol": {"type": "string"},
            "output_dir": {"type": "string"},
            "support_files": {"type": "array", "maxItems": 3, "uniqueItems": True,
                              "items": {"type": "string", "maxLength": 1024}},
            "expectation": {"type": "object", "properties": {
                "input": {"description": "Scalar or integer array for one argument; two-element array for two. Plugins validate declared types.",
                    "oneOf": [{"type": "integer", "minimum": -9223372036854775808, "maximum": 9223372036854775807},
                              {"type": "boolean"}, {"type": "string", "maxLength": 128},
                              {"type": "array", "maxItems": 8,
                               "items": {"oneOf": [{"type": "integer", "minimum": -9223372036854775808, "maximum": 9223372036854775807},
                                                     {"type": "boolean"}, {"type": "string", "maxLength": 128},
                                                     {"type": "array", "maxItems": 8, "items": {"type": "integer", "minimum": -2147483648, "maximum": 2147483647}}]}}]},
                "expected": {"oneOf": [{"type": "integer", "minimum": -9223372036854775808, "maximum": 9223372036854775807},
                    {"type": "array", "maxItems": 128, "items": {"type": "integer", "minimum": -2147483648, "maximum": 2147483647}}]},
                "requirement": {"type": "string", "minLength": 1, "maxLength": 2000}},
                "required": ["input", "expected", "requirement"], "additionalProperties": False},
            "max_inputs": {"type": "integer", "minimum": 1, "maximum": 64},
            "seed": {"type": "integer", "minimum": 0, "maximum": 4294967295},
            "timeout": {"type": "integer", "minimum": 1, "maximum": 120},
            "reduce_budget": {"type": "integer", "minimum": 0, "maximum": 16},
            "generation": {"type": "string", "enum": ["guided", "simple"]}},
            "required": ["file", "symbol", "output_dir"], "additionalProperties": False},
    },

}


class ToolError(Exception):
    """A tool call that cannot be served; reported to the agent as a tool error."""


class BrakeServer:
    def __init__(self, *, repo: Path | None = None, allow_build: bool = False,
                 build_options: dict | None = None, moonshot: bool = False):
        if not isinstance(moonshot, bool) or moonshot and allow_build is not True:
            raise ValueError('--moonshot requires explicit --allow-build and a repository')
        if allow_build and repo is None:
            raise ValueError("--allow-build needs --repo: builds run for one repository only")
        self.repo = resolve_repository(repo) if repo is not None else None
        self.allow_build = allow_build
        self.build_options = build_options or {}
        self.moonshot = moonshot

    def _available(self, name):
        if name == 'codedna_check':
            return self.allow_build
        if name == 'codedna_find_witness':
            return self.moonshot and self.allow_build
        return True

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
                                             if self._available(name)]})
        if method == "tools/call":
            return self._call(ident, params)
        return _error(ident, -32601, f"method not found: {method}")

    def _call(self, ident, params: dict) -> dict:
        name, arguments = params.get("name"), params.get("arguments") or {}
        if not isinstance(name, str) or name not in TOOLS or not self._available(name):
            return _error(ident, -32602, f"unknown tool: {name}")
        if not isinstance(arguments, dict):
            return _error(ident, -32602, "arguments must be an object")
        allowed = set(TOOLS[name]["inputSchema"]["properties"])
        unknown = sorted(set(arguments) - allowed)
        if unknown:
            return _error(ident, -32602, f"unknown arguments: {unknown}")
        profile = arguments.get('profile', False)
        if not isinstance(profile, bool):
            return _error(ident, -32602, 'profile must be a boolean')
        try:
            from codedna.performance import capture_timings
            with capture_timings(profile) as timings:
                data = self._run(name, arguments)
            if timings is not None:
                data = {**data, 'operation_timings': {**timings.to_dict(),
                     'scope': ('includes_project_execution' if name == 'codedna_find_witness' else
                              'includes_test_execution' if name == 'codedna_check' else 'analysis_only')}}
        except ToolError as exc:
            return _result(ident, _content({"error": str(exc)}, error=True))
        except Exception as exc:  # analysis errors go back to the agent, not a crash
            print(traceback.format_exc(), file=sys.stderr)
            return _result(ident, _content({"error": f"{type(exc).__name__}: {exc}"}, error=True))
        failed_witness = name == 'codedna_find_witness' and data.get('status') not in ('difference', 'no_difference_observed')
        return _result(ident, _content(data, error=failed_witness))

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
        if name == 'codedna_check':
            from codedna.behavior import execution_block_reason
            if execution_block_reason():
                raise ToolError(execution_block_reason())
        if name == 'codedna_find_witness':
            from codedna.behavior import find_difference
            for key in ('file', 'symbol', 'output_dir'):
                if not isinstance(arguments.get(key), str) or not arguments[key].strip():
                    raise ToolError(key + ' must be a non-empty string')
            try:
                return find_difference(repo, base, head, file=arguments['file'], symbol=arguments['symbol'],
                    output_dir=arguments['output_dir'], allow_build=self.allow_build,
                    max_inputs=arguments.get('max_inputs', 16), seed=arguments.get('seed', 0),
                    timeout=arguments.get('timeout', 30), reduce_budget=arguments.get('reduce_budget', 8),
                    generation=arguments.get('generation', 'guided'), expectation=arguments.get('expectation'),
                    support_files=arguments.get('support_files'))
            except ValueError as exc:
                raise ToolError(str(exc)) from exc
        method = arguments.get("method", "b10")
        if method not in ("b10", "crc"):
            raise ToolError("method must be b10 or crc")
        risk = {"risk_target": _risk_target(arguments), "must_run": _patterns(arguments),
                "method": method}
        if name == "codedna_plan_tests":
            return brake.plan(repo, base=base, head=head, **risk)
        if name == "codedna_impact":
            return _impact(repo, base, head, arguments.get("max_depth"))
        timeout = arguments.get("timeout", 1800)
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
            raise ToolError("timeout must be a positive integer")
        shadow = arguments.get("shadow", False)
        if not isinstance(shadow, bool):
            raise ToolError("shadow must be a boolean")
        attempts = arguments.get("attempts", 1)
        if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= 3:
            raise ToolError("attempts must be an integer between 1 and 3")
        return brake.check(repo, base=base, head=head, timeout=timeout, shadow=shadow, attempts=attempts, **risk,
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


def main(repo: str | None, allow_build: bool, build_options: dict | None = None, *, moonshot=False) -> int:
    try:
        server = BrakeServer(repo=Path(repo) if repo else None, allow_build=allow_build,
                             build_options=build_options, moonshot=moonshot)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if allow_build:
        print(f"warning: codedna_check will run the build of {server.repo} when an agent "
              "asks; only use this on projects you trust", file=sys.stderr)
    return server.serve(sys.stdin, sys.stdout)
