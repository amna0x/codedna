"""Typed-input transport and paired-budget allocation, plus actual JVM replay."""
import hashlib
import json
import subprocess

import pytest

from codedna.behavior import find_difference
from codedna_java.witness import _smaller, _tools, candidates
from codedna_java.witness_inputs import encode, generate, java_arguments, reductions, complexity


@pytest.mark.parametrize('types,value', [(['int'], True), (['boolean'], 1),
    (['String'], 'x'*129), (['String'], '\ud800'), (['int','String'], [1]),
    (['int'], [1,2])])
def test_bad_typed_inputs_never_become_command_arguments(types, value):
    with pytest.raises((ValueError, UnicodeError)):
        encode(types, value)


@pytest.mark.parametrize('helpers', [['../Helper.java'], ['/Helper.java'], ['C:/Helper.java'],
    ['Helper.java']*2, ['One.java','Two.java','Three.java','Four.java'], ['file.txt']])
def test_helper_paths_are_rejected_before_repository_access(tmp_path,monkeypatch,helpers):
    import codedna.behavior as behavior
    def forbidden(*args,**kwargs): raise AssertionError('invalid paths must fail before repository access')
    monkeypatch.setattr(behavior,'resolve_repository',forbidden)
    with pytest.raises(ValueError,match='support_files'):
        find_difference(tmp_path,'HEAD','HEAD',file='Fee.java',symbol='Fee#fee(int)',
            output_dir=tmp_path/'out',support_files=helpers,allow_build=True)
    assert not (tmp_path/'out').exists()


def test_string_transport_and_draft_literal_are_unambiguous():
    assert encode(['String'], 'é:😀') == 'w6k68J+YgA=='
    assert java_arguments(['int','String'], [1, '"\n']) == '1, "\\\"\\n"'
    assert encode(['boolean','int'], [False, -1]) == 'false:-1'


def test_two_argument_budget_explores_both_coordinates():
    values = generate(['int','boolean'], (), (), mode='simple', seed=7, maximum=8, int_candidates=candidates)
    assert values[:3] == [[0,False],[0,True],[1,False]]
    assert len(values) == 8
    assert values == generate(['int','boolean'], (), (), mode='simple', seed=7, maximum=8, int_candidates=candidates)


def test_structured_reduction_never_increases_complexity():
    original = [100, 'abcdef']
    smaller = reductions(original, _smaller)
    assert [0,'abcdef'] in smaller and [100,''] in smaller
    assert all(complexity(v) < complexity(original) for v in smaller)


@pytest.mark.maven
@pytest.mark.parametrize('signature,before,after,value,expected', [
    ('boolean x','return x ? 1 : 0;', 'return x ? 2 : 0;', True,1),
    ('String x','return x.length();','return x.getBytes(java.nio.charset.StandardCharsets.UTF_8).length;','é😀',3),
    ('int x, String y','return x+y.length();','return x-y.length();',[10,'abc'],13),
])
def test_typed_witness_independently_reproduces_with_supplied_requirement(repo,tmp_path,signature,before,after,value,expected):
    types=','.join(part.strip().split()[0] for part in signature.split(','))
    ids=[]
    for label,body in [('base',before),('head',after)]:
        repo.write('src/main/java/example/Fee.java',
            'package example; public class Fee { public static int fee('+signature+') { '+body+' } }')
        ids.append(repo.commit(label))
    output=tmp_path/'witness'
    result=find_difference(repo.path,*ids,file='src/main/java/example/Fee.java',
        symbol='example.Fee#fee('+types+')',output_dir=output,allow_build=True,
        max_inputs=4,reduce_budget=2,timeout=120,
        expectation={'input':value,'expected':expected,'requirement':'Explicit fixture rule'})
    assert result['status']=='difference',result
    assert result['expectation_assessment']['regression_against_supplied_requirement'] is True,result
    javac,java=_tools(repo.path)
    compiled=subprocess.run([javac,'-encoding','UTF-8','-proc:none','ReproduceDifference.java'],cwd=output,
        capture_output=True,text=True,timeout=30)
    assert compiled.returncode==0,compiled.stderr
    replay=subprocess.run([java,'-Dfile.encoding=UTF-8','-cp','.','ReproduceDifference'],cwd=output,
        capture_output=True,text=True,timeout=30)
    assert replay.returncode==0,replay.stderr
    assert 'Recorded behavioral difference reproduced' in replay.stdout
    assert 'assertEquals('+str(expected)+', example.Fee.fee('+java_arguments(types.split(','),value)+'),' in (output/'CodeDNAWitnessTest.java').read_text()
    for name,digest in result['reproducer']['files_sha256'].items():
        assert hashlib.sha256((output/name).read_bytes()).hexdigest()==digest


@pytest.mark.maven
def test_template_markers_inside_input_remain_literal_and_reproduce(repo,tmp_path):
    ids=[]
    for label,body in [('base','return x.length();'),('head','return x.length()+1;')]:
        repo.write('src/main/java/example/Fee.java',
            'package example; public class Fee { public static int fee(String x) { '+body+' } }')
        ids.append(repo.commit(label))
    value='@@TYPE@@ "\n'
    output=tmp_path/'literal'
    result=find_difference(repo.path,*ids,file='src/main/java/example/Fee.java',symbol='example.Fee#fee(String)',
        output_dir=output,allow_build=True,max_inputs=1,reduce_budget=0,timeout=120,
        expectation={'input':value,'expected':len(value),'requirement':'Keep INPUT and @@TYPE@@ literal'})
    assert result['status']=='difference',result
    javac,java=_tools(repo.path)
    compiled=subprocess.run([javac,'-encoding','UTF-8','-proc:none','ReproduceDifference.java'],cwd=output,
        capture_output=True,text=True,timeout=30)
    assert compiled.returncode==0,compiled.stderr
    replay=subprocess.run([java,'-cp','.','ReproduceDifference'],cwd=output,capture_output=True,text=True,timeout=30)
    assert replay.returncode==0,replay.stderr
    assert '@@TYPE@@' in replay.stdout


@pytest.mark.maven
def test_explicit_helper_sources_reproduce_and_refuse_tampering(repo,tmp_path):
    helper='src/main/java/example/Helper.java'
    ids=[]
    for label,extra in [('base',1),('head',2)]:
        repo.write('src/main/java/example/Fee.java',
            'package example; public class Fee { public static int fee(int x) { return Helper.apply(x); } }')
        repo.write(helper,'package example; public class Helper { public static int apply(int x) { return x+'+str(extra)+'; } }')
        ids.append(repo.commit(label))
    output=tmp_path/'helpers'
    result=find_difference(repo.path,*ids,file='src/main/java/example/Fee.java',symbol='example.Fee#fee(int)',
        support_files=[helper],output_dir=output,allow_build=True,max_inputs=2,reduce_budget=0,timeout=120)
    assert result['status']=='difference',result
    javac,java=_tools(repo.path)
    compiled=subprocess.run([javac,'-encoding','UTF-8','-proc:none','ReproduceDifference.java'],cwd=output,capture_output=True,text=True,timeout=30)
    assert compiled.returncode==0,compiled.stderr
    replay=subprocess.run([java,'-cp','.','ReproduceDifference'],cwd=output,capture_output=True,text=True,timeout=30)
    assert replay.returncode==0,replay.stderr
    (output/'head/support'/helper).write_text('changed')
    rejected=subprocess.run([java,'-cp','.','ReproduceDifference'],cwd=output,capture_output=True,text=True,timeout=30)
    assert rejected.returncode!=0 and 'Source fingerprint differs' in rejected.stderr
