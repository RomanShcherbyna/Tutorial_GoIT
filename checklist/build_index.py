#!/usr/bin/env python3
"""The readable hand-over: one page per page.

Not a defect list — a work order. For each page on the site it says which
address it lives at in all three languages, which files carry its final text,
what has to come off the page, and what still needs an answer from the client.

Usage:  python3 build_index.py <translations.json> <doc_tasks.json> <pages_dir> <out.html>
"""
import html
import json
import os
import re
import sys

LOCALES = (("pl", "Polski"), ("ua", "Українська"), ("en", "English"))

# Pages that must come off the site: no source document, nothing links to them.
UNPUBLISH = {
    "title": "Снять с публикации",
    "pages": ["/warranty-and-returns",
              "/warranty-and-returns/polityka-zwrotow",
              "/warranty-and-returns/gwarancja-na-produkt"],
    "why": ("Документа у этих страниц нет, подвал на них не ссылается, а текст — "
            "французское потребительское право (art. L217-3, Kodeks Cywilny "
            "1641–1649) и чужой бренд «Bloom» с его аутлетами. Всё нужное уже "
            "есть на странице возвратов."),
    "how": ("Во всех трёх локалях это 9 адресов. Их также надо убрать из карты "
            "сайта, иначе sitemap.xml будет отдавать 404. Редиректы не нужны: "
            "сайт закрыт от индексации, поисковой истории у страниц нет."),
}

OPEN_QUESTIONS = [
    ("Наложенный платёж", "В документе вилка «+20–23 zł». Покупателю нужна одна "
     "сумма или правило расчёта.", "/delivery-and-payment"),
    ("Порог бесплатной доставки", "500 zł считается до или после скидки?",
     "/delivery-and-payment"),
    ("Заграничная доставка", "В тексте DHL, отдельно упомянуты Nova Poshta и "
     "Meest для Украины — так и оставляем?", "/delivery-and-payment"),
    ("Дата вступления в силу", "У документа о доставке её нет, у остальных семи — "
     "24.06.2026.", "/delivery-and-payment"),
    ("Номер отдела суда", "В реквизитах KRS не заполнен Wydział Gospodarczy — "
     "XIII или XIV.", "/terms-of-use"),
    ("Адрес бутика", "В документе «ul. Mokotowska 51/53, Warszawa», без номера "
     "помещения и индекса. Для адреса возврата это существенно.",
     "/claims-and-complaints"),
    ("Ошибка в польском оригинале", "«Zgody muszą być dobrowolne, NIE odznaczone "
     "domyślnie» читается как «предвыбранные» — противоположное смыслу и GDPR. "
     "Должно быть «NIE zaznaczone». Правится в исходном документе.",
     "/zgody-klauzule-i-regulamin-newslettera"),
    ("Почта в исходных .docx", "Решение — hello@ и rodo@. В готовых текстах "
     "заменено, в самих .docx остаётся kontakt@: 11 мест в шести документах.", ""),
]


def esc(s):
    return html.escape(str(s or ""))


def page_tasks(tasks, path):
    """What has to come off this page, worst first, without the small stuff."""
    order = {"blocker": 0, "high": 1}
    out = []
    for t in tasks:
        p = (t.get("path") or "").split(",")[0].strip()
        p = re.sub(r"\s+\(.*$", "", p)
        p = re.sub(r"^/(ua|en)(?=/)", "", p)
        if p.rstrip("/") != path.rstrip("/"):
            continue
        if t.get("severity") not in order:
            continue
        out.append(t)
    return sorted(out, key=lambda t: order.get(t["severity"], 9))


CSS = """
:root{--ground:#eef0f3;--surface:#fff;--sunken:#e4e7ec;--ink:#171b24;
 --muted:#626b7c;--line:#cfd5de;--hair:#dde2e9;--accent:#2b4b7d;--warn:#b3261e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --ground:#12151b;--surface:#191d25;--sunken:#0d1015;--ink:#e6e9ef;
 --muted:#9099a8;--line:#333b47;--hair:#262d37;--accent:#8fb0e6;--warn:#ff9089}}
:root[data-theme="dark"]{--ground:#12151b;--surface:#191d25;--sunken:#0d1015;
 --ink:#e6e9ef;--muted:#9099a8;--line:#333b47;--hair:#262d37;--accent:#8fb0e6;--warn:#ff9089}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
 font:15px/1.65 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.sheet{max-width:900px;margin:0 auto;padding:2.5rem 1.25rem 5rem}
h1{margin:0 0 .4rem;font-size:clamp(1.4rem,3.2vw,2rem);font-weight:650;letter-spacing:-.015em}
.lede{margin:0 0 1.6rem;color:var(--muted);max-width:64ch}
.eyebrow{margin:0 0 .5rem;font-size:.7rem;font-weight:700;letter-spacing:.16em;
 text-transform:uppercase;color:var(--accent)}
.mast{border-bottom:2px solid var(--ink);padding-bottom:1.1rem;margin-bottom:2rem}
.page{background:var(--surface);border:1px solid var(--line);margin:0 0 1.5rem;
 padding:1.1rem 1.2rem}
.page h2{margin:0 0 .2rem;font-size:1.05rem;font-weight:700}
.addr{margin:.5rem 0 1rem;display:grid;gap:1px;background:var(--line);border:1px solid var(--line)}
.addr div{background:var(--surface);padding:.4rem .6rem;display:flex;gap:.7rem;
 align-items:baseline;font-size:.86rem}
.addr b{font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);
 min-width:2.2rem}
.addr code{font-family:ui-monospace,Menlo,monospace;font-size:.82rem;word-break:break-all}
h3{margin:1.1rem 0 .4rem;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;
 color:var(--muted);font-weight:700}
.files{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1px;
 background:var(--line);border:1px solid var(--line)}
.files div{background:var(--surface);padding:.45rem .6rem;font-size:.82rem;
 font-family:ui-monospace,Menlo,monospace}
ol.rm{margin:.3rem 0;padding-left:1.3rem;font-size:.9rem}
ol.rm li{margin-bottom:.35rem}
.q{margin:.3rem 0 0;padding-left:.8rem;border-left:2px solid var(--warn);font-size:.88rem;
 color:var(--muted)}
.warn{background:var(--surface);border:1px solid var(--warn);padding:1.1rem 1.2rem;margin:0 0 1.5rem}
.warn h2{color:var(--warn)}
.warn code{font-family:ui-monospace,Menlo,monospace;font-size:.82rem}
table{border-collapse:collapse;width:100%;font-size:.88rem;margin:.5rem 0 2rem}
th,td{text-align:left;padding:.45rem .7rem;border-bottom:1px solid var(--hair);vertical-align:top}
th{font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
td code{font-family:ui-monospace,Menlo,monospace;font-size:.8rem}
"""


def main():
    tr_path, tasks_path, pages_dir, out_path = sys.argv[1:5]
    tr = json.load(open(tr_path, encoding="utf-8"))
    tasks = json.load(open(tasks_path, encoding="utf-8"))

    rows, blocks = [], []
    for doc in tr["documents"]:
        page = doc.get("page") or {}
        if not page:
            continue
        slug = page["pl"].rstrip("/").split("/")[-1]
        path = "/" + slug
        rm = page_tasks(tasks, path)
        rows.append(f"<tr><td><code>{esc(path)}</code></td><td>{esc(doc['title'])}</td>"
                    f"<td>{len(doc['blocks'])} блоков</td><td>{len(rm)}</td></tr>")

        addr = "".join(
            f'<div><b>{code.upper()}</b><code>{esc(page[code].replace("https://",""))}</code></div>'
            for code, _ in LOCALES)
        files = "".join(
            f"<div>{esc(slug)}.{code}.docx<br>{esc(slug)}.{code}.html</div>"
            for code, _ in LOCALES)
        rm_html = ("<ol class='rm'>" + "".join(
            f"<li>{esc(t.get('title',''))}</li>" for t in rm) + "</ol>"
            if rm else "<p class='q'>Ничего лишнего не найдено — текст просто заменяется.</p>")
        qs = [q for q in OPEN_QUESTIONS if q[2] == path]
        q_html = "".join(f"<p class='q'><b>{esc(t)}.</b> {esc(d)}</p>" for t, d, _ in qs)

        blocks.append(f"""
<section class="page">
  <h2>{esc(doc['title'])}</h2>
  <div class="addr">{addr}</div>
  <h3>Файлы — .docx читать, .html вставлять</h3>
  <div class="files">{files}</div>
  <h3>Что убрать с текущей страницы</h3>
  {rm_html}
  {('<h3>Нужен ваш ответ</h3>' + q_html) if q_html else ''}
</section>""")

    general = "".join(
        f"<p class='q'><b>{esc(t)}.</b> {esc(d)}</p>"
        for t, d, p in OPEN_QUESTIONS if not p)

    doc_html = f"""<title>La Petite Bloom — что вставить на страницы</title>
<style>{CSS}</style>
<div class="sheet">
  <header class="mast">
    <p class="eyebrow">Рабочий документ · lapetitebloom.com</p>
    <h1>Что вставить на страницы</h1>
    <p class="lede">{len(blocks)} страниц, у каждой готовый текст на трёх языках.
      Адреса остаются прежними — ничего не создаётся и не переносится.
      Файлы <code>.docx</code> для чтения и согласования, <code>.html</code> —
      чтобы вставить в редактор страницы как есть.</p>
  </header>

  <table>
    <thead><tr><th>Страница</th><th>Документ</th><th>Объём</th><th>Убрать</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>

  <section class="warn">
    <h2>{esc(UNPUBLISH['title'])}</h2>
    <p>{''.join(f'<code>{esc(p)}</code> ' for p in UNPUBLISH['pages'])}</p>
    <p>{esc(UNPUBLISH['why'])}</p>
    <p>{esc(UNPUBLISH['how'])}</p>
  </section>

  {''.join(blocks)}

  <section class="page">
    <h2>Общие вопросы</h2>
    {general}
  </section>
</div>"""

    open(out_path, "w", encoding="utf-8").write(doc_html)
    print(f"{out_path}  {len(doc_html)/1024:.0f} КБ  страниц: {len(blocks)}")


if __name__ == "__main__":
    main()
