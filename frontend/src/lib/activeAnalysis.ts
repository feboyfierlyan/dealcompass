// Which analysis is on screen, and its honest label. One version drives the action, owner, target,
// approvals, unknowns, follow-up plan, cited sources and graph paths. Type-only imports for node --test.
import type { Recommendation } from './contracts';
import type { AnalysisEntry, AnalysisMeta } from './analysis';
import type { EvidencePath, PriorityItem } from './phase3';

export type AnalysisStatus = 'checking' | 'hybrid' | 'replay' | 'rules' | 'fallback' | 'more_info' | 'none';
export const statusLabel: Record<AnalysisStatus, string> = {
  checking: 'Checking context…', hybrid: 'Rules + Jev', replay: 'Rules + Jev · recorded replay', rules: 'Rules-based',
  fallback: 'Jev unavailable · rules shown', more_info: 'More information needed', none: 'No analysis yet',
};

export type ActiveAnalysis = {
  source: 'analysis' | 'priority' | null;
  recommendation: Recommendation | null;
  meta: AnalysisMeta | null;
  /** Graph paths of the displayed version only. Ranking paths are never shown for a Jev result. */
  paths: EvidencePath[];
  pathLimitations: string[];
  /** Gate text of the displayed version (same wording as the ranking gate factor). */
  gate: string | null;
  status: AnalysisStatus;
  label: string;
  refreshing: boolean;
  error: Error | null;
  /** Identifies the version on screen; changes whenever the content would. */
  versionKey: string;
};

function priorityGate(priority: PriorityItem) {
  const value = priority.factors.find(f => f.name === 'gate_approval_izin')?.value;
  return typeof value === 'string' && value.trim() ? value : null;
}

export function activeAnalysis({ dealId, priority, entry, service }: {
  dealId: string; priority: PriorityItem | null; entry: AnalysisEntry | null; service: boolean;
}): ActiveAnalysis {
  const validPriority = priority && priority.deal_id === dealId && priority.recommendation.deal_id === dealId ? priority : null;
  const envelope = entry?.envelope && entry.envelope.deal_id === dealId && entry.envelope.recommendation.deal_id === dealId ? entry.envelope : null;
  const refreshing = !!entry?.refreshing, error = entry?.error ?? null;
  if (envelope) {
    const m = envelope.analysis;
    const status: AnalysisStatus = m.analysis_status === 'insufficient_evidence' ? 'more_info'
      : m.outcome === 'jev_applied' ? (m.engine_mode === 'replay' ? 'replay' : 'hybrid')
      : m.outcome === 'jev_unavailable' ? 'fallback' : 'rules';
    return { source: 'analysis', recommendation: envelope.recommendation, meta: m, paths: m.evidence_paths, pathLimitations: m.path_limitations,
      gate: m.gate, status, label: statusLabel[status], refreshing, error, versionKey: `analysis:${m.analysis_id}:${m.generated_at}` };
  }
  const waiting = service && (!entry || entry.status === 'running');
  const status: AnalysisStatus = waiting ? 'checking'
    : !validPriority ? 'none'
    : entry?.status === 'failed' ? 'fallback'
    : validPriority.analysis_status === 'insufficient_evidence' ? 'more_info' : 'rules';
  return { source: validPriority ? 'priority' : null, recommendation: validPriority?.recommendation ?? null, meta: null,
    paths: validPriority?.evidence_paths ?? [], pathLimitations: validPriority?.limitations ?? [], gate: validPriority ? priorityGate(validPriority) : null,
    status, label: statusLabel[status], refreshing, error, versionKey: validPriority ? `priority:${dealId}` : `none:${dealId}` };
}

const time = (iso: string) => new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Jakarta' }).format(new Date(iso)) + ' WIB';

/** Plain provenance for the disclosure. A saved result is never described as newly generated. */
export function provenance(view: ActiveAnalysis): string[] {
  const m = view.meta;
  if (!m) return [view.source === 'priority' ? 'From the priority ranking (rules). The ranking order never changes because of an analysis.' : 'No analysis is displayed.'];
  const lines = [
    m.cache === 'fresh' ? `Generated ${time(m.generated_at)} for this deal context.`
      : m.cache === 'hit' ? `Saved analysis from ${time(m.generated_at)}. No new provider request was made.`
      : m.cache === 'shared' ? `Joined an analysis already in progress (generated ${time(m.generated_at)}).`
      : `Rules computed ${time(m.generated_at)}.`,
    m.outcome === 'jev_applied' ? `Jev read the customer messages and precedents (${m.provider_requests} request${m.provider_requests === 1 ? '' : 's'}${m.model ? `, ${m.model}` : ''}); rules checked the result and kept every approval and consent condition.`
      : m.outcome === 'jev_unavailable' ? `Jev was not used (${m.fallback_reason ?? 'unknown reason'}${m.provider_requests ? `; ${m.provider_requests} request${m.provider_requests === 1 ? '' : 's'} made` : ''}). The rules-based analysis is shown.`
      : m.outcome === 'not_eligible' ? 'Not enough customer conversation to analyse with Jev. No provider request was made.'
      : 'Rules-based analysis. Jev is not enabled on this server.',
  ];
  if (m.engine_mode === 'replay') lines.push('Recorded replay of earlier Jev answers, not a live provider call.');
  return lines;
}
