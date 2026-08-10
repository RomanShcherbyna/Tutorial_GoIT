#!/usr/bin/env python3
"""Merge the per-document translations into one file the app serves, and turn
the translators' notes into checklist tasks.

The notes matter as much as the translations: reading a document closely enough
to translate it surfaces what is wrong with it. One of them found that the
Polish original tells developers to pre-tick consent boxes — implemented
literally, that breaks GDPR. Those belong in front of the team, not buried in a
translator's footnote.

Usage:  python3 build_translations.py <translations_dir> <out_translations.json> <out_notes.json>
"""
import glob
import json
import os
import re
import sys

# Titles the team will recognise, and where each document is meant to land.
DOC_META = {
    "1-regulamin-sklepu": ("Регламент магазина", "/regulamin"),
    "2-polityka-prywatnosci": ("Политика конфиденциальности", "/polityka-prywatnosci"),
    "3-polityka-cookies": ("Политика cookies", "/polityka-cookies"),
    "4-polityka-zwrotow-i-reklamacji": ("Политика возвратов и рекламаций",
                                        "/zwroty-i-reklamacje"),
    "5-zgody-i-newsletter": ("Согласия и newsletter", "(не публичная страница)"),
    "6-dostawa-i-platnosci": ("Доставка и оплата", "/dostawa-i-platnosci"),
    "7-regulamin-kart-podarunkowych": ("Регламент подарочных карт",
                                       "/regulamin-kart-podarunkowych"),
    "8-deklaracja-dostepnosci": ("Декларация доступности", "/deklaracja-dostepnosci"),
}

# A note that names a legal defect in the source is not a footnote — it blocks.
BLOCKER_HINTS = re.compile(
    r"GDPR|RODO|противополож|предвыбран|pre-tick|обязан поправить|"
    r"юридически значим|нельзя показывать покупателю", re.I)
HIGH_HINTS = re.compile(
    r"противореч|конфликт|расхожд|под юриста|к юристу|место под юриста|"
    r"не указан|отсутству|пробел|плейсхолдер|placeholder|двусмысл", re.I)


def severity(note):
    if BLOCKER_HINTS.search(note):
        return "blocker"
    if HIGH_HINTS.search(note):
        return "high"
    return "medium"


def main():
    src_dir, out_tr, out_notes = sys.argv[1], sys.argv[2], sys.argv[3]
    docs, notes, n = [], [], 0

    for path in sorted(glob.glob(os.path.join(src_dir, "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        key = d["doc"]
        title, target = DOC_META.get(key, (key, ""))
        docs.append({
            "doc": key,
            "title": title,
            "target_path": target,
            "title_pl": d.get("title_pl", ""),
            "title_ua": d.get("title_ua", ""),
            "title_en": d.get("title_en", ""),
            "blocks": d.get("blocks", []),
            "notes": d.get("notes", []),
        })
        for note in d.get("notes", []):
            n += 1
            notes.append({
                "id": f"DOC-N{n:02d}",
                "kind": "LEGAL",
                "doc": f"{title} ({key})",
                "path": target if target.startswith("/") else "",
                "title": note[:160] + ("…" if len(note) > 160 else ""),
                "target": note,
                "severity": severity(note),
                "steps": [],
                "done_when": "Решение принято и внесено в документ либо на сайт",
                "note": "Замечание переводчика к исходному документу",
            })

    json.dump({"documents": docs,
               "total_blocks": sum(len(x["blocks"]) for x in docs)},
              open(out_tr, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(notes, open(out_notes, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"документов: {len(docs)} | блоков: "
          f"{sum(len(x['blocks']) for x in docs)} | замечаний: {len(notes)}")
    for s in ("blocker", "high", "medium"):
        print(f"  {s}: {sum(1 for x in notes if x['severity'] == s)}")


if __name__ == "__main__":
    main()
