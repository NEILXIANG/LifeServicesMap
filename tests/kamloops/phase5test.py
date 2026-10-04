#!/usr/bin/env python3
"""Phase 5 (2026-09-21) — task-card conditions; step counts unchanged."""
import asyncio, os, sys, subprocess, json
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)
# step counts before phase 5 (ticks are stored by position)
BEFORE = {'settle': 3, 'sin': 2, 'msp': 4, 'licence': 3, 'bank': 3, 'school': 3, 'tax': 3, 'connect': 4, 'eldercare': 4, 'sick': None, 'deposit': 3, 'hardship': 3, 'rights': 3, 'legal': 3}
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 1280, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        n = await pg.evaluate("()=>Object.fromEntries(TASKS.map(t=>[t.id,t.steps.length]))")
        check('no card gained or lost a step', all(v is None or n[k] == v for k, v in BEFORE.items()), n)
        T = await pg.evaluate("()=>JSON.stringify(TASKS)")
        for needle, why in (('within one year of moving out', 'deposit: one-year limit'), ('super visa', 'eldercare: visitor parents'),
                            ('COPR is not accepted', 'msp: accepted documents'), ('need an appointment', 'licence: tests are booked'),
                            ('secondary ID', 'sin: two documents'), ('Schools of Choice', 'school: choice programmes'),
                            ('ext. 116', 'connect: register first'), ('substantially prejudiced', 'rights: the test'),
                            ('mental health and prison law', 'legal: scope'), ('9:30 pm curfew', 'hardship: shelter rules')):
            check(why, needle in T)
        for bad in ('no referral needed, just show up', 'Seniors\' line', 'no appointment needed for most visits', 'many families pay nothing', 'take walk-ins any time, day or night'):
            check('gone: %r' % bad, bad not in T)
        six = await pg.evaluate("""()=>{const out=[];const L=['en','fr','es','zh','ko','ja'];
            const walk=(o,p)=>{if(o&&typeof o==='object'&&!Array.isArray(o)){if('en' in o&&typeof o.en==='string'){L.forEach(l=>{if(!o[l])out.push(p+'.'+l)});return;}for(const k in o)walk(o[k],p+'.'+k);}else if(Array.isArray(o))o.forEach((x,i)=>walk(x,p+'['+i+']'));};
            TASKS.forEach(t=>walk(t,t.id));return out;}""")
        check('every card text exists in six languages', not six, six[:5])
        el = await pg.evaluate("()=>P.filter(p=>['elem','school'].includes(p.c)&&/immuni/i.test((p.note||{}).en||'')).map(p=>p.n)")
        check('no school note asks for immunization records', not el, el)
        bad = await pg.evaluate("()=>{const out=[];for(const l of ['en','fr','es','zh','ko','ja']){setLang(l);for(const t of TASKS){try{openTask(t.id,'list');const h=document.getElementById('guideTasks').innerHTML;if(/undefined|NaN/.test(h))out.push(l+':'+t.id);}catch(e){out.push(l+':'+t.id+':'+e)}}}setLang('en');return out;}")
        check('every card opens cleanly in six languages', not bad, bad[:5])
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n  %d pass, %d fail' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
