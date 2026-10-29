"""Deterministic selection cannot mix repositories between research splits."""
import importlib.util
from pathlib import Path


def test_published_test_audit_does_not_erase_conflicting_results():
    file = Path(__file__).resolve().parents[2]/'scripts/audit_d088_development.py'
    spec = importlib.util.spec_from_file_location('d088_oracles', file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stage = [{'tests': [{'classname': 'Test', 'name': 'case',
                         'results': [{'result': value}]}]}
             for value in ['Failure', 'Passed']]
    assert module.outcomes(stage) == {'Test#case': {'Failure', 'Passed'}}


def test_repository_split_is_order_invariant_and_keeps_earliest_case():
    file = Path(__file__).resolve().parents[2]/'scripts/prepare_d088_manifest.py'
    spec = importlib.util.spec_from_file_location('d088_selection', file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for repo in ['adoble/adr-j']+[f'owner/project{i}' for i in range(20)]:
        for number in [2, 1]:
            rows.append({'repository': repo, 'clone_url': 'https://example.invalid/repo',
                'commit_hash': str(number), 'previous_commit_hash': '0',
                'commit_timestamp': str(number), 'metadata_file': 'input.json',
                'metadata_line': number, 'metadata_sha256': 'hash'})
    cases = module.select(rows)
    assert cases == module.select(list(reversed(rows)))
    assert len({r['repository'] for r in cases}) == 18
    assert sum(r['split'] == 'development' for r in cases) == 6
    assert sum(r['split'] == 'held_out' for r in cases) == 12
    assert all(r['commit_hash'] == '1' for r in cases)
    assert all(r['repository'] != 'adoble/adr-j' for r in cases)
