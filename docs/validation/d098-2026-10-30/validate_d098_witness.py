"""Actual frozen opt-in witness/MCP/JDK reproduction and owned JVM cleanup."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
from threading import Thread
import time

from codedna.git_analysis.git import run_git

ROOT=Path('C:/Users/hp/OneDrive/Documents/ChatGPT/codedna/.worktrees/core-evidence')
HERE=Path(__file__).parent
CORE=ROOT/'build/desktop-D098-2026-10-30/core/dist/codedna-core/codedna-core.exe'
JAVA_HOME=Path('C:/Users/hp/.codex/tools/java17/jdk-17.0.20+8')
spec=importlib.util.spec_from_file_location('d098_owned_fixture',ROOT/'backend/tests/test_owned_process.py')
owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
SOURCE='package example; public class Fee { public static int fee(int x) { BODY } }\n'


def make_repo(path,before,after):
    path.mkdir()
    run_git(path,'init','--quiet')
    file=path/'src/main/java/example/Fee.java';file.parent.mkdir(parents=True)
    shas=[]
    for label,body in [('base',before),('head',after)]:
        file.write_text(SOURCE.replace('BODY',body),encoding='utf-8',newline='\n')
        run_git(path,'add','--','src/main/java/example/Fee.java')
        run_git(path,'-c','user.name=CodeDNA frozen fixture','-c','user.email=fixture@example.invalid',
                '-c','commit.gpgsign=false','commit','--quiet','--allow-empty','-m',label)
        shas.append(run_git(path,'rev-parse','HEAD').strip())
    return shas


class Client:
    def __init__(self,repo,log,moonshot=False):
        command=[str(CORE),'mcp','--repo',str(repo),'--allow-build']
        if moonshot:command.append('--moonshot')
        self.errors=log.open('wb')
        self.process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=self.errors,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
        self.counter=0
    def request(self,method,params=None):
        self.counter+=1
        self.process.stdin.write(json.dumps({'jsonrpc':'2.0','id':self.counter,'method':method,
            'params':params or {}})+'\n');self.process.stdin.flush()
        output=queue.Queue()
        def read():
            try:output.put((True,self.process.stdout.readline()))
            except BaseException as exc:output.put((False,exc))
        Thread(target=read,daemon=True).start()
        try:ok,value=output.get(timeout=150)
        except queue.Empty:
            self.process.kill();self.process.wait(timeout=15)
            raise AssertionError('Frozen MCP exceeded bounded fixture timeout')
        if not ok:raise value
        assert value,'frozen MCP exited without response'
        answer=json.loads(value)
        return answer
    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:self.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.process.kill();self.process.wait(timeout=15)
        self.process.stdout.close();self.errors.close()


def cli(repo,shas,export,timeout):
    return [str(CORE),'witness','--repo',str(repo),'--base',shas[0],'--head',shas[1],
        '--file','src/main/java/example/Fee.java','--symbol','example.Fee#fee(int)',
        '--output-dir',str(export),'--max-inputs','1','--reduce-budget','0','--timeout',str(timeout),
        '--allow-build']


def ready_pids(path):
    try:fields=path.read_text(encoding='utf-8').strip().split(',')
    except OSError:return None
    return list(map(int,fields)) if len(fields)==2 and all(f.isdigit() for f in fields) else None


def assert_ended(pids):
    end=time.monotonic()+10
    while any(owned.alive(pid) for pid in pids) and time.monotonic()<end:time.sleep(.05)
    assert not any(owned.alive(pid) for pid in pids),pids


proof={'scope':'actual frozen D098 executable; isolated synthetic Java, not independent accuracy/clean-PC evidence',
       'core':str(CORE),'core_sha256':hashlib.sha256(CORE.read_bytes()).hexdigest(),'checks':{}}
os.environ['JAVA_HOME']=str(JAVA_HOME)
os.environ['PATH']=str(Path(os.environ['SystemRoot'])/'System32')+';C:/Program Files/Git/cmd;'+str(JAVA_HOME/'bin')
for name in ['PYTHONPATH','PYTHONHOME','CODEDNA_DESKTOP_PLUGIN_SNAPSHOT']:
    os.environ.pop(name,None)
with tempfile.TemporaryDirectory(prefix='codedna-frozen-witness-') as directory:
    work=Path(directory);repo=work/'unicode'
    os.environ['CODEDNA_PLUGIN_HOME']=str(work/'isolated-plugins')
    shas=make_repo(repo,'return "💡".getBytes().length+x;','return "💡".length()+x;')
    before=run_git(repo,'status','--porcelain')
    denied=subprocess.run([str(CORE),'mcp','--repo',str(repo),'--moonshot'],input='',
        text=True,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
    assert denied.returncode!=0 and 'allow-build' in denied.stderr
    proof['checks']['moonshot_without_execution_consent_refused']='passed'
    client=Client(repo,work/'default.log')
    try:
        tools=client.request('tools/list')['result']['tools']
        assert [t['name'] for t in tools]==['codedna_plan_tests','codedna_impact','codedna_check']
        refused=client.request('tools/call',{'name':'codedna_find_witness','arguments':{}})
        assert 'error' in refused
        proof['checks']['default_mcp_tools_unchanged']='passed'
    finally:client.close()
    export=work/'export';client=Client(repo,work/'enabled.log',moonshot=True)
    try:
        tools=client.request('tools/list')['result']['tools']
        assert 'codedna_find_witness' in [t['name'] for t in tools]
        response=client.request('tools/call',{'name':'codedna_find_witness','arguments':{
            'base':shas[0],'head':shas[1],'file':'src/main/java/example/Fee.java',
            'symbol':'example.Fee#fee(int)','output_dir':str(export),'max_inputs':1,
            'reduce_budget':0,'timeout':120,'profile':True}})['result']
        assert response['isError'] is False,response
        result=response['structuredContent'];assert result['status']=='difference',result
        assert result['witness']['input']==0 and result['witness']['base']['value']==4 and result['witness']['head']['value']==2
        assert result['source_encoding']==result['runtime_file_encoding']=='UTF-8'
        assert result['regression_established'] is False and result['required_tests_removed'] is False
        assert result['operation_timings']['scope']=='includes_project_execution'
        proof['checks']['opt_in_frozen_mcp_executes_contained_witness']='passed'
        proof['checks']['frozen_unicode_observations_use_declared_utf8']='passed'
        proof['checks']['witness_is_not_a_regression_or_skip_risk_verdict']='passed'
    finally:client.close()
    for name,digest in result['reproducer']['files_sha256'].items():
        assert hashlib.sha256((export/name).read_bytes()).hexdigest()==digest
    compiled=subprocess.run([str(JAVA_HOME/'bin/javac.exe'),'-encoding','UTF-8','-proc:none','ReproduceDifference.java'],
        cwd=export,text=True,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
    assert compiled.returncode==0,compiled.stderr
    reproduced=subprocess.run([str(JAVA_HOME/'bin/java.exe'),'-cp','.','ReproduceDifference'],
        cwd=export,text=True,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
    assert reproduced.returncode==0 and 'input=0 base=4 head=2' in reproduced.stdout,reproduced.stderr
    proof['checks']['independent_jdk_only_reproducer_matches_frozen_pair']='passed'
    assert run_git(repo,'status','--porcelain')==before
    proof['checks']['original_repository_preserved']='passed'
    for control in ['timeout','parent-kill']:
        ready=work/(control+'-pids.txt')
        shell=str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe').replace('\\','/')
        body=f'''try {{ Process child=new ProcessBuilder({json.dumps(shell)},"-NoProfile","-Command","Start-Sleep -Seconds 120").start();
            java.nio.file.Files.writeString(java.nio.file.Path.of({json.dumps(ready.as_posix())}),ProcessHandle.current().pid()+","+child.pid());
            while(true) {{ Thread.sleep(100); }} }} catch(Exception ex) {{ throw new RuntimeException(ex); }}'''
        path=work/control;ids=make_repo(path,body,body+' // fixture\n')
        process=subprocess.Popen(cli(path,ids,work/(control+'-export'),12 if control=='timeout' else 120),
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            if control=='parent-kill':
                end=time.monotonic()+30;pids=None
                while not pids:
                    pids=ready_pids(ready)
                    if pids:break
                    assert process.poll() is None,'frozen command exited before ready'
                    assert time.monotonic()<end,'frozen child readiness timeout'
                    time.sleep(.02)
                assert all(owned.alive(pid) for pid in pids)
                process.kill()
            stdout,stderr=process.communicate(timeout=45)
            pids=ready_pids(ready);assert pids,(stdout,stderr)
            assert_ended(pids)
            if control=='timeout':
                report=json.loads(stdout)
                assert report['status']=='inconclusive' and process.returncode!=0,report
            proof['checks'][('frozen_timeout_stops_jvm_and_descendant' if control=='timeout'
                             else 'terminating_frozen_parent_stops_jvm_and_descendant')]='passed'
        finally:
            if process.poll() is None:process.kill();process.wait(timeout=15)
            process.stdout.close();process.stderr.close()
(HERE/'d098-frozen-witness.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))
