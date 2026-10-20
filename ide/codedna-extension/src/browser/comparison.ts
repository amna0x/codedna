import { injectable } from '@theia/core/shared/inversify';
import { Emitter } from '@theia/core/lib/common/event';

/** What the two CodeDNA views compare. Shared, so both views always agree. */
export type ComparisonPreset = 'last' | 'last5' | 'custom';

export const PRESETS: { value: ComparisonPreset; label: string }[] = [
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
        return this.preset === 'last' ? 'HEAD~1' : this.preset === 'last5' ? 'HEAD~5' : this.customBase.trim();
    }

    get head(): string {
        return this.preset === 'custom' ? this.customHead.trim() : 'HEAD';
    }

    update(change: Partial<Pick<CodeDnaComparison, 'preset' | 'customBase' | 'customHead'>>): void {
        Object.assign(this, change);
        this.changed.fire();
    }
}
