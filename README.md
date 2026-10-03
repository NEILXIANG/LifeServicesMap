# Kamloops Living Services Map

A single HTML file. Open it in any browser — no server, no install, no account.
Everything except the map background works with no network at all.

## Files

| Path | What it is |
|---|---|
| `build/kamloops.html` | **The deliverable.** Built — do not hand-edit. `public/index.html` is a byte-identical copy that Cloudflare serves. |
| `app/engine/` | The reusable engine, split into `head.html`, `styles.css`, `body.html` and `js/*.js`; `parts.txt` gives the order. No city facts in it. |
| `src/data-kamloops.js` | Everything specific to Kamloops. |
| `build.py` | Merges the two (plus `vendor/` libraries) into one self-contained HTML file. |
| `vendor/` | Leaflet and MarkerCluster, inlined so the map works offline. |
| `scripts/check-all.sh` | Build + every check in one command. |
| `scripts/validate.py` | Static invariants. Run after every edit. |
| `tests/regress.py`, `tests/phase*test.py` | Browser checks. Need Playwright. |
| `scripts/export-open.py` | Writes out the freely-licensable subset of the data. |
| `scripts/check-links.py` | Checks the external websites still resolve (needs a network). |
| `scripts/monthly-quality-check.sh` | Stale POIs plus the link check. |
| `scripts/analytics/` | Export and analyse visit events from Cloudflare Analytics Engine. |
| `deploy.sh`, `worker.js`, `wrangler.toml` | Deployment (Cloudflare Workers). |
| `docs/guides/DATA-SCHEMA.md` | The data format, and how to add a city. |
| `docs/plans/` | Current plans, including the multi-city plan and its decision log. |
| `CHANGELOG.md` | What changed, and when. |
| `docs/archive/` | Point-in-time analyses and superseded handbooks. Not current state. |

Outreach material and finished PDFs live outside the repository, in
`../Guide to Life in Canada - ops/` (decision D4, 2026-10-03).

## Everyday use

```sh
python3 build.py                       # -> build/kamloops.html (+ public/index.html)
python3 scripts/validate.py            # ~150 static checks, a second
./scripts/check-all.sh --quick         # both of the above
./scripts/check-all.sh                 # plus every browser test
```

Edit `src/`, never the built HTML — a rebuild overwrites it.

## Running the browser tests

```sh
python3 -m venv .venv
.venv/bin/pip install playwright pypdf
.venv/bin/python -m playwright install chromium
./scripts/check-all.sh
```

## Deploying

```sh
npm install        # once: installs the pinned wrangler into node_modules/
./deploy.sh        # build -> validate -> deploy -> live probes
./deploy.sh --verify-only
```

## Which part of the data can you give away?

```sh
python3 scripts/export-open.py --csv
```

Writes `open-subset.json` (and `.csv`) containing only records whose `src` is
`official` or `own` — the ones with an authoritative source of record behind them.
The rest rest on third-party map data, whose redistribution follows that platform's
terms rather than your licence. See `docs/guides/DATA-SCHEMA.md` for what the values mean.

## A new city

See the last section of `docs/guides/DATA-SCHEMA.md`. In short: copy the data file, replace
its five objects, run `build.py`. The engine is shared, so an improvement made
here reaches every city at the next build.

## Licence

Content: CC BY-NC 4.0, attribution Neil Xiang. Facts drawn from Google Places and
official sites remain under their own terms.
