# Google Search Console for michaelorlov.com

The site is static, built by `build.py` and published to GitHub Pages by
`.github/workflows/deploy.yml` (custom domain in `static/CNAME`). This file is
in the repo root, so the build does not publish it.

## 1. Verify (recommended): Domain property, DNS TXT

Covers http, https, www and every subdomain in one property.

1. Open <https://search.google.com/search-console> and sign in with the Google account that should own the site.
2. Click the property picker (top left) > **Add property**.
3. Choose **Domain**, enter `michaelorlov.com`, click **Continue**.
4. Copy the TXT record shown (`google-site-verification=...`).
5. At your DNS provider for michaelorlov.com add a record: Type `TXT`, Host/Name `@` (blank), Value = the copied string, TTL default. Keep the existing GitHub Pages A/AAAA/CNAME records untouched.
6. Back in Search Console click **Verify**. DNS can take minutes to hours; if it fails, wait and click Verify again. Keep the TXT record permanently.

## 2. Alternative: URL-prefix property

Use only if you cannot edit DNS. Add property > **URL prefix** > `https://michaelorlov.com/`, then either:

**HTML file** (no code change)
1. Download the `googleXXXXXXXX.html` file Search Console offers.
2. Put it, unchanged, in `static/` (it is copied to the site root by the build).
3. Commit, push to `main`, wait for the deploy, open `https://michaelorlov.com/googleXXXXXXXX.html` to confirm it loads, then click **Verify**.

**HTML tag**
1. Copy only the `content="..."` value of the `<meta name="google-site-verification">` tag.
2. In `build.py` set `GSC_VERIFICATION = "<value>"` (empty by default, which emits no tag). Every page then carries the tag.
3. Commit, push, wait for the deploy, click **Verify**.

## 3. Submit the sitemap

1. Search Console > **Sitemaps** (left menu).
2. In "Add a new sitemap" enter `sitemap.xml` (full URL: `https://michaelorlov.com/sitemap.xml`) and click **Submit**.
3. Status should become **Success**. It lists every page in all 7 languages; `robots.txt` also points to it.

## 4. Request indexing

For each URL: paste it in the top **Inspect any URL** bar > wait for the result > **Request indexing**. (Quota is limited per day; do a few a day.)

- `https://michaelorlov.com/`
- `https://michaelorlov.com/VideoPoker/`
- `https://michaelorlov.com/Blackjack21/`
- `https://michaelorlov.com/OmahaPoker/`
- `https://michaelorlov.com/PinkSlipKings/` (Pink Slip Kings: Drag Racing)
- `https://michaelorlov.com/HoldemCoach/`
- `https://michaelorlov.com/BlackjackCoach/`
- the other live games: `BrasslightSlots`, `PokerVsDealer`, `FivesAndThrees`, `EightBallsPool`, `BigBenBlocks`, `StorySplit` (same pattern)

Translated pages are `https://michaelorlov.com/<de|es|fr|ja|pt-BR|ru>/...`; they are in the sitemap and linked by hreflang, so they need no manual requests.

## 5. Play Console

Linking Search Console to Play Console is **not** required. Do this instead, for each app:
Play Console > the app > **Grow users > Store presence > Store settings** (or **Store listing**) > **Store listing contact details** > **Website** = that app's page, e.g. `https://michaelorlov.com/VideoPoker/` (or `https://michaelorlov.com/`). Save and send for review if prompted.
