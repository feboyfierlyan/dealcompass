export const rupiah = (value: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value);
export function dateLabel(value: string | null) {
  if (!value) return 'Tanggal belum tersedia';
  const date = new Date(value.length === 10 ? `${value}T00:00:00Z` : value);
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Jakarta' }).format(date);
}
// CRM list status, shown only in technical details: the CRM does not store analysis results.
export const statusLabel = { not_analyzed: 'Belum dianalisis', ready: 'Analisis tersedia', insufficient_evidence: 'Bukti belum cukup' };
export const kindLabel = { direct: 'Langsung dari data', inferred: 'Dugaan dari hubungan data' };
