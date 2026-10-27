"""Authenticated read-only job routes. Build/history/plugin mutation stay separate."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from codedna.api.analysis_jobs import AnalysisJobs, JobCapacityError


def install_job_routes(app, secured):
    from codedna.api.app import AnalyzeRequest, ImpactRequest, RevRequest, RiskRequest, SelectRequest

    jobs = AnalysisJobs()
    app.state.analysis_jobs = jobs
    previous_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        async with previous_lifespan(application):
            try:
                yield
            finally:
                await run_in_threadpool(jobs.close)
    app.router.lifespan_context = lifespan

    def submit(operation, body):
        try:
            payload = body.model_dump()
            # Workers start in a trusted core directory, so anchor API-relative
            # paths here. Preserve empty optional paths and existing defaults.
            for name in ('repo', 'history_csv', 'coverage_map', 'durations'):
                value = payload.get(name)
                if isinstance(value, str) and (name == 'repo' or value):
                    payload[name] = str(Path(value).absolute())
            return jobs.submit(operation, payload)
        except JobCapacityError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post('/api/analysis-jobs/tests', dependencies=secured, status_code=202)
    def tests(body: RevRequest):
        return submit('tests', body)

    @app.post('/api/analysis-jobs/analyze', dependencies=secured, status_code=202)
    def analyze(body: AnalyzeRequest):
        return submit('analyze', body)

    @app.post('/api/analysis-jobs/impact', dependencies=secured, status_code=202)
    def impact(body: ImpactRequest):
        return submit('impact', body)

    @app.post('/api/analysis-jobs/select', dependencies=secured, status_code=202)
    def select(body: SelectRequest):
        return submit('select', body)

    @app.post('/api/analysis-jobs/risk-select', dependencies=secured, status_code=202)
    def risk_select(body: RiskRequest):
        return submit('risk-select', body)

    @app.get('/api/analysis-jobs/{job_id}', dependencies=secured)
    def status(job_id: str):
        try:
            return jobs.get(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='analysis operation not found or expired') from exc

    @app.post('/api/analysis-jobs/{job_id}/cancel', dependencies=secured)
    def cancel(job_id: str):
        try:
            return jobs.cancel(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='analysis operation not found or expired') from exc

    return jobs
