// Agent question routing. The agent only answers from DealCompass APIs; it never generates free text.
// Type-only imports keep this module runnable by node --test without a build step.
import type { Deal } from './contracts';

export type AgentIntent =
  | { kind: 'priorities' }
  | { kind: 'approvals' }
  | { kind: 'gaps' }
  | { kind: 'next-step'; dealId: string }
  | { kind: 'unsupported' };

const STOP = new Set(['group', 'hotel', 'resto', 'klinik', 'pratama', 'distribusi', 'the', 'and']);

/** Find the deal a question names, by deal ID, account ID or a distinctive word of the account name. */
export function findDeal(text: string, deals: Pick<Deal, 'deal_id' | 'account_id' | 'account_name'>[]) {
  const q = ` ${text.toLowerCase().replace(/[^a-z0-9-]+/g, ' ')} `;
  for (const deal of deals) {
    if (q.includes(` ${deal.deal_id.toLowerCase()} `) || q.includes(` ${deal.account_id.toLowerCase()} `)) return deal.deal_id;
  }
  for (const deal of deals) {
    const words = deal.account_name.toLowerCase().split(/[^a-z0-9]+/).filter(w => w.length > 3 && !STOP.has(w));
    if (words.some(w => q.includes(` ${w} `))) return deal.deal_id;
  }
  return null;
}

/** Map a typed question to one of the supported answers. Unknown questions are never guessed. */
export function routeQuestion(text: string, deals: Pick<Deal, 'deal_id' | 'account_id' | 'account_name'>[]): AgentIntent {
  const q = text.toLowerCase();
  const dealId = findDeal(text, deals);
  if (dealId) return { kind: 'next-step', dealId };
  if (/approv|discount|sign[- ]?off/.test(q)) return { kind: 'approvals' };
  if (/missing|unknown|gap|discover|unclear|confirm/.test(q)) return { kind: 'gaps' };
  if (/first|priorit|today|follow|focus|which deal|order|rank/.test(q)) return { kind: 'priorities' };
  return { kind: 'unsupported' };
}

export const initials = (name: string) => name.split(/\s+/).filter(Boolean).map(w => w[0]).slice(0, 2).join('').toUpperCase();
