"""Experimental witness contracts on disposable Git/Java fixtures; no downloads."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from threading import Event, Thread

import pytest

from codedna.behavior import find_difference
from codedna.git_analysis.git import run_git
from codedna_java.witness import candidates, _tools

SOURCE = 'package example; public class Fee { public static int fee(int x) { BODY } }'


def versions(repo, before='return x >= 100 ? 1 : 0;', after='return x >= 101 ? 1 : 0;'):
    repo.write('src/main/java/example/Fee.java', SOURCE.replace('BODY', before))
    base=repo.commit('base')
    repo.write('src/main/java/example/Fee.java', SOURCE.replace('BODY', after))
    head=repo.commit('head')
    return base,head


def invoke(repo, shas, output, **options):
    return find_difference(repo.path,*shas,file='src/main/java/example/Fee.java',
        symbol='example.Fee#fee(int)',output_dir=output,allow_build=True,timeout=120,**options)


def test_guidance_prioritizes_edited_boundary_over_many_unchanged_literals():
    prefix = tuple(token for value in range(200) for token in (str(value), ';'))
    before = prefix + ('x', '>=', '9000', '?', '1', ':', '0')
    after = prefix + ('x', '>=', '9001', '?', '1', ':', '0')
    values = candidates(before, after, mode='guided', seed=7, maximum=4)
    assert values[:3] == [9001, 9000, 9002]
    assert len(values) == len(set(values)) == 4


def test_simple_generation_does_not_use_change_literals():
    args = dict(mode='simple', seed=13, maximum=16)
    assert candidates(('9000',), ('9001',), **args) == candidates(('12',), ('13',), **args)


@pytest.mark.parametrize('expectation', [True, {}, {'input': 0, 'expected': 1},
    {'input': None, 'expected': 1, 'requirement': 'rule'},
    {'input': 0, 'expected': 2**63, 'requirement': 'rule'},
    {'input': 0, 'expected': 1, 'requirement': 'bad\nline'}])
def test_bad_expectation_is_refused_before_repository_access(tmp_path, monkeypatch, expectation):
    import codedna.behavior as behavior
    def forbidden(*a, **k): raise AssertionError('must validate before reading repository')
    monkeypatch.setattr(behavior, 'resolve_repository', forbidden)
    with pytest.raises(ValueError, match='expectation'):
        find_difference(tmp_path, 'HEAD', 'HEAD', file='Fee.java', symbol='Fee#fee(int)',
                        output_dir=tmp_path/'out', allow_build=True, expectation=expectation)
    assert not (tmp_path/'out').exists()


@pytest.mark.maven
def test_supplied_expectation_has_confirmed_evidence_and_non_oracle_junit(repo, tmp_path):
    shas = versions(repo, 'return x;', 'return 2*x;')
    supplied = {'input': 17, 'expected': 999, 'requirement': 'INPUT TYPE METHOD: externally supplied rule'}
    result = invoke(repo, shas, tmp_path/'out', max_inputs=4, reduce_budget=2, expectation=supplied)
    assert result['status'] == 'difference', result
    assert result['candidate_inputs'][0] == 17
    assessment = result['expectation_assessment']
    assert assessment['status'] == 'confirmed_at_supplied_input'
    assert assessment['base_satisfies'] is False and assessment['head_satisfies'] is False
    assert assessment['regression_against_supplied_requirement'] is False
    assert result['required_tests_removed'] is False and result['regression_established'] is False
    draft = (tmp_path/'out/CodeDNAWitnessTest.java').read_text()
    assert 'assertEquals(999, example.Fee.fee(17),' in draft
    assert 'INPUT TYPE METHOD: externally supplied rule' in draft
    assert json.loads((tmp_path/'out/SUPPLIED_EXPECTATION.json').read_text()) == supplied
    for name, expected in result['reproducer']['files_sha256'].items():
        assert hashlib.sha256((tmp_path/'out'/name).read_bytes()).hexdigest() == expected


def test_explicit_consent_precedes_repository_access_and_export(tmp_path,monkeypatch):
    import codedna.behavior as behavior
    def forbidden(*args,**kwargs):raise AssertionError('must refuse before inspecting or executing')
    monkeypatch.setattr(behavior,'resolve_repository',forbidden)
    with pytest.raises(ValueError,match='allow-build'):
        find_difference(tmp_path/'missing','HEAD','WORKTREE',file='Fee.java',symbol='Fee#fee(int)',
                        output_dir=tmp_path/'out')
    assert not (tmp_path/'out').exists()


@pytest.mark.parametrize('options',[{'max_inputs':0},{'max_inputs':65},{'max_inputs':True},
    {'seed':-1},{'timeout':121},{'reduce_budget':17},{'generation':'learned'},
    {'file':'../../Fee.java'},{'file':'C:/Fee.java'},{'symbol':''}])
def test_invalid_requests_create_no_export(repo,tmp_path,options):
    shas=versions(repo)
    arguments=dict(file='src/main/java/example/Fee.java',symbol='example.Fee#fee(int)',
                   output_dir=tmp_path/'out',allow_build=True)
    arguments.update(options)
    with pytest.raises(ValueError):find_difference(repo.path,*shas,**arguments)
    assert not (tmp_path/'out').exists()


def test_existing_and_in_repository_exports_are_refused(repo,tmp_path):
    shas=versions(repo);output=tmp_path/'out';output.mkdir();(output/'keep.txt').write_text('keep')
    with pytest.raises(ValueError,match='already exist'):invoke(repo,shas,output)
    assert (output/'keep.txt').read_text()=='keep'
    with pytest.raises(ValueError,match='outside'):invoke(repo,shas,repo.path/'export')
    assert not (repo.path/'export').exists()


def test_plugin_without_optional_capability_is_not_executed(repo,tmp_path,monkeypatch):
    import codedna.behavior as behavior
    shas=versions(repo)
    def forbidden(*args,**kwargs):raise AssertionError('unsupported plugin cannot start a worker')
    monkeypatch.setattr(behavior,'OwnedProcess',forbidden)
    with pytest.raises(ValueError,match='no experimental'):
        invoke(repo,shas,tmp_path/'out',language='python')
    assert not (tmp_path/'out').exists()


def test_candidate_modes_are_bounded_repeatable_and_preserve_int32(repo):
    versions(repo)
    for mode in ['guided','simple']:
        args=dict(mode=mode,seed=7,maximum=64)
        values=candidates(('2147483647','0x80000000'),('101','-','100','1'),**args)
        assert values==candidates(('2147483647','0x80000000'),('101','-','100','1'),**args)
        assert len(values)==len(set(values))==64
        assert all(-(2**31)<=value<=2**31-1 for value in values)
    assert candidates((),('101',),mode='guided',seed=0,maximum=3)==[101,100,102]


@pytest.mark.maven
def test_real_threshold_witness_reproduces_without_codedna_or_maven(repo,tmp_path):
    shas=versions(repo);before=run_git(repo.path,'status','--porcelain')
    output=tmp_path/'guided'
    result=invoke(repo,shas,output,max_inputs=8)
    assert result['status']=='difference',result
    assert result['witness']['input']==100
    assert result['witness']['base']['value']==1 and result['witness']['head']['value']==0
    assert result['regression_established'] is False and result['required_tests_removed'] is False
    assert result['search_inputs']==2 and result['budget']['max_inputs']==8
    for name,digest in result['reproducer']['files_sha256'].items():
        assert hashlib.sha256((output/name).read_bytes()).hexdigest()==digest
    assert json.loads((output/'report.json').read_text(encoding='utf-8'))==result
    javac,java=_tools(repo.path)
    compile=subprocess.run([javac,'-proc:none','ReproduceDifference.java'],cwd=output,
                           capture_output=True,text=True,timeout=30)
    assert compile.returncode==0,compile.stderr
    reproduced=subprocess.run([java,'-cp','.','ReproduceDifference'],cwd=output,
                              capture_output=True,text=True,timeout=30)
    assert reproduced.returncode==0,reproduced.stderr
    assert 'input=100 base=1 head=0' in reproduced.stdout
    assert 'Base is not an oracle' in reproduced.stdout
    head=output/'head/Fee.java';head.write_bytes(head.read_bytes()+b'\n// changed export')
    rejected=subprocess.run([java,'-cp','.','ReproduceDifference'],cwd=output,
                            capture_output=True,text=True,timeout=15)
    assert rejected.returncode!=0 and 'Source fingerprint differs' in rejected.stderr
    simple=invoke(repo,shas,tmp_path/'simple',max_inputs=8,generation='simple')
    assert simple['status']=='no_difference_observed' and simple['search_inputs']==8,simple
    assert not (tmp_path/'simple/base').exists()
    assert run_git(repo.path,'status','--porcelain')==before


@pytest.mark.maven
def test_reduction_retains_a_confirmed_difference_and_no_oracle(repo,tmp_path,capsys):
    from codedna.cli import main
    shas=versions(repo,'return x;','return 2*x;')
    assert main(['witness','--repo',str(repo.path),'--base',shas[0],'--head',shas[1],
        '--file','src/main/java/example/Fee.java','--symbol','example.Fee#fee(int)',
        '--output-dir',str(tmp_path/'out'),'--max-inputs','4','--timeout','120','--allow-build'])==0
    result=json.loads(capsys.readouterr().out)
    assert result['status']=='difference',result
    assert result['original_witness']['input']==2 and result['witness']['input']==1
    assert result['witness']['base']['value']==1 and result['witness']['head']['value']==2
    assert 'no global minimality claim' in result['reduction']
    assert sum(o['phase']=='confirmation' for o in result['observations'])==4


@pytest.mark.maven
def test_comment_only_change_is_finite_no_difference_not_equivalence(repo,tmp_path):
    shas=versions(repo,'return x+1;','/* intended same behavior */ return x+1;')
    result=invoke(repo,shas,tmp_path/'out',max_inputs=5)
    assert result['status']=='no_difference_observed' and result['search_inputs']==5,result
    assert 'equivalence is not established' in result['reason']
    assert not (tmp_path/'out/base').exists()


@pytest.mark.maven
@pytest.mark.parametrize('source',[
    'package example; public class Fee { public int fee(int x) { return x; } }',
    'package example; public class Fee { public static long fee(int x) { return x; } }',
    'package example; public class Fee { public static int fee(long x) { return 0; } }',
    'package example; class Fee { public static int fee(int x) { return x; } }',
    'package example; public class Fee { public static int fee(int x) { return Missing.apply(x); } }'])
def test_unsupported_signatures_and_external_dependencies_do_not_run(repo,tmp_path,source):
    shas=versions(repo);repo.write('src/main/java/example/Fee.java',source);head=repo.commit('unsupported')
    result=invoke(repo,(shas[0],head),tmp_path/'out',max_inputs=1)
    assert result['status']=='unsupported' and result['jvm_runs']==0,result
    assert not (tmp_path/'out/base').exists()


@pytest.mark.maven
def test_missing_jdk_is_actionable_and_not_a_no_difference(repo,tmp_path,monkeypatch):
    shas=versions(repo);monkeypatch.setenv('JAVA_HOME',str(tmp_path/'missing-jdk'))
    result=invoke(repo,shas,tmp_path/'out',max_inputs=1)
    assert result['status']=='unsupported' and 'JDK with javac' in result['reason'],result


@pytest.mark.maven
@pytest.mark.parametrize('body,reason',[
    ('throw new IllegalArgumentException("fixture");','Exception observed'),
    ('while (true) { System.out.println("bounded fixture log"); }','output exceeded')])
def test_exceptions_and_excess_output_are_inconclusive(repo,tmp_path,body,reason):
    shas=versions(repo,body,body+' // same signature\n')
    result=invoke(repo,shas,tmp_path/'out',max_inputs=1)
    assert result['status']=='inconclusive' and reason in result['reason'],result


@pytest.mark.maven
def test_repeated_fresh_jvms_reject_observed_nondeterminism(repo,tmp_path):
    body='''try { java.nio.file.Path p=java.nio.file.Path.of("counter");
      int n=java.nio.file.Files.exists(p)?Integer.parseInt(java.nio.file.Files.readString(p)):0;
      java.nio.file.Files.writeString(p,Integer.toString(n+1)); return n+OFFSET;
      } catch(Exception e) { throw new RuntimeException(e); }'''
    shas=versions(repo,body.replace('OFFSET','0'),body.replace('OFFSET','1'))
    result=invoke(repo,shas,tmp_path/'out',max_inputs=1)
    assert result['status']=='inconclusive' and 'unstable' in result['reason'],result
    assert not (tmp_path/'out/base').exists()


@pytest.mark.maven
@pytest.mark.parametrize('control',['timeout','cancel'])
def test_real_jvm_and_descendant_end_on_timeout_or_ctrl_c(repo,tmp_path,control):
    from test_owned_process import alive
    ready=tmp_path/'ready.txt'
    if os.name=='nt':
        command=[str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'),
                 '-NoProfile','-Command','Start-Sleep -Seconds 120']
    else:
        command=['sleep','120']
    java_args=','.join(json.dumps(s.replace('\\','/')) for s in command)
    body=f'''try {{ Process child=new ProcessBuilder({java_args}).start();
        java.nio.file.Files.writeString(java.nio.file.Path.of({json.dumps(ready.as_posix())}),
          ProcessHandle.current().pid()+","+child.pid());
        while(true) {{ Thread.sleep(100); }}
      }} catch(Exception e) {{ throw new RuntimeException(e); }}'''
    shas=versions(repo,body,body+' // same behavior\n')
    stop=Event()
    def interrupt():
        import _thread
        end=time.monotonic()+20
        while not stop.is_set() and time.monotonic()<end:
            try:
                fields=ready.read_text(encoding='utf-8').strip().split(',')
            except OSError:
                fields=[]
            # Creation can precede the short PID write; interrupt only when
            # both identities are recorded, so the cleanup assertion is stable.
            if len(fields)==2 and all(field.isdigit() for field in fields):
                _thread.interrupt_main();return
            time.sleep(.02)
    thread=Thread(target=interrupt,daemon=True) if control=='cancel' else None
    if thread:thread.start()
    try:
        result=find_difference(repo.path,*shas,file='src/main/java/example/Fee.java',symbol='example.Fee#fee(int)',
            # The cleanup test must reach the long-running JVM/child, not expire
            # during two compilations and startup on a loaded Windows machine.
            # The unchanged per-invocation execution limit still times it out.
            output_dir=tmp_path/'out',allow_build=True,max_inputs=1,timeout=60 if control=='timeout' else 30)
    finally:
        stop.set()
        if thread:thread.join(timeout=2)
    assert result['status']==('cancelled' if control=='cancel' else 'inconclusive'),result
    assert ready.exists(),result
    java_pid,child_pid=map(int,ready.read_text().split(','))
    assert not alive(java_pid) and not alive(child_pid)
    assert not (tmp_path/'out/base').exists()


@pytest.mark.maven
def test_cleanup_uncertainty_blocks_further_execution(repo,tmp_path,monkeypatch):
    import codedna.behavior as behavior
    shas=versions(repo)
    actual=behavior.OwnedProcess
    monkeypatch.setattr(behavior,'_BLOCKED_REASON',None,raising=False)
    class UncertainOwner:
        def __init__(self,*args,**kwargs):
            self.owner=actual(*args,**kwargs);self.process=self.owner.process
        def close(self):
            self.owner.close()
            raise OSError('fixture: confirmation of cleanup failed')
        def __enter__(self):return self
        def __exit__(self,*args):self.close()
    monkeypatch.setattr(behavior,'OwnedProcess',UncertainOwner)
    result=invoke(repo,shas,tmp_path/'first',max_inputs=1,reduce_budget=0)
    assert result['status']=='inconclusive' and result['further_execution_blocked'] is True,result
    def forbidden(*args,**kwargs):raise AssertionError('uncertain cleanup must prevent a new worker')
    monkeypatch.setattr(behavior,'OwnedProcess',forbidden)
    with pytest.raises(RuntimeError,match='cleanup'):
        invoke(repo,shas,tmp_path/'second',max_inputs=1)
    assert not (tmp_path/'second').exists()


@pytest.mark.maven
def test_utf8_source_and_runtime_reproduce_across_default_encodings(repo,tmp_path):
    shas=versions(repo,'return "💡".getBytes().length + x;','return "💡".length() + x;')
    output=tmp_path/'out'
    result=invoke(repo,shas,output,max_inputs=1,reduce_budget=0)
    assert result['status']=='difference',result
    assert result['witness']['base']['value']==4 and result['witness']['head']['value']==2
    assert result['source_encoding']==result['runtime_file_encoding']=='UTF-8'
    javac,java=_tools(repo.path)
    compiled=subprocess.run([javac,'-encoding','UTF-8','-proc:none','ReproduceDifference.java'],
        cwd=output,capture_output=True,text=True,timeout=30)
    assert compiled.returncode==0,compiled.stderr
    reproduced=subprocess.run([java,'-cp','.','ReproduceDifference'],cwd=output,
        capture_output=True,text=True,timeout=30)
    assert reproduced.returncode==0,reproduced.stderr
    assert 'input=0 base=4 head=2' in reproduced.stdout


@pytest.mark.maven
def test_non_utf8_java_source_is_unsupported_before_execution(repo,tmp_path):
    shas=versions(repo)
    repo.write_bytes('src/main/java/example/Fee.java',
        b'package example; public class Fee { public static int fee(int x) { /* \xff */ return x; } }')
    head=repo.commit('non-UTF8 input')
    result=invoke(repo,(shas[0],head),tmp_path/'out',max_inputs=1,reduce_budget=0)
    assert result['status']=='unsupported' and 'UTF-8' in result['reason'],result
    assert result['jvm_runs']==0
