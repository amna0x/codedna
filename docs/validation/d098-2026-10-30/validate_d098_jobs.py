"""Actual frozen API/worker cancellation and plugin activation, offline fixtures."""
import base64
import csv
import ctypes
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import time
import urllib.request
import zipfile

from codedna.git_analysis.git import run_git
from codedna.plugins import desktop_store
from codedna.plugins.catalogue import OFFICIAL_RELEASES, PluginVersion

ROOT=Path('C:/Users/hp/OneDrive/Documents/ChatGPT/codedna/.worktrees/core-evidence')
HERE=Path(__file__).parent
CORE=ROOT/'build/desktop-D098-2026-10-30/core/dist/codedna-core/codedna-core.exe'
POWERSHELL=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
spec=importlib.util.spec_from_file_location('owned_fixture',ROOT/'backend/tests/test_owned_process.py')
owned_fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned_fixture)

PLUGIN='''import json, os, subprocess, time
from pathlib import Path
from types import SimpleNamespace
class Probe:
    name='slow-probe'
    display_name='Trusted frozen lifecycle test fixture'
    version=VERSION
    api_version='1.1'
    file_suffixes=('.slowprobe',)
    def handles(self, path): return path.endswith('.slowprobe')
    def parse(self, source): return None
    def build_graph(self, *args, **kwargs): return None
    def run_tests(self, *args, **kwargs): raise RuntimeError('fixture never runs project tests')
    def discover_tests(self, repo, commit):
        config=json.loads(Path(os.environ['CODEDNA_FROZEN_LIFECYCLE_FIXTURE']).read_text())
        if config['slow']:
            shell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
            child=subprocess.Popen([str(shell),'-NoProfile','-Command','Start-Sleep -Seconds 120'],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
            Path(config['ready']).write_text(json.dumps({'worker':os.getpid(),'child':child.pid}))
            time.sleep(120)
        warning='lifecycle-fixture-version='+self.version
        return SimpleNamespace(tests=[],warnings=[warning],build_tool=None,
            to_dict=lambda:dict(repository=str(repo),commit=commit,tests=[],test_count=0,warnings=[warning],build_tool=None))
'''

def wheel(folder,version):
    module='codedna_slow_probe';dist=f'{module}-{version}.dist-info'
    files={f'{module}/__init__.py':PLUGIN.replace('VERSION',repr(version)).encode(),
        dist+'/METADATA':f'Metadata-Version: 2.1\nName: codedna-slow-probe\nVersion: {version}\n'.encode(),
        dist+'/WHEEL':b'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
        dist+'/entry_points.txt':b'[codedna.languages]\nslow-probe = codedna_slow_probe:Probe\n'}
    path=folder/f'{module}-{version}-py3-none-any.whl';record=io.StringIO(newline='');writer=csv.writer(record)
    with zipfile.ZipFile(path,'w') as output:
        for name,data in files.items():
            output.writestr(name,data)
            writer.writerow([name,'sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('='),len(data)])
        writer.writerow([dist+'/RECORD','','']);output.writestr(dist+'/RECORD',record.getvalue())
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    entry=PluginVersion('slow-probe','codedna-slow-probe',version,'1.1',False,OFFICIAL_RELEASES+'fixture/'+path.name,digest)
    return path,entry,digest

proof={'scope':'actual frozen executable, isolated offline fixtures; not clean-PC/installed IDE acceptance',
       'core':str(CORE),'checks':{}}
with tempfile.TemporaryDirectory(prefix='codedna-frozen-jobs-') as directory:
    work=Path(directory).resolve();repo=work/'repository';repo.mkdir()
    run_git(repo,'init','--quiet')
    (repo/'ATest.java').write_text('import org.junit.jupiter.api.Test; class ATest { @Test void check() {} }',encoding='utf-8')
    run_git(repo,'add','--all')
    run_git(repo,'-c','user.name=CodeDNA fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false',
            'commit','--quiet','-m','isolated fixture')
    before=run_git(repo,'status','--porcelain')
    home=work/'plugins';os.environ['CODEDNA_PLUGIN_HOME']=str(home)
    file,entry,digest=wheel(work,'1.0.0');desktop_store.install(file,entry,digest)
    config=work/'fixture.json';ready=work/'ready.json'
    def configure(slow): config.write_text(json.dumps({'slow':slow,'ready':str(ready)}),encoding='utf-8')
    configure(True)
    base_env=os.environ.copy();base_env['PATH']=str(Path(os.environ['SystemRoot'])/'System32')+';C:/Program Files/Git/cmd'
    for name in ['PYTHONPATH','PYTHONHOME','CODEDNA_DESKTOP_PLUGIN_SNAPSHOT']:
        base_env.pop(name,None)
    base_env['CODEDNA_FROZEN_LIFECYCLE_FIXTURE']=str(config)
    servers=[]

    def start_api(snapshot=None,allow_build=False):
        with socket.socket() as port_socket:
            port_socket.bind(('127.0.0.1',0));port=port_socket.getsockname()[1]
        env=base_env.copy();token=secrets.token_urlsafe(32);env['CODEDNA_API_TOKEN']=token
        if snapshot is not None:env['CODEDNA_DESKTOP_PLUGIN_SNAPSHOT']=json.dumps(snapshot)
        args=[str(CORE),'serve','--port',str(port)]
        if allow_build:args.append('--allow-build')
        errors=(work/f'api-{len(servers)}.log').open('wb')
        process=subprocess.Popen(args,cwd=work,env=env,stdout=subprocess.PIPE,stderr=errors,
                                 text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
        servers.append((process,errors))
        line=process.stdout.readline();assert line, 'frozen API exited before announcement'
        announcement=json.loads(line);url=announcement['url']
        def call(path,body=None):
            data=json.dumps(body).encode() if body is not None else None
            request=urllib.request.Request(url+path,data=data,
                headers={'X-CodeDNA-Token':token,'Content-Type':'application/json'})
            with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
        end=time.monotonic()+30
        while True:
            try:call('/api/health');break
            except Exception:
                assert process.poll() is None, 'frozen API exited during startup'
                if time.monotonic()>end:raise
                time.sleep(.1)
        return process,announcement,call

    def stop(process):
        if process.poll() is None:process.terminate()
        process.wait(timeout=15);process.stdout.close()

    def job_result(call):
        job=call('/api/analysis-jobs/tests?profile=true',{'repo':str(repo),'rev':'HEAD'});end=time.monotonic()+60
        while job['state'] not in {'completed','failed','cancelled'}:
            assert time.monotonic()<end,job
            time.sleep(.1);job=call('/api/analysis-jobs/'+job['id'])
        assert job['state']=='completed',job
        assert job['result']['test_count']==1,job
        metrics=job['metrics']
        assert metrics['schema_version']==1 and metrics['total_seconds']>0
        assert metrics['worker_startup_seconds']>=0
        assert metrics['stages']['git']['calls']>0
        assert str(repo) not in str(metrics)
        proof['checks']['real_frozen_profile_metrics_without_project_source']='passed'
        return job['result']

    unrelated=subprocess.Popen([str(POWERSHELL),'-NoProfile','-Command','Start-Sleep -Seconds 120'],
                               creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        server,announced,call=start_api()
        assert call('/api/capabilities')['analysis_jobs']['version']==1
        assert call('/api/capabilities')['analysis_jobs']['timing_version']==1
        job=call('/api/analysis-jobs/tests',{'repo':str(repo),'rev':'HEAD'})
        end=time.monotonic()+60
        while not ready.exists():
            assert time.monotonic()<end,call('/api/analysis-jobs/'+job['id'])
            time.sleep(.1)
        pids=json.loads(ready.read_text())
        assert owned_fixture.alive(pids['worker']) and owned_fixture.alive(pids['child'])
        started=time.monotonic();cancelled=call('/api/analysis-jobs/'+job['id']+'/cancel',{})
        assert cancelled['state']=='cancelled',cancelled
        end=time.monotonic()+10
        while (owned_fixture.alive(pids['worker']) or owned_fixture.alive(pids['child'])) and time.monotonic()<end:
            time.sleep(.05)
        assert not owned_fixture.alive(pids['worker']) and not owned_fixture.alive(pids['child'])
        assert unrelated.poll() is None
        proof['checks']['worker_and_descendant_cancelled']='passed'
        proof['checks']['unrelated_process_survived']='passed'
        proof['cancellation_confirmed_seconds']=round(time.monotonic()-started,4)
        assert call('/api/analysis-jobs/'+job['id'])['state']=='cancelled'
        configure(False)
        assert 'lifecycle-fixture-version=1.0.0' in job_result(call)['warnings']
        proof['checks']['analysis_recovers_after_cancel']='passed'
        file,entry,digest=wheel(work,'1.1.0');desktop_store.install(file,entry,digest)
        assert 'lifecycle-fixture-version=1.0.0' in job_result(call)['warnings']
        proof['checks']['replacement_worker_keeps_parent_plugin']='passed'
        snapshot=announced['plugin_snapshot'];stop(server)
        server,_,call=start_api(snapshot,allow_build=True)
        assert call('/api/capabilities')['allow_build'] is True
        assert 'lifecycle-fixture-version=1.0.0' in job_result(call)['warnings']
        proof['checks']['consented_api_restart_keeps_plugin_snapshot']='passed'
        stop(server)
        server,_,call=start_api()
        assert 'lifecycle-fixture-version=1.1.0' in job_result(call)['warnings']
        proof['checks']['application_restart_activates_pending_update']='passed'
        stop(server)
        assert run_git(repo,'status','--porcelain')==before
        assert not (repo/'.codedna').exists()
        proof['checks']['analysis_preserves_project_and_history']='passed'
    finally:
        for process,errors in servers:
            stop(process);errors.close()
        unrelated.terminate();unrelated.wait(timeout=15)
(HERE/'d098-frozen-jobs.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))
