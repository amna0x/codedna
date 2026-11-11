import { createRequire } from 'node:module';
import { join } from 'node:path';

/** A package.json alone does not mean this optional native addon was built. */
export const optionalWindowsCerts = {
    name: 'codedna-optional-windows-ca-certs',
    setup(build) {
        build.onResolve({ filter: /^@vscode\/windows-ca-certs$/ }, args => {
            const require = createRequire(join(args.resolveDir, 'package.json'));
            try {
                // Resolve without loading: the addon targets Electron, not build-time Node.
                require.resolve(args.path);
                return undefined;
            } catch (error) {
                if (error.code !== 'MODULE_NOT_FOUND') { throw error; }
                if (process.platform === 'win32') {
                    console.warn('@vscode/windows-ca-certs native entry is unavailable; leaving optional import external');
                }
                return { path: args.path, external: true };
            }
        });
    }
};
