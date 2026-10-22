#!/usr/bin/env python3
"""2026-09-22 — link fixes (p9) and the new tracking events (p10)."""
import asyncio, os, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

# click without leaving the page: the tracking listener runs in the capture phase,
# the page's own preventDefault stops the navigation / mail client
CLICK = "a=>{a.addEventListener('click',e=>e.preventDefault(),{once:true});a.click();}"
NEW = "['task_src','task_link','guide_link','feedback_click','season_shown']"

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--host-resolver-rules=MAP *.maptiler.com ~NOTFOUND, MAP *.arcgisonline.com ~NOTFOUND, MAP *.cartocdn.com ~NOTFOUND, MAP *.stadiamaps.com ~NOTFOUND, MAP *.openstreetmap.org ~NOTFOUND'])   # no map tiles from a test run: it spends the live site's tile quota (L-145)
        pg = await b.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        ev = lambda t: pg.evaluate("t=>_evBuf.filter(e=>e.t===t).map(e=>e.p)", t)

        # ---- p9: dead links are gone, replacements are in place
        dead = await pg.evaluate("""()=>{const all=JSON.stringify(P)+JSON.stringify(TASKS)+document.documentElement.innerHTML+
              ['en','fr','es','zh','ko','ja'].map(l=>UI[l].guideCity||'').join('');
            return ['kamloopssalvationarmy.ca/community-services','msp/bc-residents/enrolment"','icbc.com/driver-licensing/new-to-bc',
              'matiere-impots.html','staytunedauto.ca','"w":"https://www.chevron.ca"','"w":"https://www.td.com"',
              'programs-services/mini-storage-units','windsorplywood.ca/'].filter(s=>all.includes(s))}""")
        check('none of the dead or wrong links is left anywhere', not dead, dead)
        w = await pg.evaluate("""()=>{const by=n=>(P.find(p=>p.n===n)||{}).w;return {
            sa:by('The Salvation Army Community Services'),cg:(P.find(p=>/Canada Games Aquatic/.test(p.n))||{}).w,
            td:P.filter(p=>/^TD /.test(p.n)).map(p=>p.w),post:P.filter(p=>p.c==='post').map(p=>p.w),
            chev:P.filter(p=>/^Chevron/.test(p.n)&&p.w).map(p=>p.w),costco:by('Costco Wholesale')}}""")
        check('Salvation Army points at its food bank page', w['sa'] == 'https://kamloopssalvationarmy.ca/programs/emergency-food-bank', w['sa'])
        check('Canada Games Aquatic Centre points at the pool facilities page', (w['cg'] or '').endswith('/aquatics/pool-facilities'), w['cg'])
        check('every TD branch points at the Canadian branch locator', w['td'] and all('/ca/en/' in u for u in w['td']), w['td'])
        # 2026-10-04: '>= 7', not '== 7' — the London Drugs counter gained a link when it was confirmed (no hard-coded counts, L-046)
        check('every post office with a website points at Find a post office', len([u for u in w['post'] if u]) >= 7 and all(u.endswith('find-a-post-office.page') for u in w['post'] if u), w['post'])
        check('Chevron entries point at the Chevron BC station finder', len(w['chev']) == 2 and all('journie.ca/chevron/bc-en' in u for u in w['chev']), w['chev'])
        check('Costco warehouse points at the Kamloops warehouse page', w['costco'] == 'https://www.costco.ca/w/-/bc/kamloops/161', w['costco'])
        for l in ('en', 'fr', 'es', 'zh', 'ko', 'ja'):
            g = await pg.evaluate("l=>{setLang(l);openGuide('test');const h=document.getElementById('guideBody').innerHTML;closeModal(guideBackdropEl);return h}", l)
            ok = 'eligibility-and-enrolment/apply-for-msp' in g and 'moving-from-another-country' in g
            check('%s guide links to the working MSP and ICBC pages' % l, ok)
        await pg.evaluate("()=>setLang('en')")

        # ---- p10: task source and other card links
        await pg.evaluate("()=>{_evBuf.length=0;openGuide('test');openTask('doctor','list')}"); await pg.wait_for_timeout(200)
        await pg.evaluate("(%s)(document.querySelector('#guideTasks .task-src:not(.task-checked) a'))" % CLICK)
        e = await ev('task_src')
        check('the official-source link on a card is counted with the card and the site', e == [{'id': 'doctor', 'to': 'healthlinkbc.ca'}], e)
        n = await pg.evaluate("""()=>{const a=[...document.querySelectorAll('#guideTasks a[href^="http"]')].find(a=>!a.closest('.task-src'));
            if(!a)return null;a.addEventListener('click',e=>e.preventDefault(),{once:true});a.click();return a.hostname.replace(/^www\\./,'')}""")
        if n:
            e = await ev('task_link')
            check('another outbound link in a card is counted as task_link', e and e[-1] == {'id': 'doctor', 'to': n}, e)
        await pg.evaluate("(%s)(document.querySelector('#guideTasks .task-checked a'))" % CLICK)
        e = await ev('feedback_click')
        check('the card translation-fix mail link is counted as task feedback', e == [{'kind': 'task', 'id': 'doctor'}], e)
        tel = await pg.evaluate("""()=>{_evBuf.length=0;const a=document.querySelector('#guideTasks a[href^="tel:"]');
            if(a){a.addEventListener('click',e=>e.preventDefault(),{once:true});a.click();}return {had:!!a,ev:_evBuf.map(e=>e.t)}}""")
        check('tapping a phone number in a card is counted as that card only, never the number',
              tel['had'] and tel['ev'] == ['task_call'], tel)
        tc = await ev('task_call')
        check('task_call carries the card id and no digits', tc == [{'id': 'doctor'}], tc)
        await pg.evaluate("()=>{closeModal(guideBackdropEl)}"); await pg.wait_for_timeout(200)

        # ---- guide text links
        await pg.evaluate("()=>{_evBuf.length=0;openGuide('test')}"); await pg.wait_for_timeout(200)
        h = await pg.evaluate("""()=>{const a=document.querySelector('#guideBody a[href^="http"]');a.addEventListener('click',e=>e.preventDefault(),{once:true});a.click();return a.hostname.replace(/^www\\./,'')}""")
        e = await ev('guide_link')
        check('an outbound link in the long guide is counted with its site only', e == [{'to': h}], e)
        await pg.evaluate("()=>closeModal(guideBackdropEl)"); await pg.wait_for_timeout(200)

        # ---- place "Report an issue" and the general feedback link
        pid = await pg.evaluate("()=>{_evBuf.length=0;focusMarker(M[3],16);return M[3].data.id}"); await pg.wait_for_timeout(700)
        await pg.evaluate("(%s)(document.querySelector('.leaflet-popup .pv-report'))" % CLICK)
        e = await ev('feedback_click')
        check('Report an issue on a place is counted with the place id', len(e) == 1 and e[0]['kind'] == 'place' and e[0]['id'] == pid, (e, pid))
        await pg.evaluate("()=>map.closePopup()")
        await pg.evaluate("()=>{_evBuf.length=0}")
        await pg.evaluate("(%s)(document.getElementById('feedbackLink'))" % CLICK)
        e = await ev('feedback_click')
        check('the general feedback link is counted', e == [{'kind': 'general'}], e)

        # ---- the Help sheet stays untracked
        hs = await pg.evaluate("""()=>{document.getElementById('helpBtn').click();_evBuf.length=0;
            [...document.querySelectorAll('#helpModal a')].forEach(a=>{a.addEventListener('click',e=>e.preventDefault(),{once:true});a.click();});
            const out=_evBuf.map(e=>e.t);closeModal(helpBackdropEl);return out}""")
        check('nothing tapped inside the Help sheet is recorded', hs == [], hs)

        # ---- season_shown: once per page load
        # fresh page load: nothing about the season has been rendered yet
        await pg.reload(); await pg.wait_for_timeout(1300)
        # 2026-10-03: the load itself renders the season for the real date (from October
        # that adds 'winter'); drop those events so only the pinned date is measured.
        await pg.evaluate("()=>{_evBuf.length=0;_iso='2026-09-22';_isoAt=Date.now()+1e9;localStorage.removeItem('kamloopsSeason_wildfire_2026');localStorage.setItem('kamloopsFirstUseSeen','1');document.getElementById('firstUse').hidden=true;renderSeason();renderSeason();setLang('fr');setLang('en');}")
        e = await ev('season_shown')
        check('season_shown is sent once, not on every re-render', e == [{'id': 'wildfire'}], e)

        # ---- nothing new carries text or a full URL
        allp = await pg.evaluate("()=>_evBuf.concat([]).map(e=>JSON.stringify(e.p))")
        check('no new event carries a full URL', not any('http' in x for x in allp), allp)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F))
    sys.exit(1 if F else 0)
asyncio.run(main())
