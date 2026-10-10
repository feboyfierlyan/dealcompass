import { useState } from 'react';
import { Icon } from './Icon';

export type UploadedWorkspace = { workspace_id: string; name: string; snapshot_date: string; deal_count: number; source_count: number; sources: string[]; warnings: string[]; allow_jev: boolean };
export function ImportWorkspace({ onOpen, onDemo, current }: { onOpen: (w: UploadedWorkspace) => void; onDemo: () => void; current: UploadedWorkspace | null }) {
  const [file, setFile] = useState<File | null>(null);
  const [allowJev, setAllowJev] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<UploadedWorkspace | null>(null);
  async function validate() {
    if (!file || busy) return;
    setBusy(true); setError(''); setResult(null);
    try {
      if (file.size > 2_000_000) throw new Error('Choose a file smaller than 2 MB.');
      const res = await fetch(`/api/import?allow_jev=${allowJev}`, { method: 'POST', headers: { 'Content-Type': file.name.toLowerCase().endsWith('.zip') ? 'application/zip' : 'application/json' }, body: file });
      const body = await res.json();
      if (!res.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Import failed. Check the template and try again.');
      setResult(body);
    } catch (e) { setError(e instanceof Error ? e.message : 'Connection lost. Try again.'); }
    finally { setBusy(false); }
  }
  return <main className="import-page" id="main-content">
    <div className="page-head"><div><span className="eyebrow">YOUR DATA, YOUR NEXT STEP</span><h1>Bring a new sales case</h1><p>Connect CRM records and conversations. Get a fresh priority list, with evidence you can inspect.</p></div></div>
    <div className="import-grid"><section className="import-card">
      <h2><span className="step-number">1</span>Start with the template</h2>
      <p>Add your accounts, deals, sales owners and transcripts. Match conversations to accounts using their IDs.</p>
      <a className="button secondary" href="/api/import/template" download="dealcompass-example.json"><Icon name="file" size={16}/>Download example JSON</a> <a className="button secondary" href="/api/import/template.zip" download="dealcompass-csv-kit.zip">CSV + transcript kit</a>
      <details><summary>File format & supported data</summary><p>JSON contains a name, snapshot_date (YYYY-MM-DD), and tables. Each table is an array of rows. Keep column names from the template; enter values as text or whole numbers. Values are in IDR.</p><p>Stages: Lead, Discovery, Demo, Proposal, Negosiasi. Open deals: status Terbuka and account tipe prospek. Up to 20 deals, one per account, and 2,000 total rows.</p><p>For CSV: ZIP the standard CSV files, interactions.jsonl and manifest.json at the ZIP root. Manifest contains name and snapshot_date. Optional tables include decision_log.csv, support_tickets.csv, product_usage_daily.csv, feature_usage_monthly.csv and contact_employment_history.csv. Missing sources remain missing; no evidence is invented.</p><p>This version accepts structured CRM and transcript records, not PDFs, audio, or arbitrary spreadsheets. KasirNusa policy applies: IDR 350,000/outlet/month, Starter/Growth/Enterprise packages, discounts above 10% require VP Sales approval. The template includes a fictional example conversation; replace it with your own records.</p></details>
    </section><section className="import-card">
      <h2><span className="step-number">2</span>Upload & validate</h2>
      <label className="upload-drop"><Icon name="plus" size={24}/><strong>{file?.name || 'Choose your data file'}</strong><span>JSON or ZIP · up to 2 MB</span><input aria-label="Dataset file" type="file" accept=".json,.zip" disabled={busy} onChange={e => { setFile(e.target.files?.[0] ?? null); setResult(null); setError(''); }}/></label>
      <label className="consent-check"><input type="checkbox" checked={allowJev} disabled={busy} onChange={e=>{setAllowJev(e.target.checked);setResult(null);}}/><span>Use Jev with this upload<small>Relevant conversation text and evidence will be sent to TypeSafe for analysis. Leave off to keep analysis on this server.</small></span></label>
      <p className="muted">Separate workspace; access expires after 24 hours. The original demo stays unchanged. Keep your source file; uploading a revision creates a new workspace.</p>
      <button className="button primary" disabled={!file || busy} onClick={()=>void validate()}>{busy ? 'Checking data…' : 'Validate data'}<Icon name="arrow" size={16}/></button>
      {busy && <p role="status">Checking IDs, dates, graph links and recommendations…</p>}{error && <p role="alert" className="notice error">{error}</p>}
    </section></div>
    {result && <section className="import-result" aria-live="polite"><div><span className="eyebrow">READY TO EXPLORE</span><h2>{result.name}</h2><p>{result.deal_count} deals · {result.source_count} source tables · Snapshot {result.snapshot_date}</p></div><ul>{result.warnings.map(w=><li key={w}>{w}</li>)}</ul><button className="button primary" onClick={()=>onOpen(result)}>Open workspace<Icon name="arrow" size={16}/></button></section>}
    {current && <button className="text-button" onClick={onDemo}>Return to KasirNusa demo</button>}
  </main>;
}
