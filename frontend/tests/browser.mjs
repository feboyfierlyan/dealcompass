// Optional real-backend browser check. Requires Playwright + browser from the environment.
// Not run for the UI/UX redesign handoff (Playwright is not installed); see docs/handoffs/BOY.md.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ headless: true });
const base = process.env.BASE_URL || 'http://127.0.0.1:5173';
try {
  const page = await browser.newPage();
  const errors = [], posts = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (request.method() === 'POST') posts.push(request.url()); });
  for (const [width, height] of [[1440, 900], [390, 844]]) {
    const narrow = width < 900;
    await page.setViewportSize({ width, height });
    await page.goto(base);
    // The first API priority opens by default on desktop; the list is the first view on phones.
    await page.locator('.queue-item.current').waitFor();
    const open = async id => {
      if (narrow && await page.getByRole('button', { name: 'Semua deal' }).count()) await page.getByRole('button', { name: 'Semua deal' }).click();
      await page.locator(`[data-deal="${id}"]`).click();
      await page.locator('.detail-head h2').waitFor();
    };
    const closeDrawer = async () => { if (await page.getByRole('button', { name: 'Tutup panel bukti' }).count()) await page.getByRole('button', { name: 'Tutup panel bukti' }).click(); };
    for (const [id, name, total] of [['DL-001','Grup Ritel Mandala','749'], ['DL-002','Teras Kafe Group','1.305'], ['DL-003','Klinik Pratama Medika','443'], ['DL-004','Nirwana Hotel & Resto','147'], ['DL-005','PT Distribusi Sumber Rejeki','3']]) {
      await open(id);
      assert.equal(await page.locator('.detail-head h2').innerText(), name);
      await page.getByRole('heading', { name: 'Tindakan yang disarankan' }).waitFor();
      await page.getByRole('tab', { name: 'Jelajahi data', exact: true }).click();
      await page.locator('.graph-counts').waitFor();
      assert.ok((await page.locator('.graph-counts').innerText()).includes(`/ ${total} titik`));
      assert.ok(await page.locator('.focus-node').count() <= 12);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    }
    await open('DL-002');
    await page.getByRole('tab', { name: 'Jelajahi data', exact: true }).click();
    for (const id of ['I0296', 'I0348', 'D-2025-02', 'D-2025-06']) {
      await page.getByRole('textbox', { name: 'Cari di seluruh peta', exact: true }).fill(id);
      await page.locator('.graph-results > button').filter({ hasText: id }).click();
      await page.locator('.drawer .raw-source summary').filter({ hasText: id }).first().waitFor();
      await closeDrawer();
      assert.ok(await page.getByRole('button', { name: 'Titik Deal Teras Kafe Group, Deal, ID DL-002', exact: true }).count());
      await page.locator('.graph-edge').last().press('Enter');
      await page.locator('.drawer .edge-meta').waitFor();
      assert.ok((await page.locator('.drawer').innerText()).includes(id));
      await closeDrawer();
    }
    await page.getByRole('button', { name: /^Semua bukti/ }).click();
    await page.getByRole('textbox', { name: 'Cari seluruh bukti', exact: true }).fill('I0348');
    await page.locator('.evidence-row').click();
    await page.locator('.drawer blockquote').filter({ hasText: 'Mohon keputusan' }).waitFor();
    await page.keyboard.press('Escape');
    console.log(`PASS real P01-P05, graph search/provenance, evidence drawer at ${width}px`);
  }
  assert.deepEqual(posts, [], 'No analysis POST without an explicit click');
  assert.deepEqual(errors, []);
} finally { await browser.close(); }
