import { englishText } from './english';
import type { DealContext, Recommendation } from './contracts';
import type { PriorityItem } from './phase3';
import { employeeFromContext, gateSummary, splitUnknowns } from './present';

/** Presentation labels for exact API gate values; never infer a gate from a deal ID. */
export function taskHeading(priority: PriorityItem | null, source: 'priority' | 'session' | null) {
  if (source !== 'priority') return { title: 'Prepare the next step', note: 'Review the proposal and its conditions before acting.' };
  const labels: Record<string, { title: string; note: string }> = {
    'kesediaan/izin kandidat referensi belum ada': { title: 'Validate a customer reference', note: 'The candidate has not confirmed willingness or contact consent. A candidate is not permission for an introduction.' },
    'identitas pengambil keputusan masih inferred': { title: 'Confirm the decision-maker', note: 'The decision-maker identity is inferred from the data. Confirm their role first.' },
    'approval VP Sales tertunda': { title: 'Request a discount decision', note: 'The discount request is not approved. VP Sales must decide and record the decision before any offer.' },
    'discovery belum dilakukan': { title: 'Discover customer needs', note: 'Confirm needs and the decision-maker before quoting. Missing discovery does not mean the deal is lost or risk-free.' },
  };
  return labels[gateSummary(priority) ?? ''] ?? { title: 'Prepare the next step', note: gateSummary(priority) ?? 'Conditions have not been summarized. Read the full proposal before proceeding.' };
}

/** Short visible gate; full conditions stay in the disclosure and follow-up plan. */
export function gateLabel(priority: PriorityItem | null, source: 'priority' | 'session' | null, approvals: string[]) {
  if (approvals.length) return 'Approval required';
  if (source !== 'priority') return 'Review action conditions';
  const labels: Record<string, string> = {
    'kesediaan/izin kandidat referensi belum ada': 'Contact consent unconfirmed',
    'identitas pengambil keputusan masih inferred': 'Decision-maker unconfirmed',
    'approval VP Sales tertunda': 'VP Sales approval pending',
    'discovery belum dilakukan': 'Customer needs unknown',
  };
  return labels[gateSummary(priority) ?? ''] ?? 'Review action conditions';
}

/** A reviewable handoff, not an email or a CRM mutation. Preserve all business conditions verbatim. */
export function buildFollowUpBrief(r: Recommendation, context: DealContext | null, snapshot: string | null) {
  const owner = employeeFromContext(context, r.owner_id);
  const sources = [...new Set(r.evidence_ids)].map(id => {
    const e = context?.evidence.find(record => record.id === id);
    return e ? `- ${e.source_file} · ${e.source_id} · ${e.date ?? 'date unavailable'} · ${e.evidence_type} [${id}]` : `- ${id} (source unavailable)`;
  });
  return [
    `FOLLOW-UP PLAN — ${context?.deal.account_name ?? r.deal_id}`,
    `Deal: ${r.deal_id} | Data: ${snapshot ?? 'unavailable'} | Mode: ${r.engine_mode}`,
    'Draft for review. Not sent, not saved to CRM, and not approval.',
    `\nOWNER\n${owner ? `${owner.name} (${owner.id})` : r.owner_id ?? 'Not specified'}`,
    `\nPROPOSED ACTION\n${englishText(r.action)}`,
    `\nEXPECTED OUTCOME\n${englishText(r.milestone) || 'Not specified'}`,
    `\nREQUIRED APPROVALS\n${r.approvals_needed.length ? r.approvals_needed.map(x => `- ${englishText(x)}`).join('\n') : 'Not listed. This does not mean the action is approved.'}`,
    `\nSTILL TO CONFIRM\n${splitUnknowns(r, context).all.map(x => `- ${englishText(x)}`).join('\n') || 'Not provided; not confirmation of no risk.'}`,
    `\nHISTORICAL DECISIONS\n${r.precedent_ids.join(', ') || 'Not cited by the recommendation.'}\nPrecedent is not approval for this deal.`,
    `\nCITED SOURCES\n${sources.join('\n') || 'Not provided.'}`,
    `\nORIGINAL ANALYSIS — original language\n${[r.action, r.milestone, ...r.approvals_needed, ...splitUnknowns(r, context).all].join('\n')}`,
  ].join('\n');
}
