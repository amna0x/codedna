// Entry point for `theia start` and the installed app: load the bundled VS Code
// extensions (Java editing, D-044) from ./plugins, then start Theia's main.
const path = require('path');
process.env.THEIA_DEFAULT_PLUGINS ??= `local-dir:${path.resolve(__dirname, '..', 'plugins')}`;
require('../lib/backend/electron-main');
