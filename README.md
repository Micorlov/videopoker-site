# videopoker-site

The marketing site for **Video Poker: Jacks or Better** (`com.micorlov.videopoker`),
published to GitHub Pages by GitHub Actions and served at
<https://michaelorlov.com>.

```
site/               everything that gets published
  index.html        the page
  privacy-policy.html
  terms.html
  style.css
  CNAME             the custom domain
  robots.txt        points crawlers at the sitemap
  sitemap.xml       all seven URLs
  img/              icon, OG card, screenshots
  blog/
    index.html      post listing
    *.html          one file per post
.github/workflows/deploy.yml
```

## SEO

Each page carries a canonical URL, a unique title and description, and
Open Graph and Twitter card tags. The home page has `MobileApplication` and
`FAQPage` JSON-LD; each post has `BlogPosting` plus a `BreadcrumbList`; the
blog index has `Blog`. The legal pages are `noindex, follow`.

Adding a post means: copy an existing post file, edit the content and its
JSON-LD block, then add it to `blog/index.html`, the "How these games work"
section on the home page, and `sitemap.xml`.

Every push to `main` that touches `site/**` redeploys. You can also run the
workflow by hand from the Actions tab.

## How it is wired up

Already done, recorded here so it can be rebuilt:

- **Settings → Pages → Source:** GitHub Actions.
- **Settings → Pages → Custom domain:** `michaelorlov.com`.
- **DNS at GoDaddy:** four A records on `@` pointing at GitHub Pages
  (`185.199.108.153`, `.109.153`, `.110.153`, `.111.153`), and `www` as a
  CNAME to `micorlov.github.io.`. The Microsoft 365 mail records (MX,
  autodiscover, SPF) and the `chat` subdomain are untouched.

`site/CNAME` keeps the domain set on redeploys. Note that with an
Actions-based deploy the CNAME file alone does not configure Pages — the
custom domain also has to be set in Settings, which it is.

## Editing

Plain HTML and one stylesheet, no build step. Open `site/index.html` in a
browser, or serve the folder:

```sh
python3 -m http.server -d site 8000
```

The screenshots in `site/img/` are cropped from `play-store-assets/phone/` in the
game repository. To refresh them after a UI change, re-export the store
screenshots and crop to the phone frame.
