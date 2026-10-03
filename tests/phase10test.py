#!/usr/bin/env python3
"""2026-09-22 — follow-ups from the 5-day analytics review: version bump,
walk-in-clinic search, maintainer-device flag."""
import asyncio, os, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.abspath(__file__))
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx = await b.new_context()
        pg = await ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        # 2026-10-03: compare with the version in the engine source instead of a literal,
        # so every legitimate version bump no longer breaks this check.
        import re as _re
        sys.path.insert(0, os.path.dirname(_r)); import kamdata
        _ver = _re.search(r"DATA_VERSION='([^']+)'", kamdata.engine_text()).group(1)
        check('DATA_VERSION matches the engine source (%s) and rides on every event' % _ver, await pg.evaluate("v=>DATA_VERSION===v&&_evBuf.every(e=>e.v===DATA_VERSION)", _ver))
        for l, q in (('en', 'walk in clinic'), ('en', 'Walk-in clinic'), ('fr', 'clinique sans rendez-vous'), ('es', 'clínica sin cita'),
                     ('zh', '免预约诊所'), ('ko', '워크인 클리닉'), ('ja', 'ウォークインクリニック')):
            r = await pg.evaluate("([l,q])=>{setLang(l);searchInputEl.value=q;runSearch();return {n:lastVisible,hits:P.filter(p=>matchScore(p,q.toLowerCase())>0).map(p=>p.n)}}", [l, q])
            check('%s "%s" finds the North Shore walk-in centre' % (l, q), r['n'] >= 1 and 'North Shore Urgent Care (UPCC)' in r['hits'], r)
        r = await pg.evaluate("()=>{setLang('en');return P.filter(p=>matchScore(p,'walk-in clinic')>0).map(p=>p.n)}")
        check('the appointment-only South Shore centre is not offered as a walk-in clinic', 'South Shore Urgent Care (UPCLC)' not in r, r)
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}")
        # maintainer flag
        check('an ordinary visit is not tagged', await pg.evaluate("()=>{trackEvent('probe_a',{});return !_IS_OWNER&&!('env' in _evBuf.slice(-1)[0].p)}"))
        p2 = await ctx.new_page(); await p2.goto(URL + '?maintainer=1'); await p2.wait_for_timeout(1200)
        r = await p2.evaluate("()=>{trackEvent('probe_b',{x:1});return {own:_IS_OWNER,p:_evBuf.slice(-1)[0].p,url:location.search}}")
        check('?maintainer=1 marks the browser and tags events env:dev', r['own'] and r['p'].get('env') == 'dev' and r['p'].get('x') == 1, r)
        check('the maintainer parameter does not stay in the address bar', 'maintainer' not in r['url'], r['url'])
        p3 = await ctx.new_page(); await p3.goto(URL); await p3.wait_for_timeout(1200)
        check('the mark persists on the next plain visit', await p3.evaluate("()=>{trackEvent('probe_c',{});return _IS_OWNER&&_evBuf.slice(-1)[0].p.env==='dev'}"))
        check('the debug panel does not appear for a marked device', await p3.evaluate("()=>!document.getElementById('debugPanel')&&!document.querySelector('.debug-panel')"))
        await p3.evaluate("()=>{renderHelpSheet();}")
        kept = await p3.evaluate("()=>{Object.keys(localStorage).filter(k=>/^kamloops/.test(k)).forEach(k=>localStorage.removeItem(k));return localStorage.getItem('lifemapMaintainer')}")
        check("the Help sheet's clear-this-device sweep (kamloops* keys) leaves the mark alone", kept == '1', kept)
        p4 = await ctx.new_page(); await p4.goto(URL + '?maintainer=0'); await p4.wait_for_timeout(1200)
        check('?maintainer=0 removes the mark', await p4.evaluate("()=>{trackEvent('probe_d',{});return !_IS_OWNER&&localStorage.getItem('lifemapMaintainer')===null&&!('env' in _evBuf.slice(-1)[0].p)}"))
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
