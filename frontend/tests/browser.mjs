// Optional real-backend browser check. Requires Playwright + browser from the environment.
// Not used as the evidence for BOY-02's manual Codex In-app Browser verification.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ headless: true });
const base = process.env.BASE_URL || 'http://127.0.0.1:5173';
try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(base);
    for (const [id, name, total] of [['P01','Grup Ritel Mandala','749'], ['P02','Teras Kafe Group','1.305'], ['P03','Klinik Pratama Medika','443'], ['P04','Nirwana Hotel & Resto','147'], ['P05','PT Distribusi Sumber Rejeki','3']]) {
      await page.getByRole('button', { name: `${id} ${name}`, exact: true }).click();
      await page.getByRole('tab', { name: 'Peta relasi', exact: true }).click();
      await page.locator('.graph-counts').waitFor();
      assert.ok((await page.locator('.graph-counts').innerText()).includes(`/ ${total} node`));
      assert.ok(await page.locator('.focus-node').count() <= 12);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    }
    await page.getByRole('button', { name: 'P02 Teras Kafe Group', exact: true }).click();
    await page.getByRole('tab', { name: 'Peta relasi', exact: true }).click();
    for (const id of ['I0296', 'I0348', 'D-2025-02', 'D-2025-06']) {
      await page.getByRole('textbox', { name: 'Cari di seluruh graph', exact: true }).fill(id);
      await page.locator('.graph-results > button').filter({ hasText: id }).click();
      await page.locator('.inspector .source-details').filter({ hasText: id }).waitFor();
      assert.ok(await page.getByRole('button', { name: 'Node DL-002: DL-002, deal', exact: true }).count());
      const edge = page.locator('.graph-edge').last();
      await edge.press('Enter');
      await page.locator('.inspector .edge-meta').waitFor();
      assert.ok((await page.locator('.inspector').innerText()).includes(id));
    }
    await page.getByRole('tab', { name: 'Bukti 1361', exact: true }).click();
    await page.getByRole('textbox', { name: 'Cari seluruh bukti', exact: true }).fill('I0348');
    await page.locator('.evidence-row').click();
    await page.locator('.inspector blockquote').filter({ hasText: 'Mohon keputusan' }).waitFor();
    console.log(`PASS real P01-P05, graph search/provenance, evidence at ${width}px`);
  }
  assert.deepEqual(errors, []);
} finally { await browser.close(); }
