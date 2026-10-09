// Presentation-only helpers for the redesigned UI. Nothing here ranks deals, decides approvals,
// or rewrites API text: labels translate field names, and titles reuse values from source records.
// Type-only imports keep this module runnable by node --test without a build step.
import type { DealContext, Evidence, EvidenceType, GraphNode, Recommendation } from './contracts';
import type { EvidencePath, PriorityItem } from './phase3';

export const priorityKindLabel = { acceleration: 'Percepat tindak lanjut', discovery: 'Lengkapi informasi' } as const;
export const engineLabel = { rules: 'Analisis berbasis aturan', jev: 'Analisis dengan Jev', replay: 'Rekaman analisis (replay)' } as const;
export const evidenceKindLabel: Record<EvidenceType, string> = { direct: 'Langsung dari data', inferred: 'Dugaan dari hubungan data' };

export function compactRupiah(value: number): string {
  const format = (n: number) => n.toLocaleString('id-ID', { maximumFractionDigits: 1 });
  if (value >= 1e9) return `Rp${format(value / 1e9)} M`;
  if (value >= 1e6) return `Rp${format(value / 1e6)} jt`;
  return `Rp${value.toLocaleString('id-ID')}`;
}

/** Desktop shows the first API priority until the user picks; a valid user choice is never overridden. */
export function effectiveSelection({ items, ranked, userChoice }: { items: string[]; ranked: string[] | null; userChoice: string | null }): string | null {
  if (userChoice && items.includes(userChoice)) return userChoice;
  const first = ranked?.find(id => items.includes(id));
  return first ?? null;
}

export type SessionSnapshot = { status: 'idle' | 'running' | 'received' | 'failed'; data: Recommendation | null };
/** Which recommendation is on screen. A failed or running re-analysis never presents old data as new. */
export function recommendationView({ dealId, priority, session, preferred }: { dealId: string; priority: PriorityItem | null; session: SessionSnapshot; preferred: 'priority' | 'session' }) {
  const fromPriority = priority && priority.deal_id === dealId && priority.recommendation.deal_id === dealId ? priority.recommendation : null;
  const fromSession = session.status === 'received' && session.data && session.data.deal_id === dealId ? session.data : null;
  const source: 'priority' | 'session' | null = preferred === 'session' && fromSession ? 'session' : fromPriority ? 'priority' : fromSession ? 'session' : null;
  return {
    source,
    recommendation: source === 'session' ? fromSession : source === 'priority' ? fromPriority : null,
    hasPriority: !!fromPriority,
    hasSession: !!fromSession,
    sessionStatus: session.status,
  };
}

export function nextTabIndex(key: string, index: number, count: number): number | null {
  if (key === 'ArrowRight') return (index + 1) % count;
  if (key === 'ArrowLeft') return (index + count - 1) % count;
  if (key === 'Home') return 0;
  if (key === 'End') return count - 1;
  return null;
}

/** Unknowns added by this analysis (not inherited from the context) stay next to the action. */
export function splitUnknowns(recommendation: Recommendation, context: DealContext | null) {
  const inherited = new Set(context?.unknowns ?? []);
  return {
    specific: recommendation.unknowns.filter(item => !inherited.has(item)),
    all: [...new Set([...recommendation.unknowns, ...(context?.unknowns ?? [])])],
  };
}

function row(evidence: Evidence): Record<string, unknown> | null {
  try {
    const value: unknown = JSON.parse(evidence.excerpt);
    return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
  } catch { return null; }
}
const fileName = (evidence: Evidence) => evidence.source_file.split('/').pop() ?? evidence.source_file;
const text = (data: Record<string, unknown> | null, key: string) => {
  const value = data?.[key];
  return typeof value === 'string' && value.trim() ? value.trim() : null;
};

/** Owner name only from the employees.csv row whose employee_id equals the owner ID. */
export function employeeFromContext(context: DealContext | null, id: string | null) {
  if (!context || !id) return null;
  for (const evidence of context.evidence) {
    if (fileName(evidence) !== 'employees.csv' || evidence.source_id !== id) continue;
    const data = row(evidence);
    const name = text(data, 'nama');
    if (data?.employee_id === id && name) return { id, name, title: text(data, 'jabatan'), evidenceId: evidence.id };
  }
  return null;
}

const FILE_LABEL: Record<string, string> = {
  'interactions.jsonl': 'Interaksi', 'decision_log.csv': 'Keputusan', 'crm_deals.csv': 'Data deal', 'crm_accounts.csv': 'Data akun',
  'crm_contacts.csv': 'Kontak', 'contact_employment_history.csv': 'Riwayat kerja', 'employees.csv': 'Karyawan', 'features.csv': 'Fitur',
  'feature_usage_monthly.csv': 'Pemakaian fitur bulanan', 'product_usage_daily.csv': 'Ringkasan pemakaian harian', 'support_tickets.csv': 'Tiket dukungan',
  'contracts_billing.csv': 'Kontrak', 'outlets.csv': 'Outlet', 'bugs.csv': 'Bug', 'releases.csv': 'Rilis',
};
const INTERACTION_LABEL: Record<string, string> = { email: 'Email', email_internal: 'Email internal', catatan_meeting: 'Catatan meeting' };

/** Human heading for a record, built only from fields already in the record. Falls back to IDs. */
export function evidenceTitle(evidence: Evidence): { kind: string; title: string } {
  const file = fileName(evidence), data = row(evidence), t = (key: string) => text(data, key);
  const kind = FILE_LABEL[file] ?? file;
  const join = (...parts: (string | null)[]) => parts.filter(Boolean).join(' · ');
  switch (file) {
    case 'interactions.jsonl': return { kind: INTERACTION_LABEL[t('tipe') ?? ''] ?? kind, title: t('subjek') ?? evidence.source_id };
    case 'decision_log.csv': return { kind, title: join(t('decision_id') ?? evidence.source_id, t('keputusan'), t('nilai')) };
    case 'crm_accounts.csv': return { kind, title: t('nama') ? `${t('nama')} (${evidence.source_id})` : evidence.source_id };
    case 'crm_contacts.csv': return { kind, title: join(t('nama') ?? evidence.source_id, t('jabatan_saat_ini')) };
    case 'employees.csv': return { kind, title: join(t('nama') ?? evidence.source_id, t('jabatan')) };
    case 'contact_employment_history.csv': return { kind, title: join(t('contact_id'), t('jabatan'), t('organisasi')) || evidence.source_id };
    case 'features.csv': return { kind, title: join(t('feature_id') ?? evidence.source_id, t('nama')) };
    case 'support_tickets.csv': return { kind, title: join(t('ticket_id') ?? evidence.source_id, t('judul'), t('status')) };
    case 'crm_deals.csv': return { kind, title: join(t('deal_id') ?? evidence.source_id, t('stage')) };
    case 'feature_usage_monthly.csv': {
      const users = data?.pengguna_aktif;
      const count = typeof users === 'string' && users.trim() !== '' ? `${users} pengguna aktif` : typeof users === 'number' ? `${users} pengguna aktif` : 'pengguna aktif tidak tercatat';
      return { kind, title: join(t('feature_id'), t('bulan'), t('account_id'), count) };
    }
    default: return { kind, title: evidence.source_id };
  }
}

/** Sender/recipient metadata for interaction records, copied from the record. */
export function interactionMeta(evidence: Evidence) {
  if (fileName(evidence) !== 'interactions.jsonl') return null;
  const data = row(evidence);
  return { from: text(data, 'dari'), to: text(data, 'ke'), message: text(data, 'isi') };
}

const RELATION: Record<string, string> = {
  deal_for: 'deal untuk akun', interaction_for: 'interaksi dengan akun', owned_by: 'dipegang oleh', sent_to: 'dikirim ke',
  sent_from: 'dikirim dari', current_email_identity: 'alamat email milik', possible_historical_email_identity: 'kemungkinan alamat email lama milik',
  participant: 'diikuti oleh', replies_to: 'membalas', mentions: 'menyebut', possibly_mentions_feature: 'kemungkinan menyebut fitur',
  decision_for: 'keputusan untuk akun', decision_on_deal: 'keputusan untuk deal', requested_by: 'diminta oleh', decided_by: 'diputuskan oleh',
  supported_by: 'didukung interaksi', promises_feature: 'menjanjikan fitur', employed_at: 'bekerja di',
  overlapping_employment: 'pernah bekerja di organisasi dan periode yang sama dengan', current_crm_account: 'tercatat di akun',
  crm_champion: 'champion tercatat', contract_for: 'kontrak untuk akun', contract_decision: 'kontrak berdasarkan keputusan',
  outlet_of: 'outlet milik', feature_usage_for: 'pemakaian fitur oleh akun', measures_feature: 'mengukur pemakaian fitur',
  usage_for: 'ringkasan pemakaian akun', observed_version: 'memakai versi aplikasi', ticket_for: 'tiket dari akun',
  reported_at: 'dilaporkan di outlet', reported_by: 'dilaporkan oleh', linked_bug: 'terkait bug', affects_feature: 'memengaruhi fitur',
  affects_version: 'memengaruhi versi',
};
/** Plain-language name of a relation. The original relation code is always shown next to it. */
export function relationPhrase(relation: string): string {
  if (RELATION[relation]) return RELATION[relation];
  if (relation.startsWith('candidate_precedent_')) return 'keputusan terdahulu yang mungkin relevan';
  if (relation.startsWith('related_account_')) return 'akun pelanggan yang mungkin relevan';
  return relation.replaceAll('_', ' ');
}

const NODE_TYPE: Record<string, string> = {
  deal: 'Deal', account: 'Akun', contact: 'Kontak', employee: 'Karyawan', feature: 'Fitur', bug: 'Bug', outlet: 'Outlet',
  interaction: 'Interaksi', decision: 'Keputusan', contract: 'Kontrak', ticket: 'Tiket', release: 'Rilis', organization: 'Organisasi',
  email: 'Alamat email', feature_usage: 'Pemakaian fitur', usage_summary: 'Ringkasan pemakaian',
};
export const nodeTypeLabel = (type: string) => NODE_TYPE[type] ?? type;
/** A deal node's label is its ID; name it after the account so the path reads naturally. */
export function nodeName(node: GraphNode, context: DealContext) {
  return node.id === context.deal.deal_id && node.label === node.id ? `Deal ${context.deal.account_name}` : node.label;
}

/** Reading order of an API evidence path. `forward` tells whether the original edge points along the reading order. */
export function pathSteps(path: EvidencePath, context: DealContext) {
  const nodes = new Map(context.graph.nodes.map(node => [node.id, node]));
  const edges = new Map(context.graph.edges.map(edge => [edge.id, edge]));
  return path.node_ids.map((id, i) => {
    const node = nodes.get(id);
    const edge = i > 0 ? edges.get(path.edge_ids[i - 1]) ?? null : null;
    return { id, name: node ? nodeName(node, context) : id, type: node ? nodeTypeLabel(node.type) : null, edge, forward: edge ? edge.target === id : null };
  });
}
/** Compact form with original arrow direction, e.g. DL-002 → P02 ← I0348. */
export function pathArrows(path: EvidencePath, context: DealContext) {
  return pathSteps(path, context).map((step, i) => i === 0 ? step.id : `${step.forward ? ' → ' : ' ← '}${step.id}`).join('');
}

/** Records the ranking names as the stated obstacle (structured factor evidence), interactions only. */
export function obstacleEvidence(priority: PriorityItem | null, context: DealContext | null): Evidence[] {
  if (!priority || !context) return [];
  const ids = priority.factors.find(f => f.name === 'hambatan_dinyatakan_pelanggan')?.evidence_ids ?? [];
  const byId = new Map(context.evidence.map(e => [e.id, e]));
  return ids.flatMap(id => byId.get(id) ? [byId.get(id)!] : []).filter(e => fileName(e) === 'interactions.jsonl')
    .sort((a, b) => (a.date ?? '').localeCompare(b.date ?? '') || a.id.localeCompare(b.id));
}
/** Ranking factor naming the gate before action, shown verbatim. */
export function gateSummary(priority: PriorityItem | null): string | null {
  const value = priority?.factors.find(f => f.name === 'gate_approval_izin')?.value;
  return typeof value === 'string' && value.trim() ? value : null;
}
/** Display order for cited records: conversations first, then decisions, then other rows; newest first. */
export function orderEvidence(records: Evidence[]): Evidence[] {
  const rank = (e: Evidence) => fileName(e) === 'interactions.jsonl' ? 0 : fileName(e) === 'decision_log.csv' ? 1 : 2;
  return [...records].sort((a, b) => rank(a) - rank(b) || (b.date ?? '').localeCompare(a.date ?? '') || a.id.localeCompare(b.id));
}
