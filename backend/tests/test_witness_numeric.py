"""Bounded numeric-domain regressions for D087; no external datasets."""
import subprocess
import pytest
from codedna.behavior import find_difference
from codedna_java.witness import _tools
from codedna_java.witness_inputs import encode,java_arguments,reductions,complexity
from codedna_java.witness import _smaller, candidates, _literals


def test_long_literal_guidance_preserves_java_signed_width():
    assert _literals(['0xffffffffffffffffL'], 64) == [-1]
    assert _literals(['0xffffffff'], 64) == [-1]
    values = candidates(('9000000000L',), ('9000000001L',),
                        mode='guided', seed=7, maximum=4, bits=64)
    assert 9000000001 in values
    assert all(-(2**63) <= value < 2**63 for value in values)


def test_array_shrinking_preserves_declared_argument_arity():
    assert [] in reductions([0, 0], _smaller, ['int...'])
    assert complexity([]) < complexity([0])
    paired = reductions([[0, 0], 3], _smaller, ['int[]', 'long'])
    assert [[], 3] in paired
    assert all(len(value) == 2 for value in paired)

def test_numeric_transport_rejects_overflow_and_bounds_arrays():
    assert encode(['long'],2**63-1)==str(2**63-1)
    assert encode(['int...'],[1,-2])=='1,-2'
    assert java_arguments(['long'], -(2**63))=='-9223372036854775808L'
    for types,value in [(['long'],2**63),(['int[]'],[0]*9),(['int[]'],[True])]:
        with pytest.raises(ValueError):encode(types,value)

@pytest.mark.maven
@pytest.mark.parametrize('signature,kind,base,head',[
    ('long x','long','return x;','return x+1;'),
    ('int... x','int...','return x.length;','return x.length+1;')])
def test_numeric_witness_and_standalone_replay(repo,tmp_path,signature,kind,base,head):
    ids=[]
    result_type='long' if kind=='long' else 'int'
    for label,body in [('base',base),('head',head)]:
        repo.write('Fee.java','public class Fee { public static '+result_type+' fee('+signature+') { '+body+' } }')
        ids.append(repo.commit(label))
    out=tmp_path/'out'
    expectation = ({'input': 2**63-1, 'expected': 2**63-1,
                    'requirement': 'Preserve the signed long input'} if kind == 'long' else None)
    result=find_difference(repo.path,*ids,file='Fee.java',symbol='Fee#fee('+kind+')',output_dir=out,
        allow_build=True,max_inputs=2,reduce_budget=0,timeout=120,expectation=expectation)
    assert result['status']=='difference',result
    if expectation:
        assert result['witness']['head']['value'] == -(2**63)
        assert result['expectation_assessment']['regression_against_supplied_requirement'] is True
    javac,java=_tools(repo.path)
    compiled=subprocess.run([javac,'-encoding','UTF-8','-proc:none','ReproduceDifference.java'],cwd=out,capture_output=True,timeout=30)
    assert compiled.returncode==0,compiled.stderr
    replay=subprocess.run([java,'-cp','.','ReproduceDifference'],cwd=out,capture_output=True,timeout=30)
    assert replay.returncode==0,replay.stderr
