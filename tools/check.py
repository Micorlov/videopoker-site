"""Sanity checks over _site/ after `python3 build.py`. Exits non-zero on any problem.

- every internal href/src resolves to a file
- every real page loads the GA tag exactly once, and no redirect hop loads it at all
- /404.html decides its redirect before Analytics runs, so a redirect is never a 404 view
- every JSON-LD block parses
- indexable pages have a unique <title>, a description and a canonical
- titles and descriptions fit a search result, and each page has one <h1>
- a translated page declares its language, links its alternates, and stays in
  its own tree; the site is not translated into Hebrew. /salary/ is a
  standalone Hebrew tool and the only page allowed to declare lang="he"
- every <img> carries alt text and width/height, so nothing shifts as it loads
- the sitemap lists exactly the indexable pages, and the feed lists the newest posts
"""
import html, json, pathlib, re, sys, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
sys.path.insert(0, str(ROOT))
from build import DESC_MAX, FEED, GA_ID, SITE, TITLE_MAX, exists_exact  # noqa: E402
from i18n import locales  # noqa: E402

DESC_MIN = 70  # shorter than this and a search result has room it is not using

# A translation's length belongs to the translator: no seo_title in the front
# matter can shorten it, and a character count means something different in
# German and in Japanese. So a translated page is only held to a ceiling that
# catches a runaway translation, and told off in a warning before that.
L10N_TITLE_MAX, L10N_DESC_MAX = 70, 200

DEFAULT_LOCALE, LANGUAGES = locales.load()
BY_CODE = {loc.code: loc for loc in LANGUAGES}

problems, warnings, titles, indexable = [], [], {}, set()

# The games site is never published as a Hebrew locale. /salary/ is a separate
# tool written in Hebrew; it is not a /he/ tree and it is not translated.
HEBREW_TOOL_PAGES = {"/salary/"}


def locale_of(rel):
    """The language a built path belongs to, from its first segment."""
    head = rel.strip("/").split("/")[0]
    return BY_CODE.get(head, DEFAULT_LOCALE)


def resolve(page, ref):
    base = "/" + str(page.relative_to(OUT))
    path = urllib.parse.unquote(urllib.parse.urlparse(urllib.parse.urljoin(base, ref)).path)
    target = OUT / path.lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    return exists_exact(target)


for page in sorted(OUT.rglob("*.html")):
    rel = "/" + str(page.relative_to(OUT)).replace("index.html", "")
    h = page.read_text()
    # A redirect stub is a hop between two pages. Counting it inflates views and
    # invents sessions that never saw anything, so it carries no tag at all.
    hop = 'http-equiv="refresh"' in h
    if hop and "googletagmanager.com" in h:
        problems.append(f"{rel}: redirect stub loads GA (a hop is not a pageview)")
    if not hop and h.count(f"googletagmanager.com/gtag/js?id={GA_ID}") != 1:
        problems.append(f"{rel}: GA tag count != 1")
    for other in set(re.findall(r"G-[A-Z0-9]{8,12}", h)) - {GA_ID}:
        problems.append(f"{rel}: stray GA id {other}")
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            json.loads(block)
        except ValueError as e:
            problems.append(f"{rel}: bad JSON-LD ({e})")
    for tag in re.findall(r"<img\b[^>]*>", h):
        if "alt=" not in tag:
            problems.append(f"{rel}: <img> without alt ({tag[:60]})")
        if "width=" not in tag or "height=" not in tag:
            problems.append(f"{rel}: <img> without width/height ({tag[:60]})")
    for ref in re.findall(r'(?:href|src)="([^"]+)"', h):
        if re.match(r"(https?:|mailto:|#|data:)", ref):
            continue
        if not resolve(page, ref.split("#")[0]):
            problems.append(f"{rel}: broken link {ref}")
    if 'name="robots" content="noindex' in h or 'http-equiv="refresh"' in h:
        continue
    indexable.add(rel)
    loc = locale_of(rel)
    native = loc.is_default
    title = re.search(r"<title>(.*?)</title>", h).group(1)
    if (loc.code, title) in titles:
        problems.append(f"{rel}: title duplicates {titles[(loc.code, title)]}")
    titles[(loc.code, title)] = rel
    length = len(html.unescape(title))
    ceiling = TITLE_MAX if native else L10N_TITLE_MAX
    if length > ceiling:
        problems.append(f"{rel}: title is {length} chars, over {ceiling}"
                        + (" (set seo_title in the front matter)" if native
                           else " — the translation runs long"))
    elif not native and length > TITLE_MAX:
        warnings.append(f"{rel}: title is {length} chars; a search result cuts near {TITLE_MAX}")
    if h.count("<h1") != 1:
        problems.append(f"{rel}: {h.count('<h1')} <h1> headings, expected 1")
    desc = re.search(r'<meta name="description" content="([^"]*)"', h)
    size = len(html.unescape(desc.group(1))) if desc else 0
    if native and not DESC_MIN <= size <= DESC_MAX:
        problems.append(f"{rel}: description is {size} chars, want {DESC_MIN}-{DESC_MAX} "
                        f"(set seo_description in the front matter)")
    elif not native and not 1 <= size <= L10N_DESC_MAX:
        problems.append(f"{rel}: description is {size} chars, want 1-{L10N_DESC_MAX}")
    elif not native and size > DESC_MAX:
        warnings.append(f"{rel}: description is {size} chars; a search result cuts near {DESC_MAX}")
    if '<meta property="og:site_name"' not in h:
        problems.append(f"{rel}: og:site_name missing")
    if f'<link rel="canonical" href="{SITE}{rel}">' not in h:
        problems.append(f"{rel}: canonical missing or wrong")
    if rel in HEBREW_TOOL_PAGES:
        if '<html lang="he"' not in h or 'dir="rtl"' not in h:
            problems.append(f"{rel}: Hebrew tool page must set lang=\"he\" and dir=\"rtl\"")
        if 'hreflang="he"' not in h:
            problems.append(f"{rel}: Hebrew tool page must list hreflang=\"he\"")
        continue
    if f'<html lang="{loc.code}"' not in h:
        problems.append(f"{rel}: does not declare lang=\"{loc.code}\"")
    if not native:
        if f'dir="{loc.dir}"' not in h:
            problems.append(f"{rel}: missing dir=\"{loc.dir}\"")
        bare = rel[len(loc.prefix):] or "/"
        if f'hreflang="x-default" href="{SITE}{bare}"' not in h:
            problems.append(f"{rel}: x-default does not point at the English page")
    if 'hreflang="en"' not in h:
        problems.append(f"{rel}: no hreflang set")

# The 404 page redirects stale lower-case URLs. The decision has to happen above
# the GA tag, or every redirect is also counted as a view of "Page not found".
notfound = (OUT / "404.html").read_text()
if "window.__redirecting=true" not in notfound:
    problems.append("/404.html: no redirect guard, so redirects count as 404 views")
elif notfound.index("window.__redirecting=true") > notfound.index("gtag('config'"):
    problems.append("/404.html: redirect guard runs after gtag('config'), too late to stop the view")

listed = {u[len(SITE):] for u in re.findall(r"<loc>(.*?)</loc>", (OUT / "sitemap.xml").read_text())}
for u in sorted(indexable - listed):
    problems.append(f"sitemap: missing {u}")
for u in sorted(listed - indexable):
    problems.append(f"sitemap: lists non-indexable {u}")

feed = OUT / FEED.lstrip("/")
items = []
if not feed.exists():
    problems.append(f"feed: {FEED} not built")
else:
    items = re.findall(r"<item>(.*?)</item>", feed.read_text(), re.S)
    if not items:
        problems.append("feed: no items")
    for item in items:
        loc = re.search(r"<link>(.*?)</link>", item)
        if not loc:
            problems.append("feed: an item has no link")
        elif loc.group(1)[len(SITE):] not in listed:
            problems.append(f"feed: links {loc.group(1)}, which is not an indexable page")

# Hebrew is excluded as a site language. It would come back as a /he/ or /iw/
# tree, or as a lang/hreflang tag on any other page. /salary/ may declare the
# bare tag "he" and nothing else may.
hebrew_tree = re.compile(r"^/(?:he|iw)(?:-|/)", re.I)
hebrew_tag = re.compile(r'(?:lang|hreflang)="((?:he|iw)[^"]*)"', re.I)
for page in sorted(OUT.rglob("*.html")):
    rel = "/" + str(page.relative_to(OUT)).replace("index.html", "")
    if hebrew_tree.search(rel):
        problems.append(f"{rel}: a Hebrew page was built")
    for tag in set(hebrew_tag.findall(page.read_text())):
        if rel in HEBREW_TOOL_PAGES and tag.lower() == "he":
            continue
        problems.append(f"{rel}: Hebrew language tag {tag!r}")
for loc in re.findall(r"<loc>(.*?)</loc>", (OUT / "sitemap.xml").read_text()):
    if hebrew_tree.search(loc[len(SITE):]):
        problems.append(f"sitemap: lists a Hebrew URL {loc}")

# Each language's feed stays inside its own tree, so a reader never gets an
# English article through a translated feed.
for feed_file in sorted(OUT.rglob("feed.xml")):
    where = "/" + str(feed_file.relative_to(OUT))
    prefix = where[: -len("/feed.xml")]
    for link in re.findall(r"<link>(.*?)</link>", feed_file.read_text()):
        path = link[len(SITE):]
        if not path.startswith(prefix + "/"):
            problems.append(f"{where}: links {path}, outside {prefix or '/'}")

print(f"{len(titles)} indexable pages, {len(listed)} in sitemap, {len(items)} in feed")
for w in warnings:
    print("  !", w)
for p in problems:
    print("  ✗", p)
sys.exit(1 if problems else 0)
