// Usage: NODE_PATH=<directory containing playwright> node scripts/capture_evidence.cjs
// Captures the real browser rendering of the labelled, verbatim command-log pages.
const { chromium } = require('playwright');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const fs = require('node:fs');
(async () => {
  const root = path.resolve(__dirname, '..');
  const executablePath = process.env.EVIDENCE_BROWSER ||
    'C:/Program Files/Google/Chrome/Application/chrome.exe';
  const browser = await chromium.launch({executablePath, headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 1800, height: 1000}, deviceScaleFactor: 1});
    for (const name of ['01-hardware-probe', '02-bench', '03-serve-and-smoke', '04-locust-10', '05-locust-50']) {
      const input = path.join(root, 'submission/evidence', name + '.html');
      if (!fs.existsSync(input)) throw new Error('Missing actual log viewer: ' + input);
      await page.goto(pathToFileURL(input).href);
      const output = path.join(root, 'submission/screenshots', name + '.png');
      await page.locator('body').screenshot({path: output});
      console.log(output);
    }
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
