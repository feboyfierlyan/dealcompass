export const rupiah = (value: number) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value);
export function dateLabel(value: string | null) {
  if (!value) return 'Date unavailable';
  const date = new Date(value.length === 10 ? `${value}T00:00:00Z` : value);
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Jakarta' }).format(date);
}
// CRM list status, shown only in technical details: the CRM does not store analysis results.
export const statusLabel = { not_analyzed: 'Not analyzed', ready: 'Analysis available', insufficient_evidence: 'Insufficient evidence' };
export const kindLabel = { direct: 'Direct from source', inferred: 'Inferred from relationships' };
