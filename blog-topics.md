# Blog topic backlog

One post per run, taken from the top of **Queued**. When a post ships, move its
line to **Published** with the date and the slug.

## How to publish a post

The blog covers every Orlov Games app. A post is one file and nothing else:

1. Create `content/posts/<slug>.html`. The slug becomes the URL
   (`https://michaelorlov.com/blog/<slug>.html`), so never rename a published one.
2. Start it with the JSON front matter block used by every existing post:
   `title`, `date`, `modified`, `app`, `description`, `summary`, `standfirst`.
   `app` is a slug from `content/apps.json` (`VideoPoker`, `OmahaPoker`,
   `Blackjack21`, …). It files the post under `/blog/<App>/` and lists it on
   that app's page.
3. Below the front matter, write the article body. Copy an existing post for
   the markup, including the `post-foot` paragraph with the Play button.
4. Run `python3 build.py && python3 tools/check.py`, then commit and push.
   The blog index, the per-app pages, the home page, the sitemap and the
   JSON-LD all update on their own. Don't edit any of them by hand.

When Queued is empty, **stop and do not invent topics**. Publishing filler is
worse for the site than publishing nothing — tell Michael the backlog is empty
and let him refill it.

## Rules for every post

- 700–1,100 words. Long enough to answer the question properly, short enough
  that every paragraph earns its place.
- It must teach something checkable: a number, a rule, an ordering, a
  distinction. If the post could be written without knowing anything about
  the game it covers, it is not worth publishing.
- No invented statistics. Established game maths (paytable returns, hand
  frequencies, odds, strategy orderings) is fine from knowledge. Anything about
  the app itself must be true of the real app — check the Play listing or the
  game repo rather than guessing at features.
- Never imply the chips have cash value or that the game is gambling.
- British-ish plain English, same voice as the existing three posts: direct,
  no hype, no "in today's fast-paced world", no rhetorical questions as
  openers.

## Queued

Topics are grouped by app. Take the first one under any app; each post's `app`
field is the heading it came from.

### VideoPoker

1. Progressive jackpots and the point where a machine turns positive
2. What the hold percentage on a machine does and does not tell you
3. Why practising offline beats practising for money
4. Three of a kind: the hand that behaves differently in every variant
5. The order to learn video poker variants in

### Other apps

Empty. When Michael adds topics for other apps, give each app its own
`### <AppSlug>` heading above this one.

## Published

- 2026-10-09 — How shuffling works in a digital card game — `how-shuffling-works`
- 2026-10-08 — Common video poker myths, and what the maths says instead — `common-video-poker-myths`
- 2026-10-07 — Reading a Deuces Wild paytable — `reading-a-deuces-wild-paytable`
- 2026-10-06 — Full-pay machines and why they became hard to find — `full-pay-machines`
- 2026-10-05 — Bankroll and session length: how far a fixed stack actually goes — `bankroll-and-session-length`
- 2026-10-04 — How video poker differs from poker at a table — `video-poker-vs-table-poker`
- 2026-10-03 — Machines that pay on kings instead of jacks — `kings-instead-of-jacks`
- 2026-10-02 — Why a kicker never helps — `why-a-kicker-never-helps`
- 2026-10-01 — Why an inside straight draw is worth exactly half an outside one — `inside-vs-outside-straight-draws`
- 2026-09-30 — Five Play: what multi-hand does to your bankroll, and what it doesn't — `five-play-multi-hand-bankroll`
- 2026-09-29 — Why the royal flush is worth two percentage points of the return — `royal-flush-share-of-the-return`
- 2026-09-28 — What variance actually means at a video poker machine — `video-poker-variance`
- 2026-09-27 — Bonus Poker and Double Bonus: what the bigger quads cost you — `bonus-poker-and-double-bonus`
- 2026-09-26 — How to read a video poker paytable — `reading-a-video-poker-paytable`
- 2026-09-26 — Jacks or Better strategy, ranked — `jacks-or-better-strategy`
- 2026-09-26 — Why Deuces Wild breaks your Jacks or Better instincts — `deuces-wild-strategy`
