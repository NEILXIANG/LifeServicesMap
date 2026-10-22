#!/usr/bin/env python3
"""2026-09-24 — the 15 elementary schools added from the province's K-12 dataset
(p21): every record complete, findable in six languages, and claiming nothing
that was not verified."""
import asyncio, os, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

NEW = ['Bert Edwards Science & Technology School', 'Dallas Elementary', 'Dufferin Elementary',
       'George Hilliard Elementary', 'Juniper Ridge Elementary', 'Kay Bingham Elementary',
       'McGowan Park Elementary', 'Pacific Way Elementary', 'Ralph Bell Elementary',
       'Rayleigh Elementary', 'RL Clemitson Elementary', 'Summit Elementary',
       'Westmount Elementary', 'Westsyde Elementary', 'École Collines-d’or']
# SD73 lists exactly these four StrongStart centres in Kamloops
STRONGSTART = {'A E Perry Elementary', 'Arthur Hatton Elementary', 'Marion Schilling Elementary', 'Beattie Elementary'}
LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja']

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--host-resolver-rules=MAP *.maptiler.com ~NOTFOUND, MAP *.arcgisonline.com ~NOTFOUND, MAP *.cartocdn.com ~NOTFOUND, MAP *.stadiamaps.com ~NOTFOUND, MAP *.openstreetmap.org ~NOTFOUND'])   # no map tiles from a test run: it spends the live site's tile quota (L-145)
        pg = await b.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)

        n = await pg.evaluate("()=>P.filter(p=>p.c==='elem').length")
        check('the city\'s 25 elementary schools are on the map', n == 25, n)
        missing = await pg.evaluate("names=>names.filter(x=>!P.some(p=>p.n===x))", NEW)
        check('all 15 new schools are present', not missing, missing)
        bad = await pg.evaluate("""()=>P.filter(p=>p.c==='elem').filter(p=>
            !p.a||!p.p||!p.w||!p.id||p.src!=='official'||!p.note||
            !['zh','en','fr','es','ko','ja'].every(l=>p.note[l]&&p.note[l].trim())).map(p=>p.n)""")
        check('every elementary record has address, phone, website, source and six-language notes', not bad, bad)
        oob = await pg.evaluate("()=>P.filter(p=>p.c==='elem'&&!(50.5<p.lat&&p.lat<50.9&&-120.7<p.lng&&p.lng<-120.0)).map(p=>p.n)")
        check('every coordinate is inside Kamloops', not oob, oob)
        dup = await pg.evaluate("()=>{const s={},d=[];P.forEach(p=>{const k=p.n.replace(/^⭐+ ?/,'');if(s[k])d.push(k);s[k]=1});return d}")
        check('no school was added twice', not dup, dup)
        phones = await pg.evaluate("()=>P.filter(p=>p.c==='elem').map(p=>p.p).filter(x=>!/^(250|778)-\\d{3}-\\d{4}$/.test(x))")
        check('every phone number is a local number in the usual shape', not phones, phones)
        sites = await pg.evaluate("()=>P.filter(p=>p.c==='elem').map(p=>p.w).filter(w=>!/^https:\\/\\/(www\\.sd73\\.bc\\.ca|best\\.sd73\\.bc\\.ca|collinesdor\\.csf\\.bc\\.ca)\\//.test(w))")
        check('every website points at the school district or the school itself', not sites, sites)

        # nothing unverified is claimed
        ss = await pg.evaluate("()=>P.filter(p=>p.c==='elem'&&/StrongStart/i.test(JSON.stringify(p.note||{})+(p.alias||[]).join(' '))).map(p=>p.n)")
        check('only the four SD73 StrongStart schools mention StrongStart', set(ss) == STRONGSTART, ss)
        hrs = await pg.evaluate("names=>P.filter(p=>names.includes(p.n)&&p.h).map(p=>p.n)", NEW)
        check('the new schools do not invent opening hours (they show "hours unknown")', not hrs, hrs)
        csf = await pg.evaluate("()=>P.find(p=>/Collines/.test(p.n))")
        check('the francophone school says it is not part of SD73, in every language',
              all('93' in csf['note'][l] for l in LANGS), {l: csf['note'][l][:40] for l in LANGS})

        # findable
        async def n_for(l, q):
            return await pg.evaluate("([l,q])=>{setLang(l);searchInputEl.value=q;runSearch();return {n:lastVisible,cats:[...new Set(M.filter(m=>m.score>0).map(m=>m.data.c))]}}", [l, q])
        for l, q in (('en', 'elementary'), ('en', 'kindergarten'), ('zh', '小学'), ('ko', '초등학교'), ('ja', '小学校'), ('fr', 'école primaire'), ('es', 'escuela primaria')):
            r = await n_for(l, q)
            check('%s "%s" finds all 25 elementary schools' % (l, q), r['n'] >= 25, r)
        for q in ('Pacific Way', 'Rayleigh', 'Collines', 'Barnhartvale', 'BEST'):
            r = await n_for('en', q)
            check('searching "%s" finds its school' % q, r['n'] >= 1, r)
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}")

        # the map still behaves
        await pg.wait_for_function("()=>!M.some(m=>m._want!==undefined)", timeout=4000)   # p31: queued changes land after an animation
        check('every school marker is on the map with no filter', await pg.evaluate("()=>M.filter(m=>m.data.c==='elem'&&markerHome().hasLayer(m)).length===25"))
        r = await pg.evaluate("()=>{aC=new Set(['elem']);renderCats();apply();const v=lastVisible;aC=new Set();renderCats();apply();return v}")
        check('the Elementary filter shows exactly those 25', r == 25, r)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
