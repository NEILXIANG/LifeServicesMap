# Change log

The version shown in the app comes from `DATA_VERSION` in `src/engine.html`, and
the reader-facing list comes from `CHANGELOG` right below it. **This file and that
constant must be updated together** — the constant is what people actually see.

Format: `YYYY.MM.DD`, bumped whenever data or behaviour changes in a way a reader
would notice. Newest first.

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
