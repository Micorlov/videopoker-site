"""One-off: pull public Play Store listing data for the live apps.

Writes content/play/<Slug>.json (name, description, genre, rating, installs)
and saves icon.jpg + up to four screenshots under static/img/apps/<Slug>/.
apps.json stays hand-edited; build.py merges the two.

    python3 tools/fetch_play.py            # every live app in apps.json
    python3 tools/fetch_play.py OmahaPoker # one app
"""
import html, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/128 Safari/537.36"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def text(fragment):
    fragment = re.sub(r"<br\s*/?>", "\n", fragment)
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def fetch(app):
    slug, pkg = app["slug"], app["package"]
    page = get(f"https://play.google.com/store/apps/details?id={pkg}&hl=en&gl=US").decode()
    name = text(re.search(r'itemprop="name"[^>]*>(.*?)</span>', page, re.S).group(1))
    desc = text(re.search(r'data-g-id="description"[^>]*>(.*?)</div>', page, re.S).group(1))
    icon = re.search(r'<img src="(https://play-lh[^"=]+)=[^"]*"[^>]*alt="Icon image"', page).group(1)
    shots = re.findall(r'<img src="(https://play-lh[^"=]+)=[^"]*"[^>]*alt="Screenshot image"', page)
    out = ROOT / "static/img/apps" / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "icon.jpg").write_bytes(get(icon + "=s256-rj-l85"))
    saved = []
    for i, base in enumerate(shots[:4], 1):
        (out / f"shot{i}.jpg").write_bytes(get(base + "=w480-rj-l80"))
        saved.append(f"shot{i}.jpg")
    data = {"name": name, "description": desc, "screenshots": saved}
    dest = ROOT / "content/play" / f"{slug}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"{slug}: {name} — {len(desc)} chars, {len(saved)} screenshots")


def main():
    apps = json.loads((ROOT / "content/apps.json").read_text())
    wanted = set(sys.argv[1:])
    for app in apps:
        if app["status"] == "live" and (not wanted or app["slug"] in wanted):
            fetch(app)


if __name__ == "__main__":
    main()
