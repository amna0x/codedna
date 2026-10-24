import { ProgressService } from '@theia/core/lib/common/progress-service';

/**
 * Show a notification while a long core call runs. The core reports no
 * intermediate steps, so the message shows the stage name and elapsed time
 * only; it never invents a percentage.
 */
export async function withProgress<T>(progress: ProgressService, text: string, task: () => Promise<T>): Promise<T> {
    const handle = await progress.showProgress({ text, options: { location: 'notification' } });
    const started = Date.now();
    const timer = setInterval(() => handle.report({ message: `${Math.round((Date.now() - started) / 1000)} s` }), 1000);
    try {
        return await task();
    } finally {
        clearInterval(timer);
        handle.cancel();
    }
}
