#!/usr/bin/env python3
"""The phone's Back gesture steps back one layer at a time and never leaves the site by surprise.

2026-10-05, newcomer test of Kelowna: after a task card's "Open it on the map", Back left the site — closing the
guide took its history entries with it. Now that action leaves one entry, and Back from the map returns to the
card, then the card list, then closes the guide (85-search-box-sheets.js: leaveTaskForMap). Fixture city.

    .venv/bin/python tests/engine/test_back_navigation.py
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
        st = "()=>({guide:guideBackdropEl.classList.contains('open'),task:_taskOpen,href:location.href})"
        tid = await pg.evaluate("()=>{const t=TASKS.find(t=>t.place&&P.find(p=>p.id===t.place));openGuide('test',t.id);return t.id}")
        await pg.wait_for_timeout(600)
        await pg.click('#guideTasks .task-map'); await pg.wait_for_timeout(2500)
        s = await pg.evaluate(st)
        check('"Open it on the map" closes the guide', not s['guide'], s)
        await pg.go_back(); await pg.wait_for_timeout(1200); s = await pg.evaluate(st)
        check('Back from the map returns to the same card', s['guide'] and s['task'] == tid and s['href'].startswith('file:'), s)
        await pg.go_back(); await pg.wait_for_timeout(1000); s = await pg.evaluate(st)
        check('Back again returns to the card list', s['guide'] and not s['task'], s)
        await pg.go_back(); await pg.wait_for_timeout(1000); s = await pg.evaluate(st)
        check('Back again closes the guide and stays on the page', not s['guide'] and s['href'].startswith('file:'), s)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F))
    sys.exit(1 if F else 0)

asyncio.run(main())
