#!/usr/bin/env python3
"""Point every cross-reference inside the documents at the page that already
exists, in the right language.

The client keeps the current URLs, so nothing is created or redirected. The
documents refer to each other by name only ("Polityka prywatności dostępna w
Sklepie"), which is fine on paper and useless on a website — a reader cannot
click a name. Here each mention becomes a link to the live page, with the
locale prefix that language uses: none for Polish, /ua and /en for the others.

Usage:  python3 linkify.py <translations.json> [--report]
"""
import json
import re
import sys

BASE = "https://lapetitebloom.com"
PREFIX = {"pl": "", "ua": "/ua", "en": "/en"}

# Document -> the page it already lives on. Confirmed against the live footer
# in all three locales; these slugs are the same in every language.
PAGES = {
    "regulamin": "/terms-of-use",
    "prywatnosc": "/privacy-policy",
    "cookies": "/polityka-cookies",
    "zwroty": "/claims-and-complaints",
    "zgody": "/zgody-klauzule-i-regulamin-newslettera",
    "dostawa": "/delivery-and-payment",
    "karty": "/regulamin-kart-podarunkowych",
    "dostepnosc": "/deklaracja-dostepnosci",
}

# How each document is named inside the running text, per language. Longest
# first so "Polityka zwrotów i reklamacji" wins over "Polityka zwrotów".
NAMES = {
    "regulamin": {
        "pl": ["Regulaminu Sklepu", "Regulamin Sklepu", "Regulaminie Sklepu",
               "Regulaminem Sklepu", "Regulaminu", "Regulaminie", "Regulaminem",
               "Regulamin"],
        "ua": ["Правилами інтернет-магазину", "Правил інтернет-магазину",
               "Правила інтернет-магазину", "Правилах інтернет-магазину",
               "Правилами", "Правилах", "Правил", "Правила"],
        "en": ["the Terms and Conditions", "Terms and Conditions"],
    },
    "prywatnosc": {
        "pl": ["Polityce prywatności", "Polityką prywatności",
               "Polityki prywatności", "Polityka prywatności"],
        "ua": ["Політикою конфіденційності", "Політики конфіденційності",
               "Політиці конфіденційності", "Політика конфіденційності"],
        "en": ["the Privacy Policy", "Privacy Policy", "Privacy policy"],
    },
    "cookies": {
        "pl": ["Polityce cookies", "Polityką cookies", "Polityki cookies",
               "Polityka cookies"],
        "ua": ["Політикою щодо файлів cookie", "Політики щодо файлів cookie",
               "Політика щодо файлів cookie", "Політиці щодо файлів cookie"],
        "en": ["the Cookie Policy", "Cookie Policy", "Cookie policy",
               "Cookies Policy", "Cookies policy"],
    },
    "zwroty": {
        "pl": ["Polityce zwrotów i reklamacji", "Polityki zwrotów i reklamacji",
               "Polityką zwrotów i reklamacji", "Polityka zwrotów i reklamacji"],
        "ua": ["Політикою повернень і рекламацій", "Політики повернень і рекламацій",
               "Політиці повернень і рекламацій", "Політика повернень і рекламацій"],
        "en": ["the Returns and Complaints Policy", "Returns and Complaints Policy",
               "Returns and complaints policy", "Returns and complaints"],
    },
    "dostawa": {
        "pl": ["Dostawa i płatności", "Dostawie i płatnościach"],
        "ua": ["Доставка та оплата", "Доставки та оплати"],
        "en": ["Delivery and Payment"],
    },
    "karty": {
        "pl": ["Regulaminu kart podarunkowych", "Regulamin kart podarunkowych"],
        "ua": ["Правил використання подарункових карт",
               "Правила використання подарункових карт"],
        "en": ["the Gift Card Terms and Conditions", "Gift Card Terms and Conditions",
               "Gift card terms and conditions"],
    },
    "dostepnosc": {
        "pl": ["Deklaracja dostępności", "Deklaracji dostępności"],
        "ua": ["Заява про доступність", "Заяви про доступність"],
        "en": ["the Accessibility Statement", "Accessibility Statement"],
    },
}

# A document must not link to itself.
SELF = {
    "1-regulamin-sklepu": "regulamin",
    "2-polityka-prywatnosci": "prywatnosc",
    "3-polityka-cookies": "cookies",
    "4-polityka-zwrotow-i-reklamacji": "zwroty",
    "5-zgody-i-newsletter": "zgody",
    "6-dostawa-i-platnosci": "dostawa",
    "7-regulamin-kart-podarunkowych": "karty",
    "8-deklaracja-dostepnosci": "dostepnosc",
}


def url(doc_key, lang):
    return BASE + PREFIX[lang] + PAGES[doc_key]


def linkify(text, lang, skip_key):
    """Return (marked text, links found). Only the first mention of each
    document is linked — a wall of repeated links reads worse than plain text."""
    if not text:
        return text, []
    found, used = [], set()
    for key, per_lang in NAMES.items():
        if key == skip_key or key in used:
            continue
        for name in per_lang.get(lang, []):
            # Skip names already inside a marker from an earlier pass.
            # Case-insensitive: the English text writes "Privacy policy" while
            # the Polish writes "Polityka prywatności" — same document.
            pattern = re.compile(r"(?<![\w\[])" + re.escape(name) + r"(?![\w\]])",
                                 re.IGNORECASE)
            m = pattern.search(text)
            if not m:
                continue
            target = url(key, lang)
            text = text[:m.start()] + f"[[{name}|{target}]]" + text[m.end():]
            found.append({"doc": key, "name": name, "url": target})
            used.add(key)
            break
    return text, found


def main():
    path = sys.argv[1]
    report = "--report" in sys.argv
    data = json.load(open(path, encoding="utf-8"))
    total, per_doc = 0, {}

    for doc in data["documents"]:
        skip = SELF.get(doc["doc"])
        hits = []
        for b in doc["blocks"]:
            for lang in ("pl", "ua", "en"):
                marked, found = linkify(b.get(lang) or "", lang, skip)
                if found:
                    b[lang] = marked
                    hits.extend(found)
                    total += len(found)
        doc["page"] = {lang: url(skip, lang) for lang in PREFIX} if skip else {}
        doc["links"] = hits
        per_doc[doc["doc"]] = len(hits)

    json.dump(data, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"проставлено ссылок: {total}\n")
    for doc, n in per_doc.items():
        page = PAGES.get(SELF.get(doc, ""), "")
        print(f"  {doc:<34} страница {page:<42} ссылок внутри: {n}")
    if report:
        print("\nадреса по локалям:")
        for key, slug in PAGES.items():
            print(f"  {key:<12} pl {BASE}{slug}")
            print(f"  {'':<12} ua {BASE}/ua{slug}")
            print(f"  {'':<12} en {BASE}/en{slug}")


if __name__ == "__main__":
    main()
