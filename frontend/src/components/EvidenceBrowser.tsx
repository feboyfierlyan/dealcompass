import { englishText, fieldLabel } from '../lib/english';
import { useState } from 'react';
import type { Evidence } from '../lib/contracts';
import { dateLabel, kindLabel } from '../lib/format';
import { evidenceTitle, interactionMeta } from '../lib/present';
import type { Selection } from './ContextGraph';
import { Icon } from './Icon';

export function EvidenceBrowser({ records, selection, onSelect }: { records: Evidence[]; selection: Selection; onSelect: (selection: Selection) => void }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const filtered = records.filter(e => `${e.id} ${e.source_id} ${e.source_file} ${e.excerpt}`.toLowerCase().includes(query.trim().toLowerCase()));
  const pages = Math.max(1, Math.ceil(filtered.length / 12));
  return <section className="evidence-browser" aria-label="All deal sources">
    <label className="field">Search all sources<input placeholder="Search names, conversations or decisions…" value={query} onChange={e => { setQuery(e.target.value); setPage(0); }}/></label>
    <p className="small muted" role="status">{filtered.length} matches of {records.length} sources · showing {Math.min(page * 12 + 1, filtered.length)}–{Math.min((page + 1) * 12, filtered.length)}</p>
    {query && <button className="text-button small" onClick={() => { setQuery(''); setPage(0); }}><Icon name="close" size={14}/>Clear search</button>}
    {!filtered.length && <p>{records.length ? 'No matching sources. Clear search to see all records.' : 'No sources available from the service.'}</p>}
    <ul className="evidence-rows">{filtered.slice(page * 12, (page + 1) * 12).map(e => {
      const { kind, title } = evidenceTitle(e), active = selection?.kind === 'evidence' && selection.id === e.id;
      return <li key={e.id}><button className={`evidence-row ${active ? 'active' : ''}`} aria-pressed={active} onClick={() => onSelect({ kind: 'evidence', id: e.id })}>
        <span className="evidence-row-main"><span className="evidence-item-head"><span className="tag">{kind}</span><span className={`tag ${e.evidence_type}`}>{kindLabel[e.evidence_type]}</span><span className="muted small">{dateLabel(e.date)}</span></span><strong>{englishText(title)}</strong><span className="excerpt-preview">{englishText(interactionMeta(e)?.message ?? '')}</span></span><Icon name="chevron" size={18}/></button></li>;
    })}</ul>
    <div className="pagination"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Previous page</button><span>Page {page + 1} of {pages}</span><button disabled={(page + 1) * 12 >= filtered.length} onClick={() => setPage(p => p + 1)}>Next page</button></div>
  </section>;
}
