const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const root = path.resolve(__dirname, '..', '..', '..');
const localPython = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts' : 'bin',
    process.platform === 'win32' ? 'python.exe' : 'python');
const python = process.env.CODEDNA_BUILD_PYTHON || (fs.existsSync(localPython) ? localPython : 'python');
const result = spawnSync(python, [path.join(root, 'scripts', 'build_desktop_core.py')], {
    cwd: root, stdio: 'inherit', shell: false, windowsHide: true
});
if (result.error) {
    console.error(`Could not run desktop build Python: ${result.error.message}`);
    process.exit(1);
}
process.exit(result.status ?? 1);
