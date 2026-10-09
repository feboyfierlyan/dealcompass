import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type Deal = { deal_id: string; account_id: string; account_name: string; stage: string; stage_age_days: number; annual_value: number; rank: number | null; analysis_status: string };
const money = new Intl.NumberFormat('id-ID', {style: 'currency', currency: 'IDR', maximumFractionDigits: 0});

function App() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/deals', {signal: controller.signal}).then(r => {if (!r.ok) throw new Error(`API ${r.status}`); return r.json();})
      .then(data => setDeals(data.items)).catch(e => {if (e.name !== 'AbortError') setError('Daftar deal belum dapat dimuat. Pastikan backend berjalan pada port 8000.');})
      .finally(() => {if (!controller.signal.aborted) setLoading(false);});
    return () => controller.abort();
  }, []);
  return <main>
    <p className="eyebrow">KASIRNUSA · SNAPSHOT 1 OKTOBER 2026</p>
    <h1>DealCompass</h1>
    <p>Peluang penjualan dan bukti untuk menentukan tindakan berikutnya.</p>
    <aside>Fondasi proyek: daftar bersumber dari CRM. Graph dan analisis sedang dikerjakan; urutan di bawah belum merupakan ranking prioritas.</aside>
    {loading && <p role="status">Memuat data…</p>}
    {error && <p role="alert">{error}</p>}
    {!loading && !error && <section aria-label="Daftar prospek">
      {deals.map(d => <article key={d.deal_id}>
        <p className="eyebrow">{d.account_id} · {d.deal_id}</p><h2>{d.account_name}</h2>
        <p>{d.stage} · {d.stage_age_days} hari di tahap ini</p>
        <strong>{money.format(d.annual_value)} / tahun</strong><p className="muted">Belum dianalisis</p>
      </article>)}
    </section>}
  </main>;
}
createRoot(document.getElementById('root')!).render(<App/>);

