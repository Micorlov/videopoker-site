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
  img/              icon, OG card, screenshots
.github/workflows/deploy.yml
```

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
