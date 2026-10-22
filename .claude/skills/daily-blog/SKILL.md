---
name: daily-blog
description: Publish or edit posts on michaelorlov.com, including the daily one-post-per-game run and the chart or diagram each post carries. Use for any work on content/posts/, blog-topics.md, or figures in a post.
---

# Daily blog posts for michaelorlov.com

`blog-topics.md` at the repo root is the single source of truth for the daily
run: the steps, the post rules, the topic queues and the Published log. Read it
first and follow its "The daily run" section exactly. This skill only adds what
that file leaves out, and never overrides it. If `blog-topics.md` has no
"## The daily run" section, stop and report that.

## Subagents

The one-subagent-per-game writers run on Sonnet 5.5: pass `model: "sonnet"` to the
Agent tool for each. Tell each writer to include 1–2 mid-text links to its
app page (`/<Slug>/`) in the body, in the paragraph before a section heading,
as well as the closing `post-foot`. Every claim beside such a link must be in
`content/play/<Slug>.json`; testing apps say they are in closed testing.

## Every post carries one figure

Each post gets one `<figure class="chart">` placed before the paragraph or
heading it illustrates. It shows numbers the post already states and has been
checked. Never introduce a number in a figure that the body text does not
support. Decide the form by the data's job:

| Data | Form | Markup to copy |
|---|---|---|
| A ranking or a few comparable values | HTML bars (`.bars`) | `content/posts/blackjack-3-to-2-payout.html` |
| Values spanning orders of magnitude | HTML bars, log scale | `content/posts/five-card-poker-hand-frequencies.html` |
| A relationship or curve | inline SVG line chart | `content/posts/holdem-pot-odds.html` |
| Counts per category | inline SVG columns | `content/posts/fives-and-threes-scoring-explained.html` |
| A layout, rack, grid or track | inline SVG diagram | `eight-ball-rules-explained.html`, `nine-by-nine-grid-three-lines.html`, `reading-a-drag-racing-time-slip.html` |

Rules:

- **No image files.** Draw it inline (SVG with `viewBox="0 0 400 H"`, or the
  `.bars` HTML). It stays sharp, adds no requests and passes the build's
  `<img>` checks trivially. If an `<img>` is ever used it needs `alt`, `width`
  and `height`.
- SVG gets `role="img"` and an `aria-label` that states the finding, not just
  the chart type. The `<figcaption>` says what is plotted and the one thing to
  notice.
- **Colour:** `--chart-accent` for the single thing the post is about,
  `--chart-base` for everything else. Both are defined in `static/style.css`
  (with the `.chart`, `.bars` and SVG helper classes) and were validated
  against the dark site background. Do not add colours. If a new colour is
  unavoidable, check it with the `dataviz` skill's `validate_palette.js` in
  `--mode dark --surface "#07170F"`; gold brighter than `#BC8A22` fails the
  lightness band.
- **Label values directly** (a number on the bar, the line, or the key points).
  Colour is never the only cue. No dual axes, no rainbow, no legend box for a
  single series.
- Give each point a `<title>` so hover shows the value, and keep dots at least
  8px with a 2px surface ring (`.dot`).
- Keep one figure per post; do not pad the word count. Figures live in the
  body, so the 700–1,100 word range is measured on text only.

## Verify before committing

1. `python3 build.py && python3 tools/check.py` must pass.
2. Look at the figure. `npm ci --ignore-scripts` provides Playwright;
   serve `_site/` (`python3 -m http.server -d _site 8765`), screenshot
   `figure.chart` at 1200px and 360px wide, and read the images. The colour
   validator does not catch overlapping labels, clipped text or horizontal
   overflow; look for all three. Fix label collisions by moving text, not by
   shrinking the font below 12px.

## Facts about the site that bite

- `content/play/<Slug>.json` and `content/apps.json` are the only source for
  claims about an app. Do not state a feature, mode, rule variant or payout
  that is not in them. The Video Poker listing and `content/apps/VideoPoker.html`
  disagree with the app source on the royal flush payout, so state nothing about
  the royal's pay in a Video Poker post unless the listing supports it.
- Apps with `"status": "testing"` (ValleyRail) get no Play
  button and no Play Store link; say the app is in closed testing.
- Never imply chips, coins or points have cash value, or that any game is
  gambling.
- `title` is at most 60 characters and `description` 70–160. Longer natural
  versions get `seo_title` / `seo_description`; the build rejects the rest.
- This sandbox cannot reach michaelorlov.com. Confirm a deploy through the
  "Deploy site to GitHub Pages" workflow run on GitHub instead, and say in the
  report that the live URLs could not be fetched.
- Never rename, delete or rewrite a published post, except to add a figure.
