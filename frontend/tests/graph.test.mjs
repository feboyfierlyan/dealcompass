import test from 'node:test';
import assert from 'node:assert/strict';
import { indexGraph, scopeNodes, visibleGraph, pathToDeal, expandNodes, searchNodes, layoutGraph, evidenceExcerpt, INITIAL_NODE_LIMIT, MAX_VISIBLE_NODES } from '../src/lib/graphView.ts';
import { isContext, resolveEvidence } from '../src/lib/contracts.ts';

// Integration tests: fetch the running Bima backend, never substitute a fixture.
const base = process.env.GRAPH_API_URL ?? 'http://127.0.0.1:8000';
const contexts = [];
for (let i = 1; i <= 5; i++) {
  const response = await fetch(`${base}/api/deals/DL-00${i}`);
  assert.equal(response.status, 200, 'Start the real backend before running graph tests');
  const context = await response.json();
  assert.ok(isContext(context));
  contexts.push(context);
}

for (const context of contexts) test(`${context.deal.account_id}: bounded focus, reachable nodes, preserved evidence and readable layout`, () => {
  const index = indexGraph(context);
  assert.equal(index.invalidEdges.length, 0);
  const ids = scopeNodes(context, index, 'focus').slice(0, INITIAL_NODE_LIMIT);
  assert.ok(ids.includes(context.deal.account_id));
  assert.ok(ids.includes(context.deal.deal_id));
  assert.ok(ids.length <= 12);
  const graph = visibleGraph(index, ids);
  for (const edge of graph.edges) {
    assert.ok(ids.includes(edge.source) && ids.includes(edge.target));
    assert.deepEqual(resolveEvidence(edge.evidence_ids, context.evidence).missing, []);
  }
  for (const node of context.graph.nodes) {
    assert.ok(searchNodes(index, node.id).some(n => n.id === node.id));
    const path = pathToDeal(index, node.id);
    assert.equal(path.at(-1), node.id);
    for (let i = 1; i < path.length; i++) assert.ok(index.adjacent.get(path[i - 1]).some(e => e.source === path[i] || e.target === path[i]));
  }
  for (const width of [320, 760]) {
    const layout = layoutGraph(graph.nodes, width);
    assert.ok(layout.cardWidth >= 200);
    assert.equal(layout.positions.size, ids.length);
    for (const { x, y } of layout.positions.values()) {
      assert.ok(x - layout.cardWidth / 2 >= 0 && x + layout.cardWidth / 2 <= layout.width);
      assert.ok(y - 40 >= 0 && y + 48 <= layout.height);
    }
  }
});

test('P02 real large payload exposes both interactions and both precedents with original evidence IDs', () => {
  const c = contexts[1], index = indexGraph(c);
  assert.equal(c.graph.nodes.length, 1305);
  assert.equal(c.graph.edges.length, 2895);
  assert.equal(c.evidence.length, 1361);
  const focus = scopeNodes(c, index, 'focus').slice(0, 12);
  const precedents = scopeNodes(c, index, 'precedents').slice(0, 12);
  for (const id of ['I0296', 'I0348']) assert.ok(focus.includes(id));
  for (const id of ['D-2025-02', 'D-2025-06']) assert.ok(precedents.includes(id));
  for (const id of ['P02', 'I0296', 'I0348', 'D-2025-02', 'D-2025-06']) {
    const path = pathToDeal(index, id);
    assert.equal(path[0], 'DL-002');
    const edges = visibleGraph(index, path).edges;
    assert.ok(edges.length);
    const sourceId = id === 'P02' ? 'DL-002' : id;
    assert.ok(edges.some(e => resolveEvidence(e.evidence_ids, c.evidence).records.some(record => record.source_id === sourceId)), `Original source for ${id}`);
  }
});

test('expansion caps rendering at 24 and source filters do not fabricate or merge distinct edges', () => {
  const c = contexts[1], index = indexGraph(c);
  let ids = scopeNodes(c, index, 'focus').slice(0, 12);
  for (let i = 0; i < 10; i++) ids = expandNodes(index, ids, 'DL-002').ids;
  assert.equal(ids.length, MAX_VISIBLE_NODES);
  const all = visibleGraph(index, ids);
  const direct = visibleGraph(index, ids, 'direct'), inferred = visibleGraph(index, ids, 'inferred');
  assert.equal(direct.edges.length + inferred.edges.length, all.edges.length);
  assert.ok(direct.edges.every(e => e.evidence_type === 'direct'));
  assert.ok(inferred.edges.every(e => e.evidence_type === 'inferred'));
  assert.equal(new Set(all.edges.map(e => e.id)).size, all.edges.length);
  assert.ok(all.edges.filter(e => e.target === 'D-2025-02').length > 1);
});

test('missing endpoints and isolated nodes stay explicit; source isi is shown without losing raw JSON', () => {
  const c = structuredClone(contexts[4]);
  c.graph.nodes.push({ id: 'ISOLATED', label: 'Isolated', type: 'account' });
  c.graph.edges.push({ ...c.graph.edges[0], id: 'INVALID', target: 'MISSING' });
  const index = indexGraph(c);
  assert.deepEqual(pathToDeal(index, 'ISOLATED'), ['ISOLATED']);
  assert.deepEqual(pathToDeal(index, 'MISSING'), []);
  assert.equal(index.invalidEdges.length, 1);
  const source = contexts[1].evidence.find(e => e.source_id === 'I0296');
  assert.equal(evidenceExcerpt(source.excerpt).text, JSON.parse(source.excerpt).isi);
  assert.equal(evidenceExcerpt(source.excerpt).structured, true);
  assert.equal(evidenceExcerpt('plain source').structured, false);
  assert.ok(evidenceExcerpt('{"total":12}').text.includes('"total": 12'));
});
