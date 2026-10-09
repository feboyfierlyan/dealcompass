import { useId } from 'react';
import { ApiError } from '../lib/api';
import type { DealContext } from '../lib/contracts';
import type { EvidencePath, PriorityItem } from '../lib/phase3';
import { dateLabel } from '../lib/format';
import { evidenceTitle, gateSummary, interactionMeta, obstacleEvidence, recommendationView } from '../lib/present';
import { ActionSummary, ExplanationGroups, PrecedentList, RecommendationSources, UnknownList } from './AnalysisReport';
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
  if (!priority) return <section className="why-block" aria-labelledby={titleId}><h3 id={titleId}>Mengapa perlu diperhatikan</h3>
    <p className="muted">{rankingState === 'loading' ? 'Menunggu urutan prioritas…' : rankingState === 'error' ? 'Alasan prioritas belum tersedia karena urutan prioritas gagal dimuat.' : 'Alasan prioritas tidak tersedia pada mode ini.'}</p></section>;
  const quotes = obstacleEvidence(priority, context);
  const gate = gateSummary(priority);
  return <section className="why-block" aria-labelledby={titleId}>
    <h3 id={titleId}>Mengapa perlu diperhatikan</h3>
    {priority.priority_kind === 'discovery' && <p className="lead">Informasi tentang deal ini belum cukup untuk menilai hambatannya, jadi langkah pertamanya melengkapi informasi. Ini bukan tanda deal gagal, kalah, atau bebas risiko.</p>}
    {quotes.map(e => {
      const meta = interactionMeta(e), { kind, title } = evidenceTitle(e);
      return <figure className="quote" key={e.id}><blockquote>{meta?.message ? `“${meta.message}”` : title}</blockquote>
        <figcaption><span>{kind} · {dateLabel(e.date)}{meta?.from ? ` · dari ${meta.from}` : ''}</span><button className="link-button" onClick={() => onEvidence(e.id)}>Lihat bukti {e.source_id}</button></figcaption></figure>;
    })}
    {gate && <p className="gate-line"><Icon name="flag" size={16}/><span>Syarat utama menurut analisis prioritas: <strong>{gate}</strong></span></p>}
  </section>;
}

export function ActionTab({ context, priority, rankingState, view, fixture, snapshot, session, onEvidence, onReasons, onShowPaths, onAnalyze, onShowVersion }: {
  context: DealContext | null; priority: PriorityItem | null; rankingState: RankingState; view: View; fixture: boolean; snapshot: string | null;
  session: SessionInfo; onEvidence: OpenEvidence; onReasons: () => void; onShowPaths: () => void; onAnalyze: () => void; onShowVersion: (v: 'priority' | 'session') => void;
}) {
  const r = view.recommendation;
  const running = session.status === 'running';
  const rerunNote = useId();
  const pathsLabel = view.source === 'session' ? 'Lihat hubungan data dari analisis prioritas' : 'Lihat hubungan yang mendukung saran ini';
  return <div className="tab-stack">
    <WhyBlock priority={priority} context={context} rankingState={rankingState} onEvidence={onEvidence}/>
    {r ? <ActionSummary recommendation={r} context={context} fixture={fixture} onEvidence={onEvidence} actions={<>
      <button className="button primary" onClick={onReasons}>Lihat alasan & bukti<Icon name="arrow" size={17}/></button>
      <button className="button secondary" onClick={onShowPaths} disabled={!priority?.evidence_paths.length}><Icon name="graph" size={17}/>{pathsLabel}</button>
    </>}/>
      : rankingState === 'loading' && !running && session.status !== 'failed' ? <div className="action-card skeleton" role="status"><span className="visually-hidden">Menyiapkan saran dari urutan prioritas</span><i/><i/><i/></div>
      : <section className="action-card empty"><h3>Saran untuk deal ini belum tersedia</h3>
        <p>{rankingState === 'error' ? 'Urutan prioritas gagal dimuat, sehingga saran yang dipakai untuk prioritas belum bisa ditampilkan.' : 'Saran dari urutan prioritas tidak tersedia pada mode ini.'} Anda dapat meminta analisis khusus untuk deal ini.</p>
        {!running && session.status !== 'failed' && <div className="action-buttons"><button className="button primary" onClick={onAnalyze}><Icon name="arrow" size={17}/>Jalankan analisis untuk deal ini</button></div>}
        {running && <p className="status-line" role="status"><span className="spinner"/>Menjalankan analisis…</p>}
        {session.status === 'failed' && session.error && <ErrorNotice error={session.error} retry={onAnalyze} subject="Analisis"/>}
      </section>}
    {r && <section className="origin" aria-label="Asal saran">
      <div className="origin-row">
        <p><Icon name="history" size={16}/>{view.source === 'session'
          ? `Hasil analisis ulang yang Anda minta${session.receivedAt ? ` pukul ${session.receivedAt}` : ''} · urutan prioritas tidak dihitung ulang`
          : `Dari urutan prioritas${snapshot ? ` · data per ${dateLabel(snapshot)}` : ''}`}</p>
        <button className="button tertiary" onClick={onAnalyze} disabled={running} aria-describedby={rerunNote}><Icon name="refresh" size={15}/>{running ? 'Menjalankan analisis ulang…' : 'Jalankan analisis ulang'}</button>
        <span id={rerunNote} className="visually-hidden">Meminta hasil baru untuk deal ini saja. Urutan prioritas tidak berubah.</span>
      </div>
      {view.hasPriority && view.hasSession && <div className="segmented" role="group" aria-label="Versi saran yang ditampilkan">
        <button aria-pressed={view.source === 'priority'} onClick={() => onShowVersion('priority')}>Saran dari urutan prioritas</button>
        <button aria-pressed={view.source === 'session'} onClick={() => onShowVersion('session')}>Hasil analisis ulang{session.receivedAt ? ` · ${session.receivedAt}` : ''}</button>
      </div>}
      <p className="status-line small" role="status">{running ? 'Analisis ulang sedang berjalan. Saran yang tampil belum berubah.' : session.status === 'received' && view.source === 'priority' ? 'Hasil analisis ulang sudah diterima; pilih versinya di atas untuk melihat.' : ''}</p>
      {session.status === 'failed' && session.error && <ErrorNotice error={session.error} retry={onAnalyze} subject="Analisis ulang"/>}
    </section>}
  </div>;
}

export function ReasonsTab({ priority, view, context, onEvidence, onEdge, onShowPath }: { priority: PriorityItem | null; view: View; context: DealContext; onEvidence: OpenEvidence; onEdge: (id: string) => void; onShowPath: (path: EvidencePath) => void }) {
  const r = view.recommendation;
  return <div className="tab-stack">
    {r && view.hasPriority && view.hasSession && <p className="version-note">Bukti dan penjelasan di bawah mengikuti <strong>{view.source === 'session' ? 'hasil analisis ulang' : 'saran dari urutan prioritas'}</strong>.</p>}
    {r && <RecommendationSources ids={r.evidence_ids} context={context} onEvidence={onEvidence}/>}
    {r && <PrecedentList recommendation={r} context={context} onEvidence={onEvidence}/>}
    {priority && <EvidencePaths item={priority} context={context} onEvidence={onEvidence} onEdge={onEdge} onShowPath={onShowPath}/>}
    {priority ? <PriorityRationale item={priority}/> : <p className="muted">Alasan urutan prioritas belum tersedia.</p>}
    {r && <ExplanationGroups recommendation={r}/>}
    {r && <UnknownList recommendation={r} context={context}/>}
    {!r && <p className="muted">Bukti dan penjelasan saran akan tampil setelah saran tersedia.</p>}
  </div>;
}
