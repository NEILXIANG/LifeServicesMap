#!/usr/bin/env python3
"""Phase 4 (2026-09-21) — systemic cleanup, checked in the built page."""
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
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 1280, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("()=>({stars:P.filter(p=>/⭐/.test(p.n)).map(p=>p.n),picks:P.filter(p=>p.pick).length})")
        check('no ⭐ left in any name; picks kept as a field', not r['stars'] and r['picks'] >= 15, r)
        # 2026-09-24 (p27): the chip class is .pchip-pick now and it draws the icon
        # set's star instead of the ⭐ character, so the name block must carry no ⭐.
        tag = await pg.evaluate("()=>{const p=P.find(x=>x.id==='2c686174');const h=popup(p,0);"
                                "return /pchip-pick/.test(h)&&!/⭐/.test(h.split('pchip-pick')[0])}")
        check("an editor's pick still shows its tag", tag)
        sr = await pg.evaluate("()=>{searchInputEl.value='Kenna';runSearch();return lastVisible}")
        check('a former ⭐ place is still found by name', sr >= 1, sr)
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}")
        pk = await pg.evaluate("""()=>P.filter(p=>['park','dogpark','trail','beach'].includes(p.c)&&(p.p||'').startsWith('250-828-')&&p.id!=='7e4469ca').map(p=>[p.n,JSON.stringify(p.h)])""")
        check('City parks follow the bylaw: 05:00–23:00', all(h == '{"r":[[1,7,300,1380,0]]}' for n, h in pk), [x for x in pk if x[1] != '{"r":[[1,7,300,1380,0]]}'][:3])
        st = await pg.evaluate("()=>{const p=P.find(x=>x.id==='6bf24b9b');return [openState(p.h,{d:3,m:120}),openState(p.h,{d:3,m:600})]}")
        check('a park is closed at 2 am and open at 10 am', st[0]['open'] is False and st[1]['open'] is True, st)
        sp = await pg.evaluate("()=>['dd819a8a','8839dee9','61d1c228','35a610c9'].map(i=>openState(P.find(x=>x.id===i).h,{d:3,m:700}))")
        check('water parks never claim to be open once the season notice rules', all(x is None for x in sp), sp)
        ws = await pg.evaluate("()=>P.filter(p=>p.w&&!/^https:\\/\\/[a-z0-9.-]+\\.[a-z]{2,}(\\/|$)/i.test(p.w)).map(p=>p.n+' '+p.w)")
        check('every website is a well-formed https link', not ws, ws[:3])
        pq = await pg.evaluate("()=>P.filter(p=>p.pq&&!p.p).map(p=>p.n)")
        check('no phone qualifier without a phone', not pq, pq)
        bk = await pg.evaluate("()=>{const p=P.find(x=>x.id==='51c509c6');return [openState(p.h,{d:4,m:1050}).open,openState(p.h,{d:1,m:1050}).open]}")
        check('BMO Columbia is open Thursday at 5:30 pm, closed Monday then', bk == [True, False], bk)
        pb = await pg.evaluate("()=>P.find(x=>x.id==='f449c4d5').note.en")
        check('Pioneer Park Beach says swimming is not allowed', 'not allowed' in pb, pb)
        sc = await pg.evaluate("()=>P.every(p=>(p.sameComplex||[]).every(id=>{const o=P.find(x=>x.id===id);return o&&(o.sameComplex||[]).includes(p.id)}))")
        check('sameComplex is still symmetric', sc)
        bad = await pg.evaluate("()=>{const out=[];for(const l of ['en','fr','es','zh','ko','ja']){setLang(l);for(const p of P){const h=popup(p,0);if(/undefined|NaN/.test(h))out.push(l+':'+p.n);}}setLang('en');return out.slice(0,5);}")
        check('every popup renders cleanly in six languages', not bad, bad)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n  %d pass, %d fail' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
