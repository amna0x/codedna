import { CodeDnaWorkspace } from './codedna-workspace';
import { WorkflowNav } from './ui';
import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { FileDialogService } from '@theia/filesystem/lib/browser/file-dialog/file-dialog-service';
import { FileUri } from '@theia/core/lib/common/file-uri';
import { ProgressService } from '@theia/core/lib/common/progress-service';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import {
    CodeDnaService, ReplayCommit, ReplayOverview, ReplaySource, ReplayTimeline
} from '../common/codedna-protocol';
import { withProgress } from './progress';
import { plural, simpleName } from './plain-language';
import { Chip, ErrorNotice, Spinner } from './ui';

/** Line colours per policy (CSS variables from codedna.css). */
const COLOUR: Record<string, string> = {
    B0_retest_all: 'var(--cd-muted)',
    B4_dependency: 'var(--cd-deleted)',
    'B3@B10_hybrid': 'var(--cd-modified)',
    B10_hybrid: 'var(--cd-added)'
};
const CODEDNA = 'B10_hybrid';
const SPEEDS = [1, 5, 20, 60];  // commits per second
const TICK_MS = 100;

/**
 * "History replay": plays back a real project's history commit by commit and
 * shows what each test-selection policy would have run and missed. Every
 * number comes from the core (`codedna replay`, built from the experiment
 * reports); this view only picks the values at the current commit and draws them.
 */
@injectable()
export class ReplayViewWidget extends ReactWidget {

    static readonly ID = 'codedna.replay';
    static readonly LABEL = 'History replay';

    @inject(CodeDnaWorkspace) protected readonly workspace: CodeDnaWorkspace;
    @inject(CodeDnaService) protected readonly codedna: CodeDnaService;
    @inject(ProgressService) protected readonly progress: ProgressService;

    @inject(FileDialogService) protected readonly dialogs: FileDialogService;

    protected folders = '';
    protected loading = false;
    protected error: string | undefined;
    protected sources: ReplaySource[] = [];
    protected missingFolders: string[] = [];
    protected overview: ReplayOverview | undefined;
    protected overviewSeed: number | undefined;
    protected timeline: ReplayTimeline | undefined;
    protected sourcePath = '';
    protected index = 0;
    protected position = 0;
    protected speed = SPEEDS[1];
    protected timer: ReturnType<typeof setInterval> | undefined;

    @postConstruct()
    protected init(): void {
        this.id = ReplayViewWidget.ID;
        this.title.label = ReplayViewWidget.LABEL;
        this.title.caption = 'CodeDNA: replay a real project history and compare test-selection policies';
        this.title.iconClass = 'codicon codicon-history';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.addClass('cd-replay-view');
        this.toDispose.push({ dispose: () => this.pause() });
        this.codedna.replayFolders().then(folders => {
            if (folders.length && !this.folders) {
                this.folders = folders.join('\n');
                this.loadFolders();
            }
        }, () => undefined);
        this.update();
    }

    protected get folderList(): string[] {
        return this.folders.split(/\r?\n/).map(f => f.trim()).filter(f => !!f);
    }

    protected async browse(): Promise<void> {
        try {
            const folder = await this.dialogs.showOpenDialog({
                title: 'Choose a CodeDNA study results folder', canSelectFiles: false, canSelectFolders: true
            });
            if (folder) {
                this.folders = [...new Set([...this.folderList, FileUri.fsPath(folder)])].join('\n');
                this.error = undefined;
                this.update();
            }
        } catch (error) {
            this.error = error instanceof Error ? error.message : String(error);
            this.update();
        }
    }

    protected async loadFolders(): Promise<void> {
        const folders = this.folderList;
        if (!folders.length) {
            this.error = 'Enter a folder with experiment reports first.';
            this.update();
            return;
        }
        await this.busy('CodeDNA: reading the study results', async () => {
            const [sources, overview] = await Promise.all([
                this.codedna.replaySources(folders),
                this.codedna.replayOverview(folders, this.overviewSeed)
            ]);
            this.sources = sources.sources;
            this.missingFolders = sources.missing;
            this.overview = overview;
            if (!this.sources.length) {
                this.error = 'No experiment reports found in these folders. Choose a folder containing CodeDNA study reports, not a project source folder.';
            }
        });
    }

    protected async reloadOverview(seed: number | undefined): Promise<void> {
        this.overviewSeed = seed;
        await this.busy('CodeDNA: summarising the projects', async () => {
            this.overview = await this.codedna.replayOverview(this.folderList, seed);
        });
    }

    /** Best source for a project: a trace if there is one (sources come sorted that way). */
    protected async openProject(project: string): Promise<void> {
        const source = this.sources.find(s => s.project === project);
        if (source) {
            await this.openSource(source.path);
        }
    }

    protected async openSource(path: string): Promise<void> {
        this.pause();
        await this.busy('CodeDNA: preparing the replay', async () => {
            this.timeline = await this.codedna.replay(path);
            this.sourcePath = path;
            this.seek(0);
        });
    }

    protected async busy(text: string, task: () => Promise<void>): Promise<void> {
        this.loading = true;
        this.error = undefined;
        this.update();
        try {
            await withProgress(this.progress, text, task);
        } catch (error) {
            this.error = error instanceof Error ? error.message : String(error);
        } finally {
            this.loading = false;
            this.update();
        }
    }

    // --- playback ---------------------------------------------------------------------

    protected get last(): number {
        return Math.max(0, (this.timeline?.commits.length ?? 1) - 1);
    }

    protected seek(index: number): void {
        this.index = Math.min(this.last, Math.max(0, Math.round(index)));
        this.position = this.index;
        this.update();
    }

    protected play(): void {
        if (!this.timeline || this.timer) {
            return;
        }
        if (this.index >= this.last) {
            this.seek(0);
        }
        this.timer = setInterval(() => {
            this.position += this.speed * TICK_MS / 1000;
            const next = Math.min(this.last, Math.floor(this.position));
            if (next !== this.index) {
                this.index = next;
                this.update();
            }
            if (this.index >= this.last) {
                this.pause();
            }
        }, TICK_MS);
        this.update();
    }

    protected pause(): void {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = undefined;
            this.update();
        }
    }

    // --- rendering ----------------------------------------------------------------------

    protected render(): React.ReactNode {
        return <div className='cd-replay-layout'>
            <WorkflowNav workspace={this.workspace} current='replay' />
            <header className='cd-header'>
                <h2>History replay</h2>
                <p className='cd-subtitle'>Replay a real project's history commit by commit: what CodeDNA would have run,
                    what it would have missed, and how that compares with running every test.</p>
            </header>
            <form className='cd-controls' onSubmit={e => { e.preventDefault(); this.loadFolders(); }}>
                <label className='cd-field'>
                    <span className='cd-field-label'>Study results folders (one per line)</span>
                    <textarea rows={2} value={this.folders} spellCheck={false} disabled={this.loading}
                        placeholder='Paste a real study results folder, or use Browse…'
                        onChange={e => { this.folders = e.currentTarget.value; this.update(); }} />
                </label>
                <button className='cd-button cd-secondary' type='button' disabled={this.loading} onClick={() => this.browse()}>Browse…</button>
                <button className='cd-button' type='submit' disabled={this.loading || !this.folderList.length} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Loading…</> : 'Load results'}
                </button>
            </form>
            <p className='cd-help'>History replay reads completed research study reports. The placeholder is not a loaded folder.
                To inspect tests you ran in your open project, use Project history instead.</p>
            {this.error && <ErrorNotice message={this.error} />}
            {this.missingFolders.length > 0 && <div className='cd-notice'>
                <strong>Some folders were not found</strong>
                <ul>{this.missingFolders.map(f => <li key={f} className='cd-code'>{f}</li>)}</ul>
            </div>}
            {this.timeline ? this.renderTimeline(this.timeline) : this.overview && this.renderOverview(this.overview)}
        </div>;
    }

    protected renderOverview(overview: ReplayOverview): React.ReactNode {
        const keys = overview.policies.map(p => p.key);
        const label = (key: string) => overview.policies.find(p => p.key === key)?.label ?? key;
        const within = overview.within_risk_target;
        const all = overview.overall[CODEDNA];
        return <section className='cd-replay-overview' aria-label='All projects'>
            <div className='cd-replay-headline'>
                {all && <p className='cd-lede'>
                    Across {plural(overview.projects.length, 'project', 'projects')}, CodeDNA used <strong>{pct(all.mean_time_ratio.mean)}</strong> of
                    the test time on average and missed a failure on <strong>{pct(all.observed_miss_rate.mean)}</strong> of commits
                    (it estimated {pct(all.mean_estimated_skip_risk.mean)}). It stayed within the risk target
                    on {within.projects} of {within.of} projects.
                </p>}
                <label className='cd-field cd-inline'>
                    <span className='cd-field-label'>Seeds</span>
                    <select value={this.overviewSeed ?? ''} disabled={this.loading}
                        onChange={e => this.reloadOverview(e.currentTarget.value === '' ? undefined : Number(e.currentTarget.value))}>
                        <option value=''>Mean over all seeds</option>
                        {[...new Set(this.sources.map(s => s.seed).filter((s): s is number => s !== null))].sort((a, b) => a - b)
                            .map(seed => <option key={seed} value={seed}>Seed {seed} only</option>)}
                    </select>
                </label>
            </div>
            <div className='cd-table-wrap'>
                <table className='cd-table'>
                    <thead>
                        <tr>
                            <th>Project</th><th>Test commits</th><th>With failures</th>
                            {keys.map(k => <th key={k} colSpan={2} style={{ color: COLOUR[k] }}>{label(k)}</th>)}
                            <th>Within target</th><th />
                        </tr>
                        <tr className='cd-subhead'>
                            <th /><th /><th />
                            {keys.map(k => <React.Fragment key={k}><th>time</th><th>missed</th></React.Fragment>)}
                            <th /><th />
                        </tr>
                    </thead>
                    <tbody>
                        {overview.projects.map(p => <tr key={p.project}>
                            <td className='cd-code'>{p.project}</td>
                            <td>{p.commits}</td>
                            <td>{p.commits_with_failures}</td>
                            {keys.map(k => <React.Fragment key={k}>
                                <td>{pct(p.policies[k]?.mean_time_ratio)}</td>
                                <td>{pct(p.policies[k]?.observed_miss_rate)}</td>
                            </React.Fragment>)}
                            <td>{p.within_risk_target === null ? '–'
                                : <Chip tone={p.within_risk_target ? 'added' : 'deleted'}>{p.within_risk_target ? 'Yes' : 'No'}</Chip>}
                                {p.mismatches > 0 && <Chip tone='deleted' title='Replay totals differ from the report'>check</Chip>}
                            </td>
                            <td><button className='cd-button cd-small' disabled={this.loading}
                                onClick={() => this.openProject(p.project)}>
                                Replay{p.kinds.includes('trace') ? '' : ' (no SHAs)'}
                            </button></td>
                        </tr>)}
                        <tr className='cd-total'>
                            <td>All projects</td><td /><td />
                            {keys.map(k => <React.Fragment key={k}>
                                <td>{pct(overview.overall[k]?.mean_time_ratio.mean)}</td>
                                <td>{pct(overview.overall[k]?.observed_miss_rate.mean)}</td>
                            </React.Fragment>)}
                            <td>{within.projects}/{within.of}</td><td />
                        </tr>
                    </tbody>
                </table>
            </div>
            <p className='cd-help'>"time" is the share of the full suite's test time spent per commit (mean over commits);
                "missed" is the share of commits where at least one failing test was skipped. {overview.note}.</p>
        </section>;
    }

    protected renderTimeline(t: ReplayTimeline): React.ReactNode {
        const i = this.index;
        const commit = t.commits[i];
        const projectSources = this.sources.filter(s => s.project === t.project);
        return <section className='cd-replay' aria-label={`Replay of ${t.project}`}>
            <div className='cd-replay-bar'>
                <button className='cd-button cd-secondary' onClick={() => { this.pause(); this.timeline = undefined; this.update(); }}>
                    ← All projects
                </button>
                <h3 className='cd-code'>{t.project}</h3>
                {projectSources.length > 1 && <select value={this.sourcePath} disabled={this.loading}
                    aria-label='Report' onChange={e => this.openSource(e.currentTarget.value)}>
                    {projectSources.map(s => <option key={s.path} value={s.path}>
                        Seed {s.seed ?? '?'}{s.kind === 'trace' ? ' · full detail' : ' · totals only'}
                    </option>)}
                </select>}
            </div>
            <div className='cd-replay-transport'>
                {this.timer
                    ? <button className='cd-button' onClick={() => this.pause()}>Pause</button>
                    : <button className='cd-button' onClick={() => this.play()}>{i >= this.last ? 'Replay again' : 'Play'}</button>}
                <button className='cd-button cd-secondary' onClick={() => this.seek(i - 1)} aria-label='Previous commit'>‹</button>
                <button className='cd-button cd-secondary' onClick={() => this.seek(i + 1)} aria-label='Next commit'>›</button>
                <button className='cd-button cd-secondary' onClick={() => this.seek(this.last)}>End</button>
                <label className='cd-field cd-inline'>
                    <span className='cd-field-label'>Speed</span>
                    <select value={this.speed} onChange={e => { this.speed = Number(e.currentTarget.value); this.update(); }}>
                        {SPEEDS.map(s => <option key={s} value={s}>{s} commits/s</option>)}
                    </select>
                </label>
                <input className='cd-replay-scrub' type='range' min={0} max={this.last} value={i}
                    aria-label='Commit' onChange={e => { this.pause(); this.seek(Number(e.currentTarget.value)); }} />
                <span className='cd-meta'>commit {i + 1} of {t.commits.length}</span>
            </div>
            <CommitStrip timeline={t} index={i} onSeek={index => { this.pause(); this.seek(index); }} />
            {this.renderCounters(t, i)}
            <div className='cd-replay-charts'>
                <LineChart title='Share of test time spent (running mean)' timeline={t} index={i}
                    series={t.policies.map(p => ({ key: p.key, values: t.cumulative[p.key].mean_time_ratio }))} />
                <LineChart title='Commits with a missed failure (running share)' timeline={t} index={i}
                    reference={t.risk_target ?? undefined}
                    series={[
                        ...t.policies.filter(p => p.key !== 'B0_retest_all')
                            .map(p => ({ key: p.key, values: t.cumulative[p.key].observed_miss_rate })),
                        ...(t.cumulative[CODEDNA]?.mean_estimated_risk.some(v => v !== null)
                            ? [{ key: CODEDNA, values: t.cumulative[CODEDNA].mean_estimated_risk, dashed: true,
                                label: 'CodeDNA estimate' }] : [])
                    ]} />
            </div>
            {commit && this.renderCommit(t, commit)}
            {this.renderEvents(t, i)}
            {this.renderProvenance(t)}
        </section>;
    }

    protected renderCounters(t: ReplayTimeline, i: number): React.ReactNode {
        return <div className='cd-replay-counters'>
            {t.policies.map(p => {
                const c = t.cumulative[p.key];
                const run = c.seconds_run[i];
                const saved = c.seconds_saved[i];
                return <div key={p.key} className='cd-card cd-counter' style={{ borderColor: COLOUR[p.key] }}>
                    <strong style={{ color: COLOUR[p.key] }}>{p.label}</strong>
                    <span className='cd-counter-big'>{pct(c.mean_time_ratio[i])}</span>
                    <span className='cd-meta'>of the test time, on average</span>
                    {run !== null && <span>{duration(run)} of tests run{saved ? `, ${duration(saved)} saved` : ''}</span>}
                    <span>{c.failures_caught[i]} of {plural(c.failures[i], 'failing test', 'failing tests')} caught</span>
                    <span className={c.commits_with_miss[i] ? 'cd-warn' : ''}>
                        {plural(c.commits_with_miss[i], 'commit', 'commits')} with a missed failure ({pct(c.observed_miss_rate[i])})
                    </span>
                    {c.mean_estimated_risk[i] !== null && <span className='cd-meta'>
                        estimated {pct(c.mean_estimated_risk[i])}{t.risk_target !== null ? `, target ${pct(t.risk_target)}` : ''}
                    </span>}
                </div>;
            })}
        </div>;
    }

    protected renderCommit(t: ReplayTimeline, commit: ReplayCommit): React.ReactNode {
        return <div className='cd-card cd-replay-commit' aria-live='polite'>
            <div className='cd-row cd-static'>
                <span className='cd-code'>{commit.sha ? commit.sha.slice(0, 10) : `commit ${commit.index + 1}`}</span>
                <span className='cd-row-meta'>
                    {commit.tests !== null && <span className='cd-meta'>{plural(commit.tests, 'test', 'tests')}</span>}
                    {commit.suite_seconds !== null && <span className='cd-meta'>full suite {duration(commit.suite_seconds)}</span>}
                    {commit.failing > 0
                        ? <Chip tone='deleted'>{plural(commit.failing, 'failing test', 'failing tests')}</Chip>
                        : <Chip tone='muted'>no failures</Chip>}
                </span>
            </div>
            {commit.failing_tests && commit.failing_tests.length > 0 && <p className='cd-meta'>
                Failing: {commit.failing_tests.map(simpleName).join(', ')}
            </p>}
            <table className='cd-table'>
                <tbody>
                    {t.policies.map(p => {
                        const o = commit.outcomes[p.key];
                        return <tr key={p.key}>
                            <td style={{ color: COLOUR[p.key] }}>{p.label}</td>
                            <td>{o.selected !== null ? `ran ${o.selected}` : ''}</td>
                            <td>{pct(o.time_ratio)} of time{o.seconds !== null ? ` (${duration(o.seconds)})` : ''}</td>
                            <td>{o.fallback ? <Chip tone='modified' title='Unfamiliar change or risk too high: ran everything'>full suite</Chip> : ''}</td>
                            <td>{commit.failing === 0 ? '' : o.missed === 0
                                ? <Chip tone='added'>caught all</Chip>
                                : <Chip tone='deleted' title={o.missed_tests?.map(simpleName).join(', ')}>missed {o.missed}</Chip>}</td>
                            <td className='cd-meta'>{o.estimated_risk !== null ? `est. risk ${pct(o.estimated_risk)}` : ''}</td>
                        </tr>;
                    })}
                </tbody>
            </table>
        </div>;
    }

    protected renderEvents(t: ReplayTimeline, i: number): React.ReactNode {
        const recent = t.events.filter(e => e.index <= i).slice(-6).reverse();
        if (!recent.length) {
            return undefined;
        }
        return <div className='cd-replay-events'>
            <strong>CodeDNA so far</strong>
            <ul>
                {recent.map(e => <li key={e.index}>
                    <button className='cd-link' onClick={() => { this.pause(); this.seek(e.index); }}>
                        {e.sha ? e.sha.slice(0, 8) : `#${e.index + 1}`}
                    </button>{' '}
                    {e.kind === 'caught' && <>caught {plural(e.failing, 'failing test', 'failing tests')} using {pct(e.time_ratio)} of the time</>}
                    {e.kind === 'missed' && <>missed {e.missed} of {plural(e.failing, 'failing test', 'failing tests')}
                        {e.missed_tests ? ` (${e.missed_tests.map(simpleName).join(', ')})` : ''}</>}
                    {e.kind === 'fallback' && <>ran the full suite (unfamiliar change or high estimated risk)</>}
                    {e.estimated_risk !== null && <span className='cd-meta'> · estimated risk {pct(e.estimated_risk)}</span>}
                </li>)}
            </ul>
        </div>;
    }

    protected renderProvenance(t: ReplayTimeline): React.ReactNode {
        const ok = t.checks.filter(c => c.match).length;
        return <details className='cd-replay-provenance'>
            <summary>Where these numbers come from</summary>
            <p>From the experiment report <span className='cd-code'>{t.source.path}</span> (seed {t.source.seed},
                {' '}{t.source.model}, {t.source.calibration} calibration), on the {t.commits.length} newest commits of the
                project's history; the model was trained only on older commits. Totals match the report
                in {ok} of {t.checks.length} checks.</p>
            {t.source.dataset_sha256 && <p className='cd-meta'>Dataset SHA-256 {t.source.dataset_sha256}</p>}
            <ul>{t.policies.map(p => <li key={p.key}><strong>{p.label}</strong>: {p.description}</li>)}</ul>
            {t.notes.length > 0 && <ul>{t.notes.map(n => <li key={n} className='cd-meta'>{n}</li>)}</ul>}
        </details>;
    }
}

// --- small presentational pieces ------------------------------------------------------------

function CommitStrip({ timeline, index, onSeek }: { timeline: ReplayTimeline; index: number; onSeek: (i: number) => void }): React.ReactElement {
    const n = timeline.commits.length;
    const width = 1000;
    const cell = width / Math.max(1, n);
    const click = (e: React.MouseEvent<SVGSVGElement>) => {
        const box = e.currentTarget.getBoundingClientRect();
        onSeek(Math.floor((e.clientX - box.left) / box.width * n));
    };
    return <svg className='cd-replay-strip' viewBox={`0 0 ${width} 24`} preserveAspectRatio='none' onClick={click}
        role='img' aria-label='Commits: red = CodeDNA missed a failure, green = caught, amber = ran the full suite'>
        {timeline.commits.map(c => {
            const o = c.outcomes[CODEDNA];
            const fill = !o ? 'var(--cd-line)'
                : c.failing ? (o.missed ? 'var(--cd-deleted)' : 'var(--cd-added)')
                    : o.fallback ? 'var(--cd-modified)' : 'var(--cd-line)';
            return <rect key={c.index} x={c.index * cell} y={c.index <= index ? 4 : 8} width={Math.max(cell - 0.5, 0.5)}
                height={c.index <= index ? 16 : 8} fill={fill} opacity={c.index <= index ? 1 : 0.45} />;
        })}
        <rect x={index * cell} y={0} width={Math.max(cell, 2)} height={24} fill='none' stroke='var(--cd-text)' strokeWidth={1.5} />
    </svg>;
}

interface Series { key: string; values: (number | null)[]; dashed?: boolean; label?: string }

function LineChart({ title, timeline, index, series, reference }: {
    title: string; timeline: ReplayTimeline; index: number; series: Series[]; reference?: number
}): React.ReactElement {
    const width = 600, height = 160, pad = 28;
    const n = timeline.commits.length;
    // The scale uses the whole history, so lines do not jump while playing.
    const max = Math.max(reference ?? 0, 0.01,
        ...series.flatMap(s => s.values.filter((v): v is number => v !== null)));
    const x = (i: number) => pad + (n > 1 ? i / (n - 1) : 0) * (width - pad - 6);
    const y = (v: number) => height - pad + 4 - (v / max) * (height - pad - 8);
    const label = (key: string) => timeline.policies.find(p => p.key === key)?.label ?? key;
    return <figure className='cd-card cd-replay-chart'>
        <figcaption>{title}</figcaption>
        <svg viewBox={`0 0 ${width} ${height}`} role='img' aria-label={title}>
            <line x1={pad} x2={width - 6} y1={y(0)} y2={y(0)} stroke='var(--cd-line)' />
            <text x={2} y={y(max) + 4} className='cd-axis'>{pct(max, 0)}</text>
            <text x={2} y={y(0)} className='cd-axis'>0%</text>
            {reference !== undefined && <>
                <line x1={pad} x2={width - 6} y1={y(reference)} y2={y(reference)} stroke='var(--cd-text)' strokeDasharray='2 4' opacity={0.6} />
                <text x={width - 6} y={y(reference) - 3} textAnchor='end' className='cd-axis'>target {pct(reference, 0)}</text>
            </>}
            {series.map(s => {
                const points = s.values.slice(0, index + 1)
                    .map((v, i) => v === null ? undefined : `${x(i).toFixed(1)},${y(v).toFixed(1)}`)
                    .filter(p => !!p).join(' ');
                return <polyline key={s.key + (s.dashed ? '-est' : '')} points={points} fill='none'
                    stroke={COLOUR[s.key]} strokeWidth={s.key === CODEDNA && !s.dashed ? 2.5 : 1.5}
                    strokeDasharray={s.dashed ? '5 4' : undefined} />;
            })}
        </svg>
        <ul className='cd-legend'>
            {series.map(s => <li key={s.key + (s.dashed ? '-est' : '')}>
                <span className={s.dashed ? 'cd-line-dashed' : 'cd-line-solid'} style={{ borderColor: COLOUR[s.key] }} />
                {s.label ?? label(s.key)}
            </li>)}
            {reference !== undefined && <li><span className='cd-line-dashed' />risk target</li>}
        </ul>
    </figure>;
}

function pct(value: number | null | undefined, digits = 1): string {
    return value === null || value === undefined ? '–' : `${(value * 100).toFixed(digits)}%`;
}

function duration(seconds: number): string {
    if (seconds < 90) {
        return `${seconds.toFixed(0)} s`;
    }
    if (seconds < 5400) {
        return `${(seconds / 60).toFixed(0)} min`;
    }
    return `${(seconds / 3600).toFixed(1)} h`;
}
