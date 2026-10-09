export type ResourceState<T> = { status: 'idle' | 'loading'; data: null; error: null } | { status: 'ready'; data: T; error: null } | { status: 'error'; data: null; error: unknown };
/** Independent endpoint lifecycle: clears stale data immediately and rejects late callbacks. */
export function createResource<T>(request: (signal: AbortSignal) => Promise<T>) {
  let state: ResourceState<T> = { status: 'idle', data: null, error: null };
  let generation = 0, controller: AbortController | null = null;
  const listeners = new Set<() => void>();
  function publish(next: ResourceState<T>) { state = next; listeners.forEach(fn => fn()); }
  return {
    getSnapshot: () => state,
    subscribe(fn: () => void) { listeners.add(fn); return () => { listeners.delete(fn); }; },
    reset() { generation++; controller?.abort(); publish({status:'idle',data:null,error:null}); },
    async run() {
      const current = ++generation; controller?.abort(); const pending = new AbortController(); controller = pending;
      publish({status:'loading',data:null,error:null});
      try { const data = await request(pending.signal); if (current === generation && !pending.signal.aborted) publish({status:'ready',data,error:null}); }
      catch (error) { if (current === generation && !pending.signal.aborted) publish({status:'error',data:null,error}); }
    },
  };
}
