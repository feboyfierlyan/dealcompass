import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { liveApi } from './lib/api';
import type { DealApi } from './lib/api';
import { Dashboard } from './Dashboard';
import { AgentView } from './components/AgentView';
import { DealsTable } from './components/DealsTable';
import { Icon } from './components/Icon';
import type { IconName } from './components/Icon';
import './style.css';
import './shell.css';

type View = 'agent' | 'priorities' | 'deals';
const NAV: { id: View; label: string; icon: IconName }[] = [
  { id: 'agent', label: 'Agent', icon: 'bot' },
  { id: 'priorities', label: 'Priorities', icon: 'target' },
  { id: 'deals', label: 'Deals', icon: 'table' },
];

function App() {
  const [view, setView] = useState<View>('agent');
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
  const api = fixtureApi ?? liveApi;
  function goToDeal(id: string) { setOpenDeal(current => ({ id, seq: (current?.seq ?? 0) + 1 })); setView('priorities'); }
  const title = NAV.find(n => n.id === view)!.label;
  return <div className="shell">
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <aside className="sidebar" aria-label="Workspace">
      <div className="workspace"><span className="workspace-mark" aria-hidden="true">K</span><span className="workspace-sep">/</span><strong>KasirNusa</strong></div>
      <nav aria-label="Main">{NAV.map(item => <button key={item.id} className="nav-link" aria-current={view === item.id ? 'page' : undefined} onClick={() => setView(item.id)}><Icon name={item.icon} size={17}/>{item.label}</button>)}</nav>
      <div className="sidebar-foot">
        <span className="brand-line"><Icon name="compass" size={15}/>DealCompass</span>
        {import.meta.env.DEV && <button className="nav-link dev" onClick={toggleFixture} disabled={fixtureLoading}>{fixtureApi ? 'Return to live API' : fixtureLoading ? 'Loading fixtures…' : 'Preview fixtures (dev)'}</button>}
      </div>
    </aside>
    <div className="shell-main">
      <header className="topbar"><span className="crumb">{title}</span>{view === 'priorities' && <span className="crumb-note">Order of attention · not a closing probability</span>}</header>
      {fixtureApi && <div className="fixture-banner" role="status"><strong>DEVELOPMENT · FIXTURE</strong><span>P02 example from the dataset; graph and recommendations are UI fixtures, not backend or Jev results.</span><button onClick={() => setFixtureApi(null)}>Return to live API</button></div>}
      {fixtureError && <p role="alert" className="notice error">{fixtureError}</p>}
      <div className="shell-content" id={view === 'priorities' ? undefined : 'main-content'}>
        {view === 'agent' && <AgentView key={fixtureApi ? 'fixture' : 'live'} api={api} onOpenDeal={goToDeal}/>}
        {view === 'deals' && <DealsTable key={fixtureApi ? 'fixture' : 'live'} api={api} onOpenDeal={goToDeal}/>}
        {view === 'priorities' && <Dashboard key={`${fixtureApi ? 'fixture' : 'live'}-${openDeal?.seq ?? 0}`} api={api} fixture={!!fixtureApi} initialDeal={openDeal?.id ?? null}/>}
      </div>
    </div>
  </div>;
}
createRoot(document.getElementById('root')!).render(<App/>);
