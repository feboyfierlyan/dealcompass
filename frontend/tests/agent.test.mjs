// Agent routing is presentation only: it picks which API answer to show and never invents one.
import test from 'node:test';
import assert from 'node:assert/strict';
import { findDeal, routeQuestion } from '../src/lib/agent.ts';

const deals = [
  { deal_id: 'DL-001', account_id: 'P01', account_name: 'Grup Ritel Mandala' },
  { deal_id: 'DL-002', account_id: 'P02', account_name: 'Teras Kafe Group' },
  { deal_id: 'DL-003', account_id: 'P03', account_name: 'Klinik Pratama Medika' },
  { deal_id: 'DL-004', account_id: 'P04', account_name: 'Nirwana Hotel & Resto' },
  { deal_id: 'DL-005', account_id: 'P05', account_name: 'PT Distribusi Sumber Rejeki' },
];

test('a named customer, account ID or deal ID asks for that deal only', () => {
  assert.deepEqual(routeQuestion('What is the next step for Teras Kafe?', deals), { kind: 'next-step', dealId: 'DL-002' });
  assert.deepEqual(routeQuestion('next step p04', deals), { kind: 'next-step', dealId: 'DL-004' });
  assert.deepEqual(routeQuestion('status of DL-005 please', deals), { kind: 'next-step', dealId: 'DL-005' });
  assert.equal(findDeal('anything about the hotel group', deals), null, 'generic words never pick a deal');
});

test('pipeline questions map to ranking, approvals or gaps; anything else is declined, not guessed', () => {
  assert.deepEqual(routeQuestion('Which deal should I follow up first?', deals), { kind: 'priorities' });
  assert.deepEqual(routeQuestion('Which deals need an approval before we act?', deals), { kind: 'approvals' });
  assert.deepEqual(routeQuestion('Where are we missing information?', deals), { kind: 'gaps' });
  assert.deepEqual(routeQuestion('Write me a poem', deals), { kind: 'unsupported' });
});
