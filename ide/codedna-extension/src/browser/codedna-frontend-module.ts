import { ContainerModule } from '@theia/core/shared/inversify';
import { FrontendApplicationContribution, WidgetFactory, bindViewContribution } from '@theia/core/lib/browser';
import { ApplicationShellOptions } from '@theia/core/lib/browser/shell/application-shell';
import { ServiceConnectionProvider } from '@theia/core/lib/browser/messaging/service-connection-provider';
import { CODEDNA_SERVICE_PATH, CodeDnaService } from '../common/codedna-protocol';
import { ChangeViewWidget } from './change-view-widget';
import {
    ChangeViewContribution, GraphViewContribution, PluginsViewContribution, ReplayViewContribution, TestsViewContribution
} from './codedna-contributions';
import { CodeDnaComparison } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
import { GraphViewWidget } from './graph-view-widget';
import { PluginsViewWidget } from './plugins-view-widget';
import { ReplayViewWidget } from './replay-view-widget';
import { TestsViewWidget } from './tests-view-widget';
import { CodeDnaThemeContribution } from './theme/codedna-theme';
// Geist / Geist Mono (SIL OFL 1.1), bundled so the UI looks the same on every machine.
import '@fontsource-variable/geist';
import '@fontsource-variable/geist-mono';
// tsc does not copy CSS into lib/, so the bundle imports it from src (Theia convention).
import '../../src/browser/style/codedna.css';
import '../../src/browser/style/codedna-shell.css';

export default new ContainerModule((bind, _unbind, _isBound, rebind) => {
    // Side panels start a little wider (Theia default: 19 % of the window) so
    // explanations read as sentences instead of narrow columns.
    rebind(ApplicationShellOptions).toConstantValue({
        leftPanel: { initialSizeRatio: 0.24 },
        rightPanel: { initialSizeRatio: 0.24 }
    });

    bind(CodeDnaThemeContribution).toSelf().inSingletonScope();
    bind(FrontendApplicationContribution).toService(CodeDnaThemeContribution);

    bind(CodeDnaService).toDynamicValue(ctx =>
        ServiceConnectionProvider.createProxy<CodeDnaService>(ctx.container, CODEDNA_SERVICE_PATH)
    ).inSingletonScope();
    bind(CodeDnaWorkspace).toSelf().inSingletonScope();
    bind(CodeDnaComparison).toSelf().inSingletonScope();

    bind(ChangeViewWidget).toSelf();
    bind(WidgetFactory).toDynamicValue(ctx => ({
        id: ChangeViewWidget.ID,
        createWidget: () => ctx.container.get<ChangeViewWidget>(ChangeViewWidget)
    })).inSingletonScope();
    bindViewContribution(bind, ChangeViewContribution);
    bind(FrontendApplicationContribution).toService(ChangeViewContribution);

    bind(TestsViewWidget).toSelf();
    bind(WidgetFactory).toDynamicValue(ctx => ({
        id: TestsViewWidget.ID,
        createWidget: () => ctx.container.get<TestsViewWidget>(TestsViewWidget)
    })).inSingletonScope();
    bindViewContribution(bind, TestsViewContribution);
    bind(FrontendApplicationContribution).toService(TestsViewContribution);

    bind(GraphViewWidget).toSelf();
    bind(WidgetFactory).toDynamicValue(ctx => ({
        id: GraphViewWidget.ID,
        createWidget: () => ctx.container.get<GraphViewWidget>(GraphViewWidget)
    })).inSingletonScope();
    bindViewContribution(bind, GraphViewContribution);

    bind(ReplayViewWidget).toSelf();
    bind(WidgetFactory).toDynamicValue(ctx => ({
        id: ReplayViewWidget.ID,
        createWidget: () => ctx.container.get<ReplayViewWidget>(ReplayViewWidget)
    })).inSingletonScope();
    bindViewContribution(bind, ReplayViewContribution);

    bind(PluginsViewWidget).toSelf();
    bind(WidgetFactory).toDynamicValue(ctx => ({
        id: PluginsViewWidget.ID,
        createWidget: () => ctx.container.get<PluginsViewWidget>(PluginsViewWidget)
    })).inSingletonScope();
    bindViewContribution(bind, PluginsViewContribution);
});
