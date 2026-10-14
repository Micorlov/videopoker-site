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
   **Catch up first.** If `origin/blog-pending` exists, an earlier run wrote
   posts it could not publish. Merge it into `main` before writing anything
   new, set those posts' `date` and `modified` (and their lines in Published)
   to today, and take them through steps 4–7 together with today's posts. Their
   topics are already out of Queued; don't take them again. Once they are live,
   delete the branch (`git push origin --delete blog-pending`) and list them
   in the report as caught up.
2. **Refill any empty queue.** For each game whose `### <Slug>` list under
   Queued is empty, add 5 new topics to it (see *Choosing topics*). Never skip a
   game because its queue was empty.
3. **Write one post per game.** Take the first topic under each game. Write the
   12 posts in parallel with one subagent per game, each run on Sonnet 5.5 (`model: "sonnet"`); each subagent writes only
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
6. **Translate what is new.** Every new post's text must be in every language
   the site publishes, or the build drops those pages. Run
   `python3 tools/translate.py --audit` to see what each language is missing.
   For each language that has a memory file, give one **Haiku 5.5** subagent
   (`model: "haiku"`) the missing English strings and the target language; it
   writes its output to a scratch file only, never into the repo. Merge those
   files into `content/i18n/<code>.json` yourself, check every key is present
   and non-empty, and run `python3 tools/translate.py --prune` only when stale
   text needs dropping. Languages with no memory file yet are not started by
   the daily run; see *Languages* below.
7. Run `python3 build.py && python3 tools/check.py`. Fix anything it reports.
8. Commit everything in one commit (`feat: daily blog posts for <date>`), push
   to `main`, and wait for the *Deploy site to GitHub Pages* action to finish.
   Then fetch two or three of the new URLs on `https://michaelorlov.com/blog/`
   and confirm they return 200.
9. Report: each game with the title and URL of its new post, any game that got
   no post and why, and any queue that was refilled.

**If the run can't publish** (offline, push rejected twice, or a build/check
failure it can't fix), don't throw the work away and don't push to `main`.
Commit it as in step 7 and push that commit to the `blog-pending` branch
instead (`git push -u origin HEAD:blog-pending`; only `main` deploys). Report
what blocked it. The next run publishes it first, under *Catch up first*.

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
4. **Add one chart or diagram** where a number has a shape: a curve, a
   ranking, a layout. Wrap it in `<figure class="chart">` with a
   `<figcaption>` that says what it shows. For a ranked list of values use the
   `.bars` HTML markup (see `blackjack-3-to-2-payout.html`); for a curve or a
   diagram use inline SVG with `viewBox="0 0 400 …"`, `role="img"` and an
   `aria-label` (see `holdem-pot-odds.html`, `eight-ball-rules-explained.html`).
   Colours come from `--chart-accent` (the one value the post is about) and
   `--chart-base`; label every value directly so colour is never the only cue.
   Every figure must be built from numbers already checked in the post.
5. The blog index, the per-app pages, the home page, the sitemap and the
   JSON-LD all update on their own when the site builds. Don't edit any of
   them by hand.

## Languages

The site is in English plus the languages whose memory file exists in
`content/i18n/` (today: es, fr, de, pt-BR, ja, ru). Each page is published in a
language only when that language covers all of its text, so a language that
has only part of the site translated gets none of the new posts.

Starting a new language is a separate job, not a daily-run step: the whole
site (about 2,600 strings) has to be translated first. Do it only when asked,
one language at a time, by Haiku 5.5 subagents writing scratch files that are
merged into the memory, and report the cost of the run before starting.

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

1. Why practising offline beats practising for money
2. Three of a kind: the hand that behaves differently in every variant
3. The order to learn video poker variants in

### OmahaPoker

1. How a low hand is made in Omaha Hi-Lo, and what 8 or better means
2. Wraps: how an Omaha straight draw can have 20 outs
3. Why the second-best flush is a trap in Omaha

### Blackjack21

1. Splitting pairs: why you always split aces and eights
2. What a six-deck shoe changes compared with a single deck
3. Twenty-one, pontoon and blackjack: how the games differ

### BrasslightSlots

1. Why a slot is never due: independent spins explained
2. Return to player and volatility: what each number measures
3. How a pick bonus works, and why the picks are already decided

### PokerVsDealer

1. The odds of improving a pair when you exchange cards
2. Breaking ties in five-card poker: high cards and split pots
3. Is the ace high or low? The ace in five-card poker

### FivesAndThrees

1. Choosing your opening tile in Fives and Threes
2. Doubles at an open end: why they count twice
3. Counting tiles: working out what your opponent cannot hold

### BlackjackCoach

1. Insurance: why it loses unless you are counting
2. Late surrender: the hands worth giving up on
3. Hard 12 against a 2 or 3: why basic strategy says hit

### HoldemCoach

1. Why position matters: one hand from an early and a late seat
2. Reading the board: finding the best five cards from seven
3. Pocket pair against two overcards: the coin flip that isn't

### EightBallsPool

1. Cue-ball spin explained: topspin, backspin and sidespin
2. Aiming with the ghost ball
3. The 90-degree rule: where the cue ball goes after a stun shot

### BigBenBlocks

1. Holes and islands: why a fragmented board ends a block puzzle
2. From Tetris to Sudoku: where the 9x9 block puzzle comes from
3. Shapes as well as colours: block puzzles for colour-blind players

### PinkSlipKings

1. Launch RPM: between wheelspin and bogging down
2. Horsepower and torque: how to read a dyno chart
3. When to shift: why the best shift point is past peak torque

### ValleyRail

1. From coal mine to power station: how freight chains work
2. Beam, arch, truss or suspension: how each bridge carries a load
3. Railway towns: how a station made a village grow

## Published

- 2026-10-14 — What a machine's hold percentage does and does not tell you — VideoPoker — `video-poker-hold-percentage`
- 2026-10-14 — How to work out a pot-sized bet in Pot-Limit Omaha — OmahaPoker — `pot-limit-omaha-pot-sized-bet`
- 2026-10-14 — How the dealer plays, and how often each up-card busts — Blackjack21 — `blackjack-dealer-bust-rates`
- 2026-10-14 — How a wild changes the count on a ways-to-win slot — BrasslightSlots — `wilds-on-a-ways-to-win-slot`
- 2026-10-14 — Why a flush beats a straight: the rankings follow the odds — PokerVsDealer — `why-a-flush-beats-a-straight`
- 2026-10-14 — Why 15 is the best total in Fives and Threes — FivesAndThrees — `fives-and-threes-why-15-scores-best`
- 2026-10-14 — Soft 18: how to play ace-seven against every dealer card — BlackjackCoach — `soft-18-ace-seven-strategy`
- 2026-10-14 — The rule of 2 and 4 in Hold'em, and where it goes wrong — HoldemCoach — `holdem-rule-of-2-and-4`
- 2026-10-14 — 9-ball rules: lowest ball first, and what counts as a foul — EightBallsPool — `nine-ball-rules-explained`
- 2026-10-14 — Setting up double clears on a 9x9 block grid — BigBenBlocks — `block-puzzle-double-clears`
- 2026-10-14 — Gear ratios and final drive: what gearing does to a quarter mile — PinkSlipKings — `gear-ratios-and-final-drive`
- 2026-10-14 — How railway signals keep trains apart — ValleyRail — `how-railway-signals-keep-trains-apart`
- 2026-10-13 — Progressive jackpots and the point where a machine turns positive — VideoPoker — `progressive-jackpots-and-positive-machines`
- 2026-10-13 — Exactly two from your hand: the Omaha rule that fools new players — OmahaPoker — `omaha-exactly-two-hole-cards`
- 2026-10-13 — Why blackjack paying 3:2 matters more than any other rule — Blackjack21 — `blackjack-3-to-2-payout`
- 2026-10-13 — What 243 ways to win means, and how it differs from paylines — BrasslightSlots — `what-243-ways-to-win-means`
- 2026-10-13 — How rare each five-card poker hand is — PokerVsDealer — `five-card-poker-hand-frequencies`
- 2026-10-13 — How Fives and Threes scoring works, with worked examples — FivesAndThrees — `fives-and-threes-scoring-explained`
- 2026-10-13 — Hi-Lo counting: running count and true count explained — BlackjackCoach — `hi-lo-running-and-true-count`
- 2026-10-13 — Pot odds in Texas Hold'em: working out whether a call pays — HoldemCoach — `holdem-pot-odds`
- 2026-10-13 — 8-ball rules: the open table, groups and the 8 ball — EightBallsPool — `eight-ball-rules-explained`
- 2026-10-13 — Why every cell on a 9x9 block grid belongs to three lines — BigBenBlocks — `nine-by-nine-grid-three-lines`
- 2026-10-13 — Reading a drag racing time slip: reaction time, ET and trap speed — PinkSlipKings — `reading-a-drag-racing-time-slip`
- 2026-10-13 — Why railways follow rivers: gradients and the ruling grade — ValleyRail — `why-railways-follow-rivers`
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
