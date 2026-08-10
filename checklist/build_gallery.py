#!/usr/bin/env python3
"""Gallery of how the site looks right now, page by page, language by language.

The screenshots are taken from the captured pages rendered locally, so they show
the real layout and the real text — not a description of it. Useful next to the
work order: you read what changes, then look at what stands there today.

Usage:  python3 build_gallery.py <gallery_dir> <checklist.json> <out.html>
"""
import base64
import glob
import html
import json
import os
import sys

LOCALES = (("pl", "Polski"), ("ua", "Українська"), ("en", "English"))

# Pages the client's documents replace in full.
FULL_PAGES = {
    "terms-of-use", "privacy-policy", "polityka-cookies", "claims-and-complaints",
    "zgody-klauzule-i-regulamin-newslettera", "delivery-and-payment",
    "regulamin-kart-podarunkowych", "deklaracja-dostepnosci",
}

TITLES = {
    "index": "Главная", "contacts": "Контакты", "about": "О бренде",
    "delivery-and-payment": "Доставка и оплата", "terms-of-use": "Регламент магазина",
    "privacy-policy": "Политика конфиденциальности", "polityka-cookies": "Политика cookies",
    "claims-and-complaints": "Возвраты и рекламации",
    "zgody-klauzule-i-regulamin-newslettera": "Согласия и newsletter",
    "regulamin-kart-podarunkowych": "Подарочные карты",
    "deklaracja-dostepnosci": "Декларация доступности",
    "personal-data-requests": "Запросы по GDPR", "checkout": "Оформление заказа",
    "search": "Поиск", "favorites": "Избранное", "auth__login": "Вход",
    "auth__register": "Регистрация", "blog": "Блог — список",
    "brands": "Бренды — список", "special-offers": "Акции",
    "warranty-and-returns": "Гарантия и возврат (снять с публикации)",
    "warranty-and-returns__polityka-zwrotow": "Политика возвратов (снять с публикации)",
    "warranty-and-returns__gwarancja-na-produkt": "Гарантия на товар (снять с публикации)",
    "kids": "Категория: Дети", "girls": "Категория: Девочки", "boys": "Категория: Мальчики",
    "footwear": "Категория: Обувь", "accessories": "Категория: Аксессуары",
    "zabawki": "Категория: Игрушки", "niemowleta": "Категория: Малыши",
    "pielegnacja-i-kosmetyki": "Категория: Уход и косметика",
    "this-page-does-not-exist-404-probe": "Страница 404",
    "cart": "Корзина (сейчас 404)", "auth__forgot-password": "Восстановление пароля (сейчас 404)",
}


def title_for(slug):
    if slug in TITLES:
        return TITLES[slug]
    if slug.startswith("blog__"):
        return "Блог: " + slug[6:].replace("-", " ")[:46]
    if slug.startswith("brands__"):
        return "Бренд: " + slug[8:]
    if slug.startswith("search_q_"):
        return "Поиск: " + slug.split("-", 1)[-1]
    return slug.replace("__", "/").replace("-", " ")


def url_for(slug, locale):
    if slug.startswith("this-page"):
        return ""
    path = "/" + slug.replace("__", "/") if slug != "index" else ""
    pre = {"pl": "", "ua": "/ua", "en": "/en"}[locale]
    return f"lapetitebloom.com{pre}{path}"


def b64(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()


CSS = """
:root{--ground:#eef0f3;--surface:#fff;--sunken:#e4e7ec;--ink:#171b24;
 --muted:#626b7c;--line:#cfd5de;--hair:#dde2e9;--accent:#2b4b7d;--warn:#b3261e;--ok:#2f6b4f}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --ground:#12151b;--surface:#191d25;--sunken:#0d1015;--ink:#e6e9ef;--muted:#9099a8;
 --line:#333b47;--hair:#262d37;--accent:#8fb0e6;--warn:#ff9089;--ok:#7fc9a4}}
:root[data-theme="dark"]{--ground:#12151b;--surface:#191d25;--sunken:#0d1015;
 --ink:#e6e9ef;--muted:#9099a8;--line:#333b47;--hair:#262d37;--accent:#8fb0e6;
 --warn:#ff9089;--ok:#7fc9a4}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
 font:15px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.sheet{max-width:1180px;margin:0 auto;padding:2.5rem 1.25rem 5rem}
.mast{border-bottom:2px solid var(--ink);padding-bottom:1.1rem;margin-bottom:1.4rem}
.eyebrow{margin:0 0 .5rem;font-size:.7rem;font-weight:700;letter-spacing:.16em;
 text-transform:uppercase;color:var(--accent)}
h1{margin:0 0 .4rem;font-size:clamp(1.4rem,3.2vw,2rem);font-weight:650;letter-spacing:-.015em}
.lede{margin:0;color:var(--muted);max-width:68ch}
.toolbar{position:sticky;top:0;z-index:20;background:var(--ground);padding:.8rem 0;
 border-bottom:1px solid var(--line);margin-bottom:1.4rem;display:flex;gap:.5rem;
 flex-wrap:wrap;align-items:center}
input[type=search]{font:inherit;font-size:.95rem;padding:.45rem .7rem;flex:1 1 15rem;
 background:var(--surface);color:var(--ink);border:1px solid var(--line);min-width:0}
.btn{font:inherit;font-size:.74rem;letter-spacing:.05em;text-transform:uppercase;
 background:transparent;border:1px solid var(--line);color:var(--muted);
 padding:.38rem .7rem;cursor:pointer;white-space:nowrap}
.btn:hover{color:var(--ink);border-color:var(--muted)}
.btn[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--ground)}
.btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.count{font-size:.78rem;color:var(--muted);font-variant-numeric:tabular-nums}
.page{border:1px solid var(--line);background:var(--surface);margin:0 0 1rem}
.page[hidden]{display:none}
.head{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;padding:.7rem .9rem}
.ttl{font-weight:650;font-size:.96rem}
.url{font-family:ui-monospace,Menlo,monospace;font-size:.73rem;color:var(--accent);
 background:var(--sunken);padding:.05rem .35rem;word-break:break-all}
.tag{font-size:.62rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
 border:1px solid currentColor;padding:.05rem .35rem}
.t-full{color:var(--ok)} .t-off{color:var(--warn)} .t-fix{color:var(--muted)}
.n{margin-left:auto;font-size:.73rem;color:var(--muted);font-variant-numeric:tabular-nums}
.shots{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);
 border-top:1px solid var(--line)}
.shot{background:var(--surface);padding:.6rem}
.shot h4{margin:0 0 .4rem;font-size:.64rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--accent);font-weight:700;display:flex;justify-content:space-between;gap:.4rem}
.shot h4 span{color:var(--muted);font-weight:400;letter-spacing:0;text-transform:none;
 font-family:ui-monospace,Menlo,monospace;font-size:.66rem}
.shot img{width:100%;height:auto;display:block;border:1px solid var(--hair);
 background:#fff;cursor:zoom-in}
.shot img.zoom{position:fixed;inset:2vh 2vw;width:auto;height:96vh;max-width:96vw;
 object-fit:contain;object-position:top;z-index:50;cursor:zoom-out;
 box-shadow:0 4px 40px rgba(0,0,0,.5);background:#fff}
.hint{margin:0 0 1.2rem;padding:.7rem .9rem;background:var(--surface);
 border:1px solid var(--line);font-size:.87rem;color:var(--muted)}
.hint b{color:var(--ink)}
#totop{position:fixed;right:1rem;bottom:1rem;z-index:30;background:var(--surface);
 box-shadow:0 1px 6px rgba(0,0,0,.18);opacity:0;pointer-events:none;transition:opacity .2s}
#totop.on{opacity:1;pointer-events:auto}
@media (max-width:760px){.shots{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = """
var pages = [].slice.call(document.querySelectorAll('.page'));
var q = document.getElementById('q'), cnt = document.getElementById('cnt'), filter = 'all';
function apply() {
  var needle = q.value.trim().toLowerCase(), shown = 0;
  pages.forEach(function (p) {
    var okF = filter === 'all' || p.dataset.kind === filter;
    var okQ = !needle || p.dataset.search.indexOf(needle) !== -1;
    p.hidden = !(okF && okQ);
    if (okF && okQ) shown++;
  });
  cnt.textContent = shown === pages.length
    ? pages.length + ' страниц' : 'показано ' + shown + ' из ' + pages.length;
}
q.addEventListener('input', apply);
document.addEventListener('click', function (e) {
  var b = e.target.closest('.filters .btn');
  if (b) {
    [].forEach.call(document.querySelectorAll('.filters .btn'), function (x) {
      x.setAttribute('aria-pressed', String(x === b));
    });
    filter = b.dataset.k; apply(); return;
  }
  var img = e.target.closest('.shot img');
  if (img) { img.classList.toggle('zoom'); return; }
  if (e.target.closest('#theme')) {
    var r = document.documentElement;
    var dark = r.getAttribute('data-theme') === 'dark' ||
      (!r.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
    var n = dark ? 'light' : 'dark';
    r.setAttribute('data-theme', n);
    try { localStorage.setItem('lpb-theme', n); } catch (_) { }
  }
});
addEventListener('keydown', function (e) {
  if (e.key === 'Escape')
    [].forEach.call(document.querySelectorAll('.shot img.zoom'), function (i) {
      i.classList.remove('zoom');
    });
});
addEventListener('scroll', function () {
  document.getElementById('totop').classList.toggle('on', scrollY > 700);
}, { passive: true });
document.getElementById('totop').addEventListener('click', function () {
  scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
});
try { var t = localStorage.getItem('lpb-theme'); if (t) document.documentElement.setAttribute('data-theme', t); } catch (_) { }
apply();
"""


def main():
    gallery_dir, cl_path, out_path = sys.argv[1:4]
    checklist = json.load(open(cl_path, encoding="utf-8"))
    fixes_by_path = {}
    for g in checklist["groups"]:
        if g.get("path"):
            fixes_by_path[g["path"].lstrip("/") or "index"] = g["count"]

    slugs = sorted({os.path.basename(p)[:-4]
                    for p in glob.glob(os.path.join(gallery_dir, "*", "*.jpg"))})
    blocks, kinds = [], {"full": 0, "off": 0, "fix": 0}
    for slug in slugs:
        shots = []
        for code, label in LOCALES:
            path = os.path.join(gallery_dir, code, slug + ".jpg")
            if not os.path.exists(path):
                continue
            shots.append(
                f'<div class="shot"><h4>{label}<span>{html.escape(url_for(slug, code))}'
                f'</span></h4><img loading="lazy" alt="{html.escape(title_for(slug))} — '
                f'{label}" src="{b64(path)}"></div>')
        if not shots:
            continue

        if slug.startswith("warranty-and-returns"):
            kind, tag = "off", '<span class="tag t-off">снять с публикации</span>'
        elif slug in FULL_PAGES:
            kind, tag = "full", '<span class="tag t-full">заменить целиком</span>'
        else:
            kind, tag = "fix", ""
        kinds[kind] += 1
        n = fixes_by_path.get(slug, 0)
        title = title_for(slug)
        blocks.append(f"""
<section class="page" data-kind="{kind}"
         data-search="{html.escape((title + ' ' + slug + ' ' + url_for(slug,'pl')).lower())}">
  <header class="head">
    <span class="ttl">{html.escape(title)}</span>
    <code class="url">{html.escape(url_for(slug, 'pl'))}</code>
    {tag}
    <span class="n">{f'{n} правок' if n else ''}</span>
  </header>
  <div class="shots">{''.join(shots)}</div>
</section>""")

    doc = f"""<title>La Petite Bloom — как сайт выглядит сейчас</title>
<style>{CSS}</style>
<div class="sheet">
  <header class="mast">
    <p class="eyebrow">Снимки состояния · lapetitebloom.com</p>
    <h1>Как сайт выглядит сейчас</h1>
    <p class="lede">{len(blocks)} страниц в трёх языковых версиях — {len(slugs) * 3}
      снимков, страница целиком. Это то, что стоит на сайте на момент съёмки:
      настоящая вёрстка, настоящие тексты. Смотрите рядом со списком правок.</p>
  </header>

  <p class="hint"><b>Клик по снимку</b> разворачивает его на весь экран, повторный клик
    или Esc возвращает. Снимки сделаны с ширины 1440 px. Баннер согласия на них
    не попал намеренно — иначе он перекрывал бы каждую страницу.</p>

  <div class="toolbar">
    <input type="search" id="q" placeholder="Поиск по названию или адресу…"
           aria-label="Поиск" autocomplete="off">
    <span class="filters">
      <button class="btn" data-k="all" aria-pressed="true">Все</button>
      <button class="btn" data-k="full" aria-pressed="false">Заменить целиком <i>{kinds['full']}</i></button>
      <button class="btn" data-k="fix" aria-pressed="false">По абзацам <i>{kinds['fix']}</i></button>
      <button class="btn" data-k="off" aria-pressed="false">Снять <i>{kinds['off']}</i></button>
    </span>
    <span class="count" id="cnt"></span>
    <button class="btn" id="theme" type="button">Тема</button>
  </div>

  {''.join(blocks)}
</div>
<button class="btn" id="totop" type="button">↑ Наверх</button>
<script>{JS}</script>"""

    open(out_path, "w", encoding="utf-8").write(doc)
    print(f"{out_path}  {len(doc.encode('utf-8'))/1024/1024:.2f} МБ  "
          f"страниц: {len(blocks)}  снимков: {len(slugs)*3}")


if __name__ == "__main__":
    main()
