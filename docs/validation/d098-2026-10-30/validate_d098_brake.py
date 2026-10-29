"""Real frozen MCP + real Maven on explicit disposable, synthetic fixtures."""
import importlib.util
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
from threading import Thread

ROOT=Path('C:/Users/hp/OneDrive/Documents/ChatGPT/codedna/.worktrees/core-evidence')
HERE=Path(__file__).parent
CORE=ROOT/'build/desktop-D098-2026-10-30/core/dist/codedna-core/codedna-core.exe'
MVN='C:/Users/hp/.codex/tools/maven/apache-maven-3.10.0/bin/mvn.cmd'
spec=importlib.util.spec_from_file_location('frozen_demo',ROOT/'scripts/demo_brake_end_to_end.py')
demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
original=demo.demo.Client

class FrozenClient(original):
    def __init__(self,command):
        assert command[:3]==[demo.sys.executable,'-m','codedna'],command
        self.process=subprocess.Popen([str(CORE),*command[3:]],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
        self.next_id=0
    def request(self,method,params=None):
        if method=='tools/call' and params.get('name')=='codedna_check':
            params={**params,'arguments':{**params.get('arguments',{}),'timeout':120}}
        if method=='tools/call':
            params={**params,'arguments':{**params.get('arguments',{}),'profile':True}}
        result=queue.Queue()
        def read():
            try:result.put((True,original.request(self,method,params)))
            except BaseException as exc:result.put((False,exc))
        Thread(target=read,daemon=True).start()
        try:ok,value=result.get(timeout=180)
        except queue.Empty:
            self.process.kill();self.process.wait(timeout=15)
            raise AssertionError('Frozen MCP request exceeded bounded fixture timeout')
        if not ok:raise value
        if method=='tools/call' and 'structuredContent' in value:
            metrics=value['structuredContent']['operation_timings']
            assert metrics['schema_version']==1 and metrics['total_seconds']>0
            expected='includes_test_execution' if params['name']=='codedna_check' else 'analysis_only'
            assert metrics['scope']==expected
        return value

demo.demo.Client=FrozenClient
proof={'scope':'actual frozen MCP and real Maven, isolated synthetic history; engineering evidence only',
       'core':str(CORE),'checks':{}}
os.environ['JAVA_HOME']='C:/Users/hp/.codex/tools/java17/jdk-17.0.20+8'
os.environ['MAVEN_OPTS']='-Dmaven.repo.local=C:/Users/hp/.codex/tools/maven-repository'
os.environ['PATH']=str(Path(os.environ['SystemRoot'])/'System32')+';C:/Program Files/Git/cmd;'+os.environ['JAVA_HOME']+'/bin'
os.environ.pop('PYTHONPATH',None);os.environ.pop('PYTHONHOME',None)
os.environ.pop('CODEDNA_DESKTOP_PLUGIN_SNAPSHOT',None)
with tempfile.TemporaryDirectory(prefix='codedna-frozen-brake-') as directory:
    work=Path(directory).resolve();os.environ['CODEDNA_PLUGIN_HOME']=str(work/'empty-plugin-store')
    basic=work/'cold-history';demo.demo.make_repo(basic)
    client=FrozenClient([demo.sys.executable,'-m','codedna','mcp','--repo',str(basic)])
    try:
        planned=client.request('tools/call',{'name':'codedna_plan_tests','arguments':{}})['structuredContent']
        assert planned['risk']['status']=='unvalidated' and len(planned['must_run'])==2 and not planned['skipped'],planned
        assert 'codedna_check' not in {t['name'] for t in client.request('tools/list')['tools']}
        try:client.request('tools/call',{'name':'codedna_check','arguments':{}})
        except RuntimeError as exc:assert 'unknown tool' in str(exc)
        else:raise AssertionError('Build was exposed without consent')
        assert not (basic/'.codedna').exists()
        proof['checks']['cold_history_requires_full_suite']='passed'
        proof['checks']['build_consent_enforced']='passed'
    finally:client.close()
    target=work/'validated-synthetic-history'
    result=demo.run_demo(target,True,MVN)
    assert result['breaking_plan']['risk']['method']=='crc'
    assert result['breaking_plan']['risk']['status']=='validated_history',result['breaking_plan']
    assert result['breaking_check']['verdict']=='blocked',result['breaking_check']
    assert result['harmless_check']['verdict']=='passed',result['harmless_check']
    proof['checks']['crc_plan_with_synthetic_history']='passed'
    metrics=result['breaking_check']['operation_timings']
    assert metrics['counters']['fit_cache.hit']==1
    assert metrics['stages']['risk.audit']['calls']==1 and 'risk.training' not in metrics['stages']
    assert metrics['stages']['test_execution']['calls']>0
    proof['checks']['frozen_model_reuse_still_runs_fresh_audit_and_real_tests']='passed'
    proof['checks']['frozen_mcp_profile_scope_preserves_build_consent']='passed'
    proof['checks']['real_failing_required_tests_block']='passed'
    proof['checks']['real_passing_required_tests_pass']='passed'
    independent=target/'src/test/java/example/IndependentTest.java'
    independent.write_text(independent.read_text(encoding='utf-8').replace('@Test void','@org.junit.jupiter.api.Disabled @Test void'),
                           encoding='utf-8',newline='\n')
    client=FrozenClient([demo.sys.executable,'-m','codedna','mcp','--repo',str(target),'--allow-build','--mvn',MVN])
    try:
        skipped=client.request('tools/call',{'name':'codedna_check','arguments':{
            'method':'crc','must_run':['example.IndependentTest']}})['structuredContent']
        assert skipped['verdict']=='incomplete' and 'example.IndependentTest' in skipped['skipped_by_build'],skipped
        proof['checks']['real_skipped_required_test_is_incomplete']='passed'
    finally:client.close()
    proof['verdicts']={'breaking':result['breaking_check']['verdict'],
                       'harmless':result['harmless_check']['verdict'],'skipped':skipped['verdict']}
(HERE/'d098-frozen-brake.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))
