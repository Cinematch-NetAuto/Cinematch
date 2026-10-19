# Design plan

The look of CineMatch, decided before any frontend code. `frontend/src/styles/tokens.css`
(step 35) copies the values below; no colour, font or size appears anywhere else.

## Who and what

- **Who uses it:** people choosing a film to watch tonight, alone or with friends.
- **Its one job:** find a film you will like tonight, and show why it was picked.

## The idea: late at night, outside the cinema

A blue-black night sky, a faint glow above the street, and the cinema's marquee lit
gold against it. The page is the night, the panels are the dusk, the text is the
screen, and every control is lit like a marquee bulb. We chose a dark page because
posters are bright and colourful: in the dark they carry the screen. The gold tiles
and buttons come from the team's film picker sketch. The mood is quiet and elegant:
one thin gold line, generous space, and light only where you can act.

## Colours

Six named colours. Three of them have a second, lighter stop for their one gradient.

| Name | Hex | Used for | Contrast |
|---|---|---|---|
| Night | `#04070D`, glow `#0C1528` | Page background | — |
| Dusk | `#121D33` → `#0B1324` | Panels, posters without an image, unchosen tiles, inputs | — |
| Screen | `#E8EDF5` | Headings and main text | 15.5:1 on the Night glow, 14.3:1 on Dusk |
| Programme | `#93A3BD` | Years, vote counts, hints, captions | 7.1:1 on the Night glow, 6.6:1 on Dusk |
| Marquee | `#F2A93B`, light `#F8C76E` | Everything you can click or have chosen: buttons, links, chosen tiles, likes, the focus ring, the gold line under the nav bar | 8.4:1 on Dusk; Night text on it 10.1:1 |
| Exit sign | `#FF7F6B` | Dislikes and error messages | 6.8:1 on Dusk |

Every contrast is measured at the lightest point of its gradient, the hardest case,
and passes the 4.5:1 minimum. Marquee is the only colour that means "you can act
here". Hairline borders use `#1E2B45`. The gold hairline under the nav bar uses
Marquee at 18 % opacity.

## Gradients: three, and only these

Each gradient models light at night. Nothing else gets one: no text, no section
backgrounds, no decoration.

| Where | Gradient | The light it shows |
|---|---|---|
| Page background | Radial: Night glow (`#16264A` at the top centre, then `#0C1528`) out to Night (`#04070D`) at the edges | The sky above the street lights |
| Panels and poster placeholders | Top to bottom: `#121D33` → `#0B1324` | A faint sheen, as if lit from above |
| Chosen tiles and main buttons | Top to bottom: `#F8C76E` → `#F2A93B` | A lit marquee bulb |

## Type

| Typeface | Role | Why |
|---|---|---|
| League Gothic (`@fontsource/league-gothic`) | Page titles, section headings, film titles on the film page | The tall, narrow capitals of classic film-poster title blocks. Its letters are capitals by design |
| Atkinson Hyperlegible (`@fontsource/atkinson-hyperlegible`) | All other text: body, buttons, labels, numbers | Designed to stay readable at small sizes, which matters for light text on a dark page |

- Both are installed from npm and bundled with the app, so the offline demo has
  them. Licence: SIL Open Font License 1.1 (free).
- Sizes, in px: 14 (captions), 16 (body), 20 (card titles), 28 (section headings),
  40 (page titles), 64 (the film title on the film page).
- Line height: 1.5 for text, 1.05 for League Gothic headings.
- Labels, buttons and helper text use sentence case. Only League Gothic is in
  capitals, and only because the typeface is.
- Text lines stay under 75 characters.

## Shape and space

- **Corners follow the object, not one rule for everything:** posters 4 px (a
  printed one-sheet), tiles and buttons 8 px, the reason card cut like a ticket
  stub (square corners with a half-circle notch on each side).
- **No shadows.** Depth comes from Night → Dusk and the panel sheen. The only glow
  is the 2 px Marquee focus ring, offset 2 px.
- **One gold hairline**, under the nav bar. The reason ticket has no outline: its
  shape comes from two notches cut out of its sides, so the night shows through.
- **Headings breathe:** League Gothic with 1.5 px letter spacing (3 px for the
  CINEMATCH name).
- **Spacing steps, in px:** 4, 8, 12, 16, 24, 32, 48. No other values.
- **Layout:** content up to 1200 px wide and centred, 24 px side margin (16 px on a
  phone). Text and grids are left-aligned.
- **Poster grid:** `repeat(auto-fill, minmax(160px, 1fr))`, gap 16 px. Posters keep
  the 2 : 3 film-poster shape. That gives 2 columns on a phone and 6 on a laptop
  without a single media query.

## Sketches

Home (`/`), logged in:

```
+-------------------------------------------------------------------+
| CINEMATCH     [ Search films...      ]   Discover  For you  Ava v |
+-------------------------------------------------------------------+
| FOR YOU                                              See all 20   |
| +------+ +------+ +------+ +------+ +------+ +------+             |
| |      | |      | |      | |      | |      | |      |             |
| |poster| |poster| |poster| |poster| |poster| |poster|             |
| |      | |      | |      | |      | |      | |      |             |
| +------+ +------+ +------+ +------+ +------+ +------+             |
| Interstellar  Arrival  ...                                        |
| Because you liked Inception                                       |
|                                                                   |
| POPULAR NOW                                                       |
| +------+ +------+ +------+ +------+ +------+ +------+             |
| | ...  | | ...  | | ...  | | ...  | | ...  | | ...  |             |
+-------------------------------------------------------------------+
| This product uses the TMDB API but is not endorsed or certified   |
| by TMDB.                                              [TMDB logo] |
+-------------------------------------------------------------------+
```

One poster card in the grid:

```
+----------+
|          |   poster, 2:3, 4 px corners
|  poster  |   no poster -> Dusk panel with the title in League Gothic
|          |
+----------+
Interstellar        title, 16 px, one line, cut with "..."
2014   8.5          year and rating in Programme
```

## One bold thing per screen

Each main screen has exactly one element that gets the strong treatment. Everything
around it stays quiet.

| Screen | The bold thing |
|---|---|
| Recommendations | **The reason card**: a ticket under each poster, with the reason ("Because you liked Inception") in Marquee and the rating on a torn-off stub |
| Discover and sign-up | **The film picker**: the team's tile picker for genres, release period and minimum rating. A chosen tile fills with Marquee |
| Film page | **The backdrop**: the film's wide still across the top, fading into Night, with the poster and a 64 px League Gothic title over it |

The reason card:

```
 .--------------------------------:-------.
(  Because you liked Inception    :  8.5  )   reason in Marquee, no outline
 |  Sci-fi and drama              :       |   detail in Programme
 '--------------------------------:-------'
                                  ^ dashed tear line; the rating in League Gothic
```

## Motion: none

Pages appear at once, with no animation. A chosen tile or a like changes colour
instantly. Nothing slides, fades or plays by itself, so nothing can stutter in a
demo, and the reduced-motion check (step 54) passes by design.

## Three principles

1. **The poster is the interface.** Big posters, few words. A screen that shows
   films shows posters first.
2. **One bold thing per screen.** If two things shout, make one quiet.
3. **Still pages.** No animation anywhere. When you click, the result simply
   appears: a tile fills, a like turns gold.

## Generic looks we checked against

| Common default | What we did instead |
|---|---|
| Near-black (`#0B0B0B`, `#111`) with one bright accent | A blue-black night with a visible sky glow, not a flat tinted black. Gold stays because it is the marquee lit against the night, plus a second working colour (Exit sign) for dislikes and errors |
| Fade-and-slide-up entrances on every section | No animation at all. Pages appear at once |
| Gradient washes as decoration | Three gradients only, each one a light source: the sky glow, the panel sheen, the lit bulb on chosen tiles and main buttons |
| One corner radius on every element | Corners by object: poster 4 px, controls 8 px, the reason card a notched ticket |
| Identical rounded cards with the same soft shadow | No shadows and no card boxes around posters: the poster is the card |
| Small capitals labels above every heading | No labels above headings. Sentence case for every label |
| The "movie app" font (Bebas Neue) | League Gothic, the older poster title face |
| An arrow added to every button and link ("See all →") | Buttons say what they do, with no arrow |

## Checks for every screen

- Every control is reachable with Tab and shows the Marquee focus ring.
- Every poster has alt text: the film title.
- Every list has its loading, empty and error state (step 38).
- Pages work at 375 px wide (step 54).
- The footer TMDB notice is on every page.
