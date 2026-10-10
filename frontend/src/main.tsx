import { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { liveApi, workspaceApi } from './lib/api';
import type { DealApi } from './lib/api';
import { Dashboard } from './Dashboard';
import { DealsTable } from './components/DealsTable';
import { Icon } from './components/Icon';
import type { IconName } from './components/Icon';
import './style.css';
import './shell.css';
import './light.css';
import { ImportWorkspace } from './components/ImportWorkspace';
import type { UploadedWorkspace } from './components/ImportWorkspace';
import { Onboarding } from './components/Onboarding';

type View = 'priorities' | 'deals' | 'import';
const NAV: { id: View; label: string; icon: IconName }[] = [
  { id: 'priorities', label: 'Priorities', icon: 'target' },
  { id: 'deals', label: 'Deals', icon: 'table' },
  { id: 'import', label: 'Your data', icon: 'plus' },
];

function App() {
  const [uploaded, setUploaded] = useState<UploadedWorkspace | null>(()=>{try { return JSON.parse(sessionStorage.getItem('dealcompass.workspace') || 'null'); } catch { return null; }});
  const scopedApi = useMemo(()=>uploaded ? workspaceApi(uploaded.workspace_id) : liveApi,[uploaded]);
  const [tour, setTour] = useState(()=>{try { return !localStorage.getItem('dealcompass.tour.v1'); } catch { return true; }});
  function closeTour() { setTour(false); try { localStorage.setItem('dealcompass.tour.v1','done'); } catch { /* Optional preference. */ } }
  function selectWorkspace(value: UploadedWorkspace | null) { setUploaded(value); try { value ? sessionStorage.setItem('dealcompass.workspace',JSON.stringify(value)) : sessionStorage.removeItem('dealcompass.workspace'); } catch { /* Works in-memory if storage is unavailable. */ } setFixtureApi(null); setOpenDeal(null); setView('priorities'); }
  const [view, setView] = useState<View>('priorities');
  const [openDeal, setOpenDeal] = useState<{ id: string; seq: number } | null>(null);
  const [fixtureApi, setFixtureApi] = useState<DealApi | null>(null);
  const [fixtureLoading, setFixtureLoading] = useState(false);
  const [fixtureError, setFixtureError] = useState('');
  async function toggleFixture() {
    if (!import.meta.env.DEV) return;
    if (fixtureApi) { setFixtureApi(null); return; }
    setFixtureLoading(true); setFixtureError('');
    try { const module = await import('./dev/fixture'); setFixtureApi(module.fixtureApi); }
    catch { setFixtureError('Could not load development fixtures.'); }
    finally { setFixtureLoading(false); }
  }
  const api = fixtureApi ?? scopedApi;
  function goToDeal(id: string) { setOpenDeal(current => ({ id, seq: (current?.seq ?? 0) + 1 })); setView('priorities'); }
  const title = NAV.find(n => n.id === view)!.label;
  return <div className="shell">
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <aside className="sidebar" aria-label="Workspace">
      <div className="sidebar-workspace"><span className="sidebar-workspace-mark" aria-hidden="true">K</span><span className="sidebar-workspace-sep">/</span><strong>{uploaded?.name ?? 'KasirNusa'}</strong></div>
      <nav aria-label="Main">{NAV.map(item => <button key={item.id} data-tour={item.id} className="nav-link" aria-current={view === item.id ? 'page' : undefined} onClick={() => setView(item.id)}><Icon name={item.icon} size={17}/>{item.label}</button>)}</nav>
      <div className="sidebar-foot">
        <button className="nav-link" onClick={()=>{setView('priorities');setTour(true);}}><Icon name="info" size={16}/>Quick tour</button>
        {uploaded && <button className="nav-link" onClick={()=>selectWorkspace(null)}>Return to demo</button>}
        <span className="brand-line"><Icon name="compass" size={15}/>DealCompass</span>
        {import.meta.env.DEV && <button className="nav-link dev" onClick={toggleFixture} disabled={fixtureLoading}>{fixtureApi ? 'Return to live API' : fixtureLoading ? 'Loading fixtures…' : 'Preview fixtures (dev)'}</button>}
      </div>
    </aside>
    <div className="shell-main">
      <header className="topbar"><span className="crumb">{title}</span>{view === 'priorities' && <span className="crumb-note">Order of attention · not a closing probability</span>}</header>
      {fixtureApi && <div className="fixture-banner" role="status"><strong>DEVELOPMENT · FIXTURE</strong><span>P02 example from the dataset; graph and recommendations are UI fixtures, not backend or Jev results.</span><button onClick={() => setFixtureApi(null)}>Return to live API</button></div>}
      {fixtureError && <p role="alert" className="notice error">{fixtureError}</p>}
      <div className="shell-content" id={view === 'priorities' ? undefined : 'main-content'}>
        {view === 'import' && <ImportWorkspace current={uploaded} onOpen={selectWorkspace} onDemo={()=>selectWorkspace(null)}/>}
        {view === 'deals' && <DealsTable key={fixtureApi ? 'fixture' : uploaded?.workspace_id ?? 'live'} api={api} onOpenDeal={goToDeal}/>}
        {view === 'priorities' && <Dashboard key={`${fixtureApi ? 'fixture' : uploaded?.workspace_id ?? 'live'}-${openDeal?.seq ?? 0}`} api={api} fixture={!!fixtureApi} initialDeal={openDeal?.id ?? null}/>}
      </div>
    </div>
    {tour && <Onboarding onClose={closeTour}/>}
  </div>;
}
createRoot(document.getElementById('root')!).render(<App/>);
