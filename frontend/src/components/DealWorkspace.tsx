import { useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import type { ReactNode } from 'react';
import { ApiError } from '../lib/api';
import type { DealApi } from '../lib/api';
import type { Deal, DealContext } from '../lib/contracts';
import { dateLabel, rupiah, statusLabel } from '../lib/format';
import { ContextGraph } from './ContextGraph';
import type { Selection } from './ContextGraph';
import { EvidencePanel } from './EvidencePanel';
import { EvidenceBrowser } from './EvidenceBrowser';
import { Icon } from './Icon';
import { AnalysisReport, ContextNotes } from './AnalysisReport';
import { createAnalysisSession } from '../lib/analysisSession';
import type { GraphTarget } from '../lib/analysisView';
import { createResource } from '../lib/resource';
import type { ResourceState } from '../lib/resource';
import { enrichContext, mergeEvidence } from '../lib/phase3';
import type { PriorityItem, PipelineDiagnostic } from '../lib/phase3';
import { PriorityPanel, DiagnosticPanel, Statistics } from './Phase3Panels';

export function ErrorNotice({ error, retry, subject = 'Data' }: { error: ApiError; retry: () => void; subject?: string }) {
  const title = error.status === 501 ? `${subject} belum tersedia` : error.status === 404 ? 'Deal tidak ditemukan' : error.status === 408 ? 'Waktu tunggu habis' : `${subject} belum dapat dimuat`;
  const message = error.status === 501 ? 'Layanan belum menyediakan hasil untuk deal ini. Coba kembali setelah tersedia.' : error.status === 404 ? 'Deal ini tidak ditemukan oleh layanan. Muat ulang daftar atau pilih deal lain.' : error.message;
  return <div className={`notice ${error.status === 501 ? 'pending' : 'error'}`} role={error.status === 501 ? 'status' : 'alert'}><Icon name="info"/><div><strong>{title}</strong><p>{message}</p></div><button className="text-button" onClick={retry}>Coba lagi <Icon name="refresh" size={14}/></button></div>;
}
function Empty({ title, children }: { title: string; children: ReactNode }) {
  return <div className="empty-state compact"><Icon name="file" size={28}/><h3>{title}</h3><p>{children}</p></div>;
}
export function DealWorkspace({ deal, api, fixture, snapshot, priority = null, diagnosticState, retryDiagnostics }: {
  deal: Deal; api: DealApi; fixture: boolean; snapshot?: string; priority?: PriorityItem | null;
  diagnosticState?: ResourceState<PipelineDiagnostic>; retryDiagnostics?: () => void;
}) {
  const [tab, setTab] = useState<'overview' | 'graph' | 'evidence'>('overview');
  const [baseContext, setContext] = useState<DealContext | null>(null);
  const [contextError, setContextError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [reportVersion, setReportVersion] = useState<'ranking' | 'session'>('ranking');
  const diagnosticRequest = useMemo(() => createResource(async (signal: AbortSignal) => {
    if (!api.diagnostic) throw new ApiError(501, 'Diagnostic belum tersedia.');
    const result = await api.diagnostic(deal.deal_id, signal);
    if (result.account_id !== deal.account_id || result.snapshot_date !== snapshot) throw new ApiError(502, 'Snapshot atau akun diagnostic tidak cocok.');
    return result;
  }), [api, deal.deal_id, deal.account_id, snapshot]);
  const diagnosticRefresh = useSyncExternalStore(diagnosticRequest.subscribe, diagnosticRequest.getSnapshot);
  const pipelineDiagnostic = diagnosticState?.data;
  const diagnostic = diagnosticRefresh.status !== 'idle' ? diagnosticRefresh.data : pipelineDiagnostic?.deals.find(d => d.deal_id === deal.deal_id) ?? null;
  const joined = useMemo(() => {
    let context = baseContext, validPriority = null, validDiagnostic = null;
    let priorityError: Error | null = null, diagnosticError: Error | null = null;
    if (!context) return { context, validPriority, validDiagnostic, priorityError, diagnosticError };
    if (priority) try { context = enrichContext(context, priority); validPriority = priority; } catch(e) { priorityError = e as Error; }
    if (diagnostic) try { context = enrichContext(context, diagnostic); validDiagnostic = diagnostic; } catch(e) { diagnosticError = e as Error; }
    // Statistical sources may belong to a different deal. They remain readable even without a node here.
    if (pipelineDiagnostic) try {
      const ids = new Set(pipelineDiagnostic.statistical_assessment.evidence_ids);
      context = { ...context, evidence: mergeEvidence(context.evidence, pipelineDiagnostic.deals.flatMap(d => d.evidence).filter(e => ids.has(e.id))) };
    } catch(e) { diagnosticError = e as Error; }
    return { context, validPriority, validDiagnostic, priorityError, diagnosticError };
  }, [baseContext, priority, diagnostic, pipelineDiagnostic]);
  const context = joined.context;
  const localDiagnosticError = joined.diagnosticError ?? diagnosticRefresh.error ?? (diagnosticRefresh.status === 'idle' ? diagnosticState?.error : null);
  const loadingDiagnostic = diagnosticRefresh.status === 'loading' || (diagnosticRefresh.status === 'idle' && (diagnosticState?.status === 'loading' || diagnosticState?.status === 'idle'));
  const showSession = reportVersion === 'session' || !joined.validPriority;
  const session = useMemo(() => createAnalysisSession(signal => api.analyze(deal.deal_id, signal)), [api, deal.deal_id]);
  const request = useSyncExternalStore(session.subscribe, session.getSnapshot);
  const recommendation = request.data;
  const analyzing = request.status === 'running';
  const analysisError = request.status === 'failed' ? request.error instanceof ApiError ? request.error : new ApiError(0, 'Analisis belum dapat dimuat.') : null;
  const [selection, setSelection] = useState<Selection>(null);
  const [graphRequest, setGraphRequest] = useState<{ target: GraphTarget; sequence: number } | null>(null);
  function openEvidence(id: string) {
    setSelection({ kind: 'evidence', id });
    requestAnimationFrame(() => { const panel = document.getElementById('evidence-inspector'); if (panel) { panel.scrollTop = 0; panel.focus(); } });
  }
  function openGraph(target: GraphTarget) {
    setGraphRequest(current => ({ target, sequence: (current?.sequence ?? 0) + 1 }));
    setSelection(target); setTab('graph');
    requestAnimationFrame(() => document.getElementById('panel-graph')?.focus());
  }
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setContext(null); setContextError(null); setSelection(null); setGraphRequest(null);
    session.reset(); diagnosticRequest.reset();
    api.context(deal.deal_id, controller.signal).then(data => { if (data.deal.account_id !== deal.account_id || (snapshot && data.snapshot_date !== snapshot)) throw new ApiError(502, 'Snapshot atau akun konteks tidak cocok.'); if (!controller.signal.aborted) setContext(data); })
      .catch(error => { if (!controller.signal.aborted) setContextError(error instanceof ApiError ? error : new ApiError(0, 'Konteks belum dapat dimuat.')); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => { controller.abort(); session.reset(); diagnosticRequest.reset(); };
  }, [api, deal.deal_id, deal.account_id, snapshot, refresh, session, diagnosticRequest]);
  function analyze() { setReportVersion('session'); setTab('overview'); void session.run(); }
  const shownDeal = context?.deal ?? deal;
  const requestLabel = { idle: 'Belum dijalankan', running: 'Sedang berjalan', received: 'Respons diterima', failed: 'Gagal' }[request.status];
  return <section className="workspace" aria-label={`Detail ${deal.account_id}`}>
    <div className="workspace-heading"><div><p className="eyebrow">RUANG KEPUTUSAN <span>/ {deal.account_id}</span></p><h2>{deal.account_name}</h2><p className="muted small">{deal.deal_id} <span className="dot-divider">·</span> Pemilik deal {shownDeal.owner_id} <span className="dot-divider">·</span> {context ? `Konteks ${dateLabel(context.snapshot_date)}` : 'Konteks belum tersedia'}</p></div><button className="button primary" onClick={analyze} disabled={!context || loading || analyzing}><Icon name={analyzing ? 'clock' : 'arrow'} size={17}/>{analyzing ? 'Menganalisis…' : recommendation ? 'Analisis ulang' : 'Analisis langkah berikutnya'}</button></div>
    <div className="session-strip"><div className={`session-status ${request.status}`} role="status"><span>Status request sesi</span><strong>{requestLabel}</strong></div><p>Status konteks CRM: <strong>{context ? statusLabel[context.deal.analysis_status] : 'Menunggu konteks'}</strong><small>Status request hanya untuk sesi ini. Respons diterima bukan konfirmasi kecukupan bukti dan tidak mengubah status bisnis.</small></p><button className="button secondary" disabled={loading} onClick={() => { session.reset(); setRefresh(v => v + 1); }}>Muat ulang konteks</button></div>
    <div className="workspace-columns"><div className="workspace-main">
      <div className="tabs" role="tablist" aria-label="Tampilan detail deal">{([{ id: 'overview', label: 'Ringkasan', icon: 'grid' }, { id: 'graph', label: 'Peta relasi', icon: 'graph' }, { id: 'evidence', label: 'Bukti', icon: 'file' }] as const).map((item, index, items) => <button key={item.id} id={`tab-${item.id}`} role="tab" aria-controls={`panel-${item.id}`} aria-selected={tab === item.id} tabIndex={tab === item.id ? 0 : -1}
        onClick={() => setTab(item.id)} onKeyDown={e => { let next = index; if (e.key === 'ArrowRight') next = (index + 1) % items.length; else if (e.key === 'ArrowLeft') next = (index + items.length - 1) % items.length; else if (e.key === 'Home') next = 0; else if (e.key === 'End') next = items.length - 1; else return; e.preventDefault(); setTab(items[next].id); document.getElementById(`tab-${items[next].id}`)?.focus(); }}><Icon name={item.icon} size={16}/>{item.label}{item.id === 'evidence' && context && <span className="count">{context.evidence.length}</span>}</button>)}</div>
      <div className="tab-content" role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} tabIndex={0} aria-busy={loading}>
        {loading && <div className="loading-context" role="status"><span className="spinner"/><p>Menghubungkan deal dengan konteksnya…</p></div>}
        {contextError && <ErrorNotice error={contextError} retry={() => setRefresh(v => v + 1)} subject="Konteks deal"/>}
        {tab === 'overview' && <>
          <div className="deal-facts"><div><span>Tahap saat ini</span><strong>{shownDeal.stage}</strong></div><div><span>Di tahap ini</span><strong>{shownDeal.stage_age_days} <small>hari</small></strong></div><div><span>Potensi tahunan</span><strong>{rupiah(shownDeal.annual_value)}</strong></div></div>
          {joined.priorityError && <div className="notice error" role="alert">Prioritas tidak dapat dihubungkan ke konteks: {joined.priorityError.message}</div>}
          {joined.validPriority && context && <><PriorityPanel item={joined.validPriority} context={context} onEvidence={openEvidence} onGraph={openGraph}/><div className="report-version" role="group" aria-label="Versi rekomendasi"><button className="button secondary" aria-pressed={!showSession} onClick={() => setReportVersion('ranking')}>Rekomendasi ranking rules</button><button className="button secondary" aria-pressed={showSession} onClick={() => setReportVersion('session')}>Analisis sesi {recommendation ? '· tersedia' : '· belum tersedia'}</button></div></>}
          <p className="report-origin"><strong>{showSession ? 'Sumber rekomendasi: POST analisis sesi' : 'Sumber rekomendasi: GET ranking pipeline · rules'}</strong><span>{showSession ? 'Hasil sesi tidak mengubah rank pipeline.' : 'Rekomendasi yang digunakan ranking; tombol analisis sesi menghasilkan respons terpisah.'}</span></p>
          {showSession && analysisError && <ErrorNotice error={analysisError} retry={analyze} subject="Analisis"/>}
          {showSession && analyzing && <div className="panel" role="status"><span className="spinner"/> Memeriksa konteks dan preseden…</div>}
          {!showSession && joined.validPriority && context ? <AnalysisReport recommendation={joined.validPriority.recommendation} context={context} fixture={fixture} onEvidence={openEvidence}/> : recommendation && context ? <AnalysisReport recommendation={recommendation} context={context} fixture={fixture} onEvidence={openEvidence}/> : !analyzing && !analysisError && <section className="panel"><Empty title="Analisis belum dijalankan">Jalankan analisis untuk menerima usulan tindakan, milestone, kebutuhan persetujuan, dan penjelasan berbasis sumber.</Empty>{context && <ContextNotes context={context}/>}</section>}
          {!fixture && <section className="diagnostic-section" aria-label="Status diagnostic"><div className="row-between"><h3>Diagnostic bersumber</h3><button className="text-button" disabled={!baseContext || loadingDiagnostic} onClick={() => void diagnosticRequest.run()}>Muat ulang diagnostic deal</button></div>
            {loadingDiagnostic && <p role="status">Memuat diagnostic; rekomendasi dari endpoint lain tetap tersedia.</p>}
            {!!localDiagnosticError && <ErrorNotice error={localDiagnosticError instanceof ApiError ? localDiagnosticError : new ApiError(502, localDiagnosticError instanceof Error ? localDiagnosticError.message : 'Diagnostic tidak valid.')} retry={() => void diagnosticRequest.run()} subject="Diagnostic"/>}
            {joined.validDiagnostic && !localDiagnosticError && <DiagnosticPanel data={joined.validDiagnostic} onEvidence={openEvidence}/>}
            {pipelineDiagnostic && context && !joined.diagnosticError && <Statistics data={pipelineDiagnostic} onEvidence={openEvidence}/>}
            {diagnosticState?.status === 'error' && <button className="text-button" onClick={retryDiagnostics}>Coba lagi diagnostic seluruh pipeline</button>}
          </section>}
        </>}
        {tab === 'graph' && (context ? <section className="panel graph-panel">{graphRequest && <button className="text-button return-analysis" onClick={() => { setTab('overview'); requestAnimationFrame(() => document.getElementById('panel-overview')?.focus()); }}>← Kembali ke analisis</button>}<div className="panel-heading"><h3>Konteks yang saling terhubung</h3><span className="muted small">{context.graph.nodes.length} node · {context.graph.edges.length} relasi</span></div><ContextGraph key={graphRequest?.sequence ?? 0} initialFocus={graphRequest?.target} context={context} selection={selection} onSelect={setSelection}/></section> : !loading && <section className="panel"><Empty title="Peta relasi menunggu konteks">Graph akan menampilkan hubungan yang dikirim layanan, lengkap dengan sumber buktinya.</Empty></section>)}
        {tab === 'evidence' && <EvidenceBrowser records={context?.evidence ?? []} selection={selection} onSelect={value => value?.kind === 'evidence' ? openEvidence(value.id) : setSelection(value)}/>}
      </div>
    </div><EvidencePanel context={context} selection={selection} onGraph={openGraph} onClear={() => setSelection(null)}/></div>
  </section>;
}
