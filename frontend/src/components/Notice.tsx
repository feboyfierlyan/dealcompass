import { ApiError } from '../lib/api';
import { Icon } from './Icon';

/** Error/unavailable message that names the problem and offers the recovery. */
export function ErrorNotice({ error, retry, subject = 'Data', retryLabel = 'Retry' }: { error: ApiError; retry?: () => void; subject?: string; retryLabel?: string }) {
  const title = error.status === 501 ? `${subject} unavailable` : error.status === 404 ? 'Deal not found' : error.status === 408 ? `${subject}: request timed out` : `${subject} could not be loaded`;
  const message = error.status === 501 ? 'The service does not provide this result yet. Try again later.' : error.status === 404 ? 'The service could not find this deal. Refresh or select another deal.' : error.message;
  return <div className={`notice ${error.status === 501 ? 'pending' : 'error'}`} role={error.status === 501 ? 'status' : 'alert'}><Icon name="alert" size={18}/><div><strong>{title}</strong><p>{message}</p></div>{retry && <button className="button secondary small" onClick={retry}><Icon name="refresh" size={15}/>{retryLabel}</button>}</div>;
}
export const asApiError = (error: unknown, fallback: string) => error instanceof ApiError ? error : new ApiError(502, error instanceof Error ? error.message : fallback);
