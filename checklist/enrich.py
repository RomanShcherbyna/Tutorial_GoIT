#!/usr/bin/env python3
"""Give every fix an owner and a place you can actually look at.

Two things were missing and the client hit both. "Анонс-бар, ссылка вокруг текста
(header__announcement-link)" says nothing to someone who does not read markup —
it needs the address of a page where you can see it. And the list mixed work
that belongs to different people: menu wording and promo copy are the shop's own
text, colour values live in the catalogue feed, and only the rest is a
developer's job.

So each fix now carries who does it and where it is visible, and catalogue
values carry the pages that actually show them.

Usage:  python3 enrich.py <checklist.json> <raw_dir> [--drop=ID,ID]
"""
import glob
import json
import os
import re
import sys

BASE = "https://lapetitebloom.com"
PREFIX = {"pl": "", "ua": "/ua", "en": "/en"}

OWNERS = {
    "dev": ("Программисты", "Шаблон, ссылки, строки движка — правится в коде"),
    "catalog": ("Каталог / BaseLinker", "Значения атрибутов и данные товаров — "
                                        "правятся в товарной базе, не на сайте"),
    "content": ("Наш контент", "Наши собственные тексты — меню, акции, баннеры, "
                               "описания. Программистам не отдаём"),
}

# Markup-level work: nothing to write, something to fix in code.
DEV_HINT = re.compile(
    r"aria-label|href|hreflang|canonical|swatch|class=|<a |<img|<script|"
    r"FenixTranslations|walidacj|валидац|validation|404|500|redirect|редирект|"
    r"sitemap|robots|noindex|meta |<title|alt-|lazy|виджет|widget|cookiebot",
    re.I)
# The shop's own copy — the client writes these, not a developer.
CONTENT_HINT = re.compile(
    r"меню|menu|анонс|announcement|баннер|banner|слайд|slider|акци|promo|"
    r"prezenty|gifts|bestseller|подборк|описание категории|opis kategorii|"
    r"блог|blog|о бренде|about", re.I)
# Catalogue data: attribute values, product names, sizes, colours.
CATALOG_HINT = re.compile(
    r"filtr|фильтр|filter|atrybut|атрибут|attribute|kolor|колір|colour|color|"
    r"rozmiar|розмір|size|wartoś|значени|value|artykuł|sku|товар|produkt|product",
    re.I)


def owner_of(f):
    blob = " ".join(str(f.get(k, "")) for k in
                    ("action", "title", "current", "why", "issue"))
    agent = (f.get("id") or "").split("-")[0]

    if f.get("issue") == "BROKEN" or DEV_HINT.search(blob):
        # A colour swatch with a hard-coded #000 is still markup.
        if agent == "10" and not re.search(r"swatch|class=|<", blob):
            return "catalog"
        return "dev"
    if agent == "10":
        return "catalog"
    if agent == "11" and CATALOG_HINT.search(blob):
        return "catalog"
    if CONTENT_HINT.search(blob):
        return "content"
    if agent in ("12", "13", "14"):
        return "dev"
    if agent in ("01", "02", "09"):
        return "content"
    return "dev"


def index_raw(raw_dir):
    """slug -> text, so a value can be traced back to the pages showing it."""
    idx = {}
    for locale in ("pl", "ua", "en"):
        for path in glob.glob(os.path.join(raw_dir, locale, "*.txt")):
            slug = os.path.basename(path)[:-4]
            idx[(locale, slug)] = open(path, encoding="utf-8",
                                       errors="ignore").read()
    return idx


def slug_to_url(slug, locale):
    if slug == "index":
        return BASE + PREFIX[locale]
    path = "/" + slug.replace("__", "/").split("_q_")[0]
    return BASE + PREFIX[locale] + path


def values_in(f):
    """Pull the catalogue values a fix talks about out of its quote."""
    cur = f.get("current") or ""
    cur = re.sub(r"^[a-z]{2}:\s*", "", cur)
    parts = re.split(r"\s+ORAZ\s+|\s+ТА\s+|\s+AND\s+|,\s*", cur)
    out = []
    for p in parts:
        p = p.strip().strip('"«»')
        if 3 <= len(p) <= 60 and not p.startswith("<"):
            out.append(p)
    return out[:6]


def find_pages(value, idx, limit=3):
    hits = []
    for (locale, slug), text in idx.items():
        if value in text:
            hits.append((locale, slug))
    # prefer Polish, and one URL per page is enough
    hits.sort(key=lambda t: (t[0] != "pl", t[1]))
    seen, out = set(), []
    for locale, slug in hits:
        if slug in seen:
            continue
        seen.add(slug)
        out.append(slug_to_url(slug, locale))
        if len(out) >= limit:
            break
    return out


def main():
    cl_path, raw_dir = sys.argv[1], sys.argv[2]
    drop = set()
    for a in sys.argv[3:]:
        if a.startswith("--drop="):
            drop = {x.strip() for x in a.split("=", 1)[1].split(",")}

    data = json.load(open(cl_path, encoding="utf-8"))
    idx = index_raw(raw_dir)

    tally, dropped, located = {}, 0, 0
    for g in data["groups"]:
        keep = []
        for f in g["fixes"]:
            if f["id"] in drop:
                dropped += 1
                continue
            o = owner_of(f)
            f["owner"] = o
            f["owner_label"] = OWNERS[o][0]
            tally[o] = tally.get(o, 0) + 1

            # Where can this be seen? Page URLs first, catalogue values second.
            urls = []
            if g.get("urls"):
                urls = [g["urls"][k] for k in ("pl", "ua", "en") if g["urls"].get(k)]
            f["see"] = urls

            if o == "catalog":
                found = []
                for v in values_in(f):
                    for u in find_pages(v, idx):
                        if u not in found:
                            found.append(u)
                    if len(found) >= 4:
                        break
                if found:
                    f["see_values"] = found[:4]
                    located += 1
            keep.append(f)
        g["fixes"] = keep
        g["count"] = len(keep)
        g["blockers"] = sum(1 for x in keep if x["severity"] == "blocker")
        g["owners"] = sorted({x["owner"] for x in keep})

    data["groups"] = [g for g in data["groups"] if g["count"]]
    data["total_fixes"] = sum(g["count"] for g in data["groups"])
    data["total_pages"] = len(data["groups"])
    data["owners"] = [{"key": k, "label": OWNERS[k][0], "desc": OWNERS[k][1],
                       "count": tally.get(k, 0)} for k in ("dev", "content", "catalog")]

    json.dump(data, open(cl_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"снято по просьбе заказчика: {dropped}")
    print(f"правок осталось: {data['total_fixes']} на {data['total_pages']} страницах\n")
    for k in ("dev", "content", "catalog"):
        print(f"  {OWNERS[k][0]:<24} {tally.get(k,0)}")
    print(f"\nкаталожных правок со ссылками «где видно»: {located}")


if __name__ == "__main__":
    main()
