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
  { id: 'action', label: 'Tindakan', icon: 'target' },
  { id: 'reasons', label: 'Alasan & bukti', icon: 'file' },
  { id: 'explore', label: 'Peta & data', icon: 'graph' },
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
    if (!api.diagnostic) throw new ApiError(501, 'Temuan data belum tersedia.');
    const result = await api.diagnostic(deal.deal_id, signal);
    if (result.account_id !== deal.account_id || result.snapshot_date !== snapshot) throw new ApiError(502, 'Snapshot atau akun temuan data tidak cocok.');
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
    if (request.status === 'received') setReceivedAt(new Intl.DateTimeFormat('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'Asia/Jakarta' }).format(new Date()));
    else if (request.status !== 'failed') setReceivedAt(null);
  }, [request.status]);
  const view = recommendationView({ dealId: deal.deal_id, priority: joined.validPriority, session: request, preferred });
  const sessionError = request.status === 'failed' ? request.error instanceof ApiError ? request.error : new ApiError(0, 'Analisis belum dapat dimuat.') : null;

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
    api.context(deal.deal_id, controller.signal).then(data => { if (data.deal.account_id !== deal.account_id || (snapshot && data.snapshot_date !== snapshot)) throw new ApiError(502, 'Snapshot atau akun data deal tidak cocok.'); if (!controller.signal.aborted) setContext(data); })
      .catch(error => { if (!controller.signal.aborted) setContextError(error instanceof ApiError ? error : new ApiError(0, 'Data deal belum dapat dimuat.')); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => { controller.abort(); session.reset(); diagnosticRequest.reset(); };
  }, [api, deal.deal_id, deal.account_id, snapshot, refresh, session, diagnosticRequest]);
  function analyze() { setPreferred('session'); setTab('action'); void session.run(); }
  function changeTab(next: Tab, focus = false) {
    setTab(next);
    if (focus) pendingFocus.current = `${ids.panel}-${next}`;
  }
  const shownDeal = context?.deal ?? deal;
  const requestLabel = { idle: 'Belum diminta', running: 'Sedang berjalan', received: 'Hasil diterima', failed: 'Gagal' }[request.status];
  const drawerOpen = !!(selection && context);
  const exploreViews: { id: ExploreView; label: string }[] = [
    { id: 'graph', label: 'Peta hubungan' }, { id: 'evidence', label: `Semua bukti${context ? ` (${context.evidence.length.toLocaleString('id-ID')})` : ''}` },
    { id: 'method', label: 'Cara prioritas dihitung' }, { id: 'diagnostic', label: 'Temuan dari data' }, { id: 'technical', label: 'Rincian teknis' },
  ];

  return <div className={`workspace ${drawerOpen && wide ? 'with-drawer' : ''}`}>
    <article className="detail" aria-labelledby={ids.title}>
      <div className="detail-navigation"><header className="detail-head">
        {onBack && <button className="back-button" onClick={onBack}><Icon name="back" size={18}/>Semua deal</button>}
        <h2 id={ids.title} tabIndex={-1}>{deal.account_name}</h2>
        <div className="detail-meta">
          {priority ? <span className="rank-pill">Prioritas {priority.rank}{rankTotal ? ` dari ${rankTotal}` : ''}</span> : <span className="rank-pill quiet">{rankingState === 'loading' ? 'Prioritas sedang disusun' : 'Prioritas belum tersedia'}</span>}
          {priority?.priority_kind === 'discovery' && <span className="kind discovery">{priorityKindLabel.discovery}</span>}
          <span>Data per {snapshot ? dateLabel(snapshot) : 'tanggal belum tersedia'}</span>
        </div>
      </header>
      <div className="tabs" role="tablist" aria-label="Detail deal">{TABS.map((item, index) => <button key={item.id} id={`${ids.panel}-tab-${item.id}`} role="tab" aria-controls={tab === item.id ? `${ids.panel}-${item.id}` : undefined} aria-selected={tab === item.id} tabIndex={tab === item.id ? 0 : -1}
        onClick={() => setTab(item.id)} onKeyDown={e => { const next = nextTabIndex(e.key, index, TABS.length); if (next === null) return; e.preventDefault(); setTab(TABS[next].id); document.getElementById(`${ids.panel}-tab-${TABS[next].id}`)?.focus(); }}><Icon name={item.icon} size={17}/>{item.label}</button>)}</div>
      </div>
      <div className="tab-panel" role="tabpanel" id={`${ids.panel}-${tab}`} aria-labelledby={`${ids.panel}-tab-${tab}`} tabIndex={-1} aria-busy={loading}>
        {tab === 'action' && <dl className="deal-metrics" aria-label="Ringkasan deal">
          <div><dt><Icon name="flag" size={15}/>Tahap</dt><dd>{shownDeal.stage}</dd></div>
          <div><dt><Icon name="clock" size={15}/>Di tahap ini</dt><dd>{shownDeal.stage_age_days}<small>hari</small></dd></div>
          <div><dt title="Potensi nilai deal per tahun, belum pendapatan"><Icon name="target" size={15}/>Potensi / tahun</dt><dd>{rupiah(shownDeal.annual_value)}</dd></div>
        </dl>}
        {loading && <div className="loading-line" role="status"><span className="spinner"/>Memuat data deal…</div>}
        {contextError && <ErrorNotice error={contextError} retry={() => setRefresh(v => v + 1)} subject="Data deal"/>}
        {joined.priorityError && <div className="notice error" role="alert"><Icon name="alert" size={18}/><div><strong>Prioritas tidak dapat dihubungkan ke data deal</strong><p>{joined.priorityError.message}</p></div></div>}
        {tab === 'action' && !loading && !contextError && <ActionTab context={context} priority={joined.validPriority} rankingState={rankingState} view={view} fixture={fixture} snapshot={context?.snapshot_date ?? snapshot ?? null}
          session={{ status: request.status, error: sessionError, receivedAt }} onEvidence={id => select({ kind: 'evidence', id })} onReasons={() => changeTab('reasons', true)}
          onShowPaths={() => showGraph({ paths: allPaths })} onAnalyze={analyze} onShowVersion={setPreferred}/>}
        {tab === 'reasons' && context && <ReasonsTab priority={joined.validPriority} view={view} context={context} onEvidence={id => select({ kind: 'evidence', id })}
          onEdge={id => showGraph({ target: { kind: 'edge', id } })} onShowPath={path => showGraph({ paths: [path] })}/>}
        {tab === 'explore' && <div className="tab-stack">
          <div className="subnav" role="group" aria-label="Bagian data">{exploreViews.map(item => <button key={item.id} aria-pressed={explore === item.id} onClick={() => setExplore(item.id)}>{item.label}</button>)}</div>
          {explore === 'graph' && (context ? <section className="explore-panel" aria-labelledby={ids.graph}><div className="section-intro"><h3 id={ids.graph} tabIndex={-1}>Peta hubungan</h3></div>
            <ContextGraph key={graphRequest?.sequence ?? 0} initialFocus={graphRequest?.target} initialPaths={graphRequest ? graphRequest.paths : (allPaths.length ? allPaths : undefined)} context={context} selection={selection} onSelect={value => select(value, false)}/></section>
            : !loading && <p className="muted">Peta hubungan tampil setelah data deal tersedia.</p>)}
          {explore === 'evidence' && <EvidenceBrowser records={context?.evidence ?? []} selection={selection} onSelect={value => select(value)}/>}
          {explore === 'method' && <section className="explore-panel">{joined.validPriority ? <PriorityFactors item={joined.validPriority} onEvidence={id => select({ kind: 'evidence', id })}/> : <p className="muted">Faktor prioritas belum tersedia untuk deal ini.</p>}{methodology && <Methodology data={methodology}/>}</section>}
          {explore === 'diagnostic' && (fixture ? <p className="muted">Temuan data tidak tersedia pada mode fixture.</p> : <section className="explore-panel" aria-label="Temuan dari data">
            <div className="row-between"><p className="note">Diambil dari pemeriksaan data seluruh pipeline. Muat ulang hanya untuk deal ini bila diperlukan.</p><button className="button secondary small" disabled={!baseContext || loadingDiagnostic} onClick={() => void diagnosticRequest.run()}><Icon name="refresh" size={15}/>Muat ulang temuan deal ini</button></div>
            {loadingDiagnostic && <p className="loading-line" role="status"><span className="spinner"/>Memuat temuan data; saran tetap tersedia.</p>}
            {!!localDiagnosticError && <ErrorNotice error={asApiError(localDiagnosticError, 'Temuan data tidak valid.')} retry={() => void diagnosticRequest.run()} subject="Temuan data"/>}
            {joined.validDiagnostic && !localDiagnosticError && <DiagnosticPanel data={joined.validDiagnostic} onEvidence={id => select({ kind: 'evidence', id })}/>}
            {pipelineDiagnostic && context && !joined.diagnosticError && <Statistics data={pipelineDiagnostic} onEvidence={id => select({ kind: 'evidence', id })}/>}
            {diagnosticState?.status === 'error' && retryDiagnostics && <button className="button secondary small" onClick={retryDiagnostics}>Coba lagi temuan seluruh pipeline</button>}
          </section>)}
          {explore === 'technical' && <section className="explore-panel" aria-label="Rincian teknis">
            <dl className="tech-list">
              <div><dt>ID deal / akun</dt><dd className="mono">{deal.deal_id} / {deal.account_id}</dd></div>
              <div><dt>Pemilik deal (ID)</dt><dd className="mono">{shownDeal.owner_id}</dd></div>
              <div><dt>Status di daftar CRM</dt><dd>{statusLabel[shownDeal.analysis_status]}. CRM tidak menyimpan hasil analisis; saran di aplikasi berasal dari layanan prioritas (GET /api/pipeline/priorities) atau analisis ulang (POST /api/deals/{deal.deal_id}/analyze).</dd></div>
              <div><dt>Snapshot data</dt><dd>{context ? dateLabel(context.snapshot_date) : 'Belum dimuat'}</dd></div>
              <div><dt>Saran yang tampil</dt><dd>{view.recommendation ? `${view.source === 'session' ? 'Analisis ulang (POST)' : 'Urutan prioritas (GET)'} · mode ${view.recommendation.engine_mode} (${engineLabel[view.recommendation.engine_mode]})` : 'Belum ada'}</dd></div>
              <div><dt>Permintaan analisis ulang</dt><dd>{requestLabel}</dd></div>
            </dl>
            <button className="button secondary small" disabled={loading} onClick={() => { session.reset(); setRefresh(v => v + 1); }}><Icon name="refresh" size={15}/>Muat ulang data deal</button>
            {joined.validPriority && <details className="raw-source"><summary>JSON prioritas deal ini</summary><pre>{JSON.stringify(joined.validPriority, null, 2)}</pre></details>}
            {view.recommendation && <details className="raw-source"><summary>JSON saran yang tampil</summary><pre>{JSON.stringify(view.recommendation, null, 2)}</pre></details>}
          </section>}
        </div>}
      </div>
    </article>
    {drawerOpen && <EvidenceDrawer mode={wide ? 'side' : 'sheet'} titleId={ids.drawer} onClose={closeDrawer}><EvidenceInspector context={context!} selection={selection!} titleId={ids.drawer} onGraph={target => showGraph({ target })}/></EvidenceDrawer>}
  </div>;
}
