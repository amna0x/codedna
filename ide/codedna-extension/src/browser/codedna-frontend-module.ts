import { ContainerModule } from '@theia/core/shared/inversify';
import { FrontendApplicationContribution, WidgetFactory, bindViewContribution } from '@theia/core/lib/browser';
import { ServiceConnectionProvider } from '@theia/core/lib/browser/messaging/service-connection-provider';
import { CODEDNA_SERVICE_PATH, CodeDnaService } from '../common/codedna-protocol';
import { ChangeViewWidget } from './change-view-widget';
import { ChangeViewContribution, TestsViewContribution } from './codedna-contributions';
import { CodeDnaWorkspace } from './codedna-workspace';
import { TestsViewWidget } from './tests-view-widget';
import { CodeDnaThemeContribution } from './theme/codedna-theme';
// tsc does not copy CSS into lib/, so the bundle imports it from src (Theia convention).
import '../../src/browser/style/codedna.css';
import '../../src/browser/style/codedna-shell.css';

export default new ContainerModule(bind => {
    bind(CodeDnaThemeContribution).toSelf().inSingletonScope();
    bind(FrontendApplicationContribution).toService(CodeDnaThemeContribution);

    bind(CodeDnaService).toDynamicValue(ctx =>
        ServiceConnectionProvider.createProxy<CodeDnaService>(ctx.container, CODEDNA_SERVICE_PATH)
    ).inSingletonScope();
    bind(CodeDnaWorkspace).toSelf().inSingletonScope();

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
});
