// Crop each fix down to the place it is about.
//
// A full-page screenshot proves the page exists; it does not show the mistake.
// So for every fix that quotes what stands on the page, we find that text in
// the rendered page, outline it, and cut out just that band — the error with
// enough around it to recognise where you are.
//
// Fixes whose quote is not visible text (engine strings, markup attributes)
// cannot be located this way. They are reported, not faked.
//
// Usage:  node crop.js <render_dir> <jobs.json> <out_dir>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const WIDTH = 1440;
const PAD = 28;          // breathing room around the element
const MIN_H = 150;       // a one-line label alone reads as a mystery
const MAX_H = 900;

(async () => {
  const [renderDir, jobsPath, outDir] = process.argv.slice(2);
  const jobs = JSON.parse(fs.readFileSync(jobsPath, 'utf8'));

  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
  });
  const ctx = await browser.newContext({
    viewport: { width: WIDTH, height: 1000 }, offline: true,
  });
  const page = await ctx.newPage();
  page.on('pageerror', () => { });

  let ok = 0;
  const missed = [];
  let loaded = '';

  for (const job of jobs) {
    const file = path.resolve(renderDir, job.locale, job.slug + '.html');
    if (!fs.existsSync(file)) { missed.push([job.id, 'нет страницы']); continue; }

    try {
      if (loaded !== file) {
        await page.goto('file://' + file, { waitUntil: 'load', timeout: 45000 });
        await page.evaluate(async () => {
          await new Promise(r => {
            let y = 0;
            const s = () => {
              y += 1200; scrollTo(0, y);
              if (y < document.body.scrollHeight) setTimeout(s, 25);
              else { scrollTo(0, 0); setTimeout(r, 200); }
            };
            s();
          });
        });
        loaded = file;
      }

      const box = await page.evaluate((needle) => {
        const prev = document.querySelector('[data-lpb-mark]');
        if (prev) { prev.style.outline = ''; prev.removeAttribute('data-lpb-mark'); }

        const norm = s => s.replace(/\s+/g, ' ').trim().toLowerCase();
        const full = norm(needle).replace(/[…\u2026]+$/, '');
        if (!full) return null;

        // Try the whole quote, then progressively shorter heads of it: page text
        // gets truncated, reworded or split, and a shorter anchor still lands in
        // the right place.
        const tries = [full, full.slice(0, 40), full.slice(0, 24)]
          .filter((v, i, a) => v.length >= 6 && a.indexOf(v) === i);
        const ATTRS = ['placeholder', 'title', 'alt', 'value', 'aria-label'];

        let best = null;
        const all = document.body.querySelectorAll('*');
        for (const want of tries) {
          for (const el of all) {
            const r = el.getBoundingClientRect();
            if (r.width < 2 || r.height < 2) continue;
            const t = norm(el.textContent || '');
            if (t && t.includes(want)) { best = el; continue; }
            for (const a of ATTRS) {
              const v = el.getAttribute && el.getAttribute(a);
              if (v && norm(v).includes(want)) { best = el; break; }
            }
          }
          if (best) break;
        }
        if (!best) return null;

        best.setAttribute('data-lpb-mark', '1');
        best.style.outline = '3px solid #d92b2b';
        best.style.outlineOffset = '2px';
        best.scrollIntoView({ block: 'center' });
        const r = best.getBoundingClientRect();
        return { x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height };
      }, job.needle);

      if (!box || box.w < 4 || box.h < 4) { missed.push([job.id, 'текст не найден']); continue; }

      const height = Math.min(MAX_H, Math.max(MIN_H, box.h + PAD * 2));
      const y = Math.max(0, box.y - (height - box.h) / 2);
      const full = await page.evaluate(() => document.body.scrollHeight);

      // clip lives in full-page coordinates, so fullPage must be on
      const h = Math.max(40, Math.min(height, full));
      await page.screenshot({
        path: path.join(outDir, job.id + '.jpg'),
        type: 'jpeg', quality: 68, fullPage: true,
        clip: { x: 0, y: Math.max(0, Math.min(y, full - h)), width: WIDTH, height: h },
      });
      ok++;
    } catch (e) {
      missed.push([job.id, e.message.split('\n')[0].slice(0, 60)]);
    }
  }

  await browser.close();
  fs.writeFileSync(path.join(outDir, '_missed.json'), JSON.stringify(missed, null, 1));
  console.log(`вырезок сделано: ${ok} из ${jobs.length}`);
  console.log(`не нашлось на странице: ${missed.length}`);
  const why = {};
  missed.forEach(([, r]) => { why[r] = (why[r] || 0) + 1; });
  Object.entries(why).forEach(([r, n]) => console.log(`   ${r}: ${n}`));
})().catch(e => { console.error('FATAL', e); process.exit(1); });
