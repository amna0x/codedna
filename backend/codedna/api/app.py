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

Synchronous routes remain compatible. Optional read-only analysis jobs run in
contained private workers with bounded progress, deadlines and cancellation.
Build/test execution retains its separate, explicit consent boundary.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from codedna import __version__
from codedna.git_analysis import CodeDNAGitError, extract_changes
from codedna.impact_analysis import compute_impact
from codedna.models.replay import (
    ReplayError,
    find_replay_sources,
    replay_from_file,
    replay_overview,
)
from codedna.plugins import load_plugins, manager
from codedna.plugins.base import api_compatible
from codedna.plugins.catalogue import CatalogueError
from codedna.plugins.languages import (
    PluginMissingError,
    analyze_changes,
    build_graph,
    discover_tests,
)
from codedna.plugins.languages import run_tests as run_language_tests
from codedna.selection import SelectionError, compare_strategies, select_tests
from codedna.test_mapping.results import (
    COVERAGE_MAP_FILE,
    RESULTS_FILE,
    ReportError,
    load_coverage_map,
    load_results,
)

from codedna.test_history.project import (import_run, list_runs, record_saved_runs,
                                           run_detail)

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
    must_run: list[str] = Field(default_factory=list, description="Extra must-run patterns (D-050).")


class RiskRequest(ChangeRequest):
    history_csv: str | None = None
    risk_target: float = Field(default=.05, gt=0, lt=1)
    must_run: list[str] = Field(default_factory=list, description="Extra must-run patterns (D-050).")
    method: Literal['b10', 'crc'] = Field(default='b10', description="Stopping rule on validated history (D-068).")


class RunSelectionRequest(RiskRequest):
    strategy: Literal['all', 'dependency', 'risk'] = 'risk'
    allow_build: bool = False
    timeout: int = Field(default=1800, ge=1)


class CompareRequest(ChangeRequest):
    ground_truth: str
    coverage_map: str | None = None
    non_java: Literal["retest-all", "ignore"] = "retest-all"


class ReplayRequest(BaseModel):
    path: str = Field(description="Experiment report JSON (history experiment --output).")


class ReplaySourcesRequest(BaseModel):
    folders: list[str] = Field(min_length=1, description="Folders with experiment reports.")


class ReplayOverviewRequest(ReplaySourcesRequest):
    seed: int | None = None


class ImportProjectRunRequest(RepoRequest):
    source: str


class ProjectRunRequest(RepoRequest):
    run_id: str


class PluginInstallRequest(BaseModel):
    plugin: str = Field(pattern=r"^[a-z][a-z0-9-]{1,40}$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$", description="Exact catalogue version.")
    confirm: bool = Field(False, description="Installing runs the plugin's code; must be true.")


class PluginRemoveRequest(BaseModel):
    plugin: str = Field(pattern=r"^[a-z][a-z0-9-]{1,40}$")
    confirm: bool = Field(False, description="Removing changes CodeDNA's environment; must be true.")


class RunTestsRequest(RevRequest):
    output_dir: str
    allow_build: bool = False
    per_test_coverage: bool = False
    timeout: int = Field(default=1800, ge=1)


# --- application ---------------------------------------------------------------------------


def new_token() -> str:
    return secrets.token_urlsafe(32)


def create_app(token: str, *, allow_build: bool = False,
               maven_command: list[str] | None = None,
               python_command: list[str] | None = None) -> FastAPI:
    if len(token) < 16:
        raise ValueError("API token must be at least 16 characters")
    app = FastAPI(title="CodeDNA local API", version=__version__,
                  description="Local API used by the CodeDNA IDE. Loopback only.")
    app.state.allow_build = allow_build

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

    @app.exception_handler(PluginMissingError)
    async def plugin_missing(_request: Request, exc: PluginMissingError):
        return JSONResponse({"error": str(exc)}, status_code=400)

    @app.exception_handler(CatalogueError)
    async def catalogue_error(_request: Request, exc: CatalogueError):
        return JSONResponse({"error": str(exc)}, status_code=400)

    @app.exception_handler(ReplayError)
    async def replay_error(_request: Request, exc: ReplayError):
        return JSONResponse({"error": str(exc)}, status_code=400)

    @app.exception_handler(FileNotFoundError)
    async def missing_file(_request: Request, exc: FileNotFoundError):
        return JSONResponse({"error": f"file not found: {exc.filename}"}, status_code=400)

    @app.get("/api/health")
    def health() -> dict:
        """Unauthenticated liveness check; reveals nothing about repositories."""
        return {"status": "ok", "version": __version__}

    secured = [Depends(require_token)]
    from codedna.api.job_routes import install_job_routes
    install_job_routes(app, secured)


    @app.get("/api/plugins", dependencies=secured)
    def plugins() -> dict:
        return load_plugins().describe()

    @app.get("/api/plugins/catalogue", dependencies=secured)
    def plugin_catalogue() -> dict:
        """The official catalogue (fixed URL, validated) next to what is installed.

        Each version says whether this core can load it (``compatible``), so the
        IDE only displays the core's answer.
        """
        catalogue = manager.fetch_catalogue()
        for plugin in catalogue.get("plugins", []):
            for version in plugin.get("versions", []):
                version["compatible"] = api_compatible(str(version.get("api_version", "")))
        return {"catalogue": catalogue, "installed": load_plugins().describe()}

    @app.post("/api/plugins/install", dependencies=secured)
    def plugin_install(body: PluginInstallRequest) -> dict:
        # The plugin and version come from the request; the URL and checksum only
        # from the official catalogue, fetched here (D-020, D-048).
        result = manager.install(manager.fetch_catalogue(), body.plugin, body.version,
                                 confirmed=body.confirm)
        return {**result, "installed": load_plugins().describe()}

    @app.post("/api/plugins/remove", dependencies=secured)
    def plugin_remove(body: PluginRemoveRequest) -> dict:
        result = manager.remove(manager.fetch_catalogue(), body.plugin, confirmed=body.confirm)
        return {**result, "installed": load_plugins().describe()}

    @app.get("/api/capabilities", dependencies=secured)
    def capabilities() -> dict:
        return {"version": __version__, "allow_build": app.state.allow_build,
                "strategies": ["all", "dependency", "coverage"],
                "analysis_jobs": {"version": 1, "active_limit": 1, "queue_limit": 2,
                                  "deadline_seconds": 300, "timing_version": 1}}

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
            non_java=body.non_java, must_run=body.must_run).to_dict()

    @app.post('/api/risk-select', dependencies=secured)
    def risk_select(body: RiskRequest) -> dict:
        from codedna.selection.live import recommend
        return recommend(body.repo,body.base,body.head,history_csv=body.history_csv,
                         risk_target=body.risk_target,must_run=body.must_run,method=body.method)

    @app.post('/api/run-selection', dependencies=secured)
    def run_selection(body: RunSelectionRequest) -> dict:
        if not app.state.allow_build:
            raise HTTPException(status_code=403,detail='test execution is disabled on this server')
        if not body.allow_build:
            raise HTTPException(status_code=400,detail='running tests executes project code; confirm allow_build')
        from uuid import uuid4
        from codedna.git_analysis.git import resolve_repository
        if body.strategy == 'risk':
            selection = risk_select(body)
        else:
            selection = select_tests(body.repo,body.base,body.head,body.strategy,
                                     must_run=body.must_run).to_dict()
        repo = resolve_repository(body.repo)
        from codedna.test_history.recording import ignore_outputs, record_run
        ignore_outputs(repo)
        output = repo/'.codedna/runs'/uuid4().hex
        run,_ = run_language_tests(repo,selection['head_commit'],output,allow_build=True,
            selected_tests=[t['test'] for t in selection['selected']],
            maven_command=maven_command,python_command=python_command,timeout=body.timeout)
        from codedna.test_mapping.results import save_json
        save_json(selection, output / 'selection.json')
        # Whole-suite runs become project history so the risk gate can turn on (D-053).
        if selection['skipped']:
            recording = {'recorded':False,'reason':'selected runs are not recorded; '
                         'the risk gate needs complete outcomes'}
        else:
            recording = record_run(repo,run,expected_tests=[t['test'] for t in selection['selected']])
        return {'selection':selection,'results':run.to_dict(),'output_dir':str(output),
                'recording':recording}

    @app.post("/api/compare", dependencies=secured)
    def compare(body: CompareRequest) -> dict:
        coverage = _json_file(body.coverage_map, COVERAGE_MAP_FILE)
        return compare_strategies(
            body.repo, body.base, body.head,
            load_results(_json_file(body.ground_truth, RESULTS_FILE)),
            coverage_map=load_coverage_map(coverage) if coverage else None,
            non_java=body.non_java)

    @app.post("/api/project-history", dependencies=secured)
    def project_history_(body: RepoRequest) -> dict:
        """Read-only: saved runs and whether each can be history (D-057)."""
        return list_runs(body.repo)

    @app.post("/api/project-history/record", dependencies=secured)
    def record_saved_runs_(body: RepoRequest) -> dict:
        return record_saved_runs(body.repo)

    @app.post("/api/project-history/import", dependencies=secured)
    def import_project_run_(body: ImportProjectRunRequest) -> dict:
        return import_run(body.repo, body.source)

    @app.post("/api/project-history/run", dependencies=secured)
    def project_run_(body: ProjectRunRequest) -> dict:
        return run_detail(body.repo, body.run_id)

    @app.post("/api/replay", dependencies=secured)
    def replay(body: ReplayRequest) -> dict:
        """Read-only: replays a saved experiment report; runs no model and no code."""
        return replay_from_file(body.path)

    @app.post("/api/replay/sources", dependencies=secured)
    def replay_sources(body: ReplaySourcesRequest) -> dict:
        return find_replay_sources(body.folders)

    @app.post("/api/replay/overview", dependencies=secured)
    def replay_overview_(body: ReplayOverviewRequest) -> dict:
        return replay_overview(body.folders, seed=body.seed)

    @app.post("/api/run-tests", dependencies=secured)
    def run_tests(body: RunTestsRequest) -> dict:
        if not app.state.allow_build:
            raise HTTPException(status_code=403, detail=(
                "this server was started without --allow-build; running tests is disabled"))
        if not body.allow_build:
            raise HTTPException(status_code=400, detail=(
                "running tests executes project code; send allow_build: true to confirm"))
        run, coverage = run_language_tests(
            body.repo, body.rev, body.output_dir, allow_build=True,
            per_test_coverage=body.per_test_coverage, maven_command=maven_command,
            python_command=python_command, timeout=body.timeout)
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
