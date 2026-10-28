"""Offline runner guards, using temporary Git repositories and databases."""
import importlib.util
import json
from pathlib import Path
import sqlite3

import pytest


@pytest.fixture
def runner(repo):
    path = Path(__file__).resolve().parents[2] / 'scripts/run_partial_feedback_pilot.py'
    spec = importlib.util.spec_from_file_location('partial_feedback_runner', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    repo.write('readme.txt', 'temporary offline history')
    repo.commit('fixture')
    return module


def test_mapping_requires_complete_exact_nonduplicated_universe(runner):
    report = {'selected': [{'test': 'a'}], 'skipped': ['b'], 'total_tests': 2,
              'policy': {'pinned': ['a']}}
    runner.check_mapping(report, {'a', 'b'})
    for modified in [dict(report, skipped=[]), dict(report, skipped=['a', 'b']),
                     dict(report, skipped=['b', 'b']), dict(report, total_tests=3),
                     dict(report, policy={'pinned': ['foreign']})]:
        with pytest.raises(ValueError):
            runner.check_mapping(modified, {'a', 'b'})
    with pytest.raises(ValueError, match='reference_not_discovered'):
        runner.check_mapping(report, {'a', 'missing'})


def test_checkpoint_hash_and_configuration_are_both_required(runner, tmp_path):
    path = tmp_path / 'plan.json'
    binding = {'source': 'one'}
    payload = {'selected': ['a']}
    assert runner.checked_cache(path, binding) is None
    runner.write_json(path, {'binding': binding, 'payload': payload,
                             'payload_sha256': runner.digest(payload)})
    assert runner.checked_cache(path, binding) == payload
    with pytest.raises(ValueError, match='incompatible'):
        runner.checked_cache(path, {'source': 'two'})
    value = json.loads(path.read_text())
    value['payload']['selected'] = ['b']
    runner.write_json(path, value)
    with pytest.raises(ValueError, match='damaged'):
        runner.checked_cache(path, binding)


def test_history_reader_preserves_database_and_rejects_missing_base(runner, repo, tmp_path):
    base = repo.git('rev-parse', 'HEAD')
    repo.write('readme.txt', 'next')
    head = repo.commit('next')
    database = tmp_path / 'history.db'
    with sqlite3.connect(database) as connection:
        connection.executescript('CREATE TABLE meta(key TEXT,value TEXT);'
            'CREATE TABLE commits(sha TEXT,parent TEXT);'
            'CREATE TABLE changed_files(sha TEXT,path TEXT);')
        connection.execute('INSERT INTO meta VALUES (?,?)', ('repository', str(repo.path)))
        connection.execute('INSERT INTO commits VALUES (?,?)', (head, base))
        connection.execute('INSERT INTO changed_files VALUES (?,?)', (head, 'readme.txt'))
    original = database.read_bytes()
    location, bases, paths = runner.read_history(database, [head])
    assert location == repo.path
    assert bases == {head: base}
    assert paths == {head: ('readme.txt',)}
    assert database.read_bytes() == original
    with pytest.raises(ValueError, match='lacks recorded push base'):
        runner.read_history(database, [base])
    assert database.read_bytes() == original
