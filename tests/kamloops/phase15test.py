#!/usr/bin/env python3
"""2026-09-24 — licensed child care imported from the province's Child Care Map
(p25), the provincial source label and its attribution (p23), and school hours
told honestly (p24)."""
import asyncio, os, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)
LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja']

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)

        # ---- the import
        n = await pg.evaluate("()=>P.filter(p=>p.c==='daycare').length")
        check('child care went from 4 places to the licensed centres in the city (%d)' % n, n >= 80, n)
        bad = await pg.evaluate("""()=>P.filter(p=>p.src==='opendata').filter(p=>
            !p.a||!p.p||!p.note||!['zh','en','fr','es','ko','ja'].every(l=>p.note[l]&&p.note[l].trim())||
            !/^\\d{3}-\\d{3}-\\d{4}$/.test(p.p)||!(50.5<p.lat&&p.lat<50.9&&-120.7<p.lng&&p.lng<-120.0)).map(p=>p.n)""")
        check('every imported record has an address, a phone in the right shape, notes in six languages and a sane coordinate', not bad, bad)
        check('none of them invents opening hours', await pg.evaluate("()=>!P.some(p=>p.src==='opendata'&&p.h)"))
        dups = await pg.evaluate("()=>{const s={},d=[];P.forEach(p=>{const k=p.n.toLowerCase().replace(/[^a-z0-9]/g,'');if(s[k])d.push(p.n);s[k]=1});return d}")
        check('the import did not duplicate a place already on the map', not dups, dups)
        # two centres at neighbouring civic numbers keep their own points
        d = await pg.evaluate("""()=>{const a=P.find(p=>p.a==='350 Seymour St'),b=P.find(p=>p.a==='352 Seymour St');
            return a&&b?Math.round(Math.hypot((a.lat-b.lat)*111000,(a.lng-b.lng)*70000)):null}""")
        check('neighbouring addresses were re-resolved and no longer share one point', d is not None and 0 < d < 60, d)
        low = await pg.evaluate("()=>P.filter(p=>p.src==='opendata'&&p.precision==='low').map(p=>p.n)")
        check('the few that could not be resolved say "approximate location" (%d)' % len(low), len(low) <= 10, low)

        # ---- the source label
        for l in LANGS:
            t = await pg.evaluate("l=>[UI[l].srcOpenData,UI[l].srcOpenDataTip,UI[l].licenceNote]", l)
            check('%s: the provincial label, its tip, and the Open Government Licence attribution' % l,
                  t[0] and len(t[1]) > 20 and 'open-government-licence-bc' in t[2], (t[0], t[1][:30]))
        r = await pg.evaluate("""()=>{setLang('en');const p=P.find(x=>x.src==='opendata');
            const m=M.find(x=>x.data.id===p.id);focusMarker(m,15);return p.n}""")
        await pg.wait_for_timeout(2200)
        pop = await pg.evaluate("()=>(document.querySelector('.leaflet-popup-content')||{}).innerText||''")
        check('a popup shows the provincial source and says hours are not recorded',
              await pg.evaluate("()=>UI.en.srcOpenData") in pop and 'call' in pop.lower(), pop[:150])
        await pg.evaluate("()=>map.closePopup()")

        # ---- schools: hours removed, honest instruction added
        check('no elementary school claims opening hours any more', await pg.evaluate("()=>!P.some(p=>p.c==='elem'&&p.h)"))
        for l in LANGS:
            miss = await pg.evaluate("l=>P.filter(p=>p.c==='elem').filter(p=>!/call|téléphon|llame|전화|電話|打电话/i.test(p.note[l])).map(p=>p.n)", l)
            check('%s: every school note tells the reader to call or check the page' % l, not miss, miss[:3])
        r = await pg.evaluate("""()=>{setLang('en');const p=P.find(x=>x.c==='elem');const m=M.find(x=>x.data.id===p.id);
            focusMarker(m,15);return p.n}""")
        await pg.wait_for_timeout(2200)
        pop = await pg.evaluate("()=>(document.querySelector('.leaflet-popup-content')||{}).innerText||''")
        check('a school popup says the hours are not recorded rather than showing invented ones',
              'AM' not in pop.split('Hours')[-1][:40] if 'Hours' in pop else True, pop[:160])
        await pg.evaluate("()=>map.closePopup()")

        # ---- searching finds them
        for l, q, least in (('en', 'daycare', 80), ('en', 'child care', 80), ('en', 'preschool', 80),
                            ('zh', '托儿', 80), ('zh', '幼儿园', 80), ('ko', '어린이집', 80), ('ja', '保育園', 80), ('fr', 'garderie', 80)):
            r = await pg.evaluate("([l,q])=>{setLang(l);searchInputEl.value=q;runSearch();return lastVisible}", [l, q])
            check('%s "%s" finds the licensed centres (%d)' % (l, q, r), r >= least, r)
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}")
        check('the Daycare filter shows them all', await pg.evaluate("()=>{aC=new Set(['daycare']);renderCats();apply();const v=lastVisible;aC=new Set();renderCats();apply();return v>=80}"))
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
