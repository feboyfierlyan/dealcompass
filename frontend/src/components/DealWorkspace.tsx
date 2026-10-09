import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { ApiError } from '../lib/api';
import type { DealApi } from '../lib/api';
import type { Deal, DealContext, Recommendation } from '../lib/contracts';
import { dateLabel, kindLabel, rupiah } from '../lib/format';
import { ContextGraph } from './ContextGraph';
import type { Selection } from './ContextGraph';
import { EvidencePanel } from './EvidencePanel';
import { Icon } from './Icon';

export function ErrorNotice({ error, retry, subject = 'Data' }: { error: ApiError; retry: () => void; subject?: string }) {
  const title = error.status === 501 ? `${subject} belum tersedia` : error.status === 404 ? 'Deal tidak ditemukan' : error.status === 408 ? 'Waktu tunggu habis' : `${subject} belum dapat dimuat`;
  const message = error.status === 501 ? 'Layanan belum menyediakan hasil untuk deal ini. Coba kembali setelah tersedia.' : error.status === 404 ? 'Deal ini tidak ditemukan oleh layanan. Muat ulang daftar atau pilih deal lain.' : error.message;
  return <div className={`notice ${error.status === 501 ? 'pending' : 'error'}`} role={error.status === 501 ? 'status' : 'alert'}><Icon name="info"/><div><strong>{title}</strong><p>{message}</p></div><button className="text-button" onClick={retry}>Coba lagi <Icon name="refresh" size={14}/></button></div>;
}
function Empty({ title, children }: { title: string; children: ReactNode }) {
  return <div className="empty-state compact"><Icon name="file" size={28}/><h3>{title}</h3><p>{children}</p></div>;
}
function StringList({ items, empty }: { items: string[]; empty: string }) {
  return items.length ? <ul className="detail-list">{items.map((item, i) => <li key={`${i}-${item}`}>{item}</li>)}</ul> : <p className="muted small">{empty}</p>;
}
export function DealWorkspace({ deal, api, fixture }: { deal: Deal; api: DealApi; fixture: boolean }) {
  const [tab, setTab] = useState<'overview' | 'graph' | 'evidence'>('overview');
  const [context, setContext] = useState<DealContext | null>(null);
  const [contextError, setContextError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [analysisError, setAnalysisError] = useState<ApiError | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [selection, setSelection] = useState<Selection>(null);
  const analysisController = useRef<AbortController | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setContext(null); setContextError(null); setRecommendation(null); setAnalysisError(null); setSelection(null);
    analysisController.current?.abort(); setAnalyzing(false);
    api.context(deal.deal_id, controller.signal).then(data => { if (!controller.signal.aborted) setContext(data); })
      .catch(error => { if (!controller.signal.aborted) setContextError(error instanceof ApiError ? error : new ApiError(0, 'Konteks belum dapat dimuat.')); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => { controller.abort(); analysisController.current?.abort(); };
  }, [api, deal.deal_id, refresh]);
  async function analyze() {
    analysisController.current?.abort();
    const controller = new AbortController(); analysisController.current = controller;
    setAnalyzing(true); setAnalysisError(null); setRecommendation(null);
    try { const data = await api.analyze(deal.deal_id, controller.signal); if (!controller.signal.aborted) setRecommendation(data); }
    catch (error) { if (!controller.signal.aborted) setAnalysisError(error instanceof ApiError ? error : new ApiError(0, 'Analisis belum dapat dimuat.')); }
    finally { if (!controller.signal.aborted) setAnalyzing(false); }
  }
  const unknowns = [...new Set([...(context?.unknowns ?? []), ...(recommendation?.unknowns ?? [])])];
  const shownDeal = context?.deal ?? deal;
  const selectedPrecedents = new Set(recommendation?.precedent_ids ?? []);
  const missingPrecedents = (recommendation?.precedent_ids ?? []).filter(id => !context?.candidate_decisions.some(d => d.decision_id === id));
  const text = (value: unknown) => typeof value === 'string' || typeof value === 'number' ? String(value) : 'Tidak dicantumkan';
  return <section className="workspace" aria-label={`Detail ${deal.account_id}`}>
    <div className="workspace-heading"><div><p className="eyebrow">RUANG KEPUTUSAN <span>/ {deal.account_id}</span></p><h2>{deal.account_name}</h2><p className="muted small">{deal.deal_id} <span className="dot-divider">·</span> Pemilik deal {shownDeal.owner_id} <span className="dot-divider">·</span> {context ? `Konteks ${dateLabel(context.snapshot_date)}` : 'Konteks belum tersedia'}</p></div><button className="button primary" onClick={analyze} disabled={!context || loading || analyzing}><Icon name={analyzing ? 'clock' : 'arrow'} size={17}/>{analyzing ? 'Menganalisis…' : recommendation ? 'Analisis ulang' : 'Analisis langkah berikutnya'}</button></div>
    <div className="workspace-columns"><div className="workspace-main">
      <div className="tabs" role="tablist" aria-label="Tampilan detail deal">{([{ id: 'overview', label: 'Ringkasan', icon: 'grid' }, { id: 'graph', label: 'Peta relasi', icon: 'graph' }, { id: 'evidence', label: 'Bukti', icon: 'file' }] as const).map((item, index, items) => <button key={item.id} id={`tab-${item.id}`} role="tab" aria-controls={`panel-${item.id}`} aria-selected={tab === item.id} tabIndex={tab === item.id ? 0 : -1}
        onClick={() => setTab(item.id)} onKeyDown={e => { let next = index; if (e.key === 'ArrowRight') next = (index + 1) % items.length; else if (e.key === 'ArrowLeft') next = (index + items.length - 1) % items.length; else if (e.key === 'Home') next = 0; else if (e.key === 'End') next = items.length - 1; else return; e.preventDefault(); setTab(items[next].id); document.getElementById(`tab-${items[next].id}`)?.focus(); }}><Icon name={item.icon} size={16}/>{item.label}{item.id === 'evidence' && context && <span className="count">{context.evidence.length}</span>}</button>)}</div>
      <div className="tab-content" role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} tabIndex={0} aria-busy={loading}>
        {loading && <div className="loading-context" role="status"><span className="spinner"/><p>Menghubungkan deal dengan konteksnya…</p></div>}
        {contextError && <ErrorNotice error={contextError} retry={() => setRefresh(v => v + 1)} subject="Konteks deal"/>}
        {tab === 'overview' && <>
          <div className="deal-facts"><div><span>Tahap saat ini</span><strong>{shownDeal.stage}</strong></div><div><span>Di tahap ini</span><strong>{shownDeal.stage_age_days} <small>hari</small></strong></div><div><span>Potensi tahunan</span><strong>{rupiah(shownDeal.annual_value)}</strong></div></div>
          <section className={`action-panel panel ${recommendation ? 'has-action' : ''}`}><div className="panel-heading"><span className="eyebrow">LANGKAH BERIKUTNYA</span>{recommendation ? <span className={`badge engine ${recommendation.engine_mode}`}>{({ jev: 'Jev', rules: 'Aturan', replay: 'Replay' })[recommendation.engine_mode]}{fixture ? ' · fixture' : ''}</span> : <Icon name="arrow" size={18}/>}</div>
            {analyzing && <p role="status" className="muted">Memeriksa konteks dan preseden…</p>}
            {analysisError && <ErrorNotice error={analysisError} retry={analyze} subject="Analisis"/>}
            {recommendation ? <><h3>{recommendation.action || 'Tindakan belum dicantumkan.'}</h3><div className="action-meta"><div><span>Penanggung jawab</span><strong>{recommendation.owner_id ?? 'Belum ditentukan'}</strong></div><div><span>Milestone</span><strong>{recommendation.milestone || 'Belum ditentukan'}</strong></div></div><div className="evidence-links"><span>Dasar rekomendasi</span>{recommendation.evidence_ids.length ? [...new Set(recommendation.evidence_ids)].map(id => <button key={id} onClick={() => setSelection({ kind: 'evidence', id })}><Icon name="file" size={12}/>{id}</button>) : <small>Belum ada bukti yang ditautkan.</small>}</div><div className="approval"><h4>Persetujuan yang diperlukan</h4><StringList items={recommendation.approvals_needed} empty="Tidak ada persetujuan tambahan yang dicantumkan dalam respons analisis."/></div></> : !analyzing && !analysisError && <Empty title={context ? 'Siap memeriksa langkah berikutnya' : 'Rekomendasi belum tersedia'}>{context ? 'Jalankan analisis untuk melihat tindakan, milestone, dan preseden yang mendukungnya.' : 'Tindakan akan muncul setelah konteks dan analisis tersedia.'}</Empty>}
          </section>
          <section className="panel unknown-panel"><div className="panel-heading"><h3>Hambatan & informasi yang kurang</h3><Icon name="info" size={17}/></div><StringList items={unknowns} empty={context ? 'Belum ada hambatan atau informasi yang kurang dicantumkan. Ini bukan konfirmasi bahwa deal bebas hambatan.' : 'Menunggu konteks untuk mengidentifikasi informasi yang perlu diperiksa.'}/></section>
          <section className="panel precedent-panel"><div className="panel-heading"><h3>Belajar dari keputusan sebelumnya</h3><span className="count">{context?.candidate_decisions.length ?? '—'}</span></div><p className="muted small">Preseden membantu membandingkan kondisi. Persetujuan pada kasus lama tidak berlaku otomatis untuk deal ini.</p>
            {recommendation && <div className="comparison"><h4>Perbandingan dari analisis</h4><StringList items={recommendation.precedent_comparison} empty="Perbandingan belum dicantumkan dalam analisis."/></div>}
            {!!missingPrecedents.length && <p className="inline-warning">Preseden belum ditemukan dalam konteks: {missingPrecedents.join(', ')}.</p>}
            {!context?.candidate_decisions.length && <p className="empty-line">Belum ada kandidat preseden yang tersedia.</p>}
            {context?.candidate_decisions.map((decision, index) => <details className="precedent" key={`${text(decision.decision_id)}-${index}`}><summary><span className="precedent-marker"><Icon name="file" size={17}/></span><span><strong>{text(decision.decision_id)}</strong><small>{text(decision.keputusan)} · {text(decision.nilai)}</small></span><span className="badge neutral">{selectedPrecedents.has(text(decision.decision_id)) ? 'Dirujuk analisis' : 'Kandidat'}</span><Icon name="chevron" size={14}/></summary><div className="precedent-body"><p>{text(decision.alasan)}</p><dl><dt>Tanggal</dt><dd>{dateLabel(typeof decision.tanggal === 'string' ? decision.tanggal : null)}</dd><dt>Akun / deal</dt><dd>{text(decision.account_id)} / {text(decision.deal_id)}</dd><dt>Pengambil keputusan</dt><dd>{text(decision.diputuskan_oleh)}</dd></dl></div></details>)}
          </section>
        </>}
        {tab === 'graph' && (context ? <section className="panel graph-panel"><div className="panel-heading"><h3>Konteks yang saling terhubung</h3><span className="muted small">{context.graph.nodes.length} node · {context.graph.edges.length} relasi</span></div><ContextGraph context={context} selection={selection} onSelect={setSelection}/></section> : !loading && <section className="panel"><Empty title="Peta relasi menunggu konteks">Graph akan menampilkan hubungan yang dikirim layanan, lengkap dengan sumber buktinya.</Empty></section>)}
        {tab === 'evidence' && <section className="panel evidence-browser"><div className="panel-heading"><h3>Sumber yang mendasari deal</h3><Icon name="file" size={18}/></div>{context?.evidence.length ? context.evidence.map(e => <button key={e.id} className={`evidence-row ${selection?.kind === 'evidence' && selection.id === e.id ? 'active' : ''}`} aria-pressed={selection?.kind === 'evidence' && selection.id === e.id} onClick={() => setSelection({ kind: 'evidence', id: e.id })}><span className="evidence-row-icon"><Icon name="file" size={19}/></span><span><span className="row-between"><strong>{e.source_id}</strong><span className={`badge ${e.evidence_type}`}>{kindLabel[e.evidence_type]}</span></span><span className="excerpt-preview">{e.excerpt || 'Kutipan belum tersedia.'}</span><small>{dateLabel(e.date)} · {e.source_file}</small></span><Icon name="chevron" size={16}/></button>) : <Empty title="Bukti belum tersedia">Bukti akan muncul dari konteks deal. Ketiadaan bukti belum menjelaskan kondisi bisnisnya.</Empty>}</section>}
      </div>
    </div><EvidencePanel context={context} selection={selection} onClear={() => setSelection(null)}/></div>
  </section>;
}
