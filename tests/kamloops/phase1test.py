#!/usr/bin/env python3
"""Phase 1 (2026-09-21) — safety and trust. Checks the built page."""
import asyncio, os, re, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
BUILT = os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
URL = 'file://' + BUILT
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
        await pg.goto(URL + '?city=kamloops'); await pg.wait_for_timeout(1500)
        # a stale event log from an older version is removed on load
        await pg.evaluate("()=>localStorage.setItem('kamloopsEvents','[{\"t\":\"x\"}]')")
        await pg.reload(); await pg.wait_for_timeout(1500)
        check('stale kamloopsEvents is removed on an ordinary visit', await pg.evaluate("()=>localStorage.getItem('kamloopsEvents')") is None)
        await pg.evaluate("()=>{for(let i=0;i<30;i++)trackEvent('x',{});flushEvents();}")
        check('events are not written to localStorage outside debug', await pg.evaluate("()=>localStorage.getItem('kamloopsEvents')") is None)
        # search: not in the address bar, but in a share link
        await pg.fill('#searchInput', 'library'); await pg.wait_for_timeout(1800)
        url = await pg.evaluate('()=>location.search')
        check('search term stays out of the address bar', 'q=' not in url and 'library' not in url, url)
        sh = await pg.evaluate('()=>shareHref()')
        check('a share link carries the search on purpose', 'q=library' in sh, sh)
        # crisis search
        for q, lang in (('domestic violence', 'en'), ('家暴', 'zh'), ('자살', 'ko'), ('suicidio', 'es')):
            await pg.fill('#searchInput', ''); await pg.wait_for_timeout(300)
            await pg.fill('#searchInput', q); await pg.wait_for_timeout(1800)
            r = await pg.evaluate("""()=>{const el=document.getElementById('emptyState');
                return {vis:!el.hidden,crisis:!!el.querySelector('.crisis-block'),tel:el.querySelectorAll('.crisis-block a[href^="tel:"]').length,
                        logged:_evBuf.filter(e=>e.t==='search_run').slice(-1).map(e=>e.p.q)[0],share:shareHref()}}""")
            check('crisis search %r shows the lines' % q, r['vis'] and r['crisis'] and r['tel'] >= 8, r)
            check('crisis search %r is logged as [crisis] and never shared' % q, r['logged'] == '[crisis]' and 'q=' not in r['share'], r)
        for q in ('library', 'dvd', 'pharmacy', '危险品', 'abbotsford'):
            await pg.fill('#searchInput', ''); await pg.wait_for_timeout(300)
            await pg.fill('#searchInput', q); await pg.wait_for_timeout(700)
            c = await pg.evaluate("()=>!!document.querySelector('#emptyState .crisis-block')")
            check('ordinary search %r shows no crisis block' % q, not c)
        await pg.fill('#searchInput', ''); await pg.wait_for_timeout(600)
        check('clearing the search removes the crisis block', await pg.evaluate("()=>document.getElementById('emptyState').hidden"))
        # hotlines: 24h only
        hl = await pg.evaluate("()=>CITY.hotlines.map(h=>h.n)")
        check('211 left the 24-hour list; VictimLink and KUU-US joined', '211' not in hl and '1-800-563-0808' in hl and '1-800-588-8717' in hl, hl)
        # help sheet
        await pg.click('#helpBtn'); await pg.wait_for_timeout(500)
        hs = await pg.evaluate("""()=>({open:helpBackdropEl.classList.contains('open'),
            tel:[...document.querySelectorAll('#helpBody a[href^="tel:"]')].map(a=>a.getAttribute('href')),
            exit:!!document.getElementById('helpExit'),title:document.getElementById('helpTitle').textContent,
            ev:_evBuf.some(e=>e.t==='help_open')})""")
        check('help button opens the help sheet', hs['open'] and hs['exit'] and hs['ev'], hs)
        check('help sheet has the hotlines, the local crisis team and 2-1-1', 'tel:7784702725' in hs['tel'] and 'tel:211' in hs['tel'] and 'tel:911' in hs['tel'], hs['tel'])
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
        check('Escape closes the help sheet', not await pg.evaluate("()=>helpBackdropEl.classList.contains('open')"))
        # language switch relabels
        await pg.click('#helpBtn'); await pg.wait_for_timeout(300)
        await pg.evaluate("()=>setLang('zh')"); await pg.wait_for_timeout(300)
        t = await pg.evaluate("()=>[document.getElementById('helpTitle').textContent,document.getElementById('helpBtn').getAttribute('aria-label'),UI.zh.helpTitle,UI.en.helpTitle]")
        # the title is read from the data, not a fixed phrase: zh's became "📞 求助" (2026-10-20, launch review)
        check('help sheet follows a language change', t[0].strip() and t[0].strip() in t[2] and t[0].strip() not in t[3] and '求助' in t[1], t)   # the emoji renders as an icon
        # clear device: two taps
        await pg.evaluate("()=>{localStorage.setItem('kamloopsFavorites','[\"x\"]');localStorage.setItem('other','keep');}")
        await pg.click('#helpClear'); await pg.wait_for_timeout(200)
        still = await pg.evaluate("()=>localStorage.getItem('kamloopsFavorites')")
        check('clear needs a second tap', still is not None)
        await pg.click('#helpClear'); await pg.wait_for_timeout(1500)
        left = await pg.evaluate("()=>[localStorage.getItem('kamloopsFavorites'),localStorage.getItem('other'),location.search]")
        check('second tap clears this site only and reopens clean', left[0] is None and left[1] == 'keep' and 'lang=' not in left[2], left)
        # task ticks
        await pg.evaluate("()=>{setStep('msp',0,true);}")
        ts = await pg.evaluate("()=>_evBuf.filter(e=>e.t==='task_step').slice(-1)[0].p")
        check('a tick does not say which card', 'id' not in ts and ts.get('action') == 'tick', ts)
        await pg.evaluate("()=>setStep('msp',0,false)")
        # task wording
        tw = await pg.evaluate("()=>{const h=TASKS.find(t=>t.id==='hardship'),s=TASKS.find(t=>t.id==='settle');return [h.why.en,h.confid.en,s.confid.en,h.steps[1].en];}")
        check('no blanket immigration promises in hardship/settle', not any(re.search(r'report you|immigration status|affect your status|do not need status', x) for x in tw), tw)
        # footer links
        ft = await pg.evaluate("()=>[...document.querySelectorAll('.footer-emergency a')].map(a=>a.getAttribute('href'))")
        check('footer numbers are tappable, with 9-8-8', set(['tel:911', 'tel:988', 'tel:811', 'tel:2508283000']) <= set(ft), ft)
        check('no page errors', not errs, errs[:3])
        await pg.close()
        # phone header fits, every language
        for lang in ('en', 'fr', 'es', 'zh', 'ko', 'ja'):
            pm = await b.new_page(viewport={'width': 360, 'height': 780}, is_mobile=True, has_touch=True)
            await pm.goto(URL + '?city=kamloops&lang=' + lang); await pm.wait_for_timeout(1300)
            r = await pm.evaluate("""()=>{const hb=document.getElementById('helpBtn').getBoundingClientRect();
                const hl=document.getElementById('headerLinksGroup').getBoundingClientRect();
                return {sw:document.documentElement.scrollWidth,iw:innerWidth,hbVis:hb.width>0&&hb.right<=innerWidth,rows:Math.round(hl.height)}}""")
            check('360px %s: help button visible, no sideways scroll' % lang, r['hbVis'] and r['sw'] <= r['iw'], r)
            if lang in ('fr', 'zh'):
                await pm.screenshot(path='/tmp/claude-0/p1_%s.png' % lang)
                await pm.click('#helpBtn'); await pm.wait_for_timeout(500)
                await pm.screenshot(path='/tmp/claude-0/p1_help_%s.png' % lang)
            await pm.close()
        await b.close()
    print('\n  %d pass, %d fail' % (P, F))
    sys.exit(1 if F else 0)
asyncio.run(main())
