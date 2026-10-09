import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { liveApi } from './lib/api';
import type { DealApi } from './lib/api';
import { Dashboard } from './Dashboard';
import { Icon } from './components/Icon';
import './style.css';

function App() {
  const [fixtureApi, setFixtureApi] = useState<DealApi | null>(null);
  const [fixtureLoading, setFixtureLoading] = useState(false);
  const [fixtureError, setFixtureError] = useState('');
  async function toggleFixture() {
    if (!import.meta.env.DEV) return;
    if (fixtureApi) { setFixtureApi(null); return; }
    setFixtureLoading(true); setFixtureError('');
    try { const module = await import('./dev/fixture'); setFixtureApi(module.fixtureApi); }
    catch { setFixtureError('Fixture pengembangan gagal dimuat.'); }
    finally { setFixtureLoading(false); }
  }
  return <>
    <a className="skip-link" href="#main-content">Lewati ke konten utama</a>
    <header className="appbar">
      <span className="brand"><span className="brand-mark"><Icon name="compass" size={20}/></span><span className="brand-name">deal<span>compass</span></span></span>
      <span className="appbar-context">Ruang kerja sales KasirNusa</span>
      {import.meta.env.DEV && <details className="dev-tools"><summary>Alat pengembang</summary><button className="appbar-dev" onClick={toggleFixture} disabled={fixtureLoading}>{fixtureApi ? 'Kembali ke API nyata' : fixtureLoading ? 'Memuat fixture…' : 'Pratinjau fixture (dev)'}</button></details>}
    </header>
    {fixtureApi && <div className="fixture-banner" role="status"><strong>MODE PENGEMBANGAN · FIXTURE</strong><span>Contoh P02 bersumber dari dataset; graph dan rekomendasi adalah fixture UI. Bukan hasil analisis backend atau Jev.</span><button onClick={() => setFixtureApi(null)}>Kembali ke API nyata</button></div>}
    {fixtureError && <p role="alert" className="notice error">{fixtureError}</p>}
    <Dashboard key={fixtureApi ? 'fixture' : 'live'} api={fixtureApi ?? liveApi} fixture={!!fixtureApi}/>
  </>;
}
createRoot(document.getElementById('root')!).render(<App/>);
