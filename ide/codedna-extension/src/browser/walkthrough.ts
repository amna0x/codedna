import { inject, injectable } from '@theia/core/shared/inversify';
import { FrontendApplicationContribution } from '@theia/core/lib/browser';
import { CommonMenus } from '@theia/core/lib/browser/common-menus';
import { FrontendApplicationStateService } from '@theia/core/lib/browser/frontend-application-state';
import { LocalStorageService } from '@theia/core/lib/browser/storage-service';
import { CommandContribution, CommandRegistry, CommandService } from '@theia/core/lib/common/command';
import { MenuContribution, MenuModelRegistry } from '@theia/core/lib/common/menu';
import { WorkspaceService } from '@theia/workspace/lib/browser';
import { WorkspaceCommands } from '@theia/workspace/lib/browser/workspace-commands';
import { ChangeViewContribution, TestsViewContribution } from './codedna-contributions';

const storageKey = 'codedna.walkthrough.v1';
const command = { id: 'codedna.walkthrough.open', label: 'CodeDNA Walkthrough' };
type Status = 'started' | 'completed' | 'skipped';

const steps = [
    { title: 'Welcome to CodeDNA', copy: 'Review a code change and find tests to run. Follow the highlighted controls in your own project.' },
    { title: 'Open a project', copy: 'Choose the folder that contains your Git project. CodeDNA compares changes inside that project.' },
    { title: 'Show changes', copy: 'Choose saved edits to compare files on disk, or choose commits to compare changes already recorded in Git. Then select Show changes.', anchor: 'changes' },
    { title: 'Suggest tests', copy: 'Select Suggest tests to see which tests CodeDNA recommends. If there is too little evidence to skip tests, it may recommend the full suite.', anchor: 'suggest' },
    { title: 'Review the recommendation', copy: 'Read the test count and reasons in Tests to run. Run recommended tests opens a confirmation before any project code runs.', anchor: 'review' }
];

@injectable()
export class CodeDnaWalkthrough implements FrontendApplicationContribution, CommandContribution, MenuContribution {
    @inject(FrontendApplicationStateService) protected readonly state: FrontendApplicationStateService;
    // The generic StorageService binding is scoped to the open workspace.
    @inject(LocalStorageService) protected readonly storage: LocalStorageService;
    @inject(CommandService) protected readonly commands: CommandService;
    @inject(WorkspaceService) protected readonly workspace: WorkspaceService;
    @inject(ChangeViewContribution) protected readonly changes: ChangeViewContribution;
    @inject(TestsViewContribution) protected readonly tests: TestsViewContribution;

    private overlay?: HTMLElement;
    private card?: HTMLElement;
    private spotlight?: HTMLElement;
    private previousFocus?: HTMLElement;
    private observer?: MutationObserver;
    private resizeObserver?: ResizeObserver;
    private anchor?: HTMLElement;
    private workspaceListener?: { dispose(): void };
    private frame?: number;
    private step = 0;
    private revision = 0;
    private stopped = false;
    private writes = Promise.resolve();

    registerCommands(registry: CommandRegistry): void {
        registry.registerCommand(command, { execute: () => this.open(0) });
    }

    registerMenus(registry: MenuModelRegistry): void {
        registry.registerMenuAction(CommonMenus.HELP, { commandId: command.id });
    }

    onDidInitializeLayout(): void {
        // The ready state follows this hook. Waiting here would block workbench startup.
        void this.state.reachedState('ready').then(() => this.openAutomatically());
    }

    protected async openAutomatically(): Promise<void> {
        const revision = this.revision;
        const saved = await this.storage.getData<Status>(storageKey).catch(() => undefined);
        if (saved === 'completed' || saved === 'skipped') { return; }
        const step = saved === 'started' ? ((await this.workspace.roots).length ? 2 : 1) : 0;
        if (!this.stopped && this.revision === revision && !this.overlay) { await this.open(step); }
    }

    private remember(status: Status): Promise<void> {
        this.writes = this.writes.then(() => this.storage.setData(storageKey, status)).catch(() => {});
        return this.writes;
    }

    private async open(step: number): Promise<void> {
        if (this.stopped) { return; }
        if (this.overlay) { this.card?.focus(); return; }
        this.previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : undefined;
        this.overlay = document.createElement('div');
        this.overlay.className = 'cd-tour';
        this.spotlight = document.createElement('div');
        this.spotlight.className = 'cd-tour-spotlight';
        this.spotlight.setAttribute('aria-hidden', 'true');
        this.card = document.createElement('section');
        this.card.className = 'cd-tour-card';
        this.card.tabIndex = -1;
        this.card.setAttribute('role', 'dialog');
        this.card.setAttribute('aria-labelledby', 'codedna-tour-title');
        this.card.setAttribute('aria-describedby', 'codedna-tour-copy');
        this.card.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                event.preventDefault();
                event.stopPropagation();
                this.dismiss('skipped');
            }
        });
        this.overlay.append(this.spotlight, this.card);
        document.body.append(this.overlay);
        this.observer = new MutationObserver(records => {
            if (records.some(record => !this.overlay?.contains(record.target))) { this.schedulePosition(); }
        });
        this.observer.observe(document.body, { childList: true, subtree: true });
        this.resizeObserver = new ResizeObserver(this.schedulePosition);
        this.resizeObserver.observe(this.card);
        window.addEventListener('resize', this.schedulePosition);
        window.addEventListener('scroll', this.schedulePosition, true);
        this.workspaceListener = this.workspace.onWorkspaceChanged(roots => {
            if (roots.length && this.step === 1) { void this.go(2); }
        });
        await this.go(step);
    }

    private async go(step: number): Promise<void> {
        const revision = ++this.revision;
        if (step === 1 && this.step === 0 && (await this.workspace.roots).length) { step = 2; }
        if (!this.card || revision !== this.revision) { return; }
        this.step = step;
        this.render();
        try {
            if (step === 2) { await this.changes.openView({ reveal: true, activate: false }); }
            if (step >= 3) { await this.tests.openView({ reveal: true, activate: false }); }
        } catch {
            // The card is usable even if the workbench cannot reveal a panel.
        }
        if (revision === this.revision) { this.schedulePosition(); }
    }

    private async chooseFolder(button: HTMLButtonElement): Promise<void> {
        button.disabled = true;
        const revision = this.revision;
        try {
            await this.remember('started');
            if (revision !== this.revision) { return; }
            await this.commands.executeCommand(WorkspaceCommands.OPEN_FOLDER.id);
            const roots = await this.workspace.roots;
            if (revision === this.revision && roots.length) {
                await this.go(2);
            }
        } catch {
            if (revision === this.revision) {
                const message = this.card?.querySelector('[role=status]');
                if (message) { message.textContent = 'Could not open the folder. Try File → Open Folder.'; }
            }
        } finally {
            if (revision === this.revision) {
                button.disabled = false;
                button.focus();
            }
        }
    }

    private render(): void {
        const card = this.card!;
        const step = this.step;
        const content = steps[step];
        const count = document.createElement('p');
        count.className = 'cd-tour-count';
        count.textContent = `Step ${step + 1} of ${steps.length}`;
        const title = document.createElement('h2');
        title.id = 'codedna-tour-title';
        title.textContent = content.title;
        const copy = document.createElement('p');
        copy.id = 'codedna-tour-copy';
        copy.textContent = content.copy;
        const status = document.createElement('div');
        status.setAttribute('role', 'status');
        const controls = document.createElement('div');
        controls.className = 'cd-tour-actions';
        const button = (label: string, action: (control: HTMLButtonElement) => void, primary = false) => {
            const control = document.createElement('button');
            control.type = 'button';
            control.className = primary ? 'theia-button main' : 'theia-button secondary';
            control.textContent = label;
            control.addEventListener('click', () => action(control));
            controls.append(control);
        };
        button('Skip', () => this.dismiss('skipped'));
        if (step > 0) { button('Back', () => void this.go(step - 1)); }
        if (step === 1) { button('Open Folder', control => void this.chooseFolder(control)); }
        if (content.anchor) {
            button('Focus control', () => this.highlightedControl()?.focus());
            controls.lastElementChild?.setAttribute('data-tour-focus', '');
        }
        if (step === steps.length - 1) {
            button('Finish', () => this.dismiss('completed'), true);
        } else {
            button(step === 0 ? 'Start walkthrough' : 'Next', () => {
                if (step === 0) { void this.remember('started'); }
                void this.go(step + 1);
            }, true);
        }
        card.replaceChildren(count, title, copy, status, controls);
        card.focus();
        this.schedulePosition();
    }

    private highlightedControl(): HTMLElement | undefined {
        const selector = 'button:not(:disabled), select:not(:disabled), summary';
        if (this.anchor?.matches(selector)) { return this.anchor; }
        return this.anchor?.querySelector<HTMLElement>(selector) ?? undefined;
    }

    private readonly schedulePosition = (): void => {
        if (!this.card || this.frame !== undefined) { return; }
        this.frame = window.requestAnimationFrame(() => {
            this.frame = undefined;
            this.position();
        });
    };

    private position(): void {
        const card = this.card;
        const spotlight = this.spotlight;
        if (!card || !spotlight) { return; }
        const id = steps[this.step].anchor;
        const anchor = id ? document.querySelector<HTMLElement>(`[data-codedna-tour="${id}"]`) ?? undefined : undefined;
        if (anchor !== this.anchor) {
            if (this.anchor) { this.resizeObserver?.unobserve(this.anchor); }
            this.anchor = anchor;
            if (anchor) { this.resizeObserver?.observe(anchor); }
        }
        const width = window.innerWidth;
        const height = window.innerHeight;
        const rect = anchor?.getBoundingClientRect();
        const panel = anchor?.closest('.codedna-view')?.getBoundingClientRect();
        const left = Math.max(0, panel?.left ?? 0, (rect?.left ?? 0) - 4);
        const top = Math.max(0, panel?.top ?? 0, (rect?.top ?? 0) - 4);
        const right = Math.min(width, panel?.right ?? width, (rect?.right ?? 0) + 4);
        const bottom = Math.min(height, panel?.bottom ?? height, (rect?.bottom ?? 0) + 4);
        const visible = !!rect?.width && !!rect.height && right > left && bottom > top;
        spotlight.classList.toggle('cd-tour-dim', !visible);
        if (visible) {
            Object.assign(spotlight.style, { left: `${left}px`, top: `${top}px`,
                width: `${right - left}px`, height: `${bottom - top}px` });
        }
        const focus = card.querySelector<HTMLButtonElement>('[data-tour-focus]');
        if (focus) { focus.hidden = !visible || !this.highlightedControl(); }
        const { width: cardWidth, height: cardHeight } = card.getBoundingClientRect();
        const gap = 12;
        let x = (width - cardWidth) / 2;
        let y = (height - cardHeight) / 2;
        if (visible) {
            if (right + cardWidth + gap * 2 <= width) { x = right + gap; y = top; }
            else if (left >= cardWidth + gap * 2) { x = left - gap - cardWidth; y = top; }
            else if (height - bottom >= cardHeight + gap * 2) { y = bottom + gap; }
            else if (top >= cardHeight + gap * 2) { y = top - gap - cardHeight; }
            else { y = top > height - bottom ? gap : height - cardHeight - gap; }
        }
        card.style.left = `${Math.max(gap, Math.min(width - cardWidth - gap, x))}px`;
        card.style.top = `${Math.max(gap, Math.min(height - cardHeight - gap, y))}px`;
    }

    private dismiss(status: Status): void {
        this.close();
        void this.remember(status);
    }

    onStop(): void {
        this.stopped = true;
        this.close();
    }

    private close(): void {
        ++this.revision;
        this.workspaceListener?.dispose();
        this.observer?.disconnect();
        this.resizeObserver?.disconnect();
        window.removeEventListener('resize', this.schedulePosition);
        window.removeEventListener('scroll', this.schedulePosition, true);
        if (this.frame !== undefined) { window.cancelAnimationFrame(this.frame); }
        this.frame = undefined;
        this.anchor = undefined;
        this.overlay?.remove();
        this.overlay = this.card = this.spotlight = undefined;
        if (this.previousFocus?.isConnected) { this.previousFocus.focus(); }
        this.previousFocus = undefined;
    }
}
