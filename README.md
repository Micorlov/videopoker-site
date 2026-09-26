# videopoker-site

The marketing site for **Video Poker: Jacks or Better** (`com.micorlov.videopoker`),
published to GitHub Pages by GitHub Actions and served at
<https://videopoker.michaelorlov.com>.

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

## One-time setup

1. **Create the repository** on GitHub as `videopoker-site` (public — Pages needs
   a paid plan for private repos), then push this folder to `main`.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. **Settings → Pages → Custom domain:** `videopoker.michaelorlov.com`, then tick
   *Enforce HTTPS* once the certificate is issued (a few minutes).
4. **DNS at GoDaddy** — add one record to `michaelorlov.com`:

   | Type  | Name       | Value                  | TTL  |
   |-------|------------|------------------------|------|
   | CNAME | videopoker | `micorlov.github.io.`  | 600  |

   To use the apex `michaelorlov.com` instead, change `site/CNAME` to
   `michaelorlov.com` and add four A records to `185.199.108.153`,
   `185.199.109.153`, `185.199.110.153` and `185.199.111.153` instead of the
   CNAME above.

## Editing

Plain HTML and one stylesheet, no build step. Open `site/index.html` in a
browser, or serve the folder:

```sh
python3 -m http.server -d site 8000
```

The screenshots in `site/img/` are cropped from `play-store-assets/phone/` in the
game repository. To refresh them after a UI change, re-export the store
screenshots and crop to the phone frame.
