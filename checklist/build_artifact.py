#!/usr/bin/env python3
"""Build the shareable, single-file version of the checklist.

Same content as the server version, but with nothing behind it: the data is
embedded, the documents ride along as data: URIs, and ticks live in the
reader's own browser. That makes it a link anyone can open without a deploy —
at the cost of shared state, which is what the Railway build is for.

Usage:  python3 build_artifact.py <checklist.json> <translations.json> <docs_dir> <out.html>
"""
import base64
import glob
import json
import mimetypes
import os
import sys

DOCX = ("application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document")


def embed_documents(docs_dir):
    """Search below the given folder, not only in it.

    The originals live in documents/originals, so a flat glob over "documents"
    matched nothing and the artifact shipped without a single file — silently,
    because zero documents is a perfectly valid-looking number."""
    out = []
    found = glob.glob(os.path.join(docs_dir, "*.docx"))
    if not found:
        found = glob.glob(os.path.join(docs_dir, "**", "*.docx"), recursive=True)
    if not found:
        print(f"!! в {docs_dir} не найдено ни одного .docx")
    for path in sorted(found):
        raw = open(path, "rb").read()
        mime = mimetypes.guess_type(path)[0] or DOCX
        out.append({
            "name": os.path.basename(path),
            "size": len(raw),
            "href": f"data:{mime};base64," + base64.b64encode(raw).decode(),
        })
    return out


CSS = """
:root{
  --ground:#eef0f3; --surface:#fff; --sunken:#e4e7ec; --ink:#171b24;
  --muted:#626b7c; --line:#cfd5de; --hair:#dde2e9; --accent:#2b4b7d;
  --blocker:#b3261e; --high:#a35b12; --medium:#6f6a2e; --low:#3f6b57;
  --done:#2f6b4f; --doing:#8a6a1f;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ground:#12151b; --surface:#191d25; --sunken:#0d1015; --ink:#e6e9ef;
  --muted:#9099a8; --line:#333b47; --hair:#262d37; --accent:#8fb0e6;
  --blocker:#ff9089; --high:#f0b072; --medium:#d6cf8b; --low:#93c4ab;
  --done:#7fc9a4; --doing:#e0c37a;}}
:root[data-theme="dark"]{
  --ground:#12151b; --surface:#191d25; --sunken:#0d1015; --ink:#e6e9ef;
  --muted:#9099a8; --line:#333b47; --hair:#262d37; --accent:#8fb0e6;
  --blocker:#ff9089; --high:#f0b072; --medium:#d6cf8b; --low:#93c4ab;
  --done:#7fc9a4; --doing:#e0c37a;}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font:15px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.sheet{max-width:1180px;margin:0 auto;padding:2.5rem 1.25rem 6rem}
.mast{border-bottom:2px solid var(--ink);padding-bottom:1.1rem}
.eyebrow{margin:0 0 .5rem;font-size:.7rem;font-weight:700;letter-spacing:.16em;
  text-transform:uppercase;color:var(--accent)}
h1{margin:0 0 .4rem;font-size:clamp(1.4rem,3.2vw,2rem);font-weight:650;
  letter-spacing:-.015em;text-wrap:balance}
.lede{margin:0;color:var(--muted);max-width:68ch}
.bar{height:8px;background:var(--sunken);border:1px solid var(--line);
  overflow:hidden;margin-top:1.3rem}
.bar i{display:block;height:100%;background:var(--done);width:0;transition:width .3s}
.pstat{display:flex;flex-wrap:wrap;gap:.4rem 1.1rem;margin-top:.5rem;
  font-size:.82rem;color:var(--muted);font-variant-numeric:tabular-nums}
.pstat b{color:var(--ink)}
.tabs{display:flex;gap:.35rem;margin:1.5rem 0 0;flex-wrap:wrap}
.tabs button{font:inherit;font-size:.8rem;letter-spacing:.04em;
  text-transform:uppercase;background:transparent;border:1px solid var(--line);
  color:var(--muted);padding:.45rem .85rem;cursor:pointer}
.tabs button[aria-selected="true"]{background:var(--ink);border-color:var(--ink);
  color:var(--ground)}
.toolbar{position:sticky;top:0;z-index:20;background:var(--ground);
  padding:.85rem 0 .7rem;border-bottom:1px solid var(--line);margin-bottom:1.3rem}
.row{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
input[type=search]{font:inherit;font-size:.95rem;padding:.5rem .7rem;flex:1 1 16rem;
  background:var(--surface);color:var(--ink);border:1px solid var(--line);min-width:0}
input:focus-visible,button:focus-visible,select:focus-visible{
  outline:2px solid var(--accent);outline-offset:1px}
.chip{font:inherit;font-size:.75rem;letter-spacing:.05em;text-transform:uppercase;
  background:transparent;border:1px solid var(--line);color:var(--muted);
  padding:.35rem .7rem;cursor:pointer;white-space:nowrap}
.chip:hover{color:var(--ink);border-color:var(--muted)}
.chip[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--ground)}
.chip i{font-style:normal;opacity:.6;font-variant-numeric:tabular-nums}
.chips{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.55rem}
.grp{margin:0 0 .6rem;border:1px solid var(--line);background:var(--surface)}
.grp[hidden]{display:none}
.grphead{display:flex;align-items:center;gap:.6rem;padding:.7rem .85rem;flex-wrap:wrap}
.toggle{flex:1 1 auto;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;
  background:transparent;border:0;color:var(--ink);font:inherit;cursor:pointer;
  text-align:left;padding:0;min-width:0}
.tw-arrow{color:var(--muted);font-size:.8rem;width:1rem;flex:none}
.gtitle{font-weight:650;font-size:.98rem}
.gcount{font-size:.76rem;color:var(--muted);font-variant-numeric:tabular-nums;
  white-space:nowrap}
.badge{font-size:.66rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  border:1px solid currentColor;padding:.05rem .35rem;white-space:nowrap}
.b-blocker{color:var(--blocker)} .b-doc{color:var(--accent)}
.ghead-right{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap}
.gdesc{margin:0 .85rem .5rem 2.5rem;font-size:.84rem;color:var(--muted)}
select.st{font:inherit;font-size:.78rem;padding:.28rem .4rem;background:var(--surface);
  color:var(--ink);border:1px solid var(--line)}
.grp.is-done{opacity:.62;border-left:3px solid var(--done)}
.grp.is-done .grphead{background:var(--sunken)}
.grp.is-skip{opacity:.45}
.grp.is-doing{border-left:3px solid var(--doing)}
.fixes{border-top:1px solid var(--line);padding:0 .85rem}
.fix{padding:1rem 0;border-top:1px solid var(--hair)}
.fix:first-child{border-top:0}
.fix[hidden]{display:none}
.fix.is-done{opacity:.5}
.fixhead{display:flex;flex-wrap:wrap;gap:.45rem;align-items:center;margin-bottom:.4rem}
.mark{font-size:.63rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
  border-left:2px solid currentColor;padding-left:.4rem}
.s-blocker .mark{color:var(--blocker)} .s-high .mark{color:var(--high)}
.s-medium .mark{color:var(--medium)} .s-low .mark{color:var(--low)}
.kind{font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.loc{font-size:.63rem;font-weight:700;color:var(--muted);border:1px solid var(--line);
  padding:.05rem .35rem}
.fid{font-size:.68rem;color:var(--muted);font-family:ui-monospace,Menlo,monospace;
  margin-left:auto}
.action{margin:.1rem 0 .45rem;font-size:.95rem;font-weight:550}
.num{font-size:.8rem;font-weight:700;color:var(--muted);
  font-variant-numeric:tabular-nums;min-width:1.4rem}
.gurl{font-family:ui-monospace,Menlo,monospace;font-size:.76rem;color:var(--accent);
  background:var(--sunken);padding:.05rem .35rem;word-break:break-all}
.gdocs{margin:.7rem 0 .2rem;font-size:.85rem;color:var(--muted)}
.gdocs b{color:var(--ink);font-size:.68rem;letter-spacing:.08em;text-transform:uppercase}
.gsub{margin:.6rem 0 0;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);font-weight:700}
.ftitle{margin:.1rem 0 .4rem;font-size:.93rem}
.links{display:flex;gap:.3rem;flex-wrap:wrap}
.links a{font-size:.7rem;font-family:ui-monospace,Menlo,monospace;color:var(--accent);
  text-decoration:none;border:1px solid var(--line);padding:.05rem .35rem}
.links a:hover{border-color:var(--accent)}
.where{margin:.15rem 0 .45rem;font-size:.85rem;color:var(--muted)}
.where b{color:var(--ink);font-size:.66rem;letter-spacing:.09em;text-transform:uppercase}
.evidence{margin:.45rem 0;padding:.5rem .75rem;background:var(--sunken);
  border-left:2px solid var(--line);font-family:ui-monospace,Menlo,monospace;
  font-size:.79rem;white-space:pre-wrap;overflow-x:auto;max-height:14em}
.why{margin:.45rem 0;font-size:.88rem;color:var(--muted)}
.steps{margin:.45rem 0;padding-left:1.2rem;font-size:.88rem}
.note{margin:.5rem 0 0;font-size:.85rem;color:var(--muted);padding-left:.7rem;
  border-left:2px solid var(--hair)}
.lanes{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);
  border:1px solid var(--line);margin-top:.6rem}
.lanes.one{grid-template-columns:1fr}
.lane{background:var(--surface);padding:.5rem .7rem;min-width:0}
.lane h4{margin:0 0 .3rem;font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--accent);font-weight:700;display:flex;justify-content:space-between;
  align-items:center;gap:.4rem}
.lane pre{margin:0;font-family:ui-monospace,Menlo,monospace;font-size:.79rem;
  line-height:1.5;white-space:pre-wrap;overflow-x:auto}
.copy{font:inherit;font-size:.6rem;letter-spacing:.06em;text-transform:uppercase;
  background:transparent;border:1px solid var(--line);color:var(--muted);
  padding:.1rem .35rem;cursor:pointer}
.copy:hover{color:var(--ink)}
.excluded{margin:1.4rem 0 0;padding:.7rem .85rem;background:var(--sunken);
  border:1px dashed var(--line);font-size:.85rem;color:var(--muted)}
.hint{margin:1rem 0 0;padding:.7rem .85rem;background:var(--surface);
  border:1px solid var(--line);font-size:.87rem;color:var(--muted)}
.hint b{color:var(--ink)}
.docs{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  margin-top:1rem}
.docs a{background:var(--surface);padding:.6rem .8rem;font-size:.9rem;color:var(--ink);
  text-decoration:none;display:flex;justify-content:space-between;gap:1rem}
.docs a:hover{background:var(--sunken)}
.docs .sz{color:var(--muted);font-size:.8rem;font-variant-numeric:tabular-nums}
.doc{margin:0 0 .6rem;border:1px solid var(--line);background:var(--surface)}
.docblocks{border-top:1px solid var(--line);padding:0 .85rem}
.blk{padding:.8rem 0;border-top:1px solid var(--hair)}
.blk:first-child{border-top:0}
.blk .n{font-size:.66rem;color:var(--muted);font-family:ui-monospace,Menlo,monospace}
.panel{display:none}
.panel.on{display:block}
#totop{position:fixed;right:1rem;bottom:1rem;z-index:30;background:var(--surface);
  box-shadow:0 1px 6px rgba(0,0,0,.18);opacity:0;pointer-events:none;transition:opacity .2s}
#totop.on{opacity:1;pointer-events:auto}
.verdict{margin:.7rem 0 0;padding-top:.55rem;border-top:1px dashed var(--hair)}
.vrow{display:flex;gap:.4rem;align-items:center;flex-wrap:wrap}
.vbtn{font:inherit;font-size:.73rem;letter-spacing:.05em;text-transform:uppercase;
  background:transparent;border:1px solid var(--line);color:var(--muted);
  padding:.3rem .65rem;cursor:pointer;white-space:nowrap}
.vbtn:hover{color:var(--ink);border-color:var(--muted)}
.vbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.v-ok[aria-pressed="true"]{background:var(--done);border-color:var(--done);color:#fff}
.v-no[aria-pressed="true"]{background:var(--blocker);border-color:var(--blocker);color:#fff}
.vstate{font-size:.76rem;color:var(--muted)}
.notes{display:grid;gap:.5rem;margin-top:.55rem}
.notes label{display:block;font-size:.66rem;letter-spacing:.09em;
  text-transform:uppercase;color:var(--accent);font-weight:700}
.notes textarea{display:block;width:100%;margin-top:.25rem;font:inherit;
  font-size:.88rem;padding:.45rem .55rem;background:var(--sunken);color:var(--ink);
  border:1px solid var(--line);resize:vertical}
.notes textarea:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
@media (max-width:800px){.lanes{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""


def main():
    checklist_path, tr_path, docs_dir, out_path = sys.argv[1:5]
    checklist = json.load(open(checklist_path, encoding="utf-8"))
    translations = json.load(open(tr_path, encoding="utf-8"))
    documents = embed_documents(docs_dir)

    # The eight pages the client's documents replace whole are dropped here for
    # the same reason they are dropped from the work order: the audit found
    # them before the documents existed, so every one of those fixes is already
    # carried out by the replacement text. Listing them again reads as work
    # still to do. Same for the returns pages, which come down rather than
    # get edited.
    from build_workorder import COVERED_BY_DOCS, FULL_PAGES
    before = checklist["total_fixes"]
    checklist["groups"] = [g for g in checklist["groups"]
                           if g.get("key") not in COVERED_BY_DOCS
                           and g.get("path") not in FULL_PAGES]
    # Правки, которые правятся не на сайте, а в BaseLinker: значения атрибутов,
    # фильтры, тексты товаров. Ими занимается отдельный документ, и держать их
    # здесь — значит показывать одну работу в двух местах.
    from_bl = 0
    for g in checklist["groups"]:
        keep = [f for f in g["fixes"] if f.get("owner") != "catalog"]
        from_bl += len(g["fixes"]) - len(keep)
        g["fixes"] = keep
        g["count"] = len(keep)
    checklist["groups"] = [g for g in checklist["groups"] if g["count"]]
    print(f"снято как работа в BaseLinker: {from_bl}")

    checklist["total_fixes"] = sum(g["count"] for g in checklist["groups"])
    checklist["total_pages"] = len(checklist["groups"])
    print(f"снято как уже решённое заменой документов: "
          f"{before - checklist['total_fixes']}")

    payload = json.dumps({"checklist": checklist, "translations": translations,
                          "documents": documents},
                         ensure_ascii=False).replace("</", "<\\/")

    js = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "artifact.js"), encoding="utf-8").read()

    html = f"""<title>La Petite Bloom — что починить на сайте</title>
<style>{CSS}</style>
<div class="sheet">
  <header class="mast">
    <p class="eyebrow">Рабочий чек-лист · lapetitebloom.com</p>
    <h1>Что починить на сайте</h1>
    <p class="lede">Правки по трём языковым версиям, сгруппированные по страницам.
      У каждой — где она, что сейчас не так и готовый текст на PL/UA/EN.
      Здесь же документы магазина и их переводы.</p>
    <div class="bar"><i id="barfill"></i></div>
    <div class="pstat" id="pstat"></div>
    <div class="tabs" role="tablist">
      <button role="tab" data-tab="tasks" aria-selected="true">Правки</button>
      <button role="tab" data-tab="docs" aria-selected="false">Документы и переводы</button>
    </div>
  </header>

  <section class="panel on" id="p-tasks">
    <div class="toolbar">
      <div class="row">
        <input type="search" id="q" placeholder="Поиск: страница, текст, номер…"
               aria-label="Поиск" autocomplete="off">
        <button class="chip" id="theme" type="button">Тема</button>
      </div>
      <div class="chips" id="chips"></div>
    </div>
    <div id="list"></div>
    <p class="excluded" id="excluded" hidden></p>
    <p class="hint"><b>Здесь только то, что правится на самом сайте.</b>
      Значения атрибутов, фильтры и тексты товаров приходят из BaseLinker —
      править их на странице бесполезно, следующая выгрузка перезапишет. Они
      вынесены в отдельный документ про BaseLinker и отсюда убраны.</p>
    <p class="hint"><b>На каждой правке три кнопки: «Согласен», «Удалить»,
      «Комментарий».</b> Они те же, что в рабочем документе, и память у них общая:
      ответ, поставленный здесь, виден и там. Отметки живут в этом браузере и сами
      никуда не уходят — чтобы я их прочитал, нажмите «Скопировать мои ответы»
      в рабочем документе и вставьте в чат.</p>
    <p class="hint"><b>Отметки «готово» сохраняются в вашем браузере.</b>
      У коллеги по той же ссылке будет свой список — общие отметки появятся,
      когда чек-лист развернут на своём сервере.</p>
  </section>

  <section class="panel" id="p-docs">
    <p class="hint">Документы магазина в оригинале и построчные переводы на
      украинский и английский. Польский — источник правды; переводы приведены
      блок в блок, чтобы их можно было сверять и копировать.
      В текстах уже применено решение: <b>kontakt@ → hello@</b>.</p>
    <div class="docs" id="doclist"></div>
    <div id="doctexts"></div>
  </section>
</div>
<button class="chip" id="totop" type="button">↑ Наверх</button>
<script>var DATA={payload};</script>
<script>{js}</script>
"""
    open(out_path, "w", encoding="utf-8").write(html)
    kb = len(html.encode("utf-8")) / 1024
    print(f"{out_path}  {kb:.0f} КБ  "
          f"страниц: {checklist['total_pages']}  правок: {checklist['total_fixes']}  "
          f"документов: {len(documents)}  блоков перевода: {translations['total_blocks']}")


if __name__ == "__main__":
    main()
