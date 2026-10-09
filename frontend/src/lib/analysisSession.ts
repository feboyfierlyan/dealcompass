import type { Recommendation } from './contracts';

export type AnalysisState =
  | { status: 'idle' | 'running'; data: null; error: null }
  | { status: 'received'; data: Recommendation; error: null }
  | { status: 'failed'; data: null; error: unknown };

// Request lifecycle only. It never changes business status or measures evidence sufficiency.
export function createAnalysisSession(request: (signal: AbortSignal) => Promise<Recommendation>) {
  let state: AnalysisState = { status: 'idle', data: null, error: null };
  let generation = 0;
  let controller: AbortController | null = null;
  const listeners = new Set<() => void>();
  function publish(next: AnalysisState) { state = next; listeners.forEach(listener => listener()); }
  return {
    getSnapshot: () => state,
    subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; },
    reset() {
      generation++; controller?.abort(); controller = null;
      publish({ status: 'idle', data: null, error: null });
    },
    async run() {
      const current = ++generation;
      controller?.abort();
      const pending = new AbortController(); controller = pending;
      publish({ status: 'running', data: null, error: null });
      try {
        const data = await request(pending.signal);
        if (generation === current && !pending.signal.aborted) publish({ status: 'received', data, error: null });
      } catch (error) {
        if (generation === current && !pending.signal.aborted) publish({ status: 'failed', data: null, error });
      }
    },
  };
}
