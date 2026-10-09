import { englishText } from '../lib/english';
import { useState } from 'react';
import type { DealContext, Recommendation } from '../lib/contracts';
import type { ActiveAnalysis } from '../lib/activeAnalysis';
import { employeeFromContext } from '../lib/present';
import { taskHeading, gateLabel } from '../lib/planning';
import { ActionSummary } from './AnalysisReport';
import { FollowUpPlan } from './FollowUpPlan';
import { Icon } from './Icon';

/** Everything here comes from one displayed analysis version: action, owner, target, gates, sources, paths and plan. */
export function ActionOverview({ recommendation: r, view, context, snapshot, fixture, onEvidence, onReasons, onShowPaths }: {
  recommendation: Recommendation; view: ActiveAnalysis; context: DealContext | null;
  snapshot: string | null; fixture: boolean; onEvidence: (id: string) => void; onReasons: () => void; onShowPaths: () => void;
}) {
  const [planning, setPlanning] = useState(false);
  const heading = taskHeading(view.gate), owner = employeeFromContext(context, r.owner_id);
  const label = `${view.label}${fixture ? ' · fixture' : ''}`;
  return <div className="action-board">
    <section className="next-move" aria-label="Next step">
      <div className="next-move-top"><span className="eyebrow"><Icon name="target" size={15}/>Next step</span><span className={`tag analysis-status ${view.status}`}>{label}</span></div>
      <h3>{heading.title}</h3>
      <div className="move-owner" aria-label="Owner"><span className="person-avatar" aria-hidden="true">{owner?.name.split(' ').map(x => x[0]).slice(0,2).join('') ?? '—'}</span><span><strong>{owner?.name ?? r.owner_id ?? 'Not specified'}</strong></span></div>
      <div className="move-target"><span className="eyebrow">Target</span><p>{englishText(r.milestone) || 'No outcome provided by the analysis.'}</p></div>
      <details className="move-boundary"><summary><Icon name="info" size={16}/><span>{gateLabel(view.gate, r.approvals_needed)}</span><Icon name="chevron" size={14}/></summary><div><p>{heading.note}</p>{!!r.approvals_needed.length && <ul>{r.approvals_needed.map((x,i) => <li key={i}>{englishText(x)}</li>)}</ul>}</div></details>
      <div className="move-cta"><button className="button primary" onClick={() => setPlanning(true)}>Prepare follow-up<Icon name="arrow" size={18}/></button></div>
      <details className="full-proposal"><summary>Action details<Icon name="chevron" size={16}/></summary><p className="original-gate">Conditions before acting: {view.gate ?? 'Not provided'}</p><ActionSummary recommendation={r} context={context} fixture={fixture} onEvidence={onEvidence} label={view.label}/></details>
    </section>
    <nav className="proof-links" aria-label="Supporting evidence"><button className="text-button small" onClick={onReasons}><Icon name="file" size={16}/>View evidence<span className="count">{new Set(r.evidence_ids).size}</span></button><button className="text-button small" onClick={onShowPaths} disabled={!view.paths.length} title={view.paths.length ? undefined : 'No recorded graph path for this analysis'}><Icon name="graph" size={16}/>Explore relationships</button></nav>
    {planning && <FollowUpPlan recommendation={r} context={context} snapshot={snapshot} analysis={{ label: view.label, id: view.meta?.analysis_id ?? null, generatedAt: view.meta?.generated_at ?? null }} onClose={() => setPlanning(false)}/>}
  </div>;
}
