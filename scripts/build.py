#!/usr/bin/env python3
"""Builds the site's home page and privacy policy in every language the app speaks.

    python3 scripts/build.py

Renders src/home.html once per i18n/<lang>.json, and src/privacy.html around each privacy/<lang>.html:
English to /index.html and /privacy-policy.html, every other language under /<lang>/. Rewrites sitemap.xml with each page and its alternates. With fontTools
(`pip install fonttools brotli`) it also cuts each font in fonts/src/ down to the characters the
site's pages use, as fonts/<name>.woff2; without it, the fonts already in fonts/ are kept.
"""
import datetime
import hashlib
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

# The fonts each script's page preloads (what its headings paint in first).
PRELOAD = {
    "latin": ["marcellus_regular"],
    "serif": ["noto_serif_regular", "marcellus_regular"],
    "arabic": ["reem_kufi_regular", "amiri_regular"],
    "urdu": ["noto_nastaliq_urdu", "marcellus_regular"],
    "bengali": ["noto_serif_bengali_regular", "marcellus_regular"],
}

PHONE_SHOTS = ["home", "mushaf", "listen", "player", "prayer", "qibla", "library"]

# The tiles' icons: Material Symbols Rounded, filled, as the app draws them (its vector drawables
# where it has one: alarm, tv_settings_language, playlist_play, calendar_month, tv_settings_palette).
# Each is (viewBox, [path data]).
ICONS = {
    "adhan": ("0 -960 960 960", [
        "M200-200q-17 0-28.5-11.5T160-240q0-17 11.5-28.5T200-280h40v-280q0-83 50-147.5T420-792v-28q0-25 17.5-42.5T480-880q25 0 42.5 17.5T540-820v28q80 20 130 84.5T720-560v280h40q17 0 28.5 11.5T800-240q0 17-11.5 28.5T760-200H200ZM480-80q-33 0-56.5-23.5T400-160h160q0 33-23.5 56.5T480-80Z",
    ]),
    "widgets": ("0 -960 960 960", [
        "M638-468 468-638q-6-6-8.5-13t-2.5-15q0-8 2.5-15t8.5-13l170-170q6-6 13-8.5t15-2.5q8 0 15 2.5t13 8.5l170 170q6 6 8.5 13t2.5 15q0 8-2.5 15t-8.5 13L694-468q-6 6-13 8.5t-15 2.5q-8 0-15-2.5t-13-8.5Zm-518-92v-240q0-17 11.5-28.5T160-840h240q17 0 28.5 11.5T440-800v240q0 17-11.5 28.5T400-520H160q-17 0-28.5-11.5T120-560Zm400 400v-240q0-17 11.5-28.5T560-440h240q17 0 28.5 11.5T840-400v240q0 17-11.5 28.5T800-120H560q-17 0-28.5-11.5T520-160Zm-400 0v-240q0-17 11.5-28.5T160-440h240q17 0 28.5 11.5T440-400v240q0 17-11.5 28.5T400-120H160q-17 0-28.5-11.5T120-160Z",
    ]),
    "langs": ("0 0 960 960", [
        "M480,880Q398,880 325,848.5Q252,817 197.5,762.5Q143,708 111.5,635Q80,562 80,480Q80,397 111.5,324.5Q143,252 197.5,197.5Q252,143 325,111.5Q398,80 480,80Q563,80 635.5,111.5Q708,143 762.5,197.5Q817,252 848.5,324.5Q880,397 880,480Q880,562 848.5,635Q817,708 762.5,762.5Q708,817 635.5,848.5Q563,880 480,880ZM480,798Q506,762 525,723Q544,684 556,640L404,640Q416,684 435,723Q454,762 480,798ZM376,782Q358,749 344.5,713.5Q331,678 322,640L204,640Q233,690 276.5,727Q320,764 376,782ZM584,782Q640,764 683.5,727Q727,690 756,640L638,640Q629,678 615.5,713.5Q602,749 584,782ZM170,560L306,560Q303,540 301.5,520.5Q300,501 300,480Q300,459 301.5,439.5Q303,420 306,400L170,400Q165,420 162.5,439.5Q160,459 160,480Q160,501 162.5,520.5Q165,540 170,560ZM386,560L574,560Q577,540 578.5,520.5Q580,501 580,480Q580,459 578.5,439.5Q577,420 574,400L386,400Q383,420 381.5,439.5Q380,459 380,480Q380,501 381.5,520.5Q383,540 386,560ZM654,560L790,560Q795,540 797.5,520.5Q800,501 800,480Q800,459 797.5,439.5Q795,420 790,400L654,400Q657,420 658.5,439.5Q660,459 660,480Q660,501 658.5,520.5Q657,540 654,560ZM638,320L756,320Q727,270 683.5,233Q640,196 584,178Q602,211 615.5,246.5Q629,282 638,320ZM404,320L556,320Q544,276 525,237Q506,198 480,162Q454,198 435,237Q416,276 404,320ZM204,320L322,320Q331,282 344.5,246.5Q358,211 376,178Q320,196 276.5,233Q233,270 204,320Z",
    ]),
    "lists": ("0 0 960 960", [
        "M160,640Q143,640 131.5,628.5Q120,617 120,600Q120,583 131.5,571.5Q143,560 160,560L400,560Q417,560 428.5,571.5Q440,583 440,600Q440,617 428.5,628.5Q417,640 400,640L160,640ZM160,480Q143,480 131.5,468.5Q120,457 120,440Q120,423 131.5,411.5Q143,400 160,400L560,400Q577,400 588.5,411.5Q600,423 600,440Q600,457 588.5,468.5Q577,480 560,480L160,480ZM160,320Q143,320 131.5,308.5Q120,297 120,280Q120,263 131.5,251.5Q143,240 160,240L560,240Q577,240 588.5,251.5Q600,263 600,280Q600,297 588.5,308.5Q577,320 560,320L160,320ZM671,819Q666,822 661,822Q656,822 651,820Q646,818 643,813.5Q640,809 640,803L640,557Q640,551 643,546.5Q646,542 651,540Q656,538 661,538Q666,538 671,541L855,663Q860,666 862,670.5Q864,675 864,680Q864,685 862,689.5Q860,694 855,697L671,819Z",
    ]),
    "hijri": ("0 0 960 960", [
        "M200,880Q167,880 143.5,856.5Q120,833 120,800L120,240Q120,207 143.5,183.5Q167,160 200,160L240,160L240,120Q240,103 251.5,91.5Q263,80 280,80Q297,80 308.5,91.5Q320,103 320,120L320,160L640,160L640,120Q640,103 651.5,91.5Q663,80 680,80Q697,80 708.5,91.5Q720,103 720,120L720,160L760,160Q793,160 816.5,183.5Q840,207 840,240L840,800Q840,833 816.5,856.5Q793,880 760,880L200,880ZM200,800L760,800Q760,800 760,800Q760,800 760,800L760,400L200,400L200,800Q200,800 200,800Q200,800 200,800ZM480,560Q463,560 451.5,548.5Q440,537 440,520Q440,503 451.5,491.5Q463,480 480,480Q497,480 508.5,491.5Q520,503 520,520Q520,537 508.5,548.5Q497,560 480,560ZM291.5,548.5Q280,537 280,520Q280,503 291.5,491.5Q303,480 320,480Q337,480 348.5,491.5Q360,503 360,520Q360,537 348.5,548.5Q337,560 320,560Q303,560 291.5,548.5ZM640,560Q623,560 611.5,548.5Q600,537 600,520Q600,503 611.5,491.5Q623,480 640,480Q657,480 668.5,491.5Q680,503 680,520Q680,537 668.5,548.5Q657,560 640,560ZM480,720Q463,720 451.5,708.5Q440,697 440,680Q440,663 451.5,651.5Q463,640 480,640Q497,640 508.5,651.5Q520,663 520,680Q520,697 508.5,708.5Q497,720 480,720ZM291.5,708.5Q280,697 280,680Q280,663 291.5,651.5Q303,640 320,640Q337,640 348.5,651.5Q360,663 360,680Q360,697 348.5,708.5Q337,720 320,720Q303,720 291.5,708.5ZM640,720Q623,720 611.5,708.5Q600,697 600,680Q600,663 611.5,651.5Q623,640 640,640Q657,640 668.5,651.5Q680,663 680,680Q680,697 668.5,708.5Q657,720 640,720Z",
    ]),
    "design": ("0 0 960 960", [
        "M480,880Q398,880 325,848.5Q252,817 197.5,762.5Q143,708 111.5,635Q80,562 80,480Q80,397 112.5,324Q145,251 200.5,197Q256,143 330,111.5Q404,80 488,80Q568,80 639,107.5Q710,135 763.5,183.5Q817,232 848.5,298.5Q880,365 880,442Q880,557 810,618.5Q740,680 640,680L566,680Q557,680 553.5,685Q550,690 550,696Q550,708 565,730.5Q580,753 580,782Q580,832 552.5,856Q525,880 480,880ZM260,520Q286,520 303,503Q320,486 320,460Q320,434 303,417Q286,400 260,400Q234,400 217,417Q200,434 200,460Q200,486 217,503Q234,520 260,520ZM380,360Q406,360 423,343Q440,326 440,300Q440,274 423,257Q406,240 380,240Q354,240 337,257Q320,274 320,300Q320,326 337,343Q354,360 380,360ZM580,360Q606,360 623,343Q640,326 640,300Q640,274 623,257Q606,240 580,240Q554,240 537,257Q520,274 520,300Q520,326 537,343Q554,360 580,360ZM700,520Q726,520 743,503Q760,486 760,460Q760,434 743,417Q726,400 700,400Q674,400 657,417Q640,434 640,460Q640,486 657,503Q674,520 700,520Z",
    ]),
}


def icon(name: str) -> str:
    box, paths = ICONS[name]
    return f'<svg viewBox="{box}" aria-hidden="true">' + "".join(f'<path d="{d}"/>' for d in paths) + "</svg>"


def hero_mark() -> str:
    """The brand master (assets/mark.svg is the app's design/brand/muslim-haven-mark.svg), inline so its
    four discs of light can drift (assets/mark.js): ids prefixed so they stay unique in the page, the
    discs named, and the full-frame dither dropped, as it would be re-filtered on every frame."""
    svg = (ROOT / "assets" / "mark.svg").read_text(encoding="utf-8")
    svg = svg[svg.index("<svg"):]
    svg = re.sub(r'<rect width="512" height="512" filter="url\(#dither\)" />\s*', "", svg)
    svg = re.sub(r'\bid="([\w-]+)"', r'id="mh-\1"', svg)
    svg = re.sub(r'url\(#([\w-]+)\)', r'url(#mh-\1)', svg)
    svg = re.sub(r'href="#([\w-]+)"', r'href="#mh-\1"', svg)
    svg = re.sub(r'\s(width|height)="512"(?=[^>]*viewBox)', "", svg, count=2)
    svg = svg.replace('role="img"', 'aria-hidden="true" focusable="false"')
    haze = re.search(r'<g filter="url\(#mh-haze\)">(.*?)</g>', svg, re.S)
    discs = iter(range(4))
    body = re.sub(r"<circle ", lambda m: f'<circle id="mh-light-{next(discs)}" ', haze.group(1))
    svg = svg[:haze.start(1)] + body + svg[haze.end(1):]
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    return re.sub(r"\n\s*", " ", svg).strip()


def esc(value: str) -> str:
    return html.escape(value, quote=True)


# The pages built in every language: the home page and the privacy policy. English sits at the
# site root; every other language in its own folder.
KINDS = {"home": "index.html", "privacy": "privacy-policy.html"}


def path_of(lang: str, kind: str = "home") -> str:
    """The page's address: the home page is its folder, other pages their file."""
    folder = "/" if lang == "en" else f"/{lang}/"
    return folder if kind == "home" else folder + KINDS[kind]


def out_file(lang: str, kind: str) -> pathlib.Path:
    return ROOT / ("" if lang == "en" else lang) / KINDS[kind]


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
            f' width="1080" height="2404" loading="lazy" alt="{esc(alt)}" /></div>')


def common(lang: str, kind: str, d: dict, pages: dict) -> tuple:
    """The values every page fills: its address and alternates, fonts, the header and footer."""
    menu = []
    for other in LANGS:
        o = pages[other]
        current = ' aria-current="page"' if other == lang else ""
        menu.append(f'              <li><a href="{path_of(other, kind)}?lang={other}" hreflang="{other}" lang="{other}"'
                    f' dir="{o["dir"]}"{current}>{esc(o["langName"])}</a></li>')
    hreflang = [f'  <link rel="alternate" hreflang="{o}" href="{BASE}{path_of(o, kind)}" />' for o in LANGS]
    hreflang.append(f'  <link rel="alternate" hreflang="x-default" href="{BASE}{path_of("en", kind)}" />')
    preload = [f'  <link rel="preload" as="font" type="font/woff2" crossorigin href="/fonts/{f}.woff2" />'
               for f in PRELOAD[d["script"]]]
    raw = {
        "hreflang": "\n".join(hreflang),
        "preload": "\n".join(preload),
        "langsJson": json.dumps(LANGS),
        "langMenuItems": "\n".join(menu),
    }
    values = {k: v for k, v in d.items() if isinstance(v, str)}
    values.update(
        url=BASE + path_of(lang, kind), path=path_of(lang), playUrl=PLAY_URL,
        privacyUrl=path_of(lang, "privacy"),
        themeAria=d["themeTpl"].replace("{pref}", d["themeSystem"]),
    )
    return raw, values


def fill(template: str, lang: str, raw: dict, values: dict) -> str:
    """Includes the src/partials/ named by {{> name}}, then fills each {{key}}: raw HTML, or text escaped."""
    template = re.sub(r"\{\{> ([\w-]+)\}\}",
                      lambda m: (ROOT / "src" / "partials" / f"{m.group(1)}.html").read_text(encoding="utf-8").rstrip("\n"),
                      template)

    def value(match: re.Match) -> str:
        key = match.group(1)
        if key in raw:
            return raw[key]
        if key in values:
            return esc(values[key])
        sys.exit(f"build: {lang}: no value for {{{{{key}}}}}")

    return re.sub(r"\{\{(\w+)\}\}", value, template)


def render_home(lang: str, d: dict, pages: dict) -> str:
    raw, values = common(lang, "home", d, pages)
    url = values["url"]
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
            <div class="ti">{icon(t["icon"])}</div>
            <h3>{esc(t["title"])}</h3><p>{esc(t["body"])}</p>
          </div>''' for t in d["tiles"]]
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
    og_alt = [f'  <meta property="og:locale:alternate" content="{pages[o]["ogLocale"]}" />' for o in LANGS if o != lang]
    raw.update({
        "ogAlternates": "\n".join(og_alt),
        "jsonLd": "  " + json.dumps(ld, ensure_ascii=False, indent=2).replace("\n", "\n  ").replace("</", "<\\/"),
        "heroName": hero_name,
        "heroMark": hero_mark(),
        "marquee": "\n".join(phone(lang, s, captions[s], "        ") for s in PHONE_SHOTS),
        "rows": "\n\n".join(rows),
        "tiles": "\n".join(tiles),
    })
    return fill((ROOT / "src" / "home.html").read_text(encoding="utf-8"), lang, raw, values)


def render_privacy(lang: str, d: dict, pages: dict) -> str:
    """The privacy policy: privacy/<lang>.html set in the site's page, its lede as the description."""
    raw, values = common(lang, "privacy", d, pages)
    body = (ROOT / "privacy" / f"{lang}.html").read_text(encoding="utf-8")
    body = re.sub(r"^<!--.*?-->\n", "", body, flags=re.S).strip("\n")
    lede = re.search(r'<p class="lede">(.*?)</p>', body, re.S)
    description = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", lede.group(1)))).strip()
    raw["policy"] = "\n".join(("      " + line) if line else "" for line in body.split("\n"))
    values.update(pageTitle=f'{d["privacy"]} — {d["name"]}', pageDescription=description)
    return fill((ROOT / "src" / "privacy.html").read_text(encoding="utf-8"), lang, raw, values)


RENDER = {"home": render_home, "privacy": render_privacy}


def sitemap(today: str, kinds: list) -> str:
    urls = []
    for kind in kinds:
        alternates = "\n".join(f'    <xhtml:link rel="alternate" hreflang="{o}" href="{BASE}{path_of(o, kind)}"/>'
                               for o in LANGS)
        alternates += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}{path_of("en", kind)}"/>'
        frequency, priority = ("monthly", "1.0") if kind == "home" else ("yearly", "0.5")
        urls += [f"""  <url>
    <loc>{BASE}{path_of(lang, kind)}</loc>
{alternates}
    <lastmod>{today}</lastmod>
    <changefreq>{frequency}</changefreq>
    <priority>{priority}</priority>
  </url>""" for lang in LANGS]
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


# Files whose links carry a ?v=<content hash>, so a returning visitor's browser fetches a changed
# file at once instead of pairing new pages with the stylesheet it cached earlier.
STAMPED = re.compile(r"((?:fonts/[\w-]+\.woff2)|(?:styles\.css)|(?:assets/(?:theme|mark)\.js)|(?:assets/mark[\w-]*\.(?:webp|png)))"
                     r"(\?v=[0-9a-f]+)?")


def stamp(text: str) -> str:
    def version(match: re.Match) -> str:
        digest = hashlib.sha256((ROOT / match.group(1)).read_bytes()).hexdigest()[:10]
        return f"{match.group(1)}?v={digest}"
    return STAMPED.sub(version, text)


def stamp_file(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    stamped = stamp(text)
    if stamped != text:
        path.write_text(stamped, encoding="utf-8")


def main() -> None:
    pages = load()
    kinds = ["home"]
    missing = [lang for lang in LANGS if not (ROOT / "privacy" / f"{lang}.html").exists()]
    if missing:
        print(f"build: privacy policy skipped, no privacy/<lang>.html for {missing}")
    else:
        kinds.append("privacy")
    outputs, texts = [], []
    for kind in kinds:
        for lang, d in pages.items():
            page = RENDER[kind](lang, d, pages)
            out = out_file(lang, kind)
            out.parent.mkdir(exist_ok=True)
            out.write_text(page, encoding="utf-8")
            outputs.append(out)
            texts.append(page)
            print(f"build: {out.relative_to(ROOT)}")
    (ROOT / "sitemap.xml").write_text(sitemap(datetime.date.today().isoformat(), kinds), encoding="utf-8")
    hand_made = [ROOT / "404.html"]
    texts += [p.read_text(encoding="utf-8") for p in hand_made]
    subset_fonts([html.unescape(t) for t in texts])
    # The stylesheet first (its font links change its own hash), then every page that links it.
    stamp_file(ROOT / "styles.css")
    for page in outputs + hand_made:
        stamp_file(page)


if __name__ == "__main__":
    main()
