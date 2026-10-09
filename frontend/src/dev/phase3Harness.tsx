// Development-only transport controls. Successful responses still come from the real local API.
import { useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Dashboard } from '../Dashboard';
import { ApiError, liveApi } from '../lib/api';
import type { DealApi } from '../lib/api';
function Harness() {
  const [target,setTarget] = useState('priorities'), [mode,setMode] = useState('success');
  const controls = useRef({target,mode}); controls.current = {target,mode};
  const api = useMemo<DealApi>(() => {
    async function transport<T>(name: string, signal: AbortSignal, load: (signal: AbortSignal) => Promise<T>) {
      const settings = controls.current;
      if (settings.target !== name || settings.mode === 'success') return load(signal);
      if (settings.mode.startsWith('late')) await new Promise(resolve => setTimeout(resolve,2500));
      if (settings.mode.includes('error')) throw new ApiError(503, 'MOCK TRANSPORT: simulasi 503, bukan gangguan backend nyata.');
      // Deliberately ignore the old signal to exercise the generation guard.
      return load(new AbortController().signal);
    }
    return {...liveApi,
      priorities: s => transport('priorities',s,liveApi.priorities!),
      diagnostics: s => transport('diagnostic',s,liveApi.diagnostics!),
      diagnostic: (id,s) => transport('diagnostic',s,signal => liveApi.diagnostic!(id,signal)),
    };
  },[]);
  return <><div className="fixture-banner"><strong>MOCK TRANSPORT TEST · error/delay sintetis; respons sukses API lokal rules</strong><label>Endpoint <select aria-label="Target mock" value={target} onChange={e=>setTarget(e.target.value)}><option value="priorities">Ranking</option><option value="diagnostic">Diagnostic</option></select></label><label>Respons <select aria-label="Mode mock" value={mode} onChange={e=>setMode(e.target.value)}><option value="success">Sukses API</option><option value="error">Gagal 503</option><option value="late-success">Sukses terlambat 2,5 detik</option><option value="late-error">Gagal terlambat 2,5 detik</option></select></label></div><Dashboard api={api} fixture={false}/></>;
}
if(import.meta.env.DEV) createRoot(document.getElementById('root')!).render(<Harness/>);
