# Product

<!-- impeccable:product-schema 1 -->

Assumptions below are inferred from the repository and the redesign brief. This session has no structured question tool, so the init interview could not be asked. Facts taken from the repo are marked as such. Nothing here is a visual recipe.

## Platform

web

## Users

People looking for Michael Orlov's Android games, usually from Google Play, a search result, or a link in an app. They want to see what a game is, open its store listing, and read how it works. A second audience is the same person later, reading the blog for paytables, odds, and strategy. (Inferred from the site's information architecture and Play links.)

## Product Purpose

michaelorlov.com is the public site for Orlov Games. It lists every app, gives each one a page, and publishes a blog about how the games work. Success is a visitor finding the right game, reaching Google Play, and being able to read the privacy policy and the notes. (From README and the page set.)

## Positioning

One person, Michael Orlov, ships small Android games. The casino games play for chips only: no real money, ever. Most of them run offline. (From the home page lede and app listings.)

## Operating Context

The site is static HTML built by `build.py` from `content/` and published to GitHub Pages from `main`. English lives at the root. Other languages are prefixes. Hebrew is never published. Visitors arrive on a phone or a desktop browser and leave for Google Play or stay to read. (From README and the deploy workflow.)

## Capabilities and Constraints

- Keep every existing page, sentence, game link, store link, privacy page, and `static/CNAME` (`michaelorlov.com`).
- URLs stay case-sensitive. App pages are `/<Slug>/`.
- Google Analytics `G-NS1LGN6P3Y` stays on every page. Play links keep `data-app`.
- The build is Python, standard library, plus committed translations. Do not add a frontend framework or a font CDN.
- CSS uses logical properties so Arabic, Persian, and Urdu keep working.
- New reader-facing sentences drop a page out of any language that does not already translate them. Do not add prose.
- Do not publish Hebrew.

## Brand Commitments

The name is Orlov Games. The author credit is Michael Orlov. The mark in `static/img/mark.svg` is the icon. Voice on the page is plain and specific. No claim of real-money gambling. (Assets and copy from the repo. The felt-green page is the incumbent look, not a commitment to keep.)

## Evidence on Hand

Real app icons and screenshots in `static/img/` and `static/img/apps/`. Store copy in `content/play/`. Blog posts in `content/posts/`. Legal pages in `content/legal/`. No press quotes, reviews, or download counts are on the site. Do not invent any.

## Product Principles

- The games and the writing are the content. The page does not speak for them with slogans.
- Chips are not money, and the site does not imply that they are.
- Every game that exists in `content/apps.json` stays reachable.
- A page has to work with JavaScript off, on a phone, and with a keyboard.

## Accessibility & Inclusion

Skip link, visible focus, and `prefers-reduced-motion` already exist and stay. Right-to-left languages use `dir` and logical properties. Text contrast meets WCAG AA. (From the current templates and README.)
