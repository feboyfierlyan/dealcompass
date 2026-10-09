import { englishText } from '../lib/english';
import { useEffect, useId, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import { ApiError } from '../lib/api';
import type { DealApi } from '../lib/api';
import type { Deal, DealContext } from '../lib/contracts';
import { dateLabel, rupiah, statusLabel } from '../lib/format';
import { ContextGraph } from './ContextGraph';
import type { GraphPath, Selection } from './ContextGraph';
import { EvidenceDrawer, EvidenceInspector } from './EvidencePanel';
import { EvidenceBrowser } from './EvidenceBrowser';
import { Icon } from './Icon';
import { createAnalysisSession } from '../lib/analysisSession';
import type { GraphTarget } from '../lib/analysisView';
import { createResource } from '../lib/resource';
import type { ResourceState } from '../lib/resource';
import { enrichContext, mergeEvidence } from '../lib/phase3';
import type { EvidencePath, Priorities, PriorityItem, PipelineDiagnostic } from '../lib/phase3';
import { engineLabel, nextTabIndex, priorityKindLabel, recommendationView } from '../lib/present';
import { DiagnosticPanel, Methodology, PriorityFactors, Statistics } from './Phase3Panels';
import { ActionTab, ReasonsTab } from './DealTabs';
import type { RankingState } from './DealTabs';
import { ErrorNotice, asApiError } from './Notice';
import { useMedia } from '../lib/useMedia';

type Tab = 'action' | 'reasons' | 'explore';
type ExploreView = 'graph' | 'evidence' | 'method' | 'diagnostic' | 'technical';
type GraphRequest = { target?: GraphTarget; paths?: GraphPath[]; sequence: number };
const TABS: { id: Tab; label: string; icon: 'target' | 'file' | 'graph' }[] = [
  { id: 'action', label: 'Next step', icon: 'target' },
  { id: 'reasons', label: 'Evidence', icon: 'file' },
  { id: 'explore', label: 'Context graph', icon: 'graph' },
];

export function DealWorkspace({ deal, api, fixture, snapshot, priority = null, rankTotal = null, rankingState = 'unavailable', methodology = null, diagnosticState, retryDiagnostics, onBack }: {
  deal: Deal; api: DealApi; fixture: boolean; snapshot?: string; priority?: PriorityItem | null; rankTotal?: number | null; rankingState?: RankingState;
  methodology?: Priorities | null; diagnosticState?: ResourceState<PipelineDiagnostic>; retryDiagnostics?: () => void; onBack?: () => void;
}) {
  const ids = { title: useId(), drawer: useId(), graph: useId(), panel: useId() };
  const [tab, setTab] = useState<Tab>('action');
  const [explore, setExplore] = useState<ExploreView>('graph');
  const [baseContext, setContext] = useState<DealContext | null>(null);
  const [contextError, setContextError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [preferred, setPreferred] = useState<'priority' | 'session'>('priority');
  const diagnosticRequest = useMemo(() => createResource(async (signal: AbortSignal) => {
    if (!api.diagnostic) throw new ApiError(501, 'Findings are not available.');
    const result = await api.diagnostic(deal.deal_id, signal);
    if (result.account_id !== deal.account_id || result.snapshot_date !== snapshot) throw new ApiError(502, 'The findings snapshot or account does not match.');
    return result;
  }), [api, deal.deal_id, deal.account_id, snapshot]);
  const diagnosticRefresh = useSyncExternalStore(diagnosticRequest.subscribe, diagnosticRequest.getSnapshot);
  const pipelineDiagnostic = diagnosticState?.data;
  const diagnostic = diagnosticRefresh.status !== 'idle' ? diagnosticRefresh.data : pipelineDiagnostic?.deals.find(d => d.deal_id === deal.deal_id) ?? null;
  const joined = useMemo(() => {
    let context = baseContext, validPriority = null, validDiagnostic = null;
    let priorityError: Error | null = null, diagnosticError: Error | null = null;
    if (!context) return { context, validPriority, validDiagnostic, priorityError, diagnosticError };
    if (priority) try { context = enrichContext(context, priority); validPriority = priority; } catch (e) { priorityError = e as Error; }
    if (diagnostic) try { context = enrichContext(context, diagnostic); validDiagnostic = diagnostic; } catch (e) { diagnosticError = e as Error; }
    // Statistical sources may belong to a different deal. They remain readable even without a node here.
    if (pipelineDiagnostic) try {
      const statIds = new Set(pipelineDiagnostic.statistical_assessment.evidence_ids);
      context = { ...context, evidence: mergeEvidence(context.evidence, pipelineDiagnostic.deals.flatMap(d => d.evidence).filter(e => statIds.has(e.id))) };
    } catch (e) { diagnosticError = e as Error; }
    return { context, validPriority, validDiagnostic, priorityError, diagnosticError };
  }, [baseContext, priority, diagnostic, pipelineDiagnostic]);
  const context = joined.context;
  const localDiagnosticError = joined.diagnosticError ?? diagnosticRefresh.error ?? (diagnosticRefresh.status === 'idle' ? diagnosticState?.error : null);
  const loadingDiagnostic = diagnosticRefresh.status === 'loading' || (diagnosticRefresh.status === 'idle' && (diagnosticState?.status === 'loading' || diagnosticState?.status === 'idle'));

  // The analysis request runs only from an explicit button. Its lifecycle never changes ranking or CRM status.
  const session = useMemo(() => createAnalysisSession(signal => api.analyze(deal.deal_id, signal)), [api, deal.deal_id]);
  const request = useSyncExternalStore(session.subscribe, session.getSnapshot);
  const [receivedAt, setReceivedAt] = useState<string | null>(null);
  useEffect(() => {
    if (request.status === 'received') setReceivedAt(new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'Asia/Jakarta' }).format(new Date()));
    else if (request.status !== 'failed') setReceivedAt(null);
  }, [request.status]);
  const view = recommendationView({ dealId: deal.deal_id, priority: joined.validPriority, session: request, preferred });
  const sessionError = request.status === 'failed' ? request.error instanceof ApiError ? request.error : new ApiError(0, 'Analysis could not be loaded.') : null;

  const wide = useMedia('(min-width: 1800px)');
  const [selection, setSelection] = useState<Selection>(null);
  const trigger = useRef<HTMLElement | SVGElement | null>(null);
  // Focus moves after React commits the target (drawer title, map heading, tab panel or the original trigger).
  const pendingFocus = useRef<string | HTMLElement | SVGElement | null>(null);
  useEffect(() => {
    const target = pendingFocus.current;
    if (!target) return;
    pendingFocus.current = null;
    const element = typeof target === 'string' ? document.getElementById(target) : target;
    if (element && document.contains(element)) element.focus();
  });
  const [graphRequest, setGraphRequest] = useState<GraphRequest | null>(null);
  function select(next: Selection, focusDrawer = true) {
    const active = document.activeElement;
    if (next && active && active !== document.body && !active.closest('.drawer')) trigger.current = active as HTMLElement | SVGElement;
    setSelection(next);
    if (next && focusDrawer) pendingFocus.current = ids.drawer;
  }
  function closeDrawer() {
    setSelection(null);
    pendingFocus.current = trigger.current; trigger.current = null;
  }
  function showGraph(request: Omit<GraphRequest, 'sequence'>) {
    setGraphRequest(current => ({ ...request, sequence: (current?.sequence ?? 0) + 1 }));
    setTab('explore'); setExplore('graph');
    // On narrow screens the sheet would cover the map: close it and focus the map instead.
    if (request.target && wide) setSelection(request.target); else setSelection(null);
    pendingFocus.current = ids.graph;
  }
  const allPaths = (joined.validPriority?.evidence_paths ?? []) as EvidencePath[];
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setContext(null); setContextError(null); setSelection(null); setGraphRequest(null);
    session.reset(); diagnosticRequest.reset();
    api.context(deal.deal_id, controller.signal).then(data => { if (data.deal.account_id !== deal.account_id || (snapshot && data.snapshot_date !== snapshot)) throw new ApiError(502, 'The deal snapshot or account does not match.'); if (!controller.signal.aborted) setContext(data); })
      .catch(error => { if (!controller.signal.aborted) setContextError(error instanceof ApiError ? error : new ApiError(0, 'Deal data could not be loaded.')); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => { controller.abort(); session.reset(); diagnosticRequest.reset(); };
  }, [api, deal.deal_id, deal.account_id, snapshot, refresh, session, diagnosticRequest]);
  function analyze() { setPreferred('session'); setTab('action'); void session.run(); }
  function changeTab(next: Tab, focus = false) {
    setTab(next);
    if (focus) pendingFocus.current = `${ids.panel}-${next}`;
  }
  const shownDeal = context?.deal ?? deal;
  const requestLabel = { idle: 'Not requested', running: 'Running', received: 'Result received', failed: 'Failed' }[request.status];
  const drawerOpen = !!(selection && context);
  const exploreViews: { id: ExploreView; label: string }[] = [
    { id: 'graph', label: 'Relationships' }, { id: 'evidence', label: `All sources${context ? ` (${context.evidence.length.toLocaleString('en-GB')})` : ''}` },
    { id: 'method', label: 'Priority methodology' }, { id: 'diagnostic', label: 'Data findings' }, { id: 'technical', label: 'Technical details' },
  ];

  return <div className={`workspace ${drawerOpen && wide ? 'with-drawer' : ''}`}>
    <article className="detail" aria-labelledby={ids.title}>
      <div className="detail-navigation"><header className="detail-head">
        {onBack && <button className="back-button" onClick={onBack}><Icon name="back" size={18}/>All deals</button>}
        <h2 id={ids.title} tabIndex={-1}>{deal.account_name}</h2>
        <div className="detail-meta">
          {priority ? <span className="rank-pill">Priority {priority.rank}{rankTotal ? ` of ${rankTotal}` : ''}</span> : <span className="rank-pill quiet">{rankingState === 'loading' ? 'Loading priority' : 'Priority unavailable'}</span>}
          {priority?.priority_kind === 'discovery' && <span className="kind discovery">{priorityKindLabel.discovery}</span>}
          <span>Snapshot {snapshot ? dateLabel(snapshot) : 'date unavailable'}</span>
        </div>
      </header>
      <div className="tabs" role="tablist" aria-label="Deal details">{TABS.map((item, index) => <button key={item.id} id={`${ids.panel}-tab-${item.id}`} role="tab" aria-controls={tab === item.id ? `${ids.panel}-${item.id}` : undefined} aria-selected={tab === item.id} tabIndex={tab === item.id ? 0 : -1}
        onClick={() => setTab(item.id)} onKeyDown={e => { const next = nextTabIndex(e.key, index, TABS.length); if (next === null) return; e.preventDefault(); setTab(TABS[next].id); document.getElementById(`${ids.panel}-tab-${TABS[next].id}`)?.focus(); }}><Icon name={item.icon} size={17}/>{item.label}</button>)}</div>
      </div>
      <div key={tab} className="tab-panel" role="tabpanel" id={`${ids.panel}-${tab}`} aria-labelledby={`${ids.panel}-tab-${tab}`} tabIndex={-1} aria-busy={loading}>
        {tab === 'action' && <dl className="deal-metrics" aria-label="Deal summary">
          <div><dt><Icon name="flag" size={15}/>Stage</dt><dd>{englishText(shownDeal.stage)}</dd></div>
          <div><dt><Icon name="clock" size={15}/>In stage</dt><dd>{shownDeal.stage_age_days}<small> days</small></dd></div>
          <div><dt title="Annual deal potential, not realized revenue"><Icon name="target" size={15}/>Annual potential</dt><dd>{rupiah(shownDeal.annual_value)}</dd></div>
        </dl>}
        {loading && <div className="loading-line" role="status"><span className="spinner"/>Loading deal data…</div>}
        {contextError && <ErrorNotice error={contextError} retry={() => setRefresh(v => v + 1)} subject="Deal data"/>}
        {joined.priorityError && <div className="notice error" role="alert"><Icon name="alert" size={18}/><div><strong>Priorities do not match the deal data</strong><p>{joined.priorityError.message}</p></div></div>}
        {tab === 'action' && !loading && !contextError && <ActionTab context={context} priority={joined.validPriority} rankingState={rankingState} view={view} fixture={fixture} snapshot={context?.snapshot_date ?? snapshot ?? null}
          session={{ status: request.status, error: sessionError, receivedAt }} onEvidence={id => select({ kind: 'evidence', id })} onReasons={() => changeTab('reasons', true)}
          onShowPaths={() => showGraph({ paths: allPaths })} onAnalyze={analyze} onShowVersion={setPreferred}/>}
        {tab === 'reasons' && context && <ReasonsTab priority={joined.validPriority} view={view} context={context} onEvidence={id => select({ kind: 'evidence', id })}
          onEdge={id => showGraph({ target: { kind: 'edge', id } })} onShowPath={path => showGraph({ paths: [path] })}/>}
        {tab === 'explore' && <div className="tab-stack">
          <div className="subnav" role="group" aria-label="Data views">{exploreViews.map(item => <button key={item.id} aria-pressed={explore === item.id} onClick={() => setExplore(item.id)}>{item.label}</button>)}</div>
          {explore === 'graph' && (context ? <section className="explore-panel" aria-labelledby={ids.graph}><div className="section-intro"><h3 id={ids.graph} tabIndex={-1}>Relationships</h3></div>
            <ContextGraph key={graphRequest?.sequence ?? 0} initialFocus={graphRequest?.target} initialPaths={graphRequest ? graphRequest.paths : (allPaths.length ? allPaths : undefined)} context={context} selection={selection} onSelect={value => select(value, false)}/></section>
            : !loading && <p className="muted">Relationships will appear when deal data is available.</p>)}
          {explore === 'evidence' && <EvidenceBrowser records={context?.evidence ?? []} selection={selection} onSelect={value => select(value)}/>}
          {explore === 'method' && <section className="explore-panel">{joined.validPriority ? <PriorityFactors item={joined.validPriority} onEvidence={id => select({ kind: 'evidence', id })}/> : <p className="muted">Priority factors are not available for this deal.</p>}{methodology && <Methodology data={methodology}/>}</section>}
          {explore === 'diagnostic' && (fixture ? <p className="muted">Findings are unavailable in fixture mode.</p> : <section className="explore-panel" aria-label="Data findings">
            <div className="row-between"><p className="note">Findings from the pipeline audit. Refresh this deal if needed.</p><button className="button secondary small" disabled={!baseContext || loadingDiagnostic} onClick={() => void diagnosticRequest.run()}><Icon name="refresh" size={15}/>Refresh deal findings</button></div>
            {loadingDiagnostic && <p className="loading-line" role="status"><span className="spinner"/>Loading findings. Your recommendation remains available.</p>}
            {!!localDiagnosticError && <ErrorNotice error={asApiError(localDiagnosticError, 'Invalid findings response.')} retry={() => void diagnosticRequest.run()} subject="Findings"/>}
            {joined.validDiagnostic && !localDiagnosticError && <DiagnosticPanel data={joined.validDiagnostic} onEvidence={id => select({ kind: 'evidence', id })}/>}
            {pipelineDiagnostic && context && !joined.diagnosticError && <Statistics data={pipelineDiagnostic} onEvidence={id => select({ kind: 'evidence', id })}/>}
            {diagnosticState?.status === 'error' && retryDiagnostics && <button className="button secondary small" onClick={retryDiagnostics}>Retry pipeline findings</button>}
          </section>)}
          {explore === 'technical' && <section className="explore-panel" aria-label="Technical details">
            <dl className="tech-list">
              <div><dt>Deal / account ID</dt><dd className="mono">{deal.deal_id} / {deal.account_id}</dd></div>
              <div><dt>Deal owner ID</dt><dd className="mono">{shownDeal.owner_id}</dd></div>
              <div><dt>CRM list status</dt><dd>{statusLabel[shownDeal.analysis_status]}. CRM does not store analysis results; recommendations come from priorities (GET /api/pipeline/priorities) or re-analysis (POST /api/deals/{deal.deal_id}/analyze).</dd></div>
              <div><dt>Data snapshot</dt><dd>{context ? dateLabel(context.snapshot_date) : 'Not loaded'}</dd></div>
              <div><dt>Displayed recommendation</dt><dd>{view.recommendation ? `${view.source === 'session' ? 'Re-analysis (POST)' : 'Priorities (GET)'} · mode ${view.recommendation.engine_mode} (${engineLabel[view.recommendation.engine_mode]})` : 'None yet'}</dd></div>
              <div><dt>Analysis request</dt><dd>{requestLabel}</dd></div>
            </dl>
            <button className="button secondary small" disabled={loading} onClick={() => { session.reset(); setRefresh(v => v + 1); }}><Icon name="refresh" size={15}/>Refresh deal data</button>
            {joined.validPriority && <details className="raw-source"><summary>Priority JSON</summary><pre>{JSON.stringify(joined.validPriority, null, 2)}</pre></details>}
            {view.recommendation && <details className="raw-source"><summary>Recommendation JSON</summary><pre>{JSON.stringify(view.recommendation, null, 2)}</pre></details>}
          </section>}
        </div>}
      </div>
    </article>
    {drawerOpen && <EvidenceDrawer mode={wide ? 'side' : 'sheet'} titleId={ids.drawer} onClose={closeDrawer}><EvidenceInspector context={context!} selection={selection!} titleId={ids.drawer} onGraph={target => showGraph({ target })}/></EvidenceDrawer>}
  </div>;
}
