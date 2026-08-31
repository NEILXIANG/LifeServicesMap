# Kamloops Living Services Map

A single HTML file. Open it in any browser — no server, no install, no account.
Everything except the map background works with no network at all.

## Files

| File | What it is |
|---|---|
| `kamloops.html` | **The deliverable.** Built — do not hand-edit. |
| `src/engine.html` | The reusable engine. No city facts in it. |
| `src/data-kamloops.js` | Everything specific to Kamloops. |
| `build.py` | Merges the two into `kamloops.html`. |
| `validate.py` | Static invariants. Run after every edit. |
| `regress.py` | 106 browser checks. Needs Playwright. |
| `export-open.py` | Writes out the freely-licensable subset of the data. |
| `check-links.py` | Checks the 150 external websites still resolve (needs a network). |
| `DATA-SCHEMA.md` | The data format, and how to add a city. |
| `CHANGELOG.md` | What changed, and when. |

## Everyday use

```sh
python3 build.py --out "Kamloops生活服务地图.html"   # rebuild from src/
python3 validate.py                                # ~150 static checks, a second
```

Edit `src/`, never the built HTML — a rebuild overwrites it.

`validate.py` and `regress.py` take the built file as an optional argument; with no
argument they use `kamloops.html`, or the only `.html` sitting beside them, so the
renamed copy in this folder works either way.

## Running the browser tests (optional)

`validate.py` needs nothing but Python. `regress.py` additionally needs a browser:

```sh
pip3 install playwright
python3 -m playwright install chromium
python3 regress.py
```

It regenerates its own fixtures from `kamloops.html`, so build first. It takes
about five minutes and prints one line per check.

## Which part of the data can you give away?

```sh
python3 export-open.py --csv
```

Writes `open-subset.json` (and `.csv`) containing only records whose `src` is
`official` or `own` — the ones with an authoritative source of record behind them.
The rest rest on third-party map data, whose redistribution follows that platform's
terms rather than your licence. See `DATA-SCHEMA.md` for what the values mean.

## A new city

See the last section of `DATA-SCHEMA.md`. In short: copy the data file, replace
its five objects, run `build.py`. The engine is shared, so an improvement made
here reaches every city at the next build.

## Licence

Content: CC BY-NC 4.0, attribution Neil Xiang. Facts drawn from Google Places and
official sites remain under their own terms.
