#!/usr/bin/env python3
"""2026-09-22 — search dead ends (suggestions 1, 4, 5 from the analytics review):
closest matches when nothing matches every word, the task card leading the
empty state, and the health answer box. Also the hasLayer(undefined) guard."""
import asyncio, os, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

STATE = """()=>{const h=document.getElementById('searchHelp'),e=document.getElementById('emptyState');
  const eShown=!!e&&!e.hidden&&getComputedStyle(e).display!=='none'&&e.innerText.trim()!=='';
  return {exact:_exactN,closest:_closest,n:lastVisible,help:h.hidden?null:h.dataset.kind,helpTxt:h.hidden?'':h.innerText,
    empty:eShown,emptyFirst:eShown&&e.firstElementChild?e.firstElementChild.className:'',
    firstEmptyBtn:(document.querySelector('#emptyState .empty-btn')||{}).textContent||'',
    status:document.getElementById('statusText').textContent,
    shown:M.filter(m=>m.score>0).map(m=>({c:m.data.c,g:m.data.g,n:m.data.n}))}}"""

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        async def search(q, lang='en'):
            await pg.evaluate("([l,q])=>{setLang(l);searchInputEl.value=q;runSearch();}", [lang, q])
            return await pg.evaluate(STATE)

        # ---- 1. closest matches
        r = await search('cheap pharmacy near me')
        check('"cheap pharmacy near me": no exact match, closest shown', r['exact'] == 0 and r['closest'] and r['n'] >= 3, r)
        check('  …and every closest match is a pharmacy', r['shown'] and all(x['c'] == 'pharmacy' for x in r['shown']), r['shown'])
        check('  …the status line says "closest", not "results"', 'closest' in r['status'], r['status'])
        check('  …the note names the query and the count', 'cheap pharmacy near me' in r['helpTxt'] and str(r['n']) in r['helpTxt'], r['helpTxt'])
        check('  …and the empty state is not also shown', not r['empty'], r)
        r = await search('dog park open now')
        check('"dog park open now": strictest level wins — only dog parks', r['closest'] and r['shown'] and all(x['c'] == 'dogpark' for x in r['shown']), r['shown'])
        for q in ('xyzzy', 'dentistt', '604 555 1212 qqzz', 'xyzzy plugh'):
            r = await search(q)
            check('"%s" stays an honest empty result' % q, not r['closest'] and r['n'] == 0 and r['empty'] and r['help'] is None, r)
        r = await search('i want to kill myself')
        check('a crisis query never gets closest matches or the answer box', not r['closest'] and r['help'] is None and r['n'] == 0, r)
        check('  …and still shows the crisis lines', await pg.evaluate("()=>/911/.test(document.getElementById('emptyState').innerText)"))
        r = await search('pharmacy')
        check('an exact match is untouched (no closest, no note)', r['exact'] == r['n'] and r['n'] > 0 and not r['closest'] and r['help'] is None, r)
        # filters still apply
        g = await pg.evaluate("()=>{const g=P.find(p=>p.c==='pharmacy').g;aR=new Set([g]);return g}")
        r = await search('cheap pharmacy near me')
        check('closest matches respect the area filter', r['closest'] and all(x['g'] == g and x['c'] == 'pharmacy' for x in r['shown']), r['shown'])
        await pg.evaluate("()=>{aR=new Set(Object.keys(RI));}")
        # logging
        await pg.evaluate("()=>{_evBuf.length=0;}")
        await search('cheap pharmacy near me'); await pg.evaluate("()=>logSearch()")
        ev = await pg.evaluate("()=>JSON.parse(JSON.stringify(_evBuf.map(e=>({t:e.t,p:e.p}))))")
        run = [e for e in ev if e['t'] == 'search_run']; emp = [e for e in ev if e['t'] == 'search_empty']
        check('search_run records closest:true', run and run[-1]['p'].get('closest') is True, run)
        check('search_empty still fires on an exact zero, carrying the closest count', emp and emp[-1]['p'].get('closest', 0) >= 3, emp)
        await pg.evaluate("()=>{_evBuf.length=0;}")
        await search('pharmacy'); await pg.evaluate("()=>logSearch()")
        ev = await pg.evaluate("()=>JSON.parse(JSON.stringify(_evBuf.map(e=>({t:e.t,p:e.p}))))")
        check('an exact search logs no closest flag and no search_empty',
              any(e['t'] == 'search_run' and 'closest' not in e['p'] for e in ev) and not any(e['t'] == 'search_empty' for e in ev), ev)

        # ---- 4. task card leads the empty state
        r = await search('医疗卡', 'zh')
        check('"医疗卡": the task card is the first thing in the empty state', r['empty'] and r['emptyFirst'] == 'sh-card', r)
        check('  …and the first .empty-btn is still the recovery button', r['firstEmptyBtn'] == await pg.evaluate("()=>UI.zh.clearSearchBtn"), r['firstEmptyBtn'])
        await pg.evaluate("()=>{_evBuf.length=0;}")
        await pg.click('#emptyState .sh-card .sh-btn'); await pg.wait_for_timeout(500)
        st = await pg.evaluate("()=>({open:guideBackdropEl.classList.contains('open'),task:_taskOpen,ev:_evBuf.filter(e=>e.t==='guide_open'||e.t==='task_open').map(e=>e.t+':'+(e.p.src||'')+':'+(e.p.task||e.p.id||''))})")
        check('  …its button opens the MSP card and is logged as search_empty', st['open'] and st['task'] == 'msp' and any(x.startswith('guide_open:search_empty') for x in st['ev']), st)
        await pg.evaluate("()=>closeModal(guideBackdropEl)"); await pg.wait_for_timeout(300)
        r = await search('health card')
        check('"health card" (closest): the answer box carries the MSP card', r['help'] == 'closest' and await pg.evaluate("()=>!!document.querySelector('#searchHelp .sh-card')"), r)
        r = await search('xyzzy')
        check('no task card when no card fits', not await pg.evaluate("()=>!!document.querySelector('#emptyState .sh-card,#searchHelp .sh-card')"))

        # ---- 5. health answer box
        for lang, q in (('en', 'doctor'), ('en', 'walk in clinic'), ('fr', 'médecin'), ('es', 'médico'), ('zh', '看病'), ('ko', '병원'), ('ko', '아파요'), ('ja', '病院')):
            r = await search(q, lang)
            exp = await pg.evaluate("l=>{const u=UI[l],p=P.find(x=>x.id==='b29c9af7'),s=openState(p.h);return {t:u.hcTitle,h:fmtHours(p.h,l),st:s?(s.open?u.hcOpenNow:u.hcClosedNow):''}}", lang)
            links = await pg.evaluate("()=>[...document.querySelectorAll('#searchHelp a[href^=\"tel:\"]')].map(a=>a.getAttribute('href'))")
            ok = r['help'] == 'health' and exp['t'] in r['helpTxt'] and exp['h'] in r['helpTxt'] and exp['st'] in r['helpTxt'] and 'tel:811' in links and 'tel:911' in links
            check('%s "%s": health box with UPCC hours, live status, 8-1-1 and 911 links' % (lang, q), ok, (r['help'], links, r['helpTxt'][:160]))
        for lang, q in (('en', 'dentist'), ('en', 'dental clinic'), ('en', 'vet clinic'), ('en', 'legal clinic'), ('en', 'walking trail'),
                        ('ko', '아파트'), ('zh', '牙医'), ('en', 'pharmacy'), ('ja', '動物病院')):
            r = await search(q, lang)
            check('%s "%s": no health box' % (lang, q), r['help'] != 'health', r['help'])
        r = await search('아파요', 'ko')
        check('a health query with no place match does not also push the task card into the empty state',
              not await pg.evaluate("()=>!!document.querySelector('#emptyState .sh-card')"))
        await search('doctor')
        await pg.evaluate("()=>{_evBuf.length=0;}")
        await pg.click('#searchHelp .sh-btn.primary'); await pg.wait_for_timeout(1800)
        st = await pg.evaluate("()=>({ev:_evBuf.map(e=>e.t+':'+(e.p.kind||'')),popup:(document.querySelector('.leaflet-popup-content')||{}).innerText||''})")
        check('"Show it on the map" logs search_help_click and opens the UPCC popup', 'search_help_click:upcc' in st['ev'] and 'North Shore' in st['popup'], st)
        await pg.evaluate("()=>map.closePopup()")
        await pg.click('#searchHelp .sh-btn:not(.primary)'); await pg.wait_for_timeout(500)
        st = await pg.evaluate("()=>({open:guideBackdropEl.classList.contains('open'),task:_taskOpen})")
        check('the second button opens the "sick" card', st['open'] and st['task'] == 'sick', st)
        await pg.evaluate("()=>closeModal(guideBackdropEl)"); await pg.wait_for_timeout(300)
        r = await search('')
        check('clearing the search hides the box', r['help'] is None and await pg.evaluate("()=>document.getElementById('searchHelp').hidden"))

        # ---- visible on a phone
        ph = await b.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ph.on('pageerror', lambda e: errs.append('phone: ' + str(e)))
        await ph.goto(URL); await ph.wait_for_timeout(1500)
        await ph.evaluate("()=>{setLang('en');searchInputEl.value='walk in clinic';runSearch();}"); await ph.wait_for_timeout(600)
        bb = await ph.evaluate("()=>{const r=document.getElementById('searchHelp').getBoundingClientRect();return [r.top,r.bottom,r.left,r.right,innerWidth,innerHeight]}")
        check('phone: the health box is on screen and fits the width', bb[1] > bb[0] and bb[0] < bb[5] and bb[2] >= 0 and bb[3] <= bb[4], bb)
        await ph.screenshot(path='/tmp/a7/p17-phone.png')

        # ---- hasLayer guard
        check('map.hasLayer(undefined) is false, not a throw', await pg.evaluate("()=>{try{return map.hasLayer(undefined)===false&&map.hasLayer(null)===false}catch(e){return false}}"))
        check('map.hasLayer still sees real layers', await pg.evaluate("()=>{let t;map.eachLayer(l=>{t=t||l});return !!t&&map.hasLayer(t)===true}"))
        # rapid-fire searches used to throw from the cluster plugin mid-pan
        for q in ('아파요', '看病', '医疗卡', 'walk in clinic', 'health card', 'pharmacy', 'x'):
            await pg.evaluate("q=>{searchInputEl.value=q;runSearch();}", q)
        await pg.wait_for_timeout(1500)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
