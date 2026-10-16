"""Build michaelorlov.com into _site/.

No dependencies beyond the standard library. Content lives in content/,
static files in static/, and every page is wrapped by templates/base.html,
which carries the Google Analytics tag.

    python3 build.py              # writes _site/
    python3 build.py --serve      # builds, then serves _site on :8000
    python3 build.py --locales=es,fr   # only those two languages this time

Every page is built once, in English. Each language in content/locales.json is
then a pass over that finished page (see i18n/), published under /<code>/ as
soon as content/i18n/<code>.json covers its text. The build never calls a
translation API: tools/translate.py does that and commits the result, so this
stays offline and deterministic. Hebrew is excluded by request, and i18n/
refuses to build it.
"""
import datetime as dt
import html
import json
import pathlib
import re
import shutil
import struct
import sys

from i18n import locales, memory, segments
from i18n import pages as l10n

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
OUT = ROOT / "_site"

SITE = "https://michaelorlov.com"
GA_ID = "G-NS1LGN6P3Y"  # GA4 account WEB → property michaelorlov.com → web stream "michaelorlov.com"
STUDIO = "Orlov Games"
AUTHOR = "Michael Orlov"
EMAIL = "admin@michaelorlov.com"
DEFAULT_OG = "/img/og-studio.png"
FEED = "/feed.xml"

# A search result cuts a title near 60 characters and a description near 160, so
# the studio suffix is only appended while it still fits, and tools/check.py
# enforces both limits. A page whose own title or description is longer than the
# limit carries "seo_title" / "seo_description" in its front matter.
BRAND = f" — {STUDIO}"
TITLE_MAX = 60
DESC_MAX = 160

# Stable @id values, so the studio and the author stay one entity across pages.
# English is built first and lives at the root; every other language is a
# prefix under it. A language appears only once its translations are committed.
DEFAULT_LOCALE, LANGUAGES = locales.load()
PAGES = {}  # site path -> the finished English page, in build order
LOCALES_MARKER = "@@LOCALES@@"

# The strings the site shows that are on no page, so the walk over the built
# HTML cannot find them. tools/translate.py reads this list, which is why it
# lives here beside the code that prints them.
FEED_TITLE = f"{STUDIO} blog"
FEED_DESCRIPTION = ("Notes from " + STUDIO + " on how the games work underneath: "
                    "paytables, odds, strategy and the maths.")
PICKER_LABEL = "Language"
CHROME = (FEED_TITLE, FEED_DESCRIPTION, PICKER_LABEL)

ORG_ID = SITE + "/#organization"
PERSON_ID = SITE + "/#michael"
SITE_ID = SITE + "/#website"

PLAY_ICON = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3.6 2.2a1 1 0 0 0-.6.9v17.8a1 1 0 0 0 '
    '.6.9l9.5-9.8zM14.4 12.9l2.9 3L5.4 22.6zM5.4 1.4l11.9 6.7-2.9 3zM18.6 8.9l2.7 1.5a1.2 1.2 0 0 1 0 2.2l-2.7 '
    '1.5-3.2-3.1z"/></svg>'
)

esc = html.escape


# ---------------------------------------------------------------- loading


def read_front(path):
    """Split a content file into (meta dict, body) — meta is a JSON object in a leading HTML comment."""
    text = path.read_text()
    m = re.match(r"<!--\s*(\{.*?\})\s*-->\s*", text, re.S)
    if not m:
        raise SystemExit(f"{path}: missing JSON front matter")
    return json.loads(m.group(1)), text[m.end():]


def load_apps():
    apps = json.loads((CONTENT / "apps.json").read_text())
    for app in apps:
        play = json.loads((CONTENT / "play" / f"{app['slug']}.json").read_text())
        app["description"] = play["description"]
        app["screenshots"] = play["screenshots"]
        app["play_url"] = f"https://play.google.com/store/apps/details?id={app['package']}"
        app["url"] = f"/{app['slug']}/"
        app["icon"] = f"/img/apps/{app['slug']}/icon.jpg"
        app["short_name"], _, app["sub_name"] = (s.strip() for s in app["name"].partition(":"))
    return apps


def load_posts(apps_by_slug):
    posts = []
    for path in sorted((CONTENT / "posts").glob("*.html")):
        meta, body = read_front(path)
        if meta["app"] not in apps_by_slug:
            raise SystemExit(f"{path}: unknown app {meta['app']!r}")
        meta.update(slug=path.stem, body=body, url=f"/blog/{path.stem}.html")
        meta.setdefault("modified", meta["date"])
        meta.setdefault("summary", meta["description"])
        meta.setdefault("seo_title", re.sub("<[^>]+>", "", meta["title"]))
        meta.setdefault("seo_description", meta["description"])
        meta["words"] = len(re.sub("<[^>]+>", " ", body).split())
        posts.append(meta)
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


def image_size(path):
    """(width, height) of a JPEG or PNG, read from its header."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    i = 2
    while i < len(data):
        marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    raise ValueError(f"no size in {path}")


# ---------------------------------------------------------------- helpers


def nice_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


def rfc822(iso):
    """ISO date → the date format RSS 2.0 requires for pubDate."""
    d = dt.date.fromisoformat(iso)
    return f"{d:%a, %d %b %Y} 00:00:00 +0000"


def fit_title(core):
    """Add the studio name to a title only while the result still fits a search result."""
    return core + BRAND if len(core) + len(BRAND) <= TITLE_MAX else core


def play_button(app, small=False, label="Get it on Google Play"):
    cls = "play small" if small else "play"
    text = '<span class="long">Get it on</span> Google Play' if small else f"{PLAY_ICON}\n    {label}"
    return f'<a class="{cls}" href="{app["play_url"]}" data-app="{app["slug"]}">{text}</a>'


def jsonld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False, indent=2) + "\n</script>"


def breadcrumb(*items):
    elements = []
    for pos, (name, url) in enumerate(items, 1):
        el = {"@type": "ListItem", "position": pos, "name": name}
        if url:
            el["item"] = SITE + url
        elements.append(el)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": elements}


def post_items(posts, apps_by_slug, show_app=True, summary=False):
    rows = []
    for p in posts:
        app = apps_by_slug[p["app"]]
        tag = f'<a class="tag" href="/blog/{app["slug"]}/">{esc(app["short_name"])}</a>' if show_app else ""
        rows.append(
            f"""    <article class="post-item">
      <time datetime="{p['date']}">{nice_date(p['date'])}</time>
      <div>
        <h3><a href="{p['url']}">{p['title']}</a></h3>
        <p>{p['summary'] if summary else p['description']}</p>{tag}
      </div>
    </article>"""
        )
    return '<div class="post-list">\n' + "\n".join(rows) + "\n  </div>"


def shot_src(app):
    """First screenshot. Video Poker's shots live in /img/; every other app keeps its own folder."""
    name = app["screenshots"][0]
    if (STATIC / "img" / "apps" / app["slug"] / name).exists():
        return f"/img/apps/{app['slug']}/{name}"
    return f"/img/{name}"


def app_cards(apps, current=None):
    cards = []
    i = 0
    for a in apps:
        if a["slug"] == current:
            continue
        state = (
            f'<span class="state soon">Coming soon</span>'
            if a["status"] == "testing"
            else f'<span class="state">{esc(a["category"])}</span>'
        )
        cards.append(
            f"""    <a class="card" href="{a['url']}" data-shot="{shot_src(a)}" data-reveal style="--i:{i}">
      <img src="{a['icon']}" alt="" width="64" height="64" loading="lazy">
      <span class="card-text">
        <strong>{esc(a['short_name'])}</strong>
        <span>{esc(a['tagline'])}</span>
        {state}
      </span>
    </a>"""
        )
        i += 1
    return '<div class="cards">\n' + "\n".join(cards) + "\n  </div>"


def render_description(text):
    """Play Store description → HTML. ALL-CAPS lines become headings, • lines lists, 1. lines ordered lists."""
    out, para, items, kind = [], [], [], None

    def flush():
        nonlocal para, items, kind
        if para:
            out.append("<p>" + "<br>".join(esc(l) for l in para) + "</p>")
        if items:
            tag = "ol" if kind == "ol" else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{esc(i)}</li>" for i in items) + f"</{tag}>")
        para, items, kind = [], [], None

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("•"):
            if para or kind == "ol":
                flush()
            kind = "ul"
            items.append(line.lstrip("• ").strip())
        elif re.match(r"\d+\.\s", line):
            if para or kind == "ul":
                flush()
            kind = "ol"
            items.append(re.sub(r"^\d+\.\s*", "", line))
        elif len(line) < 60 and line == line.upper() and re.search(r"[A-Z]{3}", line):
            flush()
            out.append(f"<h3>{esc(line)}</h3>")
        else:
            if items:
                flush()
            para.append(line)
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- page shell

BASE = (ROOT / "templates" / "base.html").read_text()


def page(path, *, title, description, body, group, og_title=None, og_description=None, og_image=None,
         og_type="website", schema=(), header_app=None, robots=None, canonical=True, extra_head="",
         pre_head="", published=None, modified=None):
    head = []
    if canonical:
        head.append(f'<link rel="canonical" href="{SITE}{path}">')
    if robots:
        head.append(f'<meta name="robots" content="{robots}">')
    og_image = SITE + (og_image or DEFAULT_OG)
    og_title = esc(og_title or title, quote=True)
    og_description = esc(og_description or description, quote=True)
    head += [
        f'<meta property="og:title" content="{og_title}">',
        f'<meta property="og:description" content="{og_description}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:url" content="{SITE}{path}">',
        f'<meta property="og:image" content="{og_image}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{og_title}">',
        f'<meta name="twitter:description" content="{og_description}">',
        f'<meta name="twitter:image" content="{og_image}">',
    ]
    if published:
        head += [
            f'<meta property="article:published_time" content="{published}">',
            f'<meta property="article:modified_time" content="{modified or published}">',
            f'<meta property="article:author" content="{esc(AUTHOR, quote=True)}">',
        ]
    head += [jsonld(s) for s in schema]
    if extra_head:
        head.append(extra_head)
    cta = play_button(header_app, small=True) if header_app and header_app["status"] == "live" else ""
    body = body.replace("<main", '<main id="main"', 1)
    out = BASE
    # The slot sits above the GA tag, so whatever goes in it decides the page's
    # fate before Analytics counts the page.
    out = out.replace("{{ pre_head }}", pre_head + "\n" if pre_head else "", 1)
    for key, value in {
        "ga_id": GA_ID,
        "content_group": group,
        "title": esc(title),
        "description": esc(description, quote=True),
        "head": "\n".join(head),
        "header_cta": cta,
        "blog_current": ' aria-current="page"' if path.startswith("/blog/") else "",
        "body": body.strip(),
        "email": EMAIL,
        "year": str(dt.date.today().year),
    }.items():
        out = out.replace("{{ " + key + " }}", value)
    write(path, out)


def redirect(path, target):
    write(
        path,
        f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Moved — {STUDIO}</title>
<link rel="canonical" href="{SITE}{target}">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace('{target}'+location.search+location.hash);</script>
</head>
<body><p>This page has moved to <a href="{target}">{SITE}{target}</a>.</p></body>
</html>
""",
    )


def exists_exact(path):
    """Case-sensitive existence check: macOS is case-insensitive, Pages is not."""
    cur = OUT
    for part in path.relative_to(OUT).parts:
        if not cur.is_dir() or part not in {c.name for c in cur.iterdir()}:
            return False
        cur = cur / part
    return cur.exists()


def write(path, text):
    """Hold a finished English page. emit() writes it, and its translations."""
    PAGES[path] = text


def write_file(path, text):
    dest = OUT / (path.lstrip("/") + ("index.html" if path.endswith("/") else ""))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)


# ---------------------------------------------------------------- languages


def translatable(path, text):
    """Redirect hops and the 404 shell stay English-only.

    A hop is never read, and GitHub Pages serves one 404 for the whole domain,
    so neither is worth seventy copies.
    """
    return 'http-equiv="refresh"' not in text and path != "/404.html"


def localize_site(requested=None):
    """{path: {code: page}} — every page in every language that can carry it.

    A language publishes a page only when its memory covers every segment on
    it. Anything less would be a page of English served from a Spanish URL,
    which is both a worse page and a duplicate competing with the real one.
    """
    wanted = locales.select(requested, memory.translated_languages(LANGUAGES))
    memories = {loc.code: memory.Memory(loc.code) for loc in wanted}
    built = {}
    for path, text in PAGES.items():
        if not translatable(path, text):
            continue
        texts = segments.extract(text)
        for loc in wanted:
            mem = memories[loc.code]
            if mem.covers(texts):
                built.setdefault(path, {})[loc.code] = l10n.localize(text, path, loc, mem, SITE, texts)
    return built, memories, wanted


def emit(built, memories, wanted):
    """Write every page to disk: English, then each language that has it."""
    by_code = {loc.code: loc for loc in wanted}
    active = json.dumps(sorted({code for page in built.values() for code in page}))
    for path, text in PAGES.items():
        available = [by_code[c] for c in by_code if c in built.get(path, {})]
        available.sort(key=lambda loc: [l.code for l in wanted].index(loc.code))
        english = l10n.finish(text, path, DEFAULT_LOCALE, available, DEFAULT_LOCALE, SITE)
        write_file(path, english.replace(LOCALES_MARKER, active))
        for loc in available:
            label = memories[loc.code].get(PICKER_LABEL) or PICKER_LABEL
            page_html = l10n.finish(built[path][loc.code], path, loc, available,
                                    DEFAULT_LOCALE, SITE, label)
            write_file(loc.path(path), page_html.replace(LOCALES_MARKER, active))


# ---------------------------------------------------------------- pages


def build_home(apps, posts, abs_):
    live = [a for a in apps if a["status"] == "live"]
    testing = [a for a in apps if a["status"] == "testing"]
    featured = next(a for a in apps if a["featured"])
    featured_shot = shot_src(featured)
    fw, fh = image_size(STATIC / featured_shot.lstrip("/"))
    frames = []
    for i, a in enumerate(live[:6]):
        src = shot_src(a)
        w, h = image_size(STATIC / src.lstrip("/"))
        frames.append(
            f"""    <figure data-reveal class="pic" style="--i:{i}">
      <img src="{src}" width="{w}" height="{h}" alt="" decoding="async">
      <figcaption>{esc(a['short_name'])}</figcaption>
    </figure>"""
        )
    body = f"""
<main>
<div class="hero">
  <div class="monument-mask">
    <h1 class="monument">Orlov Games</h1>
  </div>
  <div class="hero-corner">
    <p class="sub">Small games for Android</p>
    <p class="lede">Card tables, casino classics, puzzles and a couple of useful tools, made by Michael Orlov in Israel. The casino games play for chips only: no real money, ever.</p>
    <div class="cta-row">
      <a class="play" href="#apps">See all {len(apps)} apps</a>
      <a class="text-link" href="/blog/">Read the blog</a>
    </div>
  </div>
</div>

<section class="wrap sheet" id="apps">
  <h2 data-reveal>Out now</h2>
  <p class="section-lede" data-reveal style="--i:1">{len(live)} apps on Google Play. Tap one for screenshots, details and its privacy policy.</p>
  <div class="catalog">
    <div class="stage-col">
      <div class="stage">
        <img data-stage src="{featured_shot}" width="{fw}" height="{fh}" alt="" fetchpriority="high" decoding="async">
      </div>
      <a class="feature" href="{featured['url']}">
        <strong>{esc(featured['name'])}</strong>
        <span class="feature-label">Most played</span>
        <span>{esc(featured['tagline'])}</span>
      </a>
    </div>
    {app_cards(live)}
  </div>
</section>

<section class="gallery wrap" id="screens">
{chr(10).join(frames)}
</section>

<section class="wrap sheet" id="testing">
  <h2 data-reveal>In testing</h2>
  <p class="section-lede" data-reveal style="--i:1">In closed testing on Google Play, and public as soon as they are ready.</p>
  {app_cards(testing)}
</section>

<section class="wrap sheet" id="blog">
  <h2 data-reveal>From the blog</h2>
  <p class="section-lede" data-reveal style="--i:1">How these games work underneath: paytables, odds, strategy and the maths behind the machines.</p>
  {post_items(posts[:5], abs_, summary=True)}
  <p class="more"><a href="/blog/">All {len(posts)} posts</a></p>
</section>
</main>
"""
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": STUDIO,
            "url": SITE + "/",
            "logo": SITE + "/img/mark-512.png",
            "email": EMAIL,
            "@id": ORG_ID,
            "founder": {"@type": "Person", "@id": PERSON_ID, "name": AUTHOR},
            "sameAs": ["https://play.google.com/store/apps/dev?id=6720418432540497347"],
        },
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": SITE_ID,
            "name": STUDIO,
            "url": SITE + "/",
            "inLanguage": "en",
            "publisher": {"@id": ORG_ID},
        },
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"Apps by {STUDIO}",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "url": SITE + a["url"], "name": a["name"]}
                for i, a in enumerate(apps, 1)
            ],
        },
    ]
    page(
        "/",
        title=f"{STUDIO}: Android games and apps by Michael Orlov",
        description=f"{len(apps)} Android games and apps by Michael Orlov: video poker, blackjack, Omaha, slots, dominoes, pool and block puzzles. Most play offline, none for real money.",
        og_title=STUDIO,
        body=body,
        group="Home",
        schema=schema,
    )


def app_schema(app, screenshots):
    s = {
        "@context": "https://schema.org",
        "@type": "MobileApplication",
        "name": app["name"],
        "operatingSystem": "Android",
        "applicationCategory": "UtilitiesApplication" if app["category"] in ("Tools", "Video tools") else "GameApplication",
        "description": app["tagline"],
        "url": SITE + app["url"],
        "image": SITE + app["icon"],
        "screenshot": [SITE + s for s in screenshots],
        "inLanguage": "en",
        "author": {"@type": "Person", "@id": PERSON_ID, "name": AUTHOR},
        "publisher": {"@type": "Organization", "@id": ORG_ID, "name": STUDIO, "email": EMAIL},
    }
    if app["status"] == "live":
        s["installUrl"] = app["play_url"]
        s["isAccessibleForFree"] = True
        s["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
    return s


def app_posts_section(app, posts, abs_, heading="From the blog"):
    mine = [p for p in posts if p["app"] == app["slug"]]
    if not mine:
        return ""
    more = f'\n  <p class="more"><a href="/blog/{app["slug"]}/">All {len(mine)} {esc(app["short_name"])} posts</a></p>' if len(mine) > 5 else ""
    return f"""<section class="wrap sheet" id="blog">
  <h2>{heading}</h2>
  <p class="section-lede">Notes on how {esc(app['short_name'])} works underneath.</p>
  {post_items(mine[:5], abs_, show_app=False, summary=True)}{more}
</section>"""


def more_apps_section(app, apps):
    return f"""<section class="wrap" id="more">
  <h2>More from {STUDIO}</h2>
  <p class="section-lede">Everything else on Google Play, and what is coming next.</p>
  {app_cards(apps, current=app['slug'])}
</section>"""


def build_app(app, apps, posts, abs_):
    if (CONTENT / "apps" / f"{app['slug']}.html").exists():
        return build_custom_app(app, apps, posts, abs_)
    shots = []
    for name in app["screenshots"]:
        src = f"/img/apps/{app['slug']}/{name}"
        w, h = image_size(STATIC / src.lstrip("/"))
        shots.append(f'    <img src="{src}" width="{w}" height="{h}" loading="lazy" alt="{esc(app["short_name"])} screenshot">')
    wide = "wide" if shots and image_size(STATIC / f"img/apps/{app['slug']}/{app['screenshots'][0]}")[0] > 600 else ""
    if app["status"] == "live":
        cta = f"""{play_button(app)}
        <p class="cta-note">Free on Google Play. {esc(app['category'])}.</p>"""
    else:
        cta = """<span class="badge-soon">Coming soon</span>
        <p class="cta-note">In closed testing on Google Play. This page will link to the store listing when it goes public.</p>"""
    privacy = (
        f'<a href="{app["privacy_url"]}">Privacy policy</a>'
        if app["privacy_url"]
        else "Privacy policy on request"
    )
    sub = f'<span class="sub">{esc(app["sub_name"])}</span>' if app["sub_name"] else ""
    body = f"""
<main>
<div class="hero wrap app-hero">
  <img class="app-icon" src="{app['icon']}" alt="" width="112" height="112" fetchpriority="high" decoding="async">
  <h1>{esc(app['short_name'])}{sub}</h1>
  <p class="lede">{esc(app['tagline'])}</p>
  <div class="cta-row">
        {cta}
  </div>
</div>

<section class="wrap sheet" id="screens">
  <h2>What it looks like</h2>
  <div class="strip {wide}">
{chr(10).join(shots)}
  </div>
</section>

<section class="wrap" id="about">
  <h2>About the {'app' if app['category'] in ('Tools', 'Video tools') else 'game'}</h2>
  <div class="listing">
{render_description(app['description'])}
  </div>
  <dl class="facts">
    <div class="fact"><dt>Category</dt><dd>{esc(app['category'])}</dd></div>
    <div class="fact"><dt>Status</dt><dd>{'On Google Play' if app['status'] == 'live' else 'Closed testing'}</dd></div>
    <div class="fact"><dt>Package</dt><dd><code>{app['package']}</code></dd></div>
    <div class="fact"><dt>Privacy</dt><dd>{privacy}</dd></div>
    <div class="fact"><dt>Contact</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd></div>
  </dl>
</section>

{app_posts_section(app, posts, abs_)}

{more_apps_section(app, apps)}
</main>
"""
    shot_urls = [f"/img/apps/{app['slug']}/{n}" for n in app["screenshots"]]
    page(
        app["url"],
        title=fit_title(f"{app['name']} for Android"),
        description=f"{app['tagline']} {'Free on Google Play' if app['status'] == 'live' else 'Coming soon to Google Play'}, from {STUDIO}.",
        og_title=app["name"],
        og_image=shot_urls[0] if wide else None,
        body=body,
        group=app["slug"],
        header_app=app,
        schema=[app_schema(app, shot_urls), breadcrumb(("Home", "/"), (app["short_name"], None))],
    )


def build_custom_app(app, apps, posts, abs_):
    meta, body = read_front(CONTENT / "apps" / f"{app['slug']}.html")
    body = body.replace("<!-- @posts -->", app_posts_section(app, posts, abs_, "How these games work"))
    body = body.replace("<!-- @more-apps -->", more_apps_section(app, apps))
    page(
        app["url"],
        title=meta["title"],
        description=meta["description"],
        og_title=meta.get("og_title"),
        og_description=meta.get("og_description"),
        og_image=meta.get("og_image"),
        body=f"<main>\n{body}\n</main>",
        group=app["slug"],
        header_app=app,
        schema=meta.get("jsonld", []) + [breadcrumb(("Home", "/"), (app["short_name"], None))],
    )


def blog_schema(posts, url, name):
    return {
        "@context": "https://schema.org",
        "@type": "Blog",
        "@id": SITE + url,
        "name": name,
        "publisher": {"@type": "Organization", "name": STUDIO},
        "blogPost": [
            {"@type": "BlogPosting", "headline": re.sub("<[^>]+>", "", p["title"]), "url": SITE + p["url"],
             "datePublished": p["date"], "description": p["description"]}
            for p in posts
        ],
    }


def blog_filters(apps, posts, current=None):
    counts = {}
    for p in posts:
        counts[p["app"]] = counts.get(p["app"], 0) + 1
    chips = [f'<a class="chip{" on" if current is None else ""}" href="/blog/">All <span>{len(posts)}</span></a>']
    for a in apps:
        if a["slug"] in counts:
            on = " on" if a["slug"] == current else ""
            chips.append(f'<a class="chip{on}" href="/blog/{a["slug"]}/">{esc(a["short_name"])} <span>{counts[a["slug"]]}</span></a>')
    return '<nav class="chips" aria-label="Filter posts by app">' + "".join(chips) + "</nav>"


def build_blog(apps, posts, abs_):
    page(
        "/blog/",
        title=fit_title("Blog — how our games work"),
        description="Notes from Orlov Games on how the games work underneath: video poker paytables and strategy, odds, variance, shuffling and the maths behind the machines.",
        og_title=f"{STUDIO} blog",
        body=f"""
<main class="post wrap">
  <div class="post-head">
    <h1>Blog</h1>
    <p class="standfirst">Notes on how these games actually work: paytables, odds, strategy, and the maths underneath.</p>
  </div>
  {blog_filters(apps, posts)}
  {post_items(posts, abs_)}
</main>
""",
        group="Blog",
        schema=[blog_schema(posts, "/blog/", f"{STUDIO} blog"), breadcrumb(("Home", "/"), ("Blog", None))],
    )
    for app in apps:
        mine = [p for p in posts if p["app"] == app["slug"]]
        if not mine:
            continue
        url = f"/blog/{app['slug']}/"
        page(
            url,
            title=fit_title(f"{app['short_name']} blog"),
            description=f"Every {STUDIO} post about {app['short_name']}: {len(mine)} notes on strategy, odds and how the game works.",
            body=f"""
<main class="post wrap">
  <div class="post-head">
    <p class="trail"><a href="/blog/">Blog</a></p>
    <h1>{esc(app['short_name'])}</h1>
    <p class="standfirst">Posts about <a href="{app['url']}">{esc(app['name'])}</a>, newest first.</p>
  </div>
  {blog_filters(apps, posts, app['slug'])}
  {post_items(mine, abs_, show_app=False)}
</main>
""",
            group="Blog",
            header_app=app,
            schema=[blog_schema(mine, url, f"{app['short_name']} blog"),
                    breadcrumb(("Home", "/"), ("Blog", "/blog/"), (app["short_name"], None))],
        )
    for p in posts:
        build_post(p, posts, abs_)


def post_sequence(older, newer):
    """Previous/next links between posts about the same game, so every post is reachable."""
    links = []
    if older:
        links.append(f'<a class="seq older" href="{older["url"]}"><span>Previous post</span>{older["title"]}</a>')
    if newer:
        links.append(f'<a class="seq newer" href="{newer["url"]}"><span>Next post</span>{newer["title"]}</a>')
    if not links:
        return ""
    return ('<nav class="post-seq wrap-inner" aria-label="More posts about this game">'
            + "".join(links) + "</nav>")


def build_post(p, posts, abs_):
    app = abs_[p["app"]]
    plain = re.sub("<[^>]+>", "", p["title"])
    mine = [q for q in posts if q["app"] == p["app"]]
    i = mine.index(p)
    older = mine[i + 1] if i + 1 < len(mine) else None
    newer = mine[i - 1] if i else None
    related = [q for q in mine if q["slug"] != p["slug"]][:3]
    if len(related) < 3:
        # A game's first posts have nothing of their own to point at, so top the
        # list up with the newest posts about anything else.
        seen = {q["slug"] for q in related} | {p["slug"]}
        related += [q for q in posts if q["slug"] not in seen][: 3 - len(related)]
    same_app = all(q["app"] == p["app"] for q in related)
    more = (
        f"""
  <aside class="related wrap-inner">
    <h2>{'More on ' + esc(app['short_name']) if same_app else 'More from the blog'}</h2>
    {post_items(related, abs_, show_app=not same_app, summary=True)}
  </aside>"""
        if related
        else ""
    )
    page(
        p["url"],
        title=fit_title(p["seo_title"]),
        description=p["seo_description"],
        og_title=plain,
        og_type="article",
        og_image="/img/og-card.png" if p["app"] == "VideoPoker" else None,
        published=p["date"],
        modified=p["modified"],
        body=f"""
<main class="post wrap">
  <div class="post-head">
    <p class="trail"><a href="/blog/">Blog</a> · <a href="/blog/{app['slug']}/">{esc(app['short_name'])}</a> · <time datetime="{p['date']}">{nice_date(p['date'])}</time></p>
    <h1>{p['title']}</h1>
    <p class="standfirst">{p['standfirst']}</p>
  </div>

  <article class="post-body">
{p['body'].strip()}
  </article>
{post_sequence(older, newer)}
{more}
</main>
""",
        group=app["slug"],
        header_app=app,
        schema=[
            {
                "@context": "https://schema.org",
                "@type": "BlogPosting",
                "headline": plain,
                "description": p["description"],
                "datePublished": p["date"],
                "dateModified": p["modified"],
                "inLanguage": "en",
                "wordCount": p["words"],
                "articleSection": app["short_name"],
                "author": {"@type": "Person", "@id": PERSON_ID, "name": AUTHOR},
                "publisher": {"@type": "Organization", "@id": ORG_ID, "name": STUDIO,
                              "logo": {"@type": "ImageObject", "url": SITE + "/img/mark-512.png"}},
                "image": SITE + ("/img/og-card.png" if p["app"] == "VideoPoker" else DEFAULT_OG),
                "mainEntityOfPage": {"@type": "WebPage", "@id": SITE + p["url"]},
                "isPartOf": {"@type": "Blog", "@id": SITE + "/blog/", "name": f"{STUDIO} blog"},
                "about": {"@type": "MobileApplication", "name": app["name"], "url": SITE + app["url"]},
            },
            breadcrumb(("Home", "/"), ("Blog", "/blog/"), (app["short_name"], f"/blog/{app['slug']}/"), (plain, None)),
        ],
    )


def build_legal(apps, abs_):
    for path in sorted((CONTENT / "legal").glob("*.html")):
        meta, body = read_front(path)
        policies = "\n".join(
            f'  <li><a href="{a["privacy_url"]}">{esc(a["name"])}</a></li>' if a["privacy_url"]
            else f'  <li>{esc(a["name"])}: write to <a href="mailto:{EMAIL}">{EMAIL}</a></li>'
            for a in apps
        )
        body = body.replace("<!-- @app-policies -->", f"<ul>\n{policies}\n</ul>")
        page(
            meta["path"],
            title=meta["title"],
            description=meta["description"],
            body=f'<main class="doc wrap">\n{body}\n</main>',
            group="Legal",
            header_app=abs_.get(meta.get("app")),
            robots="noindex, follow",
        )


def build_404(apps):
    # GitHub Pages paths are case-sensitive; send /videopoker, /OMAHAPOKER/ etc. to the real page.
    known = {}
    for a in apps:
        known[a["url"].lower()] = a["url"]
        known[f"/blog/{a['slug']}/".lower()] = f"/blog/{a['slug']}/"
    # This runs before the GA tag. A hit that is really a redirect sets the flag
    # and leaves, so it is never counted as a visit to "Page not found"; only a
    # genuine miss reaches gtag.
    # A miss inside a language keeps its language: /es/videopoker goes to
    # /es/VideoPoker/, not to the English page. The locale list is filled in at
    # emit(), once it is known which languages were actually published.
    script = (
        "<script>(function(){var m=" + json.dumps(known) + ",L=" + LOCALES_MARKER + ";"
        "var p=location.pathname.toLowerCase(),pre='';"
        "for(var i=0;i<L.length;i++){var c='/'+L[i].toLowerCase();"
        "if(p===c||p.indexOf(c+'/')===0){pre='/'+L[i];p=p.slice(c.length)||'/';break;}}"
        "if(!p.endsWith('/'))p+='/';"
        "var t=m[p];if(t&&pre+t!==location.pathname){window.__redirecting=true;"
        "location.replace(pre+t+location.search+location.hash);}})();</script>"
    )
    page(
        "/404.html",
        title=fit_title("Page not found"),
        description="This page does not exist.",
        body="""
<main class="doc wrap">
  <h1>Page not found</h1>
  <p>Nothing lives at this address. Try the <a href="/">list of apps</a> or the <a href="/blog/">blog</a>.</p>
</main>
""",
        group="404",
        robots="noindex",
        canonical=False,
        pre_head=script,
    )


def build_sitemap(apps, posts, built):
    latest = posts[0]["modified"] if posts else None
    def app_mod(a):
        # An app page lists its own posts, so it genuinely changes when one lands.
        mine = [p["modified"] for p in posts if p["app"] == a["slug"]]
        return max(mine) if mine else None

    urls = [("/", latest)] + [(a["url"], app_mod(a)) for a in apps] + [("/blog/", latest)]
    for a in apps:
        mine = [p for p in posts if p["app"] == a["slug"]]
        if mine:
            urls.append((f"/blog/{a['slug']}/", max(p["modified"] for p in mine)))
    urls += [(p["url"], p["modified"]) for p in posts]
    # Every language that carries a page is listed under its own URL. The
    # hreflang set that ties them together is on the pages themselves.
    rows = "\n".join(
        f"  <url><loc>{SITE}{prefix + u}</loc>"
        + (f"<lastmod>{m}</lastmod>" if m else "") + "</url>"
        for u, m in urls
        for prefix in [""] + [f"/{code}" for code in sorted(built.get(u, {}))]
    )
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'
    )


def build_feed(posts, abs_, locale, mem=None, built=None):
    """The RSS feed for one language, at /feed.xml or /<code>/feed.xml.

    A language's feed carries only the posts that language actually publishes,
    so a reader is never handed an English article through a Spanish feed. A
    language with no posts yet still gets an empty feed, because every page in
    it links to one.
    """
    def say(text):
        return (mem.get(text) if mem else None) or text

    mine = [p for p in posts
            if locale.is_default or locale.code in (built or {}).get(p["url"], {})]
    items = []
    for p in mine[:20]:
        app = abs_[p["app"]]
        items.append(
            f"""  <item>
    <title>{esc(say(re.sub("<[^>]+>", "", p["title"])))}</title>
    <link>{SITE}{locale.path(p['url'])}</link>
    <guid isPermaLink="true">{SITE}{locale.path(p['url'])}</guid>
    <pubDate>{rfc822(p['date'])}</pubDate>
    <category>{esc(app['short_name'])}</category>
    <description>{esc(say(p['description']))}</description>
  </item>"""
        )
    feed_url = locale.path(FEED)
    newest = mine[0]["modified"] if mine else posts[0]["modified"]
    (OUT / feed_url.lstrip("/")).parent.mkdir(parents=True, exist_ok=True)
    (OUT / feed_url.lstrip("/")).write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{esc(say(FEED_TITLE))}</title>
  <link>{SITE}{locale.path('/blog/')}</link>
  <atom:link href="{SITE}{feed_url}" rel="self" type="application/rss+xml"/>
  <description>{esc(say(FEED_DESCRIPTION))}</description>
  <language>{locale.code}</language>
  <lastBuildDate>{rfc822(newest)}</lastBuildDate>
{chr(10).join(items)}
</channel>
</rss>
"""
    )


def collect():
    """Build every English page into PAGES, touching no disk. (apps, posts, abs_)

    tools/translate.py calls this to learn what text the site contains without
    producing a site.
    """
    PAGES.clear()
    apps = load_apps()
    abs_ = {a["slug"]: a for a in apps}
    posts = load_posts(abs_)
    build_home(apps, posts, abs_)
    for app in apps:
        build_app(app, apps, posts, abs_)
    build_blog(apps, posts, abs_)
    build_legal(apps, abs_)
    build_404(apps)
    redirect("/terms.html", "/VideoPoker/terms.html")
    return apps, posts, abs_


def main():
    requested = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--locales=")), None)
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    apps, posts, abs_ = collect()

    built, memories, wanted = localize_site(requested)
    emit(built, memories, wanted)
    published = sorted({code for page in built.values() for code in page})
    build_sitemap(apps, posts, built)
    build_feed(posts, abs_, DEFAULT_LOCALE)
    for loc in wanted:
        if loc.code in published:
            build_feed(posts, abs_, loc, memories[loc.code], built)

    languages = f"{len(published) + 1} languages" if published else "English only"
    print(f"built {sum(1 for _ in OUT.rglob('*.html'))} pages into "
          f"{OUT.relative_to(ROOT)}/ ({languages})")

    if "--serve" in sys.argv:
        import functools, http.server, io, urllib.parse

        class Pages(http.server.SimpleHTTPRequestHandler):
            """Serve _site the way GitHub Pages does, so what works here works live.

            Paths are case-sensitive and a miss returns 404.html with a real 404.
            On macOS alone, /videopoker/ would quietly resolve to /VideoPoker/ and
            hide both the broken link and the redirect that handles it.
            """

            def send_head(self):
                rel = urllib.parse.unquote(urllib.parse.urlparse(self.path).path).lstrip("/")
                if rel.endswith("/") or not rel:
                    rel += "index.html"
                if exists_exact(OUT / rel):
                    return super().send_head()
                body = (OUT / "404.html").read_bytes()
                self.send_response(404)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                return io.BytesIO(body)

        handler = functools.partial(Pages, directory=str(OUT))
        print("serving http://localhost:8000")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()


if __name__ == "__main__":
    main()
