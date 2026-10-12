"""Sanity checks over _site/ after `python3 build.py`. Exits non-zero on any problem.

- every internal href/src resolves to a file
- every real page loads the GA tag exactly once, and no redirect hop loads it at all
- /404.html decides its redirect before Analytics runs, so a redirect is never a 404 view
- every JSON-LD block parses
- indexable pages have a unique <title>, a description and a canonical
- titles and descriptions fit a search result, and each page has one <h1>
- every <img> carries alt text and width/height, so nothing shifts as it loads
- the sitemap lists exactly the indexable pages, and the feed lists the newest posts
"""
import html, json, pathlib, re, sys, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
sys.path.insert(0, str(ROOT))
from build import DESC_MAX, FEED, GA_ID, SITE, TITLE_MAX, exists_exact  # noqa: E402

DESC_MIN = 70  # shorter than this and a search result has room it is not using

problems, titles, indexable = [], {}, set()


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
    title = re.search(r"<title>(.*?)</title>", h).group(1)
    if title in titles:
        problems.append(f"{rel}: title duplicates {titles[title]}")
    titles[title] = rel
    if len(html.unescape(title)) > TITLE_MAX:
        problems.append(f"{rel}: title is {len(html.unescape(title))} chars, over {TITLE_MAX} "
                        f"(set seo_title in the front matter)")
    if h.count("<h1") != 1:
        problems.append(f"{rel}: {h.count('<h1')} <h1> headings, expected 1")
    desc = re.search(r'<meta name="description" content="([^"]*)"', h)
    length = len(html.unescape(desc.group(1))) if desc else 0
    if not DESC_MIN <= length <= DESC_MAX:
        problems.append(f"{rel}: description is {length} chars, want {DESC_MIN}-{DESC_MAX} "
                        f"(set seo_description in the front matter)")
    if '<meta property="og:site_name"' not in h:
        problems.append(f"{rel}: og:site_name missing")
    if f'<link rel="canonical" href="{SITE}{rel}">' not in h:
        problems.append(f"{rel}: canonical missing or wrong")

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

print(f"{len(titles)} indexable pages, {len(listed)} in sitemap, {len(items)} in feed")
for p in problems:
    print("  ✗", p)
sys.exit(1 if problems else 0)
