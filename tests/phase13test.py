#!/usr/bin/env python3
"""2026-09-22 — plan B: a search pauses the category filter; areas, themes,
open now and near me still apply; turning a category on ends a search."""
import asyncio, os, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.abspath(__file__))
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)
LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja']

STATE = """()=>({q:searchInputEl.value,term:searchTerm,cats:[...aC].sort(),n:lastVisible,
  shown:M.filter(m=>markerHome().hasLayer(m)).map(m=>({c:m.data.c,g:m.data.g,t:m.data.t||[]})),
  note:document.getElementById('searchNote').textContent,
  chip:[...document.querySelectorAll('#activeFilters .af-chip')].map(c=>c.className+'|'+c.innerText),
  panelNote:(document.querySelector('#catGrid .cat-paused-note')||{}).textContent||'',
  paused:document.querySelectorAll('#catGrid .cat-btn.active.paused').length,
  empty:(()=>{const e=document.getElementById('emptyState');return e&&!e.hidden?{kind:e.dataset.kind,txt:e.innerText}:null})()})"""

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        st = lambda: pg.evaluate(STATE)
        async def setup(cats=(), regs=None, themes=(), open_now=False, q=''):
            await pg.evaluate("""([c,r,t,o,q])=>{setLang('en');aC=new Set(c);aR=new Set(r||Object.keys(RI));aT=new Set(t);
              openNow=o;updateOpenQuickpick();renderRegs();renderCats();renderThemes();searchInputEl.value=q;runSearch();apply();}""",
                              [list(cats), regs, list(themes), open_now, q])
            # 2026-09-24 (p31): changes made while the cluster animates a zoom land when
            # the animation ends — read the map once nothing is queued
            await pg.wait_for_function("()=>!M.some(m=>m._want!==undefined)", timeout=4000)
            return await st()
        nlib = await pg.evaluate("()=>P.filter(p=>matchScore(p,'library')>0).length")

        # ---- the pause
        s = await setup(['park'], q='library')
        check('Parks selected, search "library": the libraries appear (%d)' % nlib, s['n'] == nlib and s['n'] > 0 and all(x['c'] != 'park' or True for x in s['shown']), s['n'])
        check('  …no park is shown just for being a park', not any(x['c'] == 'park' for x in s['shown']), [x['c'] for x in s['shown']])
        check('  …the category stays selected (not lost)', s['cats'] == ['park'], s['cats'])
        u = await pg.evaluate("()=>({p:UI.en.catsPausedNote,s:UI.en.catsPausedShort,a:UI.en.searchActive})")
        check('  …the note under the search box says categories are paused', u['p'] in s['note'] and u['a'] not in s['note'], s['note'])
        check('  …the category chip is marked paused', any('af-paused' in c and u['s'] in c for c in s['chip']), s['chip'])
        check('  …the category panel says so and dims the selected button', s['panelNote'] == u['p'] and s['paused'] == 1, (s['panelNote'], s['paused']))
        s = await setup(['park'], q='')
        check('clearing the search brings the category back (parks only, nothing marked paused)',
              s['shown'] and all(x['c'] == 'park' for x in s['shown']) and not s['panelNote'] and s['paused'] == 0 and not any('af-paused' in c for c in s['chip']), (s['n'], s['chip']))

        # ---- the other filters still narrow
        s = await setup(['park'], regs=['ns'], q='pharmacy')
        check('an area still narrows a search (North Shore pharmacies only)', s['n'] > 0 and all(x['g'] == 'ns' and x['c'] == 'pharmacy' for x in s['shown']), s['shown'])
        check('  …and the note says both things', u['a'] in s['note'] and u['p'] in s['note'], s['note'])
        th = await pg.evaluate("()=>{const c={};P.forEach(p=>(p.t||[]).forEach(t=>{if(matchScore(p,'park')>0)c[t]=(c[t]||0)+1}));return Object.entries(c).sort((a,b)=>b[1]-a[1])[0][0]}")
        s = await setup(['library'], themes=[th], q='park')
        check('a theme still narrows a search (every result carries "%s")' % th, s['n'] > 0 and all(th in x['t'] for x in s['shown']), s['n'])
        await setup()
        s = await setup(['park'], open_now=True, q='pharmacy')
        # every place the search matches that is open right now (a grocery whose note mentions a
        # pharmacy counts too — the point of the check is that "open now" still applies)
        oc = await pg.evaluate("()=>P.filter(p=>matchScore(p,'pharmacy')>0&&openNowOk(p)).length")
        # how many the same search finds with no "open now" — the filter has to have
        # something to narrow, but at 4am the honest answer is that none are open, so
        # the count itself cannot be required to be above zero.
        allm = await pg.evaluate("()=>P.filter(p=>matchScore(p,'pharmacy')>0).length")
        check('"open now" still narrows a search (%d of %d matches open)' % (oc, allm),
              s['n'] == oc and allm > 0 and oc <= allm, (s['n'], oc, allm))
        await setup()

        # ---- empty states
        s = await setup(['park'], q='xyzzy')
        check('category + a search with no match: the plain "no match" message, not the filter one', s['empty'] and s['empty']['kind'] == 'search', s['empty'])
        s = await setup(['park'], regs=['ot'], q='pharmacy')
        if s['n'] == 0:
            check('area + no match: the filter message, and it no longer blames categories', s['empty'] and s['empty']['kind'] == 'search_and_filters' and 'categor' not in s['empty']['txt'].lower(), s['empty'])
        for l in LANGS:
            t = await pg.evaluate("l=>[UI[l].noResultFiltered,UI[l].searchActive,UI[l].catsPausedNote,UI[l].catsPausedShort,UI[l].themeHint]", l)
            bad = [x for x in t[:2] if any(w in x for w in ('分类', 'catégorie', 'categoría', 'category', '분류', 'カテゴリー'))]
            check('%s: the filter messages no longer say categories narrow a search; pause strings present' % l, not bad and all(t[2:4]) and len(t[4]) > 40, bad)
        await setup()

        # ---- the latest input wins
        await setup(q='library')
        await pg.evaluate("()=>{_evBuf.length=0;openPanel('cat');}"); await pg.wait_for_timeout(400)
        await pg.evaluate("()=>{document.querySelectorAll('.cat-group').forEach(g=>g.classList.add('open'));}")
        btn = pg.locator('#catGrid .cat-btn').filter(has_text=await pg.evaluate("()=>CI.bank.en")).first
        await btn.click(); await pg.wait_for_timeout(300)
        s = await st(); ev = await pg.evaluate("()=>_evBuf.map(e=>e.t+':'+(e.p.by||e.p.action||''))")
        check('turning a category on during a search ends the search and applies the category',
              s['q'] == '' and not s['term'] and s['cats'] == ['bank'] and s['shown'] and all(x['c'] == 'bank' for x in s['shown']), (s['q'], s['cats'], s['n']))
        check('  …logged as search_clear by:category', 'search_clear:category' in ev, ev)
        await pg.evaluate("()=>{searchInputEl.value='library';runSearch();}")
        btn = pg.locator('#catGrid .cat-btn.active').first
        await btn.click(); await pg.wait_for_timeout(300)
        s = await st()
        check('turning a category off during a search keeps the search', s['q'] == 'library' and s['cats'] == [], (s['q'], s['cats']))
        await pg.evaluate("()=>closePanel()"); await pg.wait_for_timeout(300)
        await setup(q='library')
        await pg.evaluate("()=>{_evBuf.length=0;document.getElementById('daily').click();}"); await pg.wait_for_timeout(300)
        s = await st(); ev = await pg.evaluate("()=>_evBuf.map(e=>e.t+':'+(e.p.by||''))")
        check('tapping a Quick Pick during a search ends the search and applies it',
              s['q'] == '' and len(s['cats']) > 3 and 'search_clear:preset' in ev, (s['q'], s['cats'], ev))
        await setup()
        await setup(q='library')
        await pg.evaluate("()=>{openPanel('cat');}"); await pg.wait_for_timeout(300)
        await pg.locator('#catGrid .grp-check').first.click(); await pg.wait_for_timeout(300)
        s = await st()
        check('ticking a whole category group during a search ends the search', s['q'] == '' and len(s['cats']) >= 1, (s['q'], s['cats']))
        await pg.evaluate("()=>closePanel()"); await pg.wait_for_timeout(300)
        await setup()

        # ---- closest matches follow the same rule
        s = await setup(['park'], q='dog park open now')
        check('"dog park open now" with Parks selected now shows the dog parks', s['n'] >= 3 and all(x['c'] == 'dogpark' for x in s['shown']), [x['c'] for x in s['shown']])
        await setup()

        # ---- logging
        await setup(['park'], q='library')
        await pg.evaluate("()=>{_evBuf.length=0;_lastLoggedQuery=null;logSearch();}")
        ev = await pg.evaluate("()=>JSON.parse(JSON.stringify(_evBuf.filter(e=>e.t==='search_run').map(e=>e.p)))")
        check('search_run: filtered:false when only categories are set, catsPaused:true', ev and ev[-1].get('filtered') is False and ev[-1].get('catsPaused') is True, ev)
        await setup()

        # ---- a shared link with a category and a search
        p2 = await b.new_page(); p2.on('pageerror', lambda e: errs.append('link: ' + str(e)))
        await p2.goto(URL + '?city=kamloops&c=park&q=library'); await p2.wait_for_timeout(1800)
        s = await p2.evaluate(STATE)
        check('a shared link with ?c=park&q=library opens with the search running and the category kept (paused)',
              s['term'] == 'library' and s['cats'] == ['park'] and s['n'] == nlib, (s['term'], s['cats'], s['n']))
        await p2.close()

        # ---- phone: the chip and note fit
        ph = await b.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ph.on('pageerror', lambda e: errs.append('phone: ' + str(e)))
        await ph.goto(URL); await ph.wait_for_timeout(1500)
        for l in LANGS:
            w = await ph.evaluate("""l=>{setLang(l);aC=new Set(['park']);renderCats();searchInputEl.value='library';runSearch();
              const els=[document.getElementById('searchNote'),...document.querySelectorAll('#activeFilters .af-chip')];
              return els.filter(e=>e.offsetParent).map(e=>{const r=e.getBoundingClientRect();return [Math.round(r.left),Math.round(r.right)]})}""", l)
            check('%s phone: the note and chips stay inside the screen' % l, w and all(a >= 0 and z <= 390 for a, z in w), w)
        await ph.screenshot(path='/tmp/a7/p19-phone.png')
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
