#!/usr/bin/env python3
"""2026-09-22 — the search synonym table (SYN), and the closest-match fallback
never hiding better matches behind a category/area filter."""
import asyncio, os, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.abspath(__file__))
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

HITS = "([l,q])=>{L_=l;const t=q.toLowerCase();return P.map(p=>({id:p.id,n:p.n,c:p.c,s:matchScore(p,t)})).filter(x=>x.s>0).sort((a,b)=>b.s-a.s)}"

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        hits = lambda l, q: pg.evaluate(HITS, [l, q])
        ncat = lambda c: pg.evaluate("c=>P.filter(p=>p.c===c).length", c)

        # the everyday word finds the whole category, in every language
        for l, q, c in (('en', 'grocery', 'grocery'), ('en', 'supermarket', 'grocery'), ('en', 'dentist', 'dental'),
                        ('en', 'mechanic', 'autorepair'), ('en', 'haircut', 'barber'), ('en', 'laundromat', 'laundry'),
                        ('en', 'atm', 'bank'), ('en', 'mosque', 'religious'), ('en', 'homeless', 'support'),
                        ('zh', '牙医', 'dental'), ('zh', '买菜', 'grocery'), ('zh', '修车', 'autorepair'), ('zh', '警察', 'police'),
                        ('ko', '세탁소', 'laundry'), ('ko', '한인마트', 'asian'), ('ja', '歯医者', 'dental'), ('ja', '美容院', 'barber'),
                        ('fr', 'dentiste', 'dental'), ('fr', 'essence', 'gas'), ('fr', 'laverie', 'laundry'),
                        ('es', 'dentista', 'dental'), ('es', 'peluquería', 'barber'), ('es', 'veterinario', 'vet'),
                        # 2026-09-24: in BC kindergarten is grade K at an elementary school; preschool is childcare
                        ('en', 'kindergarten', 'elem'), ('en', 'preschool', 'daycare'), ('en', 'child minding', 'daycare'),
                        ('ko', '유치원', 'daycare'), ('ja', '幼稚園', 'daycare'), ('zh', '学前班', 'daycare')):
            h = await hits(l, q)
            got = sum(1 for x in h if x['c'] == c)
            check('%s "%s" finds every %s place' % (l, q, c), got == await ncat(c) and got > 0, (got, [x['n'] for x in h][:5]))
        # whatever the interface language
        h = await hits('en', '超市')
        check('an English-interface reader typing 超市 gets the supermarkets', any(x['c'] == 'grocery' for x in h), [x['n'] for x in h][:4])
        h = await hits('zh', 'pharmacy')
        check('a Chinese-interface reader typing "pharmacy" gets the pharmacies', any(x['c'] == 'pharmacy' for x in h))
        # accents never decide
        a = await hits('fr', 'epicerie')
        check('"epicerie" (no accent) finds every supermarket', sum(1 for x in a if x['c'] == 'grocery') == await ncat('grocery'), len(a))
        # prefixes: 4 Latin letters, not 3
        # (the English label "Taxi & Rideshare" already contains "tax" — that predates the table)
        check('the table does not turn "tax" into taxi', await pg.evaluate("()=>synCats('tax').size===0"))
        check('the table does not turn "work" into gyms', await pg.evaluate("()=>!synCats('work').has('gym')"))
        h = await hits('en', 'groc')
        check('"groc" (typing in progress) already finds the supermarkets', any(x['c'] == 'grocery' for x in h))
        # a name still outranks a category word
        h = await hits('en', 'clinic')
        check('"clinic": a place named "…Clinic" still ranks above a category match', h and 'clinic' in h[0]['n'].lower(), h[:2])
        # 2026-09-24: a word inside a multi-word term counts too
        for q, cats in (('school', {'school', 'elem', 'schoolbus', 'driving'}),
                        ('centre', {'mall', 'commctr', 'pool', 'playcenter'}),
                        ('store', {'secondhand', 'liquor', 'pharmacy', 'grocery', 'hardware', 'conv'})):
            got = set(await pg.evaluate("q=>[...synCats(q)]", q))
            check('"%s" reaches the terms that contain it (%s)' % (q, ', '.join(sorted(cats))), got == cats, sorted(got))
        h = await hits('en', 'school')
        check('"school" now finds all 25 elementary schools', sum(1 for x in h if x['c'] == 'elem') == await ncat('elem'), sum(1 for x in h if x['c'] == 'elem'))
        for q in ('de', 'la', 'eau', 'tax', 'du'):
            check('the connecting word "%s" matches no category' % q, await pg.evaluate("q=>synCats(q).size===0", q))
        # (a centre literally named "…Preschool & Kindergarten" matches by name — that is right;
        #  what must not happen is the word itself being treated as a daycare category)
        check('"kindergarten" is a school word, not a daycare category', await pg.evaluate("()=>{const c=[...synCats('kindergarten')];return c.includes('elem')&&!c.includes('daycare')}"))
        h = await hits('en', 'kindergarten')
        check('"kindergarten" finds every elementary school', sum(1 for x in h if x['c'] == 'elem') == await ncat('elem'), sum(1 for x in h if x['c'] == 'elem'))
        h = await hits('en', 'bank')
        check('"bank": the banks come first', h and h[0]['c'] in ('bank', 'foodbank'), h[:2])
        # things that should stay empty
        for q in ('xyzzy', 'dentistt', 'coffee'):
            h = await hits('en', q)
            check('"%s" still finds nothing' % q, not h, [x['n'] for x in h][:3])
        # the crisis path is untouched
        await pg.evaluate("()=>{setLang('en');searchInputEl.value='i want to kill myself';runSearch();}")
        check('a crisis search still shows the crisis panel', await pg.evaluate("()=>!!document.querySelector('#emptyState .crisis-block')"))
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}")

        # ---- closest matches and filters
        async def run(cats, q, regs=None):
            return await pg.evaluate("""([cats,q,regs])=>{setLang('en');aC=new Set(cats);aR=new Set(regs||Object.keys(RI));searchInputEl.value=q;runSearch();
              const e=document.getElementById('emptyState');
              return {closest:_closest,n:lastVisible,empty:!!e&&!e.hidden&&getComputedStyle(e).display!=='none'&&e.innerText.trim()!=='',kind:e?e.dataset.kind:'',
                      cats:M.filter(m=>m.score>0&&markerPasses(m,1)).map(m=>m.data.c)}}""", [cats, q, regs])
        # (categories pause during a search since p19, so the guard is exercised with areas:
        #  North Shore has parks but no dog park; South Kamloops has restaurants but no Asian market)
        r = await run([], 'dog park open now', ['ns'])
        check('"dog park open now" in North Shore: no parks passed off as closest while dog parks are elsewhere', not r['closest'] and r['n'] == 0 and r['empty'] and r['kind'] == 'search_and_filters', r)
        r = await run([], 'chinese grocery store', ['sk'])
        check('"chinese grocery store" in South Kamloops: no restaurants offered in place of the markets', not r['closest'] and r['n'] == 0, r)
        r = await run([], 'dog park open now')
        check('the same search with no filter still shows the dog parks', r['closest'] and r['n'] >= 3 and set(r['cats']) == {'dogpark'}, r)
        g = await pg.evaluate("()=>P.find(p=>p.c==='pharmacy').g")
        r = await run([], 'cheap pharmacy near me', [g])
        check('an area filter that holds the best matches still gets them', r['closest'] and r['n'] >= 1 and set(r['cats']) == {'pharmacy'}, r)
        await pg.evaluate("()=>{aC=new Set();aR=new Set(Object.keys(RI));searchInputEl.value='';runSearch();}")

        # a superseded focus must not open its card late
        await pg.evaluate("()=>{setLang('ja');searchInputEl.value='動物病院';runSearch();}")
        await pg.wait_for_timeout(200)
        await pg.evaluate("()=>{setLang('en');searchInputEl.value='doctor';runSearch();}")
        await pg.click('#searchHelp .sh-btn.primary'); await pg.wait_for_timeout(2600)
        pop = await pg.evaluate("()=>(document.querySelector('.leaflet-popup-content')||{}).innerText||''")
        check('one-result search, then "Show it on the map" within 1.6 s: the card that stays open is the UPCC', 'North Shore Urgent Care' in pop, pop[:60])
        await pg.evaluate("()=>{map.closePopup();searchInputEl.value='';runSearch();}")
        # "walk-in clinic" must not offer the appointment-only centre
        h = await hits('en', 'walk-in clinic')
        check('"walk-in clinic" does not offer the appointment-only UPCLC', not any('UPCLC' in x['n'] for x in h), [x['n'] for x in h])
        # speed: typing must stay instant
        ms = await pg.evaluate("()=>{const t=performance.now();for(const q of ['g','gr','gro','groc','groce','grocer','grocery','grocery s','grocery st']){searchInputEl.value=q;runSearch();}return performance.now()-t}")
        check('nine keystrokes of search run in well under a second (%.0f ms)' % ms, ms < 900, ms)
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}")
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
