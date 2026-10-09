// Pure presentation helpers of the redesign. Synthetic inputs only; no business rule is decided here.
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  compactRupiah, effectiveSelection, employeeFromContext, engineLabel, evidenceTitle, gateSummary, interactionMeta, nextTabIndex,
  obstacleEvidence, orderEvidence, pathArrows, pathSteps, priorityKindLabel, recommendationView, relationPhrase, splitUnknowns,
} from '../src/lib/present.ts';

const deals = ['DL-001', 'DL-002', 'DL-003', 'DL-004', 'DL-005'];
const rec = (deal_id, action = 'A') => ({ schema_version: 'v1', deal_id, action, owner_id: null, milestone: null, evidence_ids: [], precedent_ids: [], precedent_comparison: [], approvals_needed: [], unknowns: [], engine_mode: 'rules' });
const priority = (deal_id, action = 'dari urutan prioritas') => ({ deal_id, account_id: 'P0X', rank: 1, priority_kind: 'acceleration', analysis_status: 'ready', factors: [], rationale: [], limitations: [], evidence_ids: [], evidence: [], evidence_paths: [], recommendation: rec(deal_id, action) });
const ev = (id, file, source_id, excerpt, date = null) => ({ id, source_file: `dataset_kasirnusa/${file}`, source_id, date, excerpt, evidence_type: 'direct' });

test('selection: the first API priority opens once ranking arrives, whatever order the API returns', () => {
  assert.equal(effectiveSelection({ items: deals, ranked: null, userChoice: null }), null);
  assert.equal(effectiveSelection({ items: deals, ranked: ['DL-004', 'DL-001', 'DL-002', 'DL-003', 'DL-005'], userChoice: null }), 'DL-004');
  assert.equal(effectiveSelection({ items: deals, ranked: ['DL-005', 'DL-004', 'DL-003', 'DL-002', 'DL-001'], userChoice: null }), 'DL-005');
  assert.equal(effectiveSelection({ items: deals, ranked: ['DL-999'], userChoice: null }), null);
});

test('selection: a deal the user picked is not replaced when the ranking arrives or reloads', () => {
  assert.equal(effectiveSelection({ items: deals, ranked: null, userChoice: 'DL-002' }), 'DL-002');
  assert.equal(effectiveSelection({ items: deals, ranked: ['DL-004', 'DL-001', 'DL-002'], userChoice: 'DL-002' }), 'DL-002');
  assert.equal(effectiveSelection({ items: deals.filter(id => id !== 'DL-002'), ranked: ['DL-004'], userChoice: 'DL-002' }), 'DL-004');
});

test('recommendation: the ranking version shows without any request; a re-analysis shows only when received for the same deal', () => {
  const idle = recommendationView({ dealId: 'DL-002', priority: priority('DL-002'), session: { status: 'idle', data: null }, preferred: 'priority' });
  assert.equal(idle.source, 'priority'); assert.equal(idle.recommendation.action, 'dari urutan prioritas'); assert.equal(idle.hasSession, false);
  const received = { status: 'received', data: rec('DL-002', 'new analysis') };
  const session = recommendationView({ dealId: 'DL-002', priority: priority('DL-002'), session: received, preferred: 'session' });
  assert.equal(session.source, 'session'); assert.equal(session.recommendation.action, 'new analysis'); assert.equal(session.hasPriority, true);
  const back = recommendationView({ dealId: 'DL-002', priority: priority('DL-002'), session: received, preferred: 'priority' });
  assert.equal(back.source, 'priority'); assert.equal(back.hasSession, true);
});

test('recommendation: running or failed requests and responses for another deal are never shown as the current result', () => {
  for (const status of ['running', 'failed']) {
    const view = recommendationView({ dealId: 'DL-002', priority: priority('DL-002'), session: { status, data: rec('DL-002', 'lama') }, preferred: 'session' });
    assert.equal(view.source, 'priority'); assert.notEqual(view.recommendation.action, 'lama'); assert.equal(view.sessionStatus, status);
    assert.equal(recommendationView({ dealId: 'DL-002', priority: null, session: { status, data: rec('DL-002', 'lama') }, preferred: 'session' }).recommendation, null);
  }
  const foreign = recommendationView({ dealId: 'DL-002', priority: null, session: { status: 'received', data: rec('DL-001') }, preferred: 'session' });
  assert.equal(foreign.recommendation, null); assert.equal(foreign.source, null);
  const wrongPriority = recommendationView({ dealId: 'DL-002', priority: priority('DL-001'), session: { status: 'idle', data: null }, preferred: 'priority' });
  assert.equal(wrongPriority.recommendation, null); assert.equal(wrongPriority.hasPriority, false);
});

test('tabs: arrow keys wrap, Home and End jump, other keys do nothing', () => {
  assert.equal(nextTabIndex('ArrowRight', 0, 3), 1); assert.equal(nextTabIndex('ArrowRight', 2, 3), 0);
  assert.equal(nextTabIndex('ArrowLeft', 0, 3), 2); assert.equal(nextTabIndex('Home', 2, 3), 0); assert.equal(nextTabIndex('End', 0, 3), 2);
  assert.equal(nextTabIndex('Enter', 1, 3), null); assert.equal(nextTabIndex('Tab', 1, 3), null);
});

test('unknowns: items added by the analysis stay next to the action; the full list keeps every item verbatim', () => {
  const r = { ...rec('DL-001'), unknowns: ['Sikap dan kriteria Rina Hapsari belum diketahui.', 'Konteks umum belum lengkap.'] };
  const { specific, all } = splitUnknowns(r, { unknowns: ['Konteks umum belum lengkap.', 'Data lain belum ada.'] });
  assert.deepEqual(specific, ['Sikap dan kriteria Rina Hapsari belum diketahui.']);
  assert.deepEqual(all, ['Sikap dan kriteria Rina Hapsari belum diketahui.', 'Konteks umum belum lengkap.', 'Data lain belum ada.']);
  assert.deepEqual(splitUnknowns(r, null).specific, r.unknowns);
});

test('owner: a name only comes from the employees.csv row with the same employee_id', () => {
  const good = ev('employees.csv:E06', 'employees.csv', 'E06', JSON.stringify({ employee_id: 'E06', nama: 'Bagus Prakoso', jabatan: 'Sales Executive' }));
  assert.deepEqual(employeeFromContext({ evidence: [good] }, 'E06'), { id: 'E06', name: 'Bagus Prakoso', title: 'Sales Executive', evidenceId: 'employees.csv:E06' });
  assert.equal(employeeFromContext({ evidence: [good] }, 'E07'), null);
  assert.equal(employeeFromContext({ evidence: [ev('employees.csv:E06', 'employees.csv', 'E06', JSON.stringify({ employee_id: 'E99', nama: 'Orang Lain' }))] }, 'E06'), null);
  assert.equal(employeeFromContext({ evidence: [ev('crm_contacts.csv:E06', 'crm_contacts.csv', 'E06', JSON.stringify({ employee_id: 'E06', nama: 'Bukan Employee' }))] }, 'E06'), null);
  assert.equal(employeeFromContext({ evidence: [ev('employees.csv:E06', 'employees.csv', 'E06', JSON.stringify({ employee_id: 'E06', nama: ' ' }))] }, 'E06'), null);
  assert.equal(employeeFromContext({ evidence: [ev('employees.csv:E06', 'employees.csv', 'E06', 'bukan JSON')] }, 'E06'), null);
  assert.equal(employeeFromContext(null, 'E06'), null); assert.equal(employeeFromContext({ evidence: [good] }, null), null);
});

test('evidence titles reuse record fields; empty values stay empty, not zero; unknown files fall back to the ID', () => {
  const message = 'Pak Andi, untuk menutup Teras Kafe saya usul diskon 20% agar menyamai KasirPro. Mohon keputusan.';
  const email = ev('interactions.jsonl:I0348', 'interactions.jsonl', 'I0348', JSON.stringify({ tipe: 'email_internal', subjek: 'Permintaan diskon 20% Teras Kafe', dari: 'citra@kasirnusa.id', ke: 'andi@kasirnusa.id', isi: message }), '2026-09-28');
  assert.deepEqual(evidenceTitle(email), { kind: 'Internal email', title: 'Permintaan diskon 20% Teras Kafe' });
  assert.deepEqual(interactionMeta(email), { from: 'citra@kasirnusa.id', to: 'andi@kasirnusa.id', message });
  const usage = value => ev('u', 'feature_usage_monthly.csv', 'F1|2026-09', JSON.stringify({ feature_id: 'F1', bulan: '2026-09', account_id: 'P01', pengguna_aktif: value }));
  assert.match(evidenceTitle(usage('')).title, /active users not recorded$/);
  assert.match(evidenceTitle(usage(null)).title, /active users not recorded$/);
  assert.match(evidenceTitle(usage(0)).title, / 0 active users$/);
  assert.deepEqual(evidenceTitle(ev('x', 'lain.csv', 'X1', 'bukan JSON')), { kind: 'lain.csv', title: 'X1' });
  assert.equal(interactionMeta(usage('3')), null);
});

test('relations: plain phrases for known codes; candidate precedents stay "mungkin relevan"; unknown codes are not invented', () => {
  assert.equal(relationPhrase('interaction_for'), 'interaction with account');
  assert.equal(relationPhrase('overlapping_employment'), 'overlapping employment with');
  assert.equal(relationPhrase('candidate_precedent_discount_request'), 'potentially relevant past decision');
  assert.equal(relationPhrase('relasi_baru_backend'), 'relasi baru backend');
});

test('evidence path: reading against an edge keeps its original arrow and endpoints', () => {
  const edge = (id, source, target, relation) => ({ id, source, target, relation, evidence_type: 'direct', evidence_ids: [], valid_from: null, valid_to: null });
  const context = { deal: { deal_id: 'DL-002', account_name: 'Teras Kafe Group' }, graph: {
    nodes: [{ id: 'DL-002', label: 'DL-002', type: 'deal' }, { id: 'P02', label: 'Teras Kafe Group', type: 'account' }, { id: 'I0348', label: 'Permintaan diskon 20% Teras Kafe', type: 'interaction' }],
    edges: [edge('e1', 'DL-002', 'P02', 'deal_for'), edge('e2', 'I0348', 'P02', 'interaction_for')] } };
  const path = { node_ids: ['DL-002', 'P02', 'I0348'], edge_ids: ['e1', 'e2'], evidence_ids: [] };
  assert.equal(pathArrows(path, context), 'DL-002 → P02 ← I0348');
  assert.deepEqual(pathSteps(path, context).map(s => [s.name, s.type, s.forward]), [['Deal Teras Kafe Group', 'Deal', null], ['Teras Kafe Group', 'Account', true], ['Permintaan diskon 20% Teras Kafe', 'Interaction', false]]);
  assert.deepEqual([context.graph.edges[1].source, context.graph.edges[1].target], ['I0348', 'P02']);
});

test('why block: obstacle records come from the ranking factor, interactions only; the gate is verbatim and null stays null', () => {
  const context = { evidence: [ev('interactions.jsonl:I2', 'interactions.jsonl', 'I2', '{}', '2026-09-28'), ev('interactions.jsonl:I1', 'interactions.jsonl', 'I1', '{}', '2026-08-17'), ev('crm_deals.csv:DL-002', 'crm_deals.csv', 'DL-002', '{}')] };
  const item = { factors: [
    { name: 'hambatan_dinyatakan_pelanggan', value: 2, effect: '', evidence_ids: ['interactions.jsonl:I2', 'crm_deals.csv:DL-002', 'interactions.jsonl:I1', 'tidak-ada'] },
    { name: 'gate_approval_izin', value: 'approval VP Sales tertunda', effect: '', evidence_ids: [] }] };
  assert.deepEqual(obstacleEvidence(item, context).map(e => e.id), ['interactions.jsonl:I1', 'interactions.jsonl:I2']);
  assert.equal(gateSummary(item), 'approval VP Sales tertunda');
  assert.equal(gateSummary({ factors: [{ name: 'gate_approval_izin', value: null, effect: '', evidence_ids: [] }] }), null);
  assert.equal(gateSummary(null), null); assert.deepEqual(obstacleEvidence(null, context), []); assert.deepEqual(obstacleEvidence(item, null), []);
});

test('cited records: conversations first, then decisions, newest first, nothing dropped; labels use plain words', () => {
  const records = [ev('a', 'crm_deals.csv', 'DL', '{}', '2026-09-30'), ev('b', 'decision_log.csv', 'D1', '{}', '2025-01-01'), ev('c', 'interactions.jsonl', 'I1', '{}', '2026-08-01'), ev('d', 'interactions.jsonl', 'I2', '{}', '2026-09-01')];
  assert.deepEqual(orderEvidence(records).map(e => e.id), ['d', 'c', 'b', 'a']);
  assert.equal(records[0].id, 'a');
  assert.equal(compactRupiah(147000000), 'Rp147M'); assert.equal(compactRupiah(37800000), 'Rp37.8M'); assert.equal(compactRupiah(1200000000), 'Rp1.2B');
  assert.equal(priorityKindLabel.acceleration, 'Follow up'); assert.equal(priorityKindLabel.discovery, 'Needs discovery');
  assert.equal(engineLabel.rules, 'Rules-based analysis'); assert.equal(engineLabel.jev, 'Jev analysis'); assert.equal(engineLabel.replay, 'Recorded analysis (replay)');
});
