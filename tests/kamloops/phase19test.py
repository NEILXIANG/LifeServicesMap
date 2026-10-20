#!/usr/bin/env python3
"""2026-09-24 (p33) — "Open now" is an errand filter: it no longer puts the crisis
lines under the filter row. The lines stay wherever they answer a real need."""
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
        await pg.goto(URL); await pg.wait_for_timeout(1600)
        for L in ('zh', 'en', 'fr', 'es', 'ko', 'ja'):
            r = await pg.evaluate("""(l)=>{resetAll();setLang(l);document.getElementById('qpOpen').click();
                const a=document.getElementById('activeFilters');
                return {on:openNow,chip:!!a.querySelector('.af-chip'),lines:a.querySelectorAll('.hotlines,.hl-line').length,
                        note:a.querySelectorAll('.af-holiday').length,holiday:isHolidayToday()}}""", L)
            check('[%s] "Open now" is on, its chip shows, and no crisis lines hang under the filters' % L,
                  r['on'] and r['chip'] and r['lines'] == 0 and (r['note'] == 0 or r['holiday']), r)
        # a statutory holiday: the row still warns, in words that do not point at missing lines
        r = await pg.evaluate("""()=>{resetAll();setLang('en');CITY.holidays.push(cityISODate());_isoAt=Date.now();
            openNow=true;updateOpenQuickpick();apply();const a=document.getElementById('activeFilters');
            const t=(a.querySelector('.af-holiday')||{}).textContent||'';const lines=a.querySelectorAll('.hl-line').length;
            CITY.holidays.pop();_isoAt=Date.now();openNow=false;updateOpenQuickpick();apply();return {t,lines}}""")
        check('on a holiday the row says listed hours may not apply', 'holiday' in r['t'] and 'call before you go' in r['t'], r)
        check('  …and no longer says "these lines" about lines it does not show', 'these lines' not in r['t'].lower() and r['lines'] == 0, r)
        keys = await pg.evaluate("()=>['zh','en','fr','es','ko','ja'].map(l=>[l,UI[l].holidayChipNote,UI[l].holidayOpenNote])")
        check('the short holiday note exists in all six languages and is the long one minus its last clause',
              all(c and o.startswith(c) and len(o) > len(c) for _, c, o in keys), [k[0] for k in keys if not k[1]])
        # nothing open at all: the empty state still carries the lines
        r = await pg.evaluate("""()=>{resetAll();setLang('en');const keep=openNowOk;window.openNowOk=()=>false;openNowOk=()=>false;
            openNow=true;updateOpenQuickpick();apply();const e=document.getElementById('emptyState');
            const out={vis:lastVisible,shown:!e.hidden,lines:e.querySelectorAll('.hl-line').length,
                       dial:[...e.querySelectorAll('.hl-line')].every(x=>/^tel:\\d+$/.test(x.getAttribute('href')))};
            openNowOk=keep;openNow=false;updateOpenQuickpick();apply();return out}""")
        check('with nothing open, the empty state still lists the 24-hour lines, all dialable',
              r['vis'] == 0 and r['shown'] and r['lines'] >= 5 and r['dial'], r)
        # the other two ways in are untouched
        r = await pg.evaluate("""async()=>{resetAll();document.getElementById('helpBtn').click();await new Promise(r=>setTimeout(r,500));
            const h=document.querySelectorAll('#helpBody .hl-line').length;document.getElementById('helpClose').click();
            searchInputEl.value='suicide';runSearch();await new Promise(r=>setTimeout(r,300));
            const c=[...document.querySelectorAll('.crisis-block .hl-line')].filter(x=>x.offsetParent).length;
            searchInputEl.value='';runSearch();return {h,c}}""")
        check('the Help button still lists the lines (%d)' % r['h'], r['h'] >= 5, r)
        check('a crisis search still brings them up (%d)' % r['c'], r['c'] >= 5, r)

        # ---------------------------------------------------------- p34: help that appears on its own must fit the query
        CARD = {'食物银行': 'hardship', '食品银行': 'hardship', '음식점': None, '동물병원': None, '歯医者': None, '自動車学校': None,
                '대학교': None, 'rent': 'housing', 'ER': None, 'free': None, 'gratuit': None, '무료': None, '租房': 'housing',
                'alquiler': 'housing', '賃貸': 'housing', '押金': 'deposit', '보증금': 'deposit', 'landlord': 'deposit',
                'health card': 'msp', '医保': 'msp', 'SIN': 'sin', '驾照': 'licence', 'family doctor': 'doctor', 'médico': 'sick',
                'bank': 'bank', '孩子上学': 'school', 'lost my job': 'jobloss'}
        got = await pg.evaluate("""(qs)=>{const o={};for(const q of qs){searchRaw=q.toLowerCase();searchTerm=searchRaw;const t=_taskForQuery();o[q]=t?t.id:null;}
            searchRaw='';searchTerm='';return o}""", list(CARD))
        wrong = {q: (got[q], w) for q, w in CARD.items() if got[q] != w}
        check('the suggested task card fits the query (%d cases: food bank ≠ bank, rent ≠ parent, ER ≠ settlement…)' % len(CARD), not wrong, wrong)
        HB = {'Little Fawn Nursery - Head Start Program': False, '수의사': False, 'eye doctor': False, 'seguro médico': False,
              'health insurance': False, 'vet': False, 'dentist': False, 'ER': True, 'walk-in clinic': True, 'sick': True,
              '看病': True, '병원': True, '病院': True, 'nurse': True, 'nursing home': False}
        hb = await pg.evaluate("(qs)=>Object.fromEntries(qs.map(q=>[q,_isHealthQuery(q)]))", list(HB))
        wrong = {q: hb[q] for q, w in HB.items() if hb[q] != w}
        check('the "sick today?" box appears for illness words only (not a nursery, a vet, eye care or insurance)', not wrong, wrong)
        trap = await pg.evaluate("(qs)=>qs.filter(q=>isCrisisQuery(q))", ['skill', 'skiing', 'pharmacy', 'haircut', 'deadline', 'diet', 'bridge',
                                  'painting', 'parents', 'harmony', 'kids', 'knives', 'gun club', 'nursery', '아파트', 'die Post'])
        check('ordinary words never open the crisis panel', not trap, trap)
        ints = await pg.evaluate("""()=>{let bad=[];for(const l of ['zh','en','fr','es','ko','ja']){setLang(l);
            TASKS.forEach(t=>{for(const q of [t.q[l]||t.q.en,t.t[l]||t.t.en]){searchRaw=q.toLowerCase();searchTerm=searchRaw;
              const x=_taskForQuery();if(!x||x.id!==t.id)bad.push([l,t.id,x?x.id:null]);}});}
            searchRaw='';searchTerm='';setLang('en');return bad}""")
        check('a card\'s own question or title, typed in any language, suggests that card (%d exceptions)' % len(ints),
              not ints, ints)   # 2026-10-04: a card's own words now win outright, so no exceptions remain
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
