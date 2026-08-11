// Общий разбор правок: страница та же, но ответы и комментарии живут на сервере,
// а не в браузере того, кто их написал. Иначе разбирать втроём нельзя — каждый
// видит только себя.
//
// Зависимостей нет намеренно. Документ отдаётся один, ходят по нему несколько
// человек, нагрузка — десятки запросов в минуту; ради этого тянуть фреймворк и
// сборку значит добавить то, что придётся чинить.
//
// Данные лежат в одном JSON-файле. На Railway файловая система пропадает при
// каждом деплое, поэтому DATA_DIR нужно повесить на том — иначе разбор
// потеряется вместе с обновлением. Об этом сказано в README.
import { createServer } from 'node:http'
import { readFile, writeFile, rename, mkdir } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { randomUUID } from 'node:crypto'

const HERE = dirname(fileURLToPath(import.meta.url))
const PORT = Number(process.env.PORT) || 3000
const DATA_DIR = process.env.DATA_DIR || join(HERE, 'data')
const DB_FILE = join(DATA_DIR, 'state.json')
const PAGE = process.env.PAGE_FILE || join(HERE, 'public', 'index.html')
// Пароль общий на всех: это не разграничение прав, а забор от случайного
// прохожего. Пусто — значит открыто по ссылке.
const PASS = process.env.ACCESS_PASSWORD || ''

const MAX_BODY = 64 * 1024
const MAX_TEXT = 4000
const MAX_NAME = 60

let db = { verdicts: {}, threads: {}, rev: 0 }
let writing = null
let dirty = false

async function load() {
  await mkdir(DATA_DIR, { recursive: true })
  if (existsSync(DB_FILE)) {
    try {
      db = JSON.parse(await readFile(DB_FILE, 'utf8'))
      db.verdicts ||= {}
      db.threads ||= {}
      db.rev ||= 0
    } catch (e) {
      // Битый файл не должен ронять сервис и, главное, не должен быть затёрт
      // пустым состоянием: отложим его в сторону и начнём с чистого.
      const bak = DB_FILE + '.broken-' + Date.now()
      await rename(DB_FILE, bak).catch(() => {})
      console.error('состояние не прочиталось, отложено в', bak, e.message)
    }
  }
}

// Запись через временный файл: половина JSON на диске хуже, чем отсутствие
// последней реплики.
async function flush() {
  if (writing) { dirty = true; return writing }
  writing = (async () => {
    do {
      dirty = false
      const tmp = DB_FILE + '.tmp'
      await writeFile(tmp, JSON.stringify(db), 'utf8')
      await rename(tmp, DB_FILE)
    } while (dirty)
  })().finally(() => { writing = null })
  return writing
}

const json = (res, code, body) => {
  const s = JSON.stringify(body)
  res.writeHead(code, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'content-length': Buffer.byteLength(s),
  })
  res.end(s)
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let n = 0
    const chunks = []
    req.on('data', (c) => {
      n += c.length
      if (n > MAX_BODY) { reject(new Error('too_large')); req.destroy(); return }
      chunks.push(c)
    })
    req.on('end', () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')) }
      catch (e) { reject(new Error('bad_json')) }
    })
    req.on('error', reject)
  })
}

const clip = (v, n) => String(v == null ? '' : v).slice(0, n)
const cookies = (req) => Object.fromEntries(
  (req.headers.cookie || '').split(';').map((p) => {
    const i = p.indexOf('=')
    return i < 0 ? [p.trim(), ''] : [p.slice(0, i).trim(), decodeURIComponent(p.slice(i + 1))]
  }))

const authed = (req) => !PASS || cookies(req).lpb_pass === PASS

const LOGIN = `<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Разбор правок — вход</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#eef0f3;
color:#171b24;font:15px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
form{background:#fff;border:1px solid #cfd5de;padding:1.6rem;min-width:min(22rem,92vw)}
h1{margin:0 0 .3rem;font-size:1.05rem}p{margin:0 0 1rem;color:#626b7c;font-size:.9rem}
input,button{font:inherit;width:100%;padding:.55rem .6rem;border:1px solid #cfd5de;background:#fff}
button{margin-top:.6rem;background:#171b24;color:#fff;border-color:#171b24;cursor:pointer}
</style>
<form method="POST" action="/login">
<h1>Разбор правок</h1><p>Введите пароль, который вам передали.</p>
<input type="password" name="password" autofocus autocomplete="current-password">
<button type="submit">Войти</button></form>`

const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x')
  const path = url.pathname

  if (path === '/healthz') return json(res, 200, { ok: true, rev: db.rev })

  // Браузер просит иконку сам; молчаливый ответ лучше 404 в консоли у каждого.
  if (path === '/favicon.ico') { res.writeHead(204); return res.end() }

  if (path === '/login' && req.method === 'POST') {
    const chunks = []
    for await (const c of req) chunks.push(c)
    const given = new URLSearchParams(Buffer.concat(chunks).toString()).get('password') || ''
    if (given !== PASS) { res.writeHead(303, { location: '/' }); return res.end() }
    res.writeHead(303, {
      location: '/',
      'set-cookie': `lpb_pass=${encodeURIComponent(PASS)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000`,
    })
    return res.end()
  }

  if (!authed(req)) {
    if (path.startsWith('/api/')) return json(res, 401, { error: 'нужен пароль' })
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' })
    return res.end(LOGIN)
  }

  // Всё состояние разом: документ открывают редко, а держать его целиком проще,
  // чем городить подписки ради сотни строк.
  if (path === '/api/state' && req.method === 'GET') {
    return json(res, 200, { rev: db.rev, verdicts: db.verdicts, threads: db.threads })
  }

  if (path === '/api/verdict' && req.method === 'POST') {
    let b
    try { b = await readBody(req) } catch (e) { return json(res, 400, { error: e.message }) }
    const id = clip(b.id, 40)
    if (!id) return json(res, 400, { error: 'нет номера правки' })
    const v = ['ok', 'no', ''].includes(b.v) ? b.v : ''
    db.verdicts[id] = { v, by: clip(b.by, MAX_NAME), at: new Date().toISOString() }
    db.rev++
    flush()
    return json(res, 200, { rev: db.rev, verdict: db.verdicts[id] })
  }

  if (path === '/api/comment' && req.method === 'POST') {
    let b
    try { b = await readBody(req) } catch (e) { return json(res, 400, { error: e.message }) }
    const id = clip(b.id, 40)
    const text = clip(b.text, MAX_TEXT).trim()
    if (!id || !text) return json(res, 400, { error: 'пусто' })
    const item = {
      key: randomUUID(), by: clip(b.by, MAX_NAME) || 'без имени',
      to: b.to === 'dev' ? 'dev' : 'claude',
      text, at: new Date().toISOString(),
    }
    ;(db.threads[id] ||= []).push(item)
    db.rev++
    flush()
    return json(res, 200, { rev: db.rev, comment: item })
  }

  if (path === '/api/comment' && req.method === 'DELETE') {
    let b
    try { b = await readBody(req) } catch (e) { return json(res, 400, { error: e.message }) }
    const list = db.threads[clip(b.id, 40)]
    if (list) {
      const i = list.findIndex((x) => x.key === b.key)
      if (i >= 0) { list.splice(i, 1); db.rev++; flush() }
    }
    return json(res, 200, { rev: db.rev })
  }

  if (path === '/api/export' && req.method === 'GET') {
    const out = []
    for (const [id, v] of Object.entries(db.verdicts)) {
      out.push({ id, verdict: v.v === 'ok' ? 'согласен' : v.v === 'no' ? 'убрать' : '',
                 by: v.by, at: v.at, comments: db.threads[id] || [] })
    }
    for (const [id, t] of Object.entries(db.threads)) {
      if (!db.verdicts[id]) out.push({ id, verdict: '', comments: t })
    }
    const s = JSON.stringify({ document: 'Что менять на сайте', answers: out }, null, 1)
    res.writeHead(200, {
      'content-type': 'application/json; charset=utf-8',
      'content-disposition': 'attachment; filename="otvety.json"',
    })
    return res.end(s)
  }

  if (path === '/' || path === '/index.html') {
    try {
      const page = await readFile(PAGE, 'utf8')
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' })
      return res.end(page)
    } catch (e) {
      res.writeHead(500, { 'content-type': 'text/plain; charset=utf-8' })
      return res.end('Страница не собрана: положите её в public/index.html')
    }
  }

  res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' })
  res.end('нет такой страницы')
})

await load()
server.listen(PORT, () => console.log(`разбор правок слушает :${PORT}, данные в ${DB_FILE}`))
