const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const ts = require('typescript');

const createElement = (type, props, ...children) => ({ type, props: props || {}, children: children.flat(Infinity) });
function load(name) {
    const source = fs.readFileSync(path.join(__dirname, '../src/browser', name + '.tsx'), 'utf8');
    const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.React, experimentalDecorators: true } }).outputText;
    const module = { exports: {} };
    vm.runInNewContext(code, { exports: module.exports, module, setInterval, clearInterval, require(id) {
        if (id.endsWith('/react')) return { createElement };
        if (id.endsWith('/inversify')) return { injectable: () => target => target, inject: () => () => {}, postConstruct: () => {} };
        if (id.endsWith('/react-widget')) return { ReactWidget: class { update() {} } };
        if (id.endsWith('/file-uri')) return { FileUri: { fsPath: uri => uri.path } };
        if (id === './progress') return { withProgress: (_, __, action) => action() };
        if (id === './test-outcomes') return load('test-outcomes');
        if (id === './plain-language') return { simpleName: x => x, plural: (n, word) => `${n} ${word}`,
            friendlyWarning: x => x, friendlyReason: x => x, packageName: () => '', breakable: x => x };
        if (id === './ui') return { Chip: 'chip', ErrorNotice: 'error', Spinner: 'spinner' };
        return {};
    } });
    return module.exports;
}
function nodes(value) {
    if (value == null || value === false) return [];
    if (Array.isArray(value)) return value.flatMap(nodes);
    if (typeof value !== 'object') return [value];
    if (typeof value.type === 'function') return nodes(value.type(value.props));
    return [value, ...value.children.flatMap(nodes)];
}
const text = tree => nodes(tree).filter(x => typeof x === 'string').join(' ');

test('replay refuses blank input; Browse adds an actual folder, cancellation keeps it', async () => {
    const { ReplayViewWidget } = load('replay-view-widget');
    const view = new ReplayViewWidget(); view.codedna = {};
    let tree = view.render();
    assert.equal(nodes(tree).find(x => x.type === 'button' && x.props.type === 'submit').props.disabled, true);
    assert.match(text(tree), /Project history instead/);
    await view.loadFolders(); assert.match(view.error, /Enter a folder/);
    let chosen = { path: 'C:/study/reports' };
    view.dialogs = { showOpenDialog: async options => { assert.equal(options.canSelectFiles, false); return chosen; } };
    await view.browse(); await view.browse(); assert.equal(view.folders, chosen.path);
    chosen = undefined; await view.browse(); assert.equal(view.folders, 'C:/study/reports');
    let requested;
    view.codedna = { replaySources: async folders => { requested = folders; return { sources: [], missing: [] }; },
        replayOverview: async () => ({}) };
    await view.loadFolders(); assert.equal(requested[0], 'C:/study/reports');
    assert.match(view.error, /not a project source folder/);
});

test('saved execution click loads actual outcomes above the list with visible selection', async () => {
    const { HistoryViewWidget } = load('history-view-widget'); const view = new HistoryViewWidget();
    view.workspace = { repositoryPath: async () => 'C:/demo' };
    view.history = { repository: 'C:/demo', candidate_runs: 1, candidate_commits: 1, runs: [
        { id: 'saved-123', commit: 'a'.repeat(40), recorded_at: '2026-10-27', tests: 1, duration_seconds: 1,
            failures: 0, candidate: true }], warnings: [], note: '' };
    view.codedna = { savedRun: async (repo, id) => {
        assert.equal(repo, 'C:/demo'); assert.equal(id, 'saved-123');
        return { id, results: { tests: [], warnings: [] }, logs: [], result_path: 'results.json' };
    } };
    const button = nodes(view.render()).find(x => x.type === 'button' && x.props['aria-pressed'] === false);
    await button.props.onClick();
    const tree = view.render(); const content = text(tree);
    let scrolled = false;
    nodes(tree).find(x => x.props?.['aria-label'] === 'Saved execution details').props.ref({
        scrollIntoView: options => { assert.equal(options.block, 'nearest'); scrolled = true; }
    });
    assert.equal(scrolled, true);
    assert.ok(content.indexOf('Recorded test outcomes:') < content.indexOf('Saved executions'));
    assert.match(content, /Viewing results/); assert.match(content, /C:\/demo/);
    assert.equal(nodes(tree).find(x => x.type === 'button' && x.props['aria-pressed'] === true).props.disabled, false);
});

test('individual recorded checks and failures are visible; old results remain readable', () => {
    const { TestOutcomes } = load('test-outcomes');
    const content = text(TestOutcomes({ tests: [{ id: 'example.PriceTest', status: 'failed', time: 1,
        cases: [{ name: 'discountIsApplied', status: 'failed', time: 1, message: 'expected 90, got 100' }] },
        { id: 'old.Run', status: 'passed', time: 0 }] }));
    assert.match(content, /discount Is Applied/); assert.match(content, /discountIsApplied/);
    assert.match(content, /expected 90, got 100/); assert.match(content, /not recorded for this run/);
});

test('unvalidated risk remains unvalidated, retains core reason and full-suite recommendation', () => {
    const { TestsViewWidget } = load('tests-view-widget'); const view = new TestsViewWidget();
    const reason = 'History includes another repository, branch or future commits.';
    const report = { base_commit: 'a'.repeat(40), head_commit: 'b'.repeat(40), warnings: [], total_tests: 1,
        selected: [{ test: 'example.Test', reasons: [] }], skipped: [], risk: { status: 'unvalidated', reasons: [reason] } };
    const before = JSON.stringify(report); const content = text(view.renderReport(report));
    assert.match(content, /Risk unvalidated/); assert.match(content, /Run the full suite/);
    assert.ok(content.includes(reason)); assert.match(content, /already contains results/);
    assert.equal(JSON.stringify(report), before);
});
