#!/usr/bin/env python3
"""The map must never be blank while the network is fine: the primary tile provider, then each fallback in turn.

2026-10-21: MapTiler suspended the account (monthly quota spent by test runs, L-145) and answered every tile with
403 and a picture reading "Invalid key". The page fell back to the one fallback it knew (keyless Esri, no longer
maintained). CITY.tiles.fallback is now a list — MapTiler → Stadia → Esri — and every step is tested here with
every provider simulated (page.route), so nothing reaches a real tile server and no quota is spent.

A refusal comes back as an *image* (403/401 with a PNG body): the tile loads and tileerror never fires, so only the
probe's status read can catch it. A network failure is the other kind: tileerror fires and the probe's fetch rejects.

    .venv/bin/python tests/engine/test_tile_fallback.py
"""
import asyncio, base64, os, subprocess, sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')
NO_TILES = ['--host-resolver-rules=MAP *.maptiler.com ~NOTFOUND, MAP *.arcgisonline.com ~NOTFOUND, MAP *.cartocdn.com ~NOTFOUND, MAP *.stadiamaps.com ~NOTFOUND, MAP *.openstreetmap.org ~NOTFOUND']   # no map tiles from a test run: it spends the live site's tile quota (L-145)

async def main():
    subprocess.run([sys.executable, os.path.join(ROOT, 'build.py'), '--city', '_fixture'], check=True, capture_output=True)
    page = os.path.join(ROOT, 'build', '_fixture.html')
    url = 'file://' + page + '?lang=en&tiles=chain'   # a local copy starts on the last provider; tiles=chain walks them all
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=NO_TILES)

        async def run(behave, *, vp=(1280, 900), offline=False, slow_primary=0, before_swap=None, at=None, local=False):
            """behave: per provider, primary first: 'ok' / 'deny' (403 or 401 with an image body) / 'abort' (network
            failure), or a dict {'img': how, 'fetch': how, 'img_delay': s, 'fetch_delay': s} to answer the map's tiles
            (<img>) and the probe (fetch) differently and late. Returns what the reader ends up with."""
            ctx = await b.new_context(viewport={'width': vp[0], 'height': vp[1]})
            pg = await ctx.new_page()
            errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            seen = {}
            chain = []
            async def handle(route):
                u = route.request.url
                for i, pre in enumerate(chain):
                    if u.startswith(pre):
                        seen[i] = seen.get(i, 0) + 1
                        bh = behave[i] if i < len(behave) else 'abort'
                        kind = 'fetch' if route.request.resource_type == 'fetch' else 'img'
                        how = bh[kind] if isinstance(bh, dict) else bh
                        delay = bh.get(kind + '_delay', 0) if isinstance(bh, dict) else 0
                        if i == 0 and slow_primary: delay = max(delay, slow_primary)
                        if delay: await asyncio.sleep(delay)
                        if how == 'abort': return await route.abort()
                        return await route.fulfill(status=200 if how == 'ok' else (403 if i == 0 else 401), body=PNG,
                                                   headers={'content-type': 'image/png', 'access-control-allow-origin': '*'})
                if at and u.split('?')[0] == at:   # the page itself, served as if from a live (non-local) address
                    return await route.fulfill(status=200, body=open(page, 'rb').read(), headers={'content-type': 'text/html; charset=utf-8'})
                await route.abort()   # anything else from the network (analytics…): never leaves the test
            # learn the provider chain from the page itself, so the test follows whatever the city configures.
            # A predicate, not a glob: 'http*://**' matched nothing from a file:// page (2026-10-22) and every
            # provider was silently "answered" by the browser's own host block instead of by this test.
            await pg.route(lambda u: u.startswith('http'), handle)
            if offline: await ctx.set_offline(True)
            await pg.goto(at + '?lang=en' if at else (url.replace('&tiles=chain', '') if local else url))
            chain[:] = await pg.evaluate("""()=>{const t=CITY.tiles||{};return [t.url].concat([].concat(t.fallback||[]).map(f=>f&&f.url))
              .filter(Boolean).map(u=>u.split('{')[0])}""")
            # the page started fetching before the chain was known: reload so every request is routed by provider
            await pg.reload()
            if before_swap: await before_swap(pg)
            await pg.wait_for_timeout(4500 + int(slow_primary * 1000))
            st = await pg.evaluate("""()=>({url:tiles._url, attr:(document.querySelector('.leaflet-control-attribution')||{}).innerText||'',
              newTab:[...document.querySelectorAll('.leaflet-control-attribution a')].every(a=>a.target==='_blank'),
              ev:_evBuf.filter(e=>/^tile_/.test(e.t)).map(e=>e.t+JSON.stringify(e.p)),
              offline:!!(document.getElementById('offlineNote')&&!document.getElementById('offlineNote').hidden),
              zoom:map.getZoom(), popup:!!(map._popup&&map.hasLayer(map._popup)), tileOk:_tileOk})""")
            n1 = sum(seen.values()); await pg.wait_for_timeout(2500); n2 = sum(seen.values())
            st.update(errs=errs, seen=dict(seen), chain=list(chain), settled=(n2 - n1) <= 2)
            await ctx.close()
            return st

        probe = await run(['ok'])
        chain = probe['chain']
        check('the city configures a primary and at least two fallbacks', len(chain) >= 3, chain)
        def on(st, i): return st['url'].startswith(chain[i])
        def served(st, upto):   # every provider up to the one in use was really asked (the simulation took effect), none after it
            return all(st['seen'].get(i, 0) > 0 for i in range(upto + 1)) and all(i <= upto for i in st['seen'])
        check('0 the simulated providers really answer the page (routing took effect)', probe['seen'].get(0, 0) > 0, probe['seen'])

        # 1. primary fine: stays, no fallback
        s = await run(['ok', 'ok', 'ok'])
        check('1 primary answers: the map stays on it and never falls back', on(s, 0) and not s['ev'] and served(s, 0) and s['tileOk'] > 0, (s['url'], s['ev'], s['seen'], s['tileOk']))
        # 2. primary refuses with an image (quota spent / key invalid): the probe hands over to the first fallback
        s = await run(['deny', 'ok', 'ok'])
        check('2 primary refuses (403 image): first fallback shows, its tiles load', on(s, 1) and served(s, 1) and s['tileOk'] > 0, (s['url'], s['ev'], s['seen'], s['tileOk']))
        check('2 …and the second fallback is not touched', 2 not in s['seen'], s['seen'])
        # 3. primary and first fallback both refuse: the second fallback shows
        s = await run(['deny', 'deny', 'ok'])
        check('3 primary and first fallback refuse: second fallback shows, its tiles load', on(s, 2) and served(s, 2) and s['tileOk'] > 0, (s['url'], s['ev'], s['seen'], s['tileOk']))
        # 4. primary unreachable (network failure): tileerror hands over
        s = await run(['abort', 'ok', 'ok'])
        check('4 primary unreachable: first fallback shows, its tiles load', on(s, 1) and served(s, 1) and s['tileOk'] > 0, (s['url'], s['ev'], s['seen'], s['tileOk']))
        # 5. primary refuses, first fallback unreachable: second fallback
        s = await run(['deny', 'abort', 'ok'])
        check('5 primary refuses, first fallback unreachable: second fallback shows, its tiles load', on(s, 2) and served(s, 2) and s['tileOk'] > 0, (s['url'], s['ev'], s['seen'], s['tileOk']))
        # 6. everything fails: no loop, no page error, the reader is told
        s = await run(['abort', 'abort', 'abort'])
        check('6 every provider fails: each tried once in order, the last one stays (no endless swapping)', on(s, len(chain) - 1) and s['settled'] and served(s, len(chain) - 1) and len(s['ev']) == len(chain) - 1, (s['url'], s['seen'], s['ev']))
        check('6 …the offline note tells the reader', s['offline'], s)
        check('6 …no page error', not s['errs'], s['errs'])
        # 7. the device really is offline: do not walk the chain, say so
        s = await run(['abort', 'abort', 'abort'], offline=True)
        check('7 device offline: no provider swap (the providers are not to blame)', on(s, 0) and not s['ev'], (s['url'], s['ev']))
        check('7 …the offline note shows', s['offline'], s)
        # 8. a card open while the swap happens stays open, at the same zoom
        async def open_card(pg):
            await pg.wait_for_timeout(600)
            await pg.evaluate("()=>focusMarker(M[0],15)"); await pg.wait_for_timeout(300)
        s = await run(['deny', 'ok', 'ok'], slow_primary=1.5, before_swap=open_card)
        check('8 a place card open during the swap stays open', s['popup'] and on(s, 1), s)
        check('8 …and the zoom does not change', s['zoom'] == 15, s['zoom'])
        # 10. guards each kept honest by a scenario that breaks without it (mutation-checked, 2026-10-22)
        # 10a stale probe: the primary's tiles fail at once (tileerror moves the map on), its probe answers 403 late —
        #     that late answer is about a provider no longer on the map and must not move it again
        s = await run([{'img': 'abort', 'fetch': 'deny', 'fetch_delay': 3.0}, 'ok', 'ok'])
        check('10a a late refusal from the provider already left behind does not skip the next one', on(s, 1) and s['tileOk'] > 0, (s['url'], s['ev'], s['seen']))
        # 10b clean slate: the primary loaded some tiles, then refused (quota ran out mid-load); the first fallback is
        #     unreachable — the counts carried over from the primary must not stop the move to the second
        s = await run([{'img': 'ok', 'fetch': 'deny', 'fetch_delay': 1.5}, 'abort', 'ok'])
        check('10b primary loaded then refused, first fallback unreachable: second fallback shows', on(s, 2) and s['tileOk'] > 0, (s['url'], s['ev'], s['seen'], s['tileOk']))
        # 10c stale errors: the primary's tiles fail slowly, after its probe already moved the map on; the first
        #     fallback answers slowly — the primary's late errors must not count against it
        s = await run([{'img': 'abort', 'img_delay': 2.0, 'fetch': 'deny'}, {'img': 'ok', 'img_delay': 2.5, 'fetch': 'ok'}, 'ok'])
        check('10c late errors from the provider left behind do not count against the next one', on(s, 1) and s['tileOk'] > 0, (s['url'], s['ev'], s['seen']))
        # 11. where the map starts (2026-10-22, Neil): a copy opened on this machine starts on the last provider and
        #     never asks the others (their quota is for readers); the live address starts on the primary
        s = await run(['ok', 'ok', 'ok'], local=True)
        check('11a a local copy starts on the last provider and never asks the others', on(s, len(chain) - 1) and set(s['seen']) <= {len(chain) - 1} and not s['ev'], (s['url'], s['seen'], s['ev']))
        # the switch survives the page's own address rewrite (a reload keeps it) and never travels in a share link
        ctx = await b.new_context(); pg = await ctx.new_page()
        await pg.route(lambda u: u.startswith('http'), lambda r: r.abort())
        await pg.goto(url); await pg.wait_for_timeout(1200)
        await pg.evaluate("()=>writeURLState()")
        kept = await pg.evaluate("()=>new URLSearchParams(location.search).get('tiles')")
        await pg.reload(); await pg.wait_for_timeout(1200)
        after = await pg.evaluate("()=>({chain:_TILE_CHAIN,share:shareHref()})")
        await ctx.close()
        check('11d ?tiles=chain survives the address rewrite and a reload', kept == 'chain' and after['chain'], (kept, after))
        check('11e …and is never part of a shared link', 'tiles=' not in after['share'], after['share'])
        s = await run(['ok', 'ok', 'ok'], at='https://guide.example.org/')
        check('11b the page at a live address starts on the primary', on(s, 0) and s['seen'].get(0, 0) > 0 and not s['ev'], (s['url'], s['seen'], s['ev']))
        s = await run(['deny', 'ok', 'ok'], at='https://guide.example.org/')
        check('11c …and at a live address a refusing primary still hands over to the first fallback', on(s, 1) and s['tileOk'] > 0, (s['url'], s['seen'], s['ev']))
        # 9. credits on phone and desktop: the provider and OpenStreetMap, links in a new tab
        for vp in ((390, 844), (1280, 900)):
            for beh, i in ((['ok', 'ok', 'ok'], 0), (['deny', 'ok', 'ok'], 1), (['deny', 'deny', 'ok'], 2)):
                s = await run(beh, vp=vp)
                check('9 %dpx, provider %d: credits name OpenStreetMap and open in a new tab' % (vp[0], i),
                      on(s, i) and 'OpenStreetMap' in s['attr'] and s['newTab'] and not s['errs'], (s['url'], s['attr'], s['errs']))
        await b.close()
    print('\n%d passed, %d failed' % (P, F))
    sys.exit(1 if F else 0)

asyncio.run(main())
