#!/usr/bin/env python3
"""Kelowna: strict GUI regression (2026-10-04).

    .venv/bin/python tests/kelowna/guitest.py          # builds build/kelowna.html first

Drives the built page the way a reader would — typing, clicking, switching languages, opening every
popup, card, route and panel — and fails on anything a newcomer should never see:

  A. no page error or console error anywhere in the session
  B. no Kamloops fact in any language (names, phone numbers, fares, data source) — in the UI strings,
     the visible page, the guide, every task card, every popup and the bus panel
  C. no unfilled placeholder, "undefined", "NaN", "[object Object]" or TODO in anything rendered
  D. every one of the places renders a popup in all six languages; tel: links are dialable
  E. searches in six languages find what a newcomer looks for; the health answer lists the three
     UPCCs; crisis words go straight to the lines, never to "check spelling"
  F. every category and every area shows places; quick picks (open now, near me) work
  G. every task card opens in every language with working links
  H. every bus route selects and draws; bus search finds the campus
  I. a favourite survives a reload; the language survives a reload; ?lang= works
  J. no horizontal scroll at 320/390/430/768/1280 px in any language, with the guide open too
  K. every button has an accessible name
"""
import asyncio, json, os, re, subprocess, sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HTML = os.path.join(ROOT, 'build', 'kelowna.html')
LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja']
P_ = F_ = 0
FAILS = []
def check(name, ok, info=None):
    global P_, F_
    if ok: P_ += 1; print('  PASS', name)
    else:
        F_ += 1; FAILS.append(name); print('  FAIL', name, ' —', str(info)[:600])

# Other cities' facts that must never reach a Kelowna reader (B). 2026-10-04: derived from every other
# city's data (kamdata.leak_markers: area names, landmarks, UPCCs, local phones, city.json leakMarkers) instead of a
# hand-written Kamloops list, so a third city is covered without editing this file. Below: spellings and
# formats that cannot be derived (digit-only phones, French price format, retired wording).
sys.path.insert(0, ROOT)
import kamdata
FORBIDDEN = [r'(?<![\w$])' + re.escape(t) + r'(?!\w)' for t in kamdata.leak_markers('kelowna')]
FORBIDDEN += [r'Kamloops', r'\bTRU\b', r'Secw[eé]pemc', r'Tk.?eml[uú]ps', r'2508283000', r'2,25 ?\$', r'Google Places', r'Columbia St']
FORB = re.compile('|'.join(FORBIDDEN))
GARBAGE = re.compile(r'\{[A-Z_]{2,}\}|\bundefined\b|\bNaN\b|\[object Object\]|\bTODO\b')

def leaks(text):
    return sorted(set(m.group(0) for m in FORB.finditer(text or '')))
def garbage(text):
    return sorted(set(m.group(0) for m in GARBAGE.finditer(text or '')))

async def main():
    subprocess.run([sys.executable, os.path.join(ROOT, 'build.py'), '--city', 'kelowna', '--no-sync-public'],
                   check=True, capture_output=True)
    url = 'file://' + HTML
    errors = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx = await b.new_context(viewport={'width': 1280, 'height': 900}, geolocation={'latitude': 49.8863, 'longitude': -119.4966},
                                  permissions=['geolocation'], locale='en-CA', timezone_id='America/Vancouver')
        pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errors.append('pageerror: ' + str(e)[:300]))
        # network refusals that only happen on file:// (the map-tile key is restricted to the site's
        # origin, so the engine falls back to the second tile server; the analytics beacon has no origin)
        NET = re.compile(r'Failed to load resource|cloudflareinsights|ERR_FAILED|CORS policy')
        pg.on('console', lambda m: errors.append('console.%s: %s' % (m.type, m.text[:300])) if m.type == 'error' and not NET.search(m.text) else None)
        await pg.goto(url + '?lang=en'); await pg.wait_for_timeout(1800)

        # ---- A/first load
        check('A1 title is the Kelowna title', (await pg.title()) == 'Kelowna Life Guide', await pg.title())
        check('A2 first-use card shows on a first visit', await pg.evaluate("()=>{const f=document.getElementById('firstUse');return !!f&&!f.hidden&&f.offsetHeight>0}"))
        await pg.evaluate("()=>dismissFirstUse('test')")

        # ---- B/C: UI strings, all languages (hidden strings too)
        ui = await pg.evaluate("()=>{const o={};for(const l of Object.keys(UI)){o[l]=Object.entries(UI[l]).filter(([k,v])=>typeof v==='string').map(([k,v])=>k+'='+v).join('\\n')}return o}")
        for l in LANGS:
            check('B1 %s: no Kamloops fact in any UI string' % l, not leaks(ui[l]), leaks(ui[l]))
            # {TD} is filled when a card renders (the card's own check date), by design
            u2 = ui[l].replace('{TD}', '')
            check('C1 %s: no unfilled placeholder in UI strings' % l, not garbage(u2),
                  [ln[:120] for ln in u2.split('\n') if GARBAGE.search(ln)][:5])

        # ---- B/C/D: per language — page, note, footer, guide, help, share, popups, bus panel
        for l in LANGS:
            await pg.evaluate("l=>setLang(l)", l); await pg.wait_for_timeout(300)
            body = await pg.evaluate("()=>document.body.innerText")
            note = await pg.evaluate("()=>document.getElementById('noteBody').innerText")
            foot = await pg.evaluate("()=>document.getElementById('footer').innerText")
            await pg.evaluate("()=>openGuide('test')"); await pg.wait_for_timeout(300)
            guide = await pg.evaluate("()=>document.getElementById('guideModal').innerText")
            await pg.evaluate("()=>closeModal(guideBackdropEl)")
            await pg.evaluate("()=>{renderHelpSheet();renderShareSheet();}")
            sheets = await pg.evaluate("()=>document.getElementById('helpBody').innerText+'\\n'+document.getElementById('shareModal').innerText")
            pops = await pg.evaluate("()=>P.map((p,i)=>{const d=document.createElement('div');d.innerHTML=popup(p,i);return d.innerText+'\\u0001'+[...d.querySelectorAll('a[href^=\"tel:\"]')].map(a=>a.getAttribute('href')).join(' ')})")
            await pg.evaluate("()=>openPanel('bus')"); await pg.wait_for_timeout(200)
            bus = await pg.evaluate("()=>document.getElementById('panel').innerText")
            await pg.evaluate("()=>closePanel()")
            allt = '\n'.join([body, note, foot, guide, sheets, bus] + pops)
            check('B2 %s: no Kamloops fact on the page, guide, sheets, popups or bus panel' % l, not leaks(allt), leaks(allt))
            check('C2 %s: nothing unfilled or broken in rendered text' % l, not garbage(allt),
                  [s for s in (re.findall(r'.{0,60}(?:\{[A-Z_]{2,}\}|undefined|NaN|\[object Object\]|TODO).{0,60}', allt))][:5])
            bad_pop = [i for i, t in enumerate(pops) if len(t.split('\u0001')[0].strip()) < 5]
            check('D1 %s: all %d places render a popup with content' % (l, len(pops)), not bad_pop, bad_pop[:5])
            tels = ' '.join(t.split('\u0001')[1] for t in pops).split()
            bad_tel = [t for t in tels if not re.fullmatch(r'tel:\+?1?\d{10}|tel:\d{3}|tel:\d{1,3}(-\d)*', t)]
            check('D2 %s: every tel: link is dialable (%d links)' % (l, len(tels)), not bad_tel, bad_tel[:5])
            check('B3 %s: footer gives the Kelowna RCMP line' % l, '250-762-3300' in foot, foot[-300:])

        # ---- E: search (typed, as a reader does)
        await pg.evaluate("l=>setLang(l)", 'en')
        async def search(q):
            await pg.fill('#searchInput', ''); await pg.type('#searchInput', q, delay=8); await pg.wait_for_timeout(650)
            return await pg.evaluate("()=>({n:lastVisible,help:document.getElementById('searchHelp').innerText,empty:document.getElementById('emptyState').innerText,hk:document.getElementById('searchHelp').dataset.kind||''})")
        queries = {'en': ['doctor', 'walk in clinic', 'pharmacy', 'daycare', 'laundry', 'library', 'UPCC', 'food bank', 'shelter',
                          'ESL', 'English class', 'school', 'park', 'beach', 'church', 'mosque', 'gurdwara', 'ICBC', 'Service Canada',
                          'WorkBC', 'legal aid', 'tax clinic', 'dentist', 'police', 'post office', 'bank', 'apartment', 'UBCO', 'Rutland'],
                   'zh': ['看病', '药房', '托儿', '图书馆', '英语', '洗衣', '食物银行', '学校', '公园', '报税'],
                   'fr': ['médecin', 'pharmacie', 'garderie', 'bibliothèque'],
                   'es': ['médico', 'farmacia', 'guardería', 'biblioteca'],
                   'ko': ['병원', '약국', '어린이집', '도서관'],
                   'ja': ['病院', '薬局', '保育', '図書館']}
        for l, qs in queries.items():
            await pg.evaluate("l=>setLang(l)", l)
            zero = []
            for q in qs:
                r = await search(q)
                if r['n'] == 0: zero.append(q)
            check('E1 %s: every newcomer search finds places (%d queries)' % (l, len(qs)), not zero, zero)
        await pg.evaluate("l=>setLang(l)", 'en')
        r = await search('doctor')
        names = ['Kelowna Urgent and Primary Care Centre', 'Rutland Urgent and Primary Care Centre', 'West Kelowna Urgent and Primary Care Centre']
        check('E2 "doctor": the health answer lists all three UPCCs', r['hk'] == 'health' and all(n in r['help'] for n in names), r['help'][:400])
        pre = await pg.evaluate("()=>JSON.stringify({shown:_upccs().map(p=>{const m=M.find(x=>x.data.id===p.id);return m?_isShown(m):'nomarker'}),aR:[...aR].length,aC:[...aC],aT:[...aT],openNow:openNow,near:nearOnly,L:L_,btn:document.querySelector('#searchHelp .sh-btn.primary').textContent,anim:map._animatingZoom,busy:_clusterBusy(),hidden:document.hidden,vis:document.visibilityState})")
        await pg.click('#searchHelp .sh-btn.primary')
        popup_open = ''
        # the map flies there first (about 2 s; much longer when the machine is busy running other suites),
        # so wait for the map's own open popup rather than a fixed time
        for _ in range(60):
            await pg.wait_for_timeout(200)
            popup_open = await pg.evaluate("()=>{const p=map._popup&&map.hasLayer(map._popup)&&document.querySelector('.leaflet-popup-content');return p?p.innerText:''}")
            if popup_open: break
        # and it has to stay open: a card that flashes and vanishes is the bug this caught (2026-10-04)
        await pg.wait_for_timeout(1500)
        if popup_open:
            popup_open = await pg.evaluate("()=>{const p=map._popup&&map.hasLayer(map._popup)&&document.querySelector('.leaflet-popup-content');return p?p.innerText:''}")
        diag = '' if popup_open else await pg.evaluate("()=>JSON.stringify({modals:[...document.querySelectorAll('.open')].map(e=>e.id||e.className).slice(0,6),help:document.getElementById('searchHelp').innerText.slice(0,80),q:searchInputEl.value,popup:!!map._popup,zoom:map.getZoom()})")
        check('E3 "Show it on the map" opens a UPCC popup that stays open', 'Urgent and Primary Care' in popup_open, popup_open[:200] or (diag + ' | before click: ' + pre))
        for l, q in [('en', 'suicide'), ('zh', '自杀'), ('fr', 'suicide'), ('es', 'suicidio'), ('ko', '자살'), ('ja', '自殺'), ('en', 'domestic violence'), ('zh', '家暴')]:
            await pg.evaluate("l=>setLang(l)", l)
            r = await search(q)
            html = await pg.evaluate("()=>document.getElementById('emptyState').innerHTML+document.getElementById('searchHelp').innerHTML+document.getElementById('searchNote').innerHTML")
            check('E4 %s crisis "%s": the crisis lines come first, dialable' % (l, q), 'tel:' in html and ('988' in html or '1-800-563-0808' in html or '18005630808' in html), html[:300])
        await pg.fill('#searchInput', ''); await pg.wait_for_timeout(400)

        # ---- F: categories, areas, quick picks
        await pg.evaluate("l=>setLang(l)", 'en')
        cats = await pg.evaluate("()=>[...new Set(P.map(p=>p.c))]")
        empty_c = await pg.evaluate("""cs=>cs.filter(c=>{aC=new Set([c]);aT=new Set();apply();return lastVisible===0})""", cats)
        check('F1 each of the %d categories shows places when chosen alone' % len(cats), not empty_c, empty_c)
        regs = await pg.evaluate("()=>Object.keys(RI)")
        empty_r = await pg.evaluate("""rs=>{aC=new Set();const out=rs.filter(r=>{aR=new Set([r]);apply();return lastVisible===0});aR=new Set(Object.keys(RI));apply();return out}""", regs)
        check('F2 each of the %d areas shows places' % len(regs), not empty_r, empty_r)
        await pg.evaluate("()=>resetAll()"); await pg.wait_for_timeout(300)
        await pg.click('#qpOpen'); await pg.wait_for_timeout(500)
        n_open = await pg.evaluate("()=>lastVisible")
        check('F3 "open now" runs (shows %d places)' % n_open, n_open >= 0)
        await pg.click('#qpOpen'); await pg.wait_for_timeout(300)
        # "near me" appears once the reader has been located (the map's locate button)
        await pg.evaluate("()=>geoControl._btn.click()"); await pg.wait_for_timeout(400)
        check('F4a the locate button explains before asking', await pg.evaluate("()=>!document.getElementById('geoNote').hidden"))
        await pg.click('#geoNoteOk'); await pg.wait_for_timeout(2000)
        await pg.click('#qpNear'); await pg.wait_for_timeout(1500)
        n_near = await pg.evaluate("()=>lastVisible")
        check('F4 "near me" from downtown Kelowna shows places (%d)' % n_near, n_near > 0, n_near)
        await pg.evaluate("()=>resetAll()"); await pg.wait_for_timeout(300)
        for pid in ['daily', 'newcomer']:
            await pg.click('#' + pid); await pg.wait_for_timeout(400)
            n = await pg.evaluate("()=>lastVisible")
            check('F5 quick pick "%s" shows places (%d)' % (pid, n), n > 0, n)
            await pg.evaluate("()=>resetAll()"); await pg.wait_for_timeout(200)

        # ---- G: every task card, every language
        tids = await pg.evaluate("()=>TASKS.map(t=>t.id)")
        for l in LANGS:
            await pg.evaluate("l=>setLang(l)", l)
            bad = []
            for t in tids:
                txt = await pg.evaluate("id=>{openTask(id,'test');const m=document.getElementById('guideModal');const r={t:m.innerText,links:[...m.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'))};return r}", t)
                problems = leaks(txt['t']) + garbage(txt['t']) + [h for h in txt['links'] if not re.match(r'(https?:|tel:|mailto:|#|\?|sms:)', h)]
                if len(txt['t']) < 80: problems.append('short')
                if problems: bad.append((t, problems[:3]))
            await pg.evaluate("()=>closeModal(guideBackdropEl)")
            check('G1 %s: all %d task cards open cleanly with valid links' % (l, len(tids)), not bad, bad[:4])

        # ---- H: bus routes
        await pg.evaluate("l=>setLang(l)", 'en')
        await pg.evaluate("()=>openPanel('bus')"); await pg.wait_for_timeout(300)
        rkeys = await pg.evaluate("()=>Object.keys(BR)")
        bad_r = await pg.evaluate("""ks=>ks.filter(k=>{try{selectRoute(k);return !selectedRoute}catch(e){return true}})""", rkeys)
        check('H1 all %d bus routes select' % len(rkeys), not bad_r, bad_r)
        # back to the route list (a selected route shows its own detail instead)
        await pg.evaluate("()=>{closePanel();resetAll();openPanel('bus')}"); await pg.wait_for_timeout(400)
        await pg.fill('#busSearch', 'UBCO'); await pg.wait_for_timeout(500)
        nb = await pg.evaluate("()=>document.querySelectorAll('#busList button, #busList li').length")
        check('H2 bus search "UBCO" lists routes (%d)' % nb, nb > 0)
        await pg.evaluate("()=>closePanel()")

        # ---- I: persistence
        await pg.evaluate("()=>resetAll()")
        await pg.evaluate("()=>{const m=M.find(x=>x.data.id==='37ef188e');focusMarker(m,16);}"); await pg.wait_for_timeout(1500)
        await pg.click('.leaflet-popup-content .fav-star'); await pg.wait_for_timeout(300)
        await pg.evaluate("l=>setLang(l)", 'ko')
        await pg.reload(); await pg.wait_for_timeout(1800)
        st = await pg.evaluate("()=>({fav:favorites.has('37ef188e'),lang:L_})")
        check('I1 a favourite survives a reload', st['fav'], st)
        check('I2 the chosen language survives a reload', st['lang'] == 'ko', st)
        await pg.goto(url + '?lang=ja'); await pg.wait_for_timeout(1500)
        check('I3 ?lang=ja opens in Japanese', await pg.evaluate("()=>L_") == 'ja')

        # ---- J: layout at phone and desktop widths
        over = []
        for w in [320, 390, 430, 768, 1280]:
            await pg.set_viewport_size({'width': w, 'height': 800})
            for l in LANGS:
                await pg.evaluate("l=>setLang(l)", l); await pg.wait_for_timeout(120)
                o = await pg.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
                await pg.evaluate("()=>openGuide('test')"); await pg.wait_for_timeout(150)
                og = await pg.evaluate("()=>{const m=document.getElementById('guideModal');return Math.max(document.documentElement.scrollWidth-document.documentElement.clientWidth, m.scrollWidth-m.clientWidth)}")
                await pg.evaluate("()=>closeModal(guideBackdropEl)")
                if o > 1 or og > 1: over.append((w, l, o, og))
        check('J1 no horizontal scroll at 320–1280 px in any language (page and guide)', not over, over[:6])
        await pg.set_viewport_size({'width': 1280, 'height': 900})

        # ---- K: accessibility basics
        unnamed = await pg.evaluate("""()=>[...document.querySelectorAll('button')].filter(b=>b.offsetParent!==null&&!(b.innerText.trim()||b.getAttribute('aria-label')||b.getAttribute('title'))).map(b=>b.id||b.className).slice(0,10)""")
        check('K1 every visible button has an accessible name', not unnamed, unnamed)

        check('A3 no page error or console error in the whole session', not errors, errors[:6])
        await b.close()
    print('\n%d passed, %d failed' % (P_, F_))
    if FAILS: print('failed:', FAILS)
    sys.exit(1 if F_ else 0)

if __name__ == '__main__':
    asyncio.run(main())
