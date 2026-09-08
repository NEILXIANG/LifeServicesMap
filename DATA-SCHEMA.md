# Data schema

Everything city-specific lives in one file: `src/data-<city>.js`. The engine
(`src/engine.html`) contains no facts about any particular city. To build a new
city you copy that one data file, replace its contents, and run `build.py`.

Run `python3 validate.py` after every edit. It checks most of what follows
mechanically, so a mistake here is usually caught before it reaches anyone.

---

## The five things in a data file

| Object | What it is |
|---|---|
| `CITY` | Config: name, map centre, contact, transit agency, school district |
| `RI` | Neighbourhood/region names, 6 languages |
| `P` | The places — the bulk of the work |
| `BR` | Bus routes: stops, geometry, service window |
| `FAV_MIGRATE` | One-time map from old place names to ids. New cities: `{}` |
| `UI.<lang>.guideCity` | The "About this city" section of the resident guide |
| `LANDMARKS` | *Optional.* Place ids shown as permanent map labels on the opening view. See below. |

Categories (`CI`), their colours and icons (`CO`/`CD`/`IC`), the groups (`GRP`/`GN`),
the themes (`TI`/`TIC`/`TORDER`), the quick-pick presets (`PRESETS`) and the rest of
the guide live in the **engine**
and are shared by every city. Change them only if the taxonomy itself should change
everywhere.

---

## `CITY`

```js
const CITY={
  key:'kamloops',                    // must match the ?city= URL parameter
  name:{zh:'…',en:'…',fr:'…',es:'…',ko:'…',ja:'…'},
  prov:{zh:'BC省',en:'BC',…},        // province/state, as it reads in each language
  country:'CA',
  centre:[50.684,-120.35], zoom:12,  // opening view
  bounds:[[50.5,-120.7],[50.9,-120.0]],   // validate.py rejects places outside this
  navSuffix:', Kamloops, BC',        // appended when handing an address to a maps app
  transit:{name:'BC Transit', url:'…'},
  schoolDistrict:{name:'SD73', url:'…'},
  contact:'…@…',                     // where feedback and corrections go
  keyStop:/exch|station|terminal/i,  // stop names whose labels are always shown
  openAir:['park','trail','beach','dogpark','splash']  // "hours posted on site"
};
```

Translated copy must never contain the city name, the transit agency or the school
district literally. Write `{CITY}`, `{PROV}`, `{TRANSIT}`, `{TRANSIT_URL}`, `{SD}`,
`{SD_URL}`, `{CONTACT}`, `{DATE}`, `{LIC}`, `{LIC_URL}` instead — `tpl()` expands
them once at startup, and `validate.py` fails the build if a literal slips back in.

---

## `P` — places

One object per place. Only six fields are required.

### Required

| Field | Type | Notes |
|---|---|---|
| `n` | string | Official name. Avoid parentheticals in a language most readers can't read — use `tag` instead. Must be unique. |
| `a` | string | Street address. If there is no civic number, navigation falls back to the coordinates. |
| `lat` `lng` | number | Must fall inside `CITY.bounds`. |
| `c` | string | Category key — must exist in `CI`. |
| `g` | string | Region key — must exist in `RI`. |
| `id` | string | Stable 8-char id. **Never change it**: favourites are stored against it. |

### Optional

| Field | Type | Notes |
|---|---|---|
| `p` | string | Phone. Digits in `NNN-NNN-NNNN` form become a tap-to-call link. No email here. |
| `pq` | key | Qualifier for the phone, e.g. `pCity`, `pNational`. Defined in the engine. |
| `e` | string | Email, if the place publishes one. |
| `w` | string | Website, `https://…`. |
| `h` | object | Opening hours — see below. Omit when genuinely unknown, **and always omit for open-air places**: the engine then renders "hours posted on site", which is true without anyone having to know the bylaw. |
| `note` | `{zh,en,fr,es,ko,ja}` | Your own description. **`zh` and `en` are required.** `fr`/`es`/`ko`/`ja` are optional but all-or-nothing: a note with French and no Korean is rejected, because one language silently showing another's text while its neighbours are translated is worse than a clean fallback. |
| `tag` | key | Short qualifier shown as a chip, e.g. `tKorean`, `t24h`. Defined in the engine. |
| `t` | array | **Themes** — the overlapping second axis. See below. Order must follow `TORDER`. |
| `precision` | `'low'` | The coordinate is approximate (roughly ±100 m): interpolated, or published only to three decimals. The popup says so, so the pin never claims a confidence it doesn't have. The address is unaffected, and navigation uses the address. |
| `sameComplex` | array of ids | Other records at the same address or in the same building. Must be **symmetric** — every id you list must list you back. The popup names them, so two markers on one coordinate read as "the postal counter is inside that pharmacy" rather than as duplicate data. |
| `v` | `YYYY-MM` | When this record was last checked. |

### `src` — provenance (required in practice)

Where this record's **factual** fields come from. It does not describe the note —
the note is always the compiler's own writing.

| Value | Means | Validator requires |
|---|---|---|
| `official` | The operator's or governing body's own website is on file, so a reader can check the details at the source | a `w` field |
| `places` | No authoritative source on file; the details rest on third-party map data | — |
| `own` | Checked in person or by phone by the compiler | — |
| `stub-pending-verify` | The details come from an official or first-party page but nobody has yet stood at the door or dialled the number | — |

The Kamloops set was seeded by one mechanical rule — **has `w` → `official`, else
`places`** — because there is no honest way to reconstruct, after the fact, which of
250 records was cross-checked on an official site. So `official` is defined by
something a reader can verify (there is a source of record, and here is the link)
rather than by an unfalsifiable claim about how the data was gathered. Promote a
record to `own` when you actually check it, and add a `w` when you find one.

Two things depend on this field:

- the small source chip in each popup, so credibility is visible per record instead
  of only in a blanket disclaimer
- `export-open.py`, which writes out the `official` + `own` subset — the part you
  can hand to a library or another city without inheriting a third party's terms

### `t` — themes, the overlapping axis

A place has exactly **one** category — it decides the pin's colour and icon, so it
cannot be a list — and **any number** of themes. That single-valued category is what
made the map hard to browse for anything but an errand: a library is filed under
`library`, yet it is also a free afternoon with a toddler, a warm room in February,
somewhere to study and a cultural venue. Themes say that out loud without touching
the category system or the map's colour language.

The ten theme keys, their labels, icons and reading order (`TI`, `TIC`, `TORDER`)
live in the **engine**, not here: they are city-agnostic, and another city reuses
them unchanged while only its records' `t` arrays differ.

```js
{ n:'…', c:'library', …, t:['family','culture','free','multi','student','indoor'] }
```

Rules `validate.py` enforces: every key exists in `TI`; no duplicates within a
record; the array is in `TORDER` order; every theme has at least one place (a chip
that can only ever show `(0)` is a wasted tap); and it warns when a theme has five
or fewer, or when more than 40% of records carry no theme at all.

Assignment is scripted rather than hand-entered, in `tools/themes.py`: a table
from category to themes, plus a small table of per-record additions. Every
per-record addition carries a comment naming the evidence **in that record's own
verified note** — a view, a waterfall, a landmark, a heritage site. `scenic` and
`history` are never inferred from a category alone, because "it is a park" is not
evidence that it has a view. Re-run the script after adding places; it is
idempotent.

Filtering is **AND**: ticking two themes means both. That is the only reading under
which adding a chip can never grow the result set, which is the same promise the
area and category filters make, and the useful queries are conjunctions — "free
AND indoor" on a wet Tuesday.

### `h` — opening hours

Structured, not prose, so all six languages render from one source and closed
days can be stated rather than implied.

```js
h:{ a:true }                                  // open 24 hours — a gas station or a
                                              // hospital, never a park
h:{ r:[[1,5,510,1230,0]] }                    // Mon–Fri 08:30–20:30
h:{ r:[[1,5,420,990,0]], q:'qOffice' }        // …with a qualifier
h:{ s:[[7,600]] }                             // a service at Sunday 10:00
h:{ k:'hCall' }                               // a keyed message: "call to confirm"
h:{ r:[[1,7,600,1260,1]], se:'winter' }       // seasonal, approximate closing
```

`r` entries are `[dayFrom, dayTo, openMinute, closeMinute, approx]`, days `1`=Monday
to `7`=Sunday, minutes from midnight. `approx:1` renders as "about". A close time
past midnight is written as `>1440`. Days not covered by any range are rendered as
explicitly closed.

Keys for `k` and `q` (`hCall`, `hCallDay`, `hSite`, `qOffice`, …) are defined in the
engine so they translate; add new ones there, in all six languages.

---

## `BR` — bus routes

```js
"1":{ n:'Tranquille', co:'#e8710a',
      f:'05:56', l:'26:09',          // first and last trip; >24h means after midnight
      s:[['Stop name',lat,lng], …],  // stops in order
      p:[[lat,lng], …] }             // polyline geometry
```

Derived from the local transit agency's GTFS feed. If a route is omitted, say so in
`busCoverage` rather than leaving a silent gap in the numbering.

---

## `LANDMARKS` — persistent map labels (optional)

Someone who has never seen the city has no anchor point when the opening view shows
only cluster-count bubbles — the map reads as an abstract grid of numbers rather
than a place. `LANDMARKS` fixes that by naming a handful of well-known places right
on the map, always on, before anyone has clicked anything.

```js
const LANDMARKS=["f4c1c1d7","251dd9d0","a41504d6","2b34314d","72b24279","752036cd"];
```

An array of existing `P` ids — nothing else to configure. Each one renders as a
small permanent text label (no separate pin; the place's own marker is unaffected)
using the same anti-overlap placement algorithm as bus-stop labels, so a landmark
label never collides with a stop label, another landmark label, or a visible
cluster bubble. Labels hide themselves at zoom levels or pan positions where they'd
crowd the view, exactly like stop labels already do.

Guidance for choosing ids: 4-8 places, genuinely famous locally (a university, a
major mall, a landmark park, the downtown core) — not evenly distributed for its
own sake, and not a marketing exercise. `validate.py` only checks that every id
resolves to a real, distinct place; the judgement of *which* places belong is
yours. Omit the constant entirely for a city that isn't ready for this yet — the
engine checks `typeof LANDMARKS!=='undefined'` and simply skips the feature.

---

## Rules the validator enforces

- Required fields present; category and region keys resolve; coordinates inside `CITY.bounds`
- Place names unique; ids unique and present
- `note` is `{zh,en}`, both non-empty, and the English contains no Chinese
- Hours objects are renderable; day ranges and times are sane
- Every `tag`/`pq`/`k`/`q` key is defined in all six languages
- All six languages have identical key sets, in the UI object and in the post-assignments
- Every record has a valid `src`, and `official` is backed by a `w`
- `note` translations are all-or-nothing, and none is a copy of the English
- No two names differ only by a ⭐ prefix; no address contains Chinese
- No open-air record claims 24-hour opening; no note says 新移民
- No hard-coded ratings, no `$` figures in notes, no email inside `p`
- No literal city/agency name in translated copy
- The engine contains no city data, and still has its `/*__CITY_DATA__*/` marker
- Every id in `LANDMARKS` (if defined) resolves to a real place, with no duplicates

## Rules it can't check — your judgement

- Whether a fact is **true**, and whether it is **still** true
- Whether a place is worth including at all — 250 chosen from thousands is the
  actual product
- Whether a note says something a reader can't get from Google
- Whether a category with one entry earns its place in the taxonomy

---

## Two categories that keep getting confused

`gov` and `commctr` have caught out two separate reviewers, so:

- **`gov`** — an office you go to in order to deal with a government or a
  government-funded programme: Service Canada, Service BC, ICBC, and settlement
  agencies delivering federally funded programmes.
- **`commctr`** — a place the community gathers, run by the city or by a cultural
  association: recreation centres, cultural centres, halls.

If it is somewhere you go to *complete a formality*, it is `gov`. If it is somewhere
you go to *spend time*, it is `commctr`.

`apt` and `propmgmt` divide the same way: `apt` is a building you could live in,
`propmgmt` is a company you phone. Do not put a management office in `apt` — it
inflates the count a person uses to judge how much choice they have.

## Adding a city

1. `cp src/data-kamloops.js src/data-<city>.js`
2. Replace `CITY`, `RI`, `P`, `BR`; set `FAV_MIGRATE={}`; rewrite the six
   `UI.<lang>.guideCity` blocks
3. If it is in another province, also update the `guideProv` tier **in the engine**
   — or move it into the data file if you are supporting several provinces
4. `python3 build.py --city <city>`
5. `python3 validate.py` and `python3 regress.py`
