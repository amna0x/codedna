"""Integrated bounded instance/array evidence on temporary trusted repositories."""
import subprocess

import pytest

from codedna.behavior import find_difference
from codedna_java.witness import _tools


@pytest.mark.maven
def test_instance_array_witness_exports_independently_replayable_requirement(repo, tmp_path):
    revisions = []
    for offset in [0, 1]:
        repo.write('Fee.java', 'public class Fee { int calls; public Fee() {} '
                   'public int[] fee(int x) { return new int[]{x, ++calls+'+str(offset)+'}; } }')
        revisions.append(repo.commit(str(offset)))
    output = tmp_path/'witness'
    result = find_difference(repo.path, *revisions, file='Fee.java', symbol='Fee#fee(int)',
        output_dir=output, allow_build=True, max_inputs=2, reduce_budget=0, timeout=120,
        expectation={'input': 7, 'expected': [7, 1], 'requirement': 'First call returns input and one'})
    assert result['status'] == 'difference', result
    assert result['expectation_assessment']['regression_against_supplied_requirement'] is True
    assert result['witness']['head']['value'] == [7, 2]
    assert 'Constructor code executes' in result['receiver_semantics']
    draft = (output/'CodeDNAWitnessTest.java').read_text()
    assert 'assertArrayEquals(new int[]{7,1}, new Fee().fee(7)' in draft
    javac, java = _tools(repo.path)
    built = subprocess.run([javac, '-encoding', 'UTF-8', '-proc:none', 'ReproduceDifference.java'],
                           cwd=output, capture_output=True, timeout=30)
    assert built.returncode == 0, built.stderr
    replay = subprocess.run([java, '-cp', '.', 'ReproduceDifference'], cwd=output,
                            capture_output=True, timeout=30)
    assert replay.returncode == 0, replay.stderr


@pytest.mark.maven
def test_exception_input_does_not_prevent_later_valid_witness(repo, tmp_path):
    revisions = []
    for offset in [0, 1]:
        repo.write('Fee.java', 'public class Fee { public int fee(int[] xs) {'
                   ' if(xs.length==0) throw new IllegalArgumentException(); return xs.length+'+str(offset)+'; } }')
        revisions.append(repo.commit(str(offset)))
    result = find_difference(repo.path, *revisions, file='Fee.java', symbol='Fee#fee(int[])',
        output_dir=tmp_path/'witness', allow_build=True, max_inputs=2, reduce_budget=0, timeout=120)
    assert result['status'] == 'difference', result
    assert result['non_normal_search_inputs'] == 1
    assert result['observations'][0]['base']['kind'] == 'exception'


@pytest.mark.maven
def test_private_constructor_never_gets_access_override(repo, tmp_path):
    revisions = []
    for offset in [0, 1]:
        repo.write('Fee.java', 'public class Fee { private Fee() {} public int fee(int x) { return x+'+str(offset)+'; } }')
        revisions.append(repo.commit(str(offset)))
    result = find_difference(repo.path, *revisions, file='Fee.java', symbol='Fee#fee(int)',
        output_dir=tmp_path/'witness', allow_build=True, max_inputs=1, timeout=120)
    assert result['status'] == 'unsupported' and result['jvm_runs'] == 0, result
