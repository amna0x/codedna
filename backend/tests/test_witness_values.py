"""Result bounds and fresh-receiver JVM evidence for the development extension."""
import subprocess

import pytest

from codedna_java.witness import HARNESS, _tools
from codedna_java.witness_values import normal_value, canonical, instance_array_probe


@pytest.mark.parametrize('value', ['true', 'null', '1.5', '[true]', '[2147483648]',
                                  str(2**63), '['+','.join(['0']*129)+']'])
def test_normal_results_are_bounded_and_not_coerced(value):
    with pytest.raises(ValueError):
        normal_value(value)


def test_normal_array_canonicalization():
    assert normal_value('[1, -2]') == [1, -2]
    assert canonical([1, -2]) == '[1,-2]'
    assert normal_value(str(-(2**63))) == -(2**63)


@pytest.mark.maven
def test_probe_uses_a_fresh_public_receiver_and_array_result(repo, tmp_path):
    source = 'public class ProbeCase { int calls; public int[] value(int x) { return new int[]{x, ++calls}; } }'
    repo.write('ProbeCase.java', source)
    repo.commit('public instance fixture')
    folder = tmp_path/'probe'
    folder.mkdir()
    (folder/'ProbeCase.java').write_text(source)
    (folder/'CodeDNABehaviorProbe.java').write_text(instance_array_probe(HARNESS))
    javac, java = _tools(repo.path)
    result = subprocess.run([javac, '-proc:none', 'ProbeCase.java', 'CodeDNABehaviorProbe.java'],
                            cwd=folder, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    for _ in range(2):
        result = subprocess.run([java, '-cp', '.', 'CodeDNABehaviorProbe', 'ProbeCase',
                                 'value', '7', 'TOKEN:', 'int'],
                                cwd=folder, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == 'TOKEN:value:[7,1]'
