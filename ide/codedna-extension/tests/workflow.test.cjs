const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const { test, after } = require('node:test');
const ts = require('typescript');

// Exercise the actual widget methods without starting Electron or executing builds.
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'codedna-workflow-'));
const relativeFile = 'component/src/test/java/odd-location/ExampleTest.java';
fs.mkdirSync(path.dirname(path.join(root, relativeFile)), { recursive: true });
fs.writeFileSync(path.join(root, relativeFile), 'package example; class ExampleTest {}');
execFileSync('git', ['init', '--quiet', root]);
execFileSync('git', ['-C', root, 'add', '.']);
execFileSync('git', ['-C', root, '-c', 'user.name=CodeDNA test', '-c', 'user.email=test@example.invalid',
    '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', 'test source']);
const head = execFileSync('git', ['-C', root, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
after(() => {
    assert.equal(path.dirname(root), os.tmpdir());
    assert.ok(path.basename(root).startsWith('codedna-workflow-'));
    fs.rmSync(root, { recursive: true, force: true });
});
const source = fs.readFileSync(path.join(__dirname, '../src/browser/tests-view-widget.tsx'), 'utf8');
const code = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
    jsx: ts.JsxEmit.React, experimentalDecorators: true, emitDecoratorMetadata: false
} }).outputText;
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };
const tick = () => new Promise(resolve => setImmediate(resolve));
const report = () => ({ repository: root, base_commit: 'a'.repeat(40), head_commit: head,
    selected: [{ test: 'example.ExampleTest', reasons: [] }], skipped: [], total_tests: 1, warnings: [] });
function widget() {
    let changed;
    const state = { confirm: () => Promise.resolve(true) };
    class ReactWidget {
        constructor() { this.title = {}; this.toDispose = []; }
        addClass() {}
        update() {}
    }
    class ConfirmDialog { open() { return state.confirm(); } }
    const module = { exports: {} };
    vm.runInNewContext(code, { exports: module.exports, module, require(id) {
        if (id.endsWith('/inversify')) return { injectable: () => target => target, inject: () => () => {}, postConstruct: () => {} };
        if (id.endsWith('/react-widget')) return { ReactWidget };
        if (id.endsWith('/dialogs')) return { ConfirmDialog };
        if (id === './progress') return { withProgress: (_, __, action) => action() };
        return {};
    } }, { filename: 'tests-view-widget.js' });
    const view = new module.exports.TestsViewWidget();
    view.comparison = { base: 'HEAD~1', head: 'HEAD', onDidChange(listener) { changed = listener; return { dispose() {} }; } };
    view.workspace = { repositoryPath: async () => root, openRepositoryFile: async () => {} };
    view.codedna = {};
    view.progress = {};
    view.init();
    return { view, state, change(base = 'other') { view.comparison.base = base; changed(); } };
}

test('test links use discovered paths and canonical repository, including module/custom locations', async () => {
    const { view } = widget(); const selected = report(); view.report = selected;
    let discoveryCalls = 0; const opened = [];
    view.workspace.openRepositoryFile = async (...args) => opened.push(args);
    view.codedna.tests = async (repo, revision) => {
        discoveryCalls++; assert.equal(repo, root); assert.equal(revision, head);
        return { repository: root, commit: head, tests: [{ id: 'example.ExampleTest', file: relativeFile }] };
    };
    await view.openTest(selected, 'example.ExampleTest');
    await view.openTest(selected, 'example.ExampleTest');
    assert.deepEqual(opened, [[root, relativeFile], [root, relativeFile]]);
    assert.ok(fs.existsSync(path.join(...opened[0])));
    assert.ok(!fs.existsSync(path.join(root, 'src/test/java/example/ExampleTest.java')));
    assert.equal(discoveryCalls, 1);
});

test('missing test paths produce an explanation instead of a guessed file', async () => {
    const { view } = widget(); const selected = report(); view.report = selected;
    view.codedna.tests = async () => ({ repository: root, commit: head, tests: [] });
    view.workspace.openRepositoryFile = async () => assert.fail('must not open a guessed path');
    await view.openTest(selected, 'example.MissingTest');
    assert.match(view.error, /No source file was discovered/);
});

test('late discovery cannot open a file for an obsolete comparison', async () => {
    const { view, change } = widget(); const selected = report(); view.report = selected;
    const waiting = deferred(); view.codedna.tests = () => waiting.promise;
    view.workspace.openRepositoryFile = async () => assert.fail('obsolete file opened');
    const opening = view.openTest(selected, 'example.ExampleTest'); change();
    waiting.resolve({ repository: root, commit: head, tests: [{ id: 'example.ExampleTest', file: relativeFile }] });
    await opening; assert.equal(view.error, undefined);
});

test('switching away and back while a recommendation loads discards the obsolete response', async () => {
    const { view, change } = widget(); const waiting = deferred(); view.codedna.select = () => waiting.promise;
    const suggesting = view.suggest(); await tick(); change(); change('HEAD~1');
    waiting.resolve(report()); await suggesting;
    assert.equal(view.report, undefined); assert.equal(view.loading, false);
});

test('a completed older execution stays in history instead of restoring stale on-screen results', async () => {
    const { view, change } = widget(); const selected = report(); view.report = selected;
    const waiting = deferred(); view.codedna.runSelection = () => waiting.promise;
    const running = view.runSelected(); await tick(); change();
    waiting.resolve({ selection: selected, results: { tests: [] } }); await running;
    assert.equal(view.report, undefined); assert.equal(view.execution, undefined);
    assert.match(view.notice, /previous comparison.*Project history/); assert.equal(view.loading, false);
});

test('changing comparison while confirmation is open prevents execution', async () => {
    const { view, state, change } = widget(); view.report = report();
    const waiting = deferred(); state.confirm = () => waiting.promise;
    view.codedna.runSelection = () => assert.fail('unconfirmed new comparison executed');
    const running = view.runSelected(); change(); waiting.resolve(true); await running;
    assert.equal(view.loading, false);
});

test('duplicate recommendation clicks do not start duplicate analyses', async () => {
    const { view } = widget(); const waiting = deferred(); let calls = 0;
    view.codedna.select = () => { calls++; return waiting.promise; };
    const first = view.suggest(); const second = view.suggest(); await tick();
    assert.equal(calls, 1); waiting.resolve(report()); await Promise.all([first, second]);
    assert.equal(view.report.head_commit, head);
});

test('late errors do not overwrite a newer comparison', async () => {
    const { view, change } = widget(); const waiting = deferred(); view.codedna.select = () => waiting.promise;
    const suggesting = view.suggest(); await tick(); change(); waiting.reject(new Error('old failure')); await suggesting;
    assert.equal(view.error, undefined); assert.equal(view.loading, false);
});
