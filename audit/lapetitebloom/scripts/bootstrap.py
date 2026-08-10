#!/usr/bin/env python3
"""Step 0: log into /acp, check whether the admin session lifts the
"Opening Soon" splash, and produce one cookie jar per locale (pl/ua/en)."""
import json
import os
import re
import sys

import requests

BASE = "https://lapetitebloom.com"
EMAIL = os.environ.get("LPB_ADMIN_EMAIL", "")
PASS = os.environ.get("LPB_ADMIN_PASS", "")
OUT = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

SPLASH = "Opening Soon"


def token(html):
    m = re.search(r'name="_token"\s+value="([^"]+)"', html)
    if not m:
        m = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
    return m.group(1) if m else None


def is_splash(text):
    return SPLASH in text and len(text) < 20000


def make_session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA,
                      "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8"})
    return s


def login(s):
    r = s.get(f"{BASE}/acp/login", timeout=60)
    t = token(r.text)
    if not t:
        print("!! no CSRF token on the login page")
        return False
    r = s.post(f"{BASE}/acp/login", timeout=60, allow_redirects=True,
               data={"_token": t, "email": EMAIL, "password": PASS, "remember": "on"},
               headers={"Referer": f"{BASE}/acp/login"})
    ok = "/acp/login" not in r.url
    print(f"login -> {r.status_code} {r.url}  success={ok}")
    if not ok:
        for pat in (r'class="[^"]*invalid-feedback[^"]*"[^>]*>\s*([^<]+)',
                    r'"message"\s*:\s*"([^"]+)"', r'alert[^>]*>\s*([^<]{5,120})'):
            m = re.findall(pat, r.text)
            if m:
                print("   reason:", m[:3])
                break
    return ok


def check_bypass(s, label):
    print(f"\n== splash check ({label}) ==")
    out = {}
    for p in ["/", "/contacts", "/kids", "/blog", "/about"]:
        r = s.get(BASE + p, timeout=60)
        sp = is_splash(r.text)
        out[p] = {"splash": sp, "len": len(r.text), "status": r.status_code}
        print(f"  {p:<12} status={r.status_code} splash={sp} len={len(r.text)}")
    return out


def set_locale(s, loc, currency="PLN"):
    r = s.get(f"{BASE}/brands/liewood", timeout=60)
    t = token(r.text)
    r = s.post(f"{BASE}/settings/locale", timeout=60, allow_redirects=True,
               data={"_token": t, "locale": loc, "currency": currency},
               headers={"Referer": f"{BASE}/brands/liewood",
                        "X-Requested-With": "XMLHttpRequest"})
    v = s.get(f"{BASE}/brands/liewood", timeout=60)
    lang = re.search(r'<html[^>]*lang="([^"]+)"', v.text)
    btn = re.search(r'header__locale-btn[^>]*>\s*([^<]+)', v.text)
    got = lang.group(1) if lang else "?"
    print(f"  {loc}: post={r.status_code} html[lang]={got} "
          f"switcher={(btn.group(1).strip() if btn else '?')!r}")
    return got


def main():
    s = make_session()

    anon = check_bypass(s, "anonymous")

    print("\n== admin login ==")
    logged = login(s)

    admin = check_bypass(s, "admin session") if logged else {}
    bypassed = logged and not any(v["splash"] for v in admin.values())
    print(f"\nSPLASH BYPASSED BY ADMIN SESSION: {bypassed}")

    print("\n== locales ==")
    locales = {}
    for loc in ("pl", "ua", "en"):
        locales[loc] = set_locale(s, loc)
        s.cookies.save if False else None
        with open(os.path.join(OUT, f"cookies_{loc}.json"), "w") as f:
            json.dump(requests.utils.dict_from_cookiejar(s.cookies), f, indent=1)

    json.dump({"anon": anon, "admin": admin, "logged_in": logged,
               "bypassed": bypassed, "locales": locales},
              open(os.path.join(OUT, "bootstrap.json"), "w"),
              ensure_ascii=False, indent=1)
    return 0 if logged else 1


if __name__ == "__main__":
    sys.exit(main())
