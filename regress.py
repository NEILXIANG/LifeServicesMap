import asyncio, sys, os, re, glob, shutil, atexit, tempfile
from playwright.async_api import async_playwright

# Test the file that is actually shipped, not a copy that was made by hand at some
# point and has been quietly ageing ever since. Both fixtures are regenerated on
# every run from kamloops.html.
HERE = os.path.dirname(os.path.abspath(__file__))

def find_built(here, argv_path=None):
    """The built file. Named kamloops.html here; readers often rename their copy,
    so fall back to the only .html sitting next to this script."""
    if argv_path:
        return argv_path
    default = os.path.join(here, 'kamloops.html')
    if os.path.exists(default):
        return default
    found = [f for f in glob.glob(os.path.join(here, '*.html'))
             if not os.path.basename(f).startswith('test_')]
    if len(found) == 1:
        return found[0]
    if not found:
        sys.exit('no built HTML found next to this script — run build.py first')
    sys.exit('several .html files here; name one: %s <file>' % os.path.basename(__file__))

SOURCE = find_built(HERE, sys.argv[1] if len(sys.argv) > 1 else None)
# Fixtures go to a temp directory, not next to the deliverable — two 500 KB copies
# of the map appearing in the reader's own folder is not a nice surprise.
TMP = tempfile.mkdtemp(prefix='kamloops-regress-')
atexit.register(lambda: shutil.rmtree(TMP, ignore_errors=True))
COPY = os.path.join(TMP, 'test_copy.html')
NOCLUSTER = os.path.join(TMP, 'test_nocluster.html')

def prepare():
    html = open(SOURCE, encoding='utf-8').read()
    # Test hooks. Kept here rather than in the shipped file so the deliverable has
    # no test scaffolding in it. Top-level const/let in a classic script live in the
    # shared global lexical environment, so a later script can see them.
    hooks = ('<script>window.Pref=P;window.Mref=M;window.mapref=map;'
             'window.aCref=()=>aC;window.aRref=()=>aR;'
             'window.CITYref=CITY;window.selRoute=()=>selectedRoute;'
             'window.fmtHoursRef=fmtHours;window.focusRef=focusMarker;'
             'window.favRef=()=>favorites;window.CIref=CI;window.GRPref=GRP;</script>')
    if '</body>' not in html:
        sys.exit('no </body> to hang the test hooks on')
    open(COPY, 'w', encoding='utf-8').write(html.replace('</body>', hooks + '</body>', 1))
    # Simulate the plugin failing to arrive — inlined or from a CDN, the app has to
    # cope with L.markerClusterGroup being undefined.
    before = html
    html = re.sub(r'<script src="[^"]*markercluster[^"]*"></script>', '', html)
    html = re.sub(r'<script>\n/\* leaflet\.markercluster\.js \*/.*?</script>', '', html, flags=re.S)
    if html == before:
        sys.exit('could not remove the cluster plugin — check how build.py emits it')
    open(NOCLUSTER, 'w', encoding='utf-8').write(html.replace('</body>', hooks + '</body>', 1))

prepare()
URL='file://'+COPY
TOUCH_PROBE = """()=>{
  const m=document.getElementById('map').getBoundingClientRect();
  const small=[];
  document.querySelectorAll('button,a[href]').forEach(e=>{
    const s=getComputedStyle(e);
    if(s.display==='none'||s.display==='inline')return;
    const b=e.getBoundingClientRect(); if(!b.width)return;
    if(Math.min(b.width,b.height)<36)small.push((e.id||e.className||e.tagName).toString().slice(0,20));});
  return {share:Math.round(100*(Math.min(m.bottom,innerHeight)-Math.max(m.top,0))/innerHeight),
          ov:document.body.scrollWidth-innerWidth, small:[...new Set(small)]};}"""

TALL_POPUP_PROBE = """async()=>{
  const idx=Pref.map((p,i)=>[i,(p.note&&p.note.fr||'').length]).sort((a,b)=>b[1]-a[1])[0][0];
  focusRef(Mref[idx],17);
  for(let t=0;t<40;t++){if(document.querySelector('.leaflet-popup'))break;
    await new Promise(r=>setTimeout(r,150));}
  await new Promise(r=>setTimeout(r,900));   // long enough for a self-closing popup to show itself
  const el=document.querySelector('.leaflet-popup');
  if(!el)return {none:true};
  const pu=el.getBoundingClientRect(), m=document.getElementById('map').getBoundingClientRect();
  const name=document.querySelector('.pt'), act=document.querySelector('.pact-btn');
  return {h:Math.round(pu.height), stillOpen:true,
          overRight:+(pu.right-innerWidth).toFixed(1),
          overLeft:+(0-pu.left).toFixed(1),
          aboveMap:+(m.top-pu.top).toFixed(1),
          nameVisible:!!name&&name.getBoundingClientRect().top>=0,
          actionVisible:!!act};}"""

FAIL=[]
def check(label, cond, detail=''):
    print(("  PASS  " if cond else "  FAIL  ")+label+((" — "+str(detail)) if detail else ''))
    if not cond: FAIL.append(label)

N = None   # number of places, read from the file under test at startup

async def main():
    global N
    async with async_playwright() as p:
        # This container ships a Chromium at a fixed path; elsewhere let Playwright
        # find the one `playwright install chromium` put down.
        exe='/opt/pw-browsers/chromium'
        b=await (p.chromium.launch(executable_path=exe) if os.path.exists(exe)
                 else p.chromium.launch())
        allerrs=[]
        pg=await b.new_page(viewport={'width':1280,'height':900})
        pg.on('pageerror', lambda e: allerrs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)

        N = await pg.evaluate("Pref.length")
        globals()['N'] = N
        print("\n--- data layer --- (%d places)" % N)
        d=await pg.evaluate("""()=>({
          n:Pref.length, ratings:Pref.filter(p=>p.r).length,
          prices:Pref.filter(p=>{const t=p.note?Object.values(p.note).join(' '):'';return /\\$\\s?\\d/.test(t);}).length,
          ids:new Set(Pref.map(p=>p.id)).size,
          bilingual:Pref.filter(p=>p.note&&p.note.zh&&p.note.en).length,
          notes:Pref.filter(p=>p.note).length,
          emailInPhone:Pref.filter(p=>(p.p||'').includes('@')).length,
          cjkNames:Pref.filter(p=>/[\\u4e00-\\u9fff]/.test(p.n)).length,
          structuredHours:Pref.filter(p=>p.h&&typeof p.h==='object').length,
          stamps:Pref.filter(p=>p.v).length})""")
        check("01 every place survives the build", d['n']==N and N>=240, d['n'])
        check("01 no hard-coded ratings", d['ratings']==0)
        check("02 no price figures in notes", d['prices']==0)
        check("24 every note bilingual", d['bilingual']==d['notes'], "%d/%d"%(d['bilingual'],d['notes']))
        check("24 Chinese gone from place names", d['cjkNames']<=1, "%d remaining (Cheng Kwong keeps its 中文 storefront name)"%d['cjkNames'])
        check("16 place ids unique", d['ids']==N)
        check("06 no email in phone field", d['emailInPhone']==0)
        # Not a fixed number: 18 open-air records deliberately lost their hours in round 7,
        # because "hours posted on site" is the honest answer for a city park.
        check("31 most records carry structured hours", d['structuredHours'] > N*0.7, d['structuredHours'])
        check("02 verification stamps present", d['stamps']==N)

        print("\n--- hours rendering across languages ---")
        h=await pg.evaluate("""()=>{const bad=[];
          ['zh','en','fr','es','ko','ja'].forEach(l=>Pref.forEach(p=>{if(!p.h)return;
            const s=fmtHoursRef(p.h,l);
            if(!s||/undefined|NaN|\\[object/.test(s))bad.push(l+':'+p.n);}));
          return bad;}""")
        check("01 hours render in all 6 languages", len(h)==0, h[:3])
        cl=await pg.evaluate("""()=>{L_='en';const p=Pref.find(x=>/South Kamloops Secondary/.test(x.n));
          return fmtHoursRef(p.h,'en');}""")
        check("01 closed days stated", 'Closed' in cl, cl)

        print("\n--- search ---")
        for term,lang,expect in [('a','en','gated'),('bank','en','some'),('은행','ko','some'),
                                 ('banque','fr','some'),('银行','zh','some'),('langar','en','some')]:
            await pg.click('[data-lang="%s"]'%lang); await pg.wait_for_timeout(300)
            await pg.fill('#searchInput',term); await pg.wait_for_timeout(560)
            n=await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)).length")
            note=await pg.inner_text('#searchNote')
            if expect=='gated': check("14 %r gated"%term, n==N and 'least' in note or 'at least' in note.lower() or '2' in note, note[:30])
            else: check("14/33 %r [%s] finds results"%(term,lang), 0<n<120, n)
            await pg.click('#searchClear'); await pg.wait_for_timeout(300)

        await pg.click('[data-lang="en"]'); await pg.wait_for_timeout(300)
        print("\n--- search + filters combine (P0-2) ---")
        # Search used to silently bypass Area/Category — a "bank" search while North
        # Shore was selected quietly searched the whole city. It now narrows within
        # whatever is already filtered, so a bank search under a North-Shore-only,
        # bank-only filter should show exactly the North Shore banks, not every bank
        # in the city and not every North Shore place.
        await pg.evaluate("(()=>{aCref().clear();['bank'].forEach(k=>aCref().add(k));aRref().clear();aRref().add('ns');renderRegs();renderCats();apply();})()")
        await pg.wait_for_timeout(400)
        await pg.fill('#searchInput','bank'); await pg.wait_for_timeout(650)
        expected=await pg.evaluate("Pref.filter(p=>p.c==='bank'&&p.g==='ns').length")
        shown=await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)).length")
        check("65 search narrows within active filters, not around them",
              shown==expected, "%d shown vs %d expected (ns banks)"%(shown,expected))
        chips=await pg.evaluate("getComputedStyle(document.getElementById('activeFilters')).display")
        check("65 filter chips stay visible while searching (no longer bypassed)", chips!='none', chips)
        note=await pg.inner_text('#searchNote')
        check("65 search note explains results are narrowed by the filter", 'filter' in note.lower(), note)
        await pg.click('#resetBtn'); await pg.wait_for_timeout(600)
        check("13 Reset clears the search too", (await pg.input_value('#searchInput'))=='')

        print("\n--- empty states ---")
        await pg.fill('#searchInput','zzzq'); await pg.wait_for_timeout(650)
        t1=await pg.inner_text('#emptyState')
        await pg.click('#searchClear'); await pg.wait_for_timeout(400)
        # an empty category set now means "no filter", so it can no longer empty the
        # map; the two reachable empty states are search-empty and filter-empty
        await pg.evaluate("(()=>{aCref().clear();renderCats();apply();})()"); await pg.wait_for_timeout(450)
        check("04 empty category set shows everything", await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)).length")==N)
        await pg.evaluate("(()=>{aCref().clear();aCref().add('dental');aRref().clear();aRref().add('ws');renderRegs();renderCats();apply();})()")
        await pg.wait_for_timeout(450)
        t3=await pg.inner_text('#emptyState')
        check("11 the two empty states differ", t1!=t3)
        check("11 filter-empty does not mention search", 'search' not in t3.lower(), t3[:60])
        await pg.evaluate("resetAll()")
        await pg.wait_for_timeout(500)

        print("\n--- empty state: search narrowed to zero by a filter (P0-2) ---")
        # A third, distinct empty state: a search that finds nothing only because an
        # active filter excludes it. The message should point at the filter, not just
        # repeat the "no matching places" wording used for an unfiltered search.
        await pg.evaluate("(()=>{aCref().clear();aCref().add('bank');aRref().clear();aRref().add('ns');renderRegs();renderCats();apply();})()")
        await pg.wait_for_timeout(400)
        await pg.fill('#searchInput','zzzq'); await pg.wait_for_timeout(650)
        t4=await pg.inner_text('#emptyState')
        check("65 filtered-zero-search empty state mentions the filter", 'filter' in t4.lower(), t4[:80])
        check("65 filtered-zero-search empty state differs from plain search-empty", t4!=t1)
        await pg.click('.empty-btn'); await pg.wait_for_timeout(450)
        aCsize=await pg.evaluate("aCref().size")
        regionBtns=await pg.evaluate("document.querySelectorAll('#regRow .reg-btn').length-1")
        aRsize=await pg.evaluate("aRref().size")
        check("65 its button clears the area/category filters", aCsize==0 and aRsize==regionBtns,
              "aC=%d aR=%d/%d"%(aCsize,aRsize,regionBtns))
        await pg.evaluate("resetAll()"); await pg.wait_for_timeout(500)

        print("\n--- favourites ---")
        await pg.evaluate("mapref.setView([50.6684,-120.3659],18)"); await pg.wait_for_timeout(700)
        await pg.evaluate("()=>{const i=Pref.findIndex(x=>/Canada Games/.test(x.n));focusRef(Mref[i],18);}"); await pg.wait_for_timeout(700)
        await pg.click('.fav-star'); await pg.wait_for_timeout(450)
        stillOpen=await pg.evaluate("!!document.querySelector('.leaflet-popup')")
        check("10 popup stays open when starring", stillOpen)
        await pg.evaluate("mapref.closePopup()"); await pg.wait_for_timeout(250)
        await pg.evaluate("()=>{const i=Pref.findIndex(x=>/Canada Games/.test(x.n));focusRef(Mref[i],18);}"); await pg.wait_for_timeout(700)
        star=await pg.evaluate("(document.querySelector('.fav-star')||{}).textContent")
        check("10 star state survives reopen", star=='★', star)
        badge=await pg.inner_text('#favBadge')
        await pg.click('#favBtn'); await pg.wait_for_timeout(450)
        rows=await pg.evaluate("document.querySelectorAll('#favList .fav-item').length")
        check("16 badge matches list", str(badge)==str(rows), "%s vs %s"%(badge,rows))
        await pg.click('#favBtn'); await pg.wait_for_timeout(250)


        print("\n--- category model (round 4) ---")
        await pg.evaluate("resetAll()"); await pg.wait_for_timeout(500)
        check("04 no filter = empty set, everything shown",
              await pg.evaluate("aCref().size")==0 and await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)).length")==N)
        await pg.click('#catBtn'); await pg.wait_for_timeout(450)
        check("11 common groups open on arrival", await pg.evaluate("document.querySelectorAll('#catGrid .cat-group.open').length")>=3)
        # P2-G: unfiltered, the title now reads "263 places total" rather than the
        # uninformative "263 / 263" — str(N) survives in both the filtered (v/t) and
        # unfiltered (showingAll) phrasing, so this checks the count is there without
        # pinning down which of the two forms it is.
        check("10 panel title carries the live count on open", str(N) in await pg.inner_text('#panelTitle'))
        check("10 bottom button says Done, not a count", str(N) not in await pg.inner_text('#applyBtn'))
        picked=await pg.evaluate("""()=>{const c=[...document.querySelectorAll('#catGrid .cat-btn')].find(x=>x.textContent.includes('Dental'));if(c){c.click();return true;}return false;}""")
        await pg.wait_for_timeout(500)
        check("04 one click isolates that category",
              picked and await pg.evaluate("[...aCref()].join()")=='dental'
              and await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)).length")==3)
        check("panel stays open when a category is clicked",
              await pg.evaluate("document.getElementById('panel').classList.contains('open')"))
        await pg.evaluate("""()=>{const g=[...document.querySelectorAll('#catGrid .cat-group')].find(c=>/Health/.test(c.textContent));g.querySelector('.grp-check').click();}""")
        await pg.wait_for_timeout(500)
        check("05 group tick means 'show me these'", await pg.evaluate("aCref().size")>=4)
        await pg.click('#clearCat'); await pg.wait_for_timeout(450)
        check("07 the single utility clears the filter",
              await pg.evaluate("aCref().size")==0 and await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)).length")==N)
        await pg.click('#catBtn'); await pg.wait_for_timeout(200)
        await pg.click('#health'); await pg.wait_for_timeout(400)
        await pg.click('#catBtn'); await pg.wait_for_timeout(400)
        await pg.evaluate("""()=>{const c=[...document.querySelectorAll('#catGrid .cat-btn')].find(x=>x.textContent.includes('Dental'));c.click();}""")
        await pg.wait_for_timeout(450)
        check("08 preset keeps its highlight after a manual tweak",
              await pg.evaluate("document.getElementById('health').classList.contains('active')")
              and await pg.evaluate("document.getElementById('health').classList.contains('adjusted')"))
        await pg.click('#catBtn'); await pg.wait_for_timeout(200)

        print("\n--- reset and reporting (round 4) ---")
        await pg.evaluate("resetAll()"); await pg.wait_for_timeout(500)
        # P0-B: Reset used to stay on screen at all times, only dimmed (.idle) with
        # nothing to undo — a control that's always visible implies there's always
        # something to press. It is now genuinely absent (DOM `hidden`, so assistive
        # tech skips it too) exactly when every axis is at its default, and reappears
        # the moment any of area/category/theme/search/route actually changes.
        check("03 reset genuinely hidden when there is nothing to undo", await pg.evaluate("document.getElementById('resetBtn').hidden"))
        await pg.click('#busBtn'); await pg.wait_for_timeout(400)
        await pg.evaluate("document.querySelector('#busList .bus-item').click()"); await pg.wait_for_timeout(800)
        await pg.fill('#searchInput','bank'); await pg.wait_for_timeout(650)
        check("03 reset appears once state exists", not await pg.evaluate("document.getElementById('resetBtn').hidden"))
        await pg.click('#resetBtn'); await pg.wait_for_timeout(900)
        st=await pg.evaluate("""()=>({r:aRref().size,c:aCref().size,route:selRoute(),
            s:document.getElementById('searchInput').value,z:mapref.getZoom(),
            pop:!!document.querySelector('.leaflet-popup')})""")
        check("02 reset clears every kind of state including the route and the view",
              st['r']==7 and st['c']==0 and st['route'] is None and st['s']=='' and st['z']==12 and not st['pop'], st)
        await pg.evaluate("()=>{const i=Pref.findIndex(x=>/Riverside Park$/.test(x.n));mapref.setView([Pref[i].lat,Pref[i].lng],18);focusRef(Mref[i],18);}")
        await pg.wait_for_timeout(700)
        rep_href=await pg.evaluate("(document.querySelector('.pv-report')||{}).href||''")
        check("01 per-place report link carries id and version",
              rep_href.startswith('mailto:') and 'body=' in rep_href and len(rep_href)>150, len(rep_href))
        await pg.evaluate("mapref.closePopup()")

        print("\n--- CITY config (round 4) ---")
        import re as _re
        leaks=set()
        for _lg in ['en','fr','es','zh','ko','ja']:
            await pg.click('[data-lang="%s"]' % _lg); await pg.wait_for_timeout(320)
            await pg.click('#guideToggle'); await pg.wait_for_timeout(260)
            _g=await pg.inner_text('#guideBody'); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(160)
            leaks |= set(_re.findall(r'\{[A-Z_]+\}', await pg.inner_text('body')))
            leaks |= set(_re.findall(r'\{[A-Z_]+\}', _g))
        check("05 no unexpanded placeholders in any language", not leaks, leaks)
        await pg.evaluate("resetAll()"); await pg.wait_for_timeout(600)
        check("05 map centre comes from CITY",
              await pg.evaluate("JSON.stringify([+mapref.getCenter().lat.toFixed(3),+mapref.getCenter().lng.toFixed(3)])")==await pg.evaluate("JSON.stringify(CITYref.centre)"))
        await pg.click('[data-lang="en"]'); await pg.wait_for_timeout(300)

        print("\n--- accessibility ---")
        a=await pg.evaluate("""()=>{
          const sel='.lang-btn,.reg-btn,.cat-btn,.preset-chip,.grp-check,.grp-expand,.bus-item,.af-clear,.af-chip .x,.rt-name,.rt-remove,.panel-close,.search-clear,.note-toggle,.empty-btn,.cat-util-btn,.fav-star';
          // an element only has to BE a button if it is not already inside one
          // (a label span inside a button row is correct markup, not a defect)
          // the real invariant: anything that HANDLES a click must be a button.
          // A container whose children handle the clicks is correct as a div.
          const all=[...document.querySelectorAll(sel)]
            .filter(e=>!e.parentElement.closest('button'))
            .filter(e=>typeof e.onclick==='function');
          return {total:all.length, nonButton:all.filter(e=>!['BUTTON','A','INPUT'].includes(e.tagName)).length,
                  offenders:all.filter(e=>!['BUTTON','A','INPUT'].includes(e.tagName)).map(e=>e.tagName+'.'+e.className),
                  markerTab:[...document.querySelectorAll('.leaflet-marker-icon[tabindex]')].filter(e=>!e.querySelector('.kcluster')).length,
                  searchAria:!!document.getElementById('searchInput').getAttribute('aria-label')};}""")
        check("28 every control is a real button", a['nonButton']==0, a)
        check("42 individual markers out of the tab order", a['markerTab']==0)
        check("43 search field labelled", a['searchAria'])
        await pg.click('#guideToggle'); await pg.wait_for_timeout(400)
        inside=await pg.evaluate("document.getElementById('guideModal').contains(document.activeElement)")
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(350)
        closed=not await pg.evaluate("document.getElementById('guideBackdrop').classList.contains('open')")
        check("29 modal takes focus", inside)
        check("15 Escape closes the modal", closed)

        # 2026-09-07: 更新记录已按要求从页面移除（内容仍保留在仓库的 CHANGELOG.md），
        # 因此原本的两项 "36 change log ..." 断言一并删除——功能没了测试还留着，
        # 只会让套件崩在一个不存在的元素上。离线提示的断言保留在下面。
        print("\n--- offline notice ---")
        off=await pg.evaluate("""()=>{const e=document.getElementById('offlineNote');
          const before=document.getElementById('map').getBoundingClientRect().top;
          // Poking .hidden/.textContent directly (as this used to) bypasses the
          // auto-compact timer added for round 36c and can leave a stale .compact
          // class from an earlier, real tile failure earlier in this same page
          // session (this sandbox has no tile access, so the app's own offline
          // path fires for real during the suite) — asserting the zoom-clearance
          // geometry against that leftover state isn't what this check is for.
          // Going through the app's own show function is what every real caller
          // does, and resets state exactly the way a fresh trigger would.
          offlineShowExpanded();
          const after=document.getElementById('map').getBoundingClientRect().top;
          const s=getComputedStyle(e);
          const r=e.getBoundingClientRect(), z=document.querySelector('.leaflet-control-zoom').getBoundingClientRect();
          const clears = r.left >= z.right;
          document.getElementById('offlineClose').click();
          return {moved:after-before, pos:s.position, clears, hidden:e.hidden};}""")
        check("36 offline notice overlays the map instead of pushing it down",
              off['moved']==0 and off['pos']=='absolute', off)
        check("36 offline notice clears the zoom control", off['clears'])
        check("36 offline notice can be dismissed", off['hidden'])

        print("\n--- offline notice auto-compacts instead of blanketing the map (round 36c) ---")
        oc=await pg.evaluate("""()=>{
          offlineShowExpanded();
          const before=document.getElementById('offlineNote').getBoundingClientRect();
          document.getElementById('offlineNote').classList.add('compact');
          const c=document.getElementById('offlineNote').getBoundingClientRect();
          const z=document.querySelector('.leaflet-control-zoom').getBoundingClientRect();
          const attr=document.querySelector('.leaflet-control-attribution');
          const ar=attr?attr.getBoundingClientRect():null;
          const shrank = (c.width*c.height) < (before.width*before.height)*0.5;
          const clearsZoom = c.left>=z.right || c.top>=z.bottom;
          const clearsAttr = !ar || c.top>=ar.bottom || c.right<=ar.left;
          document.getElementById('offlineNote').click();
          const reopened = !document.getElementById('offlineNote').classList.contains('compact')
                            && !document.getElementById('offlineNote').hidden;
          document.getElementById('offlineClose').click();
          return {shrank, clearsZoom, clearsAttr, reopened,
                  before:{w:before.width,h:before.height}, compact:{w:c.width,h:c.height}};}""")
        check("36c compact badge is meaningfully smaller than the full notice", oc['shrank'], oc)
        check("36c compact badge still clears the zoom control", oc['clearsZoom'])
        check("36c compact badge doesn't sit on the attribution link", oc['clearsAttr'])
        check("36c tapping the compact badge re-expands the full notice", oc['reopened'])

        print("\n--- provenance ---")
        pr=await pg.evaluate("""()=>{const c={};Pref.forEach(p=>{c[p.src||'missing']=(c[p.src||'missing']||0)+1;});
          const bad=Pref.filter(p=>p.src==='official'&&!p.w).length;
          return {c,bad};}""")
        check("37 every record declares a source", ('missing' not in pr['c']), pr['c'])
        check("37 no official claim without a link to check it", pr['bad']==0)
        chip=await pg.evaluate("""()=>{const out={};
          ['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);
            const i=Pref.findIndex(x=>x.src==='official');
            const h=popup(Pref[i],i);
            const j=Pref.findIndex(x=>x.src==='places');
            const h2=popup(Pref[j],j);
            out[l]=[h.indexOf('src-official')>-1&&h.indexOf(UI[l].srcOfficial)>-1,
                    h2.indexOf('src-places')>-1&&h2.indexOf(UI[l].srcPlaces)>-1];});
          setLang('en');return out;}""")
        check("37 source chip renders in every language",
              all(a and b for a,b in chip.values()), chip)

        print("\n--- popup vs map chrome ---")
        pc=await pg.evaluate("""()=>{const i=Pref.findIndex(x=>x.src==='places');
          focusRef(Mref[i],16);return i;}""")
        await pg.wait_for_timeout(1200)
        geo=await pg.evaluate("""()=>{const pu=document.querySelector('.leaflet-popup');
          const z=document.querySelector('.leaflet-control-zoom');
          const zr=z&&getComputedStyle(z).display!=='none'?z.getBoundingClientRect():null;
          const r=pu.getBoundingClientRect();
          return {left:r.left,right:r.right,iw:innerWidth,zoomShown:!!zr,zr:zr?zr.right:null};}""")
        check("38 popup clears the zoom control on a wide screen",
              (not geo['zoomShown']) or geo['left']>=geo['zr']-1, geo)
        check("38 popup stays inside the viewport", geo['right']<=geo['iw']+1, geo)
        await pg.evaluate("mapref.closePopup()")

        print("\n--- modal vs Leaflet chrome (round 6) ---")
        # #noteToggle carries `hidden` (2026-09-08, feature paused at the user's
        # request) so it can no longer be clicked — the modal and #noteBody's
        # content are still fully wired up underneath, so this opens it the same
        # way the hidden button used to, keeping the coverage this round exists for.
        await pg.evaluate("()=>{trackEvent('note_open',{});openModal(document.getElementById('noteBackdrop'));}")
        await pg.wait_for_timeout(500)
        z0=await pg.evaluate("mapref.getZoom()")
        hit=await pg.evaluate("""()=>{const out={};
          [['zoom','.leaflet-control-zoom'],['attr','.leaflet-control-attribution']].forEach(([k,sel])=>{
            const el=document.querySelector(sel);
            if(!el||getComputedStyle(el).display==='none'){out[k]='hidden';return;}
            const r=el.getBoundingClientRect();
            const t=document.elementFromPoint(Math.round(r.left+r.width/2),Math.round(r.top+r.height/2));
            out[k]=t?(t.id||(typeof t.className==='string'?t.className:t.tagName)):'none';});
          return out;}""")
        check("39 modal covers Leaflet's controls", hit['zoom'] in ('noteBackdrop','hidden') and hit['attr']=='noteBackdrop', hit)
        try:
            await pg.click('.leaflet-control-zoom-in', timeout=1200); punched=True
        except Exception: punched=False
        await pg.wait_for_timeout(300)
        check("39 zoom is not clickable through the modal",
              (not punched) and await pg.evaluate("mapref.getZoom()")==z0)
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)

        print("\n--- URL params reject prototype keys (round 6) ---")
        for q in ['lang=constructor','c=constructor','r=toString','route=constructor']:
            pgx=await b.new_page(viewport={'width':1100,'height':800})
            ex=[]; pgx.on('pageerror', lambda e: ex.append(str(e)))
            await pgx.goto(URL+'?'+q); await pgx.wait_for_timeout(1400)
            st=await pgx.evaluate("()=>({h1:document.getElementById('h1').textContent,vis:Mref.filter(m=>markerHome().hasLayer(m)).length,route:selRoute()})")
            check("40 ?%s does not break the page"%q,
                  len(ex)==0 and len(st['h1'])>0 and st['vis']==N and st['route'] is None,
                  dict(st, err=ex[:1]))
            await pgx.close()

        print("\n--- attribution, privacy, no third-party font (round 6) ---")
        at=await pg.evaluate("()=>document.querySelector('.leaflet-control-attribution').innerHTML")
        check("41 OSM attribution names contributors and links the licence",
              'contributors' in at and 'openstreetmap.org/copyright' in at)
        check("41 no external font request",
              await pg.evaluate("()=>!document.querySelector('link[href*=\"fonts.\"]')"))
        priv=await pg.evaluate("""()=>{const o={};['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);
          o[l]=document.getElementById('noteBody').innerText.indexOf(UI[l].privacyNote.replace(/<[^>]+>/g,'').slice(2,18))>-1;});
          setLang('en');return o;}""")
        check("41 privacy disclosure renders in all six languages", all(priv.values()), priv)

        print("\n--- contrast and the favourite star's state (round 6) ---")
        op=await pg.evaluate("""()=>{const out={};
          [['pv','.pv'],['cnt','.cat-btn .cnt'],['fhint','.fhint'],['lic','.licence-line'],
           ['reset','.reset-btn.idle']].forEach(([k,s])=>{
            const e=document.querySelector(s); out[k]=e?+getComputedStyle(e).opacity:null;});
          return out;}""")
        check("42 no opacity dimming small text below AA", all(v is None or v==1 for v in op.values()), op)
        check("42 every external link carries rel=noopener",
              await pg.evaluate("()=>[...document.querySelectorAll('a[target=_blank]')].filter(a=>!a.rel.includes('noopener')).length")==0)
        await pg.evaluate("()=>{focusRef(Mref[3],16);}"); await pg.wait_for_timeout(900)
        s0=await pg.evaluate("()=>{const s=document.querySelector('.fav-star');return [s.getAttribute('aria-pressed'),s.getAttribute('aria-label')];}")
        await pg.click('.fav-star'); await pg.wait_for_timeout(400)
        s1=await pg.evaluate("()=>{const s=document.querySelector('.fav-star');return [s.getAttribute('aria-pressed'),s.getAttribute('aria-label')];}")
        check("42 star exposes and flips aria-pressed", s0[0]=='false' and s1[0]=='true' and s0[1]!=s1[1], [s0,s1])
        await pg.click('.fav-star'); await pg.wait_for_timeout(300); await pg.evaluate("mapref.closePopup()")

        print("\n--- data honesty (round 7) ---")
        dh=await pg.evaluate("""()=>{
          const OA=CITYref.openAir;
          return {n:Pref.length,
            claims24:Pref.filter(p=>OA.indexOf(p.c)>=0&&p.h&&p.h.a).map(p=>p.n),
            zhAddr:Pref.filter(p=>/[\\u4e00-\\u9fff]/.test(p.a||'')).map(p=>p.n),
            oldTerm:Pref.filter(p=>p.note&&/新移民/.test(p.note.zh||'')).map(p=>p.n),
            immigrant:Pref.filter(p=>/Immigrant Services/.test(p.n)).length};}""")
        check("44 no open-air place claims 24-hour opening", len(dh['claims24'])==0, dh['claims24'][:3])
        check("44 no Chinese in any address field", len(dh['zhAddr'])==0, dh['zhAddr'][:3])
        check("44 house wording 新居民 used throughout", len(dh['oldTerm'])==0, dh['oldTerm'][:3])
        check("44 the duplicated agency appears exactly once", dh['immigrant']==1, dh['immigrant'])
        oa=await pg.evaluate("""()=>{const o={};['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);
          const p=Pref.find(x=>x.n==='Riverside Park');
          o[l]=popup(p,Pref.indexOf(p)).indexOf(UI[l].hOnSite)>-1;});setLang('en');return o;}""")
        check("44 open-air places say 'hours posted on site' in all six languages", all(oa.values()), oa)

        print("\n--- favourites survive a wiped browser (round 7) ---")
        await pg.evaluate("()=>{localStorage.clear();favRef().clear();updateFavBadge();}")
        ids=await pg.evaluate("()=>{const g=[];[0,5,9].forEach(i=>{favRef().add(Pref[i].id);g.push(Pref[i].id);});saveFavorites();updateFavBadge();return g;}")
        await pg.click('#favBtn'); await pg.wait_for_timeout(500)
        await pg.click('#favExport'); await pg.wait_for_timeout(400)
        code=await pg.evaluate("()=>document.getElementById('favCode').value")
        check("45 export covers every starred place", all(i in code for i in ids), code)
        await pg.evaluate("()=>localStorage.clear()")
        await pg.reload(); await pg.wait_for_timeout(1600)
        await pg.click('#favBtn'); await pg.wait_for_timeout(500)
        await pg.fill('#favCode', code)
        await pg.click('#favImport'); await pg.wait_for_timeout(600)
        check("45 a wiped browser restores from the code",
              await pg.evaluate("()=>favRef().size")==3
              and await pg.evaluate("()=>document.getElementById('favBadge').textContent")=='3'
              and await pg.evaluate("()=>document.querySelectorAll('#favList .fav-item').length")==3)
        await pg.fill('#favCode','not a code'); await pg.click('#favImport'); await pg.wait_for_timeout(400)
        check("45 junk input is refused without losing what is stored",
              await pg.evaluate("()=>favRef().size")==3
              and len(await pg.evaluate("()=>document.getElementById('favIOMsg').textContent"))>0)
        await pg.evaluate("()=>{localStorage.clear();favRef().clear();saveFavorites();updateFavBadge();}")
        await pg.click('#favBtn'); await pg.wait_for_timeout(300)

        print("\n--- layout with a finger, not a mouse (round 7) ---")
        # Comfortable targets cost vertical space; without this pass the sweep above
        # measures a page nobody actually holds.
        tprobs=[]
        for w,h in [(320,568),(360,640),(390,760),(430,760)]:
            for lang in ['en','fr','es','zh','ko','ja']:
                pgc=await b.new_page(viewport={'width':w,'height':h}, has_touch=True, is_mobile=True)
                pgc.on('pageerror', lambda e: allerrs.append(str(e)))
                await pgc.goto(URL); await pgc.wait_for_timeout(900)
                await pgc.click('[data-lang="%s"]'%lang); await pgc.wait_for_timeout(250)
                r=await pgc.evaluate(TOUCH_PROBE)
                tag='%s@%dx%d'%(lang,w,h)
                floor = 33 if (w <= 340 and h <= 600) else 40
                if r['share']<floor: tprobs.append(tag+' map %d%% (floor %d)'%(r['share'],floor))
                if r['ov']>0: tprobs.append(tag+' overflow %dpx'%r['ov'])
                if r['small']: tprobs.append(tag+' targets under 36px: '+str(r['small'][:2]))
                await pgc.close()
        check("47 touch layout: map keeps its share, nothing overflows, targets stay tappable",
              len(tprobs)==0, tprobs[:4])

        print("\n--- touch targets (round 7) ---")
        pgt=await b.new_page(viewport={'width':390,'height':760}, has_touch=True, is_mobile=True)
        await pgt.goto(URL); await pgt.wait_for_timeout(1500)
        tt=await pgt.evaluate("""()=>{const out=[];
          document.querySelectorAll('button,a[href]').forEach(e=>{
            const s=getComputedStyle(e);
            if(s.display==='none'||s.display==='inline')return;   // inline-in-text is exempt
            const r=e.getBoundingClientRect(); if(!r.width)return;
            if(Math.min(r.width,r.height)<44)out.push((e.id||e.className||e.tagName).toString().slice(0,22));});
          return [...new Set(out)];}""")
        check("46 at a normal phone size every non-inline control is at least 44px", len(tt)==0, tt)
        check("46 enlarging them introduced no overflow",
              await pgt.evaluate("document.body.scrollWidth-innerWidth")<=0)
        await pgt.close()

        print("\n--- taxonomy and translation (round 8) ---")
        tx=await pg.evaluate("""()=>{const c={};Pref.forEach(p=>{c[p.c]=(c[p.c]||0)+1;});
          return {apt:c.apt,propmgmt:c.propmgmt,gov:c.gov,commctr:c.commctr,
                  emoji:Pref.filter(p=>/^🏢/.test(p.n)).length,
                  labels:['zh','en','fr','es','ko','ja'].every(l=>!!CIref.propmgmt[l])};}""")
        check("48 letting agents are their own category, not padding the apartment count",
              tx['apt']==14 and tx['propmgmt']==4 and tx['emoji']==0, tx)
        check("48 the new category is labelled in every language", tx['labels'])
        # 2026-09-07: commctr 从 2 变 3 —— Westsyde Community Hall 原本用了 CI 里
        # 不存在的分类 key 'community'（正是让整页文案空白的崩溃源），现按 DATA-SCHEMA
        # 「礼堂属于 commctr」的既有定义归入社区中心。边界规则未变，只是数量对上了。
        # 2026-09-08: commctr 3 → 4 (Volunteer Kamloops). The invariant this check
        # exists for is the boundary — a community organisation is not a government
        # office — so gov stays pinned and commctr is only ever allowed to grow.
        check("49 the community centre is not filed under government",
              tx['gov']==4 and tx['commctr']>=4, [tx['gov'],tx['commctr']])
        await pg.evaluate("(()=>{aCref().clear();aCref().add('propmgmt');renderCats();apply();})()")
        await pg.wait_for_timeout(600)
        check("48 the new category filters like any other",
              await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)).length")==4)
        await pg.evaluate("(()=>{aCref().clear();renderCats();apply();})()"); await pg.wait_for_timeout(400)

        nt=await pg.evaluate("""()=>{const w=Pref.filter(p=>p.note);
          return {n:w.length,
            five:w.filter(p=>['zh','en','fr','es','ko','ja'].every(l=>p.note[l])).length,
            copiedFromEn:w.filter(p=>p.note.fr===p.note.en||p.note.es===p.note.en||p.note.ko===p.note.en).length};}""")
        check("50 every place note exists in all six languages", nt['n']==nt['five'], nt)
        check("50 no translation is just the English text again", nt['copiedFromEn']==0, nt)
        korean=await pg.evaluate("""()=>{setLang('ko');
          const p=Pref.find(x=>x.n==='Riverside Park');
          const h=popup(p,Pref.indexOf(p)); setLang('en');
          return {ko:/[\\uac00-\\ud7af]/.test(h), enLeak:h.indexOf('The most popular park')>-1};}""")
        check("50 a Korean reader gets Korean, not the English fallback",
              korean['ko'] and not korean['enLeak'], korean)

        print("\n--- the tallest popup, every size and language (round 8) ---")
        # French and Spanish run longer than English, so the worst case is a
        # translated note on the smallest screen. A popup taller than the map cannot
        # satisfy Leaflet's autoPan: it panned forever and closed itself ~300ms after
        # opening, which is why maxHeight is measured from the map, not the viewport.
        pprobs=[]
        for w,h in [(320,568),(360,640),(390,760),(1280,900)]:
            for lang in ['en','fr','es','zh','ko','ja']:
                pgp=await b.new_page(viewport={'width':w,'height':h},
                                     has_touch=(w<600), is_mobile=(w<600))
                pgp.on('pageerror', lambda e: allerrs.append(str(e)))
                await pgp.goto(URL)
                await pgp.wait_for_function('()=>window.Mref&&Mref.length>200', timeout=20000)
                await pgp.wait_for_timeout(400)
                await pgp.click('[data-lang="%s"]'%lang); await pgp.wait_for_timeout(250)
                r=await pgp.evaluate(TALL_POPUP_PROBE)
                tag='%s@%dx%d'%(lang,w,h)
                if r.get('none'): pprobs.append(tag+' popup never opened')
                elif not r['stillOpen']: pprobs.append(tag+' popup closed itself')
                elif r['overRight']>1 or r['overLeft']>1 or r['aboveMap']>1:
                    pprobs.append(tag+' '+str(r))
                elif not (r['nameVisible'] and r['actionVisible']):
                    pprobs.append(tag+' name or actions out of reach')
                await pgp.close()
        check("51 the longest note fits every screen without hiding the name or actions",
              len(pprobs)==0, pprobs[:3])

        print("\n--- button chrome ---")
        await pg.evaluate("(()=>{aCref().clear();aCref().add('bank');aRref().clear();aRref().add('ns');renderRegs();renderCats();apply();})()")
        await pg.wait_for_timeout(400); await pg.click('#favBtn'); await pg.wait_for_timeout(450)
        ch=await pg.evaluate("""()=>{const bad=[];
          ['af-clear','rt-name','cat-util-btn','lang-btn','preset-chip'].forEach(c=>{
            const e=document.querySelector('.'+c); if(!e)return;
            const s=getComputedStyle(e);
            if(s.borderStyle==='outset'||s.backgroundColor==='rgb(239, 239, 239)')bad.push(c);});
          return bad;}""")
        check("16/17 no default button chrome anywhere", len(ch)==0, ch)
        await pg.click('#favBtn'); await pg.wait_for_timeout(200)
        await pg.close()

        print("\n--- layout / overflow across languages and widths ---")
        probs=[]
        for lang in ['en','fr','es','zh','ko','ja']:
            for w,h in [(1440,900),(1280,900),(1200,800),(1024,800),(900,800),(768,800),(600,800),(430,760),(390,664),(360,640),(340,640),(320,568)]:
                pg2=await b.new_page(viewport={'width':w,'height':h})
                pg2.on('pageerror', lambda e: allerrs.append(str(e)))
                await pg2.goto(URL); await pg2.wait_for_timeout(750)
                await pg2.click('[data-lang="%s"]'%lang); await pg2.wait_for_timeout(250)
                m=await pg2.evaluate("""()=>{const mp=document.getElementById('map').getBoundingClientRect();
                  return {ov:document.body.scrollWidth-innerWidth,
                          mapShare:Math.round(100*(Math.min(mp.bottom,innerHeight)-Math.max(mp.top,0))/innerHeight)};}""")
                if m['ov']>0: probs.append("%s@%d overflow %dpx"%(lang,w,m['ov']))
                # 40% of the viewport for the map, except on a screen that is both
                # very narrow and very short (320x568, an iPhone SE) where eight rows
                # of necessary chrome in a long-worded language cannot fit above it.
                floor = 33 if (w <= 340 and h <= 600) else 40
                if w<=430 and m['mapShare']<floor:
                    probs.append("%s@%dx%d map only %d%% (floor %d)"%(lang,w,h,m['mapShare'],floor))
                # A popup that runs off the edge, or sits under the zoom control,
                # hides the place name — check it at every width, in every language.
                pp=await pg2.evaluate("""async()=>{const i=Pref.findIndex(x=>x.src==='places');
                  focusRef(Mref[i],16);
                  await new Promise(r=>setTimeout(r,900));
                  const pu=document.querySelector('.leaflet-popup');
                  if(!pu)return null;
                  const z=document.querySelector('.leaflet-control-zoom');
                  const shown=z&&getComputedStyle(z).display!=='none';
                  const r=pu.getBoundingClientRect();
                  return {l:r.left,r:r.right,iw:innerWidth,
                          zr:shown?z.getBoundingClientRect().right:null};}""")
                if pp:
                    if pp['r']>pp['iw']+1: probs.append("%s@%d popup off the right edge"%(lang,w))
                    if pp['zr'] is not None and pp['l']<pp['zr']-1:
                        probs.append("%s@%d popup under the zoom control"%(lang,w))
                await pg2.close()
        check("18/26 no overflow, map keeps a usable share", len(probs)==0, probs[:4])

        print("\n--- full walkthrough in each language ---")
        for lang in ['en','fr','es','zh','ko','ja']:
            pg3=await b.new_page(viewport={'width':1280,'height':900})
            errs=[]; pg3.on('pageerror', lambda e: errs.append(str(e)))
            await pg3.goto(URL); await pg3.wait_for_timeout(1500)
            await pg3.click('[data-lang="%s"]'%lang); await pg3.wait_for_timeout(350)
            for bid in ['#areaBtn','#areaBtn','#catBtn','#catBtn','#busBtn','#busBtn','#favBtn','#favBtn']:
                await pg3.click(bid); await pg3.wait_for_timeout(150)
            await pg3.click('#guideToggle'); await pg3.wait_for_timeout(250); await pg3.keyboard.press('Escape')
            # #noteToggle is hidden (2026-09-08); open the same modal programmatically
            # so this walkthrough still exercises it per language.
            await pg3.evaluate("()=>{trackEvent('note_open',{});openModal(document.getElementById('noteBackdrop'));}")
            await pg3.wait_for_timeout(250); await pg3.keyboard.press('Escape')
            await pg3.click('#kids'); await pg3.wait_for_timeout(350)
            await pg3.click('#resetBtn'); await pg3.wait_for_timeout(300)
            await pg3.fill('#searchInput','park'); await pg3.wait_for_timeout(600)
            await pg3.click('#searchClear'); await pg3.wait_for_timeout(350)
            await pg3.evaluate("()=>{focusRef(Mref[0],17);}"); await pg3.wait_for_timeout(500)
            title=await pg3.title()
            check("%s walkthrough clean"%lang, len(errs)==0, errs[:2])
            check("%s title localised"%lang, len(title)>0)
            allerrs+=errs
            await pg3.close()

        print("\n--- swipe to dismiss (round 6) ---")
        pgd=await b.new_page(viewport={'width':390,'height':760}, has_touch=True)
        ed=[]; pgd.on('pageerror', lambda e: ed.append(str(e)))
        await pgd.goto(URL); await pgd.wait_for_timeout(1500)
        await pgd.click('#catBtn'); await pgd.wait_for_timeout(600)
        gb=await pgd.evaluate("()=>{const r=document.getElementById('panelGrab').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,h:Math.round(r.height)};}")
        check("43 grab area is thumb-sized", gb['h']>=20, gb)
        await pgd.mouse.move(gb['x'],gb['y']); await pgd.mouse.down()
        await pgd.mouse.move(gb['x'],gb['y']+40,steps=6); await pgd.wait_for_timeout(120)
        moved=await pgd.evaluate("getComputedStyle(document.getElementById('panel')).transform")
        await pgd.mouse.move(gb['x'],gb['y']+18,steps=4); await pgd.mouse.up(); await pgd.wait_for_timeout(450)
        check("43 a short drag follows the finger then springs back",
              moved!='none' and await pgd.evaluate("document.getElementById('backdrop').classList.contains('open')")
              and await pgd.evaluate("document.getElementById('panel').style.transform")=='')
        gb=await pgd.evaluate("()=>{const r=document.getElementById('panelGrab').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2};}")
        await pgd.mouse.move(gb['x'],gb['y']); await pgd.mouse.down()
        await pgd.mouse.move(gb['x'],gb['y']+140,steps=8); await pgd.mouse.up(); await pgd.wait_for_timeout(450)
        check("43 a long drag dismisses the sheet and clears the transform",
              (not await pgd.evaluate("document.getElementById('backdrop').classList.contains('open')"))
              and await pgd.evaluate("document.getElementById('panel').style.transform")=='')
        check("43 no page errors from the gesture", len(ed)==0, ed[:2])
        await pgd.close()
        pge=await b.new_page(viewport={'width':1280,'height':900})
        await pge.goto(URL); await pge.wait_for_timeout(1300)
        await pge.click('#catBtn'); await pge.wait_for_timeout(450)
        check("43 the grab area never appears on desktop",
              await pge.evaluate("getComputedStyle(document.getElementById('panelGrab')).display")=='none')
        await pge.close()

        print("\n--- themes: the overlapping axis (round 9) ---")
        pgt=await b.new_page(viewport={'width':420,'height':820})
        et=[]; pgt.on('pageerror', lambda e: et.append(str(e)))
        await pgt.goto(URL); await pgt.wait_for_timeout(1300)
        await pgt.click('#catBtn'); await pgt.wait_for_timeout(420)
        nchips=await pgt.locator('.theme-btn').count()
        check("52 every theme has a chip", nchips==await pgt.evaluate("TORDER.length"), nchips)
        # A theme that can only ever show (0) is a chip that wastes a tap; one that
        # matches everything is not a filter. Both are data faults, not UI faults,
        # so the check is on the counts rather than on the markup.
        spread=await pgt.evaluate("()=>TORDER.map(k=>P.filter(p=>p.t&&p.t.indexOf(k)>=0).length)")
        check("52 no theme is empty and none swallows the whole map",
              min(spread)>0 and max(spread)<await pgt.evaluate("P.length"), spread)
        total=await pgt.evaluate("()=>lastVisible")
        # Themes narrow. Two of them narrow further. That is the promise the panel
        # hint makes in five languages, and it is the one thing that must not drift.
        await pgt.evaluate("()=>{aT=new Set(['free']);renderThemes();renderCats();apply();}")
        await pgt.wait_for_timeout(300); v1=await pgt.evaluate("()=>lastVisible")
        await pgt.evaluate("()=>{aT=new Set(['free','indoor']);renderThemes();renderCats();apply();}")
        await pgt.wait_for_timeout(300); v2=await pgt.evaluate("()=>lastVisible")
        check("52 one theme narrows, two narrow further (AND, not OR)",
              0<v2<=v1<total, [total,v1,v2])
        check("52 the chip count matches what ticking it actually yields",
              await pgt.evaluate("()=>themeCount('indoor')")==v2, v2)
        check("52 the Category badge counts themes too, so a theme filter is never invisible",
              await pgt.inner_text('#catBadge')=='2', await pgt.inner_text('#catBadge'))
        check("52 themes ride in the shareable URL", 't=free' in pgt.url, pgt.url[-60:])
        await pgt.click('#applyBtn'); await pgt.wait_for_timeout(280)
        check("52 each theme gets its own removable chip",
              await pgt.locator('#activeFilters .af-chip').count()>=2)
        await pgt.click('#resetBtn'); await pgt.wait_for_timeout(420)
        check("52 Reset clears themes as well as areas and categories",
              await pgt.evaluate("()=>aT.size")==0 and await pgt.evaluate("()=>lastVisible")==total)
        # Themes are read in the reading language everywhere they appear.
        tl=await pgt.evaluate("""()=>{const o={};['zh','en','fr','es','ko','ja'].forEach(l=>{
            o[l]=TORDER.every(k=>TI[k][l]&&TI[k][l].length>1);});return o;}""")
        check("52 every theme is labelled in all six languages", all(tl.values()), tl)
        await pgt.evaluate("()=>setLang('zh')"); await pgt.wait_for_timeout(250)
        await pgt.fill('#searchInput','亲子'); await pgt.wait_for_timeout(700)
        check("52 searching a theme name in the reading language finds its places",
              await pgt.evaluate("()=>lastVisible")>5, await pgt.evaluate("()=>lastVisible"))
        await pgt.fill('#searchInput',''); await pgt.wait_for_timeout(400)
        # Discovery: a reader who never opens the filter panel still meets the axis.
        await pgt.evaluate("()=>{const i=P.findIndex(p=>p.t&&p.t.length>2);focusMarker(M[i],15);}")
        await pgt.wait_for_timeout(900)
        check("52 a place's themes are visible in its popup",
              await pgt.locator('.leaflet-popup .pv-theme').count()>2)
        check("52 no page errors from the theme axis", len(et)==0, et[:2])
        await pgt.close()

        print("\n--- honest coordinates and co-located places (round 9) ---")
        pgh=await b.new_page(viewport={'width':420,'height':820})
        eh=[]; pgh.on('pageerror', lambda e: eh.append(str(e)))
        await pgh.goto(URL); await pgh.wait_for_timeout(1300)
        # precision and sameComplex both sat in the data for weeks with no renderer,
        # so a 100 m-off pin looked as confident as a surveyed one and two markers on
        # one coordinate looked like duplicate data. Both must stay visible.
        pr=await pgh.evaluate("""()=>{const i=P.findIndex(p=>p.precision==='low');
            return i<0?null:{i:i,html:popup(P[i],i)};}""")
        check("53 an approximate pin says so in its popup",
              bool(pr) and 'pv-approx' in pr['html'], bool(pr))
        sc=await pgh.evaluate("""()=>{const i=P.findIndex(p=>p.sameComplex&&p.sameComplex.length);
            if(i<0)return null;const h=popup(P[i],i);
            return {ok:h.indexOf(UI[L_].sameComplexLabel)>-1,
                    named:P[i].sameComplex.every(id=>h.indexOf((P.find(x=>x.id===id)||{}).n)>-1)};}""")
        check("53 two markers on one coordinate name each other instead of looking duplicated",
              sc and sc['ok'] and sc['named'], sc)
        for l in ('zh','en','fr','es','ko','ja'):
            await pgh.evaluate("l=>setLang(l)", l)
            ok=await pgh.evaluate("""()=>{const i=P.findIndex(p=>p.precision==='low');
                return popup(P[i],i).indexOf(UI[L_].lowPrecision)>-1;}""")
            check("53 the approximate-pin caveat is translated (%s)"%l, ok)
        check("53 no page errors", len(eh)==0, eh[:2])
        await pgh.close()

        print("\n--- the guide, now long enough to need an index (round 9) ---")
        pgg=await b.new_page(viewport={'width':420,'height':820})
        eg=[]; pgg.on('pageerror', lambda e: eg.append(str(e)))
        await pgg.goto(URL); await pgg.wait_for_timeout(1300)
        for l in ('zh','en','fr','es','ko','ja'):
            await pgg.evaluate("l=>setLang(l)", l)
            await pgg.wait_for_timeout(220)
            g=await pgg.evaluate("""()=>{const b=document.getElementById('guideBody');
                return {chars:b.innerText.length,h3:b.querySelectorAll('h3').length,
                        toc:b.querySelectorAll('.guide-toc-btn').length,
                        ph:/\{(CITY|PROV|SD|SD_URL|TRANSIT|DATE|CONTACT|LIC)/.test(b.innerText)};}""")
            # One index entry per section, in every language: the index is generated
            # from the headings, so a tier that gains a section must gain an entry.
            check("54 guide index matches its headings (%s)"%l, g['h3']==g['toc'] and g['toc']>=20, g)
            check("54 no unexpanded {PLACEHOLDER} reaches the reader (%s)"%l, not g['ph'], g)
            check("54 the guide is substantial in every language (%s)"%l, g['chars']>8000, g['chars'])
        await pgg.click('#guideToggle'); await pgg.wait_for_timeout(400)
        await pgg.click('.guide-toc-btn:nth-child(6)'); await pgg.wait_for_timeout(600)
        check("54 an index entry scrolls to and marks its section",
              await pgg.evaluate("()=>{const e=document.querySelector('.gs-flash');return !!(e&&e.textContent);}"))
        check("54 no page errors from the guide", len(eg)==0, eg[:2])
        await pgg.close()

        print("\n--- telemetry says what it claims to (round 10) ---")
        pgm=await b.new_page(viewport={'width':420,'height':820})
        em=[]; pgm.on('pageerror', lambda e: em.append(str(e)))
        await pgm.goto(URL); await pgm.wait_for_timeout(1400)
        buf=lambda: pgm.evaluate("()=>_evBuf.map(e=>({t:e.t,p:e.p}))")
        evs=await buf()
        ss=[e['p'] for e in evs if e['t']=='session_start']
        check("55 session_start segments by layout, install and deep link",
              ss and all(k in ss[0] for k in ('dev','pwa','deep','ver','lang','ref')), ss[0] if ss else None)
        # The guide is the largest thing in the project and had no open event at
        # all, so "does anyone read it" was unanswerable.
        await pgm.click('#guideToggle'); await pgm.wait_for_timeout(1300)
        await pgm.keyboard.press('Escape'); await pgm.wait_for_timeout(400)
        evs=await buf()
        gc=[e['p'] for e in evs if e['t']=='guide_close']
        check("55 the guide records being opened and how long it was read",
              len([e for e in evs if e['t']=='guide_open'])==1 and gc and gc[0].get('ms',0)>700, gc)
        # Logging per debounced keystroke made the top-searches ranking a ranking
        # of prefixes of real queries.
        before=len([e for e in await buf() if e['t']=='search_run'])
        for ch in 'library':
            await pgm.type('#searchInput',ch); await pgm.wait_for_timeout(300)
        await pgm.wait_for_timeout(1500)
        sr=[e for e in await buf() if e['t']=='search_run']
        check("55 one settled query logs one row, not one per keystroke",
              len(sr)-before==1, [e['p'] for e in sr[before:]])
        check("55 a logged search carries the result count it produced",
              sr and 'n' in sr[-1]['p'], sr[-1]['p'] if sr else None)
        # The sanitiser was keyed on the event name, so the one event whose whole
        # purpose is recording typed text shipped it raw.
        await pgm.fill('#searchInput',''); await pgm.wait_for_timeout(250)
        await pgm.fill('#searchInput','604 555 1212 qqzz'); await pgm.wait_for_timeout(1700)
        se=[e for e in await buf() if e['t']=='search_empty']
        check("55 every event carrying a typed query strips digit runs first",
              se and not re.search(r'\d{3,}', se[-1]['p'].get('q','')), se[-1]['p'] if se else None)
        check("55 no page errors from telemetry", len(em)==0, em[:2])
        await pgm.close()

        print("\n--- five languages, five sets of conventions (round 10) ---")
        pgl=await b.new_page(viewport={'width':430,'height':900})
        el=[]; pgl.on('pageerror', lambda e: el.append(str(e)))
        await pgl.goto(URL); await pgl.wait_for_timeout(1400)
        # Every language button must carry the language it switches to and a name
        # in that language. Two of the five were self-describing only because
        # their scripts happen to be distinctive; that is not a standard.
        lb=await pgl.evaluate("""()=>[...document.querySelectorAll('.lang-btn')].map(b=>
            ({k:b.dataset.lang,lang:b.getAttribute('lang'),al:b.getAttribute('aria-label'),ti:b.getAttribute('title')}))""")
        check("56 every language button declares its own language and name",
              len(lb)==6 and all(x['lang'] and x['al'] and x['ti'] for x in lb), lb)
        # A closed-day list and a bracketed count used CJK punctuation inline, so
        # English readers were shown "Closed: Tue、Thu、Sun" and "Route 1（31 stops）".
        HOURS={"r":[[1,1,540,1020,0],[3,3,540,1020,0],[5,6,540,1020,0]]}
        for lang,bad in (('en','、'),('fr','、'),('es','、'),('ko','、')):
            await pgl.evaluate("l=>setLang(l)", lang); await pgl.wait_for_timeout(200)
            txt=await pgl.evaluate("([h,l])=>fmtHours(h,l)", [HOURS,lang])
            check("56 %s uses its own list separator, not the ideographic comma"%lang,
                  bad not in txt, txt[-40:])
        await pgl.evaluate("l=>setLang(l)", 'zh'); await pgl.wait_for_timeout(200)
        zh=await pgl.evaluate("([h,l])=>fmtHours(h,l)", [HOURS,'zh'])
        check("56 zh keeps the ideographic comma, which is correct there", '、' in zh, zh[-30:])
        await pgl.evaluate("l=>setLang(l)", 'ja'); await pgl.wait_for_timeout(200)
        ja=await pgl.evaluate("([h,l])=>fmtHours(h,l)", [HOURS,'ja'])
        check("56 ja also uses the ideographic comma, a deliberate match with zh", '、' in ja, ja[-30:])
        ko=await pgl.evaluate("()=>UI.ko.colon")
        check("56 ko sets a Korean colon, not the Chinese full-width one", ko.strip()==':', repr(ko))
        ja_colon=await pgl.evaluate("()=>UI.ja.colon")
        check("56 ja sets a half-width colon, not the Chinese full-width one", ja_colon.strip()==':', repr(ja_colon))
        for lang in ('en','fr','es','ko'):
            await pgl.evaluate("l=>setLang(l)", lang); await pgl.wait_for_timeout(150)
            await pgl.evaluate("()=>renderRoute(Object.keys(BR)[0],false)"); await pgl.wait_for_timeout(300)
            ind=await pgl.inner_text('#busIndicator')
            check("56 %s brackets the stop count in its own punctuation"%lang,
                  '（' not in ind and '）' not in ind, ind.replace('\n',' ')[:60])
            await pgl.evaluate("()=>renderRoute(null,false)"); await pgl.wait_for_timeout(120)
        tags={}
        for lang in ('en','fr','es','zh','ko','ja'):
            await pgl.evaluate("l=>setLang(l)", lang); await pgl.wait_for_timeout(150)
            tags[lang]=await pgl.evaluate("()=>document.documentElement.lang")
        check("56 the document declares the locale actually written",
              tags['en']=='en-CA' and tags['fr']=='fr-CA' and tags['zh']=='zh-CN', tags)
        check("56 no page errors across the language sweep", len(el)==0, el[:2])
        await pgl.close()

        print("\n--- first-use fixes: near me, landmarks, quick-pick themes (round 11) ---")
        pge=await b.new_page(viewport={'width':390,'height':760}, has_touch=True, is_mobile=True)
        ee=[]; pge.on('pageerror', lambda e: ee.append(str(e)))
        # A stub geolocation API: records every call and hands back manual control of
        # the success/error callback, so the flow can be driven deterministically —
        # without needing real OS location permission in a headless browser, and
        # without ever letting the test itself answer the permission question the
        # app is supposed to ask a human.
        await pge.add_init_script("""
          window.__geoCalls=0;
          Object.defineProperty(navigator,'geolocation',{configurable:true,value:{
            getCurrentPosition:(ok,err,opts)=>{window.__geoCalls++;window.__geoOk=ok;window.__geoErr=err;}
          }});
        """)
        await pge.goto(URL); await pge.wait_for_timeout(1200)

        check("57 geolocate control renders on the map, not in the header",
              await pge.evaluate("()=>!!document.querySelector('.geo-btn')"))
        # 2026-09-08: this is the single most-used control on the map, so it gets a
        # bigger tap target than the shared 44px accessibility floor -- 48px --
        # under pointer:coarse (this page is has_touch/is_mobile).
        geo_btn_box=await pge.evaluate("""()=>{
            const r=document.querySelector('.geo-btn').getBoundingClientRect();
            return {w:r.width,h:r.height};}""")
        check("57 the geo button meets its enlarged 48px touch target under pointer:coarse",
              geo_btn_box['w']>=48 and geo_btn_box['h']>=48, geo_btn_box)
        check("57 geolocation is never touched before any click",
              await pge.evaluate("()=>window.__geoCalls")==0)
        await pge.click('.geo-btn'); await pge.wait_for_timeout(200)
        check("57 first tap explains before requesting, not after",
              not await pge.evaluate("()=>document.getElementById('geoNote').hidden")
              and await pge.evaluate("()=>window.__geoCalls")==0)
        await pge.click('#geoNoteCancel'); await pge.wait_for_timeout(150)
        check("57 declining the explainer never touches geolocation or persists consent",
              await pge.evaluate("()=>window.__geoCalls")==0
              and await pge.evaluate("()=>localStorage.getItem('kamloopsGeoExplained')") is None)
        await pge.click('.geo-btn'); await pge.wait_for_timeout(200)
        check("57 the explainer reappears until it is actually accepted",
              not await pge.evaluate("()=>document.getElementById('geoNote').hidden"))
        await pge.click('#geoNoteOk'); await pge.wait_for_timeout(200)
        check("57 accepting closes the explainer, calls geolocation once, and remembers",
              await pge.evaluate("()=>document.getElementById('geoNote').hidden")
              and await pge.evaluate("()=>window.__geoCalls")==1
              and await pge.evaluate("()=>localStorage.getItem('kamloopsGeoExplained')")=='1')
        await pge.evaluate("()=>window.__geoOk({coords:{latitude:50.6745,longitude:-120.3273,accuracy:15}})")
        await pge.wait_for_timeout(300)
        centre=await pge.evaluate("()=>{const c=mapref.getCenter();return {lat:+c.lat.toFixed(3),lng:+c.lng.toFixed(3)};}")
        check("57 a successful fix recentres the map on the reported position",
              abs(centre['lat']-50.6745)<0.01 and abs(centre['lng']-(-120.3273))<0.01, centre)
        geoevs=[e['p'] for e in await pge.evaluate("()=>_evBuf.map(e=>({t:e.t,p:e.p}))") if e['t']=='geo_locate']
        check("57 the fix is logged as success, with no coordinate anywhere in the event",
              bool(geoevs) and geoevs[-1].get('result')=='success'
              and not any(k in geoevs[-1] for k in ('lat','lng','latitude','longitude','coords')),
              geoevs[-1] if geoevs else None)

        # 2026-09-08: the plain circleMarker "you are here" dot was replaced with a
        # pulsing divIcon marker plus a permanent, translated tooltip, so a first-
        # time user recognizes their own location instead of seeing an ambiguous
        # blue dot. Cover the new marker shape, the tooltip text/content, and that
        # switching languages updates the tooltip in place.
        here_shape=await pge.evaluate("""()=>{
            const el=document.querySelector('.geo-here-icon');
            return {hasIcon:!!el, hasDot:!!el&&!!el.querySelector('.geo-here-dot'),
                    hasPulse:!!el&&!!el.querySelector('.geo-here-pulse'),
                    hasMarker:typeof geoMarker!=='undefined'&&!!geoMarker};}""")
        check("57 a successful fix drops a pulsing here-marker, not a plain dot",
              here_shape['hasIcon'] and here_shape['hasDot'] and here_shape['hasPulse']
              and here_shape['hasMarker'], here_shape)
        here_tip_en=await pge.evaluate("""()=>{
            const t=geoMarker&&geoMarker.getTooltip&&geoMarker.getTooltip();
            return {perm:!!t&&t.options.permanent, txt:t&&t.getContent(), expected:UI.en.geoHereLabel};}""")
        check("57 the here-marker carries a permanent tooltip with the translated label",
              here_tip_en['perm'] and here_tip_en['txt']==here_tip_en['expected'], here_tip_en)
        await pge.evaluate("l=>setLang(l)", 'zh'); await pge.wait_for_timeout(150)
        here_tip_zh=await pge.evaluate("()=>geoMarker.getTooltip().getContent()")
        check("57 switching languages updates the here-marker's tooltip in place",
              here_tip_zh==await pge.evaluate("()=>UI.zh.geoHereLabel"), here_tip_zh)
        await pge.evaluate("l=>setLang(l)", 'en'); await pge.wait_for_timeout(150)
        await pge.click('.geo-btn'); await pge.wait_for_timeout(200)
        check("57 a second tap skips the explainer — consent was already given",
              await pge.evaluate("()=>window.__geoCalls")==2
              and await pge.evaluate("()=>document.getElementById('geoNote').hidden"))
        await pge.evaluate("()=>window.__geoErr({code:1})")
        await pge.wait_for_timeout(200)
        msg=await pge.inner_text('#geoNoteText')
        check("57 a denied permission explains itself rather than failing silently",
              len(msg)>0 and not await pge.evaluate("()=>document.getElementById('geoNote').hidden"), msg)
        check("57 the privacy note discloses the Near Me capability",
              'Near Me' in await pge.inner_text('.privacy-note'))
        check("57 no page errors from the geolocation flow", len(ee)==0, ee[:3])

        lm=await pge.evaluate("()=>typeof LANDMARKS!=='undefined'?LANDMARKS.length:0")
        check("58 LANDMARKS resolves to a handful of real, distinct places", lm>=4, lm)
        await pge.evaluate("()=>mapref.setView(CITYref.centre,CITYref.zoom)")
        await pge.wait_for_timeout(500)
        vislabels=await pge.evaluate("""()=>[...document.querySelectorAll('.leaflet-tooltip.landmark-label')]
            .filter(e=>getComputedStyle(e).display!=='none').length""")
        check("58 at least one landmark label is visible on the opening view", vislabels>=1, vislabels)
        await pge.evaluate("()=>mapref.panBy([200,0])"); await pge.wait_for_timeout(500)
        check("58 landmark labels keep working after a pan, no page errors", len(ee)==0, ee[:3])

        for k,sel in (('free','#qpFree'),('family','#qpFamily'),('indoor','#qpIndoor')):
            check("59 quick-pick %s carries a real theme icon and label"%k,
                  await pge.evaluate("s=>{const e=document.querySelector(s);return !!e&&e.textContent.trim().length>1;}", sel))
        await pge.evaluate("()=>{aT.clear();aC.clear();aR=new Set(Object.keys(RI));renderThemes();renderCats();renderRegs();apply();}")
        await pge.wait_for_timeout(200)
        await pge.click('#qpFree'); await pge.wait_for_timeout(300)
        check("59 a quick-pick theme actually filters, combined with category/area",
              await pge.evaluate("()=>aT.has('free')") and await pge.evaluate("()=>lastVisible")<N)
        await pge.click('#qpFree'); await pge.wait_for_timeout(200)

        hint_ok=await pge.evaluate("""()=>UI.en.hint.length<60
            && !UI.en.hint.includes('Quick Picks to combine')
            && UI.en.hintShort && UI.en.hintShort!==UI.en.hint""")
        check("60 the default hint is short and question-shaped, with a shorter sibling",
              hint_ok, await pge.evaluate("()=>[UI.en.hint,UI.en.hintShort]"))

        subtext=await pge.evaluate("()=>document.getElementById('sub').textContent")
        subdisplay=await pge.evaluate("()=>getComputedStyle(document.getElementById('sub')).display")
        check("61 the subtitle is visually hidden but stays in the accessibility tree",
              subdisplay!='none' and len(subtext)>0, {'display':subdisplay,'len':len(subtext)})
        check("61 h1 points to it via aria-describedby",
              await pge.evaluate("()=>document.getElementById('h1').getAttribute('aria-describedby')")=='sub')
        check("61 the subtitle no longer tells a reader to pick an area first",
              'then category' not in subtext, subtext)

        await pge.click('#areaBtn'); await pge.wait_for_timeout(300)
        regtxt=await pge.evaluate("()=>[...document.querySelectorAll('#regRow .reg-btn')].map(b=>b.textContent)")
        check("62 every region button carries a parenthetical geographic cue",
              len(regtxt)>1 and all(('(' in t) for t in regtxt[1:]), regtxt)
        await pge.keyboard.press('Escape'); await pge.wait_for_timeout(200)

        await pge.evaluate("()=>resetAll()"); await pge.wait_for_timeout(300)
        st_unfiltered=await pge.inner_text('#statusText')
        check("63 unfiltered status reads as a plain total, not an empty fraction",
              '/' not in st_unfiltered and str(N) in st_unfiltered, st_unfiltered)
        await pge.evaluate("()=>{aC=new Set(['bank']);renderCats();apply();}")
        await pge.wait_for_timeout(300)
        st_filtered=await pge.inner_text('#statusText')
        check("63 a filtered status keeps the v/t form", '/' in st_filtered, st_filtered)
        await pge.evaluate("()=>resetAll()"); await pge.wait_for_timeout(200)

        short_label=await pge.evaluate("()=>document.getElementById('guideToggle').dataset.short")
        check("64 the guide button carries a short visible label", bool(short_label), short_label)
        other_hidden=await pge.evaluate("""()=>['shareBtn','feedbackLink']
            .every(id=>getComputedStyle(document.getElementById(id).querySelector('.hl-tx')).display==='none')""")
        check("64 the other two header links stay icon-only at this width", other_hidden)
        # #noteToggle is hidden outright (2026-09-08), not merely icon-only, so it
        # gets its own stronger assertion: the button itself must not render at all,
        # guarding against the CSS-cascade trap where an author-origin display rule
        # (e.g. the pointer:coarse header-links block) would otherwise defeat the
        # native [hidden] behavior.
        note_toggle_hidden=await pge.evaluate(
            "()=>getComputedStyle(document.getElementById('noteToggle')).display==='none'")
        check("64b #noteToggle stays fully hidden (not just icon-only) at this width", note_toggle_hidden)
        await pge.close()

        pgt2=await b.new_page(viewport={'width':375,'height':600}, has_touch=True, is_mobile=True)
        et2=[]; pgt2.on('pageerror', lambda e: et2.append(str(e)))
        await pgt2.goto(URL); await pgt2.wait_for_timeout(1000)
        fhint_txt=await pgt2.evaluate("()=>document.getElementById('fhint').textContent")
        short_expected=await pgt2.evaluate("()=>UI[L_].hintShort")
        check("60 a short screen shows the shortened hint instead of nothing",
              len(fhint_txt)>0 and fhint_txt==short_expected, {'shown':fhint_txt,'expected':short_expected})
        check("60 no page errors on a short screen", len(et2)==0, et2[:3])
        # This page is has_touch/is_mobile, i.e. pointer:coarse -- exactly the
        # condition under which @media(pointer:coarse){.header-links a,...} would
        # (if the defensive #noteToggle[hidden] override were ever removed) win
        # the cascade over the native [hidden] rule and make the button reappear.
        note_toggle_hidden_coarse=await pgt2.evaluate(
            "()=>getComputedStyle(document.getElementById('noteToggle')).display==='none'")
        check("60 #noteToggle stays hidden under pointer:coarse, not just fine pointer",
              note_toggle_hidden_coarse)
        await pgt2.close()

        print("\n--- 2026-09-08 audit fixes (round 65) ---")
        pga=await b.new_page(viewport={'width':1280,'height':900})
        ea=[]; pga.on('pageerror', lambda e: ea.append(str(e)))
        # Most desktop browsers have no navigator.share; that is the condition
        # under which the share sheet's biggest button used to render and do
        # nothing, because .share-native{display:block} beat the UA's [hidden].
        await pga.add_init_script("try{Object.defineProperty(navigator,'share',{get:()=>undefined,configurable:true});}catch(e){}")
        await pga.goto(URL); await pga.wait_for_timeout(1200)
        await pga.click('#shareBtn'); await pga.wait_for_timeout(300)
        sn=await pga.evaluate("""()=>{const e=document.getElementById('shareNative');
            return {hidden:e.hidden,display:getComputedStyle(e).display,vis:e.offsetParent!==null};}""")
        check("65 the native share button really disappears without navigator.share",
              sn['display']=='none' and not sn['vis'], sn)
        await pga.keyboard.press('Escape'); await pga.wait_for_timeout(200)

        # Hiding the header's Data Notes button took the privacy disclosure and
        # the disclaimer offline with it — nothing else opened that modal.
        fb=await pga.evaluate("""()=>{const b=document.getElementById('footerNoteBtn');
            return {exists:!!b,visible:!!b&&b.offsetParent!==null};}""")
        check("65 the footer carries the only remaining opener for the privacy note",
              fb['exists'] and fb['visible'], fb)
        await pga.click('#footerNoteBtn'); await pga.wait_for_timeout(350)
        pn=await pga.evaluate("""()=>{const pv=document.querySelector('#noteBody .privacy-note');
            return {open:document.getElementById('noteBackdrop').classList.contains('open'),
                    privacy:pv?pv.textContent.length:0,
                    body:document.getElementById('noteBody').textContent.length};}""")
        check("65 it opens the full privacy text and the disclaimer",
              pn['open'] and pn['privacy']>400 and pn['body']>800, pn)
        await pga.keyboard.press('Escape'); await pga.wait_for_timeout(250)

        # Every active-filter chip's x must report which filter it cleared. The
        # delegate used to read '.chip .x', which matches nothing on this page.
        chips=await pga.evaluate("""()=>{
            aC=new Set(['bank']);aR=new Set(['ns']);aT=new Set(['free']);
            renderRegs();renderCats();renderThemes();apply();
            const n0=_evBuf.length;
            for(let i=0;i<4;i++){const x=document.querySelector('#activeFilters .af-chip .x');
                                 if(!x)break;x.click();}
            return _evBuf.slice(n0).filter(e=>e.t==='filter_clear_chip').map(e=>e.p.kind);}""")
        check("65 clearing a region / theme / category chip is each recorded",
              set(chips)=={'region','theme','cat'}, chips)
        await pga.evaluate("()=>resetAll()"); await pga.wait_for_timeout(250)

        # The dead end and the way out of it are the app's clearest "stuck" signal.
        es=await pga.evaluate("""()=>{
            const n0=_evBuf.length;
            aC=new Set(['bank']);aR=new Set(['ws']);aT=new Set(['history','student']);
            apply();apply();apply();
            const shown=_evBuf.slice(n0).filter(x=>x.t==='empty_state_shown');
            const n1=_evBuf.length;
            const btn=document.querySelector('#emptyState .empty-btn'); if(btn)btn.click();
            return {shown:shown.length,
                    recovered:_evBuf.slice(n1).filter(x=>x.t==='empty_state_recover').length};}""")
        check("65 an empty result reports once on entry, plus its recovery click",
              es['shown']==1 and es['recovered']==1, es)

        # The crash: markercluster reads layer.__parent when its zoom animation
        # ends, so removing the marker mid-flight threw and the global error trap
        # showed the reader a "please refresh" toast.
        await pga.evaluate("()=>resetAll()"); await pga.wait_for_timeout(300)
        await pga.evaluate("""()=>{
            map.setView(CITY.centre,11);
            const t=P.find(p=>p.c!=='bank');
            favorites.add(t.id);renderFavList();
            document.querySelector('#favList .rt-name').click();
            aC=new Set(['bank']);renderCats();apply();}""")
        await pga.wait_for_timeout(1900)
        toast=await pga.evaluate("()=>document.getElementById('toast').classList.contains('show')")
        check("65 filtering a favourite away mid cluster-zoom no longer crashes",
              len(ea)==0 and not toast, {'errors':ea[:2],'toast':toast})

        # A saved place the current filters hide still has to answer the tap.
        hid=await pga.evaluate("""()=>{
            resetAll();
            const t=P.find(p=>p.c!=='bank');
            favorites.add(t.id);
            aC=new Set(['bank']);renderCats();apply();
            focusMarker(M.find(x=>x.data.id===t.id),16);
            return {popup:!!document.querySelector('.leaflet-popup'),
                    ev:_evBuf.filter(x=>x.t==='marker_view'&&x.p.src==='hidden_by_filter').length};}""")
        check("65 a favourite hidden by a filter still opens its own card",
              hid['popup'] and hid['ev']>=1, hid)
        check("65 no page errors across the audit-fix pass", len(ea)==0, ea[:3])
        await pga.close()

        # The two Quick Picks that read as the same chip in all six languages.
        pgc=await b.new_page(viewport={'width':1280,'height':900})
        await pgc.goto(URL); await pgc.wait_for_timeout(1100)
        coll=await pgc.evaluate("""()=>{const out={};
            ['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);
              const norm=s=>s.replace(/[^\\p{L}]/gu,'').toLowerCase().split('').sort().join('');
              out[l]=norm(document.getElementById('kids').textContent)
                    ===norm(document.getElementById('qpFamily').textContent);});
            setLang('en');return out;}""")
        check("65 the kids preset and the family theme are not the same words reordered",
              not any(coll.values()), coll)
        await pgc.close()

        # Touch: the search ✕ and the route indicator, both [hidden] traps.
        pgm=await b.new_page(viewport={'width':390,'height':760}, has_touch=True, is_mobile=True)
        em=[]; pgm.on('pageerror', lambda e: em.append(str(e)))
        await pgm.goto(URL); await pgm.wait_for_timeout(1200)
        sc=await pgm.evaluate("""()=>{const e=document.getElementById('searchClear');
            return {display:getComputedStyle(e).display,vis:e.offsetParent!==null};}""")
        check("65 the search clear button is absent on touch until there is text",
              sc['display']=='none' and not sc['vis'], sc)
        await pgm.fill('#searchInput','bank'); await pgm.wait_for_timeout(450)
        check("65 …and returns as soon as there is something to clear",
              await pgm.evaluate("()=>document.getElementById('searchClear').offsetParent!==null"))
        bi=await pgm.evaluate("""()=>{selectRoute(Object.keys(BR)[0]);
            const e=document.getElementById('busIndicator');
            return {hidden:e.hidden,display:getComputedStyle(e).display};}""")
        check("65 the route indicator is shown to sighted and assistive readers alike",
              (not bi['hidden']) and bi['display']=='flex', bi)
        # Nothing marked hidden may render, at any pointer type.
        traps=await pgm.evaluate("""()=>[...document.querySelectorAll('[hidden]')]
            .map(e=>({id:e.id||e.className,d:getComputedStyle(e).display}))
            .filter(x=>x.d!=='none')""")
        check("65 no element carrying [hidden] computes a display on touch", len(traps)==0, traps)
        check("65 no page errors on the touch pass", len(em)==0, em[:3])
        await pgm.close()

        print("\n--- Life Guide task layer (round 66) ---")
        pgt3=await b.new_page(viewport={'width':1280,'height':900})
        et3=[]; pgt3.on('pageerror', lambda e: et3.append(str(e)))
        await pgt3.goto(URL); await pgt3.wait_for_timeout(1200)
        await pgt3.click('#guideToggle'); await pgt3.wait_for_timeout(350)
        gl=await pgt3.evaluate("""()=>({cards:document.querySelectorAll('.task-card').length,
            prose:document.getElementById('guideBody').textContent.length,
            toc:!!document.querySelector('.guide-toc')})""")
        ntasks=await pgt3.evaluate("()=>TASKS.length")
        check("66 the guide opens on problems, with the long-form guide still under it",
              gl['cards']==ntasks and gl['cards']>=6 and gl['prose']>10000 and gl['toc'],
              dict(gl, tasks=ntasks))
        td=await pgt3.evaluate("""()=>{document.querySelector('.task-card[data-task=msp]').click();
            const h=document.getElementById('guideTasks');
            return {steps:h.querySelectorAll('.task-steps li').length,
                    place:(h.querySelector('.task-place b')||{}).textContent,
                    map:!!h.querySelector('.task-map'),
                    src:!!h.querySelector('.task-src a'),
                    back:!!document.getElementById('taskBack')};}""")
        check("66 a task gives steps, the office, a map hand-off and its official source",
              td['steps']>=3 and td['map'] and td['src'] and td['back'] and td['place'], td)
        # The photo BC Services Card is issued by ICBC, not Service BC — the kind of
        # detail that sends someone to the wrong counter, so it is pinned here.
        icbc=await pgt3.evaluate("""()=>TASKS.find(t=>t.id==='msp').steps
            .some(s=>/ICBC/.test(s.en))""")
        check("66 the MSP card step still names ICBC as the place that issues it", icbc)
        mapped=await pgt3.evaluate("""()=>{const n0=_evBuf.length;
            document.querySelector('.task-map').click();
            return {closed:!document.getElementById('guideBackdrop').classList.contains('open'),
                    ev:_evBuf.slice(n0).some(e=>e.t==='task_to_map')};}""")
        await pgt3.wait_for_timeout(1000)
        check("66 'where do I go' closes the guide and opens that office on the map",
              mapped['closed'] and mapped['ev']
              and await pgt3.evaluate("()=>!!document.querySelector('.leaflet-popup')"), mapped)
        # every task, every language, no silent English fallback
        tl=await pgt3.evaluate("""()=>{const out={};
            ['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);renderTaskList();
              out[l]=[...document.querySelectorAll('.task-q')].map(e=>e.textContent).join('|');});
            setLang('en');return out;}""")
        check("66 every task reads in all six languages, none falling back to English",
              len(set(tl.values()))==6 and all(v for v in tl.values()),
              {k:v[:22] for k,v in tl.items()})
        every=await pgt3.evaluate("""()=>{const bad=[];
            TASKS.forEach(t=>['q','t','why'].forEach(k=>{
              ['zh','en','fr','es','ko','ja'].forEach(l=>{
                if(!t[k]||!t[k][l])bad.push(t.id+'.'+k+'.'+l);});}));
            TASKS.forEach(t=>t.steps.forEach((s,i)=>['zh','en','fr','es','ko','ja'].forEach(l=>{
                if(!s[l])bad.push(t.id+'.step'+i+'.'+l);})));
            return bad;}""")
        check("66 no task is missing a translation in any language", len(every)==0, every[:6])
        check("66 no page errors from the task layer", len(et3)==0, et3[:3])
        await pgt3.close()

        print("\n--- multidisciplinary pass (round 67) ---")
        pgm2=await b.new_page(viewport={'width':1280,'height':950})
        em2=[]; pgm2.on('pageerror', lambda e: em2.append(str(e)))
        await pgm2.goto(URL); await pgm2.wait_for_timeout(1200)

        # Self-efficacy: ticking a task has to persist, and must stay on the device.
        await pgm2.click('#guideToggle'); await pgm2.wait_for_timeout(300)
        tick=await pgm2.evaluate("""()=>{
            document.querySelector('.task-card[data-task=sin]').click();
            document.getElementById('taskTick').click();
            document.getElementById('taskBack').click();
            return {pc:(document.querySelector('.task-pc')||{}).textContent||null,
                    badge:!!document.querySelector('.task-card[data-task=sin] .task-done-b'),
                    stored:localStorage.getItem('kamloopsTasksDone'),
                    inUrl:/sin/.test(location.search)};}""")
        check("67 marking a task done shows progress, persists, and never leaves the device",
              tick['pc'] and tick['badge'] and tick['stored'] and not tick['inUrl'], tick)

        # Salience: a deadline is the one fact that expires, so it rides on the list.
        dls=await pgm2.evaluate("""()=>[...document.querySelectorAll('.task-card .task-dl')]
            .map(e=>e.textContent)""")
        check("67 time-limited tasks show their deadline on the list", len(dls)>=4, dls)

        # The only signal that can tell us a card is wrong.
        fb=await pgm2.evaluate("""()=>{
            document.querySelector('.task-card[data-task=licence]').click();
            const n0=_evBuf.length;
            document.querySelector('.task-fb-b[data-r=stuck]').click();
            return {ev:_evBuf.slice(n0).some(e=>e.t==='task_outcome'&&e.p.result==='stuck'),
                    thanks:!!document.querySelector('.task-thanks')};}""")
        check("67 'I got stuck' is recorded and acknowledged", fb['ev'] and fb['thanks'], fb)

        # Cross-cultural: a line to read aloud, and who sees your information.
        rows=await pgm2.evaluate("""()=>{
            document.getElementById('taskBack').click();
            document.querySelector('.task-card[data-task=settle]').click();
            const h=document.getElementById('guideTasks');
            return {say:(h.querySelector('.task-say')||{}).textContent||'',
                    confid:[...h.querySelectorAll('.task-lb')].some(e=>e.textContent===UI[L_].taskConfid),
                    transfix:!!h.querySelector('.task-src a[href^="mailto:"]')};}""")
        check("67 a card offers words to say, a confidentiality line, and a translation report",
              len(rows['say'])>20 and rows['confid'] and rows['transfix'], rows)

        # Cross-linguistic: search has to work in the language being read.
        alias=await pgm2.evaluate("""()=>{const o={};
            const probe=(l,q,want)=>{setLang(l);searchInputEl.value=q;searchRaw=q;
              searchTerm=q.toLowerCase();apply();
              const hits=M.filter(m=>m.score>0).sort((a,b)=>b.score-a.score).map(m=>m.data.n);
              o[l+':'+q]=hits.length>0&&hits[0].indexOf(want)>=0;};
            probe('zh','医院','Royal Inland');probe('zh','驾照','ICBC');
            probe('ko','병원','Royal Inland');probe('ja','運転免許','ICBC');
            resetAll();setLang('en');return o;}""")
        check("67 searching in Chinese/Korean/Japanese finds the right place",
              all(alias.values()), alias)

        # Sociology: the territory's own institutions are in the data, not just its museum.
        ind=await pgm2.evaluate("""()=>{
            const labels={};['zh','en','fr','es','ko','ja'].forEach(l=>{labels[l]=CI.indigenous&&CI.indigenous[l];});
            setLang('en');aC=new Set(['indigenous']);renderCats();apply();
            const shown=M.filter(m=>markerHome().hasLayer(m)).length;
            resetAll();
            return {complete:Object.values(labels).every(Boolean),
                    distinct:new Set(Object.values(labels)).size,shown:shown};}""")
        check("67 Indigenous services is a labelled category with real entries",
              ind['complete'] and ind['distinct']==6 and ind['shown']>=2, ind)

        # History: the section exists, is indexed, and carries the support line.
        hist=await pgm2.evaluate("""()=>{const o={};
            ['en','fr','es','zh','ko','ja'].forEach(l=>{setLang(l);
              const body=document.getElementById('guideBody').textContent;
              o[l]=[...document.querySelectorAll('.guide-toc-btn')].some(b=>b.textContent.indexOf('🧡')===0)
                   && body.indexOf('1-800-588-8717')>=0 && body.indexOf('1890')>=0;});
            setLang('en');return o;}""")
        check("67 the land-and-history section is indexed in all six languages, with support",
              all(hist.values()), hist)
        check("67 no page errors across the multidisciplinary pass", len(em2)==0, em2[:3])
        await pgm2.close()

        print("\n--- multidisciplinary pass, second round (round 68) ---")
        pgm3=await b.new_page(viewport={'width':1280,'height':950})
        em3=[]; pgm3.on('pageerror', lambda e: em3.append(str(e)))
        await pgm3.goto(URL); await pgm3.wait_for_timeout(1300)

        # Two of the seven lenses had no card at all: isolation (nobody to call)
        # and material hardship (no money this month). Both are in the buckets a
        # reader in that situation would open, in all six languages.
        nc=await pgm3.evaluate("""()=>{const o={};
            ['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);renderTaskList();
              o[l]=[...document.querySelectorAll('.task-card')]
                   .filter(e=>['connect','hardship'].indexOf(e.dataset.task)>=0)
                   .map(e=>e.textContent.trim());});
            setLang('en');renderTaskList();
            const seen={};Object.values(o).forEach(v=>v.forEach((t,i)=>{
              (seen[i]=seen[i]||new Set()).add(t);}));
            return {each:Object.values(o).every(v=>v.length===2&&v.every(Boolean)),
                    distinct:Object.values(seen).map(s=>s.size),
                    buckets:TASKS.filter(t=>['connect','hardship'].indexOf(t.id)>=0)
                                 .map(t=>t.id+':'+t.when)};}""")
        check("68 the isolation and hardship cards exist in six languages, in the right buckets",
              nc['each'] and all(d==6 for d in nc['distinct'])
              and nc['buckets']==['connect:ongoing','hardship:problem'], nc)

        # Hardship is the card where the barrier is fear, not information: the
        # "nobody reports you" line has to be there in every language or the card
        # is asking people to take a risk it never addressed.
        cfd=await pgm3.evaluate("""()=>{const o={};
            ['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);renderTaskList();
              document.querySelector('.task-card[data-task=hardship]').click();
              const row=[...document.querySelectorAll('#guideTasks .task-row')]
                .find(r=>r.querySelector('.task-lb').textContent===UI[l].taskConfid);
              o[l]=row?row.querySelector('.task-bd').textContent.trim():null;});
            setLang('en');renderTaskList();return o;}""")
        check("68 the hardship card says, in every language, that asking is safe",
              all(cfd.values()) and len(set(cfd.values()))==6,
              {k:(v or '')[:24] for k,v in cfd.items()})

        # The regression this round actually caught: "where do I go" was silent
        # for any office that shares an address with another place (109 Victoria
        # St has two), because a marker that can never leave its cluster ignores
        # openPopup(). Both new cards, and a favourite, must open something.
        for tid, want in (('connect','Volunteer'), ('hardship','Food Bank')):
            await pgm3.evaluate("()=>{resetAll();if(!document.getElementById('guideBackdrop').classList.contains('open'))document.getElementById('guideToggle').click();}")
            await pgm3.wait_for_timeout(350)
            await pgm3.evaluate("""(tid)=>{renderTaskList();
                document.querySelector('.task-card[data-task='+tid+']').click();
                document.querySelector('.task-map').click();}""", tid)
            await pgm3.wait_for_timeout(1400)
            pop=await pgm3.evaluate("()=>{const t=document.querySelector('.leaflet-popup .pt');return t?t.textContent:null;}")
            check("68 '%s' → where do I go opens that office on the map"%tid,
                  bool(pop) and want in pop, pop)

        cofav=await pgm3.evaluate("""()=>{resetAll();
            // the co-located pair: two places, one set of coordinates
            const id='507845f0';
            favorites.add(id);renderFavList();
            const n=[...document.querySelectorAll('#favList .rt-name')]
              .find(x=>x.textContent.indexOf('Volunteer')>=0);
            if(!n)return {no:'not in list'};
            n.click();return {clicked:true};}""")
        await pgm3.wait_for_timeout(1500)
        favpop=await pgm3.evaluate("()=>{const t=document.querySelector('.leaflet-popup .pt');return t?t.textContent:null;}")
        check("68 opening a saved place that shares an address still opens its popup",
              cofav.get('clicked') and favpop and 'Volunteer' in favpop, {'r':cofav,'popup':favpop})

        # Crisis support is filed where someone in crisis looks, not under the
        # heading that describes who happens to run it.
        grp=await pgm3.evaluate("""()=>{resetAll();setLang('en');
            const g=GRP.find(g=>g.cats.indexOf('support')>=0);
            const labels={};['zh','en','fr','es','ko','ja'].forEach(l=>{labels[l]=CI.support&&CI.support[l];});
            aC=new Set(['support']);renderCats();apply();
            const on=M.filter(m=>markerHome().hasLayer(m)).length;
            resetAll();
            return {group:g?g.k:null,shown:on,icon:IC.support,colour:CD.support,
                    complete:Object.values(labels).every(Boolean),
                    distinct:new Set(Object.values(labels)).size};}""")
        check("68 crisis support is a labelled category filed under Services, not Faith",
              grp['group']=='services' and grp['complete'] and grp['distinct']==6
              and grp['shown']>=1 and grp['icon'] and grp['colour'], grp)

        # A place nobody can find is a place that is not in the app.
        fnd=await pgm3.evaluate("""()=>{const o={};
            const probe=(lang,q,want)=>{setLang(lang);
              searchInputEl.value=q;searchRaw=q;searchTerm=q.toLowerCase();apply();
              o[lang+':'+q]=M.filter(m=>m.score>0).some(m=>m.data.n.indexOf(want)>=0);};
            probe('zh','志愿','Volunteer');probe('ko','자원봉사','Volunteer');
            probe('zh','无家可归','Mustard');probe('fr','bénévolat','Volunteer');
            resetAll();setLang('en');return o;}""")
        check("68 the new places are findable in the reader's own words", all(fnd.values()), fnd)
        check("68 no page errors across the second multidisciplinary pass", len(em3)==0, em3[:3])
        await pgm3.close()

        print("\n--- cluster plugin absent (CDN failure) ---")
        pg4=await b.new_page(viewport={'width':1100,'height':800})
        e4=[]; pg4.on('pageerror', lambda e: e4.append(str(e)))
        await pg4.goto('file://'+NOCLUSTER); await pg4.wait_for_timeout(1600)
        vis=await pg4.evaluate("Mref.filter(m=>mapref.hasLayer(m)).length")
        await pg4.fill('#searchInput','bank'); await pg4.wait_for_timeout(650)
        st=await pg4.inner_text('#statusText')
        check("graceful degradation without clustering", vis==N and len(e4)==0, "%d markers, %d errors, %r"%(vis,len(e4),st))
        await pg4.close()

        print("\n================ %d checks failed ================"%len(FAIL))
        for f in FAIL: print("   FAILED:",f)
        print("total page errors:",len(allerrs), allerrs[:3])
        await b.close()
    sys.exit(1 if FAIL else 0)
asyncio.run(main())
