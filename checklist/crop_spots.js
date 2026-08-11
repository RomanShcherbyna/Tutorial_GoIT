// Прицельные вырезки для мест, которые обычный искатель по тексту не берёт.
//
// crop.js находит место по цитате видимого текста. Восемь мест так не найти:
// у одних правится пустой контейнер (нулевой размер, текста нет), у других
// страница снята не по тому адресу, у третьих строка вообще не видна на экране —
// она в <head>. Показывать вместо них страницу целиком нельзя: заказчик просил
// место правки, а не доказательство, что страница существует.
//
// Здесь для каждого места сказано прямо: какой файл открыть и что обвести —
// селектор или текст. Для невидимых строк <head> открывается не страница, а её
// исходный код, набранный так, чтобы нужная строка была подсвечена: это и есть
// то место, куда пойдёт программист.
//
// Usage: node crop_spots.js <spots.json> <out_dir>
const { chromium } = require('playwright')
const fs = require('fs')
const path = require('path')

const WIDTH = 1440
const PAD = 30
const MIN_H = 170
const MAX_H = 820

// Строка из <head> на экране не существует. Показываем её так, как её увидит
// исполнитель — в коде страницы, с соседями для ориентировки.
function sourceCard(spot) {
  const raw = fs.readFileSync(spot.file, 'utf8')
  const head = (raw.match(/<head[\s\S]*?<\/head>/i) || [''])[0]
  const lines = head.split('\n').map((l) => l.trim()).filter(Boolean)
  const hit = lines.findIndex((l) => new RegExp(spot.mark, 'i').test(l))
  const from = Math.max(0, hit - 3)
  const shown = lines.slice(from, hit + 4)
  const esc = (s) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]))
  const body = shown.map((l, i) => {
    const on = from + i === hit
    return `<div class="l${on ? ' hit' : ''}">${esc(l.slice(0, 200))}</div>`
  }).join('')
  return `<!doctype html><meta charset="utf-8"><style>
  body{margin:0;background:#0d1015;color:#c8cedb;font:13px/1.7 ui-monospace,Menlo,monospace;padding:18px 20px}
  .t{color:#8fb0e6;font:600 12px/1.6 ui-sans-serif,-apple-system,sans-serif;
     letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px}
  .l{white-space:pre-wrap;padding:2px 8px;border-left:3px solid transparent}
  .hit{background:#2a1113;border-left-color:#d92b2b;color:#ffd9d6}
  </style><div class="t">${esc(spot.caption)}</div>${body}`
}

;(async () => {
  const [spotsPath, outDir] = process.argv.slice(2)
  const spots = JSON.parse(fs.readFileSync(spotsPath, 'utf8'))
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
  })
  const ctx = await browser.newContext({ viewport: { width: WIDTH, height: 1000 }, offline: false })
  const page = await ctx.newPage()
  page.on('pageerror', () => {})
  // Живые снимки тянут шрифты и картинки с сайта, а сети здесь нет: без этого
  // страница висит до таймаута вместо того, чтобы отрисоваться как есть.
  // Глушим только сеть — file:// должен грузиться, это и есть сама страница.
  await page.route(/^https?:\/\//, (r) => r.abort())

  const done = [], missed = []
  for (const spot of spots) {
    try {
      if (spot.kind === 'source') {
        const tmp = path.join(outDir, '_src.html')
        fs.writeFileSync(tmp, sourceCard(spot))
        await page.setViewportSize({ width: 1100, height: 320 })
        await page.goto('file://' + tmp, { waitUntil: 'load' })
        await page.screenshot({ path: path.join(outDir, spot.id + '.jpg'), type: 'jpeg', quality: 78, fullPage: true })
        done.push(spot.id)
        continue
      }

      await page.setViewportSize({ width: WIDTH, height: 1000 })
      await page.goto('file://' + spot.file, { waitUntil: 'load', timeout: 45000 })
      await page.evaluate(async () => {
        await new Promise((r) => {
          let y = 0
          const s = () => {
            y += 1200; scrollTo(0, y)
            if (y < document.body.scrollHeight) setTimeout(s, 25)
            else { scrollTo(0, 0); setTimeout(r, 250) }
          }
          s()
        })
      })

      const box = await page.evaluate((sp) => {
        const norm = (s) => (s || '').replace(/\s+/g, ' ').trim().toLowerCase()
        let el = null
        if (sp.selector) el = document.querySelector(sp.selector)
        if (!el && sp.text) {
          const want = norm(sp.text)
          for (const c of document.body.querySelectorAll('*')) {
            const r = c.getBoundingClientRect()
            if (r.width < 2 || r.height < 2) continue
            if (norm(c.textContent).includes(want)) el = c
          }
        }
        if (!el) return null
        // Пустой контейнер сам по себе невидим — обводим его родителя, иначе
        // на вырезке будет пустое место без единого ориентира.
        let target = el
        const r0 = el.getBoundingClientRect()
        if (r0.height < 8 || r0.width < 8) {
          target = el.parentElement || el
        }
        target.style.outline = '3px solid #d92b2b'
        target.style.outlineOffset = '2px'
        target.scrollIntoView({ block: 'center' })
        const r = target.getBoundingClientRect()
        return { y: r.y + scrollY, h: r.height }
      }, spot)

      if (!box) { missed.push([spot.id, 'место не найдено']); continue }
      const full = await page.evaluate(() => document.body.scrollHeight)
      const height = Math.min(MAX_H, Math.max(MIN_H, box.h + PAD * 2))
      const h = Math.max(40, Math.min(height, full))
      const y = Math.max(0, Math.min(box.y - (height - box.h) / 2, full - h))
      await page.screenshot({
        path: path.join(outDir, spot.id + '.jpg'), type: 'jpeg', quality: 70,
        fullPage: true, clip: { x: 0, y, width: WIDTH, height: h },
      })
      done.push(spot.id)
    } catch (e) {
      missed.push([spot.id, e.message.split('\n')[0].slice(0, 70)])
    }
  }
  await browser.close()
  console.log('вырезок сделано:', done.length, done.join(' '))
  if (missed.length) { console.log('не вышло:'); missed.forEach(([i, r]) => console.log('  ', i, r)) }
})().catch((e) => { console.error('FATAL', e); process.exit(1) })
