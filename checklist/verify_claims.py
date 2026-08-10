#!/usr/bin/env python3
"""Сверить каждую правку с исходником страницы, а не с пересказом.

Дважды подряд правка описывала то, чего на странице нет: строку из языкового
файла приписали не тому полю. Оба раза это ловилось одним движением — взять
цитату из поля «сейчас» и поискать её в сохранённой странице. Скрипт делает это
для всех правок разом.

Что он умеет и чего не умеет. Он отвечает на один вопрос: встречается ли
процитированный текст на странице, к которой правка привязана. «Да» не означает,
что правка верна по существу, — строка может быть на месте, а вывод из неё
неправильным (ровно так было с 13-18). «Нет» означает, что цитата не найдена, и
это всегда повод посмотреть глазами: либо страница изменилась, либо цитаты
никогда там не было.

Usage:  python3 verify_claims.py <checklist.json> <raw_dir> [out.json]
"""
import html
import json
import os
import re
import sys
import unicodedata

LANGS = ("pl", "ua", "en")

# Адрес страницы → имя файла в снимке: тот же слуг, слэши сложены в два
# подчёркивания, как их сложил обходчик.
def slug_for(path):
    p = (path or "").strip("/")
    return (p.replace("/", "__") or "index")


# Часть правок висит не на странице, а на шаблоне или на сквозном элементе.
# Им сопоставлены страницы, где этот элемент виден.
CATEGORIES = ["kids", "boys", "girls", "footwear", "zabawki", "niemowleta",
              "accessories", "pielegnacja-i-kosmetyki"]
PRODUCTS = ["myszka-maileg-baby-w-sukience-pudrowy-17-6000-00",
            "koszulka-bobo-choses-booo-z-nadrukiem-dla-dzieci-b226ac017-2-3",
            "krem-pod-oczy-skin-minimalism-eye-revival-pielegnacja-okolic-oczu-sm-eye-revival",
            "little-dutch-kocyk-muslinowy-fairy-blossom-110x140-letni-kocyk-te12194031",
            "sol-do-kapieli-dresdner-essenz-badz-zdrow-neuro-na-katar-50-g-3-bz-katar-50",
            "trampki-veja-small-volley-atlantic-ouro-bark-zlote-sportowe-buty-ve-smallvolb",
            "sukienka-dziewczeca-robee-niebieska-paski-falbanka-wygodna-ta-dziewcze-cc30042"]

GROUP_PAGES = {
    "__global__": ["index", "kids", "auth__register", "checkout", "contacts",
                   "cart", "search"] + PRODUCTS[:2],
    "__filters__": CATEGORIES,
    "__product__": PRODUCTS,
    "__category__": CATEGORIES,
    "__system__": ["index", "kids", "auth__register", "search"] + PRODUCTS[:2],
    "__docs__": [],          # правки о документах, страниц у них нет
}


def visible_text(raw):
    """Текст страницы без разметки, но со значениями атрибутов.

    Половина спорных строк живёт в placeholder, title и alt — выбрасывать
    атрибуты значит не найти ровно то, что чаще всего и цитируют.
    """
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    t = re.sub(r"<[^>]+>", " ", t)
    return norm(html.unescape(t))


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    # Типографика на странице и в правке расходится сама по себе: кавычки,
    # тире, неразрывные пробелы. Для поиска это шум.
    for a, b in ((" ", " "), ("’", "'"), ("‘", "'"),
                 ("“", '"'), ("”", '"'), ("„", '"'),
                 ("–", "-"), ("—", "-"), ("−", "-"),
                 ("…", "..."), ("„", '"'), ("«", '"'), ("»", '"')):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip().lower()


QUOTED = re.compile(r'["«„”“](.{6,200}?)["»”“]')
PREFIXED = re.compile(r'(?m)^\s*(?:pl|ua|en)\s*:\s*(.{6,200})$')


def quotes_from(current):
    """Вытащить из поля «сейчас» то, что можно искать буквально.

    Поле пишут по-разному: то одной строкой, то «pl: … | ua: …», то прозой с
    цитатами внутри. Берём кавычки и строки с языковым префиксом, а если ни
    того ни другого нет — само поле, если оно похоже на цитату, а не на
    рассуждение.
    """
    out = []
    for m in QUOTED.finditer(current):
        out.append(m.group(1))
    for m in PREFIXED.finditer(current):
        out.append(m.group(1))
    if not out:
        for part in re.split(r"\s*\|\s*|\n", current):
            part = part.strip()
            part = re.sub(r"^(?:pl|ua|en)\s*:\s*", "", part)
            if 8 <= len(part) <= 200 and not part.endswith(":"):
                out.append(part)
    # Одна правка часто цитирует не одну строку, а перечень: пункты меню,
    # варианты сортировки, четыре подписи разом. Целиком такой перечень на
    # странице не встретится никогда — искать надо каждый пункт отдельно.
    parts = []
    for q in out:
        pieces = re.split(r"\s+…\s+|\s+/\s+|\s*\|\s*|\s*;\s*", q)
        parts.extend(pieces if len(pieces) > 1 else [q])
    # Слишком короткие куски находятся где угодно и ничего не доказывают.
    return [q.strip(" .,;—-") for q in parts if len(q.strip()) >= 8]


def найдено(quote, pair):
    """Где нашлось: на виду, в разметке — или нигде."""
    q = norm(quote)
    text, source = pair
    for label, hay in (("текст", text), ("разметка", source)):
        # Обходчик иногда режет строку по-своему: пробуем начало, чтобы не
        # объявлять пропажей то, что просто иначе разбито.
        if q in hay or (len(q) > 40 and q[:40] in hay):
            return label
    return ""


def main():
    cl_path, raw_dir = sys.argv[1], sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else ""
    cl = json.load(open(cl_path, encoding="utf-8"))

    # Тексты страниц по языкам, читаются один раз.
    pages = {}
    for lang in LANGS:
        d = os.path.join(raw_dir, lang)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.endswith(".html"):
                continue
            raw = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
            # Два взгляда на одну страницу. Текст — то, что видит покупатель.
            # Исходник — то, что видит правка: половина цитат живёт в
            # placeholder, в classе или прямо в языковом объекте внутри
            # <script>, и по видимому тексту их не найти.
            pages[(lang, f[:-5])] = (visible_text(raw), norm(html.unescape(raw)))

    report = []
    for g in cl["groups"]:
        key, path = g.get("key", ""), g.get("path")
        names = GROUP_PAGES.get(key)
        if names is None:
            names = [slug_for(path)] if path else []
        for f in g["fixes"]:
            current = (f.get("current") or "").strip()
            langs = [l for l in LANGS if l in (f.get("locale") or "pl,ua,en")] or list(LANGS)
            row = {"id": f["id"], "page": g["title"], "severity": f["severity"],
                   "title": f.get("title", "")[:90], "langs": langs}
            if not current:
                row["verdict"] = "нечего искать"
                report.append(row)
                continue
            quotes = quotes_from(current)
            if not quotes:
                row["verdict"] = "цитаты нет"
                report.append(row)
                continue
            hits, misses = [], []
            for q in quotes[:10]:
                where = []
                for l in langs:
                    for n in names:
                        if (l, n) not in pages:
                            continue
                        got = найдено(q, pages[(l, n)])
                        if got:
                            where.append(f"{l}/{n} ({got})")
                (hits if where else misses).append({"q": q[:90], "где": where[:3]})
            row["verdict"] = ("подтверждено" if hits and not misses
                              else "частично" if hits else "не найдено")
            row["найдено"], row["не найдено"] = hits, misses
            row["страницы"] = names[:4]
            report.append(row)

    counts = {}
    for r in report:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{v:5}  {k}")
    if out_path:
        json.dump(report, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("отчёт:", out_path)


if __name__ == "__main__":
    main()
