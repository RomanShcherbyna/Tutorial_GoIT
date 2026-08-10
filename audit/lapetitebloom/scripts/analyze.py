#!/usr/bin/env python3
"""Cross-locale analysis over the crawl dump.

Produces:
  cmp/<slug>.md      side-by-side pl / ua / en visible text per page
  analysis.json      machine findings (untranslated, wrong script, stubs)
  analysis.md        human summary
"""
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
CMP = os.path.join(HERE, "cmp")
LOCALES = ["pl", "ua", "en"]

CYR = re.compile(r"[Ѐ-ӿ]")
UA_ONLY = re.compile(r"[іїєґІЇЄҐ]")
RU_ONLY = re.compile(r"[ыэъёЫЭЪЁ]")
PL_DIA = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
LOREM = re.compile(
    r"\b(lorem|ipsum|dolor sit amet|consectetur|voluptat|exercitationem|"
    r"molestias|architecto|repudiandae|asperiores|reiciendis|accusantium|"
    r"perspiciatis|necessitatibus|quisquam|laboriosam|doloremque)\b", re.I)
STUB = re.compile(r"^(baner\s*\d+|banner\s*\d+|test\d*|todo|tbd|xxx+|lorem[^\s]*|"
                  r"placeholder|zaglushka|заглушка|текст|text)$", re.I)

# Boilerplate that legitimately repeats across locales (brand names, units).
SAFE_IDENTICAL = re.compile(
    r"^(la petite bloom|bloom|pln|eur|usd|uah|\W+|[\d\s.,:%/x×+-]+|"
    r"onesize|one size|xs|s|m|l|xl|xxl|\d+y|\d+m|top|new|sale|vat|nip|krs|regon|"
    r"[a-z0-9._%-]+@[a-z0-9.-]+|\+?[\d\s()-]{6,})$", re.I)


def load(locale, slug):
    p = os.path.join(RAW, locale, slug)
    if not os.path.exists(p + ".json"):
        return None, None
    meta = json.load(open(p + ".json", encoding="utf-8"))
    lines = open(p + ".txt", encoding="utf-8").read().split("\n")
    return meta, [l for l in lines if l.strip()]


def slugs():
    d = os.path.join(RAW, "pl")
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def script_issue(locale, s):
    """Return an issue code if the string is written in the wrong script."""
    if locale == "pl":
        if CYR.search(s):
            return "cyrillic_in_pl"
    elif locale == "en":
        if CYR.search(s):
            return "cyrillic_in_en"
    elif locale == "ua":
        if RU_ONLY.search(s):
            return "russian_in_ua"
        if PL_DIA.search(s):
            return "polish_in_ua"
    return None


def main():
    os.makedirs(CMP, exist_ok=True)
    findings = defaultdict(list)
    per_page = {}

    for sl in slugs():
        data = {}
        for loc in LOCALES:
            meta, lines = load(loc, sl)
            if meta:
                data[loc] = (meta, lines)
        if "pl" not in data:
            continue

        pl_meta, pl_lines = data["pl"]
        path = pl_meta["path"]

        # ---- side-by-side dump for the agents --------------------------
        with open(os.path.join(CMP, sl + ".md"), "w", encoding="utf-8") as f:
            f.write(f"# {path}\n\n")
            for loc in LOCALES:
                if loc not in data:
                    continue
                m, ls = data[loc]
                f.write(f"\n## [{loc}] {m['url']}\n")
                f.write(f"- status: {m['status']} | html lang: {m['html_lang']}\n")
                f.write(f"- title: {m['title']}\n")
                f.write(f"- meta description: {m['meta_description']}\n")
                f.write(f"- h1: {m['h1']}\n\n")
                f.write("```\n" + "\n".join(ls) + "\n```\n")

        page = {"path": path, "issues": []}

        # ---- title / description / h1 parity ---------------------------
        for field in ("title", "meta_description"):
            vals = {loc: data[loc][0][field] for loc in data}
            if vals.get("pl") and vals.get("ua") == vals.get("pl"):
                page["issues"].append({"type": "untranslated", "field": field,
                                       "locale": "ua", "text": vals["pl"]})
            if vals.get("pl") and vals.get("en") == vals.get("pl"):
                page["issues"].append({"type": "untranslated", "field": field,
                                       "locale": "en", "text": vals["pl"]})
            if not vals.get("pl"):
                page["issues"].append({"type": "empty", "field": field,
                                       "locale": "pl", "text": ""})

        # ---- per-locale line scan --------------------------------------
        pl_set = set(pl_lines)
        for loc in LOCALES:
            if loc not in data:
                continue
            _, lines = data[loc]
            for s in lines:
                if LOREM.search(s):
                    findings["lorem"].append({"path": path, "locale": loc,
                                              "text": s[:220]})
                if STUB.match(s.strip()):
                    findings["stub"].append({"path": path, "locale": loc,
                                             "text": s[:120]})
                code = script_issue(loc, s)
                if code:
                    findings[code].append({"path": path, "locale": loc,
                                           "text": s[:220]})
                if (loc != "pl" and s in pl_set and len(s) > 3
                        and not SAFE_IDENTICAL.match(s.strip())):
                    findings["identical_to_pl"].append(
                        {"path": path, "locale": loc, "text": s[:220]})

        # ---- FenixTranslations key parity ------------------------------
        keys = {}
        for loc in LOCALES:
            if loc not in data:
                continue
            ft = data[loc][0].get("fenix_translations", {})
            keys[loc] = {f"{g}.{k}": v for g, kv in ft.items()
                         for k, v in kv.items()}
        if "pl" in keys:
            for loc in ("ua", "en"):
                if loc not in keys:
                    continue
                missing = sorted(set(keys["pl"]) - set(keys[loc]))
                same = sorted(k for k in set(keys["pl"]) & set(keys[loc])
                              if keys["pl"][k] == keys[loc][k]
                              and len(keys["pl"][k]) > 3
                              and not SAFE_IDENTICAL.match(keys["pl"][k]))
                if missing:
                    page["issues"].append({"type": "ft_missing_keys",
                                           "locale": loc, "keys": missing})
                if same:
                    page["issues"].append({"type": "ft_untranslated",
                                           "locale": loc,
                                           "keys": [(k, keys["pl"][k]) for k in same]})

        per_page[path] = page

    # dedupe
    for k, v in findings.items():
        seen, out = set(), []
        for it in v:
            key = (it["locale"], it["text"])
            if key not in seen:
                seen.add(key)
                out.append(it)
        findings[k] = out

    json.dump({"findings": dict(findings), "per_page": per_page},
              open(os.path.join(HERE, "analysis.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    with open(os.path.join(HERE, "analysis.md"), "w", encoding="utf-8") as f:
        f.write("# Автоматический кросс-локальный анализ\n\n")
        for k in ("lorem", "stub", "cyrillic_in_pl", "cyrillic_in_en",
                  "russian_in_ua", "polish_in_ua", "identical_to_pl"):
            items = findings.get(k, [])
            f.write(f"\n## {k} ({len(items)})\n\n")
            for it in items[:400]:
                f.write(f"- `{it['locale']}` {it['path']} — {it['text']}\n")

        f.write("\n\n# Проблемы по страницам\n")
        for path, pg in per_page.items():
            if not pg["issues"]:
                continue
            f.write(f"\n## {path}\n")
            for i in pg["issues"]:
                if i["type"] == "ft_missing_keys":
                    f.write(f"- [{i['locale']}] нет ключей UI: {', '.join(i['keys'][:30])}\n")
                elif i["type"] == "ft_untranslated":
                    f.write(f"- [{i['locale']}] UI-ключи не переведены: "
                            f"{', '.join(k for k, _ in i['keys'][:30])}\n")
                else:
                    f.write(f"- [{i.get('locale')}] {i['type']} "
                            f"{i.get('field','')}: {i.get('text','')[:160]}\n")

    print("=== summary ===")
    for k, v in sorted(findings.items(), key=lambda x: -len(x[1])):
        print(f"{k:<20} {len(v)}")
    print(f"pages analysed: {len(per_page)}")


if __name__ == "__main__":
    main()
