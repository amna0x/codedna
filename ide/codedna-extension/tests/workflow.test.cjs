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

function walkthrough(saved, initialRoots = []) {
    const source = fs.readFileSync(path.join(__dirname, '../src/browser/walkthrough.ts'), 'utf8');
    const code = ts.transpileModule(source, { compilerOptions: {
        module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, experimentalDecorators: true
    } }).outputText;
    const module = { exports: {} };
    const frames = new Map();
    let nextFrame = 0;
    let roots = initialRoots;
    let workspaceChanged;
    let anchor;
    const writes = [];
    const reveals = [];
    class Element {
        children = [];
        style = {};
        listeners = {};
        attributes = {};
        classList = { toggle: (name, value) => { this[name] = value; } };
        get lastElementChild() { return this.children.at(-1); }
        get isConnected() { return this === document.body || !!this.parent?.isConnected; }
        append(...nodes) { for (const node of nodes) { node.parent = this; this.children.push(node); } }
        replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
        remove() { this.parent.children = this.parent.children.filter(node => node !== this); this.parent = undefined; }
        focus() { document.activeElement = this; }
        setAttribute(name, value) { this.attributes[name] = value; }
        addEventListener(name, fn) { this.listeners[name] = fn; }
        getBoundingClientRect() { return { left: 20, top: 100, right: 300, bottom: 260, width: 280, height: 160 }; }
        closest() { return null; }
        matches() { return this.tagName === 'button' && !this.disabled; }
        querySelector(selector) {
            for (const child of this.children) {
                if ((selector === '[data-tour-focus]' && 'data-tour-focus' in child.attributes)
                    || (selector === '[role=status]' && child.attributes.role === 'status')
                    || (selector.includes('button:not') && child.matches())) { return child; }
                const nested = child.querySelector(selector);
                if (nested) { return nested; }
            }
            return null;
        }
    }
    const document = {
        body: new Element(), createElement(tagName) { return Object.assign(new Element(), { tagName }); },
        querySelector: () => anchor
    };
    const editor = document.createElement('textarea');
    document.body.append(editor);
    editor.focus();
    const window = {
        innerWidth: 1000, innerHeight: 700, addEventListener() {}, removeEventListener() {},
        requestAnimationFrame(fn) { frames.set(++nextFrame, fn); return nextFrame; },
        cancelAnimationFrame(id) { frames.delete(id); }
    };
    class Observer { observe() {} unobserve() {} disconnect() {} }
    vm.runInNewContext(code, { module, exports: module.exports, document, window, HTMLElement: Element,
        MutationObserver: Observer, ResizeObserver: Observer,
        require(id) {
            if (id.endsWith('inversify')) { return { injectable: () => target => target, inject: () => () => {} }; }
            if (id.endsWith('common-menus')) { return { CommonMenus: { HELP: ['menubar', '9_help'] } }; }
            if (id.endsWith('workspace-commands')) { return { WorkspaceCommands: { OPEN_FOLDER: { id: 'workspace:openFolder' } } }; }
            return {};
        }
    });
    const tour = new module.exports.CodeDnaWalkthrough();
    const ready = deferred();
    tour.state = { reachedState: () => ready.promise };
    tour.storage = { getData: async () => saved, setData: async (key, value) => writes.push([key, value]) };
    tour.workspace = {
        get roots() { return Promise.resolve(roots); },
        onWorkspaceChanged(fn) { workspaceChanged = fn; return { dispose() { workspaceChanged = undefined; } }; }
    };
    let pickerCount = 0;
    tour.commands = { executeCommand: async () => { pickerCount++; } };
    tour.changes = { openView: async () => reveals.push('changes') };
    tour.tests = { openView: async () => reveals.push('tests') };
    let replay;
    tour.registerCommands({ registerCommand(command, handler) { assert.equal(command.label, 'CodeDNA Walkthrough'); replay = handler.execute; } });
    tour.registerMenus({ registerMenuAction(menu, action) {
        assert.equal(menu.at(-1), '9_help');
        assert.equal(action.commandId, 'codedna.walkthrough.open');
    } });
    tour.onDidInitializeLayout();
    const card = () => document.body.children[1]?.children[1];
    return {
        tour, ready, writes, reveals, replay, document, editor, card, get pickerCount() { return pickerCount; },
        title: () => card()?.children[1].textContent,
        click: async label => {
            const button = card().lastElementChild.children.find(node => node.textContent === label);
            assert.ok(button, `Missing button ${label}`);
            button.listeners.click();
            await tick();
        },
        openProject: () => { roots = [{ path: root }]; workspaceChanged(roots); },
        showAnchor: () => { anchor = document.createElement('button'); document.body.append(anchor); return anchor; },
        position: () => { for (const [id, fn] of [...frames]) { frames.delete(id); fn(); } }
    };
}

test('walkthrough waits for ready, handles folder cancellation and completes using an opened project', async () => {
    const app = walkthrough();
    assert.equal(app.card(), undefined);
    app.ready.resolve();
    await tick();
    assert.equal(app.title(), 'Welcome to CodeDNA');
    await app.click('Start walkthrough');
    await app.click('Open Folder');
    assert.equal(app.pickerCount, 1);
    assert.equal(app.title(), 'Open a project');
    assert.equal(app.writes.at(-1)[1], 'started');
    app.openProject();
    await tick();
    assert.equal(app.title(), 'Show changes');
    await app.click('Next');
    assert.equal(app.title(), 'Suggest tests');
    await app.click('Next');
    assert.equal(app.title(), 'Review the recommendation');
    await app.click('Finish');
    assert.equal(app.card(), undefined);
    assert.equal(app.document.activeElement, app.editor);
    assert.equal(app.writes.at(-1)[1], 'completed');
    assert.deepEqual(app.reveals, ['changes', 'tests', 'tests']);
});

test('walkthrough resumes after reload, centers without an anchor and focuses an available control', async () => {
    const app = walkthrough('started', [{ path: root }]);
    app.ready.resolve();
    await tick();
    assert.equal(app.title(), 'Show changes');
    app.position();
    assert.equal(app.card().style.left, '360px');
    assert.equal(app.card().querySelector('[data-tour-focus]').hidden, true);
    await app.click('Next');
    const button = app.showAnchor();
    app.position();
    assert.equal(app.card().querySelector('[data-tour-focus]').hidden, false);
    await app.click('Focus control');
    assert.equal(app.document.activeElement, button);
    await app.click('Skip');
    assert.equal(app.writes.at(-1)[1], 'skipped');
});

for (const saved of ['completed', 'skipped']) {
    test(`walkthrough stays dismissed for ${saved} profiles and can replay on demand`, async () => {
        const app = walkthrough(saved, [{ path: root }]);
        app.ready.resolve();
        await tick();
        assert.equal(app.card(), undefined);
        await app.replay();
        assert.equal(app.title(), 'Welcome to CodeDNA');
        await app.click('Start walkthrough');
        assert.equal(app.title(), 'Show changes');
        app.card().listeners.keydown({ key: 'Escape', preventDefault() {}, stopPropagation() {} });
        await tick();
        assert.equal(app.card(), undefined);
        assert.equal(app.writes.at(-1)[1], 'skipped');
    });
}

const report = () => ({ repository: root, base_commit: 'a'.repeat(40), head_commit: head,
    selected: [{ test: 'example.ExampleTest', reasons: [] }], skipped: [], total_tests: 1, warnings: [] });
const jobSource = fs.readFileSync(path.join(__dirname, '../src/browser/analysis-jobs-ui.ts'), 'utf8');
const jobCode = ts.transpileModule(jobSource, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022
} }).outputText;
const jobModule = { exports: {} };
vm.runInNewContext(jobCode, { exports: jobModule.exports, module: jobModule, setTimeout }, { filename: 'analysis-jobs-ui.js' });
const { waitForAnalysis } = jobModule.exports;

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
        if (id.endsWith('/react')) return { createElement: (type, props, ...children) => ({ type, props: props ?? {}, children }) };
        if (id === './plain-language') return {
            plural: (n, one, many) => `${n} ${n === 1 ? one : many}`,
            simpleName: value => value, packageName: () => '', breakable: value => value,
            friendlyReason: value => value, friendlyWarning: value => value
        };
        if (id === './decision-evidence') return { recoverySteps: () => ['Keep full-suite history.'] };
        if (id.endsWith('/inversify')) return { injectable: () => target => target, inject: () => () => {}, postConstruct: () => {} };
        if (id.endsWith('/react-widget')) return { ReactWidget };
        if (id.endsWith('/dialogs')) return { ConfirmDialog };
        if (id === './analysis-jobs-ui') return jobModule.exports;
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


test('test detail inspection uses the exact comparison snapshot and drops late responses', async () => {
    const { view, change } = widget(); const selected = report(); view.report = selected;
    const waiting = deferred();
    view.codedna.tests = () => waiting.promise;
    const pending = view.inspectTest(selected, 'example.ExampleTest');
    change();
    waiting.resolve({ repository: root, commit: head, tests: [{ id: 'example.ExampleTest', file: relativeFile, methods: ['checksTotal'] }] });
    await pending;
    assert.equal(view.inspected, undefined); assert.equal(view.inspecting, false);
    view.report = selected;
    view.codedna.tests = async () => ({ repository: root, commit: 'wrong', tests: [] });
    await view.inspectTest(selected, 'example.ExampleTest');
    assert.match(view.error, /another commit/); assert.equal(view.inspected, undefined);
});


test('project workflow selects, inspects, confirms execution and retains actual history recording', async () => {
    const { view, state } = widget(); const selected = report(); const calls = [];
    view.codedna.select = async (...args) => { calls.push(['select', ...args]); return selected; };
    view.codedna.tests = async () => ({ repository: root, commit: head,
        tests: [{ id: 'example.ExampleTest', file: relativeFile, methods: ['checksTotal'] }] });
    const executed = { selection: selected, results: { tests: [{ id: 'example.ExampleTest', status: 'passed', time: 1,
        cases: [{ name: 'checksTotal', status: 'passed', time: 1, message: null }] }],
        warnings: [], exit_codes: [0], failing_tests: [], duration_seconds: 1 },
        output_dir: '.codedna/runs/run-1', recording: { recorded: true, reason: null, commits_with_results: 1 } };
    view.codedna.runSelection = async (...args) => { calls.push(['run', ...args]); return executed; };
    await view.suggest();
    assert.equal(view.report, selected);
    await view.inspectTest(selected, 'example.ExampleTest');
    assert.equal(view.inspected.methods[0], 'checksTotal');
    state.confirm = async () => false;
    await view.runSelected(); assert.equal(calls.filter(call => call[0] === 'run').length, 0);
    state.confirm = async () => true;
    await view.runSelected();
    assert.equal(calls.filter(call => call[0] === 'run').length, 1);
    assert.equal(calls[1][1], root); assert.equal(calls[1][2], selected.base_commit);
    assert.equal(calls[1][3], head); assert.equal(calls[1][4], 'risk');
    assert.equal(view.execution, executed); assert.equal(view.execution.recording.recorded, true);
    assert.equal(view.execution.results.tests[0].cases[0].status, 'passed');
    assert.equal(view.loading, false);
    assert.equal(view.report.risk, undefined); // a passing run cannot manufacture risk validation
});

test('core job stages are shown and results are returned without invented progress', async () => {
    const stages = [], pauses = [];
    const service = {
        startAnalysis: async () => ({ id: 'owned', state: 'queued', stage: 'queued', elapsed_seconds: 0 }),
        analysisJob: async () => pauses.length === 1
            ? { id: 'owned', state: 'running', stage: 'selecting tests', elapsed_seconds: 2.1 }
            : { id: 'owned', state: 'completed', stage: 'completed', elapsed_seconds: 3.2, result: { selected: [] } },
        cancelAnalysis: async () => assert.fail('completed work should not be cancelled')
    };
    const result = await waitForAnalysis(service, 'select', {}, () => true, job => stages.push(job), async () => pauses.push(1));
    assert.equal(JSON.stringify(result), JSON.stringify({ selected: [] }));
    assert.equal(stages.map(s => s.stage).join(','), 'queued,selecting tests,completed');
    assert.ok(stages.every(s => !('percent' in s)));
});

test('comparison changed during submission cancels its worker instead of accepting its response', async () => {
    let current = true;
    const submitted = deferred(), cancellations = [];
    const service = {
        startAnalysis: () => submitted.promise,
        cancelAnalysis: async id => { cancellations.push(id); return { state: 'cancelled' }; },
        analysisJob: async () => assert.fail('stale job should be cancelled first')
    };
    const waiting = waitForAnalysis(service, 'select', {}, () => current, () => assert.fail('stale progress'));
    current = false; submitted.resolve({ id: 'owned', state: 'running' });
    assert.equal(await waiting, undefined);
    assert.deepEqual(cancellations, ['owned']);
});

test('worker failure and inability to confirm cancellation stay visible', async () => {
    await assert.rejects(waitForAnalysis({ startAnalysis: async () => ({ state: 'failed', error: 'deadline exceeded' }) },
        'select', {}, () => true, () => {}), /deadline exceeded/);
    await assert.rejects(waitForAnalysis({ startAnalysis: async () => ({ id: 'owned', state: 'running' }),
        cancelAnalysis: async () => { throw new Error('worker unavailable'); } },
        'select', {}, () => false, () => {}), /worker unavailable/);
});

test('job-enabled recommendation uses the core job contract and no synchronous duplicate', async () => {
    const { view } = widget(), chosen = report();
    view.codedna.analysisJobs = async () => true;
    view.codedna.select = async () => assert.fail('duplicate synchronous analysis');
    view.codedna.startAnalysis = async (operation, payload) => {
        assert.equal(operation, 'risk-select'); assert.equal(payload.repo, root);
        return { id: 'owned', state: 'completed', stage: 'completed', elapsed_seconds: 1, result: chosen };
    };
    await view.suggest();
    assert.equal(view.report, chosen); assert.equal(view.loading, false);
    assert.equal(view.analysisJob, undefined);
});

test('cancelled recommendation cannot restore late results or run project tests', async () => {
    const { view } = widget(), submitted = deferred();
    view.codedna.analysisJobs = async () => true;
    view.codedna.startAnalysis = () => submitted.promise;
    view.codedna.cancelAnalysis = async id => { assert.equal(id, 'owned'); return { id, state: 'cancelled' }; };
    view.codedna.runSelection = async () => assert.fail('analysis must never execute tests');
    const suggesting = view.suggest(); await tick();
    view.analysisCancelled = true;
    submitted.resolve({ id: 'owned', state: 'running' }); await suggesting;
    assert.equal(view.report, undefined); assert.equal(view.loading, false);
    assert.match(view.notice, /No tests were executed/);
});

test('Cancel analysis targets only the displayed job and prevents duplicate clicks', async () => {
    const { view } = widget(), cancellation = deferred(), ids = [];
    view.analysisJob = { id: 'owned', state: 'running' };
    view.codedna.cancelAnalysis = id => { ids.push(id); return cancellation.promise; };
    const stopping = view.cancelAnalysis(); await view.cancelAnalysis();
    assert.deepEqual(ids, ['owned']); assert.equal(view.cancelling, true);
    assert.equal(view.analysisCancelled, true);
    cancellation.resolve({ id: 'owned', state: 'cancelled' }); await stopping;
    assert.equal(view.analysisJob.state, 'cancelled'); assert.equal(view.cancelling, false);
});

test('late cancellation errors cannot overwrite a newer comparison', async () => {
    const { view, change } = widget(), cancellation = deferred();
    view.analysisJob = { id: 'old', state: 'running' };
    view.codedna.cancelAnalysis = () => cancellation.promise;
    const stopping = view.cancelAnalysis(); change();
    view.analysisJob = { id: 'new', state: 'running' };
    cancellation.reject(new Error('old worker unavailable')); await stopping;
    assert.equal(view.error, undefined); assert.equal(view.analysisJob.id, 'new');
});

function changeWidget() {
    let changed;
    const source = fs.readFileSync(path.join(__dirname, '../src/browser/change-view-widget.tsx'), 'utf8');
    const code = ts.transpileModule(source, { compilerOptions: {
        module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
        jsx: ts.JsxEmit.React, experimentalDecorators: true, emitDecoratorMetadata: false
    } }).outputText;
    class ReactWidget {
        constructor() { this.title = {}; this.toDispose = []; }
        addClass() {} update() {}
    }
    const module = { exports: {} };
    vm.runInNewContext(code, { exports: module.exports, module, require(id) {
        if (id.endsWith('/inversify')) return { injectable: () => target => target, inject: () => () => {}, postConstruct: () => {} };
        if (id.endsWith('/react-widget')) return { ReactWidget };
        if (id === './analysis-jobs-ui') return jobModule.exports;
        if (id === './progress') return { withProgress: (_, __, action) => action() };
        return {};
    } });
    const view = new module.exports.ChangeViewWidget();
    view.comparison = { base: 'HEAD~1', head: 'WORKTREE', onDidChange(listener) { changed = listener; return { dispose() {} }; } };
    view.workspace = { repositoryPath: async () => root };
    view.codedna = {}; view.progress = {}; view.init();
    return { view, change() { view.comparison.head = 'other'; changed(); } };
}
const changesReport = () => ({ repository: root, base_commit: 'a'.repeat(40), head_commit: head, changed_files: [], warnings: [] });

test('legacy Changes impact uses the exact analysed snapshot rather than later WORKTREE edits', async () => {
    const { view } = changeWidget(), chosen = changesReport(), impact = { impacted: [] };
    view.codedna.analysisJobs = async () => false;
    view.codedna.analyze = async (repo, base, rev) => {
        assert.equal(repo, root); assert.equal(rev, 'WORKTREE'); return chosen;
    };
    view.codedna.impact = async (repo, base, rev) => {
        assert.equal(base, chosen.base_commit); assert.equal(rev, chosen.head_commit); return impact;
    };
    await view.analyze();
    assert.equal(view.changes, chosen); assert.equal(view.impact, impact); assert.equal(view.analysisJob, undefined);
});

test('Changes rejects duplicate clicks before repository lookup and drops stale comparisons', async () => {
    const { view, change } = changeWidget(), waiting = deferred(); let calls = 0;
    view.codedna.analyze = () => { calls++; return waiting.promise; };
    view.codedna.impact = () => assert.fail('stale impact requested');
    const running = view.analyze(); await view.analyze(); await tick();
    assert.equal(calls, 1); change(); waiting.resolve(changesReport()); await running;
    assert.equal(view.changes, undefined); assert.equal(view.impact, undefined); assert.equal(view.loading, false);
});

test('Changes core jobs run in order and bind impact to immutable analysis IDs', async () => {
    const { view } = changeWidget(), chosen = changesReport(), operations = [];
    view.codedna.analysisJobs = async () => true;
    view.codedna.analyze = () => assert.fail('sync duplicate');
    view.codedna.impact = () => assert.fail('sync duplicate');
    view.codedna.startAnalysis = async (operation, payload) => {
        operations.push(operation);
        if (operation === 'impact') { assert.equal(payload.base, chosen.base_commit); assert.equal(payload.head, chosen.head_commit); }
        return { id: operation, state: 'completed', result: operation === 'analyze' ? chosen : { impacted: [] } };
    };
    await view.analyze();
    assert.deepEqual(operations, ['analyze', 'impact']); assert.equal(view.changes, chosen);
});

test('Changes cancellation during impact stops its owned job and never publishes partial results', async () => {
    const { view } = changeWidget(), ids = [], chosen = changesReport();
    view.codedna.analysisJobs = async () => true;
    view.codedna.startAnalysis = async operation => operation === 'analyze'
        ? { id: 'change', state: 'completed', result: chosen }
        : { id: 'impact', state: 'running', stage: 'analysing impact', elapsed_seconds: 1 };
    view.codedna.cancelAnalysis = async id => { ids.push(id); return { id, state: 'cancelled' }; };
    view.codedna.analysisJob = async id => ({ id, state: 'cancelled' });
    const running = view.analyze(); await tick();
    assert.equal(view.analysisJob.id, 'impact'); await view.cancelAnalysis(); await running;
    assert.ok(ids.length >= 1 && ids.every(id => id === 'impact'));
    assert.equal(view.changes, undefined); assert.equal(view.impact, undefined);
    assert.match(view.notice, /cancelled/); assert.equal(view.loading, false);
});

test('late Changes failures cannot overwrite a newer comparison', async () => {
    const { view, change } = changeWidget(), waiting = deferred();
    view.codedna.analyze = () => waiting.promise;
    const running = view.analyze(); await tick(); change();
    waiting.reject(new Error('obsolete failure')); await running;
    assert.equal(view.error, undefined); assert.equal(view.changes, undefined);
});

test('Changes file navigation uses the analysed repository and preserves the supplied line', async () => {
    const { view } = changeWidget(), chosen = changesReport(), opened = [];
    view.changes = chosen;
    view.workspace.repositoryPath = async () => path.join(root, 'component');
    view.workspace.openRepositoryFile = async (...args) => opened.push(args);
    await view.openResultFile(relativeFile, 7);
    assert.deepEqual(opened, [[root, relativeFile, 7]]);
    view.invalidate(); await view.openResultFile(relativeFile, 7);
    assert.equal(opened.length, 1);
});

test('Changes navigation explains missing working files instead of failing silently', async () => {
    const { view } = changeWidget(); view.changes = changesReport();
    view.workspace.openRepositoryFile = async () => { throw new Error('file no longer exists'); };
    await view.openResultFile(relativeFile, 7);
    assert.match(view.error, /Could not open the working file.*no longer exists/);
});

test('a late Changes file-open error cannot overwrite a newer comparison', async () => {
    const { view, change } = changeWidget(), opening = deferred(); view.changes = changesReport();
    view.workspace.openRepositoryFile = () => opening.promise;
    const pending = view.openResultFile(relativeFile, 7); change();
    opening.reject(new Error('old file missing')); await pending;
    assert.equal(view.error, undefined);
});

const sampleMetrics = () => ({ schema_version: 1, total_seconds: .5,
    stages: { git: { calls: 3, seconds: .1, self_seconds: .1 } }, counters: { 'fit_cache.hit': 1 } });

// Inspect actual rendered controls without Electron. Existing fixture above
// creates a temporary Git repository; no build or network is needed.
function elements(tree) {
    if (Array.isArray(tree)) return tree.flatMap(elements);
    if (!tree || typeof tree !== 'object') return [];
    return [tree, ...elements(tree.children)];
}
function words(tree) {
    if (Array.isArray(tree)) return tree.map(words).join('');
    return tree && typeof tree === 'object' ? words(tree.children) : String(tree ?? '');
}

test('beginner controls keep selection settings collapsed and disclose active method', () => {
    const { view } = widget();
    const tree = view.render(), nodes = elements(tree);
    const settings = nodes.find(node => node.type === 'details' && words(node).includes('Recommendation settings'));
    assert.ok(settings); assert.ok(!settings.props.open);
    const select = elements(settings).find(node => node.type === 'select');
    assert.equal(select.props.value, 'risk');
    assert.match(words(tree), /Method: Use checked project history/);
    assert.match(words(tree), /Suggesting tests does not run project code/);
    view.report = report();
    select.props.onChange({ target: { value: 'dependency' } });
    assert.equal(view.strategy, 'dependency'); assert.equal(view.report, undefined);
    assert.match(words(view.render()), /Method: Follow code links only/);
});

test('cold-history recommendation leads with test count and retains expandable evidence', () => {
    const { view } = widget(), selected = report();
    selected.risk = { status: 'unvalidated', reasons: ['Not enough earlier commits.'], target: .05 };
    const tree = view.renderReport(selected), nodes = elements(tree);
    const summary = tree.children[0];
    assert.equal(summary.props['data-codedna-tour'], 'review');
    assert.equal(summary.children[0].props.className, 'cd-lede');
    assert.match(words(summary.children[0]), /Run 1 of 1 test class or module/);
    assert.match(words(tree), /Skipping tests has not been validated/);
    assert.match(words(tree), /Run the full suite because/);
    const evidence = nodes.find(node => node.type === 'details' && words(node).includes('Why this recommendation?'));
    assert.ok(evidence && !evidence.props.open);
    assert.match(words(evidence), /Not enough earlier commits/);
    const exported = nodes.find(node => node.type === 'details' && words(node).includes('Saved runs and decision report'));
    assert.match(words(exported), /Export decision evidence/);
});

test('run action is disabled when no tests are selected even if project has tests', () => {
    const { view } = widget(), selected = report();
    selected.selected = []; selected.skipped = ['example.ExampleTest'];
    const button = elements(view.renderReport(selected)).find(node => node.type === 'button' && words(node) === 'Run 0 recommended tests');
    assert.ok(button); assert.equal(button.props.disabled, true);
});

test('recommendation retains real timing data and comparison changes clear it', async () => {
    const { view, change } = widget(), metrics = sampleMetrics();
    view.codedna.analysisJobs = async () => true;
    view.codedna.startAnalysis = async () => ({ id: 'owned', operation: 'risk-select', state: 'completed', result: report(), metrics });
    await view.suggest();
    assert.equal(view.timings.length, 1); assert.equal(view.timings[0].metrics, metrics);
    change(); assert.equal(view.timings.length, 0);
});

test('Changes keeps timing for both immutable operations without combining overlapping stages', async () => {
    const { view, change } = changeWidget();
    view.codedna.analysisJobs = async () => true;
    view.codedna.startAnalysis = async operation => ({ id: operation, operation, state: 'completed',
        metrics: sampleMetrics(), result: operation === 'analyze' ? changesReport() : { impacted: [] } });
    await view.analyze(); assert.equal(view.timings.length, 2);
    assert.equal(view.timings.map(value => value.operation).join(','), 'analyze,impact');
    assert.equal(view.timings[0].metrics.total_seconds, .5);
    change(); assert.equal(view.timings.length, 0);
});

test('timing export drops unknown fields and absent measurements stay absent', () => {
    const module = { exports: {} };
    const source = fs.readFileSync(path.join(__dirname, '../src/browser/analysis-metrics.ts'), 'utf8');
    const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
    vm.runInNewContext(code, { module, exports: module.exports });
    const metrics = sampleMetrics(); metrics.source = 'PRIVATE-SOURCE';
    metrics.stages['PRIVATE-PATH'] = { calls: 1, seconds: 3, self_seconds: 3 };
    metrics.counters.credentials = 7; metrics.stages.git.raw_log = 'PRIVATE-LOG';
    const safe = module.exports.safeAnalysisTimings([{ id: 'owned', operation: 'select', metrics }]);
    assert.equal(safe.length, 1); assert.equal(safe[0].metrics.worker_startup_seconds, undefined);
    assert.equal(Object.keys(safe[0].metrics.stages).join(','), 'git');
    assert.ok(!JSON.stringify(safe).includes('PRIVATE') && !JSON.stringify(safe).includes('credentials'));
    assert.equal(metrics.source, 'PRIVATE-SOURCE');
});
