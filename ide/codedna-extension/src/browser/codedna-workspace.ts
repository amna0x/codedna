import { inject, injectable } from '@theia/core/shared/inversify';
import URI from '@theia/core/lib/common/uri';
import { FileUri } from '@theia/core/lib/common/file-uri';
import { WorkspaceService } from '@theia/workspace/lib/browser';
import { FileService } from '@theia/filesystem/lib/browser/file-service';
import { FileDialogService } from '@theia/filesystem/lib/browser/file-dialog/file-dialog-service';
import { BinaryBuffer } from '@theia/core/lib/common/buffer';
import { EditorManager } from '@theia/editor/lib/browser';

/** The open workspace (= analysed repository) and navigation into its files. */
@injectable()
export class CodeDnaWorkspace {

    @inject(WorkspaceService) protected readonly workspace: WorkspaceService;
    @inject(EditorManager) protected readonly editors: EditorManager;
    @inject(FileService) protected readonly files: FileService;
    @inject(FileDialogService) protected readonly dialogs: FileDialogService;

    async saveDecisionEvidence(content: string): Promise<boolean> {
        const target = await this.dialogs.showSaveDialog({
            title: 'Save CodeDNA decision evidence', saveLabel: 'Save evidence',
            inputValue: 'codedna-decision.json', filters: { JSON: ['json'] }
        });
        if (!target) { return false; }
        await this.files.writeFile(target, BinaryBuffer.fromString(content));
        return true;
    }

    async repositoryPath(): Promise<string | undefined> {
        const roots = await this.workspace.roots;
        return roots.length ? FileUri.fsPath(roots[0].resource) : undefined;
    }

    async openRepositoryFile(repository: string, relativePath: string, line?: number): Promise<void> {
        const uri = FileUri.create(repository).resolve(relativePath);
        if (line === undefined) {
            await this.editors.open(uri);
        } else {
            const position = { line: Math.max(line - 1, 0), character: 0 };
            await this.editors.open(uri, { selection: { start: position, end: position } });
        }
    }

    async openFile(relativePath: string, line?: number): Promise<void> {
        const roots = await this.workspace.roots;
        if (!roots.length) {
            return;
        }
        const uri: URI = roots[0].resource.resolve(relativePath);
        const position = { line: Math.max((line ?? 1) - 1, 0), character: 0 };
        await this.editors.open(uri, { selection: { start: position, end: position } });
    }
}
