#!/usr/bin/env python3
"""A place card must follow what the reader asked for: open when they ask for a place, gone once a new search
no longer includes that place, and never reopen after they closed it.

2026-10-04, newcomer tests of both cities: after "Show it on the map" a card opened on the map itself (not on
its marker — the marker was clustered) stayed open through every later search, and a card the reader had
closed came back on the next search. Both came from fallbacks meant for a clustered or filtered-off place
(55-markers-sidebar.js: standalone(); 60-search.js: the close at the end of apply()). Fixture city.

    .venv/bin/python tests/engine/test_popup_lifecycle.py
"""
import asyncio, os, subprocess, sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

async def main():
    subprocess.run([sys.executable, os.path.join(ROOT, 'build.py'), '--city', '_fixture'], check=True, capture_output=True)
    url = 'file://' + os.path.join(ROOT, 'build', '_fixture.html') + '?lang=en'
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--host-resolver-rules=MAP *.maptiler.com ~NOTFOUND, MAP *.arcgisonline.com ~NOTFOUND, MAP *.cartocdn.com ~NOTFOUND, MAP *.stadiamaps.com ~NOTFOUND, MAP *.openstreetmap.org ~NOTFOUND'])   # no map tiles from a test run: it spends the live site's tile quota (L-145)
        pg = await b.new_page(viewport={'width': 390, 'height': 844})
        await pg.route('**/*', lambda r: r.abort() if r.request.url.startswith('http') else r.continue_())
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(url); await pg.wait_for_timeout(1500)
        async def search(t):
            await pg.fill('#searchInput', t); await pg.wait_for_timeout(900)
        async def card():
            return await pg.evaluate("""()=>{const p=map._popup;if(!p||!map.hasLayer(p))return null;
              return p._kplace?p._kplace.id:(p._source&&p._source.data?p._source.data.id:'?')}""")
        # two places with distinct first words, so a search for one never includes the other
        # chosen by the search itself: neither one's word may find the other (anywhere — name, address, note)
        a, bb = await pg.evaluate("""()=>{const w=p=>p.n.split(/\\s+/)[0].toLowerCase();
          const ok=P.filter(p=>w(p).length>=4);
          for(const a of ok)for(const b of ok){if(a===b)continue;
            if(matchScore(b,w(a))===0&&matchScore(a,w(b))===0)return [{id:a.id,q:w(a)},{id:b.id,q:w(b)}];}
          return [null,null]}""")
        await search(a['q'])
        await pg.evaluate("id=>focusMarker(M.find(m=>m.data.id===id),16)", a['id']); await pg.wait_for_timeout(2500)
        check('the asked-for place opens', await card() == a['id'], await card())
        await search(bb['q']); await pg.wait_for_timeout(1500)
        check('a new search that excludes it closes its card', await card() != a['id'], await card())
        await search(a['q'])
        await pg.evaluate("id=>focusMarker(M.find(m=>m.data.id===id),16)", a['id']); await pg.wait_for_timeout(2500)
        await pg.evaluate("()=>map.closePopup()"); await pg.wait_for_timeout(300)
        await search(''); await search(bb['q']); await search(a['q']); await pg.wait_for_timeout(1500)
        check('a card the reader closed does not come back on later searches', await card() is None, await card())
        # a place outside the area filter asked for directly (a saved place) still opens and stays
        r = await pg.evaluate("""()=>{const gs=Object.keys(RI);const m=M.find(x=>x.gk!==gs[0]);aR=new Set([gs[0]]);apply();
          focusMarker(m,16);return m.data.id}""")
        await pg.wait_for_timeout(2500)
        check('a filtered-off place asked for directly still opens', await card() == r, await card())
        # that card sits on the map itself (no marker to close it): a search that excludes the place must close it
        q = await pg.evaluate("""id=>{const p=P.find(x=>x.id===id);const w=x=>x.n.split(/\\s+/)[0].toLowerCase();
          const o=P.find(x=>w(x).length>=4&&matchScore(p,w(x))===0);return w(o)}""", r)
        await search(q); await pg.wait_for_timeout(1200)
        check('a card opened on the map itself closes when a search excludes its place', await card() != r, await card())
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F))
    sys.exit(1 if F else 0)

asyncio.run(main())
