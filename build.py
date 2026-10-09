"""Build michaelorlov.com into _site/.

No dependencies beyond the standard library. Content lives in content/,
static files in static/, and every page is wrapped by templates/base.html,
which carries the Google Analytics tag.

    python3 build.py           # writes _site/
    python3 build.py --serve   # builds, then serves _site on :8000
"""
import datetime as dt
import html
import json
import pathlib
import re
import shutil
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
OUT = ROOT / "_site"

SITE = "https://michaelorlov.com"
GA_ID = "G-S6E36TV2PC"  # GA4 property android-34c9a → web stream "michaelorlov.com"
STUDIO = "Orlov Games"
EMAIL = "admin@michaelorlov.com"
DEFAULT_OG = "/img/og-studio.png"

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


def app_cards(apps, current=None):
    cards = []
    for a in apps:
        if a["slug"] == current:
            continue
        state = (
            f'<span class="state soon">Coming soon</span>'
            if a["status"] == "testing"
            else f'<span class="state">{esc(a["category"])}</span>'
        )
        cards.append(
            f"""    <a class="card" href="{a['url']}">
      <img src="{a['icon']}" alt="" width="64" height="64" loading="lazy">
      <span class="card-text">
        <strong>{esc(a['short_name'])}</strong>
        <span>{esc(a['tagline'])}</span>
        {state}
      </span>
    </a>"""
        )
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
         og_type="website", schema=(), header_app=None, robots=None, canonical=True, extra_head=""):
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
    head += [jsonld(s) for s in schema]
    if extra_head:
        head.append(extra_head)
    cta = play_button(header_app, small=True) if header_app and header_app["status"] == "live" else ""
    out = BASE
    for key, value in {
        "ga_id": GA_ID,
        "content_group": group,
        "title": esc(title),
        "description": esc(description, quote=True),
        "head": "\n".join(head),
        "header_cta": cta,
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
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}',{{content_group:'Redirect'}});location.replace('{target}'+location.hash);</script>
</head>
<body><p>This page has moved to <a href="{target}">{SITE}{target}</a>.</p></body>
</html>
""",
    )


def write(path, text):
    dest = OUT / (path.lstrip("/") + ("index.html" if path.endswith("/") else ""))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)


# ---------------------------------------------------------------- pages


def build_home(apps, posts, abs_):
    live = [a for a in apps if a["status"] == "live"]
    testing = [a for a in apps if a["status"] == "testing"]
    featured = next(a for a in apps if a["featured"])
    body = f"""
<main>
<div class="hero wrap">
  <h1>Orlov Games<span class="sub">Small games for Android</span></h1>
  <div class="hero-grid">
    <div>
      <p class="lede">Card tables, casino classics, puzzles and a couple of useful tools, made by Michael Orlov in Israel. The casino games play for chips only: no real money, ever.</p>
      <div class="cta-row">
        <a class="play" href="#apps">See all {len(apps)} apps</a>
        <a class="text-link" href="/blog/">Read the blog</a>
      </div>
    </div>
    <a class="feature" href="{featured['url']}">
      <img src="{featured['icon']}" alt="" width="120" height="120">
      <span class="feature-label">Most played</span>
      <strong>{esc(featured['name'])}</strong>
      <span>{esc(featured['tagline'])}</span>
    </a>
  </div>
</div>

<section class="wrap" id="apps">
  <h2>Out now</h2>
  <p class="section-lede">{len(live)} apps on Google Play. Tap one for screenshots, details and its privacy policy.</p>
  {app_cards(live)}
</section>

<section class="wrap" id="testing">
  <h2>In testing</h2>
  <p class="section-lede">In closed testing on Google Play, and public as soon as they are ready.</p>
  {app_cards(testing)}
</section>

<section class="wrap" id="blog">
  <h2>From the blog</h2>
  <p class="section-lede">How these games work underneath: paytables, odds, strategy and the maths behind the machines.</p>
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
            "founder": {"@type": "Person", "name": "Michael Orlov"},
            "sameAs": ["https://play.google.com/store/apps/dev?id=6720418432540497347"],
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
        description=f"{len(apps)} Android apps from {STUDIO}: video poker, blackjack, Omaha, slots, dominoes, pool, block puzzles and more. Most play offline, and the casino games never use real money.",
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
        "author": {"@type": "Person", "name": "Michael Orlov"},
        "publisher": {"@type": "Organization", "name": STUDIO, "email": EMAIL},
    }
    if app["status"] == "live":
        s["installUrl"] = app["play_url"]
        s["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
    return s


def app_posts_section(app, posts, abs_, heading="From the blog"):
    mine = [p for p in posts if p["app"] == app["slug"]]
    if not mine:
        return ""
    more = f'\n  <p class="more"><a href="/blog/{app["slug"]}/">All {len(mine)} {esc(app["short_name"])} posts</a></p>' if len(mine) > 5 else ""
    return f"""<section class="wrap" id="blog">
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
  <img class="app-icon" src="{app['icon']}" alt="" width="112" height="112">
  <h1>{esc(app['short_name'])}{sub}</h1>
  <p class="lede">{esc(app['tagline'])}</p>
  <div class="cta-row">
        {cta}
  </div>
</div>

<section class="wrap" id="screens">
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
        title=f"{app['name']} for Android — {STUDIO}",
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
        title=f"Blog — how our games work — {STUDIO}",
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
            title=f"{app['short_name']} blog — {STUDIO}",
            description=f"Every {STUDIO} post about {app['short_name']}: {len(mine)} notes on strategy, odds and how the game works.",
            body=f"""
<main class="post wrap">
  <div class="post-head">
    <p class="kicker"><a href="/blog/">Blog</a></p>
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


def build_post(p, posts, abs_):
    app = abs_[p["app"]]
    plain = re.sub("<[^>]+>", "", p["title"])
    related = [q for q in posts if q["app"] == p["app"] and q["slug"] != p["slug"]][:3]
    more = (
        f"""
  <aside class="related wrap-inner">
    <h2>More on {esc(app['short_name'])}</h2>
    {post_items(related, abs_, show_app=False, summary=True)}
  </aside>"""
        if related
        else ""
    )
    page(
        p["url"],
        title=f"{plain} — {STUDIO}",
        description=p["description"],
        og_title=plain,
        og_type="article",
        og_image="/img/og-card.png" if p["app"] == "VideoPoker" else None,
        body=f"""
<main class="post wrap">
  <div class="post-head">
    <p class="kicker"><a href="/blog/">Blog</a> · <a href="/blog/{app['slug']}/">{esc(app['short_name'])}</a> · <time datetime="{p['date']}">{nice_date(p['date'])}</time></p>
    <h1>{p['title']}</h1>
    <p class="standfirst">{p['standfirst']}</p>
  </div>

  <article class="post-body">
{p['body'].strip()}
  </article>
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
                "author": {"@type": "Person", "name": "Michael Orlov"},
                "publisher": {"@type": "Organization", "name": STUDIO,
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
    script = (
        "<script>(function(){var m=" + json.dumps(known) + ";"
        "var p=location.pathname.toLowerCase();if(!p.endsWith('/'))p+='/';"
        "if(m[p]&&m[p]!==location.pathname)location.replace(m[p]+location.search+location.hash);})();</script>"
    )
    page(
        "/404.html",
        title=f"Page not found — {STUDIO}",
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
        extra_head=script,
    )


def build_sitemap(apps, posts):
    latest = posts[0]["modified"] if posts else None
    urls = [("/", latest)] + [(a["url"], None) for a in apps] + [("/blog/", latest)]
    for a in apps:
        mine = [p for p in posts if p["app"] == a["slug"]]
        if mine:
            urls.append((f"/blog/{a['slug']}/", max(p["modified"] for p in mine)))
    urls += [(p["url"], p["modified"]) for p in posts]
    rows = "\n".join(
        f"  <url><loc>{SITE}{u}</loc>" + (f"<lastmod>{m}</lastmod>" if m else "") + "</url>" for u, m in urls
    )
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'
    )


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
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
    build_sitemap(apps, posts)
    print(f"built {sum(1 for _ in OUT.rglob('*.html'))} pages into {OUT.relative_to(ROOT)}/")

    if "--serve" in sys.argv:
        import functools, http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("serving http://localhost:8000")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()


if __name__ == "__main__":
    main()
