import { useEffect, useId, useRef, useState } from 'react';
import { ApiError } from '../lib/api';
import type { DealApi } from '../lib/api';
import type { DealContext, Recommendation } from '../lib/contracts';
import type { PriorityItem } from '../lib/phase3';
import { englishText } from '../lib/english';
import { gateLabel, taskHeading } from '../lib/planning';
import { employeeFromContext, engineLabel, splitUnknowns } from '../lib/present';
import { routeQuestion } from '../lib/agent';
import type { AgentIntent } from '../lib/agent';
import { orderedDeals, usePipeline } from '../lib/usePipeline';
import { Icon } from './Icon';

type Deal = ReturnType<typeof orderedDeals>[number];
type NextStep = { recommendation: Recommendation; context: DealContext; at: string };
type Message =
  | { id: number; role: 'user'; text: string }
  | { id: number; role: 'agent'; intent: AgentIntent; deals: Deal[]; items: PriorityItem[]; status: 'loading' | 'done' | 'error'; result?: NextStep; error?: ApiError };

const time = () => new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Jakarta' }).format(new Date());

/** Conversational front door. Every answer is built from DealCompass APIs; the analysis POST runs only for a question the user sends. */
export function AgentView({ api, onOpenDeal }: { api: DealApi; onOpenDeal: (dealId: string) => void }) {
  const pipeline = usePipeline(api);
  const deals = orderedDeals(pipeline);
  const items = pipeline.priorities ? [...pipeline.priorities.items].sort((a, b) => a.rank - b.rank) : [];
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const nextId = useRef(1);
  const controllers = useRef(new Set<AbortController>());
  const end = useRef<HTMLDivElement>(null);
  const inputId = useId();
  useEffect(() => () => { controllers.current.forEach(c => c.abort()); }, []);
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }); }, [messages]);

  const top = deals.find(d => d.rank === 1) ?? null;
  const suggestions = [
    'Which deal should I follow up first?',
    ...(top ? [`What is the next step for ${top.account_name}?`] : []),
    'Which deals need an approval before we act?',
    'Where are we missing information?',
  ];

  function ask(text: string) {
    const question = text.trim();
    if (!question || pipeline.status === 'loading') return;
    const intent = routeQuestion(question, deals);
    const agentId = nextId.current + 1;
    nextId.current += 2;
    const pending: Message = { id: agentId, role: 'agent', intent, deals, items, status: intent.kind === 'next-step' ? 'loading' : 'done' };
    setMessages(list => [...list, { id: agentId - 1, role: 'user', text: question }, pending]);
    setDraft('');
    if (intent.kind !== 'next-step') return;
    const controller = new AbortController();
    controllers.current.add(controller);
    // Explicit, user-sent question: one analysis request for that deal. Ranking is not recomputed.
    Promise.all([api.context(intent.dealId, controller.signal), api.analyze(intent.dealId, controller.signal)])
      .then(([context, recommendation]) => {
        if (controller.signal.aborted) return;
        if (recommendation.deal_id !== intent.dealId || context.deal.deal_id !== intent.dealId) throw new ApiError(502, 'The answer did not match the requested deal.');
        setMessages(list => list.map(m => m.id === agentId && m.role === 'agent' ? { ...m, status: 'done', result: { recommendation, context, at: time() } } : m));
      })
      .catch(error => {
        if (controller.signal.aborted) return;
        setMessages(list => list.map(m => m.id === agentId && m.role === 'agent' ? { ...m, status: 'error', error: error instanceof ApiError ? error : new ApiError(0, 'The analysis could not be loaded.') } : m));
      })
      .finally(() => controllers.current.delete(controller));
  }

  return <section className="agent-page" aria-labelledby="agent-title">
    <header className="page-head"><h1 id="agent-title">Agent</h1><p>Ask about your pipeline</p></header>
    <div className="agent-thread" role="log" aria-live="polite" aria-label="Conversation">
      {!messages.length && <div className="agent-suggestions" aria-label="Suggested questions">
        {pipeline.status === 'loading' && <p className="status-line"><span className="spinner"/>Loading your pipeline…</p>}
        {pipeline.status === 'error' && <p className="agent-error">The pipeline could not be loaded: {pipeline.error?.message}</p>}
        {pipeline.status === 'ready' && suggestions.map((s, i) => <button key={s} className={`suggestion ${i === 0 ? 'lead' : ''}`} onClick={() => ask(s)}>{s}</button>)}
      </div>}
      {messages.map(m => m.role === 'user'
        ? <div key={m.id} className="msg user"><p>{m.text}</p></div>
        : <div key={m.id} className="msg agent"><span className="agent-avatar" aria-hidden="true"><Icon name="bot" size={18}/></span><div className="msg-body"><Answer message={m} onOpenDeal={onOpenDeal} onAsk={ask} retry={() => ask(retryText(m))}/></div></div>)}
      <div ref={end}/>
    </div>
    <form className="agent-input" onSubmit={e => { e.preventDefault(); ask(draft); }}>
      <label htmlFor={inputId} className="visually-hidden">Ask the agent</label>
      <input id={inputId} value={draft} onChange={e => setDraft(e.target.value)} placeholder={messages.length ? 'Ask a follow-up…' : 'Ask about a deal, a priority or an approval…'} autoComplete="off" disabled={pipeline.status !== 'ready'}/>
      <button type="submit" className="send" aria-label="Send question" disabled={!draft.trim() || pipeline.status !== 'ready'}><Icon name="send" size={16}/></button>
    </form>
    <p className="agent-footnote">Answers come from DealCompass analysis and the CRM snapshot{pipeline.list ? ` of ${pipeline.list.snapshot_date}` : ''}. The agent does not send messages or change records.</p>
  </section>;
}

function retryText(m: Extract<Message, { role: 'agent' }>) {
  if (m.intent.kind !== 'next-step') return '';
  const dealId = m.intent.dealId;
  return `What is the next step for ${m.deals.find(d => d.deal_id === dealId)?.account_name ?? dealId}?`;
}

function Answer({ message: m, onOpenDeal, onAsk, retry }: { message: Extract<Message, { role: 'agent' }>; onOpenDeal: (id: string) => void; onAsk: (q: string) => void; retry: () => void }) {
  const name = (id: string) => m.deals.find(d => d.deal_id === id)?.account_name ?? id;
  const intent = m.intent;
  if (intent.kind === 'unsupported') return <>
    <p>I can only answer from DealCompass data, and I could not match that question. Try one of these:</p>
    <div className="inline-suggestions">{['Which deal should I follow up first?', 'Which deals need an approval before we act?', 'Where are we missing information?'].map(q => <button key={q} className="suggestion" onClick={() => onAsk(q)}>{q}</button>)}</div>
    <p className="muted small">You can also name a customer, for example “next step for Teras Kafe”.</p>
  </>;
  if (intent.kind !== 'next-step' && !m.items.length) return <p>Priorities are unavailable right now, so I cannot rank the deals. You can still open each deal from the Deals page.</p>;
  if (intent.kind === 'priorities') {
    const first = m.items[0];
    return <>
      <p>Start with <strong>{name(first.deal_id)}</strong>. Here is the order of attention for today:</p>
      <ol className="answer-list">{m.items.map(item => <li key={item.deal_id}><button className="answer-row" onClick={() => onOpenDeal(item.deal_id)}><span className="rank">{item.rank}</span><span className="answer-main"><strong>{name(item.deal_id)}</strong><span>{taskHeading(item, 'priority').title}</span></span><span className="pill">{gateLabel(item, 'priority', item.recommendation.approvals_needed)}</span></button></li>)}</ol>
      <p className="muted small">Order of attention, not a closing probability.</p>
      <div className="answer-actions"><button className="button secondary small" onClick={() => onAsk(`What is the next step for ${name(first.deal_id)}?`)}><Icon name="spark" size={15}/>Next step for {name(first.deal_id)}</button></div>
    </>;
  }
  if (intent.kind === 'approvals') {
    const needing = m.items.filter(item => item.recommendation.approvals_needed.length);
    return needing.length ? <>
      <p>{needing.length === 1 ? 'One deal needs' : `${needing.length} deals need`} an approval before anyone acts:</p>
      <ul className="answer-list plain">{needing.map(item => <li key={item.deal_id}><strong>{name(item.deal_id)}</strong>{item.recommendation.approvals_needed.map((a, i) => <p key={i}>{englishText(a)}</p>)}<button className="link-button" onClick={() => onOpenDeal(item.deal_id)}>Open deal</button></li>)}</ul>
      <p className="muted small">A request is not an approval. Other deals list no approval, which does not mean their actions are approved.</p>
    </> : <p>No deal lists a required approval. That does not mean any action is approved.</p>;
  }
  if (intent.kind === 'gaps') return <>
    <p>Here is what is still unconfirmed for each deal:</p>
    <ul className="answer-list plain">{m.items.map(item => { const open = item.recommendation.unknowns; return <li key={item.deal_id}><strong>{name(item.deal_id)}</strong> <span className="muted">· {open.length} open {open.length === 1 ? 'question' : 'questions'}</span>{open[0] && <p>{englishText(open[0])}</p>}</li>; })}</ul>
    <p className="muted small">Missing information is not the same as no risk.</p>
  </>;
  const dealId = intent.dealId;
  if (m.status === 'loading') return <p className="status-line"><span className="spinner"/>Analysing {name(dealId)}…</p>;
  if (m.status === 'error' || !m.result) return <>
    <p className="agent-error">I could not get an analysis for {name(dealId)}: {m.error?.message ?? 'unknown error'}</p>
    <button className="button secondary small" onClick={retry}><Icon name="refresh" size={15}/>Try again</button>
  </>;
  const { recommendation: r, context, at } = m.result;
  const owner = employeeFromContext(context, r.owner_id);
  const confirm = splitUnknowns(r, context).specific;
  return <>
    <p className="answer-title"><strong>{name(dealId)}</strong><span className={`tag engine ${r.engine_mode}`}>{engineLabel[r.engine_mode]}</span></p>
    <p>{englishText(r.action)}</p>
    <dl className="answer-facts">
      <div><dt>Owner</dt><dd>{owner ? `${owner.name} (${owner.id})` : r.owner_id ?? 'Not specified'}</dd></div>
      <div><dt>Target</dt><dd>{englishText(r.milestone) || 'Not specified'}</dd></div>
      <div><dt>Approval</dt><dd>{r.approvals_needed.length ? r.approvals_needed.map((a, i) => <p key={i}>{englishText(a)}</p>) : 'None listed. This does not mean the action is approved.'}</dd></div>
      {!!confirm.length && <div><dt>Still to confirm</dt><dd>{confirm.map((u, i) => <p key={i}>{englishText(u)}</p>)}</dd></div>}
    </dl>
    <div className="answer-actions"><button className="button primary small" onClick={() => onOpenDeal(dealId)}>Open deal & evidence<Icon name="arrow" size={15}/></button></div>
    <p className="muted small">Fresh analysis at {at} WIB · {new Set(r.evidence_ids).size} cited sources · priority order not recomputed.</p>
  </>;
}
