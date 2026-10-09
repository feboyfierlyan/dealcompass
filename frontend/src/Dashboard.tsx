import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import { ApiError } from './lib/api';
import type { DealApi } from './lib/api';
import type { DealList } from './lib/contracts';
import { Icon } from './components/Icon';
import { DealWorkspace } from './components/DealWorkspace';
import type { RankingState } from './components/DealTabs';
import { ErrorNotice, asApiError } from './components/Notice';
import { createResource } from './lib/resource';
import { matchPipeline, rankedDeals } from './lib/phase3';
import { Methodology } from './components/Phase3Panels';
import { compactRupiah, effectiveSelection, priorityKindLabel } from './lib/present';
import { useMedia } from './lib/useMedia';
import './style.css';
import './mixpanel.css';

export function Dashboard({ api, fixture }: { api: DealApi; fixture: boolean }) {
  const [data, setData] = useState<DealList | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [userChoice, setUserChoice] = useState<string | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const narrow = useMedia('(max-width: 899px)');
  const detailRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null); setData(null);
    api.list(controller.signal).then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(e => { if (!controller.signal.aborted) setError(e instanceof ApiError ? e : new ApiError(0, 'Daftar deal belum dapat dimuat.')); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [api, refresh]);
  // Ranking and pipeline findings are GET requests. No analysis (POST) runs on load.
  const priorities = useMemo(() => createResource(async (signal: AbortSignal) => {
    if (!api.priorities || !data) throw new ApiError(501, 'Urutan prioritas belum tersedia.');
    const result = await api.priorities(signal); matchPipeline(data, result); return result;
  }), [api, data]);
  const diagnostics = useMemo(() => createResource(async (signal: AbortSignal) => {
    if (!api.diagnostics || !data) throw new ApiError(501, 'Temuan data belum tersedia.');
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
    <h1 className="visually-hidden">DealCompass · Prioritas tindak lanjut</h1>
    <section className="queue" aria-labelledby="queue-title" hidden={detailOnly}>
      <div className="queue-workspace"><span className="workspace-avatar">KN</span><div><strong>KasirNusa</strong><span>Ruang kerja sales</span></div><Icon name="compass" size={17}/></div>
      <div className="queue-section-label"><Icon name="grid" size={15}/>PIPELINE · P01–P05</div>
      <div className="queue-head">
        <h2 id="queue-title">Deal prioritas <span className="count">{deals.length || '—'}</span></h2>
        <button className="icon-button" title="Muat ulang daftar" aria-label="Muat ulang daftar" disabled={loading} onClick={() => setRefresh(v => v + 1)}><Icon name="refresh" size={15}/></button>
      </div>
      <div className="queue-status">
        {rankingState === 'loading' && <p role="status" className="status-line"><span className="spinner"/>Menyusun urutan prioritas…</p>}
        {rankingState === 'unavailable' && <p className="status-line">Urutan prioritas tidak tersedia pada mode ini. Daftar mengikuti urutan CRM.</p>}
        {rankingState === 'error' && <ErrorNotice error={asApiError(priorityState.error, 'Urutan prioritas tidak valid.')} retry={() => void priorities.run()} subject="Urutan prioritas" retryLabel="Muat ulang urutan"/>}
        {rankingState === 'error' && <p className="status-line">Daftar di bawah mengikuti urutan CRM, bukan prioritas. Deal tetap bisa dibuka.</p>}
      </div>
      {loading && <ol className="queue-list" aria-label="Memuat daftar deal">{Array.from({ length: 5 }, (_, i) => <li key={i} className="queue-skeleton"><i/><i/><i/></li>)}</ol>}
      {error && <ErrorNotice error={error} retry={() => setRefresh(v => v + 1)} subject="Daftar deal"/>}
      {!loading && !error && !deals.length && <div className="empty-state"><h2>Belum ada deal dalam daftar</h2><p>Layanan mengembalikan daftar kosong. Muat ulang setelah data tersedia.</p><button className="button secondary" onClick={() => setRefresh(v => v + 1)}>Muat ulang</button></div>}
      {!!deals.length && <ol className="queue-list">{deals.map(deal => {
        const item = itemFor(deal.deal_id), current = deal.deal_id === selected;
        return <li key={deal.deal_id}><button className={`queue-item ${current ? 'current' : ''} ${deal.rank === null ? 'no-rank' : ''}`} data-deal={deal.deal_id} aria-current={current ? 'true' : undefined} onClick={() => open(deal.deal_id)}>
          {deal.rank !== null && <span className="queue-rank"><span className="visually-hidden">Prioritas </span>{deal.rank}</span>}
          <span className="queue-body">
            <span className="queue-name">{deal.account_name}</span>
            <span className="queue-meta">Tahap {deal.stage} · {compactRupiah(deal.annual_value)}/tahun</span>
            {item && (item.priority_kind === 'discovery' || item.recommendation.approvals_needed.length > 0) && <span className="queue-reason">
              {item.priority_kind === 'discovery' ? <span className="kind discovery">{priorityKindLabel.discovery}</span> : <span className="queue-approval">Perlu persetujuan</span>}
            </span>}
          </span>
          <Icon name="chevron" size={18}/>
        </button></li>;
      })}</ol>}
      {priorityState.data && <Methodology data={priorityState.data}/>}
      <details className="queue-help"><summary><Icon name="info" size={15}/>Panduan singkat</summary><ol><li>Pilih deal dari urutan teratas.</li><li>Periksa tindakan dan syaratnya.</li><li>Siapkan rencana untuk disalin.</li></ol><p>Prioritas menunjukkan urutan perhatian, bukan peluang closing.</p></details>
    </section>
    <section className="detail-col" ref={detailRef} aria-label="Detail deal" hidden={listOnly}>
      {active && data ? <DealWorkspace key={`${fixture}-${active.deal_id}-${refresh}`} deal={active} api={api} fixture={fixture} snapshot={data.snapshot_date}
        priority={itemFor(active.deal_id)} rankTotal={priorityState.data?.items.length ?? null} rankingState={rankingState} methodology={priorityState.data}
        diagnosticState={diagnosticState} retryDiagnostics={() => void diagnostics.run()} onBack={narrow ? back : undefined}/>
        : <div className="detail-empty">{loading ? <p role="status"><span className="spinner"/>Memuat daftar deal…</p>
          : rankingState === 'loading' && deals.length ? <p role="status"><span className="spinner"/>Menyusun urutan prioritas. Deal teratas akan terbuka di sini.</p>
          : deals.length ? <p>Pilih deal dari daftar untuk melihat saran tindakan.</p> : null}</div>}
    </section>
  </main>;
}
