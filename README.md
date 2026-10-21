# Life Guide — one engine, many cities

A multilingual (zh / en / fr / es / ko / ja) guide and map for people who have just moved to a city: what to do,
where to go, what to bring — step by step. Each city is a single self-contained HTML file: no server, no install,
no account, and everything except the map background works offline.

| City | Status | Address |
|---|---|---|
| Kamloops, BC | live since September 2026 (`2026.10.20b`, deployed 2026-10-20) | <https://kamloops-lifemap.neilxiang.workers.dev/> |
| Kelowna, BC | draft — not deployable until its review checklist is clear | — |

**Documentation starts at [`docs/README.md`](docs/README.md)**; everything about adding cities (lessons, tools,
prompts) starts at [`docs/knowledge/README.md`](docs/knowledge/README.md). Working rules for Claude are in `CLAUDE.md`.

## Repository layout

Nine kinds of things, each in one place (reorganised 2026-10-04):

| Kind | Path | What it is |
|---|---|---|
| **Engine** | `app/engine/` | The shared engine: `head.html`, `styles.css`, `body.html`, `js/*.js`, `tail.html`, joined in the order of `parts.txt`. **No city facts.** |
| | `app/pwa/` | Service worker, manifest and icon templates, rendered per city into its deploy folder. |
| | `vendor/` | Leaflet and MarkerCluster, inlined so the map works offline. |
| **Data** | `cities/<id>/` | Everything about one city: `city.json` (build/deploy/review settings), `data.js` (hand-written settings and texts), `places.json` and the other data files, `guide/<lang>.html`, `PROFILE.md`, and `import/` (importer settings, provenance, desk checks, translations, opening hours, raw research). `cities/_fixture/` is the generated test city — do not edit. |
| | `provinces/bc/` | What every BC city shares: holidays, hotlines, seasonal notices (`province.json`, checked by `validate.py`) and the BC geocoder cache. |
| | `schemas/` | Place record schema; category tiers shared by the review and import scripts. |
| **Build** | `build.py`, `kamdata.py` | `build.py` merges engine + city + vendor into `build/<city>.html`; `kamdata.py` is the one place scripts read and write data through (plus shared helpers). |
| **Tools** | `scripts/` | Checks, importers, review tools, monthly maintenance, analytics — indexed in [`scripts/README.md`](scripts/README.md). |
| **Tests** | `tests/` | Engine tests, the Kamloops regression and baseline, each city's GUI test — see [`tests/README.md`](tests/README.md). |
| **Deploy** | `deploy.sh`, `worker.js`, `wrangler.toml`, `package.json` | One Cloudflare Worker per city. |
| | `public/` | Kamloops' deploy folder (committed; its URL never changes). Other cities deploy from `deploy/<id>/` (built, not committed). |
| **Records** | `records/` | Operational records of the live city: visits, data quality, feedback, business hypotheses — see [`records/README.md`](records/README.md). (Called `data/` until 2026-10-04, which read like page data.) |
| **Outreach** | `outreach/` | Sources and builders for printed and PDF material: `pdf/` (text, screenshots, `builddocs.py`), `flyers/`, `logo.svg`. Finished files are not kept here (below). |
| **Docs** | `docs/` | Methodology, handbooks, knowledge base, plans, reports, archive — start at [`docs/README.md`](docs/README.md). |

Generated and local-only (ignored by git): `build/`, `deploy/`, `records/exports/`, `outreach/pdf/_build/`, `node_modules/`, `.venv/`.

Outreach material and finished PDFs live outside the repository, in `../Guide to Life in Canada - ops/` (decision D4).

## Everyday use

```sh
python3 build.py                          # Kamloops -> build/kamloops.html (+ public/index.html)
python3 build.py --city kelowna           # any city -> build/<city>.html
python3 scripts/validate.py --city <id>   # ~140 static checks, a second
./scripts/check-all.sh --quick            # build + validate every city + consistency + knowledge base
./scripts/check-all.sh                    # plus every browser test (~25 min)
```

Edit `app/` and `cities/`, never the built HTML — a rebuild overwrites it. When page content changes, bump
`DATA_VERSION` in `app/engine/js/20-versions-templates-tasks.js` (`deploy.sh` refuses otherwise).

First-time setup for the browser tests and deployment:

```sh
python3 -m venv .venv
.venv/bin/pip install playwright pypdf
.venv/bin/python -m playwright install chromium
npm install        # the pinned wrangler, for deploy.sh
```

## Deploying

```sh
./deploy.sh                               # Kamloops: build -> validate -> deploy -> live probes
./deploy.sh --city <id> --dry-run         # show a city's deploy settings without deploying
./deploy.sh --verify-only                 # live probes only
```

A city whose `city.json` says `"status": "draft"` cannot be deployed. Kamloops' address never changes and never redirects
(decision D1). Deploying, pushing and publishing need Neil's approval.

## Adding a city

Follow [`docs/guides/新城市操作手册.md`](docs/guides/新城市操作手册.md) (step-by-step commands) and the standards in
[`docs/guides/新城市扩展方法论与标准.md`](docs/guides/新城市扩展方法论与标准.md). In short: profile the city first, run
`scripts/new-city.py`, import government open data, research official websites, have every non-government record
desk-checked by a second reader, translate, run the review checklist, phone-verify the safety-critical places, then remove
`draft`. Lessons from Kamloops and Kelowna, with what enforces each, are in [`docs/knowledge/`](docs/knowledge/README.md).

## Which part of the data can you give away?

```sh
python3 scripts/export-open.py --city <id> --csv
```

Writes the records whose facts rest on an authoritative source of record (`src` `official` or `own`), with your notes.
Records from third-party map data (`places`, Kamloops only) follow that platform's terms. Government open data
(`opendata`) is not in this export yet; it may be shared under its own licence with the attribution listed in each
city's `licenceData`. See [`docs/guides/DATA-SCHEMA.md`](docs/guides/DATA-SCHEMA.md) for what the values mean.

## Licence

Content: CC BY-NC 4.0, attribution Neil Xiang. Facts from official websites, government open data (Open Government
Licence – British Columbia and city licences, BC Transit open data terms) and, in Kamloops, third-party map data remain
under their own terms; each city's page lists its open-data licences.
