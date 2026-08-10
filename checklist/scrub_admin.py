#!/usr/bin/env python3
"""Strip admin-panel navigation from everything we hand over.

The client does not want the delivery to show that we looked inside the shop's
admin panel — developers know their own tooling. So "Админка → Слайдеры → …"
comes out, along with any mention of the crawl running under an administrator
session.

The cut is surgical, not a search for the word "админ": one legal term looks
almost identical and must survive untouched — "Administrator danych" /
"администратор данных" / "контролер даних" / "data controller" is the GDPR
controller, not a control panel.

Usage:  python3 scrub_admin.py <file> [<file> ...]
"""
import json
import os
import re
import sys

# Navigation trails: "Админка → X → Y." up to the sentence end.
NAV = re.compile(
    r"(?:В\s+)?[Аа]дмин(?:ка|ке|ку|панел\w*)\s*(?:→|->|:)?[^.;!?\n]*[.;]?\s*")
# Bare references that survive once the trail is gone.
LEFTOVER = re.compile(
    r"\s*\(?(?:в\s+)?[Аа]дмин(?:ке|ку|ка|панели)\)?\s*", re.U)
SESSION = re.compile(
    r"[^.]*?(?:под\s+)?сесси(?:ей|ю|я)\s+администратора[^.]*\.\s*", re.U)
# Drop the whole clause, not just the path — "Вход в  и проверка" reads as a bug.
ACP = re.compile(r"[^.;\n]*/acp(?:/[\w-]+)*[^.;\n]*[.;]?\s*")

# Never touch these — they are the GDPR controller, not the admin panel.
PROTECTED = re.compile(
    r"[Aa]dministrator(?:em|owi|a)?\s+danych|"
    r"[Аа]дминистратор\w*\s+(?:данных|персональных)|"
    r"[Кк]онтролер\w*\s+даних|[Dd]ata\s+controller", re.U)


def scrub_text(s):
    if not s:
        return s
    keep = {}

    def stash(m):
        token = f"\x00{len(keep)}\x00"
        keep[token] = m.group(0)
        return token

    s = PROTECTED.sub(stash, s)
    s = SESSION.sub("", s)
    s = NAV.sub("", s)
    s = LEFTOVER.sub(" ", s)
    s = ACP.sub(" ", s)
    for token, original in keep.items():
        s = s.replace(token, original)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"^\s*[—–-]\s*", "", s)
    return s.strip()


def scrub_json(path):
    data = json.load(open(path, encoding="utf-8"))
    n = [0]

    def walk(node):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if isinstance(v, str):
                    new = scrub_text(v)
                    if new != v:
                        node[k] = new
                        n[0] += 1
                else:
                    walk(v)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                if isinstance(v, str):
                    new = scrub_text(v)
                    if new != v:
                        node[i] = new
                        n[0] += 1
                else:
                    walk(v)

    walk(data)
    json.dump(data, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return n[0]


def scrub_plain(path):
    s = open(path, encoding="utf-8").read()
    out = "\n".join(scrub_text(line) if "дмин" in line or "/acp" in line else line
                    for line in s.split("\n"))
    if out != s:
        open(path, "w", encoding="utf-8").write(out)
        return 1
    return 0


def main():
    for path in sys.argv[1:]:
        if not os.path.exists(path):
            print(f"  пропуск (нет файла): {path}")
            continue
        if path.endswith(".json"):
            n = scrub_json(path)
            print(f"  {os.path.basename(path):<40} очищено полей: {n}")
        else:
            n = scrub_plain(path)
            print(f"  {os.path.basename(path):<40} {'изменён' if n else 'без изменений'}")


if __name__ == "__main__":
    main()
