#!/usr/bin/env python3
"""A tab left open for hours offers a reload once the page on the server has changed — and only then.

2026-10-16, visit log: a phone kept a tab of 2026.09.24 open for three weeks (mobile browsers resume a tab
without reloading), showing three-week-old phone numbers and hours long after 2026.09.24b went live.
85-search-box-sheets.js now asks the server (HEAD) when such a tab comes back to the front. Served over a local
HTTP server (Last-Modified changes when the file does); the page clock is fast-forwarded. Fixture city.

    .venv/bin/python tests/engine/test_update_offer.py
"""
import asyncio, functools, http.server, os, shutil, subprocess, sys, tempfile, threading, time
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

async def main():
    subprocess.run([sys.executable, os.path.join(ROOT, 'build.py'), '--city', '_fixture'], check=True, capture_output=True)
    d = tempfile.mkdtemp()
    page_file = os.path.join(d, 'index.html')
    shutil.copy(os.path.join(ROOT, 'build', '_fixture.html'), page_file)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=d))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = 'http://127.0.0.1:%d/?lang=en' % srv.server_address[1]
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--host-resolver-rules=MAP *.maptiler.com ~NOTFOUND, MAP *.arcgisonline.com ~NOTFOUND, MAP *.cartocdn.com ~NOTFOUND, MAP *.stadiamaps.com ~NOTFOUND, MAP *.openstreetmap.org ~NOTFOUND'])   # no map tiles from a test run: it spends the live site's tile quota (L-145)
        for changed in (False, True):
            pg = await b.new_page()
            await pg.route('**/*', lambda r: r.abort() if not r.request.url.startswith('http://127.0.0.1') else r.continue_())
            await pg.clock.install()
            await pg.goto(url); await pg.wait_for_timeout(800)
            await pg.clock.run_for(16000); await pg.wait_for_timeout(800)     # the first HEAD, 15 s after load
            stamp = await pg.evaluate("()=>_pageStamp")
            if changed:
                time.sleep(1.1)                                              # Last-Modified has 1 s resolution
                with open(page_file, 'a', encoding='utf-8') as f: f.write('\n<!-- new edition -->\n')
            await pg.clock.run_for(7 * 3600 * 1000)                          # the tab sits for seven hours
            await pg.evaluate("()=>document.dispatchEvent(new Event('visibilitychange'))")
            await pg.wait_for_timeout(1200)
            toast = await pg.evaluate("()=>{const t=document.getElementById('toast');return t&&!t.hidden?t.innerText:''}")
            want = await pg.evaluate("()=>UI.en.updateAvail")
            if changed:
                check('the page records the server stamp shortly after load', bool(stamp), stamp)
                check('after hours open, a changed page on the server offers a reload', want in toast, toast)
            else:
                check('an unchanged page offers nothing', want not in toast, toast)
            await pg.close()
        await b.close()
    srv.shutdown(); shutil.rmtree(d, ignore_errors=True)
    print('\n%d passed, %d failed' % (P, F))
    sys.exit(1 if F else 0)

asyncio.run(main())
