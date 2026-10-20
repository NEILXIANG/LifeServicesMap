#!/usr/bin/env python3
"""2026-09-22 — three new cards and the seasonal reminder."""
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
        pg = await b.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("""()=>['doctor','housing','jobloss'].map(id=>{const t=TASKS.find(x=>x.id===id);return t?{id,steps:t.steps.length,icon:!!EMOJI_ICON[t.icon],
            six:['en','fr','es','zh','ko','ja'].every(l=>t.q[l]&&t.t[l]&&t.why[l]&&t.steps.every(s=>s[l])&&(!t.note||t.note[l])&&(!t.help||t.help[l])),
            place:!!P.find(p=>p.id===t.place),src:/^https:\\/\\//.test(t.src)}:null})""")
        check('three new cards, complete in six languages, with an icon, a place and a source', all(x and x['six'] and x['icon'] and x['place'] and x['src'] for x in r), r)
        bad = await pg.evaluate("()=>{const out=[];for(const l of ['en','fr','es','zh','ko','ja']){setLang(l);for(const id of ['doctor','housing','jobloss']){try{openTask(id,'list');const h=document.getElementById('guideTasks').innerHTML;if(/undefined|NaN/.test(h))out.push(l+':'+id);}catch(e){out.push(l+':'+id+':'+e)}}}closeModal(guideBackdropEl);setLang('en');return out;}")
        check('each new card opens cleanly in six languages', not bad, bad)
        for q, want in (('family doctor', 'doctor'), ('家庭医生', 'doctor'), ('rental scam', 'housing'), ('失业', 'jobloss'), ('EI', 'jobloss')):
            hit = await pg.evaluate("q=>TASKS.filter(t=>taskMatchesLoose(t,q)).map(t=>t.id)", q)
            check('a search for %r reaches the %s card' % (q, want), want in hit, hit)
        # seasons: pretend the date
        async def season_at(md):
            return await pg.evaluate("md=>{_iso='2026-'+md;_isoAt=Date.now()+1e9;const x=activeSeason();return x?x.id:null}", md)
        cases = {'09-22': 'wildfire', '07-01': 'wildfire', '09-30': 'wildfire', '10-01': 'winter', '01-15': 'winter', '04-30': 'winter', '05-01': None, '06-30': None}
        got = {k: await season_at(k) for k in cases}
        check('the right season on the right day (including across the new year)', got == cases, got)
        key = await pg.evaluate("()=>{_iso='2027-02-10';_isoAt=Date.now()+1e9;return seasonKey(activeSeason())}")
        check('a winter that wraps the new year keeps the year it started in', key == 'kamloopsSeason_winter_2026', key)
        await pg.evaluate("()=>{_iso='2026-09-22';_isoAt=Date.now()+1e9;localStorage.setItem('kamloopsFirstUseSeen','1');const fu=document.getElementById('firstUse');fu.hidden=true;renderSeason();}")
        st = await pg.evaluate("()=>{const el=document.getElementById('seasonNote');return {vis:!el.hidden,links:[...el.querySelectorAll('a')].map(a=>a.href),txt:el.textContent}}")
        check('in season, with the first-use card gone, the note shows with its links', st['vis'] and len(st['links']) == 3 and all(u.startswith('https://') for u in st['links']), st)
        hid = await pg.evaluate("()=>{const fu=document.getElementById('firstUse');fu.hidden=false;renderSeason();const a=document.getElementById('seasonNote').hidden;fu.hidden=true;renderSeason();return a}")
        check('never stacked on top of the first-use card', hid is True)
        await pg.evaluate("()=>{focusMarker(M[3],16);}"); await pg.wait_for_timeout(700)
        hp = await pg.evaluate("()=>({pop:!!document.querySelector('.leaflet-popup'),hid:document.getElementById('seasonNote').hidden})")
        check('steps aside while a place card is open', hp['pop'] and hp['hid'], hp)
        await pg.evaluate("()=>map.closePopup()"); await pg.wait_for_timeout(300)
        check('comes back when the place card closes', await pg.evaluate("()=>!document.getElementById('seasonNote').hidden"))
        await pg.evaluate("()=>{selectRoute(Object.keys(BR)[0]);}"); await pg.wait_for_timeout(300)
        check('steps aside while a bus route is drawn', await pg.evaluate("()=>document.getElementById('seasonNote').hidden"))
        await pg.evaluate("()=>{selectRoute(null);}"); await pg.wait_for_timeout(300)
        await pg.evaluate("()=>document.getElementById('seasonClose').click()")
        cl = await pg.evaluate("()=>({hid:document.getElementById('seasonNote').hidden,k:localStorage.getItem('kamloopsSeason_wildfire_2026'),ev:_evBuf.some(e=>e.t==='season_close')})")
        check('closing it hides it, remembers it for this season, and is counted', cl['hid'] and cl['k'] == '1' and cl['ev'], cl)
        await pg.reload(); await pg.wait_for_timeout(1300)
        check('stays closed after a reload', await pg.evaluate("()=>{_iso='2026-09-22';_isoAt=Date.now()+1e9;renderSeason();return document.getElementById('seasonNote').hidden}"))
        nx = await pg.evaluate("()=>{_iso='2026-10-02';_isoAt=Date.now()+1e9;renderSeason();return !document.getElementById('seasonNote').hidden&&/winter|hiver|DriveBC/i.test(document.getElementById('seasonNote').textContent)}")
        check('the next season shows even though the last one was closed', nx)
        lang = await pg.evaluate("()=>{setLang('zh');return document.getElementById('seasonNote').textContent}")
        check('follows a language change', '冬' in lang, lang[:40])
        g = await pg.evaluate("()=>['en','fr','es','zh','ko','ja'].map(l=>UI[l].guideCity+' '+document.body.innerHTML).join('').includes('October 1 to March 31')")
        tire = await pg.evaluate("()=>{setLang('en');openGuide('test');const h=document.getElementById('guideModal').innerText;closeModal(guideBackdropEl);return /October 1 to April 30/.test(h)}")
        check('the long guide now gives October 1 to April 30 for winter tires', tire)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n  %d pass, %d fail' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
