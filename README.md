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
                       (seo_title / seo_description override an over-long one)
  legal/*.html         privacy policy / terms pages
templates/base.html    <head>, Google Analytics tag, header, footer — on every page
static/                copied as-is: style.css, fonts.css, fonts/, img/, CNAME,
                       robots.txt
build.py               → _site/ (pages, sitemap.xml, feed.xml, 404.html)
i18n/                  turns the finished English pages into every other language
content/locales.json   the 70 languages, plus the Hebrew exclusion
content/i18n/<code>.json  the translations the build reads (committed)
tools/translate.py     fills content/i18n/ through the Claude API (never run in CI)
tools/check.py         links, GA tag, JSON-LD, titles, descriptions, images,
                       sitemap, feed, languages — CI fails if any break
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
A scheduled agent publishes one post for every game each morning. Its
instructions and the topic queue for each game are in `blog-topics.md`, so
steer it by editing that file.

**Add an app, or move one from testing to live:** edit `content/apps.json`.
For a live app, run `python3 tools/fetch_play.py <Slug>` to pull its listing,
icon and screenshots. For an app still in testing there is no public listing,
so write `content/play/<Slug>.json` by hand from Play Console → Store listing,
and put `icon.jpg` and `shot1.jpg`… in `static/img/apps/<Slug>/`.

## Languages

The site is published in 70 languages besides English, **and never in Hebrew**.
English stays at the URLs it always had; every other language is a prefix:
`/es/`, `/pt-BR/`, `/zh-Hans/`, `/ar/` and so on, with `/es/VideoPoker/`,
`/es/blog/<post>.html` beneath. Play's ~80 listing locales are covered by
`hreflang` rather than by duplicate pages: `es-MX`, `es-419` and `es-US` all
point at `/es/`, the six English variants at the English root.

A language appears on the site once `content/i18n/<code>.json` covers every
string on a page, and not before. The build **never calls a translation API**,
so CI stays offline and deterministic; a language without translations simply
isn't built, and a page with a gap in one language isn't published in it.

```sh
pip install anthropic && export ANTHROPIC_API_KEY=...
python3 tools/translate.py --estimate            # price the job first
python3 tools/translate.py --locales es,fr,ja    # a few languages
python3 tools/translate.py --locales all --budget 25   # stops at $25
python3 tools/translate.py --audit               # what each language has
python3 build.py && python3 tools/check.py       # publish what's ready
```

It writes after every batch, so an interrupted run resumes without paying twice,
and a day's new posts cost only their own strings. Commit `content/i18n/`.
`--prune` drops text no page uses any more.

**Hebrew** is refused in three places: `i18n/locales.py` rejects it from the
registry and from `--locales`, `tools/check.py` fails the build if a Hebrew
tree, `lang`, `hreflang` or sitemap URL appears in the output, and the browser
suite requests `/he/` and `/iw/` and expects a 404.

Right-to-left (Arabic, Persian, Urdu) works through `dir="rtl"` and logical CSS
properties; don't add `left`/`right` rules to `style.css`.

**New posts** need nothing extra. The daily agent publishes English; run
`tools/translate.py --locales all` afterwards to fill the new strings in.
Until you do, the new post exists in English only.

## Search

Every indexable page carries a canonical URL, Open Graph and Twitter cards,
and JSON-LD: `Organization` + `WebSite` + `ItemList` on the home page,
`MobileApplication` on an app page, `BlogPosting` on a post, and a
`BreadcrumbList` everywhere below the home page. The studio and the author
use fixed `@id`s (`/#organization`, `/#michael`) so they stay one entity
across pages.

A search result cuts a title near 60 characters and a description near 160, so
`build.py` appends `— Orlov Games` to a title only while it still fits, and
`tools/check.py` fails the build on a title over 60 or a description outside
70–160. When a post's own `title` or `description` is longer than that, add
`seo_title` or `seo_description` to its front matter; the full text stays in
use on listing pages and in the JSON-LD.

`/feed.xml` is an RSS 2.0 feed of the 20 newest posts, linked from every page's
`<head>`. `/sitemap.xml` lists every indexable page, and `static/robots.txt`
points at it.

### Fonts

Antonio and Archivo are self-hosted in `static/fonts/`, so the first paint waits
on no cross-origin DNS, TLS and round trip to `fonts.googleapis.com` and
`fonts.gstatic.com`. `static/fonts.css` is the Google Fonts stylesheet with the
URLs pointed at local copies and nothing else changed, and the two latin files
the header and body text need are preloaded in `templates/base.html`.

To refresh them, fetch the stylesheet with a current browser's user agent (an old
one is served ttf instead of woff2), download every `.woff2` it names, and replace
`static/fonts.css` and `static/fonts/*.woff2` together:

```sh
curl -A "$(python3 -c 'print("Mozilla/5.0 Chrome/126.0.0.0 Safari/537.36")')" \
  'https://fonts.googleapis.com/css2?family=Antonio:wght@400;600;700&family=Archivo:wght@400;500;600;700&display=swap'
```

Both faces are SIL Open Font License 1.1; see `static/fonts/NOTICE`.

## Analytics

Every page loads GA4 `G-NS1LGN6P3Y`: Analytics account *WEB* →
property *michaelorlov.com* (Israel time zone) → web stream "michaelorlov.com", under
micorlov@gmail.com. Until October 2026 the site used `G-S6E36TV2PC` in the
Firebase property *android-34c9a*; older history stays there. Each page
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
