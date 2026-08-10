#!/usr/bin/env python3
"""Download the styling the saved pages refer to, so they can be rendered offline.

The browser here cannot reach the network, but curl-level HTTP can — which is
how the pages were captured in the first place. So the assets come down the same
way and the screenshots get taken from local files.

Usage:  python3 mirror_assets.py <raw_dir> <mirror_dir>
"""
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = "https://lapetitebloom.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
# Only the shop's own static files; third-party scripts are stripped, not mirrored.
ASSET = re.compile(r'(?:src|href)="(?:https://lapetitebloom\.com)?(/(?:front|storage)/[^"?]+)')


def find_assets(raw_dir):
    found = set()
    for root, _, files in os.walk(raw_dir):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            html = open(os.path.join(root, fn), encoding="utf-8", errors="ignore").read()
            found |= set(ASSET.findall(html))
    return sorted(found)


def fetch(session, path, mirror_dir):
    dest = os.path.join(mirror_dir, path.lstrip("/"))
    if os.path.exists(dest) and os.path.getsize(dest):
        return ("cached", path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(3):
        try:
            r = session.get(BASE + path, timeout=60)
            if r.status_code == 200 and r.content:
                open(dest, "wb").write(r.content)
                return ("ok", path)
            if r.status_code == 404:
                return ("404", path)
        except Exception:  # noqa: BLE001
            if attempt == 2:
                return ("error", path)
    return ("fail", path)


def main():
    raw_dir, mirror_dir = sys.argv[1], sys.argv[2]
    assets = find_assets(raw_dir)
    print(f"ресурсов найдено: {len(assets)}")

    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch, s, a, mirror_dir) for a in assets]
        for i, f in enumerate(futs, 1):
            results.append(f.result())
            if i % 150 == 0:
                print(f"  {i}/{len(assets)}")

    tally = {}
    for status, _ in results:
        tally[status] = tally.get(status, 0) + 1
    print("\nитог:", ", ".join(f"{k}: {v}" for k, v in sorted(tally.items())))

    missing = [p for st, p in results if st not in ("ok", "cached")]
    if missing:
        print(f"\nне скачалось ({len(missing)}):")
        for p in missing[:25]:
            print("  ", p)
        # A page without its stylesheet cannot be screenshotted honestly.
        css_missing = [p for p in missing if p.endswith(".css")]
        if css_missing:
            print(f"\n!! среди них {len(css_missing)} файлов CSS — снимки этих "
                  f"страниц будут без оформления")


if __name__ == "__main__":
    main()
