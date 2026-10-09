import { englishText } from './english';
import type { DealContext, Recommendation } from './contracts';
import { employeeFromContext, splitUnknowns } from './present';

const TITLES: Record<string, { title: string; note: string }> = {
  'kesediaan/izin kandidat referensi belum ada': { title: 'Validate a customer reference', note: 'The candidate has not confirmed willingness or contact consent. A candidate is not permission for an introduction.' },
  'identitas pengambil keputusan masih inferred': { title: 'Confirm the decision-maker', note: 'The decision-maker identity is inferred from the data. Confirm their role first.' },
  'approval VP Sales tertunda': { title: 'Request a discount decision', note: 'The discount request is not approved. VP Sales must decide and record the decision before any offer.' },
  'discovery belum dilakukan': { title: 'Discover customer needs', note: 'Confirm needs and the decision-maker before quoting. Missing discovery does not mean the deal is lost or risk-free.' },
};
const GATES: Record<string, string> = {
  'kesediaan/izin kandidat referensi belum ada': 'Contact consent unconfirmed',
  'identitas pengambil keputusan masih inferred': 'Decision-maker unconfirmed',
  'approval VP Sales tertunda': 'VP Sales approval pending',
  'discovery belum dilakukan': 'Customer needs unknown',
};

/** Presentation labels for exact gate values of the displayed analysis; never infer a gate from a deal ID. */
export function taskHeading(gate: string | null) {
  return TITLES[gate ?? ''] ?? { title: 'Prepare the next step', note: gate && gate !== 'tidak ada gate tercatat' ? gate : 'Review the proposal and its conditions before acting.' };
}

/** Short visible gate; full conditions stay in the disclosure and follow-up plan. */
export function gateLabel(gate: string | null, approvals: string[]) {
  if (approvals.length) return 'Approval required';
  return GATES[gate ?? ''] ?? 'Review action conditions';
}

export type BriefAnalysis = { label: string; id: string | null; generatedAt: string | null };

/** A reviewable handoff, not an email or a CRM mutation. Preserve all business conditions verbatim. */
export function buildFollowUpBrief(r: Recommendation, context: DealContext | null, snapshot: string | null, analysis: BriefAnalysis | null = null) {
  const owner = employeeFromContext(context, r.owner_id);
  const sources = [...new Set(r.evidence_ids)].map(id => {
    const e = context?.evidence.find(record => record.id === id);
    return e ? `- ${e.source_file} · ${e.source_id} · ${e.date ?? 'date unavailable'} · ${e.evidence_type} [${id}]` : `- ${id} (source unavailable)`;
  });
  return [
    `FOLLOW-UP PLAN — ${context?.deal.account_name ?? r.deal_id}`,
    `Deal: ${r.deal_id} | Data: ${snapshot ?? 'unavailable'} | Mode: ${r.engine_mode}`,
    `Analysis: ${analysis ? `${analysis.label}${analysis.id ? ` | id ${analysis.id}` : ''}${analysis.generatedAt ? ` | generated ${analysis.generatedAt}` : ''}` : 'not specified'}`,
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
