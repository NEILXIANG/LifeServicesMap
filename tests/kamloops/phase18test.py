#!/usr/bin/env python3
"""2026-09-24 — before the public demo: six languages end to end (p30), and the
marker cluster is never changed while it animates (p31)."""
import asyncio, os, re, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
ROOT = os.path.dirname(_r)
URL = 'file://' + os.path.join(ROOT, 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)
LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja']
HAN = re.compile(r'[一-鿿]'); KANA = re.compile(r'[぀-ヿ]'); HANG = re.compile(r'[가-힯]')

def script_ok(lang, t):
    if lang in ('en', 'fr', 'es'): return not (HAN.search(t) or KANA.search(t) or HANG.search(t))
    if lang == 'zh': return bool(HAN.search(t)) and not (KANA.search(t) or HANG.search(t))
    if lang == 'ko': return bool(HANG.search(t)) and not KANA.search(t)
    if lang == 'ja': return bool(KANA.search(t) or HAN.search(t)) and not HANG.search(t)

async def main():
    sys.path.insert(0, ROOT); import kamdata; src = kamdata.engine_text()
    check('the app script has no Unicode property escape (ES2017 floor)', '\\p{' not in src[src.find('<script>', src.find('</style>')):])
    data = kamdata.data_text()
    es = data[data.index('UI.es.guideCity'):data.index('UI.ko.guideCity')]
    check('Spanish uses one thousands separator in the city guide', not re.search(r'\d{1,3},\d{3}\b', es), re.findall(r'\d{1,3},\d{3}', es)[:3])

    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 430, 'height': 930}, is_mobile=True, has_touch=True)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)

        # ---------------------------------------------------------- every language
        for L in LANGS:
            r = await pg.evaluate("""(l)=>{resetAll();setLang(l);
                return {lang:document.documentElement.lang,title:document.title,h1:document.getElementById('h1').textContent,
                        ph:searchInputEl.placeholder,status:document.getElementById('statusText').textContent,
                        ann:document.getElementById('a11yAnnounce').textContent,
                        guide:document.getElementById('guideToggle').textContent.trim()}}""", L)
            check('[%s] <html lang> follows the language (%s)' % (L, r['lang']), r['lang'].lower().startswith(L), r['lang'])
            bad = [k for k in ('title', 'ph', 'status', 'guide') if not script_ok(L, r[k])]
            check('[%s] title, search hint, status and guide button are in %s' % (L, L), not bad, {k: r[k] for k in bad})
            check('[%s] no screen-reader sentence left over from the previous language' % L,
                  r['ann'] == '' or script_ok(L, r['ann']), r['ann'])
        # a popup built before the switch speaks the new language
        pop = await pg.evaluate("""async()=>{setLang('zh');setLang('ko');const m=M.find(x=>x.data.p&&x.data.h);
            map.setView(m.getLatLng(),17,{animate:false});m.openPopup();await new Promise(r=>setTimeout(r,500));
            const t=document.querySelector('.leaflet-popup-content').innerText;map.closePopup();return t;}""")
        check('a popup opened after switching zh → ko is in Korean', bool(HANG.search(pop)) and '营业' not in pop and '电话' not in pop, pop[:80])
        # the announcement after a filter change is in the current language
        ann = await pg.evaluate("""async()=>{resetAll();setLang('fr');searchInputEl.value='banque';runSearch();
            await new Promise(r=>setTimeout(r,200));return document.getElementById('a11yAnnounce').textContent;}""")
        check('the next announcement is in the new language (fr)', ann == '' or not HAN.search(ann), ann)
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}")

        # ---------------------------------------------------------- words that used to find nothing
        CASES = [('洗衣房', 'laundry'), ('食品银行', 'foodbank'), ('邮政', 'post'), ('溜冰场', 'rink'), ('室内游乐场', 'playcenter'),
                 ('佛寺', 'religious'), ('barbier', 'barber'), ('tuteur', 'tutor'), ('중고품', 'secondhand'), ('아시아마트', 'asian'),
                 ('애견공원', 'dogpark'), ('가정의', 'hospital'), ('お寺', 'religious'), ('韓国スーパー', 'asian'), ('車の修理', 'autorepair'),
                 ('自動車学校', 'driving')]
        miss = []
        for q, cat in CASES:
            r = await pg.evaluate("""([q,cat])=>{searchInputEl.value=q;runSearch();
                return {n:lastVisible,cat:M.filter(m=>m.score>0&&m.data.c===cat).length}}""", [q, cat])
            if not (r['n'] > 0 and r['cat'] > 0): miss.append((q, cat, r))
        check('%d everyday words in five languages now find their places' % len(CASES), not miss, miss)
        top = await pg.evaluate("""()=>{const o={};for(const q of ['ESL','english class','이민자 서비스','移民支援','英語教室',"cours d'anglais"]){
            searchInputEl.value=q;runSearch();const best=M.filter(m=>m.score>0).sort((a,b)=>b.score-a.score)[0];o[q]=best?best.data.n:null;}
            searchInputEl.value='대학교';runSearch();const t=M.filter(m=>m.score>0).sort((a,b)=>b.score-a.score)[0];o['대학교']=t?t.data.n:null;
            searchInputEl.value='';runSearch();return o;}""")
        check('English classes and settlement words rank Kamloops Immigrant Services first',
              all(v == 'Kamloops Immigrant Services' for k, v in top.items() if k != '대학교'), top)
        check('대학교 finds TRU', top.get('대학교', '').startswith('Thompson Rivers'), top.get('대학교'))
        noise = await pg.evaluate("()=>['센터','매장','식품','학원','ecole','parque'].map(q=>[q,[...synCats(q)].join(',')])")
        check('no new synonym widened an everyday word (센터, 매장, 식품, 학원, école, parque)',
              dict(noise) == {'센터': '', '매장': '', '식품': '', '학원': 'tutor', 'ecole': 'elem,school', 'parque': 'dogpark,park'}
              or all(v in ('', 'tutor', 'elem,school', 'school,elem', 'dogpark,park', 'park,dogpark') for _, v in noise), noise)

        # ---------------------------------------------------------- the cluster during an animation
        r = await pg.evaluate("""async()=>{resetAll();await new Promise(r=>setTimeout(r,900));
            const before=M.filter(m=>cluster.hasLayer(m)).length;
            cluster._inZoomAnimation=1;                                // pretend a zoom is animating
            searchInputEl.value='pharmacy';runSearch();
            const during=M.filter(m=>cluster.hasLayer(m)).length, n=lastVisible, pending=M.filter(m=>m._want!==undefined).length;
            cluster._inZoomAnimation=0;cluster.fire('animationend');
            await new Promise(r=>setTimeout(r,400));
            const after=M.filter(m=>cluster.hasLayer(m)).length, mism=M.filter(m=>!!markerPasses(m,m.score)!==cluster.hasLayer(m)).length;
            return {before,during,n,pending,after,mism};}""")
        check('while the cluster animates, a search changes nothing in it', r['during'] == r['before'] and r['pending'] > 0, r)
        check('  …but the count is already right', r['n'] > 0 and r['n'] < r['before'], r)
        check('  …and the queued changes land when the animation ends', r['after'] == r['n'] and r['mism'] == 0, r)
        r = await pg.evaluate("""async()=>{searchInputEl.value='';runSearch();await new Promise(r=>setTimeout(r,400));
            cluster._inZoomAnimation=1;searchInputEl.value='bank';runSearch();
            await new Promise(r=>setTimeout(r,1700));                   // a counter that never resets
            searchInputEl.value='bank ';runSearch();
            await new Promise(r=>setTimeout(r,300));
            const mism=M.filter(m=>!!markerPasses(m,m.score)!==cluster.hasLayer(m)).length;
            cluster._inZoomAnimation=0;return {mism,n:lastVisible};}""")
        check('a stuck animation counter cannot freeze the map (released after 1.5 s)', r['mism'] == 0 and r['n'] > 0, r)
        r = await pg.evaluate("""async()=>{searchInputEl.value='park';runSearch();
            for(let i=0;i<40&&(cluster._inZoomAnimation>0||M.some(m=>m._want!==undefined));i++)await new Promise(r=>setTimeout(r,100));
            const orig=cluster.addLayer;window.__thrown=0;
            // throws once — whenever the first add actually reaches the cluster — then steps aside
            cluster.addLayer=function(l){cluster.addLayer=orig;window.__thrown++;throw new TypeError("Cannot read properties of undefined (reading '_zoom')");};
            searchInputEl.value='';runSearch();                        // puts ~360 markers back
            const status=document.getElementById('statusText').textContent;   // apply() has returned by now
            for(let i=0;i<40&&!window.__thrown;i++)await new Promise(r=>setTimeout(r,100));
            await new Promise(r=>setTimeout(r,1500));                  // the repair waits for a quiet cluster
            if(cluster.addLayer!==orig)cluster.addLayer=orig;
            const thrown=window.__thrown;
            const mism=M.filter(m=>!!markerPasses(m,m.score)!==cluster.hasLayer(m)).length;
            return {thrown,status,mism,n:lastVisible};}""")
        check('if the cluster still throws, apply() finishes (the status is current)',
              r['thrown'] == 1 and re.search(r'387', r['status'] or ''), r)
        check('  …and the cluster is rebuilt to match the filters', r['mism'] == 0 and r['n'] == 387, r)
        # a single result during an animation still opens its card
        r = await pg.evaluate("""async()=>{resetAll();await new Promise(r=>setTimeout(r,900));
            cluster._inZoomAnimation=1;searchInputEl.value='Kamloops Immigrant Services';runSearch();
            setTimeout(()=>{cluster._inZoomAnimation=0;cluster.fire('animationend');},250);
            for(let i=0;i<30;i++){if(document.querySelector('.leaflet-popup'))break;await new Promise(r=>setTimeout(r,120));}
            const p=document.querySelector('.leaflet-popup .pt');return p?p.textContent:null;}""")
        check('a single result found mid-animation still opens its card', bool(r) and 'Immigrant' in r, r)
        await pg.evaluate("()=>{map.closePopup();searchInputEl.value='';runSearch();}")
        # ---------------------------------------------------------- nothing runs off a 390 px phone
        pg2 = await b.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        await pg2.goto(URL); await pg2.wait_for_timeout(1500)
        over = {}
        for L in LANGS:
            r = await pg2.evaluate("""async(l)=>{setLang(l);document.querySelector('#areaBtn').click();await new Promise(r=>setTimeout(r,500));
                const o=[...document.querySelectorAll('.reg-row .reg-btn')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>e.textContent.slice(0,30));
                closePanel();await new Promise(r=>setTimeout(r,250));
                document.querySelector('#helpBtn').click();await new Promise(r=>setTimeout(r,500));
                const h=[...document.querySelectorAll('.hotlines .hl-line')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>e.textContent.slice(0,30));
                const split=[...document.querySelectorAll('.hotlines .hl-line b')].filter(e=>e.getClientRects().length>1).map(e=>e.textContent);
                document.querySelector('#helpClose').click();await new Promise(r=>setTimeout(r,250));
                return {area:o,help:h,split};}""", L)
            if r['area'] or r['help'] or r['split']: over[L] = r
        check('every area button and crisis line fits a 390 px phone in all six languages, numbers unbroken', not over, over)
        await pg2.close()
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
