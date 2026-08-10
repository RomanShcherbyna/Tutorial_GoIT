#!/usr/bin/env python3
"""Pull every checkable claim the site makes, in all three locales.

A "claim" is anything a customer could hold the shop to and a payment provider
could check: deadlines, amounts, addresses, bank accounts, e-mails, phone
numbers, the payment operator's name, company identifiers, legal references.

These are what the client's own documents get compared against, so they are
collected verbatim with page and locale attached — never summarised.

Usage:  python3 extract_claims.py <raw_dir> <out.json>
"""
import json
import os
import re
import sys
from collections import defaultdict

LOCALES = ("pl", "ua", "en")

# Each pattern keeps enough of the sentence around the hit to stay readable.
PATTERNS = {
    "срок в днях": r"\b\d{1,3}\s*(?:dni|dniach|dnia|днів|дні|дня|days?|day)\b",
    "срок в месяцах/годах": r"\b\d{1,2}\s*(?:miesi[ęą]c\w*|місяц\w*|month\w*|lat\w*|rok\w*|рок\w*|year\w*)\b",
    "сумма": r"\b\d[\d\s.,]*\s*(?:zł|PLN|EUR|USD|UAH|грн|€|\$)\b",
    "банковский счёт": r"\b(?:[A-Z]{2}\d{2}\s?)?(?:\d{2}\s?){6,}\d{2,}\b",
    "e-mail": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "телефон": r"(?:\+\d{1,3}[\s(-]*)?(?:\d[\d\s()-]{7,}\d)",
    "оператор оплаты": r"\b(Przelewy24|PayPro|Tpay|PayU|BLIK|Klarna|PayPo|Apple Pay|Google Pay|Stripe|Paynow)\b",
    "юр. идентификатор": r"\b(NIP|REGON|KRS|VAT[- ]?UE)\b[:\s]*[\dA-Z-]*",
    "ссылка на закон": r"\b(?:art\.|artyku[łl]\w*|§|ust\.|ustaw\w+|Kodeks\w*|RODO|GDPR|L\.\d{3}-\d+|стат\w+|ст\.)\s*[\w.§ -]{0,40}",
    "адрес": r"\b(?:ul\.|ulica|вул\.|str\.)\s*[^\n,;]{3,60}",
    "почтовый индекс": r"\b\d{2}-\d{3}\b",
    "курьер/доставка": r"\b(InPost|Paczkomat\w*|DPD|DHL|UPS|GLS|Poczta Polska|Nova Poshta|Нова Пошта|Meest|FedEx|Orlen Paczka)\b",
}

# Pages whose claims bind the shop; everything else is catalogue noise.
LEGAL_PAGES = {
    "terms-of-use", "privacy-policy", "polityka-cookies",
    "warranty-and-returns", "warranty-and-returns__polityka-zwrotow",
    "warranty-and-returns__gwarancja-na-produkt", "claims-and-complaints",
    "delivery-and-payment", "regulamin-kart-podarunkowych",
    "deklaracja-dostepnosci", "zgody-klauzule-i-regulamin-newslettera",
    "personal-data-requests", "contacts", "about", "index", "checkout",
}


def context(line, m, width=110):
    """Readable slice around a match, so a claim can be judged in place."""
    s = max(0, m.start() - width // 2)
    e = min(len(line), m.end() + width // 2)
    out = line[s:e].strip()
    return ("…" if s else "") + out + ("…" if e < len(line) else "")


def main():
    raw, out_path = sys.argv[1], sys.argv[2]
    claims = []
    for loc in LOCALES:
        d = os.path.join(raw, loc)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".txt"):
                continue
            slug = fn[:-4]
            if slug not in LEGAL_PAGES:
                continue
            for n, line in enumerate(
                    open(os.path.join(d, fn), encoding="utf-8").read().split("\n"), 1):
                line = line.strip()
                if len(line) < 3:
                    continue
                for kind, pat in PATTERNS.items():
                    for m in re.finditer(pat, line):
                        val = m.group(0).strip()
                        if kind == "телефон" and len(re.sub(r"\D", "", val)) < 9:
                            continue
                        if kind == "банковский счёт" and len(re.sub(r"\D", "", val)) < 16:
                            continue
                        claims.append({
                            "locale": loc, "page": slug, "line": n,
                            "kind": kind, "value": val, "context": context(line, m),
                        })

    # Group identical claim values so cross-locale drift is visible at a glance.
    by_kind = defaultdict(lambda: defaultdict(set))
    for c in claims:
        by_kind[c["kind"]][c["value"]].add(f'{c["locale"]}:{c["page"]}')

    json.dump(claims, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"утверждений найдено: {len(claims)}\n")
    for kind in PATTERNS:
        vals = by_kind.get(kind, {})
        if not vals:
            continue
        print(f"── {kind}: {len(vals)} различных значений, "
              f"{sum(len(v) for v in vals.values())} упоминаний")


if __name__ == "__main__":
    main()
