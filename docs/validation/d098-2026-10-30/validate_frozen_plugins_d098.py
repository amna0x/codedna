"""Exercise the production frozen installer through an isolated synthetic plugin.

No public catalogue is mocked in the application. This approved test fixture
calls the normal manager with checksum-pinned synthetic catalogue/download data.
The frozen core itself performs staging, dependency checks and child probing.
"""
import base64
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

from codedna.plugins import desktop_store as store
from codedna.plugins.catalogue import PluginVersion, OFFICIAL_RELEASES

ROOT=Path('C:/Users/hp/OneDrive/Documents/ChatGPT/codedna/.worktrees/core-evidence')
CORE=ROOT/'build/desktop-D098-2026-10-30/core/dist/codedna-core/codedna-core.exe'
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('wheel_fixtures',ROOT/'backend/tests/test_desktop_plugins.py')
fixtures=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)

BOOT='''import json, os
from pathlib import Path
from codedna.plugins import manager
class Probe:
    name = "desktop-probe"
    display_name = "Isolated desktop installation smoke fixture"
    version = "1.0.0"
    api_version = "1.1"
    file_suffixes = (".desktop-probe",)
    def __init__(self):
        action = os.environ.get("CODEDNA_FROZEN_SMOKE_ACTION")
        if not action: return
        config = json.loads(Path(action).read_text())
        output = Path(config["output"])
        if output.exists(): return
        try:
            if config["action"] == "install":
                result = manager.install(config["catalogue"], "python", config["version"], confirmed=True,
                    download=lambda url: Path(config["wheel"]).read_bytes())
            else:
                result = manager.remove(config["catalogue"], config.get("plugin", "python"), confirmed=True)
            result = {"ok": True, "result": result}
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        output.write_text(json.dumps(result), encoding="utf-8")
    def handles(self, path): return False
    def parse(self, source): return None
    def build_graph(self, *args, **kwargs): return None
    def discover_tests(self, *args, **kwargs): return None
    def run_tests(self, *args, **kwargs): return None
'''

def boot_wheel(folder):
    wheel=folder/'codedna_desktop_probe-1.0.0-py3-none-any.whl'
    dist='codedna_desktop_probe-1.0.0.dist-info'
    files={'codedna_desktop_probe/__init__.py':BOOT.encode(),
        dist+'/METADATA':b'Metadata-Version: 2.1\nName: codedna-desktop-probe\nVersion: 1.0.0\n',
        dist+'/WHEEL':b'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
        dist+'/entry_points.txt':b'[codedna.languages]\ndesktop-probe = codedna_desktop_probe:Probe\n'}
    record=io.StringIO(newline='')
    writer=csv.writer(record)
    with zipfile.ZipFile(wheel,'w') as archive:
        for name,data in files.items():
            archive.writestr(name,data)
            writer.writerow([name,'sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('='),len(data)])
        writer.writerow([dist+'/RECORD','',''])
        archive.writestr(dist+'/RECORD',record.getvalue())
    return wheel

proof={'scope':'production frozen core, restricted PATH, isolated per-user store; not clean-PC acceptance','checks':{}}
with tempfile.TemporaryDirectory(prefix='codedna-frozen-plugins-') as directory:
    work=Path(directory).resolve()
    assert work.parent==Path(tempfile.gettempdir()).resolve() and work.name.startswith('codedna-frozen-plugins-')
    home=work/'managed plugins with spaces'
    os.environ['CODEDNA_PLUGIN_HOME']=str(home)
    bootstrap=boot_wheel(work)
    digest=hashlib.sha256(bootstrap.read_bytes()).hexdigest()
    entry=PluginVersion('desktop-probe','codedna-desktop-probe','1.0.0','1.1',False,
                        OFFICIAL_RELEASES+'smoke/'+bootstrap.name,digest)
    store.install(bootstrap,entry,digest)
    env=os.environ.copy()
    env['PATH']=str(Path(os.environ['SystemRoot'])/'System32')
    env.pop('PYTHONPATH',None)
    env.pop('PYTHONHOME',None)
    def run():
        result=subprocess.run([str(CORE),'plugins'],cwd=work,env=env,capture_output=True,text=True,timeout=120)
        assert result.returncode==0,(result.stdout,result.stderr)
        return json.loads(result.stdout)
    def action(wheel, operation='install', index=None):
        config=work/'action.json'
        output=work/(f'out-{len(list(work.glob("out-*.json")))}.json')
        data={'action':operation,'wheel':str(wheel),'catalogue':index or fixtures.catalogue(wheel),
              'version':wheel.name.split('-')[1],'output':str(output)}
        config.write_text(json.dumps(data))
        env['CODEDNA_FROZEN_SMOKE_ACTION']=str(config)
        listed=run()
        assert output.exists(),listed
        return json.loads(output.read_text(encoding='utf-8')),listed
    good=fixtures.make_wheel(work)
    result,_=action(good)
    assert result['ok'],result
    assert result['result']['restart_required'] is True
    cold=run()
    assert not cold['problems'],cold
    assert next(p for p in cold['plugins'] if p['name']=='python')['version']=='1.0.0',cold
    proof['checks']['install_and_cold_restart']='passed'
    active=json.loads((home/'active.json').read_text())['plugins']['python']
    source=home/'versions'/active['directory']/'site/codedna_python/__init__.py'
    original=source.read_bytes()
    source.write_text("raise RuntimeError('damaged optional copy')\n")
    damaged=run()
    assert next(p for p in damaged['plugins'] if p['name']=='python')['version']=='0.1.0',damaged
    assert any('damaged optional copy' in problem for problem in damaged['problems']),damaged
    source.write_bytes(original)
    assert next(p for p in run()['plugins'] if p['name']=='python')['version']=='1.0.0'
    proof['checks']['damaged_optional_uses_bundled_fallback']='passed'
    before=(home/'active.json').read_bytes()
    for label,kwargs in [('broken_update',{'fail':True}),('missing_dependency',{'requires':'Requires-Dist: codedna-unavailable-dependency>=9\n'})]:
        candidate=fixtures.make_wheel(work,'1.1.0',**kwargs)
        result,_=action(candidate)
        assert not result['ok'],(label,result)
        assert (home/'active.json').read_bytes()==before
        assert next(p for p in run()['plugins'] if p['name']=='python')['version']=='1.0.0'
        proof['checks'][label+'_preserves_working_version']='passed'
    index=fixtures.catalogue(good)
    index['plugins'][0]['versions'][0]['sha256']='0'*64
    result,_=action(good,index=index)
    assert not result['ok'] and 'checksum' in result['error'],result
    assert (home/'active.json').read_bytes()==before
    proof['checks']['checksum_refusal']='passed'
    result,_=action(good,'remove')
    assert result['ok'],result
    cold=run()
    assert not cold['problems'],cold
    assert next(p for p in cold['plugins'] if p['name']=='python')['version']=='0.1.0',cold
    assert any(p['name']=='java' for p in cold['plugins'])
    proof['checks']['remove_and_restore_bundled_python']='passed'
    result,_=action(good,'remove')
    assert not result['ok'] and 'bundled' in result['error'],result
    proof['checks']['bundled_removal_refused']='passed'
    manifest=json.loads((CORE.parent/'bundle-manifest.json').read_text())
    for relative,expected in manifest['files'].items():
        with (CORE.parent/relative).open('rb') as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest()==expected,relative
    proof['bundle_files_verified']=len(manifest['files'])
(HERE/'d098-frozen-plugin-validation.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
