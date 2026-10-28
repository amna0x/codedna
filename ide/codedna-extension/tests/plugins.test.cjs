const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const ts = require('typescript');
const decorators = { injectable: () => target => target, inject: () => () => {}, postConstruct: () => {} };
const tick = () => new Promise(resolve => setImmediate(resolve));
function load(file, modules) {
    const source = fs.readFileSync(path.join(__dirname, '../src/browser', file), 'utf8');
    const code = ts.transpileModule(source, { compilerOptions: {
        module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
        jsx: ts.JsxEmit.React, experimentalDecorators: true
    } }).outputText;
    const module = { exports: {} };
    vm.runInNewContext(code, { exports: module.exports, module,
        require: id => id.endsWith('/inversify') ? decorators : (modules[id] || {}) });
    return module.exports;
}

test('Extensions contains the existing Language plugins widget without allowing it to be hidden', async () => {
    class ViewContainer {} ViewContainer.Factory = Symbol('factory');
    const { ExtensionsWidgetFactory } = load('extensions-widget-factory.ts', {
        '@theia/core/lib/browser': { ViewContainer, WidgetManager: class {} },
        './plugins-view-widget': { PluginsViewWidget: { ID: 'codedna.plugins' } }
    });
    const factory = new ExtensionsWidgetFactory();
    const child = { id: 'codedna.plugins' }; let title, part, requested;
    const container = { setTitleOptions: value => { title = value; }, addWidget: (widget, options) => { part = { widget, options }; } };
    factory.viewContainerFactory = options => { assert.equal(options.id, 'codedna.extensions'); return container; };
    factory.widgetManager = { getOrCreateWidget: async id => { requested = id; return child; } };
    assert.equal(await factory.createWidget(), container);
    assert.equal(requested, 'codedna.plugins');
    assert.equal(title.label, 'Extensions');
    assert.equal(title.iconClass, 'codicon codicon-extensions');
    assert.equal(part.widget, child);
    assert.equal(part.options.canHide, false);
    assert.equal(part.options.initiallyCollapsed, false);
});

test('Restored layouts regain the Extensions tab without taking editor focus', async () => {
    class AbstractViewContribution {
        constructor(options) { this.options = options; this.opened = []; }
        async openView(options) { this.opened.push(options); }
        registerCommands() {}
    }
    const modules = { '@theia/core/lib/browser': { AbstractViewContribution },
        './extensions-widget-factory': { EXTENSIONS_CONTAINER_ID: 'codedna.extensions' } };
    for (const [file, name] of [['change-view-widget', 'ChangeViewWidget'], ['graph-view-widget','GraphViewWidget'],
        ['history-view-widget','HistoryViewWidget'], ['plugins-view-widget','PluginsViewWidget'],
        ['replay-view-widget','ReplayViewWidget'], ['tests-view-widget','TestsViewWidget']]) {
        modules['./' + file] = { [name]: { ID: 'codedna.plugins', LABEL: 'Language plugins' } };
    }
    const { PluginsViewContribution } = load('codedna-contributions.ts', modules);
    const view = new PluginsViewContribution();
    await view.onDidInitializeLayout();
    assert.equal(view.options.viewContainerId, 'codedna.extensions');
    assert.equal(view.options.defaultWidgetOptions.area, 'left');
    assert.equal(view.options.toggleKeybinding, 'ctrlcmd+shift+x');
    assert.equal(view.opened.length, 1);
    assert.equal(view.opened[0].activate, false);
    assert.equal(view.opened[0].reveal, false);
    const commands = new Map();
    view.registerCommands({ registerCommand: (command, handler) => commands.set(command.id, handler) });
    await commands.get('codedna.extensions.open').execute();
    assert.equal(view.opened[1].activate, true);
});

function pluginsWidget(confirm = false) {
    class ReactWidget { update() { this.updates = (this.updates || 0) + 1; } }
    class ConfirmDialog { async open() { return confirm; } }
    const { PluginsViewWidget } = load('plugins-view-widget.tsx', {
        '@theia/core/lib/browser/widgets/react-widget': { ReactWidget },
        '@theia/core/lib/browser/dialogs': { ConfirmDialog },
        './progress': { withProgress: (_, __, action) => action() }
    });
    return new PluginsViewWidget();
}

test('Installed languages appear while the catalogue is pending and remain available offline', async () => {
    let rejectCatalogue;
    const catalogue = new Promise((_, reject) => { rejectCatalogue = reject; });
    const installed = { api_version: '1.1', plugins: [{ name: 'java' }, { name: 'python' }], problems: [] };
    const view = pluginsWidget();
    view.codedna = { installedPlugins: async () => installed, pluginCatalogue: () => catalogue };
    const refreshing = view.refresh();
    await tick();
    assert.equal(view.installed, installed);
    assert.equal(view.loading, true);
    assert.ok(view.updates >= 2);
    rejectCatalogue(new Error('offline'));
    await refreshing;
    assert.equal(view.installed, installed);
    assert.equal(view.loading, false);
    assert.match(view.catalogueError, /offline/);
});

test('Cancelling a plugin installation never invokes the core installer', async () => {
    const view = pluginsWidget(false); let installs = 0;
    view.codedna = { installPlugin: async () => { installs++; } };
    await view.install({ id:'python', name:'Python', licence:'test', source:'https://example.invalid' },
        { version:'1.0.0', sha256:'a'.repeat(64) }, false);
    assert.equal(installs, 0);
});


test('A pending desktop plugin change requests an app restart and retains actual loaded languages', async () => {
    const view = pluginsWidget();
    const installed = { api_version: '1.1', plugins: [{ name: 'python', version: '0.1.0' }], problems: [] };
    await view.change('install', async () => ({ installed, restart_required: true }), 'Python 1.0.0 is installed.');
    assert.equal(view.installed, installed);
    assert.equal(view.loading, false);
    assert.equal(view.error, undefined);
    assert.match(view.message, /Restart CodeDNA IDE/);
    assert.doesNotMatch(view.message, /start\.bat|pip|python -m/);
});
