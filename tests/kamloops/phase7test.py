#!/usr/bin/env python3
"""Phase 7 (2026-09-21) — residents, and the Nation's own names."""
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
        g = await pg.evaluate("()=>Object.fromEntries(['zh','en','fr','es','ko','ja'].map(l=>[l,UI[l].guideCity]))")
        check('the resident section is in all six guides', all('🏡' in g[l] and 'ARCH' in g[l] and 'Snow Angels' in g[l] for l in g))
        check('Kamloopa Powwow is in June everywhere', 'Each June' in g['en'] and '6 月' in g['zh'] and not any('August the <b>Kamloopa' in v or '8 月在' in v for v in g.values()))
        check("the Nation's spelling Tk̓emlúps, no apostrophe form left in the guides", all("Tk'emlúps" not in v and 'Tk̓emlúps' in v for v in g.values()))
        check('two more 24-hour lines in the land section', all('1-866-925-4419' in v and '1-855-242-3310' in v for v in g.values()))
        check('no literal {CITY} or city name leaks into the rendered section', await pg.evaluate("()=>{setLang('en');return !/\\{CITY\\}/.test(UI.en.guideCity)}"))
        for q in ('Tkemlups', "Tk'emlúps", 'Tk̓emlúps'):
            r = await pg.evaluate("q=>P.filter(p=>matchScore(p,q.toLowerCase())>0).map(p=>p.id)", q)
            check('search %r finds the Nation’s office' % q, '718a712f' in r, r[:5])
        sub = await pg.evaluate("()=>document.getElementById('sub').textContent")
        check('the subtitle speaks to people who live here', 'lived here for years' in sub, sub)
        await pg.click('#helpBtn'); await pg.wait_for_timeout(300)
        tel = await pg.evaluate("()=>[...document.querySelectorAll('#helpBody a[href^=\"tel:\"]')].map(a=>a.getAttribute('href'))")
        check('help sheet carries the two Indigenous 24-hour lines', 'tel:18669254419' in tel and 'tel:18552423310' in tel, tel)
        await pg.keyboard.press('Escape')
        bad = await pg.evaluate("()=>{const out=[];for(const l of ['en','fr','es','zh','ko','ja']){setLang(l);openGuide('test');const h=document.getElementById('guideModal').innerHTML;if(/undefined|\\{CITY\\}|\\{PROV\\}/.test(h))out.push(l);closeModal(guideBackdropEl);}setLang('en');return out;}")
        check('the guide opens cleanly in six languages', not bad, bad)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n  %d pass, %d fail' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
