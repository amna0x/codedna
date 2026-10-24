import { injectable } from '@theia/core/shared/inversify';
import { Emitter } from '@theia/core/lib/common/event';

/** What the two CodeDNA views compare. Shared, so both views always agree. */
export type ComparisonPreset = 'uncommitted' | 'last' | 'last5' | 'custom';

export const PRESETS: { value: ComparisonPreset; label: string }[] = [
    { value: 'uncommitted', label: 'My uncommitted changes' },
    { value: 'last', label: 'My last commit' },
    { value: 'last5', label: 'My last 5 commits' },
    { value: 'custom', label: 'Choose commits…' }
];

@injectable()
export class CodeDnaComparison {

    protected readonly changed = new Emitter<void>();
    readonly onDidChange = this.changed.event;

    preset: ComparisonPreset = 'last';
    customBase = 'HEAD~1';
    customHead = 'HEAD';

    get base(): string {
        return this.preset === 'uncommitted' ? 'HEAD' : this.preset === 'last' ? 'HEAD~1'
            : this.preset === 'last5' ? 'HEAD~5' : this.customBase.trim();
    }

    get head(): string {
        // WORKTREE: the core snapshots edits and new files (not ignored ones) on top of HEAD.
        return this.preset === 'custom' ? this.customHead.trim() : this.preset === 'uncommitted' ? 'WORKTREE' : 'HEAD';
    }

    update(change: Partial<Pick<CodeDnaComparison, 'preset' | 'customBase' | 'customHead'>>): void {
        Object.assign(this, change);
        this.changed.fire();
    }
}
