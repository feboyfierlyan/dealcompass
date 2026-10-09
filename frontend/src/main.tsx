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
    catch { setFixtureError('Could not load development fixtures.'); }
    finally { setFixtureLoading(false); }
  }
  return <>
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <header className="appbar">
      <span className="brand"><span className="brand-mark"><Icon name="compass" size={20}/></span><span className="brand-name">deal<span>compass</span></span></span>
      <span className="appbar-context">Workspace / Deal acceleration</span>
      {import.meta.env.DEV && <details className="dev-tools"><summary>Developer tools</summary><button className="appbar-dev" onClick={toggleFixture} disabled={fixtureLoading}>{fixtureApi ? 'Return to live API' : fixtureLoading ? 'Loading fixtures…' : 'Preview fixtures (dev)'}</button></details>}
    </header>
    {fixtureApi && <div className="fixture-banner" role="status"><strong>DEVELOPMENT · FIXTURE</strong><span>P02 example from the dataset; graph and recommendations are UI fixtures, not backend or Jev results.</span><button onClick={() => setFixtureApi(null)}>Return to live API</button></div>}
    {fixtureError && <p role="alert" className="notice error">{fixtureError}</p>}
    <Dashboard key={fixtureApi ? 'fixture' : 'live'} api={fixtureApi ?? liveApi} fixture={!!fixtureApi}/>
  </>;
}
createRoot(document.getElementById('root')!).render(<App/>);
