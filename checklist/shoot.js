// Screenshot every prepared page from disk.
//
// The browser cannot reach the network here, which is why the pages were
// mirrored first. Rendering from file:// needs no network at all, so what comes
// out is the real page with its real stylesheet — just taken locally.
//
// Two sizes in one pass: the full-width shot to work from, and a narrow copy
// small enough to embed in a gallery.
//
// Usage:  node shoot.js <render_dir> <out_dir> [--only=slug]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const WIDTH = 1440;
const THUMB_WIDTH = 520;
const LOCALES = ['pl', 'ua', 'en'];

(async () => {
  const [renderDir, outDir] = process.argv.slice(2);
  const only = (process.argv.find(a => a.startsWith('--only=')) || '').split('=')[1];

  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
  });

  let made = 0, failed = [];
  for (const locale of LOCALES) {
    const dir = path.join(renderDir, locale);
    if (!fs.existsSync(dir)) continue;

    const ctx = await browser.newContext({
      viewport: { width: WIDTH, height: 1000 },
      deviceScaleFactor: 1,
      // Nothing should reach outside; if a stray URL survives, fail fast
      // rather than hang the run waiting for it.
      offline: true,
    });
    const page = await ctx.newPage();
    page.on('pageerror', () => { });

    fs.mkdirSync(path.join(outDir, 'full', locale), { recursive: true });
    fs.mkdirSync(path.join(outDir, 'thumb', locale), { recursive: true });

    for (const file of fs.readdirSync(dir).filter(f => f.endsWith('.html'))) {
      const slug = file.replace(/\.html$/, '');
      if (only && slug !== only) continue;
      const url = 'file://' + path.resolve(dir, file);
      try {
        await page.goto(url, { waitUntil: 'load', timeout: 60000 });
        // Lazy-loaded images only appear once they scroll into view.
        await page.evaluate(async () => {
          await new Promise(res => {
            let y = 0;
            const step = () => {
              y += 900;
              scrollTo(0, y);
              if (y < document.body.scrollHeight) setTimeout(step, 40);
              else { scrollTo(0, 0); setTimeout(res, 250); }
            };
            step();
          });
        });
        await page.waitForTimeout(350);

        await page.screenshot({
          path: path.join(outDir, 'full', locale, slug + '.jpg'),
          fullPage: true, type: 'jpeg', quality: 72,
        });

        await page.setViewportSize({ width: THUMB_WIDTH, height: 900 });
        await page.screenshot({
          path: path.join(outDir, 'thumb', locale, slug + '.jpg'),
          fullPage: true, type: 'jpeg', quality: 55,
        });
        await page.setViewportSize({ width: WIDTH, height: 1000 });

        made += 2;
      } catch (e) {
        failed.push(`${locale}/${slug}: ${e.message.split('\n')[0]}`);
      }
    }
    await ctx.close();
    console.log(`  ${locale}: готово`);
  }

  await browser.close();
  console.log(`\nснимков сделано: ${made}`);
  if (failed.length) {
    console.log(`не снялось (${failed.length}):`);
    failed.forEach(f => console.log('  ', f));
  }
})().catch(e => { console.error('FATAL', e); process.exit(1); });
