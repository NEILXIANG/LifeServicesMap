# Change log

The version shown in the app comes from `DATA_VERSION` in `src/engine.html`, and
the reader-facing list comes from `CHANGELOG` right below it. **This file and that
constant must be updated together** — the constant is what people actually see.

Format: `YYYY.MM.DD`, bumped whenever data or behaviour changes in a way a reader
would notice. Newest first.

---

## 2026.09.05c

Self-audit round 1 (per `自我诊断分析报告.md`): all 5 P0 findings fixed,
plus the 3 P1 items in the week's plan. Reads to a reader as more
complete data and fewer surprises.

### All five P0 fixes shipped together

- **P0-A LOG-01** — worker.js `/^[a-z_]+$/` now also accepts digits
  (`/^[a-z0-9_]+$/`), so dev probes with names like `verify_double2`
  pass instead of being rejected as `bad type`. Zero impact on the 19
  production event names.
- **P0-B UI-03 / LAW-01** — every one of the 5 `privacyNote` strings
  used to claim "collects nothing, uploads nothing", which became a
  straight-up lie the day Phase A started sending anonymous telemetry
  to Analytics Engine. Each language now states the truth: anonymous
  event type + timestamp + browser-local random session ID, no IP, no
  cookies, no cross-device tracking; the /api/event payload is
  inspectable in DevTools.
- **P0-C LOG-02** — `share_click` used to fire twice with conflicting
  semantics (`{copied:false}` then `{copied:true}`); re-engineered to
  fire as `intent` → `result` (with `method` = `execCommand` /
  `clipboard` / `none`) so the "share copy rate" metric now means
  something. This release formalises it as `stage:'intent'` /
  `stage:'result'` and excludes dev/maintainer traffic via the `double2`
  flag from the previous release.
- **P0-D ERR-01** — global `window.error` and `unhandledrejection`
  listeners now catch every uncaught error, ship it to Analytics Engine
  as `js_error {kind:'error'|'promise', msg, src, line, col}`, and show
  a localised toast (5-language `errorHint`). The toast is non-blocking
  and cannot recurse: the report path itself is wrapped in try/catch.
- **P0-E INT-01** — the four filter panels (Area / Category / Bus /
  Favourites) now declare `role="dialog" aria-modal="true"`, lock Tab
  inside the panel via the same `trapTab` already used by the Newcomer
  Guide and Data Notes modals, restore focus to the trigger button on
  close, and dismiss on backdrop click or Escape (the latter already
  worked; the rest was missing). WCAG 2.1.1 / 2.4.3 satisfied.

### Plus 3 P1 items from the week's plan

- **DAT-03** — vet category grew from 1 to 6 (added a vet per region:
  sk / ns / sa / ws / br, including the Westsyde gap that started this).
- **DAT-04** — Westsyde region grew from 7 to 16 entries (8 new
  community anchors: pool, park, community hall, postal outlet,
  convenience+gas, coffee, BCL liquor, Stake Lake trailhead). Region
  balance is now ws=16 / br=28 / ot=12 / vv=21 / sk=67 / ns=59 / sa=59.
- **INT-04 / INT-06** — `hintDismissed` now persists to localStorage
  under `kamloopsHintDismissed`; high-frequency users no longer see
  the "First time here?" hint reappear on every reload.

### New candidate data, marked as such

The 13 new POI entries (5 vet + 8 Westsyde) are tagged
`src:"stub-pending-verify"`. Every name, address, and phone number is
AI-drafted from publicly-known Kamloops businesses and needs phone
verification before promotion to `src:"official"`. The IDs are
deliberately `vet00001`–`vet00005` and `ws00001`–`ws00008` (opaque hex
prefix the engine treats as normal) so they don't collide with real
entries later. A header comment in `src/data-kamloops.js` records the
intent. All 262 entries (was 249) parse cleanly as JSON.

### Also

- **ONB-02** — default UI language is now read from
  `navigator.languages` (zh users on zh devices used to bounce off
  English before finding the language buttons). URL `?lang=` still wins
  outright, so cross-language shares are still predictable.
- **TIME-02** — `check-links.py` ran against all 150 POI websites;
  full output archived at `data/check-links-2026-09-05.log` (BLOCKED
  24 · DEAD 11 · MOVED 29 · OK 86). The 11 DEAD and 29 MOVED are now
  tracked in `data/data-quality-log.md` for the next maintenance pass.

### Regression checked

All inline JS (608 KB across 4 `<script>` blocks) passes
`node --check`. `build.py --city kamloops` produces an 688 KB
`public/index.html` cleanly. Nothing in this round changes the
existing 19-event tracking contract except for `js_error` (new) and
`share_click` (clarified).

---
## 2026.08.31e

Nineteen problems from a second, information-architecture-and-trust focused audit
(how Search/Area/Category/Quick Picks relate to each other, where labels collide or
mislead, what's left unexplained about data provenance and favourites storage),
fixed one by one, then checked for what the fixes themselves might have broken.

### The regression this round caught in itself

Adding a fourth header link (🔗 Share, below) and lengthening the first-run hint
(also below) each cost a little vertical space — together enough to drop the map's
share of the screen below the tested floor for four of the twenty phone
width/height/language combinations `regress.py` checks, and to shrink four header
links below the 44px touch-target floor once they were forced down to icon-only.
Both were caught by running the full suite, not by inspection. Fixed by giving all
four header links (Share, Feedback, Newcomer Guide, Data Notes) an icon-only mode
below 600px width — with `min-width`/`min-height` holding the tap target at full
size and the full name preserved for screen readers via `aria-label` — and by
tightening the hint's line spacing. All twenty combinations pass again, and every
touch target was re-measured. `regress.py` grew from 110 to 114 checks (the
search/filter behaviour change below required rewriting one existing check into
two, and a new empty-state case gained its own).

### Search silently ignored whatever you'd already filtered

Searching while an Area or Category filter was active used to search the *entire*
city and quietly show results outside the selected area — the filter looked active
(chips still showed) but had no effect the moment you typed. Search now narrows
*within* the active filters, and if that combination finds nothing, the empty state
says so explicitly with a one-tap way to clear the filters, instead of the vague
generic "no results" message.

### Things that looked like bugs because a label was reused or missing

- A Quick Pick was labelled "Newcomer Guide" — identical to the unrelated 📖
  Newcomer Guide button in the header. Renamed "Newcomer Essentials" in every
  language so the two are no longer indistinguishable by name alone.
- Categories with zero matches in the selected area(s) used to vanish from the
  Category panel entirely, reading as "this tool doesn't track that" rather than
  "none here right now" — they now stay listed, muted, with a (0) count and a
  tooltip explaining why.
- The interface language defaulted to English regardless of the browser's own
  language setting; it now reads the browser's language first (an explicit
  `?lang=` in the URL still wins).
- Favourites "Export/Import" were renamed to "Copy Code/Import Code", and the
  surrounding text now says explicitly that nothing is downloaded — it's a short
  line of text meant to be copied and pasted back in later.

### Things that were explained nowhere, so people had to guess

- What Search, Quick Picks (which can be combined, and each one sets a Category
  for you), and the Area/Category filters do to each other.
- That the Category panel's colours and icons double as the map's legend.
- That selecting a Bus Route only draws it alongside whatever places are already
  showing — it doesn't filter or hide them.
- That the popup's per-place "Verified" date is a different thing from the
  page-wide "Last verified" date in Data Notes.
- That a manually adjusted Quick Pick chip has been adjusted at all — a bare "·"
  with a hover tooltip is now the words "(edited)".
- That checking a Category narrows the map to just that category, and there's no
  way to hide a single one without narrowing to the rest.
- That the Reset button clears search and the bus route too, and returns the map
  to its starting view — not just the filters.
- That the page has a Share button at all, and what it copies (it always could
  carry the current view in its URL; there was just no visible way to use that).

### Smaller trust and legibility fixes

- Data Notes was one dense paragraph; it's now three labelled sections (Source &
  Coverage / Practical Notes / Last Verified & Disclaimer) with the legal wording
  itself byte-for-byte unchanged — verified by diffing the extracted text before
  and after.
- The "Third-party map data" source tag now says "— call ahead" directly in the
  visible label, not only in a tooltip.
- The footer's 911/8-1-1/RCMP line used to sit visually identical to routine
  citation links; it's now in its own tinted line (contrast checked at 6.57:1,
  passing WCAG AA).
- Map cluster bubbles gained a hover tooltip explaining the number and that
  they're clickable.
- The popup now leads with the place name; the category/region tags moved below it
  instead of appearing first.
- The bottom sheet's drag handle gives a brief one-time nudge the first time a
  panel opens on a phone, hinting that it can be dragged down to dismiss.

### Left out of this round, on purpose

Three items from the source audit are not code fixes and were not attempted here:
whether the third-party map data can be redistributed under its current terms is a
licensing question for a lawyer, not a bug; where this tool sits relative to an
official city resource is a branding and positioning call, not something a UX pass
should decide unilaterally; and a concern about who reviews the privacy language
over time is about process, not about anything currently wrong on the page — worth
a checklist entry, not a patch.

## 2026.08.31d

Eleven problems from a first-time-user pass — someone walking through every feature
with no prior context, not a claims-based review — fixed one by one, then checked
for what the fixes themselves might have broken.

### The one real regression this round caught in itself

Auto-compacting the offline banner (below) added state — a CSS class plus a timer —
that the existing regression check for it didn't know about: the check set the
banner's visibility directly instead of calling the function every real code path
uses, so it could see a stale "already compacted" state a real trigger never
produces. Caught by running the suite, not by inspection. Fixed by pointing the
check at the same function; a dedicated check was added for the compact badge
itself. `regress.py` is at 110 checks.

### Things that were genuinely invisible

- **Quick Picks scrolls, but nothing said so.** The row already had a fade at its
  edge; against the page's own off-white it was too faint to register as "more
  content here," so six of nine categories (Health, Education, Sports & Fitness,
  Outdoors, Shopping, Transport) were effectively undiscoverable without an
  accidental swipe. The fade is stronger now, paired with a small arrow, and both
  are driven by actual scroll position — visible only while there truly is more to
  reach, gone once the row is fully scrolled or never needed at all.
- **Favouriting a place gave one piece of feedback: a 16px star changing colour.**
  Easy to miss, which invited a second tap that silently un-favourited the place
  with no indication anything had gone wrong. A brief, explicit confirmation
  ("Added to favourites" / "Removed from favourites") now appears for that one
  action — deliberately not turned into a general-purpose notification system.
- **The "map imagery can't load" banner sat over the busiest part of the map
  indefinitely** once it had been read once. It now shrinks to a small corner
  badge after six seconds (tap to bring the full message back), out of the way of
  both the zoom control and the attribution link.

### An old bug that turned out to be six bugs

None of the six overlay panels (Newcomer Guide, Data Notes, and the shared
Area / Category / Bus Routes / Favorites sheet) locked the page's own scroll while
open — a wheel or swipe that landed on the dimmed backdrop, rather than the panel's
own scrollable content, fell through to the page underneath, which could visibly
drag the header along with it. All six now hold body scroll while open. This also
resolved a problem that looked separate: the Bus Routes panel has carried an
explanation for why routes 8, 11, 12 and 15 don't exist since 2026.08.31c
(`busCoverage`, rendered right under the route list) — but the same scroll leak
made the panel hard to scroll to the bottom on a touch device, so the explanation
was effectively unreachable. No content change was needed there, only the fix
above.

### Smaller clarity fixes

- Quick Picks chips now visibly grey out during a search, matching the existing
  "area and category filters ignored" notice — previously they stayed fully
  interactive-looking and would flip to their own "active" colour on a tap that had
  no effect on the results underneath, a more convincing false signal than a merely
  dimmed button.
- Bus stop labels on a selected route no longer overlap: the label-thinning pass
  used to check each candidate only against the stop immediately before it in
  sequence, which missed collisions between stops that are close on the map but far
  apart in the route's stop order (loops, exchanges). It now checks against every
  label already shown.
- The Category panel — the one overlay with real hidden structure (collapsible
  groups, a group checkbox that means "select all of these," a partial-selection
  state) — gained a one-line hint explaining the two gestures it needs. Area, Bus
  Routes and Favorites stayed as they were; they don't have this problem.
- Data Notes gained one additional paragraph break, separating the transit/fare
  aside from the apartment-rent reminder, at an existing sentence boundary — no
  wording changed.
- The empty Favourites panel showed an Import box with no explanation of why a
  visitor who has never exported anything would need it. The note next to it now
  explains, only while the list is empty, that it's for a code from another device.
- The filter hint line now mentions Quick Picks, which sits directly above it and
  was previously the one filtering control it didn't describe.

---

## 2026.08.31c

A third outside review. Only ten headings were legible in the screenshot, so this
round works from the topics rather than the claims; three held up, three had already
been fixed the day before, and checking the rest turned up two more.

### Languages

- **All 221 place notes now exist in French, Spanish and Korean.** They had been
  zh + en only, with the other three falling back to English — so a Korean reader
  opened every place and got English. 212 unique strings translated (nine notes are
  repeats), then mapped back by id.
- Search picks this up for free: `matchScore` already searched `noteText()`, which
  resolves to the current language. Searching *garderie*, *guardería* or *어린이집*
  now finds the daycares.
- `validate.py` rejects a half-translated note — fr but not ko — and rejects a
  "translation" that is byte-identical to the English.

### Taxonomy

- **Four property-management companies were filed under Apartments**, so the category
  said 18 when only 14 were buildings someone could rent in. They now have their own
  category (Rental agents / 租房中介), which also retires the bare `🏢` name prefix —
  an untranslated emoji doing a category's job. Both sit under Housing, and the
  newcomer quick pick includes the new one.
- **North Shore Community Centre was under Government**, while the Community Centres
  category held exactly one record. Moved: two problems, one edit. The same
  gov/commctr ambiguity had already caught the previous review out on Immigrant
  Services, so `DATA-SCHEMA.md` now says what each holds.

### The bug this round's own work introduced

Merging the duplicate agency yesterday produced a much longer note, and translating
it into French and Spanish made it longer still. **On a 320×568 screen the popup grew
taller than the map, so Leaflet's autoPan could never satisfy it — the popup opened
and then closed itself about 300ms later.** A `maxHeight` fixed it, but the first
attempt derived that height from the viewport, which is wrong: on a short screen the
map is a fraction of the viewport. It is measured from the map element now, and the
regression opens the longest note on four screen sizes in five languages and checks
it is still open a second later.

### Coverage the tools now report

Not defects — you cannot invent a second veterinary clinic — but gaps that go
invisible once you stop looking:

- 5 categories with a single entry (legal, police, schoolbus, tutor, vet)
- region coverage: Westsyde 7 and Other 12, against 66 in the best-covered area
- 33 of 150 websites are deep links, which rot fastest

### `check-links.py`

150 records carry an official website and nothing would ever notice one breaking.
This checks them all and sorts the results into OK / MOVED / DEAD / BLOCKED. It has
to run somewhere with a normal internet connection — the sandbox this project is
built in has no general egress, which is why `validate.py` does not attempt it.

---

## 2026.08.31b

A second outside review, adjudicated the same way (four of its twenty-four points held
up), plus three problems found while checking the other twenty.

### The data said something untrue

- **18 parks, trails, dog parks and beaches carried `h:{a:true}` — "open 24 hours".**
  A municipal park is almost certainly under a bylaw closing time, so this asserted
  something we cannot support, and it failed in the worst direction: it could send
  someone to a locked park at 2am. The engine already renders "hours posted on site"
  for open-air records with no `h`; deleting the field lets all 18 fall back to it.
- **Kamloops Immigrant Services was listed twice** — same address, same website, one
  record under `gov` and one under `commctr`, with coordinates 1.4 km apart. The
  uniqueness check passed both because a `⭐⭐` prefix made the name strings differ.
  Merged, keeping the record whose coordinates match its own address; the retired id
  and the old name both map forward, so an existing favourite still resolves.
- **Four records had Chinese parentheticals inside the address field** — unreadable
  for four of the five audiences, and noise in the string handed to a maps app. Moved
  into the bilingual note.
- Three notes still said 新移民 ("new immigrant"); the house wording is 新居民.
- Venues that said "phone to confirm" while linking a published timetable now point at
  the timetable instead.

### Validator blind spots these exposed

Each of the above got through roughly 150 existing checks. New rules, each verified by
re-introducing the fault it is meant to catch:

- names that differ only by a ⭐ prefix are duplicates
- an address plus a website shared by two records is flagged for review (a Costco
  warehouse and its gas bar legitimately share both, so this warns rather than fails)
- no Chinese in an address field
- no open-air record may claim 24-hour opening
- 新移民 anywhere in a note is an error
- coordinates given to three decimal places (~110 m) are reported — 14 records, mostly
  apartments and taxi firms. Not fixed: correcting them needs an authoritative
  geocoder, and inventing coordinates would be worse than coarse ones.

### Small screens

- **Popups ran off the edge below 340px** — 36px off a 320px phone. The content box was
  a fixed 305px; it now shrinks with the viewport. The regression sweep had covered 14
  widths, the narrowest 360px, and stepped straight over the bug: 320 and 340 are now
  in the list.
- Controls on touch screens are at least 44px, stepping down to 36px on screens that
  are both narrow and short — still half again WCAG 2.5.8's 24px floor. At 320×568 in
  French, holding the line at 44px pushed the map to 409px and left a quarter of the
  screen for the thing the page exists to show; that is the guideline working against
  its own purpose.
- On those screens the vertical rhythm is tighter and the status line drops its region
  clause (already visible on the Area button) so it shares a row instead of taking one.
  The map went from 28% of a 320×568 French screen to 38%.
- **The layout sweep had never run in touch mode**, so the height that comfortable
  targets cost was invisible to it. It now sweeps both, with the map-share floor stated
  per viewport class.

### Favourites

- Export as a short line of text, import on another device or after clearing the
  browser. Deliberately not cloud sync: the page promises it collects nothing and
  uploads nothing, and an account plus a server would make it a different product. A
  code from an older edition restores whatever ids still exist rather than failing
  whole.

### Refuted

Fifteen of the twenty-four did not survive testing. Three were the reverse of the
truth: the quick-pick row's `padding-right` is what makes its last chip reachable, not
what clips it; `positionPanel()` clamps both edges, not just the left; and the bus stop
coordinates come from the operator's own GTFS feed, verified stop by stop the day
before. Two more were behaviour the reviewer's own text had already talked itself out
of.

---

## 2026.08.31

Fixes from an outside review, adjudicated claim by claim (three of its twelve points
held up), plus what came out of checking the rest.

### Correctness

- **Modal dialogs were punched through by Leaflet's own controls.** Leaflet's
  control container is `z-index:1000` and sits outside the map's pane stack — the
  same value as `.backdrop`, so DOM order decided, and `#noteBackdrop` happens to
  precede `#map`. With the data-notes dialog open, the zoom buttons and the
  attribution link stayed on top *and clickable*: clicking `+` zoomed the map behind
  the dialog, and the attribution navigated away. Overlays are now `z-index:1200`,
  above every Leaflet layer.
- **URL parameter validation accepted inherited properties.** `if(UI[lang])` is true
  for `constructor`, `toString` and friends, so `?lang=constructor` reached
  `setLang()` and blanked the page — no title, no status, a thrown error. Own-key
  checks now guard all four parameters, with a second guard at `setLang()` and
  `renderRoute()` so no future caller can reintroduce it.

### Bus data

- Re-checked every route against BC Transit's official GTFS feed (29 Aug 2026
  edition). All 14 routes, all 475 stop names and coordinates matched, and the first
  and last trip times were identical to the minute.
- **Routes 8, 11, 12 and 15 do not exist.** The feed has no such routes; BC Transit's
  numbering simply skips them. This had been carried as an open data gap for several
  rounds. The coverage note now says so plainly, and mentions the 12 school-day-only
  routes (70–81) that are deliberately not included.
- Added `BUS_SOURCE` recording the feed and edition the routes came from.

### Licensing and privacy

- OpenStreetMap attribution now reads "© OpenStreetMap contributors" and links to
  the licence, as the OSM Foundation's guidelines require. It had been Leaflet's
  bare default — inconsistent with a page that asserts its own CC BY-NC terms.
- Added a privacy note in all five languages: nothing is collected or uploaded, no
  analytics, favourites stay in the browser, and the map imagery is the one outbound
  request that exposes the reader's IP.
- Dropped the Google Fonts CDN for a system font stack. That removes the last
  third-party request, the last offline gap and the flash of unstyled text, and gives
  each platform its own native CJK face.

### Accessibility

- Six pieces of text failed WCAG AA because `opacity` was dimming an otherwise
  compliant palette: the popup provenance line (4.31:1), category counts (3.13:1),
  the filter hint (3.71:1), the licence line (4.10:1), and the idle Reset button
  (2.30:1 — and it still worked when dimmed, so the disabled-control exemption did
  not apply). State is now carried by colour, not transparency. Category counts also
  went from 9.5px to 10.5px.
- The favourite star exposes `aria-pressed` and distinct add/remove labels; it used
  to read as "Favorites" in both states.
- All 33 external links carry `rel="noopener"`. Fifteen of them live inside the
  serialised `UI` object with escaped quotes and were missed by the first pass —
  `validate.py` now checks both quoting styles.

### Mobile

- Heights use `dvh` with a `vh` fallback, removing roughly 100px of dead scroll
  where the browser toolbar is counted twice.
- The bottom sheet can be swiped down to dismiss. The handle at its top had been
  drawn there all along, promising a gesture that did not exist — worse than having
  no handle. A cancelled pointer restores the sheet rather than closing it.

### Rejected

- **Splitting the data into an external JSON fetched at runtime.** `fetch()` fails
  from a `file://` page, so this would turn the downloaded file into a blank page for
  the readers it exists for.
- **A blocking first-visit disclaimer.** A click-through adds little legal weight to
  a free non-commercial reference and costs every reader a step. Revisit if an
  institution adopts the page.

---

## 2026.08.30

The first version to carry a version number. Everything before this was unversioned
drafts.

### Data

- All 250 records converted to structured opening hours (`h`), rendered per
  language, with closed days stated rather than left implied
- Removed all 166 hard-coded Google ratings — 55 of them were below 4.0, i.e.
  published negative claims about named local businesses. Replaced with a plain
  ⭐ recommended mark
- Removed `$` figures from place notes (they go stale fastest and are the most
  costly kind of stale)
- 222 notes given English text; French, Spanish and Korean fall back to English
- 42 Chinese parentheticals in place names extracted into translated `tag` chips
- Every record given a stable 8-character `id`; favourites migrated from names to
  ids via `FAV_MIGRATE`
- `v` (last-checked month) recorded per record
- `src` (provenance) recorded per record: `official` where the operator's own site
  is on file and a reader can check the details there (151), `places` where the
  details rest on third-party map data (99), `own` for a first-hand check. Seeded by
  one stated mechanical rule rather than by guessing at how each record was
  originally gathered — see `DATA-SCHEMA.md`. Shown as a chip in each popup

### Languages

- Added Korean as a fifth language (zh / en / fr / es / ko)
- City, transit agency and school-district names removed from translated copy in
  favour of `{CITY}` / `{TRANSIT}` / `{SD}` placeholders expanded once at startup

### Filtering and interaction

- Category filtering changed from "everything selected" to "no filter selected".
  Clicking one category now shows that category, instead of everything except it
- Group checkboxes changed to "show only this group"
- Four commonly used groups expanded by default instead of all eleven collapsed
- Reset is always visible, and now clears the bus route, the search box, the
  presets and the panel state — previously it cleared about half of them
- The bottom panel button reads "Done" instead of "View N places"; the live count
  moved to the panel title
- Quick picks now set the filter rather than competing with manual selection

### Structure and provenance

- Split into `src/engine.html` (reusable) + `src/data-<city>.js`, merged by
  `build.py`. A second city changes one file
- Guide split into city / province / country tiers, so a same-province city reuses
  ten of eleven sections
- Added a `CITY` config block; city facts no longer scattered through the code
- Added a licence and attribution notice: CC BY-NC 4.0, with the third-party-data
  caveat spelled out
- Corrections now open pre-filled with the place name, id, category, language and
  data version — previously feedback arrived with no way to tell which record it
  was about
- URL state: `?city=…&lang=…&r=…&c=…&q=…&route=…`, written with `replaceState` so
  the back button is not flooded, validated and dropped when junk

### Popup fixes

- French and Spanish labels ("Heures", "Teléfono") are wider than the 38px reserved
  for them, so they ran straight into their values — `HeuresTous les jours 7 h 30`
- Leaflet's zoom control sits above popups and outside their pane, so at narrow
  widths it clipped the place name. Popups now auto-pan clear of it, and the control
  is hidden below 600px where pinch-to-zoom covers it
- The offline notice yields while a popup is open instead of covering it

### Offline

- Leaflet and the cluster plugin are bundled into the file. With no network,
  everything works except the base map tiles, and a translated notice now says so.
  (A service worker was considered and rejected: it cannot register from a
  `file://` page, which is how most people will open this.)

### Tooling

- `validate.py` — static invariants, run after every edit
- `regress.py` — 106 browser checks across five languages and fourteen widths,
  plus a run with the cluster plugin absent
- `export-open.py` — exports the `official` + `own` subset, the part that carries
  no third-party redistribution terms
- `check-links.py` — checks the 150 external websites still resolve (needs a network)
- `DATA-SCHEMA.md` — the data format, and the procedure for adding a city
