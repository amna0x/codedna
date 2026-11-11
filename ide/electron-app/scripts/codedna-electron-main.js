// Entry point for `theia start` and the installed app: load the bundled VS Code
// extensions (Java editing, D-044) from ./plugins, then start Theia's main.
const path = require('path');
const { app, nativeImage } = require('electron');
const { resolveCoreExecutable } = require('./desktop-runtime.cjs');
const icon = nativeImage.createFromPath(path.resolve(__dirname, '../resources/codedna.png'));
if (!icon.isEmpty()) {
    if (process.platform === 'darwin') {
        void app.whenReady().then(() => app.dock?.setIcon(icon));
    } else {
        app.on('browser-window-created', (_event, window) => window.setIcon(icon));
    }
}
process.env.CODEDNA_EXECUTABLE = resolveCoreExecutable(process.env, process.resourcesPath);
process.env.THEIA_DEFAULT_PLUGINS ??= `local-dir:${path.resolve(__dirname, '..', 'plugins')}`;
require('../lib/backend/electron-main');
