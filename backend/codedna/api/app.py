"""Local HTTP API for the CodeDNA IDE (Milestone 6, D-019/D-028).

The API exposes the same analyses as the CLI and returns the same JSON. It is
meant to be started by the IDE on the user's own machine:

* it only listens on a loopback address (enforced by ``codedna serve``);
* every request except ``/api/health`` needs the per-session token in the
  ``X-CodeDNA-Token`` header — browsers cannot add that header to a
  cross-site request without a CORS preflight, and no CORS is allowed;
* the ``Host`` header must be a loopback name (defends against DNS rebinding);
* running a build (``/api/run-tests``) needs the server to be started with
  ``allow_build`` **and** the request to say ``allow_build: true`` (D-014).

Long operations (graph building, test runs) are synchronous; FastAPI runs them
in a worker thread. A job queue can come later if the IDE needs progress.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from codedna import __version__
from codedna.dependency_graph import build_graph
from codedna.git_analysis import CodeDNAGitError, extract_changes
from codedna.impact_analysis import compute_impact
from codedna.java_analysis import analyze_changes
from codedna.plugins import load_plugins
from codedna.selection import SelectionError, compare_strategies, select_tests
from codedna.test_mapping.discovery import discover_tests
from codedna.test_mapping.maven import run_maven_tests
from codedna.test_mapping.reports import ReportError
from codedna.test_mapping.results import (
    COVERAGE_MAP_FILE,
    RESULTS_FILE,
    load_coverage_map,
    load_results,
)

TOKEN_HEADER = "X-CodeDNA-Token"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "[::1]", "::1"})


# --- request models ----------------------------------------------------------------------


class RepoRequest(BaseModel):
    repo: str = Field(description="Path to a local Git repository.")


class RevRequest(RepoRequest):
    rev: str = "HEAD"


class ChangeRequest(RepoRequest):
    base: str
    head: str


class AnalyzeRequest(ChangeRequest):
    level: Literal["file", "method"] = "method"


class GraphRequest(RevRequest):
    include_members: bool = True


class ImpactRequest(ChangeRequest):
    max_depth: int | None = Field(default=None, ge=0)
    confirmed_only: bool = False


class SelectRequest(ChangeRequest):
    strategy: Literal["all", "dependency", "coverage"]
    coverage_map: str | None = None
    durations: str | None = None
    non_java: Literal["retest-all", "ignore"] = "retest-all"


class CompareRequest(ChangeRequest):
    ground_truth: str
    coverage_map: str | None = None
    non_java: Literal["retest-all", "ignore"] = "retest-all"


class RiskRequest(ChangeRequest):
    history_db: str = Field(description="SQLite history database of this repository.")
    risk_target: float = Field(default=0.05, ge=0.0, le=1.0)
    structural: bool = True


class RunTestsRequest(RevRequest):
    output_dir: str
    allow_build: bool = False
    per_test_coverage: bool = False
    timeout: int = Field(default=1800, ge=1)


# --- application ---------------------------------------------------------------------------


def new_token() -> str:
    return secrets.token_urlsafe(32)


def create_app(token: str, *, allow_build: bool = False,
               maven_command: list[str] | None = None) -> FastAPI:
    if len(token) < 16:
        raise ValueError("API token must be at least 16 characters")
    app = FastAPI(title="CodeDNA local API", version=__version__,
                  description="Local API used by the CodeDNA IDE. Loopback only.")
    app.state.allow_build = allow_build
    app.state.risk_gates = {}

    @app.middleware("http")
    async def loopback_host_only(request: Request, call_next):
        if _hostname(request.headers.get("host", "")) not in LOOPBACK_HOSTS:
            return JSONResponse({"error": "host not allowed"}, status_code=403)
        return await call_next(request)

    def require_token(x_codedna_token: str | None = Header(default=None)) -> None:
        if x_codedna_token is None or not secrets.compare_digest(x_codedna_token, token):
            raise HTTPException(status_code=401, detail="missing or invalid X-CodeDNA-Token")

    @app.exception_handler(CodeDNAGitError)
    async def git_error(_request: Request, exc: CodeDNAGitError):
        return JSONResponse({"error": str(exc)}, status_code=400)

    @app.exception_handler(SelectionError)
    async def selection_error(_request: Request, exc: SelectionError):
        return JSONResponse({"error": str(exc)}, status_code=400)

    @app.exception_handler(ReportError)
    async def report_error(_request: Request, exc: ReportError):
        return JSONResponse({"error": str(exc)}, status_code=400)

    @app.exception_handler(FileNotFoundError)
    async def missing_file(_request: Request, exc: FileNotFoundError):
        return JSONResponse({"error": f"file not found: {exc.filename}"}, status_code=400)

    @app.get("/api/health")
    def health() -> dict:
        """Unauthenticated liveness check; reveals nothing about repositories."""
        return {"status": "ok", "version": __version__}

    secured = [Depends(require_token)]

    @app.get("/api/plugins", dependencies=secured)
    def plugins() -> dict:
        return load_plugins().describe()

    @app.get("/api/capabilities", dependencies=secured)
    def capabilities() -> dict:
        return {"version": __version__, "allow_build": app.state.allow_build,
                "strategies": ["all", "dependency", "coverage"]}

    @app.post("/api/analyze", dependencies=secured)
    def analyze(body: AnalyzeRequest) -> dict:
        if body.level == "file":
            return extract_changes(body.repo, body.base, body.head).to_dict()
        return analyze_changes(body.repo, body.base, body.head).to_dict()

    @app.post("/api/graph", dependencies=secured)
    def graph(body: GraphRequest) -> dict:
        return build_graph(body.repo, body.rev, include_members=body.include_members).to_dict()

    @app.post("/api/impact", dependencies=secured)
    def impact(body: ImpactRequest) -> dict:
        return compute_impact(body.repo, body.base, body.head, max_depth=body.max_depth,
                              include_heuristic=not body.confirmed_only).to_dict()

    @app.post("/api/tests", dependencies=secured)
    def tests(body: RevRequest) -> dict:
        return discover_tests(body.repo, body.rev).to_dict()

    @app.post("/api/select", dependencies=secured)
    def select(body: SelectRequest) -> dict:
        coverage = _json_file(body.coverage_map, COVERAGE_MAP_FILE)
        durations = _json_file(body.durations, RESULTS_FILE)
        return select_tests(
            body.repo, body.base, body.head, body.strategy,
            coverage_map=load_coverage_map(coverage) if coverage else None,
            durations=load_results(durations) if durations else None,
            non_java=body.non_java).to_dict()

    @app.post("/api/compare", dependencies=secured)
    def compare(body: CompareRequest) -> dict:
        coverage = _json_file(body.coverage_map, COVERAGE_MAP_FILE)
        return compare_strategies(
            body.repo, body.base, body.head,
            load_results(_json_file(body.ground_truth, RESULTS_FILE)),
            coverage_map=load_coverage_map(coverage) if coverage else None,
            non_java=body.non_java)

    @app.post("/api/risk", dependencies=secured)
    def risk(body: RiskRequest) -> dict:
        # Validation retrains the model, so it is cached per database version.
        from codedna.selection.gate import GateConfig, assess_change, validate
        from codedna.test_history.features import build_dataset
        from codedna.test_history.store import HistoryStore

        db = Path(body.history_db)
        if not db.is_file():
            raise FileNotFoundError(2, "history database not found", str(db))
        key = (str(db.resolve()), db.stat().st_mtime_ns, body.risk_target, body.structural)
        with HistoryStore(db) as store:
            gate = app.state.risk_gates.get(key)
            if gate is None:
                gate = validate(build_dataset(store, body.repo, structural=body.structural),
                                GateConfig(risk_target=body.risk_target))
                app.state.risk_gates = {key: gate}
            return assess_change(store, body.base, body.head, repo_path=body.repo,
                                 structural=body.structural, gate=gate)

    @app.post("/api/run-tests", dependencies=secured)
    def run_tests(body: RunTestsRequest) -> dict:
        if not app.state.allow_build:
            raise HTTPException(status_code=403, detail=(
                "this server was started without --allow-build; running tests is disabled"))
        if not body.allow_build:
            raise HTTPException(status_code=400, detail=(
                "running tests executes project code; send allow_build: true to confirm"))
        run, coverage = run_maven_tests(
            body.repo, body.rev, body.output_dir, allow_build=True,
            per_test_coverage=body.per_test_coverage, maven_command=maven_command,
            timeout=body.timeout)
        return {"results": run.to_dict(),
                "coverage_map": coverage.to_dict() if coverage else None}

    return app


def _hostname(host_header: str) -> str:
    """``127.0.0.1:8765`` -> ``127.0.0.1``; ``[::1]:8765`` -> ``[::1]``."""
    if host_header.startswith("["):
        return host_header.split("]", 1)[0] + "]"
    return host_header.rsplit(":", 1)[0] if host_header.count(":") == 1 else host_header


def _json_file(path: str | None, default_name: str) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    return candidate / default_name if candidate.is_dir() else candidate
