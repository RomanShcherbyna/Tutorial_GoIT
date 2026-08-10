#!/usr/bin/env python3
"""One page where every finished text can be read before it goes on the site.

The archive is fine for handing to a developer and useless for checking the
work: you cannot read a .docx in a browser, and eight pages times three
languages is twenty-four files to open. Here each page renders as it will look,
a click switches language, and both files stay downloadable from the same spot.

Usage:  python3 build_preview.py <pages_dir> <translations.json> <out.html>
"""
import base64
import glob
import json
import mimetypes
import os
import re
import sys

LANGS = (("pl", "Polski"), ("ua", "Українська"), ("en", "English"))
DOCX = ("application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document")


def data_uri(path):
    raw = open(path, "rb").read()
    mime = mimetypes.guess_type(path)[0] or DOCX
    return f"data:{mime};base64," + base64.b64encode(raw).decode(), len(raw)


def collect(pages_dir, tr):
    titles, pages_meta = {}, {}
    for doc in tr["documents"]:
        page = doc.get("page") or {}
        if not page:
            continue
        slug = page["pl"].rstrip("/").split("/")[-1]
        titles[slug] = doc["title"]
        pages_meta[slug] = page

    out = []
    for folder in sorted(glob.glob(os.path.join(pages_dir, "*/"))):
        slug = folder.rstrip("/").split(os.sep)[-1]
        entry = {"slug": slug, "title": titles.get(slug, slug),
                 "urls": pages_meta.get(slug, {}), "langs": {}}
        for code, _ in LANGS:
            h = os.path.join(folder, f"{slug}.{code}.html")
            d = os.path.join(folder, f"{slug}.{code}.docx")
            if not os.path.exists(h):
                continue
            body = open(h, encoding="utf-8").read()
            html_uri, html_size = data_uri(h)
            docx_uri, docx_size = data_uri(d) if os.path.exists(d) else ("", 0)
            entry["langs"][code] = {
                "body": body,
                "words": len(re.sub(r"<[^>]+>", " ", body).split()),
                "html": html_uri, "html_size": html_size,
                "docx": docx_uri, "docx_size": docx_size,
                "file": f"{slug}.{code}",
            }
        if entry["langs"]:
            out.append(entry)
    return out


CSS = """
:root{--ground:#eef0f3;--surface:#fff;--sunken:#e4e7ec;--ink:#171b24;
 --muted:#626b7c;--line:#cfd5de;--hair:#dde2e9;--accent:#2b4b7d}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --ground:#12151b;--surface:#191d25;--sunken:#0d1015;--ink:#e6e9ef;
 --muted:#9099a8;--line:#333b47;--hair:#262d37;--accent:#8fb0e6}}
:root[data-theme="dark"]{--ground:#12151b;--surface:#191d25;--sunken:#0d1015;
 --ink:#e6e9ef;--muted:#9099a8;--line:#333b47;--hair:#262d37;--accent:#8fb0e6}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
 font:15px/1.65 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
 -webkit-font-smoothing:antialiased}
.sheet{max-width:1000px;margin:0 auto;padding:2.5rem 1.25rem 5rem}
.mast{border-bottom:2px solid var(--ink);padding-bottom:1.1rem;margin-bottom:1.6rem}
.eyebrow{margin:0 0 .5rem;font-size:.7rem;font-weight:700;letter-spacing:.16em;
 text-transform:uppercase;color:var(--accent)}
h1{margin:0 0 .4rem;font-size:clamp(1.4rem,3.2vw,2rem);font-weight:650;letter-spacing:-.015em}
.lede{margin:0;color:var(--muted);max-width:66ch}
.toolbar{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:1.2rem 0 1.6rem}
.btn{font:inherit;font-size:.76rem;letter-spacing:.05em;text-transform:uppercase;
 background:transparent;border:1px solid var(--line);color:var(--muted);
 padding:.4rem .75rem;cursor:pointer;white-space:nowrap}
.btn:hover{color:var(--ink);border-color:var(--muted)}
.btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.btn[aria-pressed="true"],.btn[aria-selected="true"]{
 background:var(--ink);border-color:var(--ink);color:var(--ground)}
.doc{border:1px solid var(--line);background:var(--surface);margin:0 0 1rem}
.dochead{display:flex;gap:.7rem;align-items:center;flex-wrap:wrap;padding:.75rem .95rem;
 cursor:pointer}
.dochead:hover{background:var(--sunken)}
.arrow{color:var(--muted);width:1rem;flex:none;font-size:.8rem}
.dtitle{font-weight:650;font-size:.98rem}
.durl{font-family:ui-monospace,Menlo,monospace;font-size:.74rem;color:var(--accent);
 background:var(--sunken);padding:.05rem .35rem;word-break:break-all}
.dmeta{margin-left:auto;font-size:.74rem;color:var(--muted);font-variant-numeric:tabular-nums}
.docbody{border-top:1px solid var(--line);padding:.85rem .95rem 1.2rem}
.tabs{display:flex;gap:.35rem;flex-wrap:wrap;margin-bottom:.5rem}
.dl{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:0 0 1rem;
 padding-bottom:.8rem;border-bottom:1px solid var(--hair);font-size:.8rem}
.dl a{color:var(--accent);text-decoration:none;border:1px solid var(--line);
 padding:.25rem .6rem;font-family:ui-monospace,Menlo,monospace;font-size:.76rem}
.dl a:hover{border-color:var(--accent)}
.dl .live{margin-left:auto;color:var(--muted);font-family:ui-monospace,Menlo,monospace;
 font-size:.74rem;word-break:break-all}
.render{background:var(--ground);border:1px solid var(--hair);padding:1.4rem 1.6rem;
 max-height:none}
.render h1{font-size:1.25rem;margin:0 0 .8rem;font-weight:650}
.render h2{font-size:.98rem;margin:1.4rem 0 .5rem;font-weight:700;
 padding-bottom:.25rem;border-bottom:1px solid var(--hair)}
.render p{margin:.6rem 0;font-size:.92rem}
.render ol,.render ul{margin:.6rem 0;padding-left:1.4rem;font-size:.92rem}
.render li{margin-bottom:.35rem}
.render a{color:var(--accent)}
.pane{display:none}
.pane.on{display:block}
.doc.closed .docbody{display:none}
#totop{position:fixed;right:1rem;bottom:1rem;z-index:30;background:var(--surface);
 box-shadow:0 1px 6px rgba(0,0,0,.18);opacity:0;pointer-events:none;transition:opacity .2s}
#totop.on{opacity:1;pointer-events:auto}
@media (max-width:600px){.render{padding:1rem}.dmeta{margin-left:0;width:100%}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = """
document.addEventListener('click', function (e) {
  var head = e.target.closest('.dochead');
  if (head && !e.target.closest('a')) {
    var doc = head.closest('.doc');
    doc.classList.toggle('closed');
    head.querySelector('.arrow').textContent = doc.classList.contains('closed') ? '▸' : '▾';
    return;
  }
  var tab = e.target.closest('.tabs .btn');
  if (tab) {
    var body = tab.closest('.docbody');
    [].forEach.call(body.querySelectorAll('.tabs .btn'), function (b) {
      b.setAttribute('aria-selected', String(b === tab));
    });
    [].forEach.call(body.querySelectorAll('.pane'), function (p) {
      p.classList.toggle('on', p.dataset.lang === tab.dataset.lang);
    });
    return;
  }
  var all = e.target.closest('#expand');
  if (all) {
    var open = all.dataset.state !== 'open';
    all.dataset.state = open ? 'open' : 'closed';
    all.textContent = open ? 'Свернуть всё' : 'Развернуть всё';
    [].forEach.call(document.querySelectorAll('.doc'), function (d) {
      d.classList.toggle('closed', !open);
      d.querySelector('.arrow').textContent = open ? '▾' : '▸';
    });
    return;
  }
  if (e.target.closest('#theme')) {
    var r = document.documentElement;
    var dark = r.getAttribute('data-theme') === 'dark' ||
      (!r.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
    var next = dark ? 'light' : 'dark';
    r.setAttribute('data-theme', next);
    try { localStorage.setItem('lpb-theme', next); } catch (_) { }
  }
});
addEventListener('scroll', function () {
  document.getElementById('totop').classList.toggle('on', scrollY > 700);
}, { passive: true });
document.getElementById('totop').addEventListener('click', function () {
  scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
});
try {
  var th = localStorage.getItem('lpb-theme');
  if (th) document.documentElement.setAttribute('data-theme', th);
} catch (_) { }
"""


def kb(n):
    return f"{max(1, round(n / 1024))} КБ"


def main():
    pages_dir, tr_path, out_path = sys.argv[1:4]
    tr = json.load(open(tr_path, encoding="utf-8"))
    pages = collect(pages_dir, tr)

    blocks = []
    for i, p in enumerate(pages):
        tabs, panes = [], []
        for code, label in LANGS:
            d = p["langs"].get(code)
            if not d:
                continue
            first = code == "pl"
            tabs.append(f'<button class="btn" type="button" data-lang="{code}" '
                        f'aria-selected="{str(first).lower()}">{label}</button>')
            live = p["urls"].get(code, "")
            panes.append(f"""
<div class="pane{' on' if first else ''}" data-lang="{code}">
  <div class="dl">
    <a href="{d['docx']}" download="{d['file']}.docx">{d['file']}.docx · {kb(d['docx_size'])}</a>
    <a href="{d['html']}" download="{d['file']}.html">{d['file']}.html · {kb(d['html_size'])}</a>
    <span class="live">{live.replace('https://', '')}</span>
  </div>
  <div class="render">{d['body']}</div>
</div>""")

        words = p["langs"].get("pl", {}).get("words", 0)
        blocks.append(f"""
<section class="doc{' closed' if i else ''}">
  <header class="dochead">
    <span class="arrow">{'▸' if i else '▾'}</span>
    <span class="dtitle">{p['title']}</span>
    <code class="durl">{p['urls'].get('pl','').replace('https://','')}</code>
    <span class="dmeta">{words} слов · 3 языка · 6 файлов</span>
  </header>
  <div class="docbody">
    <div class="tabs">{''.join(tabs)}</div>
    {''.join(panes)}
  </div>
</section>""")

    total_files = sum(len(p["langs"]) * 2 for p in pages)
    html = f"""<title>La Petite Bloom — тексты страниц</title>
<style>{CSS}</style>
<div class="sheet">
  <header class="mast">
    <p class="eyebrow">Готовые тексты · lapetitebloom.com</p>
    <h1>Тексты страниц на трёх языках</h1>
    <p class="lede">{len(pages)} страниц, {total_files} файлов. Каждая показана так,
      как будет выглядеть на сайте: переключите язык, прочитайте, скачайте
      <code>.docx</code> для согласования или <code>.html</code> для вставки.
      Адреса остаются прежними.</p>
  </header>
  <div class="toolbar">
    <button class="btn" id="expand" type="button" data-state="closed">Развернуть всё</button>
    <button class="btn" id="theme" type="button">Тема</button>
  </div>
  {''.join(blocks)}
</div>
<button class="btn" id="totop" type="button">↑ Наверх</button>
<script>{JS}</script>"""

    open(out_path, "w", encoding="utf-8").write(html)
    size = len(html.encode("utf-8")) / 1024 / 1024
    print(f"{out_path}  {size:.2f} МБ  страниц: {len(pages)}  файлов внутри: {total_files}")


if __name__ == "__main__":
    main()
