// Development-only harness: same Dashboard/DealWorkspace, deliberately synthetic responses.
import { useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Dashboard } from '../Dashboard';
import { ApiError } from '../lib/api';
import type { DealApi } from '../lib/api';
import { fixtureList } from './fixture';

function Harness() {
  const [mode, setMode] = useState('success');
  const selectedMode = useRef(mode); selectedMode.current = mode;
  const api = useMemo<DealApi>(() => ({
    list: async () => fixtureList,
    context: async id => ({
      schema_version: 'v1', snapshot_date: '2026-10-01', deal: fixtureList.items.find(d => d.deal_id === id)!,
      evidence: [], graph: { nodes: [], edges: [] }, candidate_decisions: [], unknowns: ['MOCK: tidak ada bukti bisnis pada harness ini.'],
    }),
    analyze: async id => {
      const current = selectedMode.current;
      // Intentionally ignores AbortSignal to exercise protection against late callbacks.
      if (current.startsWith('late')) await new Promise(resolve => setTimeout(resolve, 2500));
      if (current.includes('error')) throw new ApiError(503, 'MOCK HTTP 503 untuk uji retry.');
      return { schema_version: 'v1', deal_id: id, action: `MOCK usulan untuk ${id}`, owner_id: null, milestone: 'MOCK milestone', evidence_ids: [], precedent_ids: [], precedent_comparison: [], approvals_needed: [], unknowns: ['MOCK: bukan analisis nyata.'], engine_mode: 'replay' };
    },
  }), []);
  return <><div className="fixture-banner"><strong>MOCK REQUEST TEST · BUKAN DATA ANALISIS NYATA</strong><label>Respons berikutnya <select aria-label="Respons mock" value={mode} onChange={e => setMode(e.target.value)}><option value="success">Sukses segera</option><option value="error">Gagal 503</option><option value="late-success">Sukses terlambat 2,5 detik</option><option value="late-error">Gagal terlambat 2,5 detik</option></select></label></div><Dashboard api={api} fixture/></>;
}
if (import.meta.env.DEV) createRoot(document.getElementById('root')!).render(<Harness/>);
