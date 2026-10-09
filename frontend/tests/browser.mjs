// Run against local Vite + backend. Requires Playwright supplied by the test environment.
// No browser/testing dependency is added to the shared package manifest.
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.BASE_URL || 'http://127.0.0.1:5173';
const output = process.env.UI_OUTPUT_DIR || '/tmp/dealcompass-boy-ui';
mkdirSync(output, { recursive: true });
const source = readFileSync(new URL('../src/dev/fixture.ts', import.meta.url), 'utf8');
const fixture = name => JSON.parse(source.match(new RegExp(`export const ${name} = ([\\s\\S]*?) satisfies \\w+;`))[1]);
const context = fixture('fixtureContext');
const recommendation = fixture('fixtureRecommendation');
const list = fixture('fixtureList');
const browser = await chromium.launch({ headless: true });
let completed = 0;
async function run(name, fn) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1080 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try { await fn(page); assert.deepEqual(errors, [], 'no unhandled browser errors'); completed++; console.log(`PASS ${name}`); }
  finally { await page.close(); }
}
const json = (route, body, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
const selected = page => page.locator('.workspace');
const p02 = page => page.getByRole('button', { name: 'P02 Teras Kafe Group', exact: true });
const waitForText = (locator, text) => locator.getByText(text, { exact: true }).waitFor();
try {
  await run('API nyata: lima deal, pemilihan, rank null, 501, pencarian', async page => {
    await page.goto(base);
    await p02(page).waitFor();
    assert.equal(await page.locator('.deal-card').count(), 5);
    assert.equal(await page.locator('.rank-label').filter({ hasText: 'Prioritas belum tersedia' }).count(), 5);
    for (const deal of list.items) {
      await page.getByRole('button', { name: `${deal.account_id} ${deal.account_name}`, exact: true }).click();
      await waitForText(selected(page), 'Konteks deal belum tersedia');
      assert.equal(await selected(page).getByRole('heading', { name: deal.account_name, exact: true }).count(), 1);
      assert.equal(await page.getByRole('button', { name: 'Analisis langkah berikutnya', exact: true }).isDisabled(), true);
    }
    await p02(page).click();
    await waitForText(selected(page), 'Konteks deal belum tersedia');
    await page.screenshot({ path: `${output}/live-desktop.png`, fullPage: true });
    await page.getByRole('textbox', { name: 'Cari deal' }).fill('tidak ada');
    await page.getByRole('button', { name: 'Tampilkan semua' }).waitFor();
    assert.equal(await page.locator('.deal-card').count(), 0);
    await page.getByRole('button', { name: 'Tampilkan semua' }).click();
    assert.equal(await page.locator('.deal-card').count(), 5);
  });
  await run('fixture berlabel: analisis, preseden, graph, sumber dan keyboard', async page => {
    await page.goto(base);
    await page.getByRole('button', { name: 'Pratinjau fixture pengembangan', exact: true }).click();
    await page.locator('.fixture-banner').waitFor();
    await p02(page).click();
    await page.getByRole('button', { name: 'Analisis langkah berikutnya', exact: true }).click();
    await page.getByRole('heading', { name: recommendation.action, exact: true }).waitFor();
    assert.match(await page.locator('.action-panel').innerText(), /Replay · fixture/);
    await page.locator('.precedent').filter({ hasText: 'D-2025-06' }).locator('summary').click();
    assert.match(await page.locator('.precedent-body:visible').innerText(), /Pendekatan alternatif/);
    await page.screenshot({ path: `${output}/fixture-analysis.png`, fullPage: true });
    await page.getByRole('tab', { name: 'Peta relasi', exact: true }).click();
    await page.getByRole('button', { name: 'Node Demo & hambatan harga, interaction', exact: true }).click();
    await page.locator('.inspector blockquote').filter({ hasText: 'menilai harga terlalu tinggi' }).waitFor();
    await page.getByRole('button', { name: /Relasi Fixture: kandidat pendekatan pilot/ }).focus();
    await page.keyboard.press('Enter');
    await waitForText(page.locator('.inspector'), 'Inferensi');
    assert.match(await page.locator('.inspector').innerText(), /D-2025-06/);
    await page.getByRole('button', { name: 'Perbesar graph' }).click();
    await waitForText(page.locator('.zoom-controls'), '120%');
    await page.getByRole('button', { name: 'Reset tampilan graph' }).click();
    await page.screenshot({ path: `${output}/fixture-graph.png`, fullPage: true });
    await page.getByRole('tab', { name: 'Peta relasi', exact: true }).focus();
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.getByRole('tab', { name: /^Bukti/ }).getAttribute('aria-selected'), 'true');
    await page.locator('.evidence-row').filter({ hasText: 'I0348' }).click();
    assert.match(await page.locator('.inspector blockquote').innerText(), /Mohon keputusan/);
    await page.locator('.fixture-banner').getByRole('button', { name: 'Kembali ke API nyata' }).click();
    await waitForText(selected(page), 'Konteks deal belum tersedia');
    assert.equal(await page.locator('.fixture-banner').count(), 0);
  });
  await run('404 detail terlihat dan pilihan deal tetap tersedia', async page => {
    await page.route('**/api/deals/DL-001', route => json(route, { detail: { code: 'DEAL_NOT_FOUND' } }, 404));
    await page.goto(base); await waitForText(selected(page), 'Deal tidak ditemukan');
    await p02(page).click(); await waitForText(selected(page), 'Konteks deal belum tersedia');
  });
  await run('daftar kosong tidak menghasilkan deal atau nilai rekaan', async page => {
    await page.route('**/api/deals', route => json(route, { ...list, items: [] }));
    await page.goto(base); await page.getByRole('heading', { name: 'Belum ada deal dalam daftar' }).waitFor();
    assert.equal(await page.locator('.workspace').count(), 0);
  });
  await run('respons rusak dan retry daftar', async page => {
    let calls = 0;
    await page.route('**/api/deals', route => json(route, ++calls === 1 ? { items: null } : list));
    await page.goto(base); await page.getByText('Respons layanan belum sesuai kontrak data v1.', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Coba lagi', exact: true }).click();
    await p02(page).waitFor();
  });
  await run('gangguan jaringan ditangani', async page => {
    await page.route('**/api/deals', route => route.abort());
    await page.goto(base); await page.getByText('Koneksi ke layanan terputus. Periksa koneksi lalu coba lagi.', { exact: true }).waitFor();
  });
  await run('respons lambat tidak menimpa deal yang baru dipilih', async page => {
    await page.route(/\/api\/deals\/DL-00[12]$/, async route => {
      const id = route.request().url().split('/').pop();
      if (id === 'DL-001') await new Promise(resolve => setTimeout(resolve, 800));
      try { await json(route, { ...context, deal: list.items.find(d => d.deal_id === id) }); } catch { /* request cancelled by selection */ }
    });
    await page.goto(base); await p02(page).click();
    await page.getByRole('button', { name: 'Analisis langkah berikutnya', exact: true }).waitFor();
    await page.waitForTimeout(1000);
    assert.equal(await selected(page).getByRole('heading', { name: 'Teras Kafe Group', exact: true }).count(), 1);
    assert.match(await selected(page).innerText(), /DL-002/);
  });
  await run('analisis gagal dapat dicoba ulang; ID bukti hilang tetap terlihat', async page => {
    await page.route('**/api/deals/DL-002', route => json(route, context));
    let calls = 0;
    await page.route('**/api/deals/DL-002/analyze', route => ++calls === 1 ? json(route, {}, 503) : json(route, { ...recommendation, evidence_ids: ['MISSING'], precedent_ids: ['UNKNOWN'] }));
    await page.goto(base); await p02(page).click();
    await page.getByRole('button', { name: 'Analisis langkah berikutnya', exact: true }).click();
    await waitForText(page.locator('.action-panel'), 'Analisis belum dapat dimuat');
    await page.locator('.action-panel').getByRole('button', { name: 'Coba lagi' }).click();
    await page.getByRole('button', { name: 'MISSING', exact: true }).click();
    assert.match(await page.locator('.inspector').innerText(), /Sumber belum dapat diverifikasi untuk ID: MISSING/);
    assert.match(await page.locator('.precedent-panel').innerText(), /Preseden belum ditemukan dalam konteks: UNKNOWN/);
  });
  await run('payload deal yang salah ditolak', async page => {
    await page.route('**/api/deals/DL-001', route => json(route, context));
    await page.goto(base); await page.getByText('Detail yang diterima tidak sesuai deal yang dipilih.', { exact: true }).waitFor();
  });
  await run('mobile tanpa overflow horizontal; graph dan bukti dapat diakses', async page => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base); await p02(page).click();
    await waitForText(selected(page), 'Konteks deal belum tersedia');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: `${output}/live-mobile.png`, fullPage: true });
    await page.getByRole('button', { name: 'Pratinjau fixture pengembangan', exact: true }).click();
    await p02(page).click();
    await page.getByRole('tab', { name: 'Peta relasi', exact: true }).click();
    await page.getByRole('button', { name: 'Node Demo & hambatan harga, interaction', exact: true }).click();
    await page.locator('.inspector blockquote').filter({ hasText: 'menilai harga terlalu tinggi' }).waitFor();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: `${output}/fixture-mobile.png`, fullPage: true });
  });
  console.log(`${completed} browser scenarios passed. Screenshots: ${output}`);
} finally { await browser.close(); }
