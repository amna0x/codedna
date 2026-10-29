"""Build an isolated installer core from the previously validated application."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import subprocess
from codedna.git_analysis.git import run_git

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/desktop-D098-2026-10-30/core'
PROOF='a02d20f4d36b451dd80b2948d5bdcc0a6620ecd7'
proof=json.loads((ROOT/'docs/ENGINEERING_VALIDATION_D089_2026-10-29.json').read_text())
assert proof['source_commit']==PROOF and proof['passed']==780 and proof['failed']==proof['skipped']==0
assert not run_git(ROOT,'diff',PROOF,'--','backend/codedna','plugins/codedna-java','plugins/codedna-python','ide','scripts/desktop_core_entry.py','scripts/build_desktop_core.py').strip()
assert sha256((ROOT/proof['log']).read_bytes()).hexdigest()==proof['log_sha256']
assert not OUT.exists(),'Existing candidates must be preserved'
pins={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for folder in ['backend/codedna','plugins/codedna-java/codedna_java','plugins/codedna-python/codedna_python'] for p in (ROOT/folder).rglob('*.py')}
for name in ['scripts/desktop_core_entry.py','scripts/build_desktop_core.py']:
    pins[name]=sha256((ROOT/name).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('desktop_build',ROOT/'scripts/build_desktop_core.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
command=build.build_command(ROOT)
for key,value in [('--distpath',OUT/'dist'),('--workpath',OUT/'work'),('--specpath',OUT/'spec')]:command[command.index(key)+1]=str(value)
OUT.mkdir(parents=True)
(ROOT/'build/desktop-D098-2026-10-30/source-provenance.json').write_text(json.dumps({'validated_application_commit':PROOF,'packaging_commit':run_git(ROOT,'rev-parse','HEAD').strip(),'source_sha256':pins},indent=2)+'\n')
subprocess.run(command,cwd=ROOT,check=True)
for name,digest in pins.items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
manifest=build.write_manifest(OUT/'dist/codedna-core')
print(json.dumps({'candidate':str(OUT/'dist/codedna-core'),'files':len(manifest['files'])}),flush=True)
