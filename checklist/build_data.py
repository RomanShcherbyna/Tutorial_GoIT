#!/usr/bin/env python3
"""Turn the audit findings (and later the client's documents) into the task
list the checklist app serves.

The audit is written for a reader; a checklist is worked through. So each
finding becomes a task with the one thing a developer needs to act — where it
is, what is wrong, and the exact replacement text — and the ordering follows
what has to ship first, not what was found first.

Usage:  python3 build_data.py <findings.json> <out.json> [claims.json]
"""
import json
import os
import re
import sys
from collections import OrderedDict

# Which audit slice a finding came from, in words a person can act on.
AREAS = OrderedDict([
    ("19", ("Юридические реквизиты", "Данные продавца: контакты, футер, регламент, чекаут")),
    ("04", ("Доставка и оплата", "Страница /delivery-and-payment — её смотрит Przelewy24")),
    ("05", ("Возвраты и гарантия", "Условия возврата, гарантия, рекламации")),
    ("06", ("Регламент и приватность", "Regulamin, polityka prywatności, cookies")),
    ("07", ("Служебные юр. страницы", "Newsletter, подарочные карты, доступность, GDPR-запросы")),
    ("02", ("Шапка, меню и футер", "Сквозные элементы — видны на каждой странице")),
    ("01", ("Главная", "Баннеры, слайдеры, подборки")),
    ("12", ("Корзина и оформление заказа", "Путь до оплаты")),
    ("11", ("Карточка товара", "Шаблон карточки — умножается на 1307 товаров")),
    ("09", ("Категории", "Заголовки, описания, листинги")),
    ("10", ("Фильтры и атрибуты", "Значения цветов, размеров — правятся в каталоге")),
    ("13", ("Аккаунт и поиск", "Вход, регистрация, избранное, поиск")),
    ("03", ("Контакты и о бренде", "/contacts и /about")),
    ("08", ("Блог", "9 записей, из них 7 — рыба")),
    ("14", ("Системные строки", "UI движка, страницы ошибок, SEO-теги")),
])

SEV_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
SEV_LABEL = {"blocker": "Блокер", "high": "Критично",
             "medium": "Средне", "low": "Мелочь"}
ISSUE_LABEL = {
    "STUB": "Заглушка", "MISSING": "Нет перевода", "WRONG": "Кривой перевод",
    "LEFTOVER": "Чужой язык", "TYPO": "Опечатка", "LEGAL": "Юр. требование",
    "BROKEN": "Битая ссылка",
}

# Where a developer actually goes to change this kind of thing.
def where_to_fix(f):
    path, issue = f.get("path", ""), f.get("issue")
    note = (f.get("note") or "").strip()
    if note:
        return note
    if issue == "BROKEN":
        return "Шаблон или настройки — поправить ссылку/маршрут"
    if path.startswith("/blog"):
        return "Админка → Блог → запись"
    if f.get("agent") == "10":
        return "Админка → Каталог → атрибуты и их значения"
    if f.get("agent") in ("02", "14"):
        return "Админка → Переводы интерфейса, либо шаблон темы"
    if path and path != "/":
        return f"Админка → Страницы → {path}"
    return "Админка → Главная / настройки витрины"


LOCALE_URL = {"pl": "https://lapetitebloom.com{}",
              "ua": "https://lapetitebloom.com/ua{}",
              "en": "https://lapetitebloom.com/en{}"}


def urls(path):
    if not path or not path.startswith("/"):
        return {}
    p = "" if path == "/" else path
    return {k: v.format(p) for k, v in LOCALE_URL.items()}


def main():
    findings_path, out_path = sys.argv[1], sys.argv[2]
    claims_path = sys.argv[3] if len(sys.argv) > 3 else None

    findings = json.load(open(findings_path, encoding="utf-8"))
    tasks = []
    for f in findings:
        agent = f.get("agent", "")
        area, area_desc = AREAS.get(agent, ("Прочее", ""))
        tasks.append({
            "id": f["id"],
            "source": "audit",
            "area": area,
            "area_desc": area_desc,
            "severity": f["severity"],
            "severity_label": SEV_LABEL.get(f["severity"], f["severity"]),
            "issue": f["issue"],
            "issue_label": ISSUE_LABEL.get(f["issue"], f["issue"]),
            "locale": f.get("locale", "all"),
            "path": f.get("path", ""),
            "urls": urls(f.get("path", "")),
            "block": f.get("block", ""),
            "current": f.get("current", ""),
            "why": f.get("why", ""),
            "pl": f.get("pl", ""),
            "ua": f.get("ua", ""),
            "en": f.get("en", ""),
            "where": where_to_fix(f),
        })

    tasks.sort(key=lambda t: (SEV_ORDER.get(t["severity"], 4),
                              list(AREAS.values()).index(
                                  (t["area"], t["area_desc"]))
                              if (t["area"], t["area_desc"]) in AREAS.values()
                              else 99,
                              t["id"]))

    areas = []
    for code, (name, desc) in AREAS.items():
        got = [t for t in tasks if t["area"] == name]
        if got:
            areas.append({
                "name": name, "desc": desc, "count": len(got),
                "blockers": sum(1 for t in got if t["severity"] == "blocker"),
            })

    data = {
        "generated_from": os.path.basename(findings_path),
        "total": len(tasks),
        "areas": areas,
        "severities": [
            {"key": k, "label": SEV_LABEL[k],
             "count": sum(1 for t in tasks if t["severity"] == k)}
            for k in ("blocker", "high", "medium", "low")
        ],
        "issues": sorted(
            ({"key": k, "label": ISSUE_LABEL.get(k, k),
              "count": sum(1 for t in tasks if t["issue"] == k)}
             for k in {t["issue"] for t in tasks}),
            key=lambda d: -d["count"]),
        "tasks": tasks,
        "claims": [],
    }

    if claims_path and os.path.exists(claims_path):
        claims = json.load(open(claims_path, encoding="utf-8"))
        # Only the claims that differ between locales are worth a developer's
        # attention; the rest are consistent and need no decision.
        by_val = {}
        for c in claims:
            by_val.setdefault((c["kind"], c["value"]), set()).add(c["locale"])
        odd = [{"kind": k, "value": v, "locales": sorted(locs)}
               for (k, v), locs in by_val.items() if len(locs) < 3]
        data["claims"] = sorted(odd, key=lambda d: (d["kind"], d["value"]))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(data, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"задач: {len(tasks)} | разделов: {len(areas)} | "
          f"расхождений между локалями: {len(data['claims'])}")


if __name__ == "__main__":
    main()
