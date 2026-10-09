"""Sanity checks over _site/ after `python3 build.py`. Exits non-zero on any problem.

- every internal href/src resolves to a file
- every page loads the GA tag exactly once
- every JSON-LD block parses
- indexable pages have a unique <title>, a description and a canonical
- the sitemap lists exactly the indexable pages
"""
import json, pathlib, re, sys, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
sys.path.insert(0, str(ROOT))
from build import GA_ID, SITE  # noqa: E402

problems, titles, indexable = [], {}, set()


def exists_exact(path):
    """Case-sensitive existence check (macOS is case-insensitive, GitHub Pages is not)."""
    cur = OUT
    for part in path.relative_to(OUT).parts:
        if part not in {c.name for c in cur.iterdir()} if cur.is_dir() else ():
            return False
        cur = cur / part
    return True


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
    if h.count(f"googletagmanager.com/gtag/js?id={GA_ID}") != 1:
        problems.append(f"{rel}: GA tag count != 1")
    for other in set(re.findall(r"G-[A-Z0-9]{8,12}", h)) - {GA_ID}:
        problems.append(f"{rel}: stray GA id {other}")
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            json.loads(block)
        except ValueError as e:
            problems.append(f"{rel}: bad JSON-LD ({e})")
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
    if not re.search(r'<meta name="description" content="[^"]{50,}"', h):
        problems.append(f"{rel}: missing or short description")
    if f'<link rel="canonical" href="{SITE}{rel}">' not in h:
        problems.append(f"{rel}: canonical missing or wrong")

listed = {u[len(SITE):] for u in re.findall(r"<loc>(.*?)</loc>", (OUT / "sitemap.xml").read_text())}
for u in sorted(indexable - listed):
    problems.append(f"sitemap: missing {u}")
for u in sorted(listed - indexable):
    problems.append(f"sitemap: lists non-indexable {u}")

print(f"{len(titles)} indexable pages, {len(listed)} in sitemap")
for p in problems:
    print("  ✗", p)
sys.exit(1 if problems else 0)
