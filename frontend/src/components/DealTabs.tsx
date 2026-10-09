import { useId } from 'react';
import { ApiError } from '../lib/api';
import type { DealContext } from '../lib/contracts';
import type { EvidencePath, PriorityItem } from '../lib/phase3';
import { dateLabel } from '../lib/format';
import { evidenceTitle, gateSummary, interactionMeta, obstacleEvidence } from '../lib/present';
import { provenance } from '../lib/activeAnalysis';
import type { ActiveAnalysis } from '../lib/activeAnalysis';
import { ActionOverview } from './ActionOverview';
import { ExplanationGroups, PrecedentList, RecommendationSources, UnknownList } from './AnalysisReport';
import { EvidencePaths, PriorityRationale } from './Phase3Panels';
import { ErrorNotice } from './Notice';
import { Icon } from './Icon';

type OpenEvidence = (id: string) => void;
export type RankingState = 'loading' | 'ready' | 'error' | 'unavailable';

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

export function ActionTab({ context, priority, rankingState, view, fixture, snapshot, canRefresh, onEvidence, onReasons, onShowPaths, onRefresh }: {
  context: DealContext | null; priority: PriorityItem | null; rankingState: RankingState; view: ActiveAnalysis; fixture: boolean; snapshot: string | null;
  canRefresh: boolean; onEvidence: OpenEvidence; onReasons: () => void; onShowPaths: () => void; onRefresh: () => void;
}) {
  const r = view.recommendation;
  const busy = view.status === 'checking' || view.refreshing;
  const failed = view.error && !view.meta;
  const status = view.refreshing ? 'Refreshing the analysis. The analysis shown is the previous version until the new one is checked.'
    : view.status === 'checking' && r ? 'Rules-based recommendation shown while the deal context is checked.'
    : view.error && view.meta ? `Refresh failed (${view.error.message}). The previous analysis is still shown.`
    : '';
  return <div className="tab-stack">
    {r ? <ActionOverview key={view.versionKey} recommendation={r} view={view} context={context} snapshot={snapshot} fixture={fixture} onEvidence={onEvidence} onReasons={onReasons} onShowPaths={onShowPaths}/>
      : (view.status === 'checking' || rankingState === 'loading') && !failed ? <div className="action-card skeleton" role="status"><span className="visually-hidden">Checking context…</span><i/><i/><i/></div>
      : <section className="action-card empty"><h3>No recommendation available yet</h3>
        <p>{rankingState === 'error' ? 'Priorities could not be loaded, so their recommendation is unavailable.' : 'Priority recommendations are unavailable in this mode.'}</p>
        {failed && view.error && <ErrorNotice error={view.error instanceof ApiError ? view.error : new ApiError(0, view.error.message)} retry={canRefresh ? onRefresh : undefined} subject="Analysis" retryLabel="Refresh analysis"/>}
      </section>}

    {(r || view.status === 'checking') && <section className="origin" aria-label="Analysis source">
      <p className="status-line small" role="status">{busy && <span className="spinner"/>}{status}</p>
      {failed && r && <p className="status-line small">Jev unavailable: {view.error!.message} Rules-based recommendation shown.</p>}
      <details className="analysis-options"><summary><Icon name="history" size={14}/>About this analysis</summary>
        <div className="origin-row">
          <div>{provenance(view).map((line, i) => <p key={i}>{line}</p>)}</div>
          {canRefresh && <button className="button tertiary" onClick={onRefresh} disabled={busy}><Icon name="refresh" size={15}/>{busy ? 'Checking…' : 'Refresh analysis'}</button>}
        </div>
        {view.meta && <dl className="tech-list compact">
          <div><dt>Analysis ID</dt><dd className="mono">{view.meta.analysis_id}</dd></div>
          <div><dt>Version</dt><dd className="mono">{view.meta.analysis_version}</dd></div>
          <div><dt>Context fingerprint</dt><dd className="mono">{view.meta.context_fingerprint}</dd></div>
        </dl>}
        <p className="note">Refreshing re-checks only this deal. The priority order is never changed by an analysis.</p>
      </details>
    </section>}
  </div>;
}

export function ReasonsTab({ priority, view, context, onEvidence, onEdge, onShowPath }: { priority: PriorityItem | null; view: ActiveAnalysis; context: DealContext; onEvidence: OpenEvidence; onEdge: (id: string) => void; onShowPath: (path: EvidencePath) => void }) {
  const r = view.recommendation;
  return <div className="tab-stack">
    <WhyBlock priority={priority} context={context} rankingState={priority ? 'ready' : 'unavailable'} onEvidence={onEvidence}/>
    {r && <p className="version-note">Sources, paths and reasoning below belong to the analysis shown: <strong>{view.label}</strong>{view.meta ? <> · <span className="mono">{view.meta.analysis_id}</span></> : null}.</p>}
    {r && <RecommendationSources ids={r.evidence_ids} context={context} onEvidence={onEvidence}/>}
    {r && <PrecedentList recommendation={r} context={context} onEvidence={onEvidence}/>}
    {r && <EvidencePaths paths={view.paths} limitations={view.pathLimitations} context={context} onEvidence={onEvidence} onEdge={onEdge} onShowPath={onShowPath}/>}
    {priority ? <PriorityRationale item={priority}/> : <p className="muted">Priority reasoning is not available.</p>}
    {r && <ExplanationGroups recommendation={r}/>}
    {r && <UnknownList recommendation={r} context={context}/>}
    {!r && <p className="muted">Evidence and reasoning will appear when a recommendation is available.</p>}
  </div>;
}
