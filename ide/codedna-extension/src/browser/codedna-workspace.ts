import { inject, injectable } from '@theia/core/shared/inversify';
import URI from '@theia/core/lib/common/uri';
import { FileUri } from '@theia/core/lib/common/file-uri';
import { WorkspaceService } from '@theia/workspace/lib/browser';
import { EditorManager } from '@theia/editor/lib/browser';

/** The open workspace (= analysed repository) and navigation into its files. */
@injectable()
export class CodeDnaWorkspace {

    @inject(WorkspaceService) protected readonly workspace: WorkspaceService;
    @inject(EditorManager) protected readonly editors: EditorManager;

    async repositoryPath(): Promise<string | undefined> {
        const roots = await this.workspace.roots;
        return roots.length ? FileUri.fsPath(roots[0].resource) : undefined;
    }

    async openRepositoryFile(repository: string, relativePath: string): Promise<void> {
        await this.editors.open(FileUri.create(repository).resolve(relativePath));
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
