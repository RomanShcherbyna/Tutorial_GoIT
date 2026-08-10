#!/usr/bin/env python3
"""The work order: what to do on every page, in the form the page needs.

Two kinds of page, and they are worked differently.

Where the client has a document, the page is replaced whole — the old text goes,
the new text arrives, and listing what to delete is noise. Where there is no
document, only some paragraphs change, and a developer needs the pair: this is
what stands there now, this is what replaces it, in each language.

Usage:  python3 build_workorder.py <checklist.json> <translations.json> <pages_dir> <out.html>
"""
import base64
import glob
import html
import json
import mimetypes
import os
import re
import sys

LANGS = (("pl", "Polski"), ("ua", "Українська"), ("en", "English"))
DOCX = ("application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document")

# Pages the client's documents cover — these get replaced in full.
FULL_PAGES = {
    "/terms-of-use", "/privacy-policy", "/polityka-cookies",
    "/claims-and-complaints", "/zgody-klauzule-i-regulamin-newslettera",
    "/delivery-and-payment", "/regulamin-kart-podarunkowych",
    "/deklaracja-dostepnosci",
}

# Groups whose every item disappears the moment the page above is replaced.
#
# The audit found these before the documents arrived, so the same page shows up
# twice: once as a finished text in part 1, once as a list of paragraph fixes
# below. Repeating the second list is worse than useless — it reads as extra
# work that is in fact already done by the replacement.
#
# Four of them are the same eight pages under a Polish slug the audit proposed
# before the client ruled that addresses do not change. "__docs__" holds the
# translator's notes on the consents document. The /warranty-and-returns trio
# is being taken down, so its paragraphs are not worth fixing.
COVERED_BY_DOCS = {
    "/polityka-prywatnosci", "/regulamin", "/zwroty-i-reklamacje",
    "/dostawa-i-platnosci", "__docs__",
    "/warranty-and-returns", "/warranty-and-returns/polityka-zwrotow",
    "/warranty-and-returns/gwarancja-na-produkt",
}

# Pages copied from another brand, carrying French consumer law. They are not
# edited — they come down, in all three locales.
UNPUBLISH = [
    "https://lapetitebloom.com/warranty-and-returns",
    "https://lapetitebloom.com/warranty-and-returns/polityka-zwrotow",
    "https://lapetitebloom.com/warranty-and-returns/gwarancja-na-produkt",
    "https://lapetitebloom.com/ua/warranty-and-returns",
    "https://lapetitebloom.com/ua/warranty-and-returns/polityka-zwrotow",
    "https://lapetitebloom.com/ua/warranty-and-returns/gwarancja-na-produkt",
    "https://lapetitebloom.com/en/warranty-and-returns",
    "https://lapetitebloom.com/en/warranty-and-returns/polityka-zwrotow",
    "https://lapetitebloom.com/en/warranty-and-returns/gwarancja-na-produkt",
]

# Nine things the finished text could not decide on its own. The client decided
# them; this is the record of what was chosen and where each answer landed, so
# nobody has to reopen the question later to find out what was agreed.
DECIDED = [
    ("Наложенный платёж стоит 23 zł",
     "Стояла вилка «+20–23 zł». Цена доставки должна быть точной до "
     "оформления заказа — вилку проверяющий не пропустит.",
     "Регламент §7.1 · Доставка и оплата — проставлено в трёх языках"),
    ("Бесплатная доставка — от 500 zł по корзине после скидок",
     "Было просто «od 500 zł», и при промокоде магазин с покупателем "
     "посчитали бы по-разному.",
     "Регламент §7.2 · Доставка и оплата — дописано «liczonej od wartości "
     "koszyka po uwzględnieniu rabatów»"),
    ("За границу возит DHL",
     "Документ противоречил сам себе: в перечне тарифов стоял DHL, а ниже "
     "было сказано, что для Украины доступны Nova Poshta и Meest. "
     "Оставлен DHL — упоминание двух других служб из текста убрано.",
     "Доставка и оплата, абзац о заграничной отправке"),
    ("Все восемь документов вступают в силу 01.09.2026, версия 1.0",
     "Стояло 24.06.2026 — дата, которая уже прошла, при том что магазин "
     "не открыт. Документ утверждал бы, что был в силе, когда покупателей "
     "не было. Это первая редакция, предупреждать об изменении правил "
     "некого, поэтому дата равна дню публикации. У «Доставки и оплаты» "
     "даты не было вообще — теперь та же. Сдвинется запуск — меняется одно "
     "число в шапке каждого документа.",
     "Шапка всех восьми документов · декларация доступности ещё в конце"),
    ("Возврат шлём на Mokotowska 51/53, реквизиты фирмы — Kasprzaka 31/119",
     "В документах это уже разведено правильно, менять ничего не пришлось: "
     "адрес компании стоит в реквизитах, адрес возврата — в порядке возврата "
     "и в бланке отказа. Осталась задача проставить адрес возврата в "
     "интерфейсе, письмах и вкладыше в посылку.",
     "Регламент §2 и §8 · Возвраты и рекламации"),
    ("Срок возврата — 14 дней",
     "В полосе преимуществ на всех страницах сайта обещано 30 дней, "
     "в регламенте — 14 по закону. Обещание с сайта снимается.",
     "Полоса преимуществ, все страницы, три языка — задача DOC-09, "
     "текст на замену теперь есть"),
    ("Оба согласия на маркетинг остаются",
     "Два чекбокса читались как одно и то же разрешение. Оставлены оба, "
     "но разведены по каналам: первый — рассылка о новинках и акциях, "
     "второй — электронные каналы, e-mail и SMS, по ст. 10 uśude.",
     "Согласия и newsletter, тексты чекбоксов"),
    ("Почта — hello@ и rodo@",
     "В переводах эти адреса уже стояли, kontakt@ не встречался ни разу. "
     "Убрана только редакторская пометка «(opcjonalnie alias "
     "zwroty@/reklamacje@)» — покупателю незачем читать заметку о том, "
     "какие ящики мы, может быть, когда-нибудь заведём.",
     "Регламент §2, список контактов"),
]

OWNER_STYLE = {"dev": "o-dev", "content": "o-content", "catalog": "o-catalog"}

KIND = {
    "replace": ("Заменить", "Такой текст стоит на странице сейчас — его меняем"),
    "add": ("Добавить", "Этого на странице нет, надо дописать"),
    "do": ("Сделать", "Правка техническая, готового текста не требует"),
}


def esc(s):
    return html.escape(str(s or ""))


def data_uri(path):
    raw = open(path, "rb").read()
    mime = mimetypes.guess_type(path)[0] or DOCX
    return f"data:{mime};base64," + base64.b64encode(raw).decode(), len(raw)


def kind_of(f):
    has_text = any(f.get(k) for k in ("pl", "ua", "en"))
    if f.get("current") and has_text:
        return "replace"
    if has_text:
        return "add"
    return "do"


def collect_full(pages_dir, tr):
    """Pages replaced whole, with their finished text and files."""
    out = []
    for doc in tr["documents"]:
        page = doc.get("page") or {}
        if not page:
            continue
        slug = page["pl"].rstrip("/").split("/")[-1]
        folder = os.path.join(pages_dir, slug)
        if not os.path.isdir(folder):
            continue
        langs = {}
        for code, _ in LANGS:
            h = os.path.join(folder, f"{slug}.{code}.html")
            d = os.path.join(folder, f"{slug}.{code}.docx")
            if not os.path.exists(h):
                continue
            html_uri, hs = data_uri(h)
            docx_uri, ds = data_uri(d) if os.path.exists(d) else ("", 0)
            langs[code] = {"body": open(h, encoding="utf-8").read(),
                           "html": html_uri, "html_size": hs,
                           "docx": docx_uri, "docx_size": ds,
                           "file": f"{slug}.{code}"}
        ui = []
        ui_folder = os.path.join(pages_dir, f"{slug}-ui")
        if os.path.isdir(ui_folder):
            for code, _ in LANGS:
                h = os.path.join(ui_folder, f"{slug}-ui.{code}.html")
                if os.path.exists(h):
                    ui.append((code, open(h, encoding="utf-8").read()))
        out.append({"slug": slug, "title": doc["title"], "urls": page,
                    "langs": langs, "ui": ui, "ui_title": doc.get("ui_title", "")})
    return out


OWNER_NAMES = [("dev", "Программисты"), ("content", "Наш контент"),
               ("catalog", "Каталог / BaseLinker")]


def attach_crops(groups, crops_dir):
    """Each fix gets a cut-out of the spot it is about, with the place outlined.

    A whole-page screenshot proves the page exists; it does not show the
    mistake, which is what was asked for."""
    if not crops_dir or not os.path.isdir(crops_dir):
        return groups, 0
    n = 0
    for g in groups:
        # collect_partial already copied the fixes into "items"; writing to
        # "fixes" here would decorate objects nobody renders.
        for f in g.get("items", g["fixes"]):
            path = os.path.join(crops_dir, f["id"] + ".jpg")
            if os.path.exists(path):
                f["crop"] = ("data:image/jpeg;base64,"
                             + base64.b64encode(open(path, "rb").read()).decode())
                n += 1
    return groups, n


# This document is about wording only: what is written on the site and how it
# is spelled. Two things are deliberately not here. Attribute values and
# product copy come down from BaseLinker, so fixing them on the page is
# pointless — the next import overwrites it. And required legal paragraphs are
# new writing rather than proofreading; they live in their own document.
TEXT_ISSUES = {"TYPO", "WRONG", "MISSING", "LEFTOVER", "STUB", "CONFLICT"}
FROM_BASELINKER = "catalog"

# Three product-card fixes are filed against the template but read the feed:
# the raw supplier name in the heading, the country of origin, and the
# manufacturer contact. Whoever edits the page cannot hold them — the next
# import writes over the field.
FEED_FED = {"11-01", "11-06", "11-07"}


def is_wording(f):
    return (f.get("owner") != FROM_BASELINKER
            and f.get("issue") in TEXT_ISSUES
            and f.get("id") not in FEED_FED)


def collect_partial(checklist):
    out = []
    for g in checklist["groups"]:
        if g.get("path") in FULL_PAGES or g.get("key") in COVERED_BY_DOCS:
            continue
        items = [dict(f, _kind=kind_of(f))
                 for f in g["fixes"] if is_wording(f)]
        if not items:
            continue
        owners = [o for o in g.get("owners", [])
                  if any(f.get("owner") == o for f in items)]
        out.append({**g, "items": items, "owners": owners})
    return out


CSS = """
:root{--ground:#eef0f3;--surface:#fff;--sunken:#e4e7ec;--ink:#171b24;
 --muted:#626b7c;--line:#cfd5de;--hair:#dde2e9;--accent:#2b4b7d;
 --was:#a3352c;--now:#2f6b4f}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --ground:#12151b;--surface:#191d25;--sunken:#0d1015;--ink:#e6e9ef;
 --muted:#9099a8;--line:#333b47;--hair:#262d37;--accent:#8fb0e6;
 --was:#ff9089;--now:#7fc9a4}}
:root[data-theme="dark"]{--ground:#12151b;--surface:#191d25;--sunken:#0d1015;
 --ink:#e6e9ef;--muted:#9099a8;--line:#333b47;--hair:#262d37;--accent:#8fb0e6;
 --was:#ff9089;--now:#7fc9a4}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
 font:15px/1.65 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
 -webkit-font-smoothing:antialiased}
.sheet{max-width:1000px;margin:0 auto;padding:2.5rem 1.25rem 5rem}
.mast{border-bottom:2px solid var(--ink);padding-bottom:1.1rem;margin-bottom:1.5rem}
.eyebrow{margin:0 0 .5rem;font-size:.7rem;font-weight:700;letter-spacing:.16em;
 text-transform:uppercase;color:var(--accent)}
h1{margin:0 0 .4rem;font-size:clamp(1.4rem,3.2vw,2rem);font-weight:650;letter-spacing:-.015em}
.lede{margin:0;color:var(--muted);max-width:68ch}
h2.sec{margin:2.5rem 0 .3rem;font-size:1.15rem;font-weight:700}
p.secnote{margin:0 0 1.1rem;color:var(--muted);font-size:.92rem;max-width:70ch}
.toolbar{display:flex;gap:.5rem;flex-wrap:wrap;margin:1.2rem 0 0}
.btn{font:inherit;font-size:.76rem;letter-spacing:.05em;text-transform:uppercase;
 background:transparent;border:1px solid var(--line);color:var(--muted);
 padding:.4rem .75rem;cursor:pointer;white-space:nowrap}
.btn:hover{color:var(--ink);border-color:var(--muted)}
.btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.btn[aria-selected="true"]{background:var(--ink);border-color:var(--ink);color:var(--ground)}
.doc{border:1px solid var(--line);background:var(--surface);margin:0 0 .8rem}
.dochead{display:flex;gap:.7rem;align-items:center;flex-wrap:wrap;padding:.75rem .95rem;cursor:pointer}
.dochead:hover{background:var(--sunken)}
.arrow{color:var(--muted);width:1rem;flex:none;font-size:.8rem}
.dtitle{font-weight:650;font-size:.98rem}
.durl{font-family:ui-monospace,Menlo,monospace;font-size:.74rem;color:var(--accent);
 background:var(--sunken);padding:.05rem .35rem;word-break:break-all}
.dmeta{margin-left:auto;font-size:.74rem;color:var(--muted);font-variant-numeric:tabular-nums}
.tagfull{font-size:.63rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
 border:1px solid var(--now);color:var(--now);padding:.05rem .35rem}
.docbody{border-top:1px solid var(--line);padding:.85rem .95rem 1.1rem}
.tabs{display:flex;gap:.35rem;flex-wrap:wrap;margin-bottom:.6rem}
.dl{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:0 0 .9rem;
 padding-bottom:.7rem;border-bottom:1px solid var(--hair)}
.dl a{color:var(--accent);text-decoration:none;border:1px solid var(--line);
 padding:.25rem .6rem;font-family:ui-monospace,Menlo,monospace;font-size:.76rem}
.dl a:hover{border-color:var(--accent)}
.render{background:var(--ground);border:1px solid var(--hair);padding:1.3rem 1.5rem}
.render h1{font-size:1.2rem;margin:0 0 .8rem;font-weight:650}
.render h2{font-size:.96rem;margin:1.3rem 0 .5rem;font-weight:700;
 padding-bottom:.25rem;border-bottom:1px solid var(--hair)}
.render p{margin:.55rem 0;font-size:.9rem}
.render ol,.render ul{margin:.55rem 0;padding-left:1.4rem;font-size:.9rem}
.render a{color:var(--accent)}
.pane{display:none}.pane.on{display:block}
.doc.closed .docbody{display:none}
ol.items{margin:0;padding:0;list-style:none;counter-reset:it}
ol.items>li{counter-increment:it;padding:.9rem 0;border-top:1px solid var(--hair)}
ol.items>li:first-child{border-top:0}
.ihead{display:flex;gap:.5rem;align-items:baseline;flex-wrap:wrap;margin-bottom:.4rem}
.inum{font-weight:700;font-variant-numeric:tabular-nums;min-width:1.6rem}
.inum::before{content:counter(it) "."}
.ikind{font-size:.63rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
 border:1px solid var(--line);padding:.05rem .4rem;color:var(--muted)}
.k-replace{color:var(--accent);border-color:currentColor}
.k-add{color:var(--now);border-color:currentColor}
.iact{font-size:.92rem}
.swap{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);margin:.5rem 0 0}
.swap>div{background:var(--surface);padding:.5rem .7rem}
.swap b{display:block;font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;
 margin-bottom:.25rem}
.was b{color:var(--was)} .now b{color:var(--now)}
.swap pre{margin:0;font-family:ui-monospace,Menlo,monospace;font-size:.79rem;
 line-height:1.5;white-space:pre-wrap;overflow-x:auto}
.lang3{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line)}
.lang3>div{background:var(--surface);padding:.45rem .65rem;min-width:0}
.lang3 h4{margin:0 0 .25rem;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--accent);font-weight:700}
.why{margin:.35rem 0 0;font-size:.85rem;color:var(--muted)}
.verdict{margin:.7rem 0 0;padding-top:.55rem;border-top:1px dashed var(--hair)}
.vrow{display:flex;gap:.4rem;align-items:center;flex-wrap:wrap}
.vbtn{font:inherit;font-size:.73rem;letter-spacing:.05em;text-transform:uppercase;
 background:transparent;border:1px solid var(--line);color:var(--muted);
 padding:.3rem .65rem;cursor:pointer;white-space:nowrap}
.vbtn:hover{color:var(--ink);border-color:var(--muted)}
.vbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.v-ok[aria-pressed="true"]{background:var(--now);border-color:var(--now);color:#fff}
.v-no[aria-pressed="true"]{background:var(--was);border-color:var(--was);color:#fff}
.v-note[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.vstate{font-size:.76rem;color:var(--muted)}
.notes{display:grid;gap:.5rem;margin-top:.55rem}
.notes label{display:block;font-size:.66rem;letter-spacing:.09em;
 text-transform:uppercase;color:var(--accent);font-weight:700}
.notes textarea{display:block;width:100%;margin-top:.25rem;font:inherit;
 font-size:.88rem;padding:.45rem .55rem;background:var(--sunken);color:var(--ink);
 border:1px solid var(--line);resize:vertical}
.notes textarea:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
li.is-no{opacity:.45}
li.is-ok > .ihead{border-left:3px solid var(--now);padding-left:.5rem}
.answers{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;
 margin:.9rem 0 0;padding:.6rem .7rem;background:var(--sunken);
 border:1px solid var(--line)}
.answers .cnt{font-size:.8rem;color:var(--muted);font-variant-numeric:tabular-nums}
.answers .cnt b{color:var(--ink)}
#dumptext{width:100%;font:inherit;font-family:ui-monospace,Menlo,monospace;
 font-size:.8rem;padding:.5rem .6rem;background:var(--sunken);color:var(--ink);
 border:1px solid var(--line);resize:vertical}
ul.urls{margin:.9rem 0 0;padding-left:1.1rem}
ul.urls li{margin:.2rem 0}
ul.urls code{font-size:.82rem;word-break:break-all}
.owner{font-size:.62rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
 border:1px solid currentColor;padding:.05rem .4rem;white-space:nowrap}
.o-dev{color:var(--accent)} .o-content{color:var(--now)} .o-catalog{color:#8a6a1f}
:root:not([data-theme="light"]) .o-catalog{color:#e0c37a}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .o-catalog{color:#e0c37a}}
:root[data-theme="dark"] .o-catalog{color:#e0c37a}
.see{margin:.3rem 0 .1rem;font-size:.82rem;color:var(--muted)}
.see b{font-size:.62rem;letter-spacing:.09em;text-transform:uppercase;color:var(--ink)}
.see a{color:var(--accent);font-family:ui-monospace,Menlo,monospace;font-size:.76rem;
 text-decoration:none;border-bottom:1px solid var(--line);margin-right:.4rem}
.see a:hover{border-color:var(--accent)}
.fld{margin:.28rem 0;font-size:.87rem}
.fld b{font-size:.62rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);
 margin-right:.4rem}
.crop{margin:.5rem 0;border:1px solid var(--hair);background:var(--sunken)}
.crop summary{cursor:pointer;padding:.4rem .7rem;font-size:.79rem;color:var(--accent)}
.crop summary:hover{color:var(--ink)}
.crop img{display:block;width:100%;height:auto;border-top:1px solid var(--line);
 background:#fff}
.legend{display:flex;gap:.5rem;flex-wrap:wrap;margin:.8rem 0 0;font-size:.83rem;
 color:var(--muted)}
.legend div{display:flex;gap:.4rem;align-items:baseline}
#totop{position:fixed;right:1rem;bottom:1rem;z-index:30;background:var(--surface);
 box-shadow:0 1px 6px rgba(0,0,0,.18);opacity:0;pointer-events:none;transition:opacity .2s}
#totop.on{opacity:1;pointer-events:auto}
@media (max-width:700px){.lang3{grid-template-columns:1fr}.dmeta{margin-left:0}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = """
document.addEventListener('click', function (e) {
  var head = e.target.closest('.dochead');
  if (head && !e.target.closest('a')) {
    var d = head.closest('.doc');
    d.classList.toggle('closed');
    head.querySelector('.arrow').textContent = d.classList.contains('closed') ? '▸' : '▾';
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
  var own = e.target.closest('.toolbar .btn[data-own]');
  if (own) {
    [].forEach.call(document.querySelectorAll('.toolbar .btn[data-own]'), function (b) {
      b.setAttribute('aria-selected', String(b === own));
    });
    var k = own.dataset.own;
    [].forEach.call(document.querySelectorAll('ol.items > li'), function (li) {
      li.hidden = k !== 'all' && li.dataset.owner !== k;
    });
    [].forEach.call(document.querySelectorAll('.doc'), function (d) {
      var any = d.querySelector('ol.items > li:not([hidden])');
      d.hidden = !!d.querySelector('ol.items') && !any;
    });
    return;
  }
  if (e.target.closest('#theme')) {
    var r = document.documentElement;
    var dark = r.getAttribute('data-theme') === 'dark' ||
      (!r.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
    var n = dark ? 'light' : 'dark';
    r.setAttribute('data-theme', n);
    try { localStorage.setItem('lpb-theme', n); } catch (_) { }
  }
});
addEventListener('scroll', function () {
  document.getElementById('totop').classList.toggle('on', scrollY > 700);
}, { passive: true });
document.getElementById('totop').addEventListener('click', function () {
  scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
});
try { var t = localStorage.getItem('lpb-theme'); if (t) document.documentElement.setAttribute('data-theme', t); } catch (_) { }

// ---- ответы читателя -------------------------------------------------
// Held in this browser and nowhere else: the page is a static file, so there
// is no server to post to. One button turns everything typed here into a file
// to hand back — that is the whole round trip.
var KEY = 'lpb-verdicts';
var A = {};
try { A = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (_) { A = {}; }

function persist() {
  try { localStorage.setItem(KEY, JSON.stringify(A)); } catch (_) { }
  paint();
}

function entry(id) { return (A[id] = A[id] || {}); }

function answered(a) {
  return !!(a && (a.v || (a.claude || '').trim() || (a.dev || '').trim()));
}

function paint() {
  var ok = 0, no = 0, notes = 0;
  [].forEach.call(document.querySelectorAll('ol.items > li[data-id]'), function (li) {
    var a = A[li.dataset.id] || {};
    li.classList.toggle('is-ok', a.v === 'ok');
    li.classList.toggle('is-no', a.v === 'no');
    var box = li.querySelector('.verdict');
    if (!box) return;
    [].forEach.call(box.querySelectorAll('.vbtn'), function (b) {
      b.setAttribute('aria-pressed', String(
        b.dataset.v === 'note' ? !!((a.claude || '') + (a.dev || '')).trim()
          : a.v === b.dataset.v));
    });
    var s = box.querySelector('.vstate');
    var bits = [];
    if (a.v === 'ok') bits.push('согласен');
    if (a.v === 'no') bits.push('убрать');
    if ((a.claude || '').trim()) bits.push('есть комментарий мне');
    if ((a.dev || '').trim()) bits.push('есть комментарий программисту');
    s.textContent = bits.join(' · ');
    if (a.v === 'ok') ok++;
    if (a.v === 'no') no++;
    if ((a.claude || '').trim() || (a.dev || '').trim()) notes++;
  });
  var total = document.querySelectorAll('ol.items > li[data-id]').length;
  document.getElementById('cnt').innerHTML =
    'отвечено <b>' + (ok + no) + '</b> из ' + total +
    ' · согласен <b>' + ok + '</b> · убрать <b>' + no + '</b>' +
    ' · с комментарием <b>' + notes + '</b>';
}

document.addEventListener('click', function (e) {
  var b = e.target.closest('.vbtn');
  if (b) {
    var box = b.closest('.verdict'), id = box.dataset.for, a = entry(id);
    if (b.dataset.v === 'note') {
      var n = box.querySelector('.notes');
      n.hidden = !n.hidden;
      if (!n.hidden) n.querySelector('textarea').focus();
    } else {
      a.v = a.v === b.dataset.v ? '' : b.dataset.v;
      a.act = b.closest('li').dataset.act || '';
      persist();
    }
    return;
  }
  var only = e.target.closest('#onlyans');
  if (only) {
    var on = only.getAttribute('aria-pressed') !== 'true';
    only.setAttribute('aria-pressed', String(on));
    [].forEach.call(document.querySelectorAll('ol.items > li[data-id]'), function (li) {
      li.hidden = on && !answered(A[li.dataset.id]);
    });
    [].forEach.call(document.querySelectorAll('.doc'), function (d) {
      var list = d.querySelector('ol.items');
      d.hidden = !!list && !d.querySelector('ol.items > li:not([hidden])');
      if (!d.hidden && on) d.classList.remove('closed');
    });
  }
});

document.addEventListener('input', function (e) {
  var ta = e.target.closest('.notes textarea');
  if (!ta) return;
  var box = ta.closest('.verdict'), a = entry(box.dataset.for);
  a[ta.dataset.to] = ta.value;
  a.act = ta.closest('li').dataset.act || '';
  persist();
});

function collect() {
  var out = [];
  [].forEach.call(document.querySelectorAll('ol.items > li[data-id]'), function (li) {
    var a = A[li.dataset.id];
    if (!answered(a)) return;
    var page = li.closest('.doc').querySelector('.dtitle').textContent.trim();
    out.push({
      id: li.dataset.id, page: page, action: li.dataset.act || '',
      verdict: a.v === 'ok' ? 'согласен' : a.v === 'no' ? 'убрать' : '',
      dlya_claude: (a.claude || '').trim(),
      dlya_programmista: (a.dev || '').trim()
    });
  });
  return JSON.stringify({ document: 'Что менять на сайте', answers: out },
    null, 1);
}

// Copy is the whole hand-back path: a publicly shared artifact may not save
// files, so the text has to travel through the clipboard. If the clipboard is
// refused too, the textarea below is the answer that always works.
function reveal(text) {
  var box = document.getElementById('dump');
  var ta = document.getElementById('dumptext');
  ta.value = text;
  box.hidden = false;
  ta.focus();
  ta.select();
}

document.getElementById('copy').addEventListener('click', function (e) {
  var text = collect(), btn = e.target;
  function done(okFlag) {
    btn.textContent = okFlag ? 'Скопировано' : 'Не вышло — текст ниже';
    setTimeout(function () { btn.textContent = 'Скопировать мои ответы'; }, 2000);
    if (!okFlag) reveal(text);
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function () { done(true); },
      function () { done(false); });
  } else { done(false); }
});

document.getElementById('show').addEventListener('click', function () {
  var box = document.getElementById('dump');
  if (!box.hidden) { box.hidden = true; return; }
  reveal(collect());
});

// Restore what was typed before, then draw the counters.
[].forEach.call(document.querySelectorAll('.verdict'), function (box) {
  var a = A[box.dataset.for];
  if (!a) return;
  [].forEach.call(box.querySelectorAll('textarea'), function (ta) {
    if (a[ta.dataset.to]) ta.value = a[ta.dataset.to];
  });
  if ((a.claude || '').trim() || (a.dev || '').trim())
    box.querySelector('.notes').hidden = false;
});
paint();
"""


def kb(n):
    return f"{max(1, round(n / 1024))} КБ"


def full_block(p, i):
    tabs, panes = [], []
    for code, label in LANGS:
        d = p["langs"].get(code)
        if not d:
            continue
        first = code == "pl"
        tabs.append(f'<button class="btn" type="button" data-lang="{code}" '
                    f'aria-selected="{str(first).lower()}">{label}</button>')
        panes.append(f"""
<div class="pane{' on' if first else ''}" data-lang="{code}">
  <div class="dl">
    <a href="{d['docx']}" download="{d['file']}.docx">{d['file']}.docx · {kb(d['docx_size'])}</a>
    <a href="{d['html']}" download="{d['file']}.html">{d['file']}.html · {kb(d['html_size'])}</a>
  </div>
  <div class="render">{d['body']}</div>
</div>""")
    ui = ""
    if p["ui"]:
        ui = ('<p class="why"><b>Отдельно:</b> ' + esc(p["ui_title"]) +
              ' — это не идёт на страницу, тексты вставляются в чекаут, '
              'регистрацию и настройки cookie-баннера. Файлы в архиве, папка '
              f'<code>{esc(p["slug"])}-ui</code>.</p>')
    return f"""
<section class="doc{' closed' if i else ''}">
  <header class="dochead">
    <span class="arrow">{'▸' if i else '▾'}</span>
    <span class="dtitle">{esc(p['title'])}</span>
    <code class="durl">{esc(p['urls'].get('pl','').replace('https://',''))}</code>
    <span class="tagfull">заменить целиком</span>
    <span class="dmeta">3 языка · 6 файлов</span>
  </header>
  <div class="docbody">
    <p class="why">Содержимое страницы заменяется полностью — всё, что стоит
      там сейчас, уходит вместе с заменой. Адрес не меняется.</p>
    {ui}
    <div class="tabs">{''.join(tabs)}</div>
    {''.join(panes)}
  </div>
</section>"""


def item_block(f):
    k = f["_kind"]
    label, _ = KIND[k]
    langs = [(c, l, f.get(c)) for c, l in LANGS if f.get(c)]
    lang_html = ""
    if langs:
        lang_html = ('<div class="lang3">' + "".join(
            f'<div><h4>{esc(l)}</h4><pre>{esc(t)}</pre></div>'
            for _, l, t in langs) + "</div>")
    swap = ""
    if k == "replace":
        swap = (f'<div class="swap"><div class="was"><b>Было на странице</b>'
                f'<pre>{esc(f["current"])[:1200]}</pre></div>'
                f'<div class="now"><b>Стало</b>{lang_html}</div></div>')
    elif k == "add":
        swap = f'<div class="swap"><div class="now"><b>Добавить</b>{lang_html}</div></div>'
    owner = f.get("owner", "dev")
    badge = (f'<span class="owner {OWNER_STYLE[owner]}">'
             f'{esc(f.get("owner_label",""))}</span>')
    see = f.get("see_values") or f.get("see") or []
    see_html = ""
    if see:
        see_html = ('<p class="see"><b>Где посмотреть</b> ' + " ".join(
            f'<a href="{esc(u)}" target="_blank" rel="noopener">'
            f'{esc(u.replace("https://lapetitebloom.com", "") or "/")}</a>'
            for u in see[:4]) + "</p>")
    place = f.get("title") or ""
    crop = ""
    if f.get("crop"):
        crop = (f'<details class="crop"><summary>Показать это место на странице'
                f'</summary><img loading="lazy" src="{f["crop"]}" '
                f'alt="Место правки {esc(f["id"])}"></details>')
    return f"""
<li data-owner="{esc(owner)}" data-id="{esc(f['id'])}"
    data-act="{esc(f.get('action') or place)}">
  <div class="ihead"><span class="inum"></span>
    {badge}
    <span class="ikind k-{k}">{esc(label)}</span>
    <span class="iact">{esc(f.get('action') or place)}</span></div>
  {f'<p class="fld"><b>Где</b> {esc(place)}</p>' if place else ''}
  {see_html}
  {f'<p class="fld"><b>Почему</b> {esc(f.get("why"))}</p>' if f.get('why') else ''}
  {crop}
  {swap}
  {verdict_block(f['id'])}
</li>"""


def verdict_block(fid):
    """Two buttons and two comment boxes on every fix.

    The client reads this list and needs to answer back: keep it, or throw it
    out — and sometimes say why, separately to me and to the developer. The
    answers live in the reader's own browser and leave it only when they press
    «Выгрузить ответы», which writes one file to hand back.
    """
    return f"""
<div class="verdict" data-for="{esc(fid)}">
  <div class="vrow">
    <button class="vbtn v-ok" type="button" data-v="ok">Согласен</button>
    <button class="vbtn v-no" type="button" data-v="no">Удалить лишнее</button>
    <button class="vbtn v-note" type="button" data-v="note">Комментарий</button>
    <span class="vstate"></span>
  </div>
  <div class="notes" hidden>
    <label>Мне (Claude)<textarea rows="2" data-to="claude"
      placeholder="Что переписать, что уточнить, что не так"></textarea></label>
    <label>Программисту<textarea rows="2" data-to="dev"
      placeholder="Пояснение для того, кто будет править"></textarea></label>
  </div>
</div>"""


def partial_block(g):
    counts = {}
    for f in g["items"]:
        counts[f["_kind"]] = counts.get(f["_kind"], 0) + 1
    meta = " · ".join(f"{KIND[k][0].lower()}: {n}" for k, n in counts.items())
    url = g.get("url_label", "")
    owners = "".join(f'<span class="owner {OWNER_STYLE[o]}">'
                     f'{esc(dict(d for d in OWNER_NAMES)[o])}</span>'
                     for o in g.get("owners", []))
    shot = ""
    return f"""
<section class="doc closed" data-owners="{esc(' '.join(g.get('owners', [])))}">
  <header class="dochead">
    <span class="arrow">▸</span>
    <span class="dtitle">{esc(g['title'])}</span>
    {f'<code class="durl">{esc(url)}</code>' if url else ''}
    {owners}
    <span class="dmeta">{g['count']} правок · {meta}</span>
  </header>
  <div class="docbody">
    {f'<p class="why">{esc(g["desc"])}</p>' if g.get('desc') else ''}
    {shot}
    <ol class="items">{''.join(item_block(f) for f in g['items'])}</ol>
  </div>
</section>"""


def unpublish_block():
    rows = "".join(f"<li><code>{esc(u)}</code></li>" for u in UNPUBLISH)
    return f"""
<section class="doc closed" data-owners="dev">
  <header class="dochead">
    <span class="arrow">▸</span>
    <span class="dtitle">Снять с публикации — старые страницы возвратов</span>
    <span class="owner o-dev">Программисты</span>
    <span class="dmeta">{len(UNPUBLISH)} адресов</span>
  </header>
  <div class="docbody">
    <p class="why">На этих страницах стоит французское потребительское право
      (L.221-18, L.221-24, Code civil 1641–1649) — текст скопирован у другого
      бренда и к польскому магазину отношения не имеет. Заменять его не нужно:
      всё, что должно там быть, уже лежит в готовых документах «Политика
      возвратов и рекламаций» и «Регламент магазина». Страницы убираются
      и вычёркиваются из sitemap. Редиректы не нужны — сайт закрыт от
      индексации.</p>
    <ul class="urls">{rows}</ul>
  </div>
</section>"""


def decided_block():
    items = "".join(f"""
<li data-owner="content">
  <div class="ihead"><span class="inum"></span>
    <span class="owner o-content">Наш контент</span>
    <span class="ikind k-replace">Решено</span>
    <span class="iact">{esc(what)}</span></div>
  <p class="fld"><b>Почему спрашивали</b> {esc(why)}</p>
  <p class="fld"><b>Где в тексте</b> {esc(where)}</p>
</li>""" for what, why, where in DECIDED)
    return f"""
<section class="doc" data-owners="content">
  <header class="dochead">
    <span class="arrow">▸</span>
    <span class="dtitle">Решения, которые уже внесены в файлы</span>
    <span class="owner o-content">Наш контент</span>
    <span class="dmeta">{len(DECIDED)} решений</span>
  </header>
  <div class="docbody">
    <p class="why">Эти вопросы готовый текст решить не мог — суммы, даты,
      перевозчик, адреса. Решения приняты и уже стоят в файлах из первой
      части; здесь они записаны, чтобы через месяц не выяснять заново,
      о чём договорились.</p>
    <ol class="items">{items}</ol>
  </div>
</section>"""


def main():
    cl_path, tr_path, pages_dir, out_path = sys.argv[1:5]
    checklist = json.load(open(cl_path, encoding="utf-8"))
    tr = json.load(open(tr_path, encoding="utf-8"))

    full = collect_full(pages_dir, tr)
    partial, n_crops = attach_crops(collect_partial(checklist),
                                    os.environ.get("CROPS_DIR", ""))
    n_items = sum(len(g["items"]) for g in partial)

    doc = f"""<title>La Petite Bloom — что менять на сайте</title>
<style>{CSS}</style>
<div class="sheet">
  <header class="mast">
    <p class="eyebrow">Рабочий документ · lapetitebloom.com</p>
    <h1>Что менять на сайте</h1>
    <p class="lede">Только текст: опечатки, кривой перевод, непереведённые
      куски, чужой язык на странице, заглушки и расхождения с вашими
      документами. Две части. Там, где есть ваш документ, страница заменяется
      целиком — берёте файл и вставляете. Там, где документа нет, меняются
      отдельные абзацы, и на каждый показано что стоит сейчас и что должно
      стать, на трёх языках. Адреса страниц не меняются.</p>
    <p class="lede" style="margin-top:.5rem">Сюда не вошло то, что тянется
      из BaseLinker: значения атрибутов, фильтры и тексты товаров. Править их
      на сайте бесполезно — следующая выгрузка перезапишет. Обязательные
      юридические абзацы тоже вынесены отдельно: это не вычитка, а написание
      нового текста.</p>
    <div class="toolbar">
      <button class="btn" data-own="all" aria-selected="true">Все правки</button>
      <button class="btn" data-own="dev" aria-selected="false">Программистам</button>
      <button class="btn" data-own="content" aria-selected="false">Наш контент</button>
      <button class="btn" id="theme" type="button">Тема</button>
    </div>
    <div class="answers">
      <button class="btn" id="copy" type="button">Скопировать мои ответы</button>
      <button class="btn" id="show" type="button">Показать текстом</button>
      <button class="btn" id="onlyans" type="button" aria-pressed="false">
        Показать только отвеченные</button>
      <span class="cnt" id="cnt"></span>
    </div>
    <div id="dump" hidden>
      <p class="secnote" style="margin:.6rem 0 .3rem">Выделите всё и вставьте
        мне в чат — я разберу и перепишу список.</p>
      <textarea id="dumptext" rows="12" readonly></textarea>
    </div>
    <p class="secnote" style="margin:.5rem 0 0">На каждой правке две кнопки и
      два поля для комментария — мне и программисту. Ответы держатся в этом
      браузере, никуда сами не уходят; чтобы я их прочитал, нажмите
      «Скопировать мои ответы» и вставьте в чат.</p>
    <div class="legend">
      <div><span class="owner o-dev">Программисты</span> шаблон, ссылки, строки движка</div>
      <div><span class="owner o-content">Наш контент</span> меню, акции, баннеры — пишем сами</div>
    </div>
  </header>

  <h2 class="sec">1. Заменить целиком — {len(full)} страниц</h2>
  <p class="secnote">Содержимое страницы меняется полностью: старый текст уходит
    вместе с заменой, отдельно ничего удалять не нужно. Файл
    <code>.docx</code> — читать и согласовывать, <code>.html</code> — вставлять
    в редактор страницы.</p>
  {''.join(full_block(p, i) for i, p in enumerate(full))}

  <h2 class="sec">2. Снять с публикации</h2>
  <p class="secnote">Страницы, которые не правятся, а убираются: их содержимое
    перекрыто готовыми документами из первой части.</p>
  {unpublish_block()}

  <h2 class="sec">3. Поменять по абзацам — {len(partial)} страниц, {n_items} правок</h2>
  <p class="secnote">Здесь готового документа нет, поэтому меняется не вся
    страница, а отдельные места. У каждой правки свой номер: слева то, что
    стоит на странице сейчас, справа то, что должно стать, на трёх языках.
    Страницы из первой части сюда не попадают — их правки уже внесены
    в готовый текст.</p>
  {''.join(partial_block(g) for g in partial)}

  <h2 class="sec">4. Что решили — {len(DECIDED)} решений</h2>
  <p class="secnote">Не задание, а запись: что было спорным и как решили.
    В файлы первой части это уже внесено.</p>
  {decided_block()}
</div>
<button class="btn" id="totop" type="button">↑ Наверх</button>
<script>{JS}</script>"""

    open(out_path, "w", encoding="utf-8").write(doc)
    size = len(doc.encode("utf-8")) / 1024 / 1024
    print(f"{out_path}  {size:.2f} МБ")
    print(f"  вырезок с местом ошибки: {n_crops}")
    print(f"  заменить целиком: {len(full)} страниц")
    print(f"  по абзацам: {len(partial)} страниц, {n_items} правок")
    kinds = {}
    for g in partial:
        for f in g["items"]:
            kinds[f["_kind"]] = kinds.get(f["_kind"], 0) + 1
    for k, n in kinds.items():
        print(f"     {KIND[k][0]}: {n}")


if __name__ == "__main__":
    main()
