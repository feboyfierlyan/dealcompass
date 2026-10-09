import { useState } from 'react';
import type { Evidence } from '../lib/contracts';
import { evidenceExcerpt } from '../lib/graphView';
import { dateLabel, kindLabel } from '../lib/format';
import type { Selection } from './ContextGraph';
import { Icon } from './Icon';

export function EvidenceBrowser({ records, selection, onSelect }: { records: Evidence[]; selection: Selection; onSelect: (selection: Selection) => void }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const filtered = records.filter(e => `${e.id} ${e.source_id} ${e.source_file} ${e.excerpt}`.toLowerCase().includes(query.trim().toLowerCase()));
  return <section className="panel evidence-browser"><div className="panel-heading"><h3>Sumber yang mendasari deal</h3><Icon name="file" size={18}/></div>
    <label className="evidence-search">Cari seluruh bukti<input placeholder="ID, nama file, atau isi sumber" value={query} onChange={e => { setQuery(e.target.value); setPage(0); }}/></label>
    <p className="small muted" role="status">{filtered.length} cocok dari {records.length} bukti · menampilkan {Math.min(page * 12 + 1, filtered.length)}–{Math.min((page + 1) * 12, filtered.length)}</p>
    {!filtered.length && <p>{records.length ? 'Tidak ada bukti yang cocok. Hapus pencarian untuk melihat semua sumber.' : 'Bukti belum tersedia dari layanan.'}</p>}
    {filtered.slice(page * 12, (page + 1) * 12).map(e => <button key={e.id} className={`evidence-row ${selection?.kind === 'evidence' && selection.id === e.id ? 'active' : ''}`} aria-pressed={selection?.kind === 'evidence' && selection.id === e.id} onClick={() => onSelect({ kind: 'evidence', id: e.id })}><span className="evidence-row-icon"><Icon name="file" size={19}/></span><span><span className="row-between"><strong>{e.source_id}</strong><span className={`badge ${e.evidence_type}`}>{kindLabel[e.evidence_type]}</span></span><span className="excerpt-preview">{evidenceExcerpt(e.excerpt).text || 'Kutipan belum tersedia.'}</span><small>{dateLabel(e.date)} · {e.source_file}</small></span><Icon name="chevron" size={16}/></button>)}
    <div className="pagination"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Halaman sebelumnya</button><span>Halaman {page + 1} / {Math.max(1, Math.ceil(filtered.length / 12))}</span><button disabled={(page + 1) * 12 >= filtered.length} onClick={() => setPage(p => p + 1)}>Halaman berikutnya</button></div>
  </section>;
}
