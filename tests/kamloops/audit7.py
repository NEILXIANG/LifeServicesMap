#!/usr/bin/env python3
"""2026-09-22 — independent functional audit (written from scratch, not derived
from the earlier suites). Every check recomputes the expected answer from the raw
data in Python or plain JS and compares it with what the page actually shows."""
import asyncio, os, sys, json, re, math
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
LANGS = ['en', 'fr', 'es', 'zh', 'ko', 'ja']
P_ = F_ = 0
def check(name, ok, info=None):
    global P_, F_
    if ok: P_ += 1; print('  PASS', name)
    else: F_ += 1; print('  FAIL', name, ' —', str(info)[:600])

def open_state(h, d, m, mo=9):
    """Independent re-implementation of the documented hours rules."""
    if not isinstance(h, dict): return None
    if h.get('a'): return True
    if h.get('k') or h.get('q'): return None
    se = h.get('se')
    if se == 'summer' and not (5 <= mo <= 9): return None
    if se == 'winter' and not (mo >= 11 or mo <= 3): return None
    known = False
    for r in h.get('r') or []:
        d1, d2, o, c = r[0], r[1], r[2], r[3]
        if o is None: continue
        known = True
        today = d1 <= d <= d2
        yd = 7 if d == 1 else d - 1
        yest = d1 <= yd <= d2
        if c is None:
            if today and m >= o: return True
            continue
        if c > o:
            if today and o <= m < c: return True
        else:
            if today and m >= o: return True
            if yest and m < c: return True
    return False if known else None

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 1280, 'height': 900})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append('console:' + m.text) if m.type == 'error' and 'tile' not in m.text.lower() and 'net::' not in m.text
            and 'cloudflareinsights' not in m.text and 'Failed to load resource' not in m.text else None)
        await pg.goto(URL); await pg.wait_for_timeout(1800)
        D = json.loads(await pg.evaluate("()=>JSON.stringify({P,TASKS,CITY,BR,CI:Object.keys(CI),RI:Object.keys(RI)})"))
        P, TASKS, CITY, BR = D['P'], D['TASKS'], D['CITY'], D['BR']

        # ---- 1. every category and every area shows exactly the places the data says
        await pg.evaluate("()=>{localStorage.setItem('kamloopsFirstUseSeen','1');}")
        bad = []
        for c in D['CI']:
            n = await pg.evaluate("c=>{aC=new Set([c]);aR=new Set(Object.keys(RI));aT=new Set();openNow=false;searchTerm='';apply();return M.filter(m=>markerPasses(m)).length}", c)
            want = sum(1 for p in P if p['c'] == c)
            if n != want: bad.append((c, n, want))
        check('each category filter shows exactly its places (%d categories)' % len(D['CI']), not bad, bad)
        bad = []
        for g in D['RI']:
            n = await pg.evaluate("g=>{aC=new Set();aR=new Set([g]);aT=new Set();openNow=false;searchTerm='';apply();return M.filter(m=>markerPasses(m)).length}", g)
            want = sum(1 for p in P if p['g'] == g)
            if n != want: bad.append((g, n, want))
        check('each area filter shows exactly its places', not bad, bad)
        allv = await pg.evaluate("()=>{aC=new Set();aR=new Set(Object.keys(RI));aT=new Set();openNow=false;searchTerm='';apply();return lastVisible}")
        check('with no filter every place is on the map', allv == len(P), (allv, len(P)))

        # ---- 2. search: every place is found by its own name, in every language
        miss = {}
        for l in LANGS:
            m = await pg.evaluate("""l=>{setLang(l);aC=new Set();aR=new Set(Object.keys(RI));aT=new Set();openNow=false;
                const out=[];for(const p of P){const q=p.n.replace(/^[⭐\\s]+/,'').toLowerCase();if(!(matchScore(p,q)>0))out.push(p.n);}return out}""", l)
            if m: miss[l] = m[:5]
        check('every place is found by searching its own name, in all six languages', not miss, miss)
        await pg.evaluate("()=>setLang('en')")

        # ---- 3. "open now" agrees with an independent reading of the hours, all week
        diffs = []
        for d in range(1, 8):
            for m in range(0, 1440, 30):
                page = await pg.evaluate("([d,m])=>P.map(p=>{const s=openState(p.h,{d,m,mo:9});return s?s.open:null})", [d, m])
                for p, got in zip(P, page):
                    want = open_state(p.get('h'), d, m, 9)
                    if got != want: diffs.append((p['n'], d, m, got, want))
        check('open/closed matches an independent evaluation for every place, every half hour of the week', not diffs, diffs[:5])
        oddh = [p['n'] for p in P if isinstance(p.get('h'), dict) for r in p['h'].get('r', []) if r[0] > r[1] or (r[2] is not None and not 0 <= r[2] <= 1440) or (r[3] is not None and not 0 <= r[3] <= 1440)]
        check('no hours range is inverted or out of the day', not oddh, oddh)

        # ---- 4. place cards: in every language, no template leak; links and phones match the data
        leaks = []; linkbad = []
        for l in LANGS:
            r = await pg.evaluate("""l=>{setLang(l);const out=[],lb=[];P.forEach((p,i)=>{const h=popup(p,i);
                if(/undefined|NaN|\\{[A-Z]+\\}|\\[object/.test(h))out.push(p.n);
                const d=document.createElement('div');d.innerHTML=h;
                d.querySelectorAll('a[href]').forEach(a=>{const u=a.getAttribute('href');
                  if(/^tel:/.test(u)){if(p.p&&u.replace(/\\D/g,'')!==p.p.replace(/\\D/g,'').slice(-u.replace(/\\D/g,'').length))lb.push(p.n+' tel '+u)}
                  else if(/^https?:/.test(u)){if(!u.startsWith('https://'))lb.push(p.n+' http '+u)}
                });
                if(p.w&&!h.includes(p.w.replace(/&/g,'&amp;')))lb.push(p.n+' website missing');
                if(p.p&&!d.querySelector('a[href^="tel:"]'))lb.push(p.n+' phone not tappable');});return [out,lb]}""", l)
            if r[0]: leaks.append((l, r[0][:4]))
            if r[1]: linkbad.append((l, r[1][:4]))
        check('no place card shows undefined / NaN / an unfilled {TEMPLATE}, in any language', not leaks, leaks)
        check('every place card links the website on file and a tappable phone that dials the number on file', not linkbad, linkbad)
        await pg.evaluate("()=>setLang('en')")

        # ---- 5. task cards: all 17 open in every language; steps tick and persist; deep link opens the card
        bad = []
        for l in LANGS:
            r = await pg.evaluate("""l=>{setLang(l);const out=[];for(const t of TASKS){try{openGuide('test');openTask(t.id,'list');
                const h=document.getElementById('guideTasks').innerHTML;if(/undefined|NaN|\\{[A-Z]+\\}/.test(h))out.push(t.id+':leak');
                const n=document.querySelectorAll('#guideTasks .task-step, #guideTasks [data-step]').length;
                const src=(t.srcL&&t.srcL[l])||t.src;   /* the reader's own language where the agency has one (2026-10-20) */
                if(src&&!h.includes(src.replace(/&/g,'&amp;')))out.push(t.id+':src');}catch(e){out.push(t.id+':'+e)}}
                closeModal(guideBackdropEl);return out}""", l)
            if r: bad.append((l, r[:6]))
        check('all task cards open cleanly in six languages and show their official source', not bad, bad)
        st = await pg.evaluate("""()=>{const t=TASKS[1];setStep(t.id,0,true);const a=JSON.parse(localStorage.getItem('kamloopsSteps')||'{}');
            setStep(t.id,0,false);return {id:t.id,saved:a}}""")
        check('ticking a step is saved on the device', isinstance(st['saved'], dict) and st['id'] in st['saved'], st)
        pg2 = await b.new_page()
        await pg2.goto(URL + '?city=kamloops&task=jobloss'); await pg2.wait_for_timeout(1800)
        dl = await pg2.evaluate("()=>({open:guideBackdropEl.classList.contains('open'),t:_taskOpen})")
        check('a ?task= link opens that card', dl['open'] and dl['t'] == 'jobloss', dl)
        await pg2.close()

        # ---- 6. bus routes: each draws, and its service line matches the data
        bad = []
        for k, r in BR.items():
            h = await pg.evaluate("k=>{selectRoute(k);return routeInfoHtml(k)}", k)
            f, lst = r['f'], r['l']
            def fmt(t):
                hh, mm = map(int, t.split(':')); return '%02d:%02d' % (hh % 24, mm)
            if fmt(f) not in h or fmt(lst) not in h or 'undefined' in h: bad.append((k, h[:120]))
        await pg.evaluate("()=>selectRoute(null)")
        check('every bus route draws and states its first and last times', not bad, bad)
        badt = [(k, r['f'], r['l']) for k, r in BR.items() if not re.match(r'^\d\d:\d\d$', r['f']) or not re.match(r'^\d\d:\d\d$', r['l']) or r['f'] >= r['l']]
        check('route times are well-formed and first < last', not badt, badt)

        # ---- 7. shared link round trip
        url = await pg.evaluate("""()=>{aC=new Set(['bank','post']);aR=new Set(['ns']);aT=new Set();openNow=true;apply();urlWriteBlocked=false;writeURLState();return location.href}""")
        pg3 = await b.new_page()
        await pg3.goto(url); await pg3.wait_for_timeout(1800)
        rt = await pg3.evaluate("()=>({c:[...aC].sort(),r:[...aR],o:openNow})")
        check('a shared link restores its categories, area and open-now filter', rt == {'c': ['bank', 'post'], 'r': ['ns'], 'o': True}, (url, rt))
        await pg3.close()
        await pg.evaluate("()=>{openNow=false;aC=new Set();aR=new Set(Object.keys(RI));apply();}")

        # ---- 8. favourites survive a reload
        fid = P[5]['id']
        await pg.evaluate("i=>{favorites.add(i);saveFavorites();}", fid)
        await pg.reload(); await pg.wait_for_timeout(1500)
        check('a favourite survives a reload', await pg.evaluate("i=>favorites.has(i)", fid))
        await pg.evaluate("i=>{favorites.delete(i);saveFavorites();}", fid)

        # ---- 9. help sheet: every hotline is tappable with the right digits, in every language
        bad = []
        for l in LANGS:
            r = await pg.evaluate("""l=>{setLang(l);renderHelpSheet();const h=document.getElementById('helpBody').innerHTML;
                return CITY.hotlines.filter(x=>!h.includes('tel:'+x.n.replace(/[^\\d]/g,''))).map(x=>x.n)}""", l)
            if r: bad.append((l, r))
        check('every hotline is a tappable number in the Help sheet, in all languages', not bad, bad)

        # ---- 10. the long guide: no template leaks, all outbound links https
        bad = []
        for l in LANGS:
            r = await pg.evaluate("""l=>{setLang(l);openGuide('test');const g=document.getElementById('guideBody');const h=g.innerHTML;
                const out=[];if(/undefined|\\{[A-Z_]+\\}/.test(h))out.push('leak');
                g.querySelectorAll('a[href^="http:"]').forEach(a=>out.push(a.href));closeModal(guideBackdropEl);return out}""", l)
            if r: bad.append((l, r[:4]))
        check('the resident guide has no template leaks or insecure links, in any language', not bad, bad)

        # ---- 11. every UI string exists in all six languages
        miss = await pg.evaluate("""()=>{const keys=new Set();Object.keys(UI).forEach(l=>Object.keys(UI[l]).forEach(k=>keys.add(k)));
            const out=[];keys.forEach(k=>['en','fr','es','zh','ko','ja'].forEach(l=>{if(UI[l][k]===undefined||UI[l][k]==='')out.push(l+'.'+k)}));return out}""")
        check('every interface string exists in all six languages', not miss, miss[:10])

        # ---- 12. data sanity that a person would notice
        B = CITY['bounds']
        out = [p['n'] for p in P if not (B[0][0] <= p['lat'] <= B[1][0] and B[0][1] <= p['lng'] <= B[1][1])]
        check('every place lies inside the city bounds', not out, out)
        dup = {}
        for p in P: dup.setdefault(p['id'], []).append(p['n'])
        check('place ids are unique', all(len(v) == 1 for v in dup.values()), [v for v in dup.values() if len(v) > 1])

        # ---- 13. facts corrected in this pass (p11), read back from the live page
        fx = await pg.evaluate("""()=>{const by=n=>P.find(p=>p.n===n);return {
            pool:by('Brocklehurst Outdoor Pool').p, seedw:by('The Mustard Seed West End Shelter').w,
            seed:by('The Mustard Seed West End Shelter').note.en, fjc:by('Kamloops Family Justice Centre').w,
            cm:[by('Columbia Manor').lat,by('Columbia Manor').lng,by('Columbia Manor').g],
            r13:BR['13'].l, r1:BR['1'].l, r9:BR['9'].l,
            card:TASKS.find(t=>t.id==='hardship').note.en}}""")
        check('Brocklehurst pool phone is the City number 250-554-1747', fx['pool'] == '250-554-1747', fx['pool'])
        # 2026-10-04: bed counts change month to month (City list, Sept 2026: 22) — the note and the card no longer
        # state one; the link and the shelter line are what must stay
        check('West End Shelter links to its Kamloops listing; no stale bed count in its note or the card',
              'bc.211.ca' in fx['seedw'] and '30 beds' not in fx['seed'] and '250-372-9890' in fx['card'], fx)
        check('Family Justice Centre links to the Kamloops page', fx['fjc'].endswith('/locations/kamloops'), fx['fjc'])
        check('bus last trips come from regular service (13 Yellowhead 20:46, 1 Tranquille 01:14)', fx['r13'] == '20:46' and fx['r1'] == '25:14' and fx['r9'] == '26:16', fx)
        dist = lambda a, b: math.hypot((a[0]-b[0])*111000, (a[1]-b[1])*70500)
        check('Columbia Manor sits at 1336 Columbia St, South Kamloops', dist(fx['cm'], (50.671986, -120.308858)) < 30 and fx['cm'][2] == 'sk', fx['cm'])
        tel = await pg.evaluate("()=>{const i=P.findIndex(p=>/Mental Health & Substance Use/.test(p.n));const d=document.createElement('div');d.innerHTML=popup(P[i],i);return [...d.querySelectorAll('a[href^=\"tel:\"]')].map(a=>a.getAttribute('href'))}")
        check('the 310-6478 Interior Health line is tappable', 'tel:3106478' in tel, tel)
        ph = await pg.evaluate("()=>phoneHtml('Call 250-554-1747 or 310-6789 or 8-1-1; Suite 2310 is not a phone')")
        check('phone linking catches 10-digit, 310- and 8-1-1 numbers and nothing else',
              ph.count('<a href=') == 3 and 'tel:3106789' in ph and '2310</' not in ph, ph)

        check('no page errors or console errors', not errs, errs[:5])
        await b.close()
    print('\n%d passed, %d failed' % (P_, F_))
    sys.exit(1 if F_ else 0)
asyncio.run(main())
