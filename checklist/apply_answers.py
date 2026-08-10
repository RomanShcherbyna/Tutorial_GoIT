#!/usr/bin/env python3
"""Write the client's nine answers into the eight documents.

The audit could not decide these from the text: what cash on delivery actually
costs, whether the free-delivery threshold is counted before or after a
discount, who carries parcels abroad, from which day the documents are in
force, and so on. The client answered, and the answers belong inside the
finished text — not in a list of open questions next to it.

Each edit below names the answer that caused it and prints what it replaced,
so the change is reviewable rather than a diff of a 259-block JSON file.
Running it twice changes nothing the second time.

Usage:  python3 apply_answers.py <translations.json> [checklist.json]
"""
import json
import re
import sys

# One date for all eight documents, equal to the day they go live. The store is
# not open yet, so a document dated 24.06.2026 claims to have been in force
# when there was no shop and no customer — a verifier checks that. This is the
# first edition, so the 14-day notice for changing terms does not apply: there
# is nobody bound by an earlier one.
#
# Move the launch and this one constant moves with it.
DATE = "01.09.2026"
OLD_DATE = "24.06.2026"
VERSION = {"pl": "wersja 1.0", "ua": "версія 1.0", "en": "version 1.0"}
IN_FORCE = {"pl": f"obowiązuje od dnia {DATE}",
            "ua": f"чинні з {DATE}",
            "en": f"in force from {DATE}"}

changes = []


def find(tr, doc_key, n):
    for d in tr["documents"]:
        if d["doc"] == doc_key:
            for b in d["blocks"]:
                if b["n"] == n:
                    return b
    raise KeyError(f"{doc_key} блок {n}")


def edit(tr, doc_key, n, answer, **repl):
    """Replace text in one block, one language at a time."""
    b = find(tr, doc_key, n)
    for lang, (old, new) in repl.items():
        cur = b.get(lang) or ""
        # Test for the result before testing for the source: several of these
        # edits extend a phrase rather than swap it, so the old text is still a
        # substring of the new one and a second run would append twice.
        if new and new in cur:
            continue
        if old not in cur:
            changes.append((answer, doc_key, n, lang, "НЕ НАЙДЕНО", old))
            continue
        b[lang] = cur.replace(old, new)
        changes.append((answer, doc_key, n, lang, old, new))


def main():
    tr_path = sys.argv[1]
    tr = json.load(open(tr_path, encoding="utf-8"))

    # 1 — cash on delivery is 23 zł, not a range. A delivery price has to be
    #     exact before the order is placed; a range fails manual verification.
    for doc, n in (("1-regulamin-sklepu", 43), ("6-dostawa-i-platnosci", 4)):
        edit(tr, doc, n, "1 · наложенный платёж 23 zł",
             pl=("+20–23 zł", "+23 zł"),
             ua=("+20–23 zł", "+23 zł"),
             en=("+20–23 zł", "+23 zł"))

    # 2 — the 500 zł threshold is the cart after discounts. Left unsaid, the
    #     shop and the customer count a promo code differently.
    edit(tr, "1-regulamin-sklepu", 46, "2 · порог 500 zł после скидки",
         pl=("o wartości od 500 zł",
             "o wartości od 500 zł, liczonej od wartości koszyka "
             "po uwzględnieniu rabatów"),
         ua=("вартістю від 500 zł",
             "вартістю від 500 zł, що рахується від вартості кошика "
             "після врахування знижок"),
         en=("with a value from 500 zł",
             "with a value from 500 zł, counted from the cart value after "
             "discounts have been applied"))
    edit(tr, "6-dostawa-i-platnosci", 7, "2 · порог 500 zł после скидки",
         pl=("z góry od 500 zł",
             "z góry od 500 zł, liczonych od wartości koszyka po "
             "uwzględnieniu rabatów"),
         ua=("наперед, від 500 zł",
             "наперед, від 500 zł, що рахуються від вартості кошика після "
             "врахування знижок"),
         en=("in advance from 500 zł",
             "in advance from 500 zł, counted from the cart value after "
             "discounts have been applied"))

    # 3 — abroad is DHL. Block 6 already said DHL while block 11 offered Nova
    #     Poshta and Meest for Ukraine; the answer resolves it in DHL's favour,
    #     so the other two carriers leave the text.
    edit(tr, "6-dostawa-i-platnosci", 11, "3 · за границу только DHL",
         pl=(" Dla Ukrainy dostępne są Nova Poshta oraz Meest.", ""),
         ua=(" Для України доступні Nova Poshta та Meest.", ""),
         en=(" For Ukraine, Nova Poshta and Meest are available.", ""))

    # 4 + 5 — one date on all eight, equal to publication day.
    for doc, n in (("1-regulamin-sklepu", 2), ("2-polityka-prywatnosci", 1),
                   ("3-polityka-cookies", 1),
                   ("4-polityka-zwrotow-i-reklamacji", 1),
                   ("5-zgody-i-newsletter", 1),
                   ("7-regulamin-kart-podarunkowych", 1)):
        b = find(tr, doc, n)
        for lang in ("pl", "ua", "en"):
            cur = b.get(lang) or ""
            if OLD_DATE not in cur:
                continue
            new = cur.replace(OLD_DATE, DATE)
            if VERSION[lang] not in new:
                new += f" · {VERSION[lang]}"
            changes.append(("4+5 · одна дата на все документы",
                            doc, n, lang, cur, new))
            b[lang] = new

    # The delivery document had no date at all — it gets the same line.
    b = find(tr, "6-dostawa-i-platnosci", 1)
    for lang in ("pl", "ua", "en"):
        cur = b.get(lang) or ""
        if DATE in cur:
            continue
        new = f"{cur} · {IN_FORCE[lang]} · {VERSION[lang]}"
        changes.append(("4 · дата для документа о доставке",
                        "6-dostawa-i-platnosci", 1, lang, cur, new))
        b[lang] = new

    # The accessibility statement words its date differently but shares it.
    for n in (1, 10):
        b = find(tr, "8-deklaracja-dostepnosci", n)
        for lang in ("pl", "ua", "en"):
            cur = b.get(lang) or ""
            if OLD_DATE not in cur:
                continue
            changes.append(("5 · одна дата на все документы",
                            "8-deklaracja-dostepnosci", n, lang, cur,
                            cur.replace(OLD_DATE, DATE)))
            b[lang] = cur.replace(OLD_DATE, DATE)

    # 8 — both marketing consents stay. As written they read as the same
    #     permission twice; naming the channels tells them apart, so a customer
    #     ticking one knows what the other is for.
    edit(tr, "5-zgody-i-newsletter", 9, "8 · два согласия, разведены по каналам",
         pl=("informacji marketingowych drogą elektroniczną (e-mail),",
             "informacji marketingowych drogą elektroniczną — e-mail i SMS — "
             "w rozumieniu art. 10 ustawy o świadczeniu usług drogą "
             "elektroniczną,"),
         ua=("маркетингової інформації електронними засобами "
             "(електронною поштою)",
             "маркетингової інформації електронними засобами — електронною "
             "поштою та SMS — у розумінні ст. 10 закону про надання послуг "
             "електронними засобами"),
         en=("marketing information by electronic means (e-mail),",
             "marketing information by electronic means — e-mail and SMS — "
             "within the meaning of art. 10 of the Act on providing services "
             "by electronic means,"))

    # 9 — hello@ and rodo@ are the working addresses, and they are already in
    #     the text. What has to go is the editor's aside: a customer should not
    #     be reading a note about aliases we might set up one day.
    edit(tr, "1-regulamin-sklepu", 16, "9 · убрать редакторскую пометку",
         pl=(" (opcjonalnie alias zwroty@/reklamacje@)", ""),
         ua=(" (опційно аліас zwroty@/reklamacje@)", ""),
         en=(" (optionally the alias zwroty@/reklamacje@)", ""))

    json.dump(tr, open(tr_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # 7 — fourteen days. The task to fix the strip of promises already existed
    #     but carried no replacement text, because the audit did not know
    #     whether the longer term was a mistake or a deliberate offer.
    if len(sys.argv) > 2:
        cl_path = sys.argv[2]
        cl = json.load(open(cl_path, encoding="utf-8"))
        text = {"pl": "Zwrot w ciągu 14 dni",
                "ua": "Повернення протягом 14 днів",
                "en": "14-day returns"}
        hit = touched = 0
        for g in cl["groups"]:
            for f in g["fixes"]:
                if f["id"] != "DOC-09":
                    continue
                hit += 1
                if all(f.get(k) == v for k, v in text.items()):
                    continue
                f.update(text)
                touched += 1
                changes.append(("7 · срок возврата 14 дней", "checklist",
                                "DOC-09", "pl,ua,en",
                                "текста на замену не было",
                                " / ".join(text.values())))
        # 9 — the audit wrote its replacement texts against the documents as
        #     they arrived, where returns went to kontakt@. Only hello@ and
        #     rodo@ exist, so any text a developer is told to paste has to say
        #     so. The "why" and the quoted current state keep the old address:
        #     that is a description of what was found, not an instruction.
        mails = 0
        for g in cl["groups"]:
            for f in g["fixes"]:
                for k in ("pl", "ua", "en"):
                    v = f.get(k) or ""
                    if "kontakt@lapetitebloom.com" in v:
                        f[k] = v.replace("kontakt@lapetitebloom.com",
                                         "hello@lapetitebloom.com")
                        mails += 1
                        touched += 1
        if mails:
            changes.append(("9 · почта hello@ и rodo@", "checklist",
                            "тексты на вставку", "pl,ua,en",
                            "kontakt@lapetitebloom.com",
                            f"hello@lapetitebloom.com ({mails} строк)"))

        # The task that asked to resolve the conflict is the conflict's answer
        # now; left as it was, it would send a developer looking for kontakt@.
        for g in cl["groups"]:
            for f in g["fixes"]:
                if f["id"] != "DOC-16":
                    continue
                new_action = ("Свести почту к двум адресам: hello@ для заказов, "
                              "возвратов и рекламаций, rodo@ для персональных "
                              "данных")
                if f.get("action") == new_action:
                    continue
                f["action"] = new_action
                # "title" is what the document prints as «Где»; leaving the old
                # wording there would put the resolved conflict back on screen.
                f["title"] = ("Контакты в шапке, в подвале, на странице "
                              "контактов, в письмах и во всех документах")
                f["why"] = ("Решено: работают только hello@lapetitebloom.com и "
                            "rodo@lapetitebloom.com. Документы приведены к ним, "
                            "на сайте должны быть ровно эти два адреса и "
                            "никаких других. Адрес, по которому отзывают "
                            "согласие и подают запрос по GDPR, обязан "
                            "существовать и отвечать.")
                touched += 1
                changes.append(("9 · почта hello@ и rodo@", "checklist",
                                "DOC-16", "—",
                                "«документы требуют kontakt@ и rodo@»",
                                new_action))

        if touched:
            json.dump(cl, open(cl_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
        if not hit:
            print("!! DOC-09 не найден в чек-листе")

    missing = [c for c in changes if c[4] == "НЕ НАЙДЕНО"]
    print(f"правок внесено: {len(changes) - len(missing)}")
    if missing:
        print(f"НЕ НАЙДЕНО: {len(missing)}")
        for a, doc, n, lang, _, old in missing:
            print(f"   [{a}] {doc} блок {n} {lang}: {old[:60]}")
    last = None
    for a, doc, n, lang, old, new in changes:
        if a == "НЕ НАЙДЕНО" or old == "НЕ НАЙДЕНО":
            continue
        if a != last:
            print(f"\n{a}")
            last = a
        print(f"   {doc} блок {n} [{lang}]")
        print(f"      было:  {old[:110]}")
        print(f"      стало: {new[:110]}")


if __name__ == "__main__":
    main()
