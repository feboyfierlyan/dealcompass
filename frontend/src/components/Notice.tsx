import { ApiError } from '../lib/api';
import { Icon } from './Icon';

/** Error/unavailable message that names the problem and offers the recovery. */
export function ErrorNotice({ error, retry, subject = 'Data', retryLabel = 'Coba lagi' }: { error: ApiError; retry?: () => void; subject?: string; retryLabel?: string }) {
  const title = error.status === 501 ? `${subject} belum tersedia` : error.status === 404 ? 'Deal tidak ditemukan' : error.status === 408 ? `${subject}: waktu tunggu habis` : `${subject} belum dapat dimuat`;
  const message = error.status === 501 ? 'Layanan belum menyediakan hasil ini. Coba lagi setelah tersedia.' : error.status === 404 ? 'Deal ini tidak ditemukan oleh layanan. Muat ulang data atau pilih deal lain.' : error.message;
  return <div className={`notice ${error.status === 501 ? 'pending' : 'error'}`} role={error.status === 501 ? 'status' : 'alert'}><Icon name="alert" size={18}/><div><strong>{title}</strong><p>{message}</p></div>{retry && <button className="button secondary small" onClick={retry}><Icon name="refresh" size={15}/>{retryLabel}</button>}</div>;
}
export const asApiError = (error: unknown, fallback: string) => error instanceof ApiError ? error : new ApiError(502, error instanceof Error ? error.message : fallback);
