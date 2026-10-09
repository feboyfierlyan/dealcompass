import { useEffect, useState } from 'react';
import { ApiError } from './lib/api';
import type { DealApi } from './lib/api';
import type { DealList } from './lib/contracts';
import { dateLabel, rupiah, statusLabel } from './lib/format';
import { Icon } from './components/Icon';
import { DealWorkspace, ErrorNotice } from './components/DealWorkspace';
import './style.css';

export function Dashboard({ api, fixture }: { api: DealApi; fixture: boolean }) {
  const [data, setData] = useState<DealList | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null); setData(null);
    api.list(controller.signal).then(result => {
      if (controller.signal.aborted) return;
      setData(result); setSelected(current => result.items.some(d => d.deal_id === current) ? current : result.items[0]?.deal_id ?? null);
    }).catch(e => { if (!controller.signal.aborted) setError(e instanceof ApiError ? e : new ApiError(0, 'Daftar deal belum dapat dimuat.')); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [api, refresh]);
  const deals = data?.items ?? [];
  const visible = deals.filter(d => `${d.account_name} ${d.account_id} ${d.deal_id}`.toLowerCase().includes(search.toLowerCase().trim()));
  const active = deals.find(d => d.deal_id === selected);
  const rankCount = deals.filter(d => d.rank !== null).length;
  const total = deals.reduce((sum, d) => sum + d.annual_value, 0);
  return <>
    <header className="topbar"><div><span className="breadcrumb">Ruang kerja sales</span><Icon name="chevron" size={12}/><strong>Deal acceleration</strong></div><span className="snapshot"><Icon name="clock" size={14}/>{data ? `Snapshot ${dateLabel(data.snapshot_date)}` : 'Snapshot belum dimuat'}</span></header>
    <main id="main-content"><div className="page-heading"><div><p className="eyebrow orange">PIPELINE INTELLIGENCE</p><h1>Langkah tepat.<br/><span>Deal bergerak.</span></h1><p>Hubungkan konteks, periksa bukti, tentukan langkah berikutnya.</p></div><div className="page-heading-aside"><span className="live-label"><i/>{fixture ? 'Fixture pengembangan' : 'Sumber data CRM'}</span><button className="button secondary" disabled={loading} onClick={() => setRefresh(v => v + 1)}><Icon name="refresh" size={15}/>Muat ulang</button></div></div>
      <div className="metrics"><div className="metric"><span>Potensi pipeline tahunan</span><strong>{data ? rupiah(total) : '—'}</strong><small>Nilai peluang, belum menjadi pendapatan</small></div><div className="metric"><span>Deal dalam cakupan</span><strong>{data ? String(deals.length).padStart(2, '0') : '—'}<em> / P01–P05</em></strong><small>Setiap prospek punya konteksnya sendiri</small></div><div className="metric"><span>Prioritas dari analisis</span><strong className="metric-text">{data ? rankCount ? `${rankCount} deal memiliki ranking` : 'Belum tersedia' : 'Menunggu data'}</strong><small>Urutan kartu mengikuti sumber data</small></div></div>
      <section className="pipeline" aria-labelledby="pipeline-title"><div className="section-heading"><div><h2 id="pipeline-title">Pilih deal untuk ditelusuri <span>{data ? String(deals.length).padStart(2, '0') : '—'}</span></h2><p className="muted small">Periksa konteks dan tindakan berikutnya untuk setiap prospek.</p></div><label className="search"><Icon name="search" size={17}/><input aria-label="Cari deal" placeholder="Cari nama atau ID deal" value={search} onChange={e => setSearch(e.target.value)}/>{search && <button aria-label="Hapus pencarian" onClick={() => setSearch('')}>×</button>}</label></div>
        {loading && <div className="deal-grid" role="status" aria-label="Memuat daftar deal">{Array.from({ length: 5 }, (_, i) => <div className="skeleton-card" key={i}><i/><i/><i/></div>)}</div>}
        {error && <ErrorNotice error={error} retry={() => setRefresh(v => v + 1)} subject="Daftar deal"/>}
        {!loading && !error && !deals.length && <div className="panel empty-state"><Icon name="grid" size={30}/><h3>Belum ada deal dalam daftar</h3><p>Layanan mengembalikan daftar kosong. Muat ulang setelah data tersedia.</p><button className="button secondary" onClick={() => setRefresh(v => v + 1)}>Muat ulang</button></div>}
        {!loading && !!deals.length && !visible.length && <div className="search-empty" role="status">Tidak ada deal yang cocok dengan “{search}”. <button className="text-button" onClick={() => setSearch('')}>Tampilkan semua</button></div>}
        <div className="deal-grid">{visible.map(deal => <button key={deal.deal_id} className={`deal-card ${selected === deal.deal_id ? 'active' : ''}`} aria-pressed={selected === deal.deal_id} aria-label={`${deal.account_id} ${deal.account_name}`} onClick={() => setSelected(deal.deal_id)}><span className="row-between"><span className="account-id">{deal.account_id}</span><span className="stage">{deal.stage}</span></span><strong className="deal-name">{deal.account_name}</strong><span className="deal-value">{rupiah(deal.annual_value)}<small> / tahun</small></span><span className="deal-age"><Icon name="clock" size={13}/>{deal.stage_age_days} hari di tahap ini</span><span className="card-footer"><span><span className="rank-label">{deal.rank === null ? 'Prioritas belum tersedia' : `Prioritas #${deal.rank}`}</span><small>Status API: {statusLabel[deal.analysis_status]}</small></span><span className="card-arrow"><Icon name="arrow" size={16}/></span></span></button>)}</div>
      </section>
      {active && !loading && <DealWorkspace key={`${fixture}-${active.deal_id}-${refresh}`} deal={active} api={api} fixture={fixture}/>}
      <footer className="page-footer"><span>DEALCOMPASS <span> / </span> KasirNusa</span><span>Keputusan yang bisa ditelusuri.</span></footer>
    </main>
  </>;
}
