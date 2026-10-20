import { ContainerModule } from '@theia/core/shared/inversify';
import { ConnectionHandler, RpcConnectionHandler } from '@theia/core/lib/common/messaging';
import { BackendApplicationContribution } from '@theia/core/lib/node';
import { CODEDNA_SERVICE_PATH, CodeDnaService } from '../common/codedna-protocol';
import { CodeDnaServiceImpl } from './codedna-service-impl';

export default new ContainerModule(bind => {
    bind(CodeDnaServiceImpl).toSelf().inSingletonScope();
    bind(CodeDnaService).toService(CodeDnaServiceImpl);
    bind(BackendApplicationContribution).toService(CodeDnaServiceImpl);
    bind(ConnectionHandler).toDynamicValue(ctx =>
        new RpcConnectionHandler(CODEDNA_SERVICE_PATH, () => ctx.container.get<CodeDnaService>(CodeDnaService))
    ).inSingletonScope();
});
