# Acaloops

Website for the **Acaloops 50-Mile Fat Ass Loop Trail Ultramarathon** at Acalanes Ridge Open Space in Walnut Creek, California.

**Live site:** https://acaloops.run

## Event

**Date:** Saturday, May 15, 2027

Acaloops is a loop trail ultra built around an approximately **8.5-mile course with 2,400+ feet of climbing per lap**.

Six laps = approximately:

- 51 miles
- 14,500+ feet of climbing

The event starts and finishes on Mallard Drive in Walnut Creek, adjacent to Acalanes Ridge Open Space.

## Site

This is intentionally a simple static website hosted with **GitHub Pages**.

It uses:

- HTML: `index.html`
- CSS: `styles.css`
- Images and route assets: `assets/`
- Python elevation-profile generator: `scripts/generate_elevation_profile.py`
- Strava's external embed script for the interactive route

There is:

- no framework
- no build system
- no CMS
- no custom JavaScript
- no backend
- no database

The site can therefore be maintained by editing the HTML and CSS directly and pushing the changes to GitHub.

## Project Structure

```text
acaloops/
├── assets/
│   ├── images/
│   │   ├── acalanes-ridge-open-space-diablo-view.jpeg
│   │   └── elevation-profile-200-800-by-100.svg
│   └── route/
│       └── acaloop.gpx
├── scripts/
│   └── generate_elevation_profile.py
├── CNAME
├── README.md
├── index.html
└── styles.css
```

## Page Structure

The page currently consists of:

```text
Hero

Event Info
────────────────────
The Loop
────────────────────
Segment Showdown
────────────────────
Explore the Loop
────────────────────
RSVP
────────────────────
Footer
```

The major content sections are separate `<section>` elements in `index.html`.

Current section IDs include:

```text
#details
#route
#segments
#interactive-route
```

These IDs can also be used for direct links to individual sections if needed later.

## The Loop

The GPX file used by the site is:

```text
assets/route/acaloop.gpx
```

Current route summary:

```text
Distance:       8.5 mi
Climbing:       2,400+ ft
Laps:           6
Total distance: 51 mi
Total climbing: 14,500+ ft
```

The current Strava route is:

```text
https://www.strava.com/routes/3536498169656453488
```

The GPX file is also downloadable directly from the website.

## Elevation Profile

The elevation profile is generated from:

```text
assets/route/acaloop.gpx
```

using:

```text
scripts/generate_elevation_profile.py
```

Run the generator from the repository root with:

```bash
python3 scripts/generate_elevation_profile.py
```

The generated SVG currently used by the website is:

```text
assets/images/elevation-profile-200-800-by-100.svg
```

The profile uses a fixed displayed elevation range of approximately:

```text
200–800 ft
```

with 100-foot elevation intervals.

If the route changes, update the GPX and regenerate the elevation profile rather than manually redrawing it.

Raw GPX elevation gain may differ somewhat from Strava, COROS, or other platforms because those services use their own elevation correction and smoothing.

For public event copy, the route is described as approximately **2,400 ft of climbing per lap**.

## Segment Showdown

Segment Showdown is its own major page section.

The desktop layout uses a centered 2 × 2 CSS Grid.

The important CSS concept is:

```css
.segments-grid {
  display: grid;
  grid-template-columns: repeat(2, max-content);
  justify-content: center;
}
```

`max-content` allows each column to size itself to its contents instead of stretching across the full width of the page.

`justify-content: center` then centers the compact two-column grid.

On mobile, the layout switches to a single full-width column:

```css
.segments-grid {
  grid-template-columns: 1fr;
}
```

Do not automatically replace this mobile `1fr` with `max-content`. The full-width single-column layout is intentional.

## Responsive Layout

The stylesheet currently uses three responsive breakpoints:

```text
900px — general tablet adjustments
800px — Segment Showdown switches from 2 × 2 to 1 × 4
600px — general mobile adjustments
```

These are based on where the layout benefits from changing rather than on specific device models.

The mobile layout includes changes such as:

- single-column event details
- single-column Segment Showdown
- two-column route statistics
- vertically stacked route buttons
- smaller hero/supporting typography where needed

## Typography

The primary site font stack is:

```css
"Helvetica Neue",
Helvetica,
Arial,
sans-serif
```

The supporting text in the hero uses:

```css
"Roboto Condensed", sans-serif
```

Roboto Condensed is loaded through Google Fonts in `index.html`.

The large `ACALOOPS` hero title intentionally continues to use the main sans-serif stack.

## CSS Organization

`styles.css` is organized in approximately the same order as the page:

```text
1. DESIGN TOKENS
2. GLOBAL
3. HERO
4. BUTTONS
5. MAIN LAYOUT
6. DETAILS
7. ROUTE
8. SEGMENT SHOWDOWN
9. RSVP
10. FOOTER
11. TABLET
12. SEGMENT GRID BREAKPOINT
13. MOBILE
```

When adding or modifying styles, prefer editing the appropriate existing section instead of creating unnecessary new selectors.

### General CSS conventions

The stylesheet currently uses:

- `rem` primarily for typography
- `em` when a value should scale relative to its parent text
- `vw` for deliberate viewport-responsive typography
- `vh` for hero height
- `px` for much of the fixed layout spacing and borders

There is no requirement that every measurement use the same unit.

Clarity is more important than mechanical consistency.

### Spacing

When choosing new fixed spacing values, a rough 4-pixel rhythm is useful:

```text
4
8
12
16
20
24
28
32
36
40
48
56
64
72
96
```

Existing values should not be changed merely to make them fit this sequence if the current design already looks right.

## CSS Cache Busting

Browsers may sometimes continue using an older cached copy of `styles.css` after the stylesheet has been changed.

The simplest cache-busting method for this site is to add a version query string to the stylesheet URL.

Instead of:

```html
<link rel="stylesheet" href="styles.css">
```

use:

```html
<link rel="stylesheet" href="styles.css?v=1">
```

After a meaningful CSS update, increment the version:

```html
<link rel="stylesheet" href="styles.css?v=2">
```

then:

```html
<link rel="stylesheet" href="styles.css?v=3">
```

and so on.

The query string does **not** mean there are separate files named:

```text
styles.css?v=1
styles.css?v=2
```

There is still only one file:

```text
styles.css
```

The changing URL simply encourages browsers and intermediary caches to request the latest copy instead of reusing a previously cached version.

There is no need to increment the number for every tiny development change.

A reasonable workflow is to increment it when a meaningful CSS update is ready to be relied upon publicly.

During development, other ways to force-refresh the stylesheet include:

```text
Chrome hard reload:
Command + Shift + R
```

or opening DevTools and enabling:

```text
Network → Disable cache
```

while DevTools is open.

## RSVP

RSVP currently links to an external Google Form:

```text
https://forms.gle/oJFLSTh5SJZNJ9s4A
```

The form opens in a new tab.

External links use:

```html
target="_blank"
rel="noopener noreferrer"
```

The form is intentionally linked rather than embedded in the site.

## Hosting

The site is hosted with **GitHub Pages** from:

```text
b-barrett/acaloops
```

GitHub Pages publishes from:

```text
main branch
repository root
```

There is no separate deployment command or build step.

Normal deployment is simply:

```text
edit files
→ commit changes
→ push to main
→ GitHub Pages publishes the updated site
```

Changes may take a short time to appear publicly.

## Custom Domain

The canonical domain is:

```text
acaloops.run
```

The repository contains:

```text
CNAME
```

whose contents are:

```text
acaloops.run
```

GitHub Pages HTTPS is enabled.

### DNS

DNS is managed through Porkbun.

The root domain uses the standard GitHub Pages A records:

```text
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

`www` points to:

```text
b-barrett.github.io
```

using a CNAME record.

Do not remove or replace these records without a reason, since they are what connect the custom domain to GitHub Pages.

## Alternate Domain

The singular domain:

```text
acaloop.run
```

is also owned.

It is intentionally **not** a second website.

Porkbun URL forwarding permanently redirects it to:

```text
https://acaloops.run
```

The redirect is configured as a permanent `301` redirect and includes requested URI paths.

The canonical/official domain should remain:

```text
acaloops.run
```

## Domain / Hosting Responsibilities

Current division of responsibilities:

```text
Porkbun
  Domain registration
  DNS
  acaloop.run → acaloops.run redirect

GitHub
  Source code
  Version history

GitHub Pages
  Static website hosting
  HTTPS

Google Forms
  RSVP form

Google Sheets
  RSVP response storage
```

There is currently no need for Cloudflare, paid Porkbun web hosting, WordPress, or another hosting platform.

## Making Changes

For normal site maintenance:

1. Edit `index.html` for content or page structure.
2. Edit `styles.css` for appearance or responsive behavior.
3. Update assets under `assets/` when necessary.
4. Regenerate the elevation profile if the GPX changes.
5. Preview the changes locally or through GitHub Pages.
6. Commit the working version.
7. Push to `main`.
8. If appropriate, increment the stylesheet cache-busting version.

Try to change one meaningful thing at a time when tuning the design. This makes it much easier to understand which CSS property actually caused the visual change.

## Design Philosophy

The site is intentionally restrained.

Current design priorities include:

- large, distinctive Acaloops hero
- clear event information
- strong route statistics
- custom elevation profile
- centered Segment Showdown
- minimal decoration
- generous whitespace
- simple responsive behavior
- no unnecessary cards, icons, frameworks, or effects

When adding something new, prefer extending the existing visual system rather than creating a new one.

## Possible Future Additions

Ideas that have been discussed but are not required for the current site include:

- route time-lapse video
- direct links to individual page sections
- richer social-sharing metadata
- annual results and recap photos
- more detailed documentation if the site becomes significantly more complex

The current static architecture does not prevent adding a backend, database, or other services later if they ever become useful.
