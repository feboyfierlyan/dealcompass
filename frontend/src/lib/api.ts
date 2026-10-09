import { isContext, isDealList, isRecommendation } from './contracts';
import type { DealContext, DealList, Recommendation } from './contracts';

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'ApiError'; }
}
export interface DealApi {
  list(signal: AbortSignal): Promise<DealList>;
  context(id: string, signal: AbortSignal): Promise<DealContext>;
  analyze(id: string, signal: AbortSignal): Promise<Recommendation>;
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
    if (!response.ok) throw new ApiError(response.status, `Layanan mengembalikan HTTP ${response.status}.`);
    let data: unknown;
    try { data = await response.json(); } catch { throw new ApiError(502, 'Respons layanan bukan JSON yang valid.'); }
    if (!valid(data)) throw new ApiError(502, 'Respons layanan belum sesuai kontrak data v1.');
    return data;
  } catch (error) {
    if (signal.aborted) throw new DOMException('Dibatalkan', 'AbortError');
    if (timedOut) throw new ApiError(408, 'Layanan belum merespons dalam 20 detik. Coba lagi.');
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'Koneksi ke layanan terputus. Periksa koneksi lalu coba lagi.');
  } finally {
    clearTimeout(timer);
    signal.removeEventListener('abort', abort);
  }
}
export const liveApi: DealApi = {
  list: signal => request('/api/deals', signal, isDealList),
  context: async (id, signal) => {
    const data = await request(`/api/deals/${encodeURIComponent(id)}`, signal, isContext);
    if (data.deal.deal_id !== id) throw new ApiError(502, 'Detail yang diterima tidak sesuai deal yang dipilih.');
    return data;
  },
  analyze: async (id, signal) => {
    const data = await request(`/api/deals/${encodeURIComponent(id)}/analyze`, signal, isRecommendation, 'POST');
    if (data.deal_id !== id) throw new ApiError(502, 'Analisis yang diterima tidak sesuai deal yang dipilih.');
    return data;
  },
};
