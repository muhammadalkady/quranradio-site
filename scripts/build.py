#!/usr/bin/env python3
"""Builds the site's home page in every language the app speaks.

    python3 scripts/build.py

Renders src/home.html once per i18n/<lang>.json: English to /index.html and every other language
to /<lang>/index.html. Rewrites sitemap.xml with each page and its alternates. With fontTools
(`pip install fonttools brotli`) it also cuts each font in fonts/src/ down to the characters the
site's pages use, as fonts/<name>.woff2; without it, the fonts already in fonts/ are kept.
"""
import datetime
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://quranradio.app"
PLAY_URL = "https://play.google.com/store/apps/details?id=com.kady.muhammad.quran_radio"

# Menu and sitemap order: English (the default), then the rest grouped by script.
LANGS = ["en", "ar", "ur", "id", "ms", "tr", "az", "fr", "de", "it", "ru", "bn"]

# Localized Google Play badges; any other language uses the English one with a localized alt.
BADGES = {"en": "/assets/google-play-badge.png", "ar": "/assets/google-play-badge-ar.png"}

# The fonts each script's page preloads (what its headings paint in first).
PRELOAD = {
    "latin": ["marcellus_regular"],
    "serif": ["noto_serif_regular", "marcellus_regular"],
    "arabic": ["reem_kufi_regular", "amiri_regular"],
    "urdu": ["noto_nastaliq_urdu", "marcellus_regular"],
    "bengali": ["noto_serif_bengali_regular", "marcellus_regular"],
}

PHONE_SHOTS = ["home", "mushaf", "listen", "player", "prayer", "qibla", "library"]

ICONS = {
    "adhan": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
    "widgets": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/>'
               '<rect x="3" y="14" width="18" height="7" rx="2"/>',
    "langs": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "lists": '<path d="M4 6h11M4 12h11M4 18h7"/><circle cx="18.5" cy="16.5" r="2.5"/><path d="M21 16.5V8l-3 1"/>',
    "hijri": '<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z"/><path d="M17 3l.8 1.7L19.5 5.5l-1.7.8L17 8l-.8-1.7'
             'L14.5 5.5l1.7-.8z"/>',
    "design": '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 0 0 18z"/>',
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def path_of(lang: str) -> str:
    return "/" if lang == "en" else f"/{lang}/"


def load() -> dict:
    pages = {}
    for lang in LANGS:
        pages[lang] = json.loads((ROOT / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))
    extra = {p.stem for p in (ROOT / "i18n").glob("*.json")} - set(LANGS)
    if extra:
        sys.exit(f"build: i18n has languages missing from LANGS: {sorted(extra)}")
    return pages


def phone(lang: str, shot: str, alt: str, indent: str) -> str:
    return (f'{indent}<div class="frame frame--phone"><img class="frame__shot" src="/assets/screens/{lang}/phone-{shot}.webp"'
            f' width="720" height="1603" loading="lazy" alt="{esc(alt)}" /></div>')


def render(lang: str, d: dict, pages: dict) -> str:
    url = BASE + path_of(lang)
    captions = {row["shot"]: row["h2"] for row in d["rows"]}
    rows = []
    for i, row in enumerate(d["rows"]):
        reverse = " reverse" if i % 2 else ""
        eyebrow = f'            <p class="eyebrow">{esc(row["eyebrow"])}</p>' if row["eyebrow"] else ""
        rows.append(f'''        <div class="feature{reverse} reveal">
          <div class="feature__text">
{eyebrow}
            <h2>{esc(row["h2"])}</h2>
            <p>{esc(row["body"])}</p>
          </div>
          <div class="feature__media">
{phone(lang, row["shot"], row["h2"], "            ")}
          </div>
        </div>''')
    tiles = [f'''          <div class="tile reveal">
            <div class="ti"><svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[t["icon"]]}</svg></div>
            <h3>{esc(t["title"])}</h3><p>{esc(t["body"])}</p>
          </div>''' for t in d["tiles"]]
    menu = []
    for other in LANGS:
        o = pages[other]
        current = ' aria-current="page"' if other == lang else ""
        menu.append(f'            <li><a href="{path_of(other)}" hreflang="{other}" lang="{other}" dir="{o["dir"]}"'
                     f' data-set-lang="{other}"{current}>{esc(o["langName"])}</a></li>')
    hreflang = [f'  <link rel="alternate" hreflang="{o}" href="{BASE}{path_of(o)}" />' for o in LANGS]
    hreflang.append(f'  <link rel="alternate" hreflang="x-default" href="{BASE}/" />')
    og_alt = [f'  <meta property="og:locale:alternate" content="{pages[o]["ogLocale"]}" />' for o in LANGS if o != lang]
    preload = [f'  <link rel="preload" as="font" type="font/woff2" crossorigin href="/fonts/{f}.woff2" />'
               for f in PRELOAD[d["script"]]]
    if lang == "ar":
        hero_name = '<p class="arabic" lang="en">Muslim Haven</p>'
    else:
        hero_name = '<p class="arabic" lang="ar" dir="rtl">مَلَاذُ الْمُسْلِم</p>'
    ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": d["name"],
        "alternateName": [d["title"]] + (["Muslim Haven"] if d["name"] != "Muslim Haven" else []),
        "operatingSystem": "Android, Android TV",
        "applicationCategory": "LifestyleApplication",
        "description": d["lede"],
        "url": url,
        "downloadUrl": PLAY_URL,
        "image": f"{BASE}/icon-512.png",
        "screenshot": f"{BASE}/assets/screens/{lang}/phone-home.webp",
        "inLanguage": [lang] + [o for o in LANGS if o != lang],
        "author": {"@type": "Person", "name": "Muhammad Alkady"},
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }
    raw = {
        "hreflang": "\n".join(hreflang),
        "ogAlternates": "\n".join(og_alt),
        "preload": "\n".join(preload),
        "jsonLd": "  " + json.dumps(ld, ensure_ascii=False, indent=2).replace("\n", "\n  ").replace("</", "<\\/"),
        "langsJson": json.dumps(LANGS),
        "langMenuItems": "\n".join(menu),
        "heroName": hero_name,
        "marquee": "\n".join(phone(lang, s, captions[s], "        ") for s in PHONE_SHOTS),
        "rows": "\n\n".join(rows),
        "tiles": "\n".join(tiles),
    }
    values = {k: v for k, v in d.items() if isinstance(v, str)}
    values.update(
        url=url, path=path_of(lang), playUrl=PLAY_URL, badge=BADGES.get(lang, BADGES["en"]),
        privacyUrl="/privacy-policy.html#ar" if lang == "ar" else "/privacy-policy.html",
        themeAria=d["themeTpl"].replace("{pref}", d["themeSystem"]),
    )
    template = (ROOT / "src" / "home.html").read_text(encoding="utf-8")

    def fill(match: re.Match) -> str:
        key = match.group(1)
        if key in raw:
            return raw[key]
        if key in values:
            return esc(values[key])
        sys.exit(f"build: {lang}: no value for {{{{{key}}}}}")

    return re.sub(r"\{\{(\w+)\}\}", fill, template)


def sitemap(today: str) -> str:
    alternates = "\n".join(f'    <xhtml:link rel="alternate" hreflang="{o}" href="{BASE}{path_of(o)}"/>' for o in LANGS)
    alternates += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}/"/>'
    urls = [f"""  <url>
    <loc>{BASE}{path_of(lang)}</loc>
{alternates}
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>""" for lang in LANGS]
    policy = re.search(r"<url>\s*<loc>[^<]*privacy-policy[^<]*</loc>.*?</url>",
                       (ROOT / "sitemap.xml").read_text(encoding="utf-8"), re.S)
    if policy:
        urls.append("  " + policy.group(0))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n")


def subset_fonts(texts: list) -> None:
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        print("build: fontTools not installed; kept the fonts already in fonts/ (pip install fonttools brotli)")
        return
    used = set("".join(texts)) | {chr(c) for c in range(0x20, 0x7F)} | set("’‘“”–—…·©")
    for src in sorted((ROOT / "fonts" / "src").glob("*.ttf")):
        cmap = TTFont(src).getBestCmap()
        chars = sorted(ord(c) for c in used if ord(c) in cmap)
        options = subset.Options()
        options.flavor = "woff2"
        options.layout_features = ["*"]
        options.hinting = False
        options.desubroutinize = True
        font = subset.load_font(str(src), options)
        subsetter = subset.Subsetter(options)
        subsetter.populate(unicodes=chars)
        subsetter.subset(font)
        out = ROOT / "fonts" / f"{src.stem}.woff2"
        subset.save_font(font, str(out), options)
        print(f"build: fonts/{out.name}: {len(chars)} characters, {out.stat().st_size // 1024} KB")


def main() -> None:
    pages = load()
    texts = []
    for lang, d in pages.items():
        page = render(lang, d, pages)
        out = ROOT / ("index.html" if lang == "en" else f"{lang}/index.html")
        out.parent.mkdir(exist_ok=True)
        out.write_text(page, encoding="utf-8")
        texts.append(page)
        print(f"build: {out.relative_to(ROOT)}")
    (ROOT / "sitemap.xml").write_text(sitemap(datetime.date.today().isoformat()), encoding="utf-8")
    for other in ("privacy-policy.html", "404.html"):
        texts.append((ROOT / other).read_text(encoding="utf-8"))
    subset_fonts([html.unescape(t) for t in texts])


if __name__ == "__main__":
    main()
