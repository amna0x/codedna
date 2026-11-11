import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import esbuild from 'esbuild';
import { optionalWindowsCerts } from './optional-windows-certs.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const localPython = join(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
const python = process.env.CODEDNA_TEST_PYTHON || (existsSync(localPython) ? localPython : 'python');

for (const state of ['absent', 'partial', 'compiled']) {
    test(`optional certificate addon bundles when ${state}`, async () => {
        const repo = mkdtempSync(join(tmpdir(), 'codedna-certs-'));
        try {
            execFileSync(python, ['-c', 'import sys; from pathlib import Path; from codedna.git_analysis.git import run_git; run_git(Path(sys.argv[1]), "init", "--quiet")', repo], { cwd: root });
            const module = join(repo, 'node_modules/@vscode/windows-ca-certs');
            if (state !== 'absent') {
                mkdirSync(module, { recursive: true });
                writeFileSync(join(module, 'package.json'), JSON.stringify({ name: '@vscode/windows-ca-certs', main: 'build/Release/crypt32' }));
            }
            if (state === 'compiled') {
                mkdirSync(join(module, 'build/Release'), { recursive: true });
                // Resolution and bundling must not try to load an Electron native addon.
                writeFileSync(join(module, 'build/Release/crypt32.node'), 'fixture-native-bytes');
            }
            const result = await esbuild.build({
                stdin: { contents: 'try { require("@vscode/windows-ca-certs"); } catch {}', resolveDir: repo },
                bundle: true, platform: 'node', write: false, outdir: join(repo, 'out'),
                metafile: true, loader: { '.node': 'file' },
                resolveExtensions: ['.js', '.json', '.node'], plugins: [optionalWindowsCerts]
            });
            const imports = Object.values(result.metafile.outputs).flatMap(output => output.imports);
            if (state === 'compiled') {
                assert.ok(Object.keys(result.metafile.inputs).some(path => path.endsWith('crypt32.node')));
                assert.ok(!imports.some(item => item.external && item.path === '@vscode/windows-ca-certs'));
            } else {
                assert.ok(imports.some(item => item.external && item.path === '@vscode/windows-ca-certs'));
            }
        } finally {
            assert.equal(dirname(repo), tmpdir());
            assert.ok(repo.split(/[\\/]/).pop().startsWith('codedna-certs-'));
            rmSync(repo, { recursive: true, force: true });
        }
    });
}
