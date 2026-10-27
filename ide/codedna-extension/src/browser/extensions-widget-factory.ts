import { inject, injectable } from '@theia/core/shared/inversify';
import { ViewContainer, WidgetFactory, WidgetManager } from '@theia/core/lib/browser';
import { PluginsViewWidget } from './plugins-view-widget';

export const EXTENSIONS_CONTAINER_ID = 'codedna.extensions';

/** Persistent activity-bar home for CodeDNA analysis plugins. */
@injectable()
export class ExtensionsWidgetFactory implements WidgetFactory {
    readonly id = EXTENSIONS_CONTAINER_ID;

    @inject(ViewContainer.Factory) protected readonly viewContainerFactory: ViewContainer.Factory;
    @inject(WidgetManager) protected readonly widgetManager: WidgetManager;

    async createWidget(): Promise<ViewContainer> {
        const container = this.viewContainerFactory({ id: this.id, progressLocationId: this.id });
        container.setTitleOptions({ label: 'Extensions', caption: 'Extensions: Language plugins',
            iconClass: 'codicon codicon-extensions', closeable: true });
        const plugins = await this.widgetManager.getOrCreateWidget<PluginsViewWidget>(PluginsViewWidget.ID);
        container.addWidget(plugins, { canHide: false, initiallyCollapsed: false,
            disableDraggingToOtherContainers: true });
        return container;
    }
}
