import { injectable } from '@theia/core/shared/inversify';
import { AbstractViewContribution } from '@theia/core/lib/browser';
import { ChangeViewWidget } from './change-view-widget';
import { GraphViewWidget } from './graph-view-widget';
import { TestsViewWidget } from './tests-view-widget';

@injectable()
export class ChangeViewContribution extends AbstractViewContribution<ChangeViewWidget> {
    constructor() {
        super({
            widgetId: ChangeViewWidget.ID,
            widgetName: ChangeViewWidget.LABEL,
            defaultWidgetOptions: { area: 'left', rank: 300 },
            toggleCommandId: 'codedna.changes.toggle',
            toggleKeybinding: 'ctrlcmd+alt+d'
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
            toggleKeybinding: 'ctrlcmd+alt+t'
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
            toggleKeybinding: 'ctrlcmd+alt+g'
        });
    }
}
