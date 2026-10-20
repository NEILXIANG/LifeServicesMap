#!/usr/bin/env python3
"""The guide must open offline after ONE visit.

2026-10-19, walkthrough of the live site: the page was stored for offline use only when a later visit went through
the service worker. The first visit is never controlled by it, so a reader who opened the guide once (from a flyer
QR code, say) and then had no signal got a browser error. sw.js now pre-caches the page at install.

Serves the built deploy directory of a city on localhost (a secure context, so the service worker runs), visits
it once, cuts the network and opens it again.

    .venv/bin/python tests/engine/test_offline_first_visit.py [--city kamloops]
"""
import asyncio, functools, http.server, os, socketserver, subprocess, sys, threading
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import kamdata
CITY = sys.argv[sys.argv.index('--city') + 1] if '--city' in sys.argv else 'kamloops'
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):                      # /api/event: answer like the Worker would, record nothing
        self.send_response(204); self.end_headers()

async def main():
    subprocess.run([sys.executable, os.path.join(ROOT, 'build.py'), '--city', CITY], check=True, capture_output=True)
    d = os.path.join(ROOT, kamdata.city_meta(CITY)['deploy']['assetsDir'])
    srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=d))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = 'http://localhost:%d/' % srv.server_address[1]
    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch(); ctx = await b.new_context(); pg = await ctx.new_page()
            await pg.goto(url + '?lang=en')
            await pg.wait_for_function("navigator.serviceWorker&&navigator.serviceWorker.controller!==null", timeout=15000)
            await pg.wait_for_timeout(1500)            # install's pre-cache settles
            cached = await pg.evaluate("caches.keys().then(ks=>Promise.all(ks.map(k=>caches.open(k).then(c=>c.keys())))).then(a=>a.flat().map(r=>new URL(r.url).pathname))")
            check('after one visit the page itself is in the offline cache', '/' in cached, cached)
            await ctx.set_offline(True)
            try:
                await pg.goto(url + '?lang=zh'); await pg.wait_for_timeout(1500)
                n = await pg.evaluate("typeof P!=='undefined'?P.length:0")
            except Exception as e:
                n = 'error: ' + str(e)[:80]
            check('offline, a different link to the guide still opens it with every place', isinstance(n, int) and n > 0, n)
            await b.close()
    finally:
        srv.shutdown()
    print('\n%d passed, %d failed' % (P, F))
    sys.exit(1 if F else 0)

asyncio.run(main())
