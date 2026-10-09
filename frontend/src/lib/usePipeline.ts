import { useEffect, useState } from 'react';
import { ApiError } from './api';
import type { DealApi } from './api';
import type { DealList } from './contracts';
import { matchPipeline, rankedDeals } from './phase3';
import type { Priorities } from './phase3';

export type PipelineState = { status: 'loading' | 'ready' | 'error'; list: DealList | null; priorities: Priorities | null; error: ApiError | null };

/** GET-only pipeline snapshot for the agent and deal table. Ranking failure keeps the CRM list usable. */
export function usePipeline(api: DealApi, refresh = 0): PipelineState {
  const [state, setState] = useState<PipelineState>({ status: 'loading', list: null, priorities: null, error: null });
  useEffect(() => {
    const controller = new AbortController();
    setState({ status: 'loading', list: null, priorities: null, error: null });
    (async () => {
      try {
        const list = await api.list(controller.signal);
        let priorities: Priorities | null = null, error: ApiError | null = null;
        if (api.priorities) {
          try { priorities = await api.priorities(controller.signal); matchPipeline(list, priorities); }
          catch (e) { if (controller.signal.aborted) return; priorities = null; error = e instanceof ApiError ? e : new ApiError(502, 'The priority response is invalid.'); }
        }
        if (!controller.signal.aborted) setState({ status: 'ready', list, priorities, error });
      } catch (e) {
        if (!controller.signal.aborted) setState({ status: 'error', list: null, priorities: null, error: e instanceof ApiError ? e : new ApiError(0, 'Deals could not be loaded.') });
      }
    })();
    return () => controller.abort();
  }, [api, refresh]);
  return state;
}

export function orderedDeals(state: PipelineState) {
  if (!state.list) return [];
  return state.priorities ? rankedDeals(state.list, state.priorities) : state.list.items.map(d => ({ ...d, rank: null }));
}
