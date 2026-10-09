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
  return <><a className="skip-link" href="#main-content">Lewati ke konten</a><div className="app-shell"><aside className="sidebar"><a className="brand" href="#main-content" aria-label="DealCompass ke konten utama"><span className="brand-mark"><Icon name="compass" size={26}/></span><span>deal<span className="brand-light">compass</span><small>CONTEXT TO ACTION</small></span></a><div className="workspace-label">WORKSPACE</div><a href="#pipeline-title" className="nav-item active"><Icon name="grid" size={19}/>Deal acceleration<span className="nav-dot"/></a><div className="sidebar-note"><span className="sidebar-note-symbol"><Icon name="graph" size={24}/></span><p>Konteks terhubung.<br/><strong>Keputusan beralasan.</strong></p><span>P01—P05 / SALES</span></div><div className="sidebar-bottom">{import.meta.env.DEV && <button className="fixture-toggle" onClick={toggleFixture} disabled={fixtureLoading}>{fixtureApi ? 'Kembali ke API nyata' : fixtureLoading ? 'Memuat fixture…' : 'Pratinjau fixture pengembangan'}</button>}<div className="team"><span className="avatar">KN</span><span>KasirNusa<small>Sales workspace</small></span><span className="team-dot"/></div></div></aside><div className="app-body">{fixtureApi && <div className="fixture-banner" role="status"><strong>MODE PENGEMBANGAN · FIXTURE</strong><span>Contoh P02 bersumber dari dataset; graph dan rekomendasi adalah fixture UI. Bukan hasil analisis backend atau Jev.</span><button onClick={() => setFixtureApi(null)}>Kembali ke API nyata</button></div>}{fixtureError && <p role="alert" className="notice error">{fixtureError}</p>}<Dashboard key={fixtureApi ? 'fixture' : 'live'} api={fixtureApi ?? liveApi} fixture={!!fixtureApi}/></div></div></>;
}
createRoot(document.getElementById('root')!).render(<App/>);
