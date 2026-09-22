#!/usr/bin/env python3
"""Phase 3 (2026-09-21) — holidays, appointment-only places, freshness label."""
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
        pg = await b.new_page(viewport={'width': 1280, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        hd = await pg.evaluate("()=>CITY.holidays")
        check('holiday list covers the next year, in order', hd == sorted(hd) and hd[-1] >= '2027-12-25' and '2026-09-30' in hd and '2026-10-12' in hd, hd[:3])
        check('today is not treated as a holiday unless listed', await pg.evaluate("()=>isHolidayToday()===CITY.holidays.includes(cityISODate())"))
        # an ordinary-day question still gets an ordinary answer
        st = await pg.evaluate("()=>{const p=P.find(x=>x.id==='9db87af4');return openState(p.h,{d:2,m:700}).open}")
        check('a clock passed in is answered as an ordinary day', st is True)
        # make today a holiday
        n0 = await pg.evaluate("()=>{openNow=true;updateOpenQuickpick();apply();return lastVisible;}")
        await pg.evaluate("()=>{CITY.holidays.push(cityISODate());_isoAt=Date.now();openNow=false;updateOpenQuickpick();apply();}")
        r = await pg.evaluate("""()=>{const x=P.filter(p=>p.h&&!p.h.a&&!p.h.q&&!p.h.k&&p.h.r);
            const unknown=x.every(p=>openState(p.h)===null);
            const a24=P.filter(p=>p.h&&p.h.a).every(p=>openState(p.h).open===true);
            const pop=popup(P.find(p=>p.id==='9db87af4'),0);
            openNow=true;updateOpenQuickpick();apply();
            const note=!!document.querySelector('#activeFilters .af-holiday');
            const vis=lastVisible, n24=P.filter(p=>p.h&&p.h.a).length;
            openNow=false;updateOpenQuickpick();apply();
            return {unknown,a24,pill:/pv-open hol/.test(pop),note,vis,n24};}""")
        check('on a holiday listed hours are not trusted', r['unknown'], r)
        check('24-hour places stay open on a holiday', r['a24'], r)
        check('the popup says the hours may differ', r['pill'], r)
        check('open now explains the holiday', r['note'], r)
        check('open now on a holiday shows only round-the-clock places', r['vis'] <= r['n24'], r)
        await pg.reload(); await pg.wait_for_timeout(1300)
        # appointment-only
        ap = await pg.evaluate("""()=>['78386973','7f3150f8','507845f0','b353ea62','dd6680fb'].map(i=>{const p=P.find(x=>x.id===i);
            return [openState(p.h,{d:2,m:700}),/appointment/.test(fmtHours(p.h,'en'))]})""")
        check('appointment-only places never claim to be open, and say why', all(a[0] is None and a[1] for a in ap), ap)
        # freshness
        fr = await pg.evaluate("""()=>{const pl=P.find(p=>p.src==='places'&&p.v),of=P.find(p=>p.src==='official'&&p.v);
            return [/Listed/.test(popup(pl,0))&&!/Verified/.test(popup(pl,0)),/Verified/.test(popup(of,0))]}""")
        check('map-data rows say Listed, checked rows say Verified', fr == [True, True], fr)
        bad = await pg.evaluate("()=>{const out=[];for(const l of ['en','fr','es','zh','ko','ja']){setLang(l);for(const p of P){const h=popup(p,0);if(/undefined|NaN/.test(h))out.push(l+':'+p.n);}}setLang('en');return out.slice(0,5);}")
        check('every popup renders cleanly in six languages', not bad, bad)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n  %d pass, %d fail' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
