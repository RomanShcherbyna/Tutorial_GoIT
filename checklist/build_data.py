#!/usr/bin/env python3
"""Turn the audit findings and the document tasks into the checklist the team
works from.

Grouped by page, not by finding. 334 separate ticks is a wall nobody starts
climbing; "fix this page, it has 16 things wrong with it" is a morning's work.
So a page is the unit of progress, and the individual fixes live inside it.

Findings that repeat across a whole class of pages — the product card template,
the filter sidebar, anything site-wide — are collapsed into one entry that says
how many pages it touches, because fixing them is one edit, not a thousand.

Usage:  python3 build_data.py <findings.json> <out.json> [claims.json] [doc_tasks.json]
"""
import json
import os
import re
import sys
from collections import OrderedDict

SEV_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
SEV_LABEL = {"blocker": "Блокер", "high": "Критично",
             "medium": "Средне", "low": "Мелочь"}
ISSUE_LABEL = {
    "STUB": "Заглушка", "MISSING": "Нет перевода", "WRONG": "Кривой перевод",
    "LEFTOVER": "Чужой язык", "TYPO": "Опечатка", "LEGAL": "Юр. требование",
    "BROKEN": "Битая ссылка", "PUBLISH": "Выложить документ",
    "CONFLICT": "Расходится с документом", "DEV": "Доработка", "REMOVE": "Убрать",
}

# Human names for the pages the team will recognise.
PAGE_TITLES = {
    "/": "Главная",
    "/contacts": "Контакты",
    "/about": "О бренде",
    "/delivery-and-payment": "Доставка и оплата",
    "/terms-of-use": "Регламент магазина",
    "/privacy-policy": "Политика конфиденциальности",
    "/polityka-cookies": "Политика cookies",
    "/warranty-and-returns": "Возвраты и гарантия",
    "/warranty-and-returns/polityka-zwrotow": "Политика возвратов",
    "/warranty-and-returns/gwarancja-na-produkt": "Гарантия на товар",
    "/claims-and-complaints": "Рекламации",
    "/zgody-klauzule-i-regulamin-newslettera": "Согласия и newsletter",
    "/regulamin-kart-podarunkowych": "Подарочные карты",
    "/deklaracja-dostepnosci": "Декларация доступности",
    "/personal-data-requests": "Запросы по GDPR",
    "/checkout": "Оформление заказа",
    "/cart": "Корзина",
    "/search": "Поиск",
    "/favorites": "Избранное",
    "/auth/login": "Вход",
    "/auth/register": "Регистрация",
    "/blog": "Блог — список",
    "/brands": "Бренды — список",
    "/special-offers": "Акции",
}

# Groups that are one fix applied to many pages.
TEMPLATES = OrderedDict([
    ("__global__", ("Сквозные элементы", "Шапка, меню, футер, попап языка, "
                    "панель фильтров — видно на каждой странице сайта")),
    ("__product__", ("Карточка товара — шаблон", "Одна правка расходится "
                     "на все 1307 карточек")),
    ("__category__", ("Категории — шаблон", "Листинг, сортировки, бейджи, "
                      "пустые состояния — общие для 108 категорий")),
    ("__filters__", ("Фильтры и атрибуты", "Правятся в каталоге, а не в "
                     "тексте страниц: значения цветов, размеров, «Artykuł»")),
    ("__blogpost__", ("Блог — записи", "7 записей из 9 — рыба на латыни")),
    ("__system__", ("Системные строки и SEO", "Строки движка, страницы ошибок, "
                    "title/description, hreflang")),
])

LOCALE_RE = re.compile(r"^/(?:ua|en)(?=/|$)")

# Left out of the working list on the client's instruction: the blog is still
# placeholder text and is not being fixed in this pass. Reported, not silently
# dropped, so nobody assumes it was overlooked.
EXCLUDED_KEYS = {"__blogpost__", "/blog"}
EXCLUDED_REASON = ("Блог сейчас целиком на заглушках и в эту итерацию не входит "
                   "— по решению заказчика.")


def norm_path(raw):
    """One finding may name several pages or a locale-prefixed one."""
    if not raw:
        return ""
    first = raw.split(",")[0].strip()
    first = LOCALE_RE.sub("", first) or "/"
    first = first.split("?")[0].rstrip("/") or "/"
    return first


def classify(f, path):
    """Which bucket a finding belongs to — a real page or a template."""
    agent = f.get("agent", "")
    raw = (f.get("path") or "").strip()

    if raw == "*" or agent in ("02",):
        return "__global__"
    if agent == "14":
        return "__system__"
    if agent == "10":
        return "__filters__"
    if path.startswith("/blog/"):
        return "__blogpost__"
    if agent == "11":
        return "__product__"
    if agent == "09" and path not in PAGE_TITLES:
        return "__category__"
    if not path:
        return "__global__"
    return path


def urls(path):
    if not path.startswith("/"):
        return {}
    p = "" if path == "/" else path
    return {"pl": f"https://lapetitebloom.com{p}",
            "ua": f"https://lapetitebloom.com/ua{p}",
            "en": f"https://lapetitebloom.com/en{p}"}


def where_to_fix(f):
    note = (f.get("note") or "").strip()
    if note:
        return note
    agent, path = f.get("agent", ""), f.get("path", "")
    if f.get("issue") == "BROKEN":
        return "Шаблон или маршруты — поправить ссылку"
    if agent == "10":
        return "Админка → Каталог → атрибуты и их значения"
    if agent in ("02", "14"):
        return "Админка → Переводы интерфейса, либо шаблон темы"
    if path.startswith("/blog"):
        return "Админка → Блог → запись"
    if path and path.startswith("/"):
        return f"Админка → Страницы → {path}"
    return "Админка → настройки витрины"


def fix_from_finding(f):
    return {
        "id": f["id"],
        "source": "audit",
        "severity": f["severity"],
        "severity_label": SEV_LABEL.get(f["severity"], f["severity"]),
        "issue": f["issue"],
        "issue_label": ISSUE_LABEL.get(f["issue"], f["issue"]),
        "locale": f.get("locale", "all"),
        "title": f.get("block") or f.get("why") or f.get("issue"),
        "current": f.get("current", ""),
        "why": f.get("why", ""),
        "pl": f.get("pl", ""), "ua": f.get("ua", ""), "en": f.get("en", ""),
        "where": where_to_fix(f),
        "steps": [], "done_when": "", "note": "",
    }


def fix_from_doc_task(t):
    return {
        "id": t["id"],
        "source": "document",
        "severity": t.get("severity", "medium"),
        "severity_label": SEV_LABEL.get(t.get("severity", "medium"), ""),
        "issue": t.get("kind", "DEV"),
        "issue_label": ISSUE_LABEL.get(t.get("kind", "DEV"), t.get("kind", "")),
        "locale": "all",
        "title": t.get("title", ""),
        "current": t.get("current", ""),
        "why": t.get("target", ""),
        "pl": "", "ua": "", "en": "",
        "where": t.get("doc", ""),
        "steps": t.get("steps", []),
        "done_when": t.get("done_when", ""),
        "note": t.get("note", ""),
    }


def main():
    findings_path, out_path = sys.argv[1], sys.argv[2]
    claims_path = sys.argv[3] if len(sys.argv) > 3 else None
    doctasks_path = sys.argv[4] if len(sys.argv) > 4 else None

    buckets = OrderedDict()

    def bucket(key, title, desc, path=""):
        if key not in buckets:
            buckets[key] = {"key": key, "title": title, "desc": desc,
                            "path": path, "urls": urls(path) if path else {},
                            "fixes": []}
        return buckets[key]

    for f in json.load(open(findings_path, encoding="utf-8")):
        path = norm_path(f.get("path", ""))
        key = classify(f, path)
        if key in TEMPLATES:
            title, desc = TEMPLATES[key]
            bucket(key, title, desc)["fixes"].append(fix_from_finding(f))
        else:
            title = PAGE_TITLES.get(key, key)
            bucket(key, title, "", key)["fixes"].append(fix_from_finding(f))

    if doctasks_path and os.path.exists(doctasks_path):
        for t in json.load(open(doctasks_path, encoding="utf-8")):
            path = norm_path(t.get("path", ""))
            key = path if path else "__docs__"
            if key == "__docs__":
                b = bucket(key, "Публикация документов",
                           "Выложить документы заказчика и убрать старые страницы")
            else:
                b = bucket(key, PAGE_TITLES.get(key, key), "", key)
            b["fixes"].append(fix_from_doc_task(t))

    # Order: worst first, then by how much is wrong.
    for b in buckets.values():
        b["fixes"].sort(key=lambda x: (SEV_ORDER.get(x["severity"], 4), x["id"]))
        b["count"] = len(b["fixes"])
        b["blockers"] = sum(1 for x in b["fixes"] if x["severity"] == "blocker")
        b["worst"] = min((SEV_ORDER.get(x["severity"], 4) for x in b["fixes"]),
                         default=4)
        b["from_documents"] = sum(1 for x in b["fixes"]
                                  if x["source"] == "document")

    excluded = [b for b in buckets.values() if b["key"] in EXCLUDED_KEYS]
    groups = sorted((b for b in buckets.values() if b["key"] not in EXCLUDED_KEYS),
                    key=lambda b: (b["worst"], -b["blockers"], -b["count"]))

    all_fixes = [x for b in groups for x in b["fixes"]]
    data = {
        "total_pages": len(groups),
        "total_fixes": len(all_fixes),
        "severities": [
            {"key": k, "label": SEV_LABEL[k],
             "count": sum(1 for x in all_fixes if x["severity"] == k)}
            for k in ("blocker", "high", "medium", "low")
        ],
        "issues": sorted(
            ({"key": k, "label": ISSUE_LABEL.get(k, k),
              "count": sum(1 for x in all_fixes if x["issue"] == k)}
             for k in {x["issue"] for x in all_fixes}),
            key=lambda d: -d["count"]),
        "groups": groups,
        "excluded": {
            "reason": EXCLUDED_REASON,
            "pages": [{"title": b["title"], "count": b["count"]} for b in excluded],
            "fixes": sum(b["count"] for b in excluded),
        },
        "claims": [],
    }

    if claims_path and os.path.exists(claims_path):
        by_val = {}
        for c in json.load(open(claims_path, encoding="utf-8")):
            by_val.setdefault((c["kind"], c["value"]), set()).add(c["locale"])
        data["claims"] = sorted(
            ({"kind": k, "value": v, "locales": sorted(locs)}
             for (k, v), locs in by_val.items() if len(locs) < 3),
            key=lambda d: (d["kind"], d["value"]))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(data, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"страниц/групп: {len(groups)} | правок внутри: {len(all_fixes)} | "
          f"исключено (блог): {data['excluded']['fixes']} | "
          f"расхождений между локалями: {len(data['claims'])}\n")
    for b in groups[:14]:
        print(f"  {b['title'][:46]:<48} {b['count']:>3} правок  "
              f"блокеров: {b['blockers']}")


if __name__ == "__main__":
    main()
