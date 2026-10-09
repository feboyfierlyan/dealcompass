import type { DealApi } from '../lib/api';
import { englishText } from '../lib/english';
import { gateLabel } from '../lib/planning';
import { compactRupiah, priorityKindLabel } from '../lib/present';
import { orderedDeals, usePipeline } from '../lib/usePipeline';

/** Compact pipeline table. Rows open the deal workspace; no data is edited here. */
export function DealsTable({ api, onOpenDeal }: { api: DealApi; onOpenDeal: (dealId: string) => void }) {
  const pipeline = usePipeline(api);
  const deals = orderedDeals(pipeline);
  const item = (id: string) => pipeline.priorities?.items.find(i => i.deal_id === id) ?? null;
  return <section className="table-page" aria-labelledby="deals-title">
    <header className="page-head"><h1 id="deals-title">Deals</h1><p>{deals.length ? `${deals.length} open · data ${pipeline.list?.snapshot_date}` : 'Pipeline snapshot'}</p></header>
    {pipeline.status === 'loading' && <p className="status-line"><span className="spinner"/>Loading deals…</p>}
    {pipeline.status === 'error' && <p className="agent-error">Deals could not be loaded: {pipeline.error?.message}</p>}
    {pipeline.status === 'ready' && !pipeline.priorities && <p className="status-line">Priorities are unavailable. Showing CRM order.</p>}
    {!!deals.length && <table className="data-table">
      <thead><tr><th scope="col">#</th><th scope="col">Account</th><th scope="col">Stage</th><th scope="col">Annual value</th><th scope="col">Focus</th></tr></thead>
      <tbody>{deals.map(deal => { const p = item(deal.deal_id); return <tr key={deal.deal_id}>
        <td className="num">{deal.rank ?? '—'}</td>
        <th scope="row"><button className="row-link" onClick={() => onOpenDeal(deal.deal_id)}>{deal.account_name}</button></th>
        <td>{englishText(deal.stage)} <span className="muted">· {deal.stage_age_days} d</span></td>
        <td className="num">{compactRupiah(deal.annual_value)}</td>
        <td>{p ? <span className={`status-pill ${p.recommendation.approvals_needed.length ? 'warn' : p.priority_kind === 'discovery' ? 'info' : 'ok'}`}>{p.priority_kind === 'discovery' ? priorityKindLabel.discovery : gateLabel(p, 'priority', p.recommendation.approvals_needed)}</span> : <span className="muted">—</span>}</td>
      </tr>; })}</tbody>
    </table>}
  </section>;
}
