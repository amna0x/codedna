import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ConfirmDialog } from '@theia/core/lib/browser/dialogs';
import { ProgressService } from '@theia/core/lib/common/progress-service';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import {
    CataloguePlugin, CatalogueVersion, CodeDnaService, InstalledPlugins, PluginCatalogueView, PluginChange
} from '../common/codedna-protocol';
import { withProgress } from './progress';
import { Chip, ErrorNotice, Spinner } from './ui';

/**
 * "Language plugins": what the engine found, and the official catalogue
 * (D-020, D-048, D-054). The view only shows the core's JSON and sends a
 * plugin id and exact version; the core fetches the catalogue from its fixed
 * URL, checks the SHA-256 and installs. Nothing here takes a URL or file.
 */
@injectable()
export class PluginsViewWidget extends ReactWidget {

    static readonly ID = 'codedna.plugins';
    static readonly LABEL = 'Language plugins';

    @inject(CodeDnaService) protected readonly codedna: CodeDnaService;
    @inject(ProgressService) protected readonly progress: ProgressService;

    protected loading = false;
    protected error: string | undefined;
    protected catalogueError: string | undefined;
    protected installed: InstalledPlugins | undefined;
    protected catalogue: PluginCatalogueView['catalogue'] | undefined;
    protected message: string | undefined;

    @postConstruct()
    protected init(): void {
        this.id = PluginsViewWidget.ID;
        this.title.label = PluginsViewWidget.LABEL;
        this.title.caption = 'CodeDNA: language plugins and the official catalogue';
        this.title.iconClass = 'codicon codicon-extensions';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.refresh();
    }

    protected async refresh(): Promise<void> {
        this.loading = true;
        this.error = this.catalogueError = undefined;
        this.update();
        try {
            this.installed = await this.codedna.installedPlugins();
        } catch (error) {
            this.error = errorText(error);
        }
        try {
            const view = await this.codedna.pluginCatalogue();
            this.catalogue = view.catalogue;
            this.installed = view.installed;
        } catch (error) {
            this.catalogue = undefined;
            this.catalogueError = errorText(error);
        } finally {
            this.loading = false;
            this.update();
        }
    }

    protected async install(plugin: CataloguePlugin, version: CatalogueVersion, update: boolean): Promise<void> {
        const confirmed = await new ConfirmDialog({
            title: `${update ? 'Update' : 'Install'} ${plugin.name} ${version.version}?`,
            msg: `A plugin is code that runs with your permissions. CodeDNA downloads it from the official catalogue, `
                + `checks its SHA-256 (${version.sha256?.slice(0, 12)}…) and installs only that file.\n\n`
                + `Licence: ${plugin.licence}\nSource: ${plugin.source}`,
            ok: update ? 'Update' : 'Install', cancel: 'Cancel'
        }).open();
        if (!confirmed) { return; }
        await this.change(`CodeDNA: installing ${plugin.name} ${version.version}`,
            () => this.codedna.installPlugin(plugin.id, version.version),
            `${plugin.name} ${version.version} is installed.`);
    }

    protected async remove(plugin: CataloguePlugin): Promise<void> {
        const confirmed = await new ConfirmDialog({
            title: `Remove ${plugin.name}?`,
            msg: `CodeDNA will stop analysing ${plugin.name} files until you install it again.`,
            ok: 'Remove', cancel: 'Cancel'
        }).open();
        if (!confirmed) { return; }
        await this.change(`CodeDNA: removing ${plugin.name}`, () => this.codedna.removePlugin(plugin.id),
            `${plugin.name} is removed.`);
    }

    protected async change(label: string, action: () => Promise<PluginChange>, done: string): Promise<void> {
        this.loading = true;
        this.error = this.message = undefined;
        this.update();
        try {
            const result = await withProgress(this.progress, label, action);
            this.installed = result.installed;
            this.message = result.restart_required
                ? `${done} Restart CodeDNA (close it and run start.bat again) so the change takes effect.`
                : done;
        } catch (error) {
            this.error = errorText(error);
        } finally {
            this.loading = false;
            this.update();
        }
    }

    protected render(): React.ReactNode {
        return <div>
            <header className='cd-header'>
                <h2>Language plugins</h2>
                <p className='cd-subtitle'>Each language CodeDNA understands comes from a plugin. Java and Python are bundled.</p>
            </header>
            <div className='cd-controls'>
                <button className='theia-button secondary' disabled={this.loading} onClick={() => this.refresh()}>
                    Refresh
                </button>
                {this.loading && <Spinner />}
            </div>
            {this.message && <div className='cd-notice' role='status'><p>{this.message}</p></div>}
            {this.error && <ErrorNotice message={this.error} />}
            {this.renderInstalled()}
            {this.renderCatalogue()}
        </div>;
    }

    protected renderInstalled(): React.ReactNode {
        const installed = this.installed;
        if (!installed) { return undefined; }
        return <section>
            <h3>Installed</h3>
            {installed.plugins.length === 0
                ? <p className='cd-help'>No language plugin is installed, so CodeDNA can list changed files but not
                    analyse them. Run start.bat once, or: <code>pip install -e plugins/codedna-java -e plugins/codedna-python</code></p>
                : <ul className='cd-plugin-list'>
                    {installed.plugins.map(p => <li key={p.name}>
                        <strong>{p.display_name}</strong> <Chip tone='muted'>v{p.version}</Chip>
                        <span className='cd-meta'> {p.file_suffixes.join(', ')} · plugin API {p.api_version}</span>
                    </li>)}
                </ul>}
            {installed.problems.length > 0 && <div className='cd-notice'>
                <strong>Plugins that could not be loaded</strong>
                <ul>{installed.problems.map(p => <li key={p}><code>{p}</code></li>)}</ul>
            </div>}
        </section>;
    }

    protected renderCatalogue(): React.ReactNode {
        if (this.catalogueError) {
            return <section>
                <h3>Official catalogue</h3>
                <div className='cd-notice'>
                    <strong>The catalogue can’t be reached</strong>
                    <p>Installing new plugins needs the official catalogue online. Installed plugins keep working.</p>
                    <details><summary>Details</summary><code>{this.catalogueError}</code></details>
                </div>
            </section>;
        }
        if (!this.catalogue) { return undefined; }
        return <section>
            <h3>Official catalogue</h3>
            <ul className='cd-plugin-list'>{this.catalogue.plugins.map(p => this.renderEntry(p))}</ul>
        </section>;
    }

    protected renderEntry(plugin: CataloguePlugin): React.ReactNode {
        const installed = this.installed?.plugins.find(p => p.name === plugin.id);
        const core = this.installed?.api_version ?? '?';
        const usable = plugin.versions.filter(v => v.compatible === true)
            .sort((a, b) => compareVersions(b.version, a.version));
        const latest = usable[0];
        let action: React.ReactNode;
        if (!latest) {
            action = <span className='cd-meta'>No version works with this CodeDNA (plugin API {core}).</span>;
        } else if (latest.builtin) {
            action = <span className='cd-meta'>{installed ? 'Bundled with CodeDNA.' : 'Bundled: run start.bat once to install it.'}</span>;
        } else if (!installed) {
            action = <button className='theia-button' disabled={this.loading}
                onClick={() => this.install(plugin, latest, false)}>Install v{latest.version}</button>;
        } else {
            action = <>
                {compareVersions(latest.version, installed.version) > 0 && <button className='theia-button' disabled={this.loading}
                    onClick={() => this.install(plugin, latest, true)}>Update to v{latest.version}</button>}
                <button className='theia-button secondary' disabled={this.loading}
                    onClick={() => this.remove(plugin)}>Remove</button>
            </>;
        }
        return <li key={plugin.id}>
            <strong>{plugin.name}</strong> {installed && <Chip tone='added'>installed v{installed.version}</Chip>}
            <p>{plugin.description}</p>
            <p className='cd-meta'>Licence: {plugin.licence} · Source: {plugin.source}</p>
            <div className='cd-controls'>{action}</div>
        </li>;
    }
}

function errorText(error: unknown): string {
    return error instanceof Error ? error.message : String(error);
}

export function compareVersions(a: string, b: string): number {
    const x = a.split('.').map(Number);
    const y = b.split('.').map(Number);
    for (let i = 0; i < Math.max(x.length, y.length); i++) {
        const d = (x[i] ?? 0) - (y[i] ?? 0);
        if (d !== 0) { return d; }
    }
    return 0;
}
