import { englishText } from '../lib/english';
import { useEffect, useId, useRef, useState } from 'react';
import type { DealContext, Recommendation } from '../lib/contracts';
import { employeeFromContext, splitUnknowns } from '../lib/present';
import { buildFollowUpBrief } from '../lib/planning';
import type { BriefAnalysis } from '../lib/planning';
import { Icon } from './Icon';

/** Native modal isolates a single preparation task. Copying never marks business work done. */
export function FollowUpPlan({ recommendation, context, snapshot, analysis = null, onClose }: {
  recommendation: Recommendation; context: DealContext | null; snapshot: string | null; analysis?: BriefAnalysis | null; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null), title = useRef<HTMLHeadingElement>(null), field = useRef<HTMLTextAreaElement>(null);
  const titleId = useId(), noteId = useId();
  const [copy, setCopy] = useState<'idle' | 'pending' | 'copied' | 'failed'>('idle');
  const brief = buildFollowUpBrief(recommendation, context, snapshot, analysis);
  const owner = employeeFromContext(context, recommendation.owner_id);
  const readable = englishText(recommendation.action).replace(/\bE\d{2,}\b/g, id => employeeFromContext(context, id)?.name ?? id);
  const unknowns = splitUnknowns(recommendation, context);
  const [showRaw, setShowRaw] = useState(false);
  useEffect(() => { if (copy === 'failed') { field.current?.focus(); field.current?.select(); } }, [copy]);
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    dialog.current?.showModal(); title.current?.focus();
    return () => { if (trigger?.isConnected) trigger.focus(); };
  }, []);
  async function copyBrief() {
    setCopy('pending');
    try { await navigator.clipboard.writeText(brief); setCopy('copied'); }
    catch { setShowRaw(true); setCopy('failed'); }
  }
  return <dialog ref={dialog} className="plan-dialog" aria-labelledby={titleId} aria-describedby={noteId}
    onKeyDown={event => {
      if (event.key !== 'Tab') return;
      const targets = [...event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled), textarea, summary, a[href], [tabindex="0"]')].filter(el => el.getClientRects().length > 0);
      const first = targets[0], last = targets[targets.length - 1];
      if (!first || !last) return;
      if (event.shiftKey && (document.activeElement === first || !targets.includes(document.activeElement as HTMLElement))) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }}
    onCancel={e => { e.preventDefault(); onClose(); }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
    <div className="plan-header"><div><h2 ref={title} id={titleId} tabIndex={-1}>Follow-up plan</h2></div><button className="icon-button" aria-label="Close follow-up plan" onClick={onClose}><Icon name="close"/></button></div>
    <p id={noteId} className="plan-note">Draft · {context?.deal.account_name ?? recommendation.deal_id} · Not sent or saved to CRM.{analysis ? ` · ${analysis.label}` : ''}</p>
    <div className="plan-body">
      <div className="plan-assignee"><Icon name="user" size={17}/><strong>{owner?.name ?? recommendation.owner_id ?? 'Owner not assigned'}</strong><span>· {snapshot ? `Data ${snapshot}` : 'Snapshot date unavailable'}</span></div>
      <section><h3>Proposed action</h3><p className="plan-action">{readable}</p></section>
      <section><h3>Expected outcome</h3><p>{englishText(recommendation.milestone) || 'Not specified'}</p></section>
      <section className="plan-conditions"><h3>Before you act</h3>{recommendation.approvals_needed.length ? <ul>{recommendation.approvals_needed.map((line,i) => <li key={i}>{englishText(line)}</li>)}</ul> : <p>No approval is listed. This does not mean the action is approved.</p>}
        {!!unknowns.specific.length && <ul>{unknowns.specific.map((line,i) => <li key={i}>{englishText(line)}</li>)}</ul>}
      </section>
      <details className="plan-export" open={showRaw} onToggle={event => setShowRaw(event.currentTarget.open)}><summary>Full text & sources</summary><label className="plan-field">Complete plan and sources<textarea ref={field} value={brief} readOnly spellCheck={false}/></label></details>
    </div>
    <div className="plan-footer"><div role="status" aria-live="polite">{copy === 'copied' ? <span className="copy-success"><Icon name="check" size={18}/>Plan copied. Follow-up has not been performed.</span> : copy === 'failed' ? 'Copy failed. Text selected; press Ctrl/Cmd+C.' : 'Copy as a working note.'}</div>
      <button className="button primary" onClick={() => void copyBrief()} disabled={copy === 'pending'}><Icon name={copy === 'copied' ? 'check' : 'file'} size={17}/>{copy === 'pending' ? 'Copying…' : copy === 'copied' ? 'Copy again' : 'Copy plan'}</button></div>
  </dialog>;
}
