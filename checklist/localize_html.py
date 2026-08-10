#!/usr/bin/env python3
"""Rewrite the saved pages so they render from disk exactly as they look live.

Two changes only. The shop's own assets point at the local mirror. Third-party
scripts are removed — they cannot load here, and the consent banner in
particular would cover every screenshot with an overlay.

Everything else, including all of the site's own CSS, is left alone: the whole
point is that the screenshot shows the real page.

Usage:  python3 localize_html.py <raw_dir> <mirror_dir> <render_dir>
"""
import os
import re
import sys

BASE = "https://lapetitebloom.com"

# Anything hosted elsewhere: consent manager, Google fonts, analytics.
EXTERNAL_SCRIPT = re.compile(
    r'<script[^>]+src="https?://(?!lapetitebloom\.com)[^"]+"[^>]*>\s*</script>',
    re.I)
EXTERNAL_LINK = re.compile(
    r'<link[^>]+href="https?://(?!lapetitebloom\.com)[^"]+"[^>]*>', re.I)
# The banner markup itself, in case it is inlined rather than injected.
CONSENT_BLOCK = re.compile(
    r'<div[^>]+(?:id|class)="[^"]*(?:CybotCookiebot|cookie-?banner)[^"]*"[^>]*>.*?</div>',
    re.I | re.S)


def localize(html, depth):
    up = "../" * depth

    def to_local(m):
        # file:// ignores nothing — a "?v=123" cache-buster makes the path miss,
        # and the first casualty is the stylesheet.
        return f'{m.group(1)}="{up}mirror{m.group(2)}"'

    html = re.sub(
        r'(src|href)="(?:https://lapetitebloom\.com)?(/(?:front|storage)/[^"?]+)(?:\?[^"]*)?"',
        to_local, html)
    html = EXTERNAL_SCRIPT.sub("", html)
    html = EXTERNAL_LINK.sub("", html)
    html = CONSENT_BLOCK.sub("", html)
    return html


def main():
    raw_dir, mirror_dir, render_dir = sys.argv[1:4]
    made, skipped = 0, []
    for locale in ("pl", "ua", "en"):
        src_dir = os.path.join(raw_dir, locale)
        if not os.path.isdir(src_dir):
            continue
        out_dir = os.path.join(render_dir, locale)
        os.makedirs(out_dir, exist_ok=True)
        for fn in sorted(os.listdir(src_dir)):
            if not fn.endswith(".html"):
                continue
            html = open(os.path.join(src_dir, fn), encoding="utf-8",
                        errors="ignore").read()
            if "Opening Soon" in html and len(html) < 20000:
                skipped.append(f"{locale}/{fn}")
                continue
            # render/<locale>/<file> -> two levels up to reach the mirror
            open(os.path.join(out_dir, fn), "w", encoding="utf-8").write(
                localize(html, depth=2))
            made += 1

    print(f"подготовлено страниц: {made}")
    if skipped:
        print(f"пропущено (заглушка Opening Soon): {len(skipped)}")
        for s in skipped[:10]:
            print("  ", s)

    # sanity: the mirror really has to sit where the rewritten paths point
    sample = os.path.join(render_dir, "pl", "index.html")
    if os.path.exists(sample):
        html = open(sample, encoding="utf-8").read()
        refs = re.findall(r'(?:src|href)="(\.\./\.\./mirror/[^"]+)"', html)
        ok = sum(1 for r in refs[:40]
                 if os.path.exists(os.path.normpath(
                     os.path.join(render_dir, "pl", r))))
        print(f"проверка путей на /: {ok} из {min(40, len(refs))} ресурсов на месте")


if __name__ == "__main__":
    main()
