const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const ts = require('typescript');

const createElement = (type, props, ...children) => ({ type, props: props || {}, children: children.flat(Infinity) });
function load(name) {
    const candidate = path.join(__dirname, '../src/browser', name);
    const source = fs.readFileSync(fs.existsSync(candidate + '.tsx') ? candidate + '.tsx' : candidate + '.ts', 'utf8');
    const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.React, experimentalDecorators: true } }).outputText;
    const module = { exports: {} };
    vm.runInNewContext(code, { exports: module.exports, module, setInterval, clearInterval, require(id) {
        if (id.endsWith('/buffer')) return { BinaryBuffer: { fromString: text => text } };
        if (id.endsWith('/react')) return { createElement };
        if (id.endsWith('/inversify')) return { injectable: () => target => target, inject: () => () => {}, postConstruct: () => {} };
        if (id.endsWith('/react-widget')) return { ReactWidget: class { update() {} } };
        if (id.endsWith('/file-uri')) return { FileUri: { fsPath: uri => uri.path } };
        if (id === './progress') return { withProgress: (_, __, action) => action() };
        if (id === './test-outcomes') return load('test-outcomes');
        if (id === './decision-evidence') return load('decision-evidence');
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


test('test explanation shows source check names and warns that discovery is not execution', () => {
    const { TestsViewWidget } = load('tests-view-widget'); const view = new TestsViewWidget();
    view.inspected = { id: 'PriceTest', file: 'tests/PriceTest.java', framework: 'junit5', language: 'java',
        methods: ['discountIsApplied', 'zeroTotal'] };
    const report = { repository: 'C:/demo', base_commit: 'a'.repeat(40), head_commit: 'b'.repeat(40),
        total_tests: 1, selected: [{ test: 'PriceTest', file: 'tests/PriceTest.java', reasons: ['changed test class'] }],
        skipped: [], warnings: [] };
    const content = text(view.renderReport(report));
    assert.match(content, /discount Is Applied/); assert.match(content, /discountIsApplied/);
    assert.match(content, /tests\/PriceTest.java/); assert.match(content, /does not execute or verify/);
    assert.match(content, /Explain this test/);
});

test('evidence guidance preserves refusal and provenance without claiming more data guarantees approval', () => {
    const { recoverySteps } = load('decision-evidence');
    const report = { risk: { status: 'unvalidated', reasons: ['History includes another repository, branch or future commits.'] } };
    const before = JSON.stringify(report);
    const content = recoverySteps(report).join(' ');
    assert.match(content, /ending at the comparison base/); assert.match(content, /audit must pass/);
    assert.equal(JSON.stringify(report), before);
});

test('diagnostic export omits raw logs, source and failure messages but preserves observed statuses', () => {
    const { decisionRecord } = load('decision-evidence');
    const report = { repository: 'C:/demo', base_commit: 'base', head_commit: 'head', strategy: 'risk',
        total_tests: 1, selected: [{ test: 'PriceTest', reasons: ['required'] }], skipped: [], warnings: [],
        risk: { status: 'unvalidated', reasons: ['insufficient history'] },
        source: 'SOURCE_SECRET', environment: { TOKEN: 'TOKEN_SECRET' } };
    const execution = { output_dir: 'LOG_SECRET', results: { tests: [{ id: 'PriceTest', status: 'failed', time: 1,
        cases: [{ name: 'discount', status: 'failed', time: 1, message: 'MESSAGE_SECRET' }] }],
        failing_tests: ['PriceTest'], exit_codes: [1], duration_seconds: 1, logs: 'RAW_SECRET' } };
    const record = decisionRecord(report, execution, '2026-10-27T00:00:00Z');
    const content = JSON.stringify(record);
    assert.match(content, /failed/); assert.match(content, /insufficient history/);
    for (const secret of ['SOURCE_SECRET', 'TOKEN_SECRET', 'LOG_SECRET', 'MESSAGE_SECRET', 'RAW_SECRET']) {
        assert.ok(!content.includes(secret));
    }
    assert.equal(record.execution.tests[0].cases[0].name, 'discount');
    assert.match(record.disclosure, /Review before sharing/);
    assert.equal(decisionRecord(report, undefined).execution, null);
});


test('evidence save requires a chosen destination and propagates write failures', async () => {
    const { CodeDnaWorkspace } = load('codedna-workspace'); const workspace = new CodeDnaWorkspace();
    const writes = [];
    let target;
    workspace.dialogs = { showSaveDialog: async options => {
        assert.equal(options.inputValue, 'codedna-decision.json'); return target;
    } };
    workspace.files = { writeFile: async (...args) => writes.push(args) };
    assert.equal(await workspace.saveDecisionEvidence('evidence'), false);
    assert.equal(writes.length, 0);
    target = { path: '/chosen/decision.json' };
    assert.equal(await workspace.saveDecisionEvidence('evidence'), true);
    assert.equal(writes.length, 1); assert.equal(writes[0][0], target); assert.equal(writes[0][1], 'evidence');
    workspace.files.writeFile = async () => { throw new Error('read-only destination'); };
    await assert.rejects(workspace.saveDecisionEvidence('evidence'), /read-only destination/);
});


test('view export saves the current decision, handles cancellation and reports a failed save', async () => {
    const { TestsViewWidget } = load('tests-view-widget'); const view = new TestsViewWidget();
    const report = { repository: 'C:/demo', base_commit: 'base', head_commit: 'head', strategy: 'risk',
        total_tests: 1, selected: [{ test: 'PriceTest', reasons: ['required'] }], skipped: [], warnings: [],
        risk: { status: 'unvalidated', reasons: ['insufficient history'] } };
    view.report = report;
    let payload;
    view.workspace = { saveDecisionEvidence: async content => { payload = JSON.parse(content); return false; } };
    await view.exportEvidence(report);
    assert.equal(payload.comparison.head, 'head'); assert.equal(payload.risk.status, 'unvalidated');
    assert.equal(view.notice, undefined);
    view.workspace.saveDecisionEvidence = async () => true;
    await view.exportEvidence(report); assert.match(view.notice, /evidence saved/);
    view.workspace.saveDecisionEvidence = async () => { throw new Error('disk is full'); };
    await view.exportEvidence(report); assert.match(view.error, /disk is full/);
    view.report = undefined; view.workspace.saveDecisionEvidence = () => assert.fail('obsolete decision exported');
    await view.exportEvidence(report);
});
