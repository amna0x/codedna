"""Private stdin/stdout worker protocol. Wait for containment before any work."""
from __future__ import annotations

import json
import sys

MAX_MESSAGE = 8 * 1024 * 1024


def execute(operation: str, payload: dict) -> dict:
    """Use the same request schemas, core functions and defaults as sync routes."""
    from codedna.api.app import (AnalyzeRequest, ImpactRequest, RevRequest,
                                 RiskRequest, SelectRequest, _json_file)
    from codedna.git_analysis import extract_changes
    from codedna.impact_analysis import compute_impact
    from codedna.plugins.languages import analyze_changes, discover_tests
    from codedna.selection import select_tests
    from codedna.selection.live import recommend
    from codedna.test_mapping.results import (COVERAGE_MAP_FILE, RESULTS_FILE,
                                             load_coverage_map, load_results)

    if operation == 'tests':
        body = RevRequest.model_validate(payload)
        return discover_tests(body.repo, body.rev).to_dict()
    if operation == 'analyze':
        body = AnalyzeRequest.model_validate(payload)
        if body.level == 'file':
            return extract_changes(body.repo, body.base, body.head).to_dict()
        return analyze_changes(body.repo, body.base, body.head).to_dict()
    if operation == 'impact':
        body = ImpactRequest.model_validate(payload)
        return compute_impact(body.repo, body.base, body.head, max_depth=body.max_depth,
                              include_heuristic=not body.confirmed_only).to_dict()
    if operation == 'select':
        body = SelectRequest.model_validate(payload)
        coverage = _json_file(body.coverage_map, COVERAGE_MAP_FILE)
        durations = _json_file(body.durations, RESULTS_FILE)
        return select_tests(body.repo, body.base, body.head, body.strategy,
                            coverage_map=load_coverage_map(coverage) if coverage else None,
                            durations=load_results(durations) if durations else None,
                            non_java=body.non_java, must_run=body.must_run).to_dict()
    if operation == 'risk-select':
        body = RiskRequest.model_validate(payload)
        return recommend(body.repo, body.base, body.head, history_csv=body.history_csv,
                         risk_target=body.risk_target, must_run=body.must_run, method=body.method)
    raise ValueError('unsupported analysis operation')


def main() -> int:
    # No plugin activation, project inspection or child process before this read.
    line = sys.stdin.buffer.readline(MAX_MESSAGE + 1)
    output = sys.stdout

    def emit(kind, value):
        message = json.dumps({'kind': kind, 'value': value}, ensure_ascii=True,
                             allow_nan=False, separators=(',', ':'))
        if len(message) > MAX_MESSAGE:
            raise ValueError('analysis result exceeds the worker message limit')
        output.write(message + '\n'); output.flush()

    timings = None
    metrics_emitted = False
    try:
        if len(line) > MAX_MESSAGE:
            raise ValueError('analysis request exceeds the worker message limit')
        request = json.loads(line)
        from contextlib import redirect_stdout
        from codedna.performance import capture_timings
        with capture_timings(request.get('profile', False)) as timings:
            with redirect_stdout(sys.stderr):
                emit('stage', 'loading analysis core')
                if getattr(sys, 'frozen', False):
                    from codedna.plugins import desktop_store
                    desktop_store.pin_worker_snapshot(request['plugins'])
                stages = {'tests': 'discovering tests', 'analyze': 'analysing changes',
                          'impact': 'analysing impact', 'select': 'selecting tests',
                          'risk-select': 'checking history and selecting tests'}
                operation = request['operation']
                if operation not in stages:
                    raise ValueError('unsupported analysis operation')
                emit('stage', stages[operation])
                result = execute(operation, request['payload'])
        if timings is not None:
            emit('metrics', timings.to_dict())
            metrics_emitted = True
        emit('result', result)
        return 0
    except Exception as exc:
        if timings is not None and not metrics_emitted:
            emit('metrics', timings.to_dict())
        emit('error', str(exc)[:1000] or type(exc).__name__)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
