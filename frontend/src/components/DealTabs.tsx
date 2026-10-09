import { useId } from 'react';
import { ApiError } from '../lib/api';
import type { DealContext } from '../lib/contracts';
import type { EvidencePath, PriorityItem } from '../lib/phase3';
import { dateLabel } from '../lib/format';
import { evidenceTitle, gateSummary, interactionMeta, obstacleEvidence, recommendationView } from '../lib/present';
import { ActionOverview } from './ActionOverview';
import { ExplanationGroups, PrecedentList, RecommendationSources, UnknownList } from './AnalysisReport';
import { EvidencePaths, PriorityRationale } from './Phase3Panels';
import { ErrorNotice } from './Notice';
import { Icon } from './Icon';

type OpenEvidence = (id: string) => void;
export type RankingState = 'loading' | 'ready' | 'error' | 'unavailable';
export type SessionInfo = { status: 'idle' | 'running' | 'received' | 'failed'; error: ApiError | null; receivedAt: string | null };
type View = ReturnType<typeof recommendationView>;

/** "Why this deal": the customer's own recorded words named by the ranking, plus its stated gate. */
export function WhyBlock({ priority, context, rankingState, onEvidence }: { priority: PriorityItem | null; context: DealContext | null; rankingState: RankingState; onEvidence: OpenEvidence }) {
  const titleId = useId();
  if (!priority) return <section className="why-block" aria-labelledby={titleId}><h3 id={titleId}>Why this deal</h3>
    <p className="muted">{rankingState === 'loading' ? 'Waiting for priorities…' : rankingState === 'error' ? 'Priority reasoning is unavailable because priorities could not be loaded.' : 'Priority reasoning is unavailable in this mode.'}</p></section>;
  const quotes = obstacleEvidence(priority, context);
  const gate = gateSummary(priority);
  return <section className="why-block" aria-labelledby={titleId}>
    <h3 id={titleId}>Why this deal</h3>
    {priority.priority_kind === 'discovery' && <p className="lead">There is not enough information to assess blockers. Start with discovery. This does not mean the deal is lost or risk-free.</p>}
    {quotes.map(e => {
      const meta = interactionMeta(e), { kind, title } = evidenceTitle(e);
      return <figure className="quote" key={e.id}><blockquote>{meta?.message ? `“${meta.message}”` : title}</blockquote>
        <figcaption><span>{kind} · {dateLabel(e.date)}{meta?.from ? ` · from ${meta.from}` : ''}</span><button className="link-button" onClick={() => onEvidence(e.id)}>View source {e.source_id}</button></figcaption></figure>;
    })}
    {gate && <p className="gate-line"><Icon name="flag" size={16}/><span>Original priority condition: <strong>{gate}</strong></span></p>}
  </section>;
}

export function ActionTab({ context, priority, rankingState, view, fixture, snapshot, session, onEvidence, onReasons, onShowPaths, onAnalyze, onShowVersion }: {
  context: DealContext | null; priority: PriorityItem | null; rankingState: RankingState; view: View; fixture: boolean; snapshot: string | null;
  session: SessionInfo; onEvidence: OpenEvidence; onReasons: () => void; onShowPaths: () => void; onAnalyze: () => void; onShowVersion: (v: 'priority' | 'session') => void;
}) {
  const r = view.recommendation;
  const running = session.status === 'running';
  const rerunNote = useId();
  return <div className="tab-stack">
    {r ? <ActionOverview key={`${r.deal_id}-${view.source}-${JSON.stringify(r)}`} recommendation={r} context={context} priority={priority} source={view.source} snapshot={snapshot} fixture={fixture} onEvidence={onEvidence} onReasons={onReasons} onShowPaths={onShowPaths}/>
      : rankingState === 'loading' && !running && session.status !== 'failed' ? <div className="action-card skeleton" role="status"><span className="visually-hidden">Preparing the priority recommendation</span><i/><i/><i/></div>
      : <section className="action-card empty"><h3>No recommendation available yet</h3>
        <p>{rankingState === 'error' ? 'Priorities could not be loaded, so their recommendation is unavailable.' : 'Priority recommendations are unavailable in this mode.'} You can request an analysis for this deal.</p>
        {!running && session.status !== 'failed' && <div className="action-buttons"><button className="button primary" onClick={onAnalyze}><Icon name="arrow" size={17}/>Analyze this deal</button></div>}
        {running && <p className="status-line" role="status"><span className="spinner"/>Running analysis…</p>}
        {session.status === 'failed' && session.error && <ErrorNotice error={session.error} retry={onAnalyze} subject="Analysis"/>}
      </section>}

    {r && <section className="origin" aria-label="Analysis source">
      <details className="analysis-options"><summary><Icon name="history" size={14}/>Versions & re-analysis</summary><div className="origin-row">
        <p><Icon name="history" size={16}/>{view.source === 'session'
          ? `Requested re-analysis${session.receivedAt ? ` at ${session.receivedAt}` : ''} · priority order unchanged`
          : `From priority ranking${snapshot ? ` · snapshot ${dateLabel(snapshot)}` : ''}`}</p>
        <button className="button tertiary" onClick={onAnalyze} disabled={running} aria-describedby={rerunNote}><Icon name="refresh" size={15}/>{running ? 'Running analysis…' : 'Run analysis again'}</button>
        <span id={rerunNote} className="visually-hidden">Request a new result for this deal only. Priority order stays unchanged.</span>
      </div>
      {view.hasPriority && view.hasSession && <div className="segmented" role="group" aria-label="Displayed recommendation version">
        <button aria-pressed={view.source === 'priority'} onClick={() => onShowVersion('priority')}>Priority recommendation</button>
        <button aria-pressed={view.source === 'session'} onClick={() => onShowVersion('session')}>New analysis{session.receivedAt ? ` · ${session.receivedAt}` : ''}</button>
      </div>}
      </details>
      <p className="status-line small" role="status">{running ? 'Analysis is running. The displayed recommendation has not changed.' : session.status === 'received' && view.source === 'priority' ? 'New analysis is available under Versions & re-analysis.' : ''}</p>
      {session.status === 'failed' && session.error && <ErrorNotice error={session.error} retry={onAnalyze} subject="Re-analysis"/>}
    </section>}
  </div>;
}

export function ReasonsTab({ priority, view, context, onEvidence, onEdge, onShowPath }: { priority: PriorityItem | null; view: View; context: DealContext; onEvidence: OpenEvidence; onEdge: (id: string) => void; onShowPath: (path: EvidencePath) => void }) {
  const r = view.recommendation;
  return <div className="tab-stack">

    <WhyBlock priority={priority} context={context} rankingState={priority ? 'ready' : 'unavailable'} onEvidence={onEvidence}/>
    {r && view.hasPriority && view.hasSession && <p className="version-note">Evidence below follows the <strong>{view.source === 'session' ? 'new analysis' : 'priority recommendation'}</strong>.</p>}
    {r && <RecommendationSources ids={r.evidence_ids} context={context} onEvidence={onEvidence}/>}
    {r && <PrecedentList recommendation={r} context={context} onEvidence={onEvidence}/>}
    {priority && <EvidencePaths item={priority} context={context} onEvidence={onEvidence} onEdge={onEdge} onShowPath={onShowPath}/>}
    {priority ? <PriorityRationale item={priority}/> : <p className="muted">Priority reasoning is not available.</p>}
    {r && <ExplanationGroups recommendation={r}/>}
    {r && <UnknownList recommendation={r} context={context}/>}
    {!r && <p className="muted">Evidence and reasoning will appear when a recommendation is available.</p>}
  </div>;
}
