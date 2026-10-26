const fs = require('fs');
const path = require('path');

/** Preserve an explicit override; packaged apps otherwise use their own core. */
function resolveCoreExecutable(env, resourcesPath, exists = fs.existsSync) {
    if (env.CODEDNA_EXECUTABLE) {
        return env.CODEDNA_EXECUTABLE;
    }
    if (resourcesPath) {
        const bundled = path.join(resourcesPath, 'core', 'codedna-core.exe');
        if (exists(bundled)) {
            return bundled;
        }
    }
    return 'codedna';
}

module.exports = { resolveCoreExecutable };
