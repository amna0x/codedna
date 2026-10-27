import { AnalysisJob, AnalysisOperation, CodeDnaService } from '../common/codedna-protocol';

/** Display core stages only. No percentage, risk calculation or fetch-only cancellation. */
export async function waitForAnalysis<T>(
    service: CodeDnaService, operation: AnalysisOperation, payload: object,
    current: () => boolean, progress: (job: AnalysisJob) => void,
    pause: () => Promise<void> = () => new Promise(resolve => setTimeout(resolve, 500))
): Promise<T | undefined> {
    let job = await service.startAnalysis(operation, payload);
    while (true) {
        if (!current()) {
            if (job.state === 'queued' || job.state === 'running') {
                await service.cancelAnalysis(job.id);
            }
            return undefined;
        }
        progress(job);
        if (job.state === 'cancelled') { return undefined; }
        if (job.state === 'failed') { throw new Error(job.error || 'Analysis failed.'); }
        if (job.state === 'completed') {
            if (!job.result) { throw new Error('Analysis completed without a result.'); }
            return job.result as T;
        }
        await pause();
        job = await service.analysisJob(job.id);
    }
}
