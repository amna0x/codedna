/**
 * This file can be edited to adjust the ESBuild build process.
 * To reset, delete this file and rerun theia build again.
 */
import { browserOptions, watch } from './gen-esbuild.browser.mjs';
import { nodeOptions } from './gen-esbuild.node.mjs';
import { electronOptions } from './gen-esbuild.electron.mjs';
import esbuild from 'esbuild';
import resolvePackagePath from 'resolve-package-path';

// @vscode/windows-ca-certs is an optional, Windows-only native module that npm
// drops silently when it cannot compile it (e.g. Build Tools without the
// ClangCL toolset that Node 24 headers ask for). Theia's plugin then fails the
// whole bundle. Without it the plugin host only skips reading the Windows
// certificate store for proxied requests (the error is caught and logged), so
// leave the import external instead of failing.
const optionalWindowsCerts = {
    name: 'codedna-optional-windows-ca-certs',
    setup(build) {
        build.onResolve({ filter: /^@vscode\/windows-ca-certs$/ }, () => {
            // Same lookup Theia's plugin uses; when found, let it bundle the binary.
            if (resolvePackagePath('@vscode/windows-ca-certs', process.cwd())) {
                return undefined;
            }
            if (process.platform === 'win32') {
                console.warn('@vscode/windows-ca-certs is not installed; leaving it out of the bundle');
            }
            return { path: '@vscode/windows-ca-certs', external: true };
        });
    }
};
nodeOptions.plugins.unshift(optionalWindowsCerts);

const browserContext = await esbuild.context(browserOptions);
const nodeContext = await esbuild.context(nodeOptions);
const electronContext = await esbuild.context(electronOptions);

if (watch) {
    await Promise.all([
        browserContext.watch(),
        nodeContext.watch(),
        electronContext.watch(),
    ]);
} else {
    try {
        await browserContext.rebuild();
        await browserContext.dispose();
        await nodeContext.rebuild();
        await nodeContext.dispose();
        await electronContext.rebuild();
        await electronContext.dispose();
    } catch {
        process.exit(1);
    }
}
