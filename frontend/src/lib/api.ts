import { isContext, isDealList, isRecommendation } from './contracts';
import type { DealContext, DealList, Recommendation } from './contracts';
import { isPriorities, isPipelineDiagnostic, isDealDiagnostic } from './phase3';
import type { Priorities, PipelineDiagnostic, Diagnostic } from './phase3';
import { isAnalysisEnvelope } from './analysis';
import type { AnalysisEnvelope } from './analysis';

export class ApiError extends Error {
  constructor(public status: number, message: string, public code?: string) { super(message); this.name = 'ApiError'; }
}
export interface DealApi {
  list(signal: AbortSignal): Promise<DealList>;
  context(id: string, signal: AbortSignal): Promise<DealContext>;
  analyze(id: string, signal: AbortSignal): Promise<Recommendation>;
  /** Active analysis with provenance. refresh=true only from the explicit Refresh analysis button. */
  analysis?(id: string, refresh: boolean, signal: AbortSignal): Promise<AnalysisEnvelope>;
  priorities?(signal: AbortSignal): Promise<Priorities>;
  diagnostics?(signal: AbortSignal): Promise<PipelineDiagnostic>;
  diagnostic?(id: string, signal: AbortSignal): Promise<Diagnostic>;
}
async function request<T>(path: string, signal: AbortSignal, valid: (v: unknown) => v is T, method = 'GET'): Promise<T> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  signal.addEventListener('abort', abort, { once: true });
  if (signal.aborted) abort();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 20000);
  try {
    const response = await fetch(path, { method, signal: controller.signal, headers: { Accept: 'application/json' } });
    if (!response.ok) {
      let code: string | undefined;
      try { code = (await response.json())?.detail?.code; } catch { /* Non-JSON error: keep the HTTP status. */ }
      if (response.status === 404 && code === 'DEAL_NOT_FOUND') throw new ApiError(404, 'This deal was not found in the dataset.', code);
      if (response.status === 404 && /\/analysis(?:\?|$)/.test(path)) {
        throw new ApiError(404, 'The analysis endpoint is missing from the running backend. Restart the backend from the latest project version, then refresh the analysis.');
      }
      throw new ApiError(response.status, `The service returned HTTP ${response.status}.`);
    }
    let data: unknown;
    try { data = await response.json(); } catch { throw new ApiError(502, 'The service response is not valid JSON.'); }
    if (!valid(data)) throw new ApiError(502, 'The service response does not match the v1 data contract.');
    return data;
  } catch (error) {
    if (signal.aborted) throw new DOMException('Cancelled', 'AbortError');
    if (timedOut) throw new ApiError(408, 'The service did not respond within 20 seconds. Try again.');
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'Connection lost. Check your connection and retry.');
  } finally {
    clearTimeout(timer);
    signal.removeEventListener('abort', abort);
  }
}
export const liveApi: DealApi = {
  priorities: signal => request('/api/pipeline/priorities', signal, isPriorities),
  diagnostics: signal => request('/api/pipeline/initial-analysis', signal, isPipelineDiagnostic),
  diagnostic: async (id, signal) => {
    const data = await request(`/api/deals/${encodeURIComponent(id)}/initial-analysis`, signal, isDealDiagnostic);
    if (data.deal_id !== id) throw new ApiError(502, 'The findings do not match the selected deal.');
    return data;
  },
  list: signal => request('/api/deals', signal, isDealList),
  context: async (id, signal) => {
    const data = await request(`/api/deals/${encodeURIComponent(id)}`, signal, isContext);
    if (data.deal.deal_id !== id) throw new ApiError(502, 'The detail response does not match the selected deal.');
    return data;
  },
  analyze: async (id, signal) => {
    const data = await request(`/api/deals/${encodeURIComponent(id)}/analyze`, signal, isRecommendation, 'POST');
    if (data.deal_id !== id) throw new ApiError(502, 'The analysis does not match the selected deal.');
    return data;
  },
  analysis: async (id, refresh, signal) => {
    const data = await request(`/api/deals/${encodeURIComponent(id)}/analysis${refresh ? '?refresh=true' : ''}`, signal, isAnalysisEnvelope, 'POST');
    if (data.deal_id !== id) throw new ApiError(502, 'The analysis does not match the selected deal.');
    return data;
  },
};
