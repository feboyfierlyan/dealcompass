import test from 'node:test';
import assert from 'node:assert/strict';
import { englishText } from '../src/lib/english.ts';
test('unreviewed text and source quotations remain exact, including negation', () => {
  for (const source of ['Jangan janjikan diskon 25%.', 'Customer has NOT consented.', 'I0348', '', 'Negosiasi tambahan']) assert.equal(englishText(source), source);
  assert.equal(englishText('Negosiasi'), 'Negotiation');
});
test('reviewed approval translation retains threshold, missing decision and provenance', () => {
  const source = 'VP Sales (E01): putuskan dan catat di decision_log permintaan diskon 20% (I0348, 2026-09-28); >10% wajib approval. Belum ada keputusan sah yang tercatat untuk DL-002.';
  const translated = englishText(source);
  for (const text of ['E01', '20%', 'I0348', '2026-09-28', 'above 10% require approval', 'No valid decision has been recorded for DL-002']) assert.ok(translated.includes(text));
  assert.ok(source.includes('Belum ada keputusan sah'));
});

test('decision and graph presentation is English without changing approval or source identity', () => {
  assert.equal(englishText('Status pengadaan'), 'Procurement status');
  assert.equal(englishText('Re: Jadwal integrasi akuntansi'), 'Re: Accounting integration schedule');
  assert.equal(englishText('approval VP Sales tertunda'), 'VP Sales approval pending');
  const source = 'INTERPRETASI | [sebagian] Paket Starter (maks 10 outlet) TIDAK dapat langsung menampung 15 outlet deal ini. Meniru D-2025-06 berarti pilot sebagian outlet: usulan skenario, belum disetujui pelanggan maupun VP Sales.';
  const translated = englishText(source);
  for (const text of ['10 outlets', 'CANNOT', '15 outlets', 'D-2025-06', 'not approved by the customer or VP Sales']) assert.ok(translated.includes(text));
});
