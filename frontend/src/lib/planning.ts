import type { DealContext, Recommendation } from './contracts';
import type { PriorityItem } from './phase3';
import { employeeFromContext, gateSummary, splitUnknowns } from './present';

/** Presentation labels for exact API gate values; never infer a gate from a deal ID. */
export function taskHeading(priority: PriorityItem | null, source: 'priority' | 'session' | null) {
  if (source !== 'priority') return { title: 'Siapkan langkah berikutnya', note: 'Periksa usulan dan batasannya sebelum menindaklanjuti.' };
  const labels: Record<string, { title: string; note: string }> = {
    'kesediaan/izin kandidat referensi belum ada': { title: 'Validasi referensi pelanggan', note: 'Kesediaan dan izin kontak kandidat belum dikonfirmasi. Kandidat bukan izin untuk memperkenalkan.' },
    'identitas pengambil keputusan masih inferred': { title: 'Konfirmasi pengambil keputusan', note: 'Identitas pengambil keputusan masih dugaan dari data. Perannya perlu dikonfirmasi.' },
    'approval VP Sales tertunda': { title: 'Minta keputusan atas diskon', note: 'Permintaan diskon belum disetujui. VP Sales perlu memutuskan dan mencatat sebelum ada penawaran.' },
    'discovery belum dilakukan': { title: 'Gali kebutuhan pelanggan', note: 'Cari tahu kebutuhan dan pengambil keputusan sebelum menawarkan harga. Ini bukan tanda deal gagal, kalah, atau bebas risiko.' },
  };
  return labels[gateSummary(priority) ?? ''] ?? { title: 'Siapkan langkah berikutnya', note: gateSummary(priority) ?? 'Syarat tindakan belum dirangkum. Baca usulan lengkap sebelum melanjutkan.' };
}

/** A reviewable handoff, not an email or a CRM mutation. Preserve all business conditions verbatim. */
export function buildFollowUpBrief(r: Recommendation, context: DealContext | null, snapshot: string | null) {
  const owner = employeeFromContext(context, r.owner_id);
  const sources = [...new Set(r.evidence_ids)].map(id => {
    const e = context?.evidence.find(record => record.id === id);
    return e ? `- ${e.source_file} · ${e.source_id} · ${e.date ?? 'tanggal tidak tersedia'} · ${e.evidence_type} [${id}]` : `- ${id} (sumber belum tersedia)`;
  });
  return [
    `RENCANA TINDAK LANJUT — ${context?.deal.account_name ?? r.deal_id}`,
    `Deal: ${r.deal_id} | Data: ${snapshot ?? 'tidak tersedia'} | Mode: ${r.engine_mode}`,
    'Draf untuk ditinjau. Belum dikirim, belum disimpan ke CRM, dan bukan persetujuan.',
    `\nPENANGGUNG JAWAB\n${owner ? `${owner.name} (${owner.id})` : r.owner_id ?? 'Belum ditentukan'}`,
    `\nUSULAN LENGKAP\n${r.action}`,
    `\nTARGET LANGKAH BERIKUTNYA\n${r.milestone || 'Belum ditentukan'}`,
    `\nPERSETUJUAN YANG DIPERLUKAN\n${r.approvals_needed.length ? r.approvals_needed.map(x => `- ${x}`).join('\n') : 'Tidak dicantumkan. Ini tidak berarti tindakan sudah disetujui.'}`,
    `\nYANG MASIH PERLU DIPASTIKAN\n${splitUnknowns(r, context).all.map(x => `- ${x}`).join('\n') || 'Tidak dicantumkan; bukan konfirmasi bebas risiko.'}`,
    `\nKEPUTUSAN TERDAHULU\n${r.precedent_ids.join(', ') || 'Tidak dirujuk oleh saran.'}\nPreseden bukan persetujuan untuk deal ini.`,
    `\nBUKTI YANG DIRUJUK\n${sources.join('\n') || 'Belum dicantumkan.'}`,
  ].join('\n');
}
