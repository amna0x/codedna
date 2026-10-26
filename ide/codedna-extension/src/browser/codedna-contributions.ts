import { injectable } from '@theia/core/shared/inversify';
import { AbstractViewContribution } from '@theia/core/lib/browser';
import { CommandRegistry } from '@theia/core/lib/common/command';
import { ChangeViewWidget } from './change-view-widget';
import { GraphViewWidget } from './graph-view-widget';
import { HistoryViewWidget } from './history-view-widget';
import { PluginsViewWidget } from './plugins-view-widget';
import { ReplayViewWidget } from './replay-view-widget';
import { TestsViewWidget } from './tests-view-widget';

@injectable()
export class ChangeViewContribution extends AbstractViewContribution<ChangeViewWidget> {
    constructor() {
        super({
            widgetId: ChangeViewWidget.ID,
            widgetName: ChangeViewWidget.LABEL,
            defaultWidgetOptions: { area: 'left', rank: 300 },
            toggleCommandId: 'codedna.changes.toggle',
            toggleKeybinding: 'ctrlcmd+shift+alt+d'
        });
    }
}

@injectable()
export class TestsViewContribution extends AbstractViewContribution<TestsViewWidget> {
    constructor() {
        super({
            widgetId: TestsViewWidget.ID,
            widgetName: TestsViewWidget.LABEL,
            defaultWidgetOptions: { area: 'right', rank: 300 },
            toggleCommandId: 'codedna.tests.toggle',
            toggleKeybinding: 'ctrlcmd+shift+alt+t'
        });
    }
}

@injectable()
export class GraphViewContribution extends AbstractViewContribution<GraphViewWidget> {
    constructor() {
        super({
            widgetId: GraphViewWidget.ID,
            widgetName: GraphViewWidget.LABEL,
            defaultWidgetOptions: { area: 'main' },
            toggleCommandId: 'codedna.graph.toggle',
            toggleKeybinding: 'ctrlcmd+shift+alt+g'
        });
    }
}

@injectable()
export class ReplayViewContribution extends AbstractViewContribution<ReplayViewWidget> {
    constructor() {
        super({
            widgetId: ReplayViewWidget.ID,
            widgetName: ReplayViewWidget.LABEL,
            defaultWidgetOptions: { area: 'main' },
            toggleCommandId: 'codedna.replay.toggle',
            toggleKeybinding: 'ctrlcmd+shift+alt+r'
        });
    }
}

@injectable()
export class PluginsViewContribution extends AbstractViewContribution<PluginsViewWidget> {
    constructor() {
        super({
            widgetId: PluginsViewWidget.ID,
            widgetName: PluginsViewWidget.LABEL,
            defaultWidgetOptions: { area: 'main' },
            toggleCommandId: 'codedna.plugins.toggle'
        });
    }
}

@injectable()
export class HistoryViewContribution extends AbstractViewContribution<HistoryViewWidget> {
    constructor() {
        super({
            widgetId: HistoryViewWidget.ID,
            widgetName: HistoryViewWidget.LABEL,
            defaultWidgetOptions: { area: 'main' },
            toggleCommandId: 'codedna.history.toggle',
            toggleKeybinding: 'ctrlcmd+shift+alt+h'
        });
    }

    override registerCommands(commands: CommandRegistry): void {
        super.registerCommands(commands);
        commands.registerCommand({ id: 'codedna.history.open', label: 'Project history', category: 'CodeDNA' },
            { execute: () => this.openView({ activate: true, reveal: true }) });
    }
}
