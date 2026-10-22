#!/usr/bin/env python3
"""Phase 2 (2026-09-21) — the serious data fixes, checked in the built page."""
import asyncio, os, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--host-resolver-rules=MAP *.maptiler.com ~NOTFOUND, MAP *.arcgisonline.com ~NOTFOUND, MAP *.cartocdn.com ~NOTFOUND, MAP *.stadiamaps.com ~NOTFOUND, MAP *.openstreetmap.org ~NOTFOUND'])   # no map tiles from a test run: it spends the live site's tile quota (L-145)
        pg = await b.new_page(viewport={'width': 1280, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        g = lambda i, k: pg.evaluate("([i,k])=>{const p=P.find(x=>x.id===i);return p?(k?p[k]:true):null}", [i, k])
        for i in ('878135f5', 'a634fe38', '645ae374', '97daa003', '8606c30e'):
            check('%s is off the map and in quarantine' % i, await g(i, None) is None and await pg.evaluate("i=>QUARANTINE.some(q=>q.id===i&&q.quarantined)", i))
        check('no sameComplex points at a removed row', await pg.evaluate("()=>P.every(p=>(p.sameComplex||[]).every(id=>P.some(x=>x.id===id)))"))
        check('Pathways rings the shelter, not the weekday office', await g('b08eb3fe', 'p') == '250-299-7936')
        check('Overlanders no longer suggests floating', 'float' not in (await g('80e697e8', 'note'))['en'])
        # weekend hours: Aberdeen Mall open Saturday 11:00
        st = await pg.evaluate("()=>{const p=P.find(x=>x.id==='9db87af4');return [openState(p.h,{d:6,m:660}).open,openState(p.h,{d:7,m:700}).open]}")
        check('Aberdeen Mall is open at the weekend', st == [True, True], st)
        # 2026-09-22: TNRL's branch page now lists Saturday 10:00-4:00 (was 12:00-4:00)
        st = await pg.evaluate("()=>{const p=P.find(x=>x.id==='c597c849');return [openState(p.h,{d:6,m:590}).open,openState(p.h,{d:6,m:630}).open,openState(p.h,{d:6,m:970}).open,openState(p.h,{d:7,m:700}).open,openState(p.h,{d:7,m:730}).open]}")
        check('Aberdeen Tiny Library: Saturday 10-4, Sunday 12-4 (TNRL page)', st == [False, True, False, False, True], st)
        st = await pg.evaluate("()=>{const p=P.find(x=>x.id==='61154281');return openState(p.h,{d:5,m:600}).open}")
        check('Planet Fitness is open on Friday', st is True)
        st = await pg.evaluate("()=>{const p=P.find(x=>x.id==='ef8db6fb');return openState(p.h,{d:7,m:750}).open}")
        check('K-SPOON is closed on Sunday', st is False)
        for i, ph in (('42b06f2f', '250-372-7797'), ('88a72602', '250-314-0429'), ('e252ea96', '250-828-3600'), ('872c0058', '236-313-0824')):
            check('%s phone is %s' % (i, ph), await g(i, 'p') == ph)
        # 2026-09-22 (p14): numbers that no official source confirms are not shown
        for i in ('54085508', '046b81d1'):
            check('%s shows no unconfirmed phone' % i, await g(i, 'p') is None)
        check('Paul Lake and Cooney Bay no longer ring the City switchboard', await g('600d0f4c', 'p') is None and await g('5308dd0d', 'p') is None)
        check('Interior Savings is Beem, and still found by its old name', (await g('e3a1f254', 'n')).startswith('Beem') and 'Interior Savings' in (await g('e3a1f254', 'alias')))
        check('BC Wildlife Park is not tagged free', 'free' not in (await g('dd440908', 't')))
        tx = await pg.evaluate("()=>{const t=TASKS.find(x=>x.id==='tax');return [t.why.en,t.note.en]}")
        check('tax card: newcomers apply on arrival (RC66 / RC151)', 'as soon as they arrive' in tx[0] and 'RC66' in tx[1] and 'RC151' in tx[1], tx)
        hs = await pg.evaluate("()=>JSON.stringify(TASKS.find(x=>x.id==='hardship'))")
        check('hardship card: Pathways number and Salvation Army schedule fixed', '376-7558' not in hs and '250-299-7936' in hs and '12:30' not in hs)
        # popups still render for every place, in every language
        bad = await pg.evaluate("()=>{const out=[];for(const l of ['en','fr','es','zh','ko','ja']){setLang(l);for(const p of P){try{const h=popup(p,0);if(!h||/undefined|NaN/.test(h))out.push(l+':'+p.n);}catch(e){out.push(l+':'+p.n+':'+e);}}}setLang('en');return out.slice(0,5);}")
        check('every popup renders cleanly in six languages', not bad, bad)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n  %d pass, %d fail' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
