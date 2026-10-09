# michaelorlov.com

The site for **Orlov Games**: a home page listing every app in the Play
Console, a page per app, and a blog that covers all of them. A small
standard-library Python build turns `content/` into `_site/`, and GitHub Actions
publishes that to GitHub Pages at <https://michaelorlov.com>.

```
content/
  apps.json            every app: slug, name, package, status (live|testing),
                       category, tagline (= Play short description), privacy_url
  play/<Slug>.json     full Play description + screenshot list (from tools/fetch_play.py)
  apps/VideoPoker.html hand-written page body; any app with a file here gets it
                       instead of the generated page
  posts/*.html         blog posts: JSON front matter + article body
  legal/*.html         privacy policy / terms pages
templates/base.html    <head>, Google Analytics tag, header, footer — on every page
static/                copied as-is: style.css, img/, CNAME, robots.txt
build.py               → _site/ (pages, sitemap.xml, 404.html)
tools/check.py         links, GA tag, JSON-LD, titles, sitemap — CI fails if any break
tools/fetch_play.py    refresh listing text, icons and screenshots from Google Play
```

## URLs

| URL | What |
|---|---|
| `/` | Studio home: every app, latest posts |
| `/<Slug>/` | One page per app, e.g. `/VideoPoker/`, `/OmahaPoker/`, `/ValleyRail/` |
| `/blog/` | All posts, with a filter for each app |
| `/blog/<Slug>/` | Posts for one app (only built for apps that have posts) |
| `/blog/<post>.html` | A post |
| `/privacy-policy.html` | Website policy (Google Analytics) + links to each app's policy |
| `/VideoPoker/privacy-policy.html`, `/VideoPoker/terms.html` | Video Poker's own legal pages |

URLs are case-sensitive on GitHub Pages. `404.html` sends a wrong-case app URL
(`/videopoker`, `/OMAHAPOKER/`) to the right page. `/terms.html` redirects to
the Video Poker terms, which is what it used to show.

## Everyday jobs

**Build and preview**

```sh
python3 build.py --serve      # http://localhost:8000
python3 tools/check.py
```

**Add a blog post:** see `blog-topics.md`. It's one new file in
`content/posts/` with an `app` field. Everything else updates on its own.

**Add an app, or move one from testing to live:** edit `content/apps.json`.
For a live app, run `python3 tools/fetch_play.py <Slug>` to pull its listing,
icon and screenshots. For an app still in testing there is no public listing,
so write `content/play/<Slug>.json` by hand from Play Console → Store listing,
and put `icon.jpg` and `shot1.jpg`… in `static/img/apps/<Slug>/`.

## Analytics

Every page loads GA4 `G-S6E36TV2PC`: property *android-34c9a* in the
micorlov@gmail.com Analytics account, web stream "michaelorlov.com". Each page
also sends a `content_group`: the app slug on app pages and posts, or `Home`,
`Blog`, `Legal`, `404`. That splits reports by app under Engagement → Pages and
screens → Content group. Clicks on a Google Play button send a
`play_store_click` event with an `app` parameter.

The tag lives in `templates/base.html`, and `tools/check.py` fails the deploy if
any page has it missing, duplicated, or carries another GA ID.

## How it is wired up

Already done, recorded here so it can be rebuilt:

- **Settings → Pages → Source:** GitHub Actions.
- **Settings → Pages → Custom domain:** `michaelorlov.com`.
- **DNS at GoDaddy:** four A records on `@` pointing at GitHub Pages
  (`185.199.108.153`, `.109.153`, `.110.153`, `.111.153`), and `www` as a
  CNAME to `micorlov.github.io.`. The Microsoft 365 mail records (MX,
  autodiscover, SPF) and the `chat` subdomain are untouched.

`static/CNAME` keeps the domain set on redeploys. Every push to `main` that
touches the site sources rebuilds and redeploys. You can also run the workflow
by hand from the Actions tab.
