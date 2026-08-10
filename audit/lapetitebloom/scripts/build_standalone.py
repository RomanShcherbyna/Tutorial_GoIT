#!/usr/bin/env python3
"""Wrap the audit into one HTML file that can be emailed and opened by
double-click — no server, no internet, no tooling on the far end.

The artifact page is a fragment (it starts at <title>, the host supplies the
document around it). Here we build the same body from the same source and add
what a 334-item page needs when nobody is there to explain it: a text search, a
live count, a contents list, a back-to-top button, a theme switch, print rules
that turn Ctrl+P into a usable PDF, and the glossary appended so there is only
ever one file to forward.

Usage:  python3 build_standalone.py <findings.json> <glossary.md> <out.html>
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_report  # noqa: E402


# --------------------------------------------------------------------------
def glossary_html(path):
    """Render glossary.md. Falls back to a minimal converter if the markdown
    package is unavailable, so the deliverable never depends on a pip install."""
    src = open(path, encoding="utf-8").read()
    # The file's own H1 duplicates the section heading we add below.
    src = re.sub(r"\A#\s+[^\n]*\n", "", src)
    try:
        import markdown
        body = markdown.markdown(src, extensions=["tables", "sane_lists"])
    except ImportError:
        body = _mini_markdown(src)
    # Wide term tables must scroll inside themselves, not push the page sideways.
    body = re.sub(r"<table>", '<div class="tw"><table>', body)
    body = re.sub(r"</table>", "</table></div>", body)
    return body


def _mini_markdown(src):
    out, rows = [], []

    def flush():
        if not rows:
            return
        head, body = rows[0], rows[2:] if len(rows) > 2 else []
        cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
        out.append("<div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{_inline(c)}</th>" for c in cells(head))
                   + "</tr></thead><tbody>"
                   + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>"
                                              for c in cells(r)) + "</tr>"
                             for r in body)
                   + "</tbody></table></div>")
        rows.clear()

    for line in src.split("\n"):
        if line.startswith("|"):
            rows.append(line)
            continue
        flush()
        s = line.strip()
        if not s:
            continue
        m = re.match(r"(#{1,4})\s+(.*)", s)
        if m:
            lvl = len(m.group(1)) + 1
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
        elif s.startswith(("- ", "* ")):
            out.append(f"<ul><li>{_inline(s[2:])}</li></ul>")
        elif set(s) <= set("-—= "):
            out.append("<hr>")
        else:
            out.append(f"<p>{_inline(s)}</p>")
    flush()
    return "\n".join(out)


def _inline(s):
    s = build_report.esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


# --------------------------------------------------------------------------
HEAD_EXTRA = """
/* ---------- standalone-only chrome ---------- */
.toolbar{
  position:sticky;top:0;z-index:20;background:var(--ground);
  padding:.9rem 0 .7rem;margin-bottom:.2rem;
  border-bottom:1px solid var(--line);
}
.search{
  display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;
}
.search input{
  flex:1 1 18rem;min-width:0;font:inherit;font-size:.95rem;
  padding:.5rem .75rem;background:var(--surface);color:var(--ink);
  border:1px solid var(--line);
}
.search input:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.search .count{
  font-size:.78rem;color:var(--muted);white-space:nowrap;
  font-variant-numeric:tabular-nums;
}
.iconbtn{
  font:inherit;font-size:.78rem;letter-spacing:.05em;text-transform:uppercase;
  background:transparent;border:1px solid var(--line);color:var(--muted);
  padding:.45rem .7rem;cursor:pointer;white-space:nowrap;
}
.iconbtn:hover{color:var(--ink);border-color:var(--muted)}
.iconbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.howto{
  margin:1rem 0 0;padding:.85rem 1rem;background:var(--surface);
  border:1px solid var(--line);font-size:.9rem;color:var(--muted);
}
.howto b{color:var(--ink)}
.toc{
  margin:1.25rem 0 0;padding:0;list-style:none;display:flex;
  flex-wrap:wrap;gap:.4rem .5rem;font-size:.85rem;
}
.toc a{
  color:var(--accent);text-decoration:none;border-bottom:1px solid transparent;
  padding:.15rem 0;
}
.toc a:hover{border-bottom-color:var(--accent)}
#totop{
  position:fixed;right:1rem;bottom:1rem;z-index:30;background:var(--surface);
  box-shadow:0 1px 6px rgba(0,0,0,.18);opacity:0;pointer-events:none;
  transition:opacity .2s;
}
#totop.on{opacity:1;pointer-events:auto}

/* ---------- glossary ---------- */
.glossary{margin:3rem 0 0;padding-top:1.5rem;border-top:2px solid var(--ink)}
.glossary h2{
  margin:2rem 0 .8rem;font-size:1.12rem;font-weight:700;padding-bottom:.4rem;
  border-bottom:1px solid var(--line);
}
.glossary h3{margin:1.4rem 0 .5rem;font-size:.95rem;font-weight:700}
.glossary h4{margin:1.1rem 0 .4rem;font-size:.88rem;font-weight:700;color:var(--muted)}
.glossary p{margin:.55rem 0;font-size:.93rem;max-width:74ch}
.glossary ul{padding-left:1.1rem;font-size:.93rem}
.glossary li{margin-bottom:.35rem}
.glossary code{
  background:var(--sunken);padding:.05rem .3rem;font-size:.85em;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
}
.tw{overflow-x:auto;margin:.9rem 0;border:1px solid var(--line)}
.glossary table{border-collapse:collapse;width:100%;font-size:.85rem;min-width:40rem}
.glossary th,.glossary td{
  text-align:left;padding:.45rem .7rem;border-bottom:1px solid var(--hair);
  vertical-align:top;
}
.glossary thead th{
  background:var(--sunken);font-weight:700;font-size:.75rem;
  letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  position:sticky;top:0;
}
.glossary tbody tr:last-child td{border-bottom:0}

/* ---------- print: Ctrl+P becomes a usable PDF ---------- */
@media print{
  :root{
    --ground:#fff; --surface:#fff; --sunken:#f4f4f4; --ink:#000;
    --muted:#444; --line:#bbb; --hair:#ddd; --accent:#333;
  }
  .toolbar,.filters,#totop,.howto,.toc{display:none!important}
  body{font-size:10.5pt}
  .sheet{max-width:none;padding:0}
  .find{break-inside:avoid;page-break-inside:avoid}
  .lanes{grid-template-columns:1fr}
  .tw{overflow:visible;border:0}
  .glossary table{min-width:0;font-size:8.5pt}
  .glossary thead th{position:static}
  .evidence,.lane pre{max-height:none;overflow:visible}
  h1,h2,h3{break-after:avoid;page-break-after:avoid}
  a{color:inherit;text-decoration:none}
}
"""

TOOLBAR = """
<div class="toolbar">
  <div class="search">
    <input type="search" id="q" placeholder="Поиск по находкам: страница, текст, номер…"
           aria-label="Поиск по находкам" autocomplete="off">
    <span class="count" id="count"></span>
    <button class="iconbtn" id="theme" type="button">Тема</button>
    <button class="iconbtn" id="print" type="button">Печать / PDF</button>
  </div>
</div>
"""


def howto(total):
    return f"""
<p class="howto"><b>Как этим пользоваться.</b> Ниже {total} находок, отсортированных по
серьёзности. Кнопки под шапкой фильтруют по типу проблемы, поле поиска ищет по адресу
страницы, цитате и номеру находки — работают вместе. У каждой находки сначала идёт
точная цитата того, <b>что сейчас на сайте</b>, затем готовый текст на трёх языках:
его можно выделить и скопировать прямо в админку. Кнопка «Печать / PDF» сохраняет
отчёт файлом. Интернет не нужен, файл работает сам по себе.</p>

<ul class="toc">
  <li><a href="#glavnoe">Главное</a></li>
  <li><a href="#rekvizity">Вопрос про KRS / NIP / REGON</a></li>
  <li><a href="#nahodki">Все находки</a></li>
  <li><a href="#neproveryali">Что не проверяли</a></li>
  <li><a href="#glossary">Глоссарий терминов</a></li>
</ul>
"""


SCRIPT = """
(function(){
  var finds=[].slice.call(document.querySelectorAll('.find'));
  var btns=[].slice.call(document.querySelectorAll('.filters button'));
  var q=document.getElementById('q');
  var count=document.getElementById('count');
  var empty=document.querySelector('.empty');
  var total=finds.length;
  var state={key:'all',val:null,query:''};

  finds.forEach(function(f){
    f._hay=(f.textContent||'').toLowerCase();
  });

  function apply(){
    var needle=state.query.trim().toLowerCase();
    var shown=0;
    finds.forEach(function(f){
      var okFilter = state.key==='all' || f.dataset[state.key]===state.val;
      var okQuery  = !needle || f._hay.indexOf(needle)!==-1;
      var ok = okFilter && okQuery;
      f.hidden=!ok;
      if(ok) shown++;
    });
    if(empty) empty.hidden = shown>0;
    count.textContent = shown===total
      ? total+' находок'
      : 'показано '+shown+' из '+total;
  }

  btns.forEach(function(b){
    b.addEventListener('click',function(){
      btns.forEach(function(x){x.setAttribute('aria-pressed',String(x===b));});
      state.key=b.dataset.f==='all'?'all':(b.dataset.f==='sev'?'sev':'issue');
      state.val=b.dataset.v||null;
      apply();
    });
  });
  q.addEventListener('input',function(){state.query=q.value;apply();});

  // theme: follow the system until the reader says otherwise, then remember
  var root=document.documentElement;
  try{
    var saved=localStorage.getItem('lpb-theme');
    if(saved) root.setAttribute('data-theme',saved);
  }catch(e){}
  document.getElementById('theme').addEventListener('click',function(){
    var dark=root.getAttribute('data-theme')==='dark'
      || (!root.getAttribute('data-theme')
          && matchMedia('(prefers-color-scheme: dark)').matches);
    var next=dark?'light':'dark';
    root.setAttribute('data-theme',next);
    try{localStorage.setItem('lpb-theme',next);}catch(e){}
  });
  document.getElementById('print').addEventListener('click',function(){print();});

  var top=document.getElementById('totop');
  addEventListener('scroll',function(){
    top.classList.toggle('on',scrollY>900);
  },{passive:true});
  top.addEventListener('click',function(){
    scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches
      ?'auto':'smooth'});
  });

  apply();
})();
"""


# --------------------------------------------------------------------------
def main():
    findings_path, glossary_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    items = json.load(open(findings_path, encoding="utf-8"))
    stats = {
        "pages": 54,
        "sev": Counter(f["severity"] for f in items),
        "issue": Counter(f["issue"] for f in items),
    }

    frag = build_report.html_report(items, stats)

    # Split the fragment into <title> / <style> / body / <script>.
    title = re.search(r"<title>(.*?)</title>", frag, re.S).group(1)
    css = re.search(r"<style>(.*?)</style>", frag, re.S).group(1)
    js = re.search(r"<script>(.*?)</script>\s*\Z", frag, re.S).group(1)
    body = frag
    for chunk in (f"<title>{title}</title>", f"<style>{css}</style>",
                  f"<script>{js}</script>"):
        body = body.replace(chunk, "")
    body = body.strip()

    # Anchors for the contents list.
    body = body.replace("<h2>Главное</h2>", '<h2 id="glavnoe">Главное</h2>', 1)
    body = body.replace("<h2>Все находки</h2>",
                        '<h2 id="nahodki">Все находки</h2>', 1)
    body = body.replace("<h2>Что не проверяли</h2>",
                        '<h2 id="neproveryali">Что не проверяли</h2>', 1)
    body = re.sub(r"<h2>(Нам вписывать KRS[^<]*)</h2>",
                  r'<h2 id="rekvizity">\1</h2>', body, count=1)

    # Toolbar + how-to go right after the masthead; the filters stay put.
    body = body.replace("</header>", "</header>\n" + TOOLBAR
                        + howto(len(items)), 1)

    glossary = f"""
<section class="glossary" id="glossary">
  <h2>Глоссарий терминов PL / UA / EN</h2>
  <p class="dim">Чтобы одно и то же на сайте называлось одинаково, пока правки
    расходятся по страницам. В конце — список мест, где сейчас один термин
    переведён по-разному.</p>
  {glossary_html(glossary_path)}
</section>"""

    # The glossary belongs inside .sheet, so it inherits the page width —
    # splice it in before the wrapper's closing tag rather than after it.
    close = body.rfind("</div>")
    if close == -1:
        raise SystemExit("could not find the closing .sheet wrapper")
    body = body[:close] + glossary + "\n" + body[close:]

    doc = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{title}</title>
<style>{css}{HEAD_EXTRA}</style>
</head>
<body>
{body}
<button class="iconbtn" id="totop" type="button" aria-label="Наверх">↑ Наверх</button>
<script>{SCRIPT}</script>
</body>
</html>
"""
    open(out_path, "w", encoding="utf-8").write(doc)
    print(f"wrote {out_path}  {len(doc):,} bytes  {len(items)} findings")


if __name__ == "__main__":
    main()
