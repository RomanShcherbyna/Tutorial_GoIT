#!/usr/bin/env python3
"""Crawl lapetitebloom.com in all three locales with an admin session
(which lifts the "Opening Soon" splash) and dump, per page:
  raw/<locale>/<slug>.html  full HTML
  raw/<locale>/<slug>.txt   visible text, one block per line
  raw/<locale>/<slug>.json  parsed window.FenixTranslations + page meta

Locales are URL-prefixed: pl = no prefix, ua = /ua, en = /en.
"""
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup

BASE = "https://lapetitebloom.com"
EMAIL = os.environ.get("LPB_ADMIN_EMAIL", "")
PASS = os.environ.get("LPB_ADMIN_PASS", "")
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
LOCALES = {"pl": "", "ua": "/ua", "en": "/en"}

PATHS = [
    # --- static pages -------------------------------------------------
    "/", "/about", "/contacts", "/delivery-and-payment",
    "/warranty-and-returns", "/warranty-and-returns/polityka-zwrotow",
    "/warranty-and-returns/gwarancja-na-produkt", "/terms-of-use",
    "/privacy-policy", "/personal-data-requests", "/claims-and-complaints",
    "/polityka-cookies", "/zgody-klauzule-i-regulamin-newslettera",
    "/regulamin-kart-podarunkowych", "/deklaracja-dostepnosci",
    # --- blog ---------------------------------------------------------
    "/blog",
    "/blog/soluta-exercitationem-omnis-id32924",
    "/blog/assumenda-molestias-minima-aut-unde3877",
    "/blog/quas-odio-ut5808",
    "/blog/kocyki-klippan-naturalne-cieplo-i-skandynawska-jakosc-dla-najmlodszych",
    "/blog/sit-rerum-labore23250",
    "/blog/odit-ut-voluptates3981",
    "/blog/aut-est2794",
    "/blog/saepe-consequatur-architecto-est15163",
    # --- top-level categories ------------------------------------------
    "/kids", "/girls", "/boys", "/footwear", "/accessories", "/zabawki",
    "/pielegnacja-i-kosmetyki", "/niemowleta",
    # --- brands ---------------------------------------------------------
    "/brands", "/brands/liewood", "/brands/veja", "/brands/maileg",
    # --- funnel / account -----------------------------------------------
    "/special-offers", "/search", "/search?q=sukienka",
    "/auth/login", "/auth/register", "/auth/forgot-password",
    "/favorites", "/cart", "/checkout",
    # --- product cards, one per type ------------------------------------
    "/trampki-veja-small-volley-atlantic-ouro-bark-zlote-sportowe-buty-ve-smallvolb",
    "/sukienka-dziewczeca-robee-niebieska-paski-falbanka-wygodna-ta-dziewcze-cc30042",
    "/krem-pod-oczy-skin-minimalism-eye-revival-pielegnacja-okolic-oczu-sm-eye-revival",
    "/myszka-maileg-baby-w-sukience-pudrowy-17-6000-00",
    "/koszulka-bobo-choses-booo-z-nadrukiem-dla-dzieci-b226ac017-2-3",
    "/little-dutch-kocyk-muslinowy-fairy-blossom-110x140-letni-kocyk-te12194031",
    "/skarpetki-bobo-choses-hug-hairy-monster-dla-dzieci-b226ai001-23-25",
    "/sol-do-kapieli-dresdner-essenz-badz-zdrow-neuro-na-katar-50-g-3-bz-katar-50",
    # --- error page -------------------------------------------------------
    "/this-page-does-not-exist-404-probe",
]


def slug(path):
    s = path.strip("/").replace("/", "__").replace("?", "_q_").replace("=", "-")
    return s or "index"


def login():
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    r = s.get(f"{BASE}/acp/login", timeout=60)
    t = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
    r = s.post(f"{BASE}/acp/login", timeout=60,
               data={"_token": t, "email": EMAIL, "password": PASS})
    if "/acp/login" in r.url:
        sys.exit("login failed")
    return s


def session_for(locale):
    """A logged-in session pinned to one locale.

    Unprefixed URLs (Polish) follow whatever locale the session last stored,
    so each locale needs its own session rather than a shared one.
    """
    s = login()
    r = s.get(f"{BASE}/brands/liewood", timeout=60)
    t = re.search(r'name="_token"\s+value="([^"]+)"', r.text).group(1)
    s.post(f"{BASE}/settings/locale", timeout=60,
           data={"_token": t, "locale": locale, "currency": "PLN"},
           headers={"Referer": f"{BASE}/brands/liewood"})
    return s


def visible_text(soup):
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    lines = []
    for chunk in soup.stripped_strings:
        c = re.sub(r"\s+", " ", chunk).strip()
        if c and (not lines or lines[-1] != c):
            lines.append(c)
    return lines


def fenix(html):
    """Pull the window.FenixTranslations.<group> = {...} literals."""
    out = {}
    for m in re.finditer(r"window\.FenixTranslations\.(\w+)\s*=\s*(\{.*?\});",
                         html, re.S):
        group, body = m.group(1), m.group(2)
        pairs = re.findall(r'(\w+)\s*:\s*"((?:[^"\\]|\\.)*)"', body)
        out[group] = {k: v for k, v in pairs}
    return out


def grab(session, locale, path):
    prefix = LOCALES[locale]
    # "/" must not become "/en/" — that redirects back to the default locale
    url = BASE + prefix if path == "/" else BASE + prefix + path
    if path == "/" and not prefix:
        url = BASE + "/"
    try:
        r = session.get(url, timeout=90)
    except Exception as e:  # noqa: BLE001
        return {"path": path, "locale": locale, "error": str(e)}

    html = r.text
    d = os.path.join(RAW, locale)
    os.makedirs(d, exist_ok=True)
    base = os.path.join(d, slug(path))
    open(base + ".html", "w", encoding="utf-8").write(html)

    soup = BeautifulSoup(html, "lxml")
    lines = visible_text(soup)
    open(base + ".txt", "w", encoding="utf-8").write("\n".join(lines))

    lang = re.search(r'<html[^>]*lang="([^"]+)"', html)
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    desc = soup.find("meta", attrs={"name": "description"})
    h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    body_html = re.sub(r"(?s)<script.*?</script>", "", html)
    cyr = sorted({c.strip() for c in
                  re.findall(r'[^<>"]*[Ѐ-ӿ][^<>"]*', body_html)
                  if c.strip()})

    meta = {
        "url": url, "path": path, "locale": locale,
        "status": r.status_code, "html_lang": lang.group(1) if lang else None,
        "title": title,
        "meta_description": desc.get("content", "") if desc else "",
        "h1": h1, "text_lines": len(lines),
        "cyrillic_strings": cyr,
        "fenix_translations": fenix(html),
    }
    json.dump(meta, open(base + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return {"path": path, "locale": locale, "status": r.status_code,
            "lang": meta["html_lang"], "title": title, "lines": len(lines),
            "bytes": len(html)}


def main():
    sessions = {loc: session_for(loc) for loc in LOCALES}
    print(f"logged in; crawling {len(PATHS)} paths x {len(LOCALES)} locales")
    jobs = [(loc, p) for p in PATHS for loc in LOCALES]
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(grab, sessions[loc], loc, p) for loc, p in jobs]
        for i, f in enumerate(futs, 1):
            r = f.result()
            results.append(r)
            if i % 25 == 0:
                print(f"  {i}/{len(jobs)}")
    json.dump(results, open(os.path.join(HERE, "crawl_index.json"), "w"),
              ensure_ascii=False, indent=1)

    bad = [r for r in results if r.get("error") or r.get("status") != 200]
    mism = [r for r in results
            if r.get("lang") and r["lang"][:2] != {"pl": "pl", "ua": "uk",
                                                   "en": "en"}[r["locale"]]]
    print(f"\ndone: {len(results)} pages, {len(bad)} non-200, "
          f"{len(mism)} locale mismatches")
    for r in bad[:20]:
        print("  BAD ", r["locale"], r["path"], r.get("status"), r.get("error", ""))
    for r in mism[:20]:
        print("  LANG", r["locale"], r["path"], "->", r["lang"])


if __name__ == "__main__":
    main()
