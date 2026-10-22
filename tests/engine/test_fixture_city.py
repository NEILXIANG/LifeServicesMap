#!/usr/bin/env python3
"""Engine smoke test on the fixture city (cities/_fixture, "Testville").

Builds build/_fixture.html and drives the page the way a reader would. Its job is
to catch the engine leaning on Kamloops: a second city must load cleanly, show its
own name, keep its data under its own storage prefix and never touch kamloops* keys.

    python3 tests/make-fixture-city.py     # only when the fixture should change
    .venv/bin/python tests/engine/test_fixture_city.py
"""
import asyncio, json, os, subprocess, sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import kamdata

P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

async def main():
    subprocess.run([sys.executable, os.path.join(ROOT, 'build.py'), '--city', '_fixture'],
                   check=True, capture_output=True)
    meta = kamdata.city_meta('_fixture')
    places = json.load(open(os.path.join(kamdata.city_dir('_fixture'), 'places.json'), encoding='utf-8'))
    url = 'file://' + os.path.join(ROOT, 'build', '_fixture.html')
    errors = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--host-resolver-rules=MAP *.maptiler.com ~NOTFOUND, MAP *.arcgisonline.com ~NOTFOUND, MAP *.cartocdn.com ~NOTFOUND, MAP *.stadiamaps.com ~NOTFOUND, MAP *.openstreetmap.org ~NOTFOUND'])   # no map tiles from a test run: it spends the live site's tile quota (L-145)
        pg = await b.new_page(viewport={'width': 1280, 'height': 900})
        pg.on('pageerror', lambda e: errors.append(str(e)))
        await pg.goto(url + '?lang=en'); await pg.wait_for_timeout(1500)

        check('the page title is the fixture city\'s', await pg.title() == meta['title'], await pg.title())
        st = await pg.evaluate("()=>({city:CITY.name.en, sp:SP, n:P.length, vis:lastVisible})")
        check('CITY and the storage prefix come from the fixture', st['city'] == 'Testville' and st['sp'] == meta['storagePrefix'], st)
        check('every fixture place is loaded and shown', st['n'] == len(places) and st['vis'] == len(places), (st, len(places)))

        # search for a fixture place by its first word
        word = places[0]['n'].split()[0].lower()
        n = await pg.evaluate("w=>{searchInputEl.value=w;runSearch();return lastVisible}", word)
        check('search finds a fixture place', n >= 1, (word, n))
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}")

        # favourites and the rest of local state live under the fixture's prefix only
        await pg.evaluate("id=>{favorites.add(id);saveFavorites();}", places[0]['id'])
        for lang in ('zh', 'ja', 'fr', 'en'):
            await pg.evaluate("l=>setLang(l)", lang); await pg.wait_for_timeout(150)
        keys = await pg.evaluate("()=>Object.keys(localStorage)")
        check('the favourite is stored under the fixture prefix',
              meta['storagePrefix'] + 'Favorites' in keys, keys)
        check('no kamloops* key is written by another city', not [k for k in keys if k.startswith('kamloops')], keys)
        check('every app key carries the fixture prefix', all(k.startswith(meta['storagePrefix']) for k in keys), keys)

        # the guide's city section fills {CITY} with the fixture's name
        await pg.evaluate("()=>openGuide('test')"); await pg.wait_for_timeout(400)
        g = await pg.evaluate("()=>document.getElementById('guideBody').innerText")
        check('the guide names the fixture city', 'Testville' in g and '{CITY}' not in g, g[:120])

        # a task card and the one bus route open without errors
        await pg.goto(url + '?lang=en&task=msp'); await pg.wait_for_timeout(1200)
        route = next(iter(json.load(open(os.path.join(kamdata.city_dir('_fixture'), 'bus-routes.json'), encoding='utf-8'))))
        await pg.evaluate("r=>{openPanel('bus');selectRoute(r);}", route); await pg.wait_for_timeout(400)

        # the app's own chrome never names Kamloops (place names and task text are city data)
        chrome = await pg.evaluate("()=>[document.title, document.querySelector('header')?.innerText||'', "
                                   "document.getElementById('metaDesc')?.content||'', "
                                   "document.querySelector('meta[property=\\'og:url\\']')?.content||''].join(' | ')")
        check('the header, title and meta never say Kamloops', 'kamloops' not in chrome.lower(), chrome[:200])
        check('no page errors', not errors, errors[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F))
    sys.exit(1 if F else 0)

asyncio.run(main())
