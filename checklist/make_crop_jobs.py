#!/usr/bin/env python3
"""Work out, for each fix, what text to look for and on which page.

The quote a fix carries is not always plain page text: some are wrapped in
markup, some are three languages joined with pipes, some are engine strings that
never appear in the DOM at all. This turns the usable ones into a search needle
and drops the rest rather than sending the cropper on a hunt it cannot win.

Usage:  python3 make_crop_jobs.py <checklist.json> <out_jobs.json>
"""
import glob
import json
import os
import re
import sys

# Template groups have no page of their own — point them at one that shows it.
REPRESENTATIVE = {
    "__global__": "index",
    "__filters__": "kids",
    "__category__": "kids",
    "__product__": "sukienka-dziewczeca-robee-niebieska-paski-falbanka-wygodna-ta-dziewcze-cc30042",
    "__system__": "index",
    "__docs__": "index",
}

LOCALE_OF = {"pl": "pl", "ua": "ua", "en": "en"}


def slug_of(group):
    key = group.get("key", "")
    if key in REPRESENTATIVE:
        return REPRESENTATIVE[key]
    path = (group.get("path") or "").strip("/")
    return path.replace("/", "__") or "index"


def needle_from(current, locale):
    """Pull out something a browser could actually find on the page."""
    if not current:
        return ""
    s = current.strip()

    # "pl: "…" | ua: "…" | en: "…"" — take this locale's own string
    m = re.search(rf'{locale}:\s*"([^"]+)"', s)
    if m:
        s = m.group(1)
    else:
        m = re.match(r'^[a-z]{2}:\s*"([^"]+)"', s)
        if m:
            s = m.group(1)

    # a markup quote: use the text between the tags, not the tags
    if s.lstrip().startswith("<"):
        inner = re.sub(r"<[^>]+>", " ", s)
        inner = re.sub(r"\s+", " ", inner).strip()
        if len(inner) < 3:
            return ""
        s = inner

    # "A ORAZ B" — one of them is enough to find the place
    s = re.split(r"\s+(?:ORAZ|ТА|AND)\s+", s)[0]
    s = re.split(r"\s+\|\s+", s)[0]
    s = s.split("\n")[0]
    s = re.sub(r"\s+", " ", s).strip().strip('"«»')

    if len(s) < 4:
        return ""
    return s[:70]


def build_index(raw_dir):
    """Page text per locale, so a quote can be traced to the page showing it."""
    idx = {}
    for locale in ("pl", "ua", "en"):
        for path in glob.glob(os.path.join(raw_dir, locale, "*.txt")):
            slug = os.path.basename(path)[:-4]
            txt = open(path, encoding="utf-8", errors="ignore").read()
            idx[(locale, slug)] = re.sub(r"\s+", " ", txt).lower()
    return idx


def locate(needle, locale, idx, preferred):
    """Where does this text actually live? The group's page is a guess; the
    index knows."""
    probe = re.sub(r"\s+", " ", needle).strip().lower().rstrip("…")[:36]
    if len(probe) < 6:
        return preferred, False
    if idx.get((locale, preferred), "").find(probe) != -1:
        return preferred, True
    for (loc, slug), txt in idx.items():
        if loc == locale and probe in txt:
            return slug, True
    for (loc, slug), txt in idx.items():
        if probe in txt:
            return slug, True
    return preferred, False


def main():
    cl_path, out_path = sys.argv[1], sys.argv[2]
    raw_dir = sys.argv[3] if len(sys.argv) > 3 else ""
    data = json.load(open(cl_path, encoding="utf-8"))
    idx = build_index(raw_dir) if raw_dir else {}

    jobs, skipped = [], 0
    for g in data["groups"]:
        slug = slug_of(g)
        for f in g["fixes"]:
            loc = (f.get("locale") or "pl").lower()
            loc = loc.split(",")[0].strip()
            if loc not in LOCALE_OF or loc == "all":
                loc = "pl"
            needle = needle_from(f.get("current"), loc)
            if not needle:
                skipped += 1
                continue
            target, found = (locate(needle, loc, idx, slug) if idx
                             else (slug, True))
            if not found:
                skipped += 1
                continue
            jobs.append({"id": f["id"], "slug": target, "locale": loc,
                         "needle": needle})

    json.dump(jobs, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"задач на вырезку: {len(jobs)}")
    print(f"пропущено (текста нет ни на одной странице): {skipped}")
    by_slug = {}
    for j in jobs:
        by_slug[j["slug"]] = by_slug.get(j["slug"], 0) + 1
    print("\nпо страницам (топ):")
    for s, n in sorted(by_slug.items(), key=lambda x: -x[1])[:8]:
        print(f"   {s[:48]:<50} {n}")


if __name__ == "__main__":
    main()
