import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { isDealList, isContext, isRecommendation, resolveEvidence } from '../src/lib/contracts.ts';

const source = readFileSync(new URL('../src/dev/fixture.ts', import.meta.url), 'utf8');
function fixture(name) {
  const match = source.match(new RegExp(`export const ${name} = ([\\s\\S]*?) satisfies \\w+;`));
  assert.ok(match, `fixture ${name} exists`);
  return JSON.parse(match[1]);
}
test('API v1 accepts unranked five-deal data without converting null to zero', () => {
  const list = fixture('fixtureList');
  assert.equal(isDealList(list), true);
  assert.deepEqual(list.items.map(d => d.account_id), ['P01', 'P02', 'P03', 'P04', 'P05']);
  assert.ok(list.items.every(d => d.rank === null));
  list.items[0].rank = 0;
  assert.equal(isDealList(list), false);
});
test('duplicate IDs and incompatible schemas cannot silently replace deal data', () => {
  const list = fixture('fixtureList');
  list.items.push(list.items[0]);
  assert.equal(isDealList(list), false);
  assert.equal(isDealList({ ...fixture('fixtureList'), schema_version: 'v2' }), false);
});
test('missing context arrays and incomplete temporal edges are rejected', () => {
  const context = fixture('fixtureContext');
  assert.equal(isContext(context), true);
  assert.equal(isContext({ ...context, evidence: undefined }), false);
  delete context.graph.edges[0].valid_from;
  assert.equal(isContext(context), false);
});
test('recommendation modes and approvals follow the shared contract', () => {
  const recommendation = fixture('fixtureRecommendation');
  assert.equal(isRecommendation(recommendation), true);
  assert.equal(isRecommendation({ ...recommendation, engine_mode: 'pretend-live' }), false);
  assert.equal(isRecommendation({ ...recommendation, approvals_needed: 'Approved' }), false);
});
test('missing evidence stays visible and duplicate references do not duplicate records', () => {
  const context = fixture('fixtureContext');
  const resolved = resolveEvidence(['I0296', 'MISSING', 'I0296', 'MISSING'], context.evidence);
  assert.deepEqual(resolved.records.map(e => e.id), ['I0296']);
  assert.deepEqual(resolved.missing, ['MISSING']);
});
