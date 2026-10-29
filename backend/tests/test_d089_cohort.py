"""Outcome-blind cohort selection and actual Git ancestry, without network."""
import importlib.util
import io
from pathlib import Path
import zipfile

import pytest

from codedna.git_analysis.git import run_git


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[2]/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_candidate_split_does_not_leak_later_reruns():
    rows = [{'project': 'activemq', 'pr_base_branch': 'main', 'pr_name': str(i),
        'build_head_sha': str(i), 'build_id': '1', 'build_timestamp': str(i), 'stage_id': 'single'}
        for i in range(200)]
    rows.append({**rows[0], 'build_id': '99', 'build_timestamp': '999'})
    choose = load('prepare_d089_brake_cohort').choose
    builds = choose(rows)
    assert builds == choose(list(reversed(rows)))
    assert len(builds) == 200
    assert builds[0]['excluded_later_rerun_rows'] == 1
    assert builds[0]['jobs'][0]['build_id'] == '1'
    assert [sum(b['split']==s for b in builds) for s in ['train','audit','evaluation']] == [120,40,40]


def test_sibling_branches_are_not_mistaken_for_ancestors(repo):
    repo.write('a', 'base')
    base = repo.commit('base')
    run_git(repo.path, 'checkout', '-b', 'left')
    repo.write('a', 'left')
    left = repo.commit('left')
    run_git(repo.path, 'checkout', '--detach', base)
    run_git(repo.path, 'checkout', '-b', 'right')
    repo.write('a', 'right')
    right = repo.commit('right')
    ancestors = load('audit_d089_ancestry').ancestor_sets(repo.path, [left, right])
    assert base in ancestors[left] and base in ancestors[right]
    assert left not in ancestors[right] and right not in ancestors[left]


@pytest.mark.parametrize('body', ['A,-1,0', 'A,nan,0', 'A,1,0\nA,2,1'])
def test_inventory_rejects_invalid_durations_and_duplicate_classes(body):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('test_class.csv', 'testclass,duration,outcome\n'+body+'\n')
    with pytest.raises(ValueError):
        load('audit_d089_inventories').inspect(stream.getvalue())
