#!/usr/bin/env python3
"""Merge the per-agent findings into findings.json plus the two deliverables:
report.html (artifact page) and README.md.

Usage:  python3 build_report.py <findings_dir> <out_dir>
"""
import html
import json
import os
import sys
from collections import Counter, defaultdict

SEV_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
SEV_LABEL = {"blocker": "Блокер", "high": "Критично",
             "medium": "Средне", "low": "Мелочь"}
ISSUE_LABEL = {
    "STUB": "Заглушка", "MISSING": "Нет перевода", "WRONG": "Кривой перевод",
    "LEFTOVER": "Чужой язык", "TYPO": "Опечатка", "LEGAL": "Юр. требование",
    "BROKEN": "Битая ссылка",
}
LOC_LABEL = {"pl": "PL", "ua": "UA", "en": "EN", "all": "все"}


def load(findings_dir):
    out = []
    for fn in sorted(os.listdir(findings_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(findings_dir, fn)
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"  !! {fn}: {e}")
            continue
        if isinstance(data, dict):
            data = data.get("findings", [])
        agent = fn[:-5]
        for i, f in enumerate(data, 1):
            if not isinstance(f, dict):
                continue
            f.setdefault("id", f"{agent}-{i:02d}")
            f["agent"] = agent
            f["severity"] = str(f.get("severity", "medium")).lower()
            f["issue"] = str(f.get("issue", "")).upper()
            f["locale"] = str(f.get("locale", "all")).lower()
            out.append(f)
        print(f"  {fn}: {len(data)}")
    return out


def dedupe(items):
    seen, out = {}, []
    for f in items:
        key = (f.get("path", ""), (f.get("current") or "")[:120].strip().lower(),
               f.get("issue"))
        if key in seen and (f.get("current") or "").strip():
            # keep the richer record
            old = seen[key]
            if len(json.dumps(f, ensure_ascii=False)) > len(json.dumps(old, ensure_ascii=False)):
                out[out.index(old)] = f
                seen[key] = f
            continue
        seen[key] = f
        out.append(f)
    return out


def srt(items):
    return sorted(items, key=lambda f: (SEV_ORDER.get(f["severity"], 4),
                                        f.get("path", ""), f.get("id", "")))


# --------------------------------------------------------------------------
def md_report(items, stats):
    L = []
    w = L.append
    w("# Контент-аудит lapetitebloom.com — PL / UA / EN\n")
    w("Аудит трёх языковых версий магазина перед запуском и верификацией в Przelewy24.\n")
    w(f"Проверено **{stats['pages']} страниц** × 3 локали = "
      f"**{stats['pages'] * 3} снимков**. Найдено **{len(items)}** проблем.\n")

    w("\n## Сводка\n")
    w("| Уровень | Сколько |")
    w("|---|---|")
    for s in ("blocker", "high", "medium", "low"):
        w(f"| {SEV_LABEL[s]} | {stats['sev'].get(s, 0)} |")

    w("\n| Тип проблемы | Сколько |")
    w("|---|---|")
    for k, v in stats["issue"].most_common():
        w(f"| {ISSUE_LABEL.get(k, k)} | {v} |")

    for sev in ("blocker", "high", "medium", "low"):
        group = [f for f in items if f["severity"] == sev]
        if not group:
            continue
        w(f"\n---\n\n## {SEV_LABEL[sev]} ({len(group)})\n")
        for f in group:
            w(f"\n### {f.get('id')} · {f.get('path', '')} · "
              f"{ISSUE_LABEL.get(f['issue'], f['issue'])} "
              f"[{LOC_LABEL.get(f['locale'], f['locale'])}]\n")
            if f.get("block"):
                w(f"**Где:** {f['block']}\n")
            if f.get("current"):
                w(f"\n**Сейчас:**\n\n> {f['current'][:1500]}\n")
            if f.get("why"):
                w(f"\n**Почему проблема:** {f['why']}\n")
            if any(f.get(k) for k in ("pl", "ua", "en")):
                w("\n**Предлагаемый текст:**\n")
                for lang, lab in (("pl", "PL"), ("ua", "UA"), ("en", "EN")):
                    if f.get(lang):
                        w(f"\n*{lab}:*\n\n```\n{f[lang]}\n```\n")
            if f.get("note"):
                w(f"\n**Куда вписать / примечание:** {f['note']}\n")
    return "\n".join(L)


# --------------------------------------------------------------------------
# Artifact page.
#
# Design plan — the subject is a marked-up proof of a trilingual shop, so the
# page borrows a proofreader's sheet rather than a card dashboard.
#   Colour  cool paper #eef0f3 / white surface / ink #171b24, blue-biased grey
#           #626b7c, structural accent ink-blue #2b4b7d; severity is a separate
#           semantic ramp (red / amber / olive / green) so it never doubles as
#           the accent.
#   Type    condensed letterspaced uppercase for labels and headings (spec-sheet
#           register, not editorial serif), system sans for prose, monospace for
#           evidence and proposed copy — the two things that get copied out.
#   Layout  a narrow margin gutter carries the severity mark and the id, the way
#           proof marks sit in a margin; findings are separated by hairlines
#           rather than floating cards. Proposed copy sits in three lanes
#           PL | UA | EN so parity reads at a glance, stacking under 800px.
# --------------------------------------------------------------------------
def esc(s):
    return html.escape(str(s or ""))


CSS = """
:root{
  --ground:#eef0f3; --surface:#ffffff; --sunken:#e4e7ec;
  --ink:#171b24; --muted:#626b7c; --line:#cfd5de; --hair:#dde2e9;
  --accent:#2b4b7d;
  --blocker:#b3261e; --high:#a35b12; --medium:#6f6a2e; --low:#3f6b57;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#12151b; --surface:#191d25; --sunken:#0d1015;
    --ink:#e6e9ef; --muted:#9099a8; --line:#333b47; --hair:#262d37;
    --accent:#8fb0e6;
    --blocker:#ff9089; --high:#f0b072; --medium:#d6cf8b; --low:#93c4ab;
  }
}
:root[data-theme="dark"]{
  --ground:#12151b; --surface:#191d25; --sunken:#0d1015;
  --ink:#e6e9ef; --muted:#9099a8; --line:#333b47; --hair:#262d37;
  --accent:#8fb0e6;
  --blocker:#ff9089; --high:#f0b072; --medium:#d6cf8b; --low:#93c4ab;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font:15px/1.65 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.sheet{max-width:1180px;margin:0 auto;padding:3rem 1.25rem 6rem}

/* ---------- masthead ---------- */
.mast{border-bottom:2px solid var(--ink);padding-bottom:1.25rem;margin-bottom:1.75rem}
.eyebrow{
  font-size:.7rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
  color:var(--accent);margin:0 0 .6rem;
}
h1{
  margin:0 0 .5rem;font-size:clamp(1.5rem,3.4vw,2.15rem);line-height:1.15;
  font-weight:650;letter-spacing:-.015em;text-wrap:balance;
}
.lede{margin:0;color:var(--muted);max-width:62ch}
.lede b{color:var(--ink);font-weight:650}

/* ---------- tally ---------- */
.tally{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
  gap:1px;background:var(--line);border:1px solid var(--line);
  margin:1.75rem 0;
}
.tally div{background:var(--surface);padding:.85rem 1rem}
.tally b{
  display:block;font-size:1.75rem;line-height:1.1;font-weight:650;
  font-variant-numeric:tabular-nums;
}
.tally span{
  font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
}
.t-blocker b{color:var(--blocker)} .t-high b{color:var(--high)}
.t-medium b{color:var(--medium)} .t-low b{color:var(--low)}

/* ---------- filters ---------- */
.filters{
  display:flex;flex-wrap:wrap;gap:.35rem;margin:0 0 2.25rem;
  padding-bottom:1.25rem;border-bottom:1px solid var(--line);
}
.filters button{
  font:inherit;font-size:.75rem;letter-spacing:.06em;text-transform:uppercase;
  background:transparent;color:var(--muted);border:1px solid var(--line);
  padding:.34rem .7rem;cursor:pointer;
}
.filters button:hover{color:var(--ink);border-color:var(--muted)}
.filters button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.filters button[aria-pressed="true"]{
  background:var(--ink);border-color:var(--ink);color:var(--ground);
}
.filters i{font-style:normal;opacity:.65;font-variant-numeric:tabular-nums}

/* ---------- findings ---------- */
.find{
  display:grid;grid-template-columns:5.5rem 1fr;gap:0 1.4rem;
  padding:1.6rem 0;border-top:1px solid var(--hair);
}
.find:first-of-type{border-top:1px solid var(--line)}
.gutter{position:relative}
.mark{
  font-size:.66rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  padding:.2rem 0;border-top:2px solid currentColor;display:block;
}
.s-blocker .mark{color:var(--blocker)} .s-high .mark{color:var(--high)}
.s-medium .mark{color:var(--medium)} .s-low .mark{color:var(--low)}
.fid{
  display:block;margin-top:.45rem;font-size:.7rem;color:var(--muted);
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
}
.tags{display:flex;flex-wrap:wrap;gap:.4rem;align-items:baseline;margin-bottom:.55rem}
.kind{font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}
.loc{
  font-size:.65rem;font-weight:700;letter-spacing:.08em;color:var(--muted);
  border:1px solid var(--line);padding:.05rem .35rem;
}
.path{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem;
  color:var(--accent);word-break:break-all;
}
.where{margin:0 0 .55rem;font-size:.9rem}
.where b{
  font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
  font-weight:700;
}
.evidence{
  margin:.6rem 0;padding:.6rem .85rem;background:var(--sunken);
  border-left:2px solid var(--line);
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.82rem;
  white-space:pre-wrap;overflow-x:auto;max-height:18em;
}
.why{margin:.6rem 0;color:var(--muted);font-size:.92rem}
.lanes{
  display:grid;grid-template-columns:repeat(3,1fr);gap:1px;
  background:var(--line);border:1px solid var(--line);margin:.9rem 0 0;
}
.lanes.one{grid-template-columns:1fr}
.lane{background:var(--surface);padding:.6rem .8rem;min-width:0}
.lane h4{
  margin:0 0 .4rem;font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);font-weight:700;
}
.lane pre{
  margin:0;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.82rem;
  line-height:1.55;white-space:pre-wrap;overflow-x:auto;
}
.note{
  margin:.8rem 0 0;font-size:.87rem;color:var(--muted);
  padding-left:.85rem;border-left:2px solid var(--hair);
}
.note b{
  font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink);
}
.find[hidden]{display:none}
.empty{padding:2rem 0;color:var(--muted)}
@media (max-width:800px){
  .find{grid-template-columns:1fr;gap:.6rem}
  .gutter{display:flex;gap:.7rem;align-items:baseline}
  .mark{border-top:0;border-left:2px solid currentColor;padding:0 0 0 .5rem}
  .fid{margin-top:0}
  .lanes{grid-template-columns:1fr}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

JS = """
const btns=[...document.querySelectorAll('.filters button')];
const finds=[...document.querySelectorAll('.find')];
const empty=document.querySelector('.empty');
function apply(btn){
  btns.forEach(b=>b.setAttribute('aria-pressed',String(b===btn)));
  const key=btn.dataset.f,val=btn.dataset.v;
  let shown=0;
  finds.forEach(f=>{
    const ok = key==='all' || f.dataset[key]===val;
    f.hidden=!ok; if(ok) shown++;
  });
  empty.hidden=shown>0;
}
btns.forEach(b=>b.addEventListener('click',()=>apply(b)));
"""


def html_report(items, stats):
    sev_label = {"blocker": "Блокер", "high": "Критично",
                 "medium": "Средне", "low": "Мелочь"}
    issue_label = {"STUB": "Заглушка", "MISSING": "Нет перевода",
                   "WRONG": "Кривой перевод", "LEFTOVER": "Чужой язык",
                   "TYPO": "Опечатка", "LEGAL": "Юр. требование",
                   "BROKEN": "Битая ссылка"}
    loc_label = {"pl": "PL", "ua": "UA", "en": "EN", "all": "PL·UA·EN"}

    blocks = []
    for f in items:
        sev = f["severity"]
        lanes = [(lab, f[k]) for k, lab in
                 (("pl", "Polski"), ("ua", "Українська"), ("en", "English"))
                 if f.get(k)]
        lanes_html = ""
        if lanes:
            cls = "lanes one" if len(lanes) == 1 else "lanes"
            inner = "".join(
                f'<div class="lane"><h4>{lab}</h4><pre>{esc(txt)}</pre></div>'
                for lab, txt in lanes)
            lanes_html = f'<div class="{cls}">{inner}</div>'

        blocks.append(f"""
<section class="find s-{esc(sev)}" data-sev="{esc(sev)}" data-issue="{esc(f['issue'])}">
  <div class="gutter">
    <span class="mark">{esc(sev_label.get(sev, sev))}</span>
    <span class="fid">{esc(f.get('id'))}</span>
  </div>
  <div class="body">
    <div class="tags">
      <span class="kind">{esc(issue_label.get(f['issue'], f['issue']))}</span>
      <span class="loc">{esc(loc_label.get(f['locale'], f['locale'].upper()))}</span>
      <span class="path">{esc(f.get('path', ''))}</span>
    </div>
    {f'<p class="where"><b>Где</b> &nbsp;{esc(f.get("block"))}</p>' if f.get("block") else ""}
    {f'<div class="evidence">{esc(f.get("current"))[:1800]}</div>' if f.get("current") else ""}
    {f'<p class="why">{esc(f.get("why"))}</p>' if f.get("why") else ""}
    {lanes_html}
    {f'<p class="note"><b>Куда вписать</b><br>{esc(f.get("note"))}</p>' if f.get("note") else ""}
  </div>
</section>""")

    tally = "".join(
        f'<div class="t-{s}"><b>{stats["sev"].get(s, 0)}</b>'
        f'<span>{sev_label[s]}</span></div>'
        for s in ("blocker", "high", "medium", "low")
        if stats["sev"].get(s))

    filters = ['<button data-f="all" aria-pressed="true">Всё '
               f'<i>{len(items)}</i></button>']
    for s in ("blocker", "high", "medium", "low"):
        if stats["sev"].get(s):
            filters.append(f'<button data-f="sev" data-v="{s}" aria-pressed="false">'
                           f'{sev_label[s]} <i>{stats["sev"][s]}</i></button>')
    for k, v in stats["issue"].most_common():
        filters.append(f'<button data-f="issue" data-v="{k}" aria-pressed="false">'
                       f'{issue_label.get(k, k)} <i>{v}</i></button>')

    return f"""<title>Контент-аудит lapetitebloom.com — PL / UA / EN</title>
<style>{CSS}</style>

<div class="sheet">
  <header class="mast">
    <p class="eyebrow">Проверка трёх языковых версий · перед запуском и Przelewy24</p>
    <h1>Контент-аудит lapetitebloom.com</h1>
    <p class="lede">Обойдено <b>{stats['pages']} страниц</b> в трёх локалях —
      польской, украинской и английской, <b>{stats['pages'] * 3} снимков</b>.
      Найдено <b>{len(items)}</b> проблем: заглушки, непереведённые блоки,
      кривые переводы и юридические дыры. У каждой — готовый текст на трёх языках.</p>
  </header>

  <div class="tally">{tally}</div>

  <nav class="filters" aria-label="Фильтр находок">{"".join(filters)}</nav>

  {"".join(blocks)}

  <p class="empty" hidden>Ничего не подошло под фильтр.</p>
</div>

<script>{JS}</script>"""



def main():
    fdir, odir = sys.argv[1], sys.argv[2]
    print("loading findings:")
    items = dedupe(load(fdir))
    items = srt(items)
    stats = {
        "pages": 54,
        "sev": Counter(f["severity"] for f in items),
        "issue": Counter(f["issue"] for f in items),
        "agents": Counter(f["agent"] for f in items),
    }
    os.makedirs(odir, exist_ok=True)
    json.dump(items, open(os.path.join(odir, "findings.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(odir, "README.md"), "w", encoding="utf-8").write(
        md_report(items, stats))
    open(os.path.join(odir, "report.html"), "w", encoding="utf-8").write(
        html_report(items, stats))
    print(f"\ntotal {len(items)} findings")
    for s in ("blocker", "high", "medium", "low"):
        print(f"  {s:<8} {stats['sev'].get(s, 0)}")


if __name__ == "__main__":
    main()
