# What's Open: ADA Title II accessibility testing

Working record for testing the What's Open directory against **WCAG 2.1 Level AA**. Keep this file current: update the checklist and add a dated entry to the results log after every round of testing or any significant change to the page.

> This is a testing record, not legal advice. Have the City's ADA coordinator or counsel review the conclusions before the site is described as compliant.

| | |
|---|---|
| **Product** | What's Open: Downtown Rochester business directory and construction access map |
| **Live address** | <https://chenghmatthew.github.io/RochesterMN/> (also embedded in the City's Squarespace page) |
| **Standard** | WCAG 2.1 Level A and AA (50 success criteria) |
| **Owner** | _(name the person responsible for testing and fixes)_ |
| **City reviewer** | _(City ADA coordinator or web owner)_ |
| **Last full test** | Not yet done. Baseline automated check: 2026-11-17 |

## 1. Why this applies

The U.S. Department of Justice's 2024 rule updating ADA Title II (28 CFR Part 35, Subpart H) requires state and local government web content and mobile apps to meet **WCAG 2.1 Level AA**. Compliance dates are staggered by population: entities of 50,000 or more by **April 24, 2026**, smaller entities and special districts by April 26, 2027. Rochester, MN is above 50,000. Confirm the date and any exceptions that apply to this site with the City, because this tool is published for the City even though it is hosted outside the City's domain.

## 2. Scope

Three views and every state the visitor can reach:

- **Map**: markers, clusters, popups, legend, basemap switch, City live layers, walking and parking routes.
- **Cards**: business cards, photos, filters, search, "Details and walking route".
- **List**: grouped rows, expandable details.
- Business detail panel and route results.
- The Squarespace embed (the page inside an iframe).
- Phone-width layout (under 760px) and the desktop layout.

Out of scope: third-party content shown inside the page (Mapbox's own controls, the City's ArcGIS layers). Record problems in those, report them to the provider, and make sure the Cards and List views offer an equivalent.

## 3. Test environment

Record the versions used for each round in the results log.

| Area | Tools |
|---|---|
| Automated | `automated-check.js` in this folder (paste in the browser console), axe DevTools, WAVE, Lighthouse |
| Contrast | Colour Contrast Analyser, or the check in `automated-check.js` |
| Screen readers | NVDA with Firefox and Chrome (Windows), VoiceOver with Safari (iPhone) |
| Keyboard | Keyboard only, no mouse |
| Zoom and reflow | Browser zoom 200% and 400%, a 320px-wide window, Windows text size at 150% |
| Devices | One desktop, one iPhone, one Android phone |

## 4. Test procedure

Run these for each of the three views. Note failures with the view, steps and what was expected.

1. **Automated pass.** Run axe DevTools and WAVE, then `automated-check.js`. Fix or log everything reported. Automated tools find only part of the problems, so a clean scan never means compliant.
2. **Keyboard.** Using Tab, Shift+Tab, Enter, Space and Escape only: reach every control (tabs, filters, search, cards, popup buttons, route buttons, legend, basemap switch); the focus outline is always visible (2.4.7); the order makes sense (2.4.3); there are no traps (2.1.2); Escape closes popups and focus returns to a sensible place; nothing needs a mouse drag or the map itself (2.1.1).
3. **Screen reader.** Open the page cold and complete these tasks without sight: find a named business, read its hours and access notes, filter to "Open now", start a route from a parking ramp, and hear the result. Check that headings, landmarks, button names, state ("selected", "expanded") and route results are announced (4.1.2, 4.1.3).
4. **Zoom and reflow.** At 200% and at a 320px-wide window nothing is cut off, overlaps, or needs two-way scrolling (1.4.4, 1.4.10). Apply the text-spacing bookmarklet and confirm nothing is lost (1.4.12).
5. **Color and contrast.** Text 4.5:1 (3:1 for large text), interface parts and map lines 3:1 (1.4.3, 1.4.11). Turn on a grayscale filter: closure types and categories must still be distinguishable without color (1.4.1).
6. **Touch.** On a phone, targets are comfortably tappable and nothing requires a gesture that has no simple alternative (2.5.1 to 2.5.4).
7. **Embed.** Repeat steps 2 and 3 inside the Squarespace page: the iframe has a title, focus enters and leaves it, and a page with the embed has no keyboard trap.

## 5. WCAG 2.1 A and AA checklist

Status values: **Pass**, **Fail**, **Partial** (some views or states tested), **Needs work** (known gap, not fixed), **Not tested**, **N/A**. Update the notes with the date and view tested.

### Perceivable

| SC | Name | Level | Status | Notes |
|---|---|---|---|---|
| 1.1.1 | Non-text content | A | Partial | Photos now have alt text "Photo of {business}" (2026-11-17). Map markers, route lines and closure shapes need a text equivalent; Cards and List are the alternative. |
| 1.2.1 | Audio-only and video-only | A | N/A | No audio or video. |
| 1.2.2 | Captions (prerecorded) | A | N/A | No audio or video. |
| 1.2.3 | Audio description or media alternative | A | N/A | No audio or video. |
| 1.2.4 | Captions (live) | AA | N/A | No audio or video. |
| 1.2.5 | Audio description (prerecorded) | AA | N/A | No audio or video. |
| 1.3.1 | Info and relationships | A | Partial | Card titles are now `h2` under the one `h1`; search box labeled. Check popups, detail panel, List view, filter chips (grouped and labeled?) and tab roles. |
| 1.3.2 | Meaningful sequence | A | Not tested | |
| 1.3.3 | Sensory characteristics | A | Not tested | Instructions must not rely on color or position alone. |
| 1.3.4 | Orientation | AA | Not tested | |
| 1.3.5 | Identify input purpose | AA | Not tested | Search box only; likely N/A. |
| 1.4.1 | Use of color | A | Needs work | Closure types and categories rely on color. Add patterns, dashes or labels. |
| 1.4.2 | Audio control | A | N/A | |
| 1.4.3 | Contrast (minimum) | AA | Partial | Cards view: 0 failures by automated check (2026-11-17), after changing gray text `#77828A` to `#5B6770`. Map, List, popups, detail panel, legend not yet scanned. |
| 1.4.4 | Resize text | AA | Not tested | |
| 1.4.5 | Images of text | AA | Not tested | Business logos and photos are exempt where they are logos. |
| 1.4.10 | Reflow | AA | Not tested | Test at 320px wide. |
| 1.4.11 | Non-text contrast | AA | Needs work | Map lines, markers, focus rings and control borders need 3:1. |
| 1.4.12 | Text spacing | AA | Not tested | |
| 1.4.13 | Content on hover or focus | AA | Not tested | Popups open on click; check tooltips and the legend. |

### Operable

| SC | Name | Level | Status | Notes |
|---|---|---|---|---|
| 2.1.1 | Keyboard | A | Not tested | The map itself cannot be fully operated by keyboard; confirm Cards and List give the same information and routes. |
| 2.1.2 | No keyboard trap | A | Not tested | Include popups and the iframe. |
| 2.1.4 | Character key shortcuts | A | Not tested | Escape only, so likely pass. |
| 2.2.1 | Timing adjustable | A | N/A | No time limits. |
| 2.2.2 | Pause, stop, hide | A | Not tested | Check map animations and fly-to motion. |
| 2.3.1 | Three flashes | A | Not tested | |
| 2.4.1 | Bypass blocks | A | Needs work | No skip link; only one landmark found. Add "Skip to businesses" and landmarks (`header`, `nav`, `main`). |
| 2.4.2 | Page titled | A | Pass | "What's Open – Downtown Rochester" (2026-11-17). |
| 2.4.3 | Focus order | A | Not tested | |
| 2.4.4 | Link purpose (in context) | A | Not tested | "Details and walking route" repeats on every card; consider accessible names that include the business. |
| 2.4.5 | Multiple ways | AA | Pass | Map, Cards, List and search. Confirm in testing. |
| 2.4.6 | Headings and labels | AA | Partial | Heading structure fixed for Cards. Check the other views. |
| 2.4.7 | Focus visible | AA | Not tested | |
| 2.5.1 | Pointer gestures | A | Not tested | Map pinch and drag need a simple alternative (zoom buttons). |
| 2.5.2 | Pointer cancellation | A | Not tested | |
| 2.5.3 | Label in name | A | Not tested | |
| 2.5.4 | Motion actuation | A | N/A | No motion-triggered features. |

### Understandable

| SC | Name | Level | Status | Notes |
|---|---|---|---|---|
| 3.1.1 | Language of page | A | Pass | `lang="en"` added 2026-11-17. |
| 3.1.2 | Language of parts | AA | N/A | English only. |
| 3.2.1 | On focus | A | Not tested | |
| 3.2.2 | On input | A | Not tested | Filters and search update results; confirm no unexpected context change. |
| 3.2.3 | Consistent navigation | AA | Not tested | |
| 3.2.4 | Consistent identification | AA | Not tested | |
| 3.3.1 | Error identification | A | N/A | No data-entry forms beyond search. Re-check if one is added. |
| 3.3.2 | Labels or instructions | A | Pass | Search box has a label (2026-11-17). |
| 3.3.3 | Error suggestion | AA | N/A | |
| 3.3.4 | Error prevention | AA | N/A | |

### Robust

| SC | Name | Level | Status | Notes |
|---|---|---|---|---|
| 4.1.1 | Parsing | A | Not tested | Obsolete in WCAG 2.2; still listed in 2.1. Validate the page. |
| 4.1.2 | Name, role, value | A | Partial | No unnamed buttons, no clickable elements missing a role (2026-11-17). Check tab state, expanded rows, filter chips (pressed state). The hidden photo file inputs are not exposed to assistive tech and the photo upload is disabled on the public page. |
| 4.1.3 | Status messages | AA | Needs work | Route results, result counts ("305 of 305") and filter changes should be announced via an `aria-live` region. |

## 6. Results log

### 2026-11-17: baseline automated check and first fixes

Method: browser (Edge, headless) against the Cards view, using `automated-check.js`. Single view, desktop width only.

Found, then fixed in `index.html`:

| Finding | SC | Fix |
|---|---|---|
| No `lang` attribute on the page | 3.1.1 | `<html lang="en">` |
| 305 card titles were `h3` with no `h2` above | 1.3.1 | Card titles are `h2` |
| 15 text items at 3.93:1 (addresses, "Live City data", source lines) | 1.4.3 | Gray `#77828A` replaced with `#5B6770` (5.9:1) everywhere it was used |
| Search box had no accessible name | 1.3.1, 4.1.2 | `aria-label="Search businesses"` |
| Photos had empty alt text | 1.1.1 | Alt text "Photo of {business}" for the 302 businesses with photos; none for the 3 without |
| Photo slots showed "Drop a photo… or browse files" to visitors | 3.3.2, 4.1.2 | Slots are read-only on the public page; captions read "No photo available" |

Result after fixes: `lang` set, 1 `h1` and 305 `h2`, 0 contrast failures, search labeled, 302 alt texts, 0 unnamed buttons. The 305 remaining "unlabeled inputs" are the hidden photo file pickers (`hidden`, not exposed).

Not covered by this check: Map, List, popups, detail panel, legend, keyboard use, screen readers, zoom and reflow, phone layout.

## 7. Known issues and next steps

Highest risk first. Mark each done with the date.

1. **Keyboard and the map.** Confirm every function (find a business, read hours, get a route) can be done from Cards or List with the keyboard alone, and add a visible "View as list" link near the map.
2. **Color alone.** Add patterns or dash styles and legend labels for road closure, sidewalk closure and temporary route lines; check marker contrast (1.4.1, 1.4.11).
3. **Status messages.** Add an `aria-live="polite"` region for route results and result counts (4.1.3). Give route results a text version of the directions.
4. **Skip link and landmarks.** Add "Skip to businesses", `<main>`, `<nav>`, `<header>` (2.4.1).
5. **Focus.** Visible focus outline on every control; focus management for popups and the detail panel (2.4.3, 2.4.7).
6. **Repeated link text.** Make "Details and walking route" unique per card for screen readers (2.4.4).
7. **Reflow and text spacing.** Test and fix at 320px, 200% and 400% zoom (1.4.4, 1.4.10, 1.4.12).
8. **Zoom controls.** Provide + and − buttons so the map does not depend on pinch or scroll (2.5.1).
9. **Popup content.** Dismissable, hoverable and persistent (1.4.13).

## 8. Accessibility statement (draft)

Publish this on the City page that hosts the embed, with the City's real contact details.

> The City of Rochester is committed to making What's Open accessible to everyone. We aim to meet the Web Content Accessibility Guidelines (WCAG) 2.1 Level AA. The map is a visual tool, so the same business information, hours, access notes and walking routes are also available in the Cards and List views.
>
> If you have trouble using this tool or need information in another format, contact _(name, phone, email)_. Please include the page, the problem and the device or assistive technology you were using. We respond within _(number)_ business days.
>
> Last tested: _(date)_. Known limitations: _(list from section 7)_.

## 9. Keeping it current

Re-run the automated check and the affected manual tests whenever:

- the page layout, colors, or components change;
- the business data is reloaded (new fields or businesses can introduce blank names or missing alt text);
- a map layer or route style is added;
- once a quarter regardless, and before each major construction phase update.

Keep the dated results log, the screenshots of failures and their fixes, and any user complaints and responses. These records are the evidence if the site is ever reviewed.
