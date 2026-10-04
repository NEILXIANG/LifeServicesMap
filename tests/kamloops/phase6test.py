#!/usr/bin/env python3
"""Phase 6 (2026-09-21) — coverage additions."""
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
        async def search(q):
            return await pg.evaluate("q=>P.filter(p=>matchScore(p,q.toLowerCase())>0).map(p=>p.n)", q)
        for q, want in (('legal aid', 'Legal Aid BC (Kamloops)'), ('mental health', 'Kamloops Mental Health & Substance Use (Interior Health)'),
                        ('sexual assault', 'Kamloops Sexual Assault Counselling Centre'), ('gurdwara', 'Gurdwara Sahib Society'),
                        ('Indian', 'FraserCart Indian Store'), ('StrongStart', 'Beattie Elementary'), ('CDCP', 'Kamloops Dental Centre')):
            r = await search(q)
            check('search %r finds %s' % (q, want), want in r, r[:5])
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}")
        await pg.click('#helpBtn'); await pg.wait_for_timeout(400)
        tel = await pg.evaluate("()=>[...document.querySelectorAll('#helpBody a[href^=\"tel:\"]')].map(a=>a.getAttribute('href'))")
        check('help sheet: women’s shelter, Interior crisis line and CRCL', all(t in tel for t in ('tel:2503746162', 'tel:18883532273', 'tel:7784702725')), tel)
        await pg.keyboard.press('Escape')
        hs = await pg.evaluate("()=>TASKS.find(t=>t.id==='hardship').note")
        check('hardship card names the women’s shelter in six languages', all('250-374-6162' in hs[l] for l in ('en','fr','es','zh','ko','ja')))
        sc = await pg.evaluate("()=>P.every(p=>(p.sameComplex||[]).every(id=>{const o=P.find(x=>x.id===id);return o&&(o.sameComplex||[]).includes(p.id)}))")
        check('sameComplex stays symmetric', sc)
        bad = await pg.evaluate("()=>{const out=[];for(const l of ['en','fr','es','zh','ko','ja']){setLang(l);for(const p of P){const h=popup(p,0);if(/undefined|NaN/.test(h))out.push(l+':'+p.n);}}setLang('en');return out.slice(0,5);}")
        check('every popup renders cleanly in six languages', not bad, bad)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n  %d pass, %d fail' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
