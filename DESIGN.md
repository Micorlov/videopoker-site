---
name: Orlov Games
description: The studio name is the monument. The live picture is a real game screen.
colors:
  forest: "#0f1f10"
  sheet: "#ffffff"
  ink: "#ffffff"
  sheet-ink: "#0f1f10"
  muted: "#b7c4b4"
  sheet-muted: "#3c4c3e"
  lime: "#c6f19d"
  lime-ink: "#0f1f10"
  field: "#000000"
  chart-base: "#7dcea0"
  chart-grid: "#1c3320"
typography:
  display:
    fontFamily: "General Sans, system-ui, sans-serif"
    fontSize: "clamp(4.75rem, 20.5vw, 20rem)"
    fontWeight: 700
    lineHeight: 0.8
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "General Sans, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 2vw + 1rem, 2.5rem)"
    fontWeight: 700
    lineHeight: 0.92
    letterSpacing: "-0.03em"
  title:
    fontFamily: "General Sans, system-ui, sans-serif"
    fontSize: "clamp(1.375rem, 4vw, 2.25rem)"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  body:
    fontFamily: "General Sans, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  label:
    fontFamily: "General Sans, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0"
rounded:
  none: "0"
spacing:
  gutter: "clamp(16px, 3vw, 32px)"
  step: "clamp(88px, 12vw, 168px)"
components:
  button-primary:
    backgroundColor: "{colors.lime}"
    textColor: "{colors.lime-ink}"
    rounded: "{rounded.none}"
    padding: "12px 18px"
  button-primary-hover:
    backgroundColor: "#d9f7bc"
    textColor: "{colors.lime-ink}"
    rounded: "{rounded.none}"
    padding: "12px 18px"
  button-primary-active:
    backgroundColor: "{colors.lime}"
    textColor: "{colors.lime-ink}"
    rounded: "{rounded.none}"
    padding: "12px 18px"
---

# Design System: Orlov Games

## Overview

**Creative North Star: "The name is the monument"**

Orlov Games is a one-person Android studio. The page treats the name as the largest thing on the site, set in two lines inside a mask, and treats a real game screenshot as the thing that changes while you read the list. Forest is the ground. White is a sheet you read on. Black is the closing field. Lime appears twice: the filled action, and the wordmark in the footer.

The world is flat, square, and quiet. Hierarchy comes from size and weight. Motion is the name rising into place, a short slide as sections arrive, a press on the action, and the screenshot swapping to the game under the pointer. Nothing else moves for attention.

This record was written in the same session as the redesign, without a live interview. The north star is the direction that was built: name-as-monument, with the no-cash chip as the constraint on the casino games, not as a second visual theme.

**Key Characteristics:**

- One typeface, General Sans, self-hosted.
- Forest, white sheet, black field. Lime only on the filled action and the footer name.
- Square corners. No resting shadow, gradient, glass, or hairline rule.
- The catalog's picture is a real screenshot and follows the game you are on.
- Logical properties, so Arabic, Persian, and Urdu mirror without a second stylesheet.

## Colors

Forest ground, a white reading sheet, and a black close. Lime is a signal, not a theme.

### Primary

- **Forest** (`#0f1f10`): page ground, hero, and the default ink on a white sheet.
- **Lime** (`#c6f19d`): filled action background, footer wordmark, and the highlighted chart bar. Text on lime is Forest (`#0f1f10`). Lime is not used as text on white.

### Neutral

- **Sheet** (`#ffffff`): catalog, testing, blog, app facts, and legal reading bands.
- **Sheet ink** (`#0f1f10`): text on a sheet. The sheet resets `--ink`.
- **Muted on forest** (`#b7c4b4`): secondary text on forest and on the black footer. It is a tint of the ground, not a neutral gray.
- **Muted on sheet** (`#3c4c3e`): secondary text on white. A gray that passes on forest fails here, so the sheet carries its own muted.
- **Field** (`#000000`): footer only, so the lime wordmark clears contrast.
- **Chart base** (`#7dcea0`) and **chart grid** (`#1c3320`): bars and axes inside posts. They stay inside the chart; they are not page chrome.

Focus rings use the current `--ink`, so they flip with the band. Selection is lime with forest text.

## Typography

General Sans, weights 400, 500, and 700, in `static/fonts/`. Preload 400 and 700. Scripts the face does not cover (Arabic, Hebrew, Devanagari, CJK) fall through to `system-ui`. Do not load a font CDN.

The monument ("Orlov Games") is `clamp(4.75rem, 20.5vw, 20rem)`, weight 700, line-height 0.8, tracking `-0.04em`, max-width `6.4ch`, so the two words break as two lines and stay one text node. That size is past a 6rem display cap on purpose: the direction is the name at monument scale. Tracking does not go tighter than `-0.04em`.

Section headings sit well below the monument. Post titles use a lower clamp so a long title stays on two lines. Body is `1.0625rem` / 1.5, measure `65ch`. Blog dates and chart numbers use tabular numerals.

## Layout

The header is a sticky bar, 64px, forest, with the mark and a text link to the blog. The hero is the name, then a corner block: the existing lede and two actions. It fills the first screen and sits at the bottom of that screen.

The catalog is two columns from 860px up: a sticky 4:5 screenshot, and the list of live games. Below 860px the screenshot sticks under the bar, shorter, and the list follows. Testing, the blog index on the home page, and app detail bands are sheets. The screenshot gallery is two columns of the games' own shots on forest; on a narrow screen the shots stack at alternating widths.

The footer is a black field. The wordmark is the name again, in lime, then the existing copyright, privacy link, and language list.

Breakpoints in the stylesheet: 860px and 620px. The header Play button hides at 620px; the in-page actions stay.

## Elevation & Depth

Flat. Bands change by colour, not by shadow. The sticky bar and the sticky screenshot are the only layered elements, and they are opaque. Charts sit on the sheet with no card shadow. Do not add a resting drop shadow, a glass blur, or a gradient fill.

## Shapes

Corners are square (`0`). Buttons, cards, chips, and screenshots do not use pills or circles. The app icon images stay as the stores drew them. The language disclosure uses a CSS triangle, not a glyph.

Tables use a zebra of `color-mix` rather than a 1px rule. Focus is a 2px outline, offset 3px.

## Components

- **Primary action** (`.play`): lime fill, forest text, 48px target, square. Hover lightens the fill on a fine pointer. Press scales to `0.97` in 140ms. The label is the existing sentence ("See all 14 apps", "Get it on Google Play").
- **Text link**: inherited colour, underline on hover, 44px target. No second button style.
- **Game row** (`.card`): icon, name, tagline, and category or "Coming soon". No box. The row under the pointer or in the center of the list is heavier type, and the sticky shot swaps to that game's `data-shot`.
- **Screenshot stage**: one image. Swap is a 140ms opacity dip, then the new source. A slow linear scale drift runs on the picture only.
- **Chips**: text filters, not pills. The current one is heavier. The count stays in a `span`.
- **Post list**: date, title, summary. Titles are `h3` so the existing tests keep finding them.
- **Trail**: the blog breadcrumb and date sit under the title (flex order), in muted type at body size. It is not a label above the heading.
- **Language picker**: a disclosure in the footer. Current language is heavier.

## Do's and Don'ts

- Do keep "Orlov Games" as one text node. A line break tag splits it and the glossary can translate "Games".
- Do use the games' own screenshots. Do not add stock photography or a texture set.
- Do retint muted text when the band changes. Forest muted fails on white.
- Do gate hover styles with `(hover: hover) and (pointer: fine)`.
- Do keep motion on transform and opacity, with a reduced-motion path that leaves content in place.
- Don't put lime on white text, or use it as a second body colour.
- Don't add an eyebrow, a numbered index, a hairline, a gradient, a pill, or a resting shadow.
- Don't invent reviews, ratings, or download counts.
- Don't load fonts from a CDN. The woff2 files in `static/fonts/` are the source.
