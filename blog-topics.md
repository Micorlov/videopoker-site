# Blog topic backlog

A scheduled agent publishes **one new post for every game, every day**. This
file is its instructions and its memory: the topic queue for each game and the
log of everything already published. Edit, reorder or delete queued topics
freely; the agent always takes the first one under each game.

## Games covered

The 12 game slugs from `content/apps.json`. StorySplit and AiPicDetect are
tools, not games, and get no daily post.

`VideoPoker`, `OmahaPoker`, `Blackjack21`, `BrasslightSlots`, `PokerVsDealer`,
`FivesAndThrees`, `BlackjackCoach`, `HoldemCoach`, `EightBallsPool`,
`BigBenBlocks`, `PinkSlipKings`, `ValleyRail`

When an app is added to `content/apps.json`, add it to this list and give it a
`### <Slug>` heading under Queued if it should get daily posts.

## The daily run

1. `git pull` on `main`. Note today's date (Asia/Jerusalem); every post written
   today carries it as `date` and `modified`.
2. **Refill any empty queue.** For each game whose `### <Slug>` list under
   Queued is empty, add 5 new topics to it (see *Choosing topics*). Never skip a
   game because its queue was empty.
3. **Write one post per game.** Take the first topic under each game. Write the
   12 posts in parallel with one subagent per game; each subagent writes only
   its own `content/posts/<slug>.html` and must not touch any other file. Give
   each one the topic, the app's entry from `content/apps.json`, the path to
   `content/play/<Slug>.json`, two existing posts to copy markup from, and the
   rules in this file.
4. **Review every post** against *Rules for every post* before keeping it. A
   post that fails and can't be fixed in one pass is deleted, and its topic
   stays at the top of the queue for tomorrow. Shipping 11 good posts beats
   shipping 12 with one bad one.
5. **Update this file.** Remove each published topic from Queued and add a line
   to the top of Published: `- <date> — <title> — <App> — \`<slug>\``.
6. Run `python3 build.py && python3 tools/check.py`. Fix anything it reports.
7. Commit everything in one commit (`feat: daily blog posts for <date>`), push
   to `main`, and wait for the *Deploy site to GitHub Pages* action to finish.
   Then fetch two or three of the new URLs on `https://michaelorlov.com/blog/`
   and confirm they return 200.
8. Report: each game with the title and URL of its new post, any game that got
   no post and why, and any queue that was refilled.

## How a post is built

The blog covers every Orlov Games app. A post is one file and nothing else:

1. Create `content/posts/<slug>.html`. The slug becomes the URL
   (`https://michaelorlov.com/blog/<slug>.html`), so never rename a published
   one, and never reuse an existing file name.
2. Start it with the JSON front matter block used by every existing post:
   `title`, `date`, `modified`, `app`, `description`, `summary`, `standfirst`.
   `app` is the game's slug. It files the post under `/blog/<App>/` and lists
   it on that app's page. Add `seo_title` or `seo_description` only when the
   title or description breaks the length rule below.
3. Below the front matter, write the article body. Copy an existing post for
   the markup, and end with a `post-foot` block that links to the app page
   (`/<Slug>/`).
   - **Live app:** add the Play button, copied from an existing post, with
     `href="https://play.google.com/store/apps/details?id=<package>"`.
   - **App in testing** (`"status": "testing"`: PinkSlipKings, ValleyRail):
     no Play button. Its listing is not public, so link only to `/<Slug>/`
     and say it is in closed testing.
4. The blog index, the per-app pages, the home page, the sitemap and the
   JSON-LD all update on their own when the site builds. Don't edit any of
   them by hand.

## Choosing topics

When a game's queue runs out, the agent writes 5 new topics for it. A good
topic:

- Answers a question a player of that game would really search for: a rule,
  a scoring detail, a strategy decision, the maths behind a choice, a common
  mistake, how the real-world game or sport works.
- Can be backed by established rules, maths or physics, or by something the
  app's Play listing (`content/play/<Slug>.json`) states. Nothing that depends
  on guessing what the app does.
- Is not a near-duplicate of any title in Published, **across every app**.
  Blackjack21 and BlackjackCoach, and HoldemCoach, OmahaPoker, PokerVsDealer
  and VideoPoker, overlap heavily. Give each its own angle rather than writing
  the same post twice.
- Is one line, phrased as the post's working title.

## Rules for every post

- 700–1,100 words. Long enough to answer the question properly, short enough
  that every paragraph earns its place.
- It must teach something checkable: a number, a rule, an ordering, a
  distinction. If the post could be written without knowing anything about
  the game it covers, it is not worth publishing.
- No invented statistics. Established game maths (paytable returns, hand
  frequencies, odds, strategy orderings, scoring rules, physics) is fine from
  knowledge. Anything about the app itself (features, modes, levels, chip
  amounts, rules variants) must be stated in `content/play/<Slug>.json` or on
  the app page. If it isn't there, don't claim it.
- Never imply that chips or coins have cash value, or that any game is
  gambling. Casino-style apps are free practice games with no real money.
- British-ish plain English, in the same voice as the existing posts: direct,
  no hype, no "in today's fast-paced world", no rhetorical questions as
  openers.
- Link to other posts for the same app where they genuinely help.
- **Lengths that search results allow.** Keep `title` at 60 characters or
  fewer and `description` between 70 and 160. If the natural title or
  description is longer, keep it and add a shorter `seo_title` or
  `seo_description` beside it — that one is what the `<title>` and the meta
  description use, while the long version still appears on listing pages and
  in the JSON-LD. `python3 tools/check.py` fails the build otherwise.
- One `<h1>` per post (the build writes it from `title`, so don't add another),
  and every `<img>` in the body needs `alt`, `width` and `height`.

## Queued

Take the first topic under each game. Each post's `app` field is the heading
it came from. An empty list means the next run writes 5 new topics for it.

### VideoPoker

1. Progressive jackpots and the point where a machine turns positive
2. What the hold percentage on a machine does and does not tell you
3. Why practising offline beats practising for money
4. Three of a kind: the hand that behaves differently in every variant
5. The order to learn video poker variants in

### OmahaPoker

### Blackjack21

### BrasslightSlots

### PokerVsDealer

### FivesAndThrees

### BlackjackCoach

### HoldemCoach

### EightBallsPool

### BigBenBlocks

### PinkSlipKings

### ValleyRail

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
