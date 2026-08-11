#!/usr/bin/env python3
"""Склеить правки, которые исполнитель закрывает одним действием.

Вход — план склеек: у каждой lead, члены и механизм («все строки в одном
языковом объекте», «один блок футера»). План предлагают агенты и проверяют
скептики, но в данные его переносит этот скрипт, а не модель: применение должно
быть дословным и повторяемым.

Ведущая правка забирает содержимое членов: «сейчас» и готовые тексты
складываются подписанными блоками, чтобы исполнитель видел каждую строку,
которую меняет. Члены помечаются merged_into и из документов уходят. Ответы
заказчика привязаны к номерам, поэтому ведущей становится правка, на которую
он уже ответил, — иначе ответ осиротеет.

Usage: python3 apply_merges.py <plan.json> <checklist.json>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_workorder import load_verdicts  # noqa: E402


def block(f, field):
    txt = (f.get(field) or "").strip()
    if not txt:
        return ""
    head = f"— {f['id']} · {(f.get('title') or '').strip()}"
    return head + "\n" + txt


def main():
    plan_path, cl_path = sys.argv[1], sys.argv[2]
    plan = json.load(open(plan_path, encoding="utf-8"))
    cl = json.load(open(cl_path, encoding="utf-8"))
    F = {f["id"]: f for g in cl["groups"] for f in g["fixes"]}
    verdicts = load_verdicts(cl_path)

    merged = kept = 0
    for c in plan["approved"]:
        ids = [m for m in c["members"] if m in F]
        if len(ids) < 2:
            continue
        # ответ заказчика важнее выбора агента: ведёт тот, на кого уже отвечено
        answered = [m for m in ids if verdicts.get(m, {}).get("v") == "ok"]
        lead_id = (answered[0] if answered
                   else c["lead"] if c["lead"] in ids else ids[0])
        rest = [m for m in ids if m != lead_id]
        lead = F[lead_id]

        lead["title"] = c["task_title"]
        lead["action"] = "Заменить — " + c["task_title"]
        lead["merge_mechanism"] = c["mechanism"]
        order = [lead_id] + rest
        for field in ("current", "pl", "ua", "en"):
            parts = [block(F[m], field) for m in order]
            parts = [p for p in parts if p]
            if parts:
                lead[field] = "\n\n".join(parts)
        heads = "\n".join(
            f"• {F[m]['id']} — {(F[m].get('title') or '').strip()}" for m in order)
        lead["why"] = (
            f"Одна работа вместо {len(order)}: {c['mechanism']}\n\n"
            f"Закрывает разом:\n{heads}\n\n"
            + "\n\n".join(
                f"[{F[m]['id']}] " + (F[m].get("why") or "").strip()
                for m in order if (F[m].get("why") or "").strip()))
        for m in rest:
            F[m]["merged_into"] = lead_id
            F[m]["merged_note"] = (
                f"Входит в задачу {lead_id}: {c['mechanism']}")
        merged += len(rest)
        kept += 1

    json.dump(cl, open(cl_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"склеек применено: {kept}, правок поглощено: {merged}")


if __name__ == "__main__":
    main()
