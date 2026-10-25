import { ChildProcess, spawn } from 'child_process';
import { randomBytes } from 'crypto';
import { createServer } from 'net';
import { delimiter } from 'path';
import { injectable } from '@theia/core/shared/inversify';
import { BackendApplicationContribution } from '@theia/core/lib/node';
import {
    AnalyzeReport, CodeDnaService, CodeDnaStatus, ImpactOptions, ImpactReport, InstalledPlugins, PluginCatalogueView, PluginChange,
    ReplayOverview, ReplaySources, ReplayTimeline,
    ProjectHistory, RecordedHistory, SavedRun,
    SelectionReport, SelectionStrategy, SelectionRun
} from '../common/codedna-protocol';

/**
 * Starts the Python core's local API (`codedna serve`) on first use and
 * forwards requests to it.
 *
 * - The executable is `codedna` on PATH, or `CODEDNA_EXECUTABLE`.
 * - A fresh random token is passed through the environment
 *   (`CODEDNA_API_TOKEN`), never on the command line, and stays in this
 *   backend process — the renderer never sees it.
 * - The server listens on 127.0.0.1 only and is stopped with the IDE.
 * - Builds start disabled. Only runSelection, after explicit view confirmation,
 *   restarts the server with build permission and sends a confirmed request.
 */
// Build execution is now enabled only after runSelection receives explicit UI consent.
@injectable()
export class CodeDnaServiceImpl implements CodeDnaService, BackendApplicationContribution {

    protected buildsEnabled = false;
    protected process: ChildProcess | undefined;
    protected baseUrl: string | undefined;
    protected token: string | undefined;
    protected starting: Promise<void> | undefined;
    protected lastError: string | undefined;
    protected version: string | undefined;

    protected get executable(): string {
        return process.env.CODEDNA_EXECUTABLE || 'codedna';
    }

    onStop(): void {
        this.process?.kill();
        this.process = undefined;
    }

    async status(): Promise<CodeDnaStatus> {
        try {
            await this.ensureStarted();
        } catch (error) {
            return { running: false, executable: this.executable, error: String(error instanceof Error ? error.message : error) };
        }
        return { running: true, version: this.version, executable: this.executable };
    }

    analyze(repo: string, base: string, head: string): Promise<AnalyzeReport> {
        return this.post('/api/analyze', { repo, base, head, level: 'method' });
    }

    impact(repo: string, base: string, head: string, options: ImpactOptions = {}): Promise<ImpactReport> {
        return this.post('/api/impact', { repo, base, head,
            max_depth: options.maxDepth, confirmed_only: options.confirmedOnly ?? false });
    }

    select(repo: string, base: string, head: string, strategy: SelectionStrategy, historyCsv?: string): Promise<SelectionReport> {
        return strategy === 'risk'
            ? this.post('/api/risk-select', { repo, base, head, history_csv: historyCsv || undefined })
            : this.post('/api/select', { repo, base, head, strategy });
    }

    async runSelection(repo: string, base: string, head: string, strategy: SelectionStrategy, historyCsv?: string): Promise<SelectionRun> {
        // Called only after the view's explicit build-execution confirmation.
        await this.starting;
        if (!this.buildsEnabled) {
            this.onStop();
            this.buildsEnabled = true;
        }
        return this.post('/api/run-selection', {
            repo, base, head, strategy, history_csv: historyCsv || undefined, allow_build: true
        });
    }

    projectHistory(repo: string): Promise<ProjectHistory> {
        return this.post('/api/project-history', { repo });
    }

    recordSavedRuns(repo: string): Promise<RecordedHistory> {
        return this.post('/api/project-history/record', { repo });
    }

    importRun(repo: string, source: string): Promise<{ id: string; tests: number; failures: number }> {
        return this.post('/api/project-history/import', { repo, source });
    }

    savedRun(repo: string, runId: string): Promise<SavedRun> {
        return this.post('/api/project-history/run', { repo, run_id: runId });
    }

    async replayFolders(): Promise<string[]> {
        // Set by start.bat to the study results in the repository.
        return (process.env.CODEDNA_REPLAY_FOLDERS ?? '').split(delimiter).map(f => f.trim()).filter(f => !!f);
    }

    replaySources(folders: string[]): Promise<ReplaySources> {
        return this.post('/api/replay/sources', { folders });
    }

    replayOverview(folders: string[], seed?: number): Promise<ReplayOverview> {
        return this.post('/api/replay/overview', { folders, seed: seed ?? undefined });
    }

    replay(path: string): Promise<ReplayTimeline> {
        return this.post('/api/replay', { path });
    }

    installedPlugins(): Promise<InstalledPlugins> {
        return this.get('/api/plugins');
    }

    pluginCatalogue(): Promise<PluginCatalogueView> {
        return this.get('/api/plugins/catalogue');
    }

    installPlugin(plugin: string, version: string): Promise<PluginChange> {
        // Called only after the view's confirmation; the core takes the URL and
        // checksum from the official catalogue, never from here.
        return this.post('/api/plugins/install', { plugin, version, confirm: true });
    }

    removePlugin(plugin: string): Promise<PluginChange> {
        return this.post('/api/plugins/remove', { plugin, confirm: true });
    }

    protected get<T>(path: string): Promise<T> {
        return this.request(path, { method: 'GET' });
    }

    protected post<T>(path: string, body: object): Promise<T> {
        return this.request(path, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
        });
    }

    protected async request<T>(path: string, init: { method: string; headers?: Record<string, string>; body?: string }): Promise<T> {
        await this.ensureStarted();
        const response = await fetch(`${this.baseUrl}${path}`, {
            ...init,
            headers: { ...init.headers, 'X-CodeDNA-Token': this.token! }
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const message = data.error ?? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail ?? data));
            throw new Error(message || `CodeDNA API returned HTTP ${response.status}`);
        }
        return data as T;
    }

    protected ensureStarted(): Promise<void> {
        if (this.process && this.baseUrl && this.process.exitCode === null) {
            return Promise.resolve();
        }
        if (!this.starting) {
            this.starting = this.start().finally(() => { this.starting = undefined; });
        }
        return this.starting;
    }

    protected async start(): Promise<void> {
        const port = await freePort();
        const token = randomBytes(32).toString('base64url');
        const args = ['serve', '--host', '127.0.0.1', '--port', String(port)];
        if (this.buildsEnabled) { args.push('--allow-build'); }
        const child = spawn(this.executable, args, {
            env: { ...process.env, CODEDNA_API_TOKEN: token },
            stdio: ['ignore', 'pipe', 'pipe'],
            shell: false,
            windowsHide: true
        });
        let stderr = '';
        child.stderr?.on('data', chunk => { stderr = (stderr + chunk.toString()).slice(-2000); });

        const announced = new Promise<string>((resolve, reject) => {
            let buffer = '';
            child.stdout?.on('data', chunk => {
                buffer += chunk.toString();
                const newline = buffer.indexOf('\n');
                if (newline >= 0) {
                    try {
                        resolve(JSON.parse(buffer.slice(0, newline)).url);
                    } catch {
                        reject(new Error(`unexpected output from "${this.executable} serve": ${buffer.slice(0, 200)}`));
                    }
                }
            });
            child.on('error', error => reject(new Error(
                `could not start "${this.executable}": ${error.message}. Install the CodeDNA core ` +
                '(pip install -e ".[api]") or set CODEDNA_EXECUTABLE.')));
            child.on('exit', code => reject(new Error(`"${this.executable} serve" exited with ${code}: ${stderr.trim()}`)));
        });

        try {
            const url = await withTimeout(announced, 15000, 'CodeDNA API did not start within 15 s');
            this.version = await waitForHealth(url);
            this.process = child;
            this.baseUrl = url;
            this.token = token;
            this.lastError = undefined;
            child.on('exit', () => {
                if (this.process === child) {
                    this.process = undefined;
                    this.baseUrl = undefined;
                }
            });
        } catch (error) {
            child.kill();
            this.lastError = error instanceof Error ? error.message : String(error);
            throw error;
        }
    }
}

function freePort(): Promise<number> {
    return new Promise((resolve, reject) => {
        const server = createServer();
        server.unref();
        server.on('error', reject);
        server.listen(0, '127.0.0.1', () => {
            const address = server.address();
            const port = typeof address === 'object' && address ? address.port : 0;
            server.close(() => resolve(port));
        });
    });
}

async function waitForHealth(url: string): Promise<string | undefined> {
    for (let attempt = 0; attempt < 50; attempt++) {
        try {
            const response = await fetch(`${url}/api/health`);
            if (response.ok) {
                return (await response.json()).version;
            }
        } catch {
            // server not listening yet
        }
        await new Promise(resolve => setTimeout(resolve, 200));
    }
    throw new Error('CodeDNA API did not answer /api/health');
}

function withTimeout<T>(promise: Promise<T>, ms: number, message: string): Promise<T> {
    return new Promise<T>((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(message)), ms);
        promise.then(value => { clearTimeout(timer); resolve(value); },
            error => { clearTimeout(timer); reject(error); });
    });
}
