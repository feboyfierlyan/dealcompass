import { englishText } from './lib/english';
import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import { ApiError } from './lib/api';
import type { DealApi } from './lib/api';
import type { DealList } from './lib/contracts';
import { Icon } from './components/Icon';
import { DealWorkspace } from './components/DealWorkspace';
import type { RankingState } from './components/DealTabs';
import { ErrorNotice, asApiError } from './components/Notice';
import { createResource } from './lib/resource';
import { analysisStoreFor } from './lib/analysis';
import { matchPipeline, rankedDeals } from './lib/phase3';
import { compactRupiah, effectiveSelection, priorityKindLabel } from './lib/present';
import { useMedia } from './lib/useMedia';
import './style.css';
import './corporate.css';

export function Dashboard({ api, fixture, initialDeal = null }: { api: DealApi; fixture: boolean; initialDeal?: string | null }) {
  const [data, setData] = useState<DealList | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [userChoice, setUserChoice] = useState<string | null>(initialDeal);
  const [showDetail, setShowDetail] = useState(false);
  const narrow = useMedia('(max-width: 899px)');
  // Shared per API object: returning to a deal reuses its analysis instead of requesting it again.
  const store = fixture ? null : analysisStoreFor(api);
  const detailRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null); setData(null);
    api.list(controller.signal).then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(e => { if (!controller.signal.aborted) setError(e instanceof ApiError ? e : new ApiError(0, 'Deals could not be loaded.')); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [api, refresh]);
  // Ranking and pipeline findings are GET requests. Only the opened deal gets an analysis (DealWorkspace).
  const priorities = useMemo(() => createResource(async (signal: AbortSignal) => {
    if (!api.priorities || !data) throw new ApiError(501, 'Priorities are not available.');
    const result = await api.priorities(signal); matchPipeline(data, result); return result;
  }), [api, data]);
  const diagnostics = useMemo(() => createResource(async (signal: AbortSignal) => {
    if (!api.diagnostics || !data) throw new ApiError(501, 'Findings are not available.');
    const result = await api.diagnostics(signal); matchPipeline(data, result); return result;
  }), [api, data]);
  const priorityState = useSyncExternalStore(priorities.subscribe, priorities.getSnapshot);
  const diagnosticState = useSyncExternalStore(diagnostics.subscribe, diagnostics.getSnapshot);
  useEffect(() => {
    if (data && !fixture) { void priorities.run(); void diagnostics.run(); }
    return () => { priorities.reset(); diagnostics.reset(); };
  }, [data, fixture, priorities, diagnostics]);
  const rankingState: RankingState = fixture || !api.priorities ? 'unavailable' : priorityState.status === 'ready' ? 'ready' : priorityState.status === 'error' ? 'error' : 'loading';
  const deals = data ? priorityState.data ? rankedDeals(data, priorityState.data) : data.items.map(d => ({ ...d, rank: null })) : [];
  const ranked = priorityState.data ? [...priorityState.data.items].sort((a, b) => a.rank - b.rank).map(i => i.deal_id) : null;
  // The top-ranked deal opens by default; a deal the user picked stays open when the ranking arrives.
  const selected = effectiveSelection({ items: deals.map(d => d.deal_id), ranked, userChoice });
  const active = deals.find(d => d.deal_id === selected) ?? null;
  const itemFor = (id: string) => priorityState.data?.items.find(i => i.deal_id === id) ?? null;
  // On phones the list and the detail are separate views; focus follows the view that just opened.
  const pendingFocus = useRef<'detail' | { deal: string } | null>(null);
  useEffect(() => {
    const target = pendingFocus.current;
    if (!target) return;
    pendingFocus.current = null;
    const element = target === 'detail' ? detailRef.current?.querySelector<HTMLElement>('h2') : document.querySelector<HTMLElement>(`[data-deal="${target.deal}"]`);
    element?.focus();
  });
  function open(id: string) {
    setUserChoice(id);
    if (!narrow) return;
    setShowDetail(true);
    pendingFocus.current = 'detail';
  }
  function back() {
    setShowDetail(false);
    if (selected) pendingFocus.current = { deal: selected };
  }
  const detailOnly = narrow && showDetail && !!active;
  const listOnly = narrow && !detailOnly;

  return <main id="main-content" className={`layout ${detailOnly ? 'show-detail' : ''} ${listOnly ? 'show-list' : ''}`}>
    <h1 className="visually-hidden">DealCompass · Sales priorities</h1>
    <section className="queue" aria-labelledby="queue-title" hidden={detailOnly}>
      <div className="queue-workspace"><span className="workspace-avatar">KN</span><div><strong>KasirNusa</strong><span>Sales workspace</span></div><Icon name="compass" size={17}/></div>
      <div className="queue-section-label"><Icon name="grid" size={15}/>PIPELINE{deals.length ? ` · ${deals.length} DEALS` : ''}</div>
      <div className="queue-head">
        <h2 id="queue-title">Priority deals <span className="count">{deals.length || '—'}</span></h2>
        <button className="icon-button" title="Refresh deals" aria-label="Refresh deals" disabled={loading} onClick={() => setRefresh(v => v + 1)}><Icon name="refresh" size={15}/></button>
      </div>
      <div className="queue-status">
        {rankingState === 'loading' && <p role="status" className="status-line"><span className="spinner"/>Loading priorities…</p>}
        {rankingState === 'unavailable' && <p className="status-line">Priorities are unavailable in this mode. Showing CRM order.</p>}
        {rankingState === 'error' && <ErrorNotice error={asApiError(priorityState.error, 'The priority response is invalid.')} retry={() => void priorities.run()} subject="Priority order" retryLabel="Refresh priorities"/>}
        {rankingState === 'error' && <p className="status-line">Showing CRM order. You can still open each deal.</p>}
      </div>
      {loading && <ol className="queue-list" aria-label="Loading deals">{Array.from({ length: 5 }, (_, i) => <li key={i} className="queue-skeleton"><i/><i/><i/></li>)}</ol>}
      {error && <ErrorNotice error={error} retry={() => setRefresh(v => v + 1)} subject="Deals"/>}
      {!loading && !error && !deals.length && <div className="empty-state"><h2>No deals yet</h2><p>The service returned no deals. Refresh when data is available.</p><button className="button secondary" onClick={() => setRefresh(v => v + 1)}>Refresh</button></div>}
      {!!deals.length && <ol className="queue-list">{deals.map(deal => {
        const item = itemFor(deal.deal_id), current = deal.deal_id === selected;
        return <li key={deal.deal_id}><button className={`queue-item ${current ? 'current' : ''} ${deal.rank === null ? 'no-rank' : ''}`} data-deal={deal.deal_id} aria-current={current ? 'true' : undefined} onClick={() => open(deal.deal_id)}>
          {deal.rank !== null && <span className="queue-rank"><span className="visually-hidden">Priority </span>{deal.rank}</span>}
          <span className="queue-body">
            <span className="queue-name">{deal.account_name}</span>
            <span className="queue-meta">Stage {englishText(deal.stage)} · {compactRupiah(deal.annual_value)}/yr</span>
            {item && (item.priority_kind === 'discovery' || item.recommendation.approvals_needed.length > 0) && <span className="queue-reason">
              {item.priority_kind === 'discovery' ? <span className="kind discovery">{priorityKindLabel.discovery}</span> : <span className="queue-approval">Approval needed</span>}
            </span>}
          </span>
          <Icon name="chevron" size={18}/>
        </button></li>;
      })}</ol>}
      <details className="queue-help"><summary><Icon name="info" size={15}/>Quick guide</summary><ol><li>Start with the highest-priority deal.</li><li>Review the action and its conditions.</li><li>Prepare a plan to copy.</li></ol><p>Priority is an order of attention, not a closing probability.</p></details>
    </section>
    <section className="detail-col" ref={detailRef} aria-label="Deal details" hidden={listOnly}>
      {active && data ? <DealWorkspace key={`${fixture}-${active.deal_id}-${refresh}`} deal={active} api={api} fixture={fixture} snapshot={data.snapshot_date} store={store}
        priority={itemFor(active.deal_id)} rankTotal={priorityState.data?.items.length ?? null} rankingState={rankingState} methodology={priorityState.data}
        diagnosticState={diagnosticState} retryDiagnostics={() => void diagnostics.run()} onBack={narrow ? back : undefined}/>
        : <div className="detail-empty">{loading ? <p role="status"><span className="spinner"/>Loading deals…</p>
          : rankingState === 'loading' && deals.length ? <p role="status"><span className="spinner"/>Loading priorities. The top deal will open here.</p>
          : deals.length ? <p>Select a deal to view its next step.</p> : null}</div>}
    </section>
  </main>;
}
