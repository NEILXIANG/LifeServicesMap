import asyncio, sys, os, re, glob, shutil, atexit, tempfile, subprocess
from playwright.async_api import async_playwright

# 2026-09-13 (item 13): on phones the six language buttons live in a menu behind
# one button; open it first when the target button is not on screen
async def pick_lang(pg,lang):
    sel='[data-lang="%s"]'%lang
    if not await pg.is_visible(sel):
        await pg.click('#langMenuBtn'); await pg.wait_for_timeout(150)
    await pg.click(sel)

# Test the file that is actually shipped, not a copy that was made by hand at some
# point and has been quietly ageing ever since. Both fixtures are regenerated on
# every run from kamloops.html.
def _project_root(p):
    """向上找到项目根（放着 app/engine/parts.txt 的那一层），
    这样脚本放在 scripts/ 或 tests/ 里也能正确定位，不必待在根目录。"""
    import os as _os
    for _ in range(6):
        if _os.path.exists(_os.path.join(p, 'app', 'engine', 'parts.txt')):
            return p
        p = _os.path.dirname(p)
    raise SystemExit('找不到项目根目录（需要 app/engine/parts.txt）')

HERE = _project_root(os.path.dirname(os.path.abspath(__file__)))

def find_built(here, argv_path=None):
    """The built file. Named kamloops.html here; readers often rename their copy,
    so fall back to the only .html sitting next to this script."""
    if argv_path:
        return argv_path
    default = os.path.join(here, 'build', 'kamloops.html')
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
sys.path.insert(0, HERE)
import kamdata
CITY_TASKS_CHECKED = (re.search(r"tasksChecked:'(\d{4}-\d{2}-\d{2})'", kamdata.data_text()) or [None,'0000'])[1]

async def main():
    global N
    async with async_playwright() as p:
        # This container ships a Chromium at a fixed path; elsewhere let Playwright
        # find the one `playwright install chromium` put down.
        exe='/opt/pw-browsers/chromium'
        # never let a test run fetch real map tiles: a headless browser hammering a
        # tile provider with no referer is exactly what got the site blocked
        _args=['--host-resolver-rules=MAP *.arcgisonline.com ~NOTFOUND, MAP *.cartocdn.com ~NOTFOUND, MAP *.maptiler.com ~NOTFOUND, MAP *.stadiamaps.com ~NOTFOUND, MAP *.openstreetmap.org ~NOTFOUND']
        b=await (p.chromium.launch(executable_path=exe,args=_args) if os.path.exists(exe)
                 else p.chromium.launch(args=_args))
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
          // 2026-09-24: hours are not published for every kind of place. A city park
          // posts them on site; SD73 does not publish office hours and bell times move
          // with the school year; the province's child care dataset carries none. Those
          // records say "hours unknown" on purpose, so the ratio is measured over the
          // kinds of place that do have published hours.
          hoursExpected:Pref.filter(p=>!['park','trail','beach','dogpark','splash','elem','school','daycare','schoolbus','apt'].includes(p.c)).length,
          hoursExpectedWith:Pref.filter(p=>!['park','trail','beach','dogpark','splash','elem','school','daycare','schoolbus','apt'].includes(p.c)&&p.h&&typeof p.h==='object').length,
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
        check("31 most records that can have hours carry them",
              d['hoursExpectedWith'] > d['hoursExpected']*0.85,   # transit exchanges, taxis and some places of worship post none either
              "%d/%d (of %d records in total; parks, schools and child care publish none)"
              % (d['hoursExpectedWith'], d['hoursExpected'], N))
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
            await pick_lang(pg,lang); await pg.wait_for_timeout(300)
            await pg.fill('#searchInput',term); await pg.wait_for_timeout(560)
            n=await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)).length")
            note=await pg.inner_text('#searchNote')
            if expect=='gated': check("14 %r gated"%term, n==N and 'least' in note or 'at least' in note.lower() or '2' in note, note[:30])
            else: check("14/33 %r [%s] finds results"%(term,lang), 0<n<120, n)
            await pg.click('#searchClear'); await pg.wait_for_timeout(300)

        await pick_lang(pg,'en'); await pg.wait_for_timeout(300)
        print("\n--- search + filters combine (P0-2) ---")
        # Search used to silently bypass Area/Category — a "bank" search while North
        # Shore was selected quietly searched the whole city. It now narrows within
        # whatever is already filtered, so a bank search under a North-Shore-only,
        # bank-only filter should show exactly the North Shore banks, not every bank
        # in the city and not every North Shore place.
        await pg.evaluate("(()=>{aCref().clear();['bank'].forEach(k=>aCref().add(k));aRref().clear();aRref().add('ns');renderRegs();renderCats();apply();})()")
        await pg.wait_for_timeout(400)
        await pg.fill('#searchInput','bank'); await pg.wait_for_timeout(650)
        # 2026-09-22 (plan B): a search pauses the category filter — the area still
        # narrows it. So: every North Shore place that matches "bank", not only the
        # Banks category, and nothing outside North Shore.
        expected=await pg.evaluate("Pref.filter(p=>p.g==='ns'&&matchScore(p,'bank')>0).length")
        shown=await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)).length")
        outside=await pg.evaluate("Mref.filter(m=>markerHome().hasLayer(m)&&m.data.g!=='ns').length")
        check("65 search narrows within the area filter, not around it (categories pause during a search)",
              shown==expected and outside==0 and shown>0, "%d shown vs %d expected (ns 'bank' matches), %d outside"%(shown,expected,outside))
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
        # 2026-09-24 (p27): the star is the icon set's star, filled by a class, not
        # the ★ character — the saved state now reads off aria-pressed and .active.
        star=await pg.evaluate("""()=>{const s=document.querySelector('.fav-star');
            return s?{p:s.getAttribute('aria-pressed'),on:s.classList.contains('active'),
                      svg:!!s.querySelector('svg.ic'),glyph:/[★☆]/.test(s.textContent)}:null;}""")
        check("10 star state survives reopen",
              bool(star) and star['p']=='true' and star['on'] and star['svg'] and not star['glyph'], star)
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
        # 2026-09-11: the category sets live at the top of the Category sheet
        # now (the panel is still open from the clicks above)
        await pg.click('#health'); await pg.wait_for_timeout(400)
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
            await pick_lang(pg,_lg); await pg.wait_for_timeout(320)
            await pg.click('#guideToggle'); await pg.wait_for_timeout(260)
            _g=await pg.inner_text('#guideBody'); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(160)
            leaks |= set(_re.findall(r'\{[A-Z_]+\}', await pg.inner_text('body')))
            leaks |= set(_re.findall(r'\{[A-Z_]+\}', _g))
        check("05 no unexpanded placeholders in any language", not leaks, leaks)
        await pg.evaluate("resetAll()"); await pg.wait_for_timeout(600)
        check("05 map centre comes from CITY",
              await pg.evaluate("JSON.stringify([+mapref.getCenter().lat.toFixed(3),+mapref.getCenter().lng.toFixed(3)])")==await pg.evaluate("JSON.stringify(CITYref.centre)"))
        await pick_lang(pg,'en'); await pg.wait_for_timeout(300)

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
        # 2026-09-09: the full statement now sits behind an expander, so it is in
        # the DOM but not in innerText until opened — textContent is the right
        # question for "is the disclosure there", and the summary is the right
        # question for "is it readable".
        priv=await pg.evaluate("""()=>{const o={};['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);
          o[l]=document.getElementById('noteBody').textContent.indexOf(UI[l].privacyNote.replace(/<[^>]+>/g,'').slice(2,18))>-1;});
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
          // 2026-09-21: City parks now carry Parks Bylaw 35-104 hours (5–23); the open-air row with nothing posted is an informal site
          const p=Pref.find(x=>x.n==='Cooney Bay');
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
                await pick_lang(pgc,lang); await pgc.wait_for_timeout(250)
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
        # 2026-09-10: gov 4 -> 5 (the BC Employment and Assistance office is a
        # government office and belongs there). The boundary is what is pinned:
        # nothing that is a community organisation may sit in gov.
        # 2026-09-10 (fresh scan): gov 5 -> 9 — the Law Courts, City Hall and the
        # two WorkBC centres (a provincial programme, delivered under contract;
        # a reader looking for "the employment office" expects it here).
        check("49 the community centre is not filed under government",
              tx['gov']==9 and tx['commctr']>=4
              and not any(p['c']=='gov' and ('Community' in p['n'] or 'Society' in p['n'] or 'Association' in p['n']) for p in await pg.evaluate("()=>Pref.map(p=>({c:p.c,n:p.n}))")),
              [tx['gov'],tx['commctr']])
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
                await pick_lang(pgp,lang); await pgp.wait_for_timeout(250)
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
                await pick_lang(pg2,lang); await pg2.wait_for_timeout(250)
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
            await pick_lang(pg3,lang); await pg3.wait_for_timeout(350)
            for bid in ['#areaBtn','#areaBtn','#catBtn','#catBtn','#busBtn','#busBtn','#favBtn','#favBtn']:
                await pg3.click(bid); await pg3.wait_for_timeout(150)
            await pg3.click('#guideToggle'); await pg3.wait_for_timeout(250); await pg3.keyboard.press('Escape')
            # #noteToggle is hidden (2026-09-08); open the same modal programmatically
            # so this walkthrough still exercises it per language.
            await pg3.evaluate("()=>{trackEvent('note_open',{});openModal(document.getElementById('noteBackdrop'));}")
            await pg3.wait_for_timeout(250); await pg3.keyboard.press('Escape')
            await pg3.click('#qpMore'); await pg3.wait_for_timeout(300)
            await pg3.click('#kids'); await pg3.wait_for_timeout(350)
            await pg3.keyboard.press('Escape'); await pg3.wait_for_timeout(200)
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
        # The disclosure has to be *reachable*, not merely present: open the
        # expander the way a reader would and read what they would then see.
        await pge.evaluate("()=>{const b=document.getElementById('pvMore');if(b&&document.getElementById('pvFull').hidden)b.click();}")
        await pge.wait_for_timeout(200)
        # (two .privacy-note blocks since 2026-09-10 — the legal summary sits
        #  above the privacy one; read the block that owns the expander)
        check("57 the privacy note discloses the Near Me capability",
              'Near Me' in await pge.evaluate("()=>{const f=document.getElementById('pvFull');return f?f.closest('.privacy-note').innerText:''}"))
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

        # 2026-09-09: the six were re-picked. Five of the original six were parks
        # — comfortable to put a label on, weak to navigate by. What the labels
        # have to satisfy is structural, not a fixed list of names: one per area
        # (so they spread instead of clumping), and a bare place name (no ⭐,
        # which belongs to the list and the popup, not to the map).
        lmk=await pge.evaluate("""()=>{
            const rows=LANDMARKS.map(id=>Pref.find(p=>p.id===id)).filter(Boolean);
            return {n:rows.length,
                    regions:rows.map(p=>p.g),
                    parks:rows.filter(p=>p.c==='park').length,
                    names:rows.map(p=>p.n)};}""")
        check("58 one landmark per area, none doubled up",
              lmk['n']==len(set(lmk['regions'])), lmk['regions'])
        check("58 the areas a newcomer has to tell apart each get a name",
              set(lmk['regions'])>={'sk','ns','sa'}, lmk['regions'])
        lmcats=await pge.evaluate("()=>LANDMARKS.map(id=>(Pref.find(p=>p.id===id)||{}).c)")
        check("58 the central areas are anchored by something you navigate by, not a park",
              all(c!='park' for c,g in zip(lmcats,lmk['regions']) if g in ('sk','ns','sa')),
              list(zip(lmk['names'],lmcats)))
        rendered=await pge.evaluate("""()=>[...document.querySelectorAll('.leaflet-tooltip.landmark-label')]
            .map(e=>e.textContent)""")
        check("58 no editorial ⭐ leaks into a map label",
              all(not t.strip().startswith('⭐') for t in rendered), rendered)
        # The point of re-picking them is lost if the new ones never draw. They are
        # the most central, so they compete with the densest cluster bubbles; a
        # label blocked above its point now tries below it and then either side.
        await pge.evaluate("()=>mapref.setView(CITYref.centre,CITYref.zoom)")
        await pge.wait_for_timeout(700)
        drawn=await pge.evaluate("""()=>[...document.querySelectorAll('.leaflet-tooltip.landmark-label')]
            .filter(e=>getComputedStyle(e).display!=='none').map(e=>e.textContent)""")
        # 2026-09-13: a label that would hang off the map's edge is no longer drawn
        # as a clipped fragment, so only landmarks whose point is inside the map
        # (with room for the label) are expected on a 390px opening view
        inview=await pge.evaluate("""()=>{const sz=mapref.getSize();return landmarkMarkers.filter(it=>{const p=mapref.latLngToContainerPoint([it.lat,it.lng]);return p.x>70&&p.x<sz.x-70&&p.y>30&&p.y<sz.y-30;}).length;}""")
        check("58 every landmark inside the opening view finds a slot",
              len(drawn)>=inview and len(drawn)>=3, (drawn,inview))

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
        # 2026-09-13: the leading emoji is drawn as an icon now; compare the words
        check("60 a short screen shows the shortened hint instead of nothing",
              len(fhint_txt)>0 and fhint_txt.strip()==short_expected.replace('🔍','').strip(), {'shown':fhint_txt,'expected':short_expected})
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

        # --- the privacy statement, summarised (round 69) ---------------------
        # An accurate 400-word paragraph nobody reads discloses nothing. Three
        # lines carry the answers; the full text stays one tap away, unchanged.
        await pgm3.evaluate("()=>{setLang('en');}")
        await pgm3.click('#footerNoteBtn'); await pgm3.wait_for_timeout(400)
        pvs=await pgm3.evaluate("""()=>{const o={};
            ['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);
              const li=[...document.getElementById('pvFull').closest('.privacy-note').querySelectorAll('.pv-sum li')];
              o[l]={n:li.length,
                    vis:li.every(e=>e.getClientRects().length>0),
                    lead:li.map(e=>(e.querySelector('b')||{}).textContent||''),
                    foot:document.querySelector('.footer-privacy').textContent.trim(),
                    hidden:document.getElementById('pvFull').hidden};});
            setLang('en');return o;}""")
        check("69 three visible summary lines in every language, full text collapsed",
              all(v['n']==3 and v['vis'] and v['hidden'] and all(v['lead']) for v in pvs.values()),
              {k:(v['n'],v['vis'],v['hidden']) for k,v in pvs.items()})
        check("69 each summary line leads with a distinct claim, per language",
              all(len(set(v['lead']))==3 for v in pvs.values()),
              {k:v['lead'][0][:26] for k,v in pvs.items()})
        # The footer line used to be a denial ("...no personal data"). A denial in
        # brackets is what makes a disclosure read as a cover story; the line now
        # states what is recorded and sends the reader to look at it.
        check("69 the footer line states what is recorded rather than denying",
              all('no personal data' not in v['foot'] and '不含个人信息' not in v['foot']
                  and '個人情報は含みません' not in v['foot'] for v in pvs.values()),
              {k:v['foot'][:34] for k,v in pvs.items()})
        pvx=await pgm3.evaluate("""()=>{const b=document.getElementById('pvMore');
            const before=b.textContent, n0=_evBuf.length;
            b.click();
            const opened={txt:document.getElementById('pvFull').innerText.length,
                          aria:b.getAttribute('aria-expanded'),label:b.textContent};
            b.click();
            return {before:before,opened:opened,
                    reclosed:document.getElementById('pvFull').hidden,
                    label2:b.textContent,ev:_evBuf.slice(n0).map(e=>e.t)};}""")
        check("69 the expander opens the full statement, closes again, and is recorded",
              pvx['opened']['txt']>800 and pvx['opened']['aria']=='true'
              and pvx['opened']['label']!=pvx['before'] and pvx['reclosed']
              and pvx['label2']==pvx['before'] and pvx['ev']==['privacy_expand','privacy_expand'], pvx)
        await pgm3.keyboard.press('Escape'); await pgm3.wait_for_timeout(250)

        check("68 no page errors across the second multidisciplinary pass", len(em3)==0, em3[:3])
        await pgm3.close()

        print("\n--- guide first, map second; open now (round 70) ---")
        pg70=await b.new_page(viewport={'width':1280,'height':900})
        e70=[]; pg70.on('pageerror', lambda e: e70.append(str(e)))
        await pg70.goto(URL); await pg70.wait_for_timeout(1400)
        # The first build of "open now" declared its const below the marker pass
        # and the page died on load. Load-time errors are the whole check here.
        check("70 the page loads with no error at all", len(e70)==0, e70[:2])
        # Positioning: the title names the guide, the subtitle says what it does,
        # and the guide's own button asks the reader's question, in six languages.
        pos=await pg70.evaluate("""()=>{const o={};['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);
            o[l]={h1:document.getElementById('h1').textContent,
                  subVisible:document.getElementById('sub').getBoundingClientRect().height>10,
                  btn:document.getElementById('guideToggle').textContent.trim(),
                  qp:document.getElementById('qpGuide').textContent.trim(),
                  primary:getComputedStyle(document.getElementById('guideToggle')).backgroundColor!==getComputedStyle(document.getElementById('shareBtn')).backgroundColor};});
            setLang('en');return o;}""")
        check("70 the title is the guide, not the map, in six languages",
              all(('地图' not in v['h1'] and 'Map' not in v['h1'] and 'Carte' not in v['h1'] and 'Mapa' not in v['h1'] and '지도' not in v['h1'] and 'マップ' not in v['h1']) for v in pos.values()),
              {k:v['h1'] for k,v in pos.items()})
        check("70 the subtitle is visible and the guide button is the one filled control",
              all(v['subVisible'] and v['primary'] for v in pos.values()), {k:(v['subVisible'],v['primary']) for k,v in pos.items()})
        check("70 the guide button and Quick Pick ask a question, not name a document",
              all(('?' in v['btn'] or '？' in v['btn']) and v['qp']==v['btn'] for v in pos.values()), {k:v['btn'] for k,v in pos.items()})
        # openState: synthetic clocks, so the answer does not depend on when this runs
        logic=await pg70.evaluate("""()=>{
            const H={r:[[1,5,540,990,0]]}, O={r:[[5,6,1200,120,0]]}, F={r:[[1,7,480,null,0]]}, U={r:[[1,7,null,null,0]]};
            const s=(h,d,m)=>openState(h,{d:d,m:m});
            return [s(H,3,720).open===true && s(H,3,720).until===990, s(H,3,1020).open===false, s(H,7,720).open===false,
                    s(O,6,60).open===true, s(O,7,60).open===true, s(O,1,60).open===false,
                    s(F,2,600).open===true, s(U,2,600)===null, openState(null)===null,
                    openState({a:true}).open===true, openState({k:'hPrayer5'})===null];}""")
        check("70 open-now logic: weekday windows, overnight ranges, open-from, and unknown stays unknown",
              all(logic), logic)
        # the filter through the real controls, and its chip, and reset
        flt=await pg70.evaluate("""()=>{resetAll();const all=M.filter(m=>markerHome().hasLayer(m)).length;
            document.getElementById('qpOpen').click();
            const on=M.filter(m=>markerHome().hasLayer(m)).length;
            const shownOpen=M.filter(m=>markerHome().hasLayer(m)).every(m=>(openState(m.data.h)||{}).open===true);
            const chip=!!document.querySelector('.af-chip .x[data-kind=open]');
            const active=document.getElementById('qpOpen').classList.contains('active');
            document.querySelector('.af-chip .x[data-kind=open]').click();
            const back=M.filter(m=>markerHome().hasLayer(m)).length;
            document.getElementById('qpOpen').click();resetAll();
            const afterReset=M.filter(m=>markerHome().hasLayer(m)).length&&!openNow;
            return {all,on,shownOpen,chip,active,back,afterReset};}""")
        check("70 'open now' filters to places known to be open, shows a chip, clears, and reset clears it",
              flt['on']<flt['all'] and flt['shownOpen'] and flt['chip'] and flt['active'] and flt['back']==flt['all'] and flt['afterReset'], flt)
        # the popup: an open/closed pill next to hours, never for unknown hours
        # 2026-09-10 (fresh scan): hours flagged `q` (an office's hours, not the
        # venue's) or `se` (seasonal) answer "unknown" — a spray park in January
        # is not "open now" — so the pill is checked on a place with plain hours,
        # and its absence on a qualified one.
        pill=await pg70.evaluate("""()=>{const withH=P.find(p=>p.h&&p.h.r&&p.h.r[0][2]!==null&&!p.h.q&&!p.h.se);const noH=P.find(p=>!p.h);
            const qual=P.find(p=>p.h&&p.h.r&&(p.h.q||p.h.se));
            const a=popup(withH,0), b=popup(noH,0), c=qual?popup(qual,0):'';
            return {withHours:/pv-open (on|off)/.test(a), withoutHours:!/pv-open/.test(b), qualified:!/pv-open/.test(c)};}""")
        check("70 the popup states open/closed when it can and stays silent when it cannot", pill['withHours'] and pill['withoutHours'] and pill['qualified'], pill)
        # the reverse entry: from an office's popup into the card that names it
        await pg70.evaluate("()=>{resetAll();const m=M.find(x=>x.data.n==='Service BC Centre');focusMarker(m,16);}")
        await pg70.wait_for_timeout(1500)
        rev=await pg70.evaluate("""()=>{const c=document.querySelector('.leaflet-popup-content');
            const go=c&&c.querySelector('.pv-task-go');if(!go)return {no:'no entry'};
            const n0=_evBuf.length;go.click();
            return {opened:document.getElementById('guideBackdrop').classList.contains('open'),
                    card:(document.querySelector('#guideTasks h4')||{}).textContent||null,
                    ev:_evBuf.slice(n0).map(e=>e.t+':'+(e.p&&e.p.src)+':'+(e.p&&e.p.task))};}""")
        check("70 a place's popup opens the card that names it, and says which door was used",
              rev.get('opened') and rev.get('card') and 'guide_open:popup:msp' in rev.get('ev',[]), rev)
        await pg70.keyboard.press('Escape'); await pg70.wait_for_timeout(250)
        # the popup and quick pick are on every place a card names
        cov=await pg70.evaluate("""()=>TASKS.filter(t=>t.place).map(t=>{const p=P.find(x=>x.id===t.place);return p?/pv-task-go/.test(popup(p,0)):false;})""")
        check("70 every card with an office is reachable back from that office's popup", all(cov) and len(cov)>=8, cov)
        check("70 no page errors across round 70", len(e70)==0, e70[:3])
        await pg70.close()

        print("\n--- the backlog, implemented (round 71) ---")
        pg71=await b.new_page(viewport={'width':1280,'height':900})
        e71=[]; pg71.on('pageerror', lambda e: e71.append(str(e)))
        # a deep link opens its card, and only names the card — never a tick
        await pg71.goto(URL+'?city=kamloops&lang=zh&task=licence'); await pg71.wait_for_timeout(1500)
        dl=await pg71.evaluate("()=>({open:document.getElementById('guideBackdrop').classList.contains('open'),card:(document.querySelector('#guideTasks h4')||{}).textContent,url:location.search})")
        check("71 ?task= opens that card and carries no personal state", dl['open'] and '驾照' in (dl['card'] or '') and 'done' not in dl['url'], dl)
        await pg71.keyboard.press('Escape'); await pg71.wait_for_timeout(200)
        # first-use card: shown once, every door works, never again after dismissal
        # 2026-09-13 (item 1): the card is one honest line now — the doors moved
        # into the search box's suggestions; the flyer variant is checked in round 74
        fu=await pg71.evaluate("""()=>{localStorage.removeItem('kamloopsFirstUseSeen');renderFirstUse();
            const el=document.getElementById('firstUse');const shown=!el.hidden;
            const n=el.querySelectorAll('[data-go]').length;const slim=el.classList.contains('slim');
            const safe=(el.querySelector('.fu-safe')||{}).textContent||'';
            el.querySelector('#fuClose').click();
            return {shown,n,slim,safe:safe.length>10,hiddenAfter:el.hidden,stored:localStorage.getItem('kamloopsFirstUseSeen')};}""")
        check("71 the first-use card shows once as one line, closes, and stays dismissed", fu['shown'] and fu['n']==0 and fu['slim'] and fu['safe'] and fu['hiddenAfter'] and fu['stored']=='1', fu)
        await pg71.reload(); await pg71.wait_for_timeout(1300)
        check("71 …and does not come back on the next visit", await pg71.evaluate("()=>document.getElementById('firstUse').hidden"))
        # 2026-09-24 (p33): "open now" no longer hangs the 24-hour lines under the chip row;
        # they still sit above the guide's 'need help' bucket, all dialable
        hl=await pg71.evaluate("""()=>{openNow=true;updateOpenQuickpick();apply();
            const a=document.querySelectorAll('#activeFilters .hotlines .hl-line').length;
            openNow=false;updateOpenQuickpick();apply();
            document.getElementById('guideToggle').click();
            const g=document.querySelectorAll('#guideTasks .hotlines.compact .hl-line').length;
            return {a,g,tel:[...document.querySelectorAll('#guideTasks .hl-line')].every(x=>/^tel:\\d+$/.test(x.getAttribute('href')))};}""")
        check("71 'open now' shows no crisis lines under the filters; they stay above 'when you need help', all dialable", hl['a']==0 and hl['g']>=4 and hl['tel'], hl)
        # arrival date turns '90 days' into a date, sorts, and stays on the device
        ar=await pg71.evaluate("""()=>{renderTaskList();const i=document.getElementById('arriveDate');i.value='2026-08-01';i.dispatchEvent(new Event('change'));
            const first=document.querySelector('.task-card').dataset.task;
            const badge=(document.querySelector('.task-card[data-task=licence] .task-dl')||{}).textContent||'';
            const inUrl=/2026-08-01/.test(location.href);
            setArrival(null);renderTaskList();return {first,badge,inUrl};}""")
        check("71 an arrival date dates the licence deadline, sorts it first, and never enters the URL", ar['first']=='licence' and '2026' in ar['badge'] and not ar['inUrl'], ar)
        # caveats sit on the cards that carry the risk, and only those
        cv=await pg71.evaluate("""()=>{const o={};['legal','sick','tax','sin','connect'].forEach(id=>{renderTaskList();document.querySelector('.task-card[data-task='+id+']').click();o[id]=!!document.querySelector('.task-caveat');});return o;}""")
        check("71 not-advice caveats on legal, health and tax cards — and not on the others", cv['legal'] and cv['sick'] and cv['tax'] and not cv['sin'] and not cv['connect'], cv)
        # the guide search finds a card by the reader's word and by its office's alias
        gs=await pg71.evaluate("""()=>{renderTaskList();const i=document.getElementById('taskSearch');
            const q=w=>{i.value=w;i.dispatchEvent(new Event('input'));return [...document.querySelectorAll('.task-card')].map(e=>e.dataset.task);};
            const r={a:q('老人'),b:q('licence'),c:q('zzzz').length};i.value='';i.dispatchEvent(new Event('input'));return r;}""")
        check("71 the guide's own search finds cards by word and alias, and empties honestly", gs['a']==['eldercare'] and 'licence' in gs['b'] and gs['c']==0, gs)
        # stuck → an exit, not just thanks
        st=await pg71.evaluate("""()=>{renderTaskList();document.querySelector('.task-card[data-task=msp]').click();document.querySelector('.task-fb-b[data-r=stuck]').click();
            const x=document.querySelector('.task-stuck-exit');return x?x.querySelectorAll('a[href^=tel]').length:0;}""")
        check("71 'I got stuck' hands over two phone numbers", st==2, st)
        await pg71.keyboard.press('Escape'); await pg71.wait_for_timeout(200)
        # landmark labels carry a gloss in the reader's language
        gl=await pg71.evaluate("""()=>{const o={};['zh','ko','fr','en'].forEach(l=>{setLang(l);o[l]=[...document.querySelectorAll('.leaflet-tooltip.landmark-label .lm-g')].length;});setLang('en');return o;}""")
        check("71 landmark labels are glossed for non-English readers, bare for English", gl['zh']==6 and gl['ko']==6 and gl['fr']==6 and gl['en']==0, gl)
        # quarantine: none of the doubtful rows is on the map
        qq=await pg71.evaluate("()=>({q:typeof QUARANTINE!=='undefined'?QUARANTINE.length:0,leak:typeof QUARANTINE!=='undefined'?QUARANTINE.filter(x=>P.some(p=>p.n===x.n)).length:0})")
        check("71 the quarantined rows exist for the record and are absent from the map", qq['q']>=7 and qq['leak']==0, qq)
        check("71 the printed-source parameter is recorded on session_start", await pg71.evaluate("()=>{const s=_evBuf.find(e=>e.t==='session_start');return !!s&&('src' in s.p||s.p.src===undefined);}"))
        check("71 no page errors across round 71", len(e71)==0, e71[:3])
        await pg71.close()

        print("\n--- quick picks in context; sid rotation (round 72) ---")
        pg72=await b.new_page(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True)
        e72=[]; pg72.on('pageerror', lambda e: e72.append(str(e)))
        await pg72.goto(URL+'?src=flyer-f-2609'); await pg72.wait_for_timeout(1500)
        row=await pg72.evaluate("""()=>{const v=[...document.querySelectorAll('#presetRow .preset-chip')].filter(e=>!e.hidden);
            return {ids:v.map(e=>e.id),n:v.length,first:v[0]&&v[0].id,last:v[v.length-1]&&v[v.length-1].id,
                    more:document.getElementById('qpMore').textContent.trim(),
                    setsInRow:['kids','edu','health','sports','outdoor','shopping','auto'].filter(id=>document.getElementById(id).closest('#presetRow')).length,
                    setsInSheet:['kids','edu','health','sports','outdoor','shopping','auto'].filter(id=>document.getElementById(id).closest('#panelCat')).length};}""")
        check("72 the row is guide-first, More-last, and at most eight chips", row['first']=='qpGuide' and row['last']=='qpMore' and 6<=row['n']<=8, row)
        check("72 the seven category sets moved from the row into the Category sheet", row['setsInRow']==0 and row['setsInSheet']==7, row)
        check("72 a flyer arrival puts the newcomer set right after the guide", row['ids'][1]=='newcomer' or (row['ids'][1]=='qpOpen' and row['ids'][2]=='newcomer'), row['ids'])
        rules=await pg72.evaluate("""()=>({
            noon:quickPickOrder({h:12,d:2,mo:6,src:'',visits:1}),
            evening:quickPickOrder({h:19,d:2,mo:6,src:'',visits:1}),
            sunday:quickPickOrder({h:10,d:7,mo:6,src:'',visits:1}),
            winter:quickPickOrder({h:12,d:2,mo:1,src:'',visits:1}),
            returning:quickPickOrder({h:12,d:2,mo:6,src:'',visits:3}),
            indoorOn:quickPickOrder({h:12,d:2,mo:7,src:'',visits:1,on:{indoor:true}})})""")
        check("72 ordering rules: evening/Sunday lift Open now, winter shows Indoor, returning demotes the newcomer set",
              rules['noon'][1]=='daily' and 'qpIndoor' not in rules['noon']
              and rules['evening'][1]=='qpOpen' and rules['sunday'][1]=='qpOpen' and rules['sunday'].index('qpFamily')<rules['sunday'].index('newcomer')
              and rules['winter'].index('qpIndoor')==3 and rules['indoorOn'].index('qpIndoor')==3
              and rules['returning'].index('newcomer')>rules['returning'].index('qpFamily')
              and all(r[0]=='qpGuide' and r[-1]=='qpMore' for r in rules.values()), rules)
        await pg72.click('#qpMore'); await pg72.wait_for_timeout(500)
        more=await pg72.evaluate("""()=>({open:document.getElementById('panel').classList.contains('open'),mode:panelMode,
            first:document.querySelector('#panelCat .psec').id,label:document.getElementById('presetSecLabel').textContent.trim().length>2,
            kidsVisible:document.getElementById('kids').getBoundingClientRect().height>0,
            ev:_evBuf.some(e=>e.t==='qp_more')})""")
        check("72 More opens the Category sheet with the sets section first", more['open'] and more['mode']=='cat' and more['first']=='presetSec' and more['label'] and more['kidsVisible'] and more['ev'], more)
        await pg72.click('#kids'); await pg72.wait_for_timeout(450)
        kk=await pg72.evaluate("()=>({active:document.getElementById('kids').classList.contains('active'),n:aC.size,vis:lastVisible,stillOpen:document.getElementById('panel').classList.contains('open')})")
        check("72 a set chip in the sheet still selects its categories and keeps the sheet open", kk['active'] and kk['n']>=10 and 0<kk['vis']<N and kk['stillOpen'], kk)
        await pg72.click('#kids'); await pg72.wait_for_timeout(300)
        await pg72.keyboard.press('Escape'); await pg72.wait_for_timeout(300)
        # desktop: the More click must not count as a click outside the panel
        pg72d=await b.new_page(viewport={'width':1280,'height':900})
        await pg72d.goto(URL); await pg72d.wait_for_timeout(1200)
        await pg72d.click('#qpMore'); await pg72d.wait_for_timeout(400)
        check("72 desktop: More opens the Category panel and it stays open", await pg72d.evaluate("()=>document.getElementById('panel').classList.contains('open')&&panelMode==='cat'"))
        await pg72d.close()
        sid=await pg72.evaluate("""()=>{const a=getSid();const at1=localStorage.getItem('kamloopsSidAt');
            localStorage.setItem('kamloopsSidAt',String(Date.now()-100*24*3600*1000));const b=getSid();
            const at2=parseInt(localStorage.getItem('kamloopsSidAt'),10);
            return {stamped:!!at1,rotated:a!==b,fresh:Date.now()-at2<5000,shape:/^[a-z0-9]{12,32}$/.test(b)};}""")
        check("72 the session id carries a birth date and is rotated after 90 days", sid['stamped'] and sid['rotated'] and sid['fresh'] and sid['shape'], sid)
        v1=await pg72.evaluate("()=>parseInt(localStorage.getItem('kamloopsVisits'),10)")
        await pg72.reload(); await pg72.wait_for_timeout(1200)
        v2=await pg72.evaluate("()=>({n:parseInt(localStorage.getItem('kamloopsVisits'),10),ss:(_evBuf.slice().reverse().find(e=>e.t==='session_start')||{p:{}}).p.visits})")
        check("72 visits are counted per load and reported on session_start", v1>=1 and v2['n']==v1+1 and v2['ss']==v1+1, (v1,v2))
        # print a card: the body is position:fixed while a sheet is open, which used
        # to print as a blank page on desktop
        pg72p=await b.new_page(viewport={'width':1280,'height':900})
        await pg72p.goto(URL+'?lang=en&task=msp'); await pg72p.wait_for_timeout(1500)
        await pg72p.evaluate("()=>{window.print=()=>{};document.getElementById('taskPrint').click();}")
        await pg72p.emulate_media(media='print'); await pg72p.wait_for_timeout(100)
        prt=await pg72p.evaluate("""()=>{const r=s=>{const e=document.querySelector(s);return e?e.getBoundingClientRect():{height:0,width:0};};
            const gone=s=>{const e=document.querySelector(s);return !e||getComputedStyle(e).display==='none';};
            return {cls:document.body.classList.contains('print-task'),bodyPos:getComputedStyle(document.body).position,
                    modalH:Math.round(r('#guideTasks').height),modalW:Math.round(r('#guideTasks').width),
                    map:gone('#map'),tools:gone('.task-tools'),guide:gone('#guideBody'),header:gone('header'),
                    white:getComputedStyle(document.body).backgroundColor==='rgb(255, 255, 255)'};}""")
        pdfp=os.path.join(tempfile.gettempdir(),'kl-print-check.pdf')
        await pg72p.pdf(path=pdfp, format='Letter', print_background=True)
        # 2026-10-03: without pdftotext the old fallback text lacked the address, so this
        # check failed on every machine without poppler. Now the PDF-text half is skipped
        # (and said so); the layout half above still runs.
        try: ptxt=subprocess.run(['pdftotext',pdfp,'-'],capture_output=True,text=True,timeout=30).stdout
        except Exception: ptxt=None
        if ptxt is None:
            # no poppler (Homebrew has no bottle for some Macs): read the PDF with pypdf
            try:
                import pypdf
                ptxt='\n'.join((pg_.extract_text() or '') for pg_ in pypdf.PdfReader(pdfp).pages)
            except Exception: ptxt=None
        if ptxt is None:
            print('  SKIP  72 PDF text check — neither pdftotext nor pypdf available (.venv/bin/pip install pypdf)')
            prt['pdfHasCard']=prt['pdfNoChrome']=True
        else:
            prt['pdfHasCard']=('Service BC' in ptxt) and ('455 Columbia' in ptxt)
            prt['pdfNoChrome']=('Quick Picks' not in ptxt) and ('Bus Routes' not in ptxt)
        check("72 printing a card lays the card out on a white page with the app chrome gone",
              prt['cls'] and prt['bodyPos']=='static' and prt['modalH']>200 and prt['modalW']>600 and prt['map'] and prt['tools'] and prt['guide'] and prt['header'] and prt['white'] and prt['pdfHasCard'] and prt['pdfNoChrome'], prt)
        await pg72p.emulate_media(media='screen'); await pg72p.evaluate("()=>window.dispatchEvent(new Event('afterprint'))")
        check("72 afterprint restores the screen layout", not await pg72p.evaluate("()=>document.body.classList.contains('print-task')"))
        await pg72p.close()
        check("72 no page errors across round 72", len(e72)==0, e72[:3])
        await pg72.close()

        print("\n--- launch audit fixes (round 73) ---")
        pg73=await b.new_page(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True)
        e73=[]; pg73.on('pageerror', lambda e: e73.append(str(e)))
        await pg73.goto(URL); await pg73.wait_for_timeout(1500)
        # single-result search: popup inside the map, at street zoom, twice in a row
        async def single(term):
            await pg73.fill('#searchInput',term); await pg73.wait_for_timeout(900)
            return await pg73.evaluate("""()=>{const pp=document.querySelector('.leaflet-popup');const mr=document.getElementById('map').getBoundingClientRect();
              return {z:map.getZoom(),v:lastVisible,popup:!!pp,top:pp?Math.round(pp.getBoundingClientRect().top-mr.top):-999};}""")
        s1=await single('South Kamloops Secondary')
        await pg73.click('#searchClear'); await pg73.wait_for_timeout(400)
        s2=await single('South Kamloops Secondary')
        check("73 a single search result opens its popup inside the map at street zoom, and again after clearing", s1['v']==1 and s1['popup'] and s1['top']>=0 and s1['z']>=15 and s2['popup'] and s2['top']>=0, (s1,s2))
        # a re-run of apply() with nothing changed must not move the view or reopen the popup
        await pg73.evaluate("()=>{map.closePopup();map.setZoom(13);}"); await pg73.wait_for_timeout(400)
        await pg73.evaluate("()=>apply()"); await pg73.wait_for_timeout(400)
        still=await pg73.evaluate("()=>({z:map.getZoom(),popup:!!document.querySelector('.leaflet-popup')})")
        check("73 re-applying unchanged filters (the minute tick) leaves the view and the closed popup alone", still['z']==13 and not still['popup'], still)
        await pg73.click('#searchClear'); await pg73.wait_for_timeout(400)
        # a search whose best result is hidden by a filter focuses the visible one
        # (2026-09-22: categories pause during a search, so an area does the hiding —
        #  "shoppers" ranks the Summit store first; North Shore shows only Tranquille)
        hid=await pg73.evaluate("""()=>{aR=new Set(['ns']);renderRegs();apply();searchInputEl.value='shoppers';runSearch();
            const pp=document.querySelector('.leaflet-popup');return {v:lastVisible,name:pp?pp.querySelector('.pt').textContent:''};}""")
        await pg73.wait_for_timeout(600)
        hid2=await pg73.evaluate("()=>{const pp=document.querySelector('.leaflet-popup');return {v:lastVisible,name:pp?pp.querySelector('.pt').textContent:''};}")
        check("73 the single visible result is the one focused, not a filtered-out match", hid2['v']==1 and 'Shoppers' in hid2['name'], hid2)
        await pg73.evaluate("()=>resetAll()"); await pg73.wait_for_timeout(400)
        # open-now round-trips through the URL and re-lights a preset
        onurl=await pg73.evaluate("""()=>{document.getElementById('qpOpen').click();document.getElementById('daily').click();return location.search;}""")
        await pg73.goto(URL+onurl); await pg73.wait_for_timeout(1500)
        rt=await pg73.evaluate("()=>({open:openNow,chip:document.getElementById('qpOpen').classList.contains('active'),daily:document.getElementById('daily').classList.contains('active'),sp:selPresets.has('daily')})")
        check("73 open-now and the Daily preset survive a reload through the URL", 'o=1' in onurl and rt['open'] and rt['chip'] and rt['daily'] and rt['sp'], (onurl,rt))
        await pg73.evaluate("()=>resetAll()"); await pg73.wait_for_timeout(300)
        # panel counts follow open-now and the search term
        cnt=await pg73.evaluate("""()=>{searchInputEl.value='bank';runSearch();renderCats();
            const b=[...document.querySelectorAll('#catGrid .cat-btn')].find(x=>x.textContent.includes('Bank'));const m=b?parseInt((b.querySelector('.cnt').textContent.match(/\\d+/)||[0])[0],10):-1;
            const sch=[...document.querySelectorAll('#catGrid .cat-btn')].find(x=>x.textContent.includes('High Schools'));const ms=sch?parseInt((sch.querySelector('.cnt').textContent.match(/\\d+/)||[0])[0],10):-1;
            searchInputEl.value='';runSearch();return {bank:m,school:ms,vis:lastVisible};}""")
        check("73 category counts in the sheet follow the search term", cnt['bank']>0 and cnt['school']==0, cnt)
        # a standalone popup (favourite hidden by a filter) follows the language
        await pg73.evaluate("""()=>{resetAll();const m=M.find(x=>x.data.c==='school');favorites.add(m.data.id);aC=new Set(['bank']);renderCats();apply();window._spm=m;}""")
        await pg73.wait_for_timeout(500)
        await pg73.evaluate("()=>focusMarker(window._spm,16)"); await pg73.wait_for_timeout(700)
        sp=await pg73.evaluate("""()=>{const pp=document.querySelector('.leaflet-popup');const mr=document.getElementById('map').getBoundingClientRect();
            const top=pp?Math.round(pp.getBoundingClientRect().top-mr.top):-999;setLang('zh');const zh=document.querySelector('.leaflet-popup')?.textContent||'';setLang('en');
            favorites.delete(window._spm.data.id);resetAll();return {top,zh:/导航|电话|时间|路线/.test(zh)};}""")
        check("73 a filtered-out favourite opens inside the map and re-renders on language switch", sp['top']>=0 and sp['zh'], sp)
        # translated Leaflet controls, named map and dialogs
        await pg73.evaluate("()=>setLang('fr')"); await pg73.wait_for_timeout(300)
        a11y=await pg73.evaluate("""()=>{const zi=document.querySelector('.leaflet-control-zoom-in');const mp=document.getElementById('map');
            openGuide('header');const lb=guideBackdropEl.getAttribute('aria-labelledby');closeModal(guideBackdropEl);
            const out={zoom:zi&&zi.getAttribute('aria-label'),map:mp.getAttribute('aria-label'),role:mp.getAttribute('role'),lb};setLang('en');return out;}""")
        check("73 Leaflet controls, the map and the dialogs are named in the reader's language", a11y['zoom']=='Zoom avant' and a11y['role']=='region' and 'Kamloops' in (a11y['map'] or '') and a11y['lb']=='guideTitle', a11y)
        await pg73.wait_for_timeout(300)
        # Escape in the guide search clears the box instead of closing the guide; the list follows
        esc=await pg73.evaluate("""()=>{openGuide('header');const ts=document.getElementById('taskSearch');ts.value='bank';ts.dispatchEvent(new Event('input',{bubbles:true}));
            const n1=document.querySelectorAll('#taskBuckets .task-card').length;
            ts.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));
            const n2=document.querySelectorAll('#taskBuckets .task-card').length;const open=guideBackdropEl.classList.contains('open');
            ts.value='';ts.dispatchEvent(new Event('search',{bubbles:true}));
            return {n1,n2,open,q:_taskQ};}""")
        check("73 Escape in the guide search clears the box, keeps the guide open, and the list follows", esc['n1']<esc['n2'] and esc['n2']>=14 and esc['open'] and esc['q']=='', esc)
        await pg73.keyboard.press('Escape'); await pg73.wait_for_timeout(300)
        # whole calendar days for deadlines
        dl=await pg73.evaluate("""()=>{const t=localISODate();setArrival(t);const d=deadlineDate({id:'licence'});const n=daysLeft(d);setArrival(null);return n;}""")
        check("73 the licence deadline counts 90 whole days from today, morning or afternoon", dl==90, dl)
        # arrival date works with storage blocked
        mem=await pg73.evaluate("""()=>{const real=localStorage;try{Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked');},configurable:true});
            setArrival('2026-06-01');const a=arrivalDate();setArrival(null);const b=arrivalDate();
            Object.defineProperty(window,'localStorage',{value:real,configurable:true});return {a,b};}catch(e){return {err:String(e)};}}""")
        check("73 the arrival date still works for the sitting when storage is blocked", mem.get('a')=='2026-06-01' and mem.get('b') is None, mem)
        # in-app browser: share-sheet email copies the link, not an empty address
        pgw=await b.new_page(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True, user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.40')
        await pgw.goto(URL); await pgw.wait_for_timeout(1400)
        wx=await pgw.evaluate("""()=>{window._cp='';document.execCommand=()=>{const ta=document.activeElement;window._cp=ta&&ta.value||'';return true;};
            document.getElementById('shareBtn').click();const a=document.querySelector('#shareBackdrop a[href^="mailto:"]');if(!a)return {noLink:true};a.click();
            const t=document.querySelector('.toast');return {inApp:IN_APP_BROWSER,copied:window._cp,toast:t?t.textContent:''};}""")
        check("73 in an in-app browser the share sheet's Email copies the link and says so", wx.get('inApp') and 'city=' in (wx.get('copied') or '') and 'copied' in (wx.get('toast') or '').lower(), wx)
        await pgw.close()
        # landscape phone keeps the map on screen
        pgl=await b.new_page(viewport={'width':844,'height':390}, has_touch=True, is_mobile=True)
        await pgl.goto(URL); await pgl.wait_for_timeout(1200)
        land=await pgl.evaluate("()=>{const r=document.getElementById('map').getBoundingClientRect();return {top:Math.round(r.top),visible:Math.round(Math.min(r.bottom,innerHeight)-r.top),hscroll:document.documentElement.scrollWidth>innerWidth};}")
        check("73 a phone held sideways sees the map without scrolling", land['visible']>=150 and not land['hscroll'], land)
        await pgl.close()
        # 320px: language buttons on one line
        pgs=await b.new_page(viewport={'width':320,'height':568}, has_touch=True, is_mobile=True)
        await pgs.goto(URL); await pgs.wait_for_timeout(1200)
        await pgs.click('#langMenuBtn'); await pgs.wait_for_timeout(200)
        lb=await pgs.evaluate("()=>[...document.querySelectorAll('.lang-btn')].map(b=>Math.round(b.getBoundingClientRect().height))")
        check("73 320px: every language button stays on one line", max(lb)-min(lb)<=2 and max(lb)<=44 and min(lb)>0, lb)
        await pgs.keyboard.press('Escape')
        await pgs.close()
        # the card footer date comes from the data layer and nothing leaks
        foot=await pg73.evaluate("()=>{openGuide('header','msp');const f=document.querySelector('.task-checked');const t=f?f.textContent:'';closeModal(guideBackdropEl);return t;}")
        check("73 the card footer carries the data layer's check date", '{TD}' not in foot and CITY_TASKS_CHECKED in foot, foot)
        check("73 no page errors across round 73", len(e73)==0, e73[:3])
        await pg73.close()

        print("\n--- UX batch: search-led first use, timeline, steps, distance, language menu, icons (round 74) ---")
        pg74=await b.new_page(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True)
        e74=[]; pg74.on('pageerror', lambda e: e74.append(str(e)))
        # item 2: a flyer arrival gets the flyer's three promises as buttons
        await pg74.goto(URL+'?src=flyer-f-2609'); await pg74.wait_for_timeout(1500)
        fl=await pg74.evaluate("""()=>{localStorage.removeItem('kamloopsFirstUseSeen');renderFirstUse();const el=document.getElementById('firstUse');
            return {flyer:el.classList.contains('flyer'),doors:[...el.querySelectorAll('[data-go]')].map(b=>b.dataset.go)};}""")
        check("74 arriving from a flyer, the first-use card offers the flyer's three cards", fl['flyer'] and fl['doors']==['task:msp','task:sin','task:settle'], fl)
        await pg74.evaluate("()=>document.querySelector('#firstUse [data-go=\"task:msp\"]').click()"); await pg74.wait_for_timeout(500)
        check("74 …and each door opens its card", await pg74.evaluate("()=>guideBackdropEl.classList.contains('open')&&_taskOpen==='msp'"))
        await pg74.keyboard.press('Escape'); await pg74.wait_for_timeout(300)
        # item 1: suggestions on focus, gone on typing; each one acts
        await pg74.goto(URL+'?lang=zh'); await pg74.wait_for_timeout(1500)
        await pg74.focus('#searchInput'); await pg74.wait_for_timeout(250)
        sg=await pg74.evaluate("()=>({hidden:document.getElementById('searchSuggest').hidden,n:document.querySelectorAll('#searchSuggest button').length,rot:Array.isArray(UI.zh.searchPhRot)&&UI.zh.searchPhRot.length===3})")
        check("74 an empty search box offers four suggestions on focus", (not sg['hidden']) and sg['n']==4 and sg['rot'], sg)
        await pg74.fill('#searchInput','bank'); await pg74.wait_for_timeout(200)
        check("74 …which disappear once there is text", await pg74.evaluate("()=>document.getElementById('searchSuggest').hidden"))
        await pg74.click('#searchClear'); await pg74.wait_for_timeout(200)
        await pg74.focus('#searchInput'); await pg74.wait_for_timeout(250)
        await pg74.click('#searchSuggest button:nth-of-type(3)'); await pg74.wait_for_timeout(700)
        ph=await pg74.evaluate("()=>({open:openNow,cats:[...aC],vis:lastVisible,sug:document.getElementById('searchSuggest').hidden})")
        check("74 'which pharmacy is open now' sets pharmacy + open-now", ph['open'] and ph['cats']==['pharmacy'] and ph['sug'], ph)
        await pg74.evaluate("()=>resetAll()"); await pg74.wait_for_timeout(200)
        await pg74.focus('#searchInput'); await pg74.wait_for_timeout(250)
        await pg74.click('#searchSuggest button:nth-of-type(4)'); await pg74.wait_for_timeout(600)
        bt=await pg74.evaluate("()=>({panel:document.getElementById('panel').classList.contains('open'),mode:panelMode,q:_busQ,n:document.querySelectorAll('#busList .bus-item').length})")
        check("74 'which bus goes to TRU' opens the bus sheet filtered to TRU", bt['panel'] and bt['mode']=='bus' and bt['q']=='TRU' and 0<bt['n']<14, bt)
        await pg74.keyboard.press('Escape'); await pg74.wait_for_timeout(300)
        # item 3: a card opened from a link is the page — one Back leaves
        await pg74.goto(URL+'?lang=en'); await pg74.wait_for_timeout(800)
        await pg74.goto(URL+'?task=msp'); await pg74.wait_for_timeout(1500)
        dl3=await pg74.evaluate("()=>({open:guideBackdropEl.classList.contains('open'),task:_taskOpen,st:!!(history.state&&history.state.kSheet)})")
        await pg74.go_back(); await pg74.wait_for_timeout(600)
        left='task=msp' not in pg74.url
        check("74 a card opened from a link pushes no history: one Back leaves", dl3['open'] and dl3['task']=='msp' and not dl3['st'] and left, (dl3,pg74.url))
        # item 7 + 4: timeline order, step ticks, auto-done, progress by steps
        await pg74.goto(URL+'?lang=zh'); await pg74.wait_for_timeout(1500)
        tl=await pg74.evaluate("""()=>{openGuide('header');const ids=[...document.querySelectorAll('#taskBuckets .task-card')].map(c=>c.dataset.task);
            const due=[...document.querySelectorAll('#taskBuckets .task-due')].map(x=>x.textContent);
            return {first:ids.slice(0,6),lic:ids.indexOf('licence'),tax:ids.indexOf('tax'),dueN:due.length,allDue:TASKS.every(t=>t.due)};}""")
        check("74 the list runs on a timeline: week-1 cards before the 90-day and tax-season ones", tl['allDue'] and tl['lic']>tl['first'].index('bank') and tl['tax']>tl['lic'] and tl['dueN']>=5, tl)
        st=await pg74.evaluate("""()=>{openTask('sin','t');const cbs=[...document.querySelectorAll('.task-step input')];
            cbs[0].checked=true;cbs[0].dispatchEvent(new Event('change'));const one={sd:(stepDone.sin||[]).slice(),done:taskDone.has('sin')};
            cbs.forEach(cb=>{if(!cb.checked){cb.checked=true;cb.dispatchEvent(new Event('change'));}});const all={sd:(stepDone.sin||[]).slice(),done:taskDone.has('sin')};
            cbs[0].checked=false;cbs[0].dispatchEvent(new Event('change'));const un={sd:(stepDone.sin||[]).slice(),done:taskDone.has('sin')};
            document.getElementById('taskTick').click();const btn={done:taskDone.has('sin'),all:cbs.every(c=>c.checked)};
            document.getElementById('taskBack').click();const pc=(document.querySelector('.task-pc')||{}).textContent||'';
            return {n:cbs.length,one,all,un,btn,pc};}""")
        check("74 steps tick one by one; the last tick marks the card done, an un-tick un-marks it, the button ticks all",
              st['n']==2 and st['one']['sd']==[0] and not st['one']['done'] and st['all']['done'] and st['all']['sd']==[0,1]
              and not st['un']['done'] and st['un']['sd']==[1] and st['btn']['done'] and st['btn']['all'] and '/' in st['pc'], st)
        await pg74.evaluate("()=>{closeModal(guideBackdropEl);}"); await pg74.wait_for_timeout(300)
        # (file:// pages share storage: start from a clean slate, earlier rounds tick cards)
        await pg74.evaluate("()=>{taskDone.clear();stepDone={};saveTaskDone();saveStepDone();setArrival(null);}")
        strip=await pg74.evaluate("()=>{toggleTaskDone('sin');updateGuideProgress();const el=document.getElementById('guideProgress');const t=el.textContent;const shown=!el.hidden;toggleTaskDone('sin');return {shown,week:t.indexOf(UI.zh.gpThisWeek)>=0};}")
        check("74 once started, the landing strip names this week's next card", strip['shown'] and strip['week'], strip)
        await pg74.evaluate("()=>{taskDone.clear();stepDone={};saveTaskDone();saveStepDone();}")
        # item 10A / 11: nearest stop with route buttons; distance once located; 15-min-walk chip
        ns=await pg74.evaluate("""()=>{const m=M.find(x=>/Royal Inland/.test(x.data.n));const html=popup(m.data,m.i);const d=document.createElement('div');d.innerHTML=html;
            return {stop:!!d.querySelector('.pv-stop'),routes:[...d.querySelectorAll('.pv-route')].map(b=>b.dataset.route),dist:!!d.querySelector('.pv-dist'),near:document.getElementById('qpNear').hidden};}""")
        check("74 a place card names its nearest stop and the routes that serve it; no distance before locating", ns['stop'] and len(ns['routes'])>=1 and not ns['dist'] and ns['near'], ns)
        await pg74.evaluate("()=>{userPos=[50.6745,-120.3273];M.forEach(m=>m.setPopupContent(popup(m.data,m.i)));renderFavList();updateNearQuickpick();applyQuickPickOrder();}"); await pg74.wait_for_timeout(200)
        nr=await pg74.evaluate("""()=>{const m=M.find(x=>/Royal Inland/.test(x.data.n));const d=document.createElement('div');d.innerHTML=popup(m.data,m.i);
            const dist=(d.querySelector('.pv-dist')||{}).textContent||'';document.getElementById('qpNear').click();
            const on={near:nearOnly,vis:lastVisible,chip:!!document.querySelector('.af-chip .x[data-kind=near]')};
            const far=M.filter(x=>markerHome().hasLayer(x)).every(x=>distFromUser(x.data)<=NEAR_M);
            resetAll();return {dist,shownChip:!document.getElementById('qpNear').hidden,on,far,after:nearOnly};}""")
        check("74 once located: distance on the card, a '15-min walk' chip that filters and resets", ('m' in nr['dist']) and nr['shownChip'] and nr['on']['near'] and 0<nr['on']['vis']<N and nr['on']['chip'] and nr['far'] and not nr['after'], nr)
        await pg74.evaluate("""()=>{const m=M.find(x=>/Royal Inland/.test(x.data.n));map.setView(m.getLatLng(),16,{animate:false});focusMarker(m);}""")
        await pg74.wait_for_timeout(800)
        rt=await pg74.evaluate("""()=>{const rb=document.querySelector('.leaflet-popup .pv-route');if(!rb)return {noBtn:true};rb.click();return {sel:selectedRoute,k:rb.dataset.route};}""")
        await pg74.wait_for_timeout(500)
        check("74 a route number on the card draws that route", rt.get('sel') and rt['sel']==rt['k'], rt)
        await pg74.evaluate("()=>{userPos=null;resetAll();}"); await pg74.wait_for_timeout(300)
        # item 13: the phone's language menu
        lm=await pg74.evaluate("()=>({btn:document.getElementById('langMenuBtn').offsetHeight>0,listHidden:document.querySelector('.lang-btn').offsetHeight===0,cur:document.getElementById('langMenuCur').textContent})")
        await pg74.click('#langMenuBtn'); await pg74.wait_for_timeout(200)
        lm2=await pg74.evaluate("()=>({open:document.getElementById('langSw').classList.contains('open'),first:document.querySelector('#langMenu .lang-btn').dataset.lang,vis:document.querySelector('.lang-btn').offsetHeight>0})")
        await pg74.click('[data-lang="ko"]'); await pg74.wait_for_timeout(300)
        lm3=await pg74.evaluate("()=>({L:L_,closed:!document.getElementById('langSw').classList.contains('open'),cur:document.getElementById('langMenuCur').textContent})")
        check("74 on a phone the languages sit behind one button: current first, pick closes it", lm['btn'] and lm['listHidden'] and lm['cur']=='中文' and lm2['open'] and lm2['first']=='zh' and lm2['vis'] and lm3['L']=='ko' and lm3['closed'] and lm3['cur']=='한국어', (lm,lm2,lm3))
        await pg74.evaluate("()=>setLang('en')")
        # item 15: the chrome draws its icons; the six-language strings keep their emoji
        ic=await pg74.evaluate("""()=>({filters:[...document.querySelectorAll('.fbicon')].every(e=>e.querySelector('svg.ic')),
            header:[...document.querySelectorAll('.hl-ic')].filter(e=>e.closest('[hidden]')===null).every(e=>e.querySelector('svg.ic')),
            qp:!!document.querySelector('#qpGuide svg.ic')&&!!document.querySelector('#daily svg.ic')&&!!document.querySelector('#qpOpen svg.ic'),
            search:!!document.querySelector('.search-ic svg.ic'),
            popup:(()=>{const m=M[0];const d=document.createElement('div');d.innerHTML=popup(m.data,m.i);return d.querySelectorAll('.pact-btn svg.ic').length>=1;})(),
            emojiKept:UI.en.guideToggleLabel.indexOf('🧭')===0,
            lang:typeof ICONS==='object'&&Object.keys(ICONS).length>=40})""")
        check("74 the chrome uses the line-icon set; strings keep their emoji as the fallback", all(ic.values()), ic)
        pg74d=await b.new_page(viewport={'width':1280,'height':900})
        await pg74d.goto(URL); await pg74d.wait_for_timeout(1200)
        dk=await pg74d.evaluate("()=>({menuHidden:document.getElementById('langMenuBtn').offsetHeight===0,six:[...document.querySelectorAll('.lang-btn')].filter(b=>b.offsetHeight>0).length,order:[...document.querySelectorAll('#langMenu .lang-btn')].map(b=>b.dataset.lang).join(''),sug:(()=>{document.getElementById('searchInput').focus();return document.querySelectorAll('#searchSuggest button').length;})()})")
        check("74 desktop keeps the six-button language control in its usual order, and the suggestions", dk['menuHidden'] and dk['six']==6 and dk['order']=='enfreszhkoja' and dk['sug']==4, dk)
        await pg74d.close()
        check("74 no page errors across round 74", len(e74)==0, e74[:3])
        await pg74.close()

        print("\n--- visual + interaction audit fixes (round 75) ---")
        pg75=await b.new_page(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True)
        e75=[]; pg75.on('pageerror', lambda e: e75.append(str(e)))
        await pg75.goto(URL+'?lang=zh'); await pg75.wait_for_timeout(1400)
        hd=await pg75.evaluate("()=>{const r=s=>document.querySelector(s).getBoundingClientRect();return {btnB:Math.round(r('#langMenuBtn').bottom),h1T:Math.round(r('h1').top),linksT:Math.round(r('.header-links').top),btnT:Math.round(r('#langMenuBtn').top)};}")
        check("75 phone header: the language button sits beside the links and above the title, nothing overlaps", hd['btnB']<=hd['h1T'] and abs(hd['btnT']-hd['linksT'])<=2, hd)
        before=await pg75.evaluate("()=>Math.round(document.querySelector('.ftoolbar').getBoundingClientRect().top)")
        await pg75.focus('#searchInput'); await pg75.wait_for_timeout(250)
        ov=await pg75.evaluate("()=>{const b=document.getElementById('searchSuggest');const sb=document.querySelector('.search-bar').getBoundingClientRect();const r=b.getBoundingClientRect();return {pos:getComputedStyle(b).position,top:Math.round(r.top-sb.bottom),tb:Math.round(document.querySelector('.ftoolbar').getBoundingClientRect().top),z:parseInt(getComputedStyle(b).zIndex,10)};}")
        check("75 the suggestions float under the search bar without pushing the page down", ov['pos']=='absolute' and 0<=ov['top']<=12 and ov['tb']==before and ov['z']>1000, (before,ov))
        await pg75.keyboard.press('Tab'); await pg75.wait_for_timeout(250)
        tb=await pg75.evaluate("()=>({inSugg:!!document.activeElement.closest('#searchSuggest'),hidden:document.getElementById('searchSuggest').hidden})")
        check("75 Tab reaches the suggestions and they stay open", tb['inSugg'] and not tb['hidden'], tb)
        await pg75.keyboard.press('Escape'); await pg75.wait_for_timeout(200)
        # a search bar that does not jump when ✕ appears
        h0=await pg75.evaluate("()=>document.querySelector('.search-bar').getBoundingClientRect().height")
        await pg75.fill('#searchInput','bank'); await pg75.wait_for_timeout(400)
        h1=await pg75.evaluate("()=>document.querySelector('.search-bar').getBoundingClientRect().height")
        check("75 the search bar keeps its height when the clear button appears", abs(h1-h0)<=1, (h0,h1))
        await pg75.click('#searchClear'); await pg75.wait_for_timeout(300)
        # deep link → list → another card → ✕ stays on the page; the open card rides in the URL
        await pg75.goto(URL+'?lang=fr'); await pg75.wait_for_timeout(600)
        await pg75.goto(URL+'?task=msp'); await pg75.wait_for_timeout(1400)
        await pg75.evaluate("()=>document.getElementById('taskBack').click()"); await pg75.wait_for_timeout(250)
        await pg75.evaluate("()=>document.querySelector('.task-card[data-task=sin]').click()"); await pg75.wait_for_timeout(250)
        u1=await pg75.evaluate("()=>location.search")
        await pg75.evaluate("()=>closeModal(guideBackdropEl)"); await pg75.wait_for_timeout(500)
        st=await pg75.evaluate("()=>({here:location.pathname.indexOf('kamloops')>=0||location.pathname.indexOf('test_copy')>=0,open:guideBackdropEl.classList.contains('open'),url:location.search})")
        check("75 from a linked card: list → another card → ✕ closes the guide and stays on the page; the URL follows the open card", 'task=sin' in u1 and st['here'] and not st['open'] and 'task=' not in st['url'], (u1,st))
        # a door-opened card after a normal close still has its own Back level
        await pg75.goto(URL); await pg75.wait_for_timeout(1200)
        await pg75.evaluate("()=>{openGuide('header');openTask('msp','list');closeModal(guideBackdropEl);}"); await pg75.wait_for_timeout(300)
        await pg75.evaluate("()=>openGuide('progress','sin')"); await pg75.wait_for_timeout(300)
        d1=await pg75.evaluate("()=>history.state&&history.state.kSheet")
        await pg75.go_back(); await pg75.wait_for_timeout(400)
        d2=await pg75.evaluate("()=>({open:guideBackdropEl.classList.contains('open'),task:_taskOpen})")
        check("75 a card opened through a door after an earlier close: Back returns to the list", d1=='guideTask' and d2['open'] and d2['task'] is None, (d1,d2))
        await pg75.evaluate("()=>closeModal(guideBackdropEl)"); await pg75.wait_for_timeout(300)
        # a route chosen on a place card keeps the card open
        await pg75.evaluate("()=>{resetAll();focusMarker(M[2],17);}"); await pg75.wait_for_timeout(800)
        await pg75.evaluate("()=>{const rb=document.querySelector('.leaflet-popup .pv-route');if(rb)rb.click();}"); await pg75.wait_for_timeout(600)
        rp=await pg75.evaluate("()=>({route:selectedRoute,popup:!!document.querySelector('.leaflet-popup')})")
        check("75 choosing a route from a place card draws it and keeps the card open", rp['route'] and rp['popup'], rp)
        # the near filter alone shows Reset
        await pg75.evaluate("()=>{resetAll();userPos=[50.6745,-120.3273];updateNearQuickpick();applyQuickPickOrder();document.getElementById('qpNear').click();}"); await pg75.wait_for_timeout(300)
        check("75 the 15-min-walk filter alone shows Reset", await pg75.evaluate("()=>!document.getElementById('resetBtn').hidden&&nearOnly"))
        await pg75.evaluate("()=>{resetAll();userPos=null;}")
        # accessible names carry words, not pictograms
        an=await pg75.evaluate("()=>[document.getElementById('shareBtn').getAttribute('aria-label'),document.getElementById('guideToggle').getAttribute('aria-label'),document.getElementById('qpMore').title]")
        check("75 icon-only controls are named with words, not emoji", all(a and not any(ord(ch)>0x2500 and ord(ch)!=0x2026 for ch in a[:2]) for a in an), an)
        check("75 no page errors across round 75 (phone)", len(e75)==0, e75[:3])
        await pg75.close()
        # 320px flyer card, tablet header, desktop suggestion click
        pg75s=await b.new_page(viewport={'width':320,'height':568}, has_touch=True, is_mobile=True)
        await pg75s.goto(URL+'?lang=fr&src=flyer-f-2609'); await pg75s.wait_for_timeout(1300)
        fb=await pg75s.evaluate("()=>{const c=document.getElementById('firstUse').getBoundingClientRect();return [...document.querySelectorAll('#firstUse [data-go]')].map(b=>{const r=b.getBoundingClientRect();return Math.round(c.right-r.right);});}")
        check("75 320px flyer card: every button stays inside the card", len(fb)==3 and all(x>=0 for x in fb), fb)
        await pg75s.close()
        pg75t=await b.new_page(viewport={'width':820,'height':1180}, has_touch=True, is_mobile=True)
        await pg75t.goto(URL+'?lang=es'); await pg75t.wait_for_timeout(1300)
        th=await pg75t.evaluate("()=>{const r=s=>document.querySelector(s).getBoundingClientRect();const ls=r('.lang-sw'),hl=r('.header-links'),sub=r('.sub');const pr=parseFloat(getComputedStyle(document.querySelector('.sub')).paddingRight)||0;return {gap:Math.round(hl.top-ls.bottom),subClear:Math.round(hl.left-(sub.right-pr))};}")
        check("75 tablet header: language strip, links and tagline do not overlap", th['gap']>=0 and th['subClear']>=0, th)
        await pg75t.close()
        pg75d=await b.new_page(viewport={'width':1280,'height':900})
        await pg75d.goto(URL); await pg75d.wait_for_timeout(1200)
        await pg75d.focus('#searchInput'); await pg75d.wait_for_timeout(250)
        await pg75d.click('#searchSuggest button:nth-of-type(4)'); await pg75d.wait_for_timeout(600)
        dk=await pg75d.evaluate("()=>({panel:document.getElementById('panel').classList.contains('open'),mode:panelMode,q:_busQ})")
        check("75 desktop: the 'which bus goes to TRU' suggestion opens the bus panel and it stays open", dk['panel'] and dk['mode']=='bus' and dk['q']=='TRU', dk)
        rt=await pg75d.evaluate("()=>{const r=document.querySelector('.pv-route')||(function(){const d=document.createElement('div');d.innerHTML=popup(M.find(x=>/Royal Inland/.test(x.data.n)).data,0);document.body.appendChild(d);return d.querySelector('.pv-route');})();const cs=getComputedStyle(r);return {color:cs.color,bw:cs.borderTopWidth};}")
        check("75 route numbers on a card are ink on white with a coloured ring", rt['color']=='rgb(28, 28, 30)' and rt['bw']=='2px', rt)
        await pg75d.close()

        print("\n--- first-time-user bug sweep (round 76) ---")
        e76=[]
        pg76=await b.new_page(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True, device_scale_factor=2)
        pg76.on('pageerror', lambda e: e76.append(str(e)))
        await pg76.goto(URL+'?lang=zh'); await pg76.wait_for_timeout(1300)
        await pg76.evaluate("()=>{localStorage.clear();_arriveMem=null;}")
        # P-01: the landing strip wraps instead of squeezing the count to one glyph per line
        await pg76.evaluate("()=>setArrival('2026-06-25')")
        gp=await pg76.evaluate("()=>{const el=document.getElementById('guideProgress');const r=el.getBoundingClientRect();const d=el.querySelector('.gp-dl').getBoundingClientRect();return {sw:el.scrollWidth,cw:el.clientWidth,dlIn:d.right<=r.right+1,cnt:el.children[1].getBoundingClientRect().height};}")
        check("76 progress strip: count on one line, deadline inside the strip", gp['sw']<=gp['cw']+1 and gp['dlIn'] and gp['cnt']<40, gp)
        # P-10: a step tick shows the strip at once
        await pg76.evaluate("()=>{localStorage.clear();_arriveMem=null;updateGuideProgress();}")
        h0=await pg76.evaluate("()=>document.getElementById('guideProgress').hidden")
        await pg76.evaluate("()=>setStep('msp',0,true)")
        h1=await pg76.evaluate("()=>document.getElementById('guideProgress').hidden")
        check("76 ticking a step shows the progress strip without a reload", h0 and not h1, (h0,h1))
        await pg76.evaluate("()=>{setStep('msp',0,false);localStorage.clear();updateGuideProgress();}")
        # P-05: the place count is readable on a 390px phone
        st=await pg76.evaluate("()=>document.getElementById('statusText').getBoundingClientRect().width")
        check("76 390px phone: the place count has room (not '2…')", st>=100, st)
        # T-04/P-06/P-07: notes clear of the 48px locate button
        ov=await pg76.evaluate("()=>{placeMapNotes();const g=document.querySelector('.geo-btn').getBoundingClientRect();const o=document.getElementById('offlineNote');const was=o.hidden,wc=o.classList.contains('compact');o.hidden=false;o.classList.remove('compact');const n=o.getBoundingClientRect();const gn=document.getElementById('geoNote');const wg=gn.hidden;gn.hidden=false;const gr=gn.getBoundingClientRect();o.hidden=was;if(wc)o.classList.add('compact');gn.hidden=wg;const f=(a,b)=>Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left))*Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));return [f(g,n),f(g,gr)];}")
        check("76 offline note and location explainer do not sit under the locate button", ov==[0,0], ov)
        # P-08: a double tap on the guide button does not open-and-close
        bb=await pg76.evaluate("()=>{const r=document.getElementById('guideToggle').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2];}")
        await pg76.touchscreen.tap(bb[0],bb[1]); await pg76.wait_for_timeout(120); await pg76.touchscreen.tap(bb[0],bb[1]); await pg76.wait_for_timeout(500)
        check("76 double tap on the guide button leaves the guide open", await pg76.evaluate("()=>guideBackdropEl.classList.contains('open')"))
        await pg76.wait_for_timeout(450)
        await pg76.touchscreen.tap(bb[0],bb[1]); await pg76.wait_for_timeout(300)
        check("76 a backdrop tap after the sheet settled still closes it", not await pg76.evaluate("()=>guideBackdropEl.classList.contains('open')"))
        # P-04: closing with a card open, reopening shows the list
        await pg76.evaluate("()=>{openGuide('header');openTask('msp','list');closeModal(guideBackdropEl);}"); await pg76.wait_for_timeout(300)
        await pg76.evaluate("()=>openGuide('header')"); await pg76.wait_for_timeout(300)
        rl=await pg76.evaluate("()=>({back:!!document.getElementById('taskBack'),cards:document.querySelectorAll('.task-card').length})")
        check("76 reopening the guide after closing it on a card shows the list", not rl['back'] and rl['cards']>5, rl)
        # P-09: swipe down on the sheet header dismisses it
        hb=await pg76.evaluate("()=>{const r=document.querySelector('#guideModal .guide-head').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2];}")
        cdp=await pg76.context.new_cdp_session(pg76)
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':hb[0],'y':hb[1]}]})
        for i in range(1,11):
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':hb[0],'y':hb[1]+i*40}]}); await pg76.wait_for_timeout(16)
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg76.wait_for_timeout(500)
        check("76 swiping down on the sheet header dismisses the guide", not await pg76.evaluate("()=>guideBackdropEl.classList.contains('open')"))
        await cdp.detach()
        # P-03: link-opened guide — back to list, another card, Back returns to the list, never off the page
        await pg76.goto(URL+'?lang=zh&task=msp'); await pg76.wait_for_timeout(1300)
        await pg76.click('#taskBack'); await pg76.wait_for_timeout(300)
        await pg76.click('.task-card[data-task="sin"]'); await pg76.wait_for_timeout(300)
        await pg76.go_back(); await pg76.wait_for_timeout(500)
        lb=await pg76.evaluate("()=>({here:/kamloops/.test(location.href),open:guideBackdropEl.classList.contains('open'),back:!!document.getElementById('taskBack'),cards:document.querySelectorAll('.task-card').length})")
        check("76 deep link → list → card → Back returns to the list", lb['here'] and lb['open'] and not lb['back'] and lb['cards']>5, lb)
        await pg76.go_back(); await pg76.wait_for_timeout(500)
        lb2=await pg76.evaluate("()=>({here:/kamloops/.test(location.href),open:guideBackdropEl.classList.contains('open')})")
        check("76 … and the next Back closes the guide, still on the page", lb2['here'] and not lb2['open'], lb2)
        # P-02 + P-12: a route chosen on a card leaves the card readable; the popup ✕ is a real target
        await pg76.goto(URL+'?lang=en'); await pg76.wait_for_timeout(1300)
        await pg76.evaluate("()=>{const m=M.find(m=>/Service BC/i.test(m.data.n));focusMarker(m,17);}"); await pg76.wait_for_timeout(1500)
        await pg76.evaluate("()=>{const rb=document.querySelector('.leaflet-popup .pv-route');if(rb)rb.click();}"); await pg76.wait_for_timeout(1200)
        rp=await pg76.evaluate("()=>{const p=document.querySelector('.leaflet-popup-content');const c=document.querySelector('.leaflet-popup-close-button');if(!p||!c)return null;const cr=c.getBoundingClientRect();const el=document.elementFromPoint(cr.left+cr.width/2,cr.top+cr.height/2);return {top:p.getBoundingClientRect().top,bar:document.getElementById('busIndicator').getBoundingClientRect().bottom,hit:!!(el&&el.closest('.leaflet-popup-close-button')),cw:cr.width,ch:cr.height,route:selectedRoute};}")
        check("76 route from a card: the card clears the route bar and its ✕ can be tapped", rp and rp['route'] and rp['top']>=rp['bar']-1 and rp['hit'], rp)
        check("76 popup ✕ is at least 40px on a phone", rp and rp['cw']>=40 and rp['ch']>=40, rp)
        # P-11: turning the phone sideways keeps the open card inside the map
        await pg76.set_viewport_size({'width':844,'height':390}); await pg76.wait_for_timeout(900)
        rot=await pg76.evaluate("()=>{const p=document.querySelector('.leaflet-popup');if(!p)return null;return {pt:p.getBoundingClientRect().top,mt:document.getElementById('map').getBoundingClientRect().top,open:!!map._popup&&map._popup.isOpen()};}")
        check("76 rotating with a card open keeps its header inside the map", rot and rot['open'] and rot['pt']>=rot['mt']-1, rot)
        await pg76.set_viewport_size({'width':390,'height':844}); await pg76.wait_for_timeout(400)
        await pg76.evaluate("()=>{selectRoute(null);map.closePopup();}")
        check("76 no page errors across round 76 (phone)", len(e76)==0, e76[:3])
        await pg76.close()
        # desktop + logic
        pg76d=await b.new_page(viewport={'width':1280,'height':900})
        e76d=[]; pg76d.on('pageerror', lambda e: e76d.append(str(e)))
        await pg76d.goto(URL+'?lang=en'); await pg76d.wait_for_timeout(1300)
        await pg76d.evaluate("()=>{localStorage.clear();_arriveMem=null;}")
        await pg76d.click('#guideToggle'); await pg76d.wait_for_timeout(300)
        await pg76d.focus('#arriveDate')
        for ch in '09012026': await pg76d.keyboard.type(ch)
        await pg76d.click('.task-lead'); await pg76d.wait_for_timeout(300)
        check("76 typing an arrival date digit by digit stores it and throws nothing", await pg76d.evaluate("()=>localStorage.getItem('kamloopsArrived')")=='2026-09-01' and len(e76d)==0, e76d[:2])
        await pg76d.evaluate("()=>{localStorage.setItem('kamloopsArrived','0202-09-01');_arriveMem=null;closeModal(guideBackdropEl);}"); await pg76d.wait_for_timeout(300)
        await pg76d.click('#guideToggle'); await pg76d.wait_for_timeout(300)
        check("76 a stored half-typed year is ignored, not thrown on", await pg76d.evaluate("()=>arrivalDate()") is None and len(e76d)==0, e76d[:2])
        await pg76d.evaluate("()=>{localStorage.clear();_arriveMem=null;renderTaskList();}")
        await pg76d.focus('#arriveDate')
        for ch in '06012030': await pg76d.keyboard.type(ch)
        await pg76d.click('.task-lead'); await pg76d.wait_for_timeout(300)
        fd=await pg76d.evaluate("()=>[localStorage.getItem('kamloopsArrived'),document.getElementById('arriveDate').value,arrivalDate()]")
        check("76 a future arrival date is not accepted and the field shows what is stored", fd==[None,'',None], fd)
        await pg76d.keyboard.press('Escape'); await pg76d.wait_for_timeout(200)
        check("76 fmtDist is monotonic around 1 km", await pg76d.evaluate("()=>[fmtDist(949),fmtDist(950),fmtDist(951),fmtDist(1450)]")==['950 m','1.0 km','1.0 km','1.5 km'])
        check("76 debug panel stacks under the sheets", await pg76d.evaluate("()=>{buildDebugPanel();return +getComputedStyle(document.getElementById('debugPanel')).zIndex;}")<1200)
        # T-02: switching sections opens the new one at its top
        await pg76d.click('#catBtn'); await pg76d.wait_for_timeout(300)
        await pg76d.evaluate("()=>document.querySelector('.panel-body').scrollTop=600")
        await pg76d.click('#panelClose'); await pg76d.wait_for_timeout(200)
        await pg76d.click('#busBtn'); await pg76d.wait_for_timeout(300)
        check("76 opening Bus Routes after scrolling Category starts at the top (search box visible)", await pg76d.evaluate("()=>document.querySelector('.panel-body').scrollTop")==0)
        await pg76d.keyboard.press('Escape'); await pg76d.wait_for_timeout(200)
        await pg76d.evaluate("()=>{favMsg('x');setLang('ja');}"); await pg76d.wait_for_timeout(200)
        check("76 favourites import message does not outlive a language switch", await pg76d.evaluate("()=>document.getElementById('favIOMsg').textContent")=='')
        await pg76d.evaluate("()=>setLang('en')")
        check("76 no page errors across round 76 (desktop)", len(e76d)==0, e76d[:3])
        await pg76d.close()
        # tablets
        pg76t=await b.new_page(viewport={'width':1024,'height':600}, has_touch=True, device_scale_factor=2)
        await pg76t.goto(URL+'?lang=fr'); await pg76t.wait_for_timeout(1300)
        await pg76t.click('#catBtn'); await pg76t.wait_for_timeout(400)
        pb=await pg76t.evaluate("()=>({ab:document.getElementById('applyBtn').getBoundingClientRect().bottom,pb:document.getElementById('panel').getBoundingClientRect().bottom,vh:innerHeight})")
        check("76 1024x600 tablet: the filter panel and its Done button fit on screen", pb['ab']<=pb['vh'] and pb['pb']<=pb['vh'], pb)
        await pg76t.close()
        pg76t2=await b.new_page(viewport={'width':820,'height':1180}, has_touch=True, device_scale_factor=2)
        await pg76t2.goto(URL+'?lang=en&src=flyer-en'); await pg76t2.wait_for_timeout(1300)
        fl=await pg76t2.evaluate("()=>{const h=document.querySelector('#firstUse .fu-h');const x=document.getElementById('fuClose').getBoundingClientRect();const bs=[...document.querySelectorAll('#firstUse .fu-row button')].map(b=>b.getBoundingClientRect());const f=(a,b)=>Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left))*Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));return {hh:h.getBoundingClientRect().height,txt:h.textContent.trim().length,ov:bs.map(b=>f(x,b))};}")
        check("76 tablet flyer card: heading shows and the ✕ target is clear of the buttons", fl['hh']>10 and fl['txt']>5 and all(o==0 for o in fl['ov']), fl)
        await pg76t2.evaluate("()=>selectRoute('1')"); await pg76t2.wait_for_timeout(700)
        zb=await pg76t2.evaluate("()=>({zr:document.querySelector('.leaflet-control-zoom').getBoundingClientRect().right,bl:document.getElementById('busIndicator').getBoundingClientRect().left})")
        check("76 820px: the route bar clears the zoom control", zb['bl']>=zb['zr'], zb)
        await pg76t2.evaluate("()=>selectRoute(null)")
        await pg76t2.close()
        pg76t3=await b.new_page(viewport={'width':1024,'height':768}, has_touch=True, device_scale_factor=2)
        await pg76t3.goto(URL+'?lang=zh'); await pg76t3.wait_for_timeout(1300)
        await pg76t3.click('#guideToggle'); await pg76t3.wait_for_timeout(300)
        await pg76t3.click('.task-card[data-task="msp"]'); await pg76t3.wait_for_timeout(300)
        await pg76t3.click('.task-map'); await pg76t3.wait_for_timeout(2500)
        om=await pg76t3.evaluate("()=>{const p=document.querySelector('.leaflet-popup');if(!p)return null;const r=p.getBoundingClientRect();return {b:r.bottom,t:r.top,vh:innerHeight};}")
        check("76 1024x768: 'open it on the map' shows the whole card, action row included", om and om['b']<=om['vh'] and om['t']>=0, om)
        await pg76t3.close()
        pg76t4=await b.new_page(viewport={'width':1180,'height':820}, has_touch=True, device_scale_factor=2)
        await pg76t4.goto(URL+'?lang=fr'); await pg76t4.wait_for_timeout(2500)
        lc=await pg76t4.evaluate("()=>{const ls=[...document.querySelectorAll('.leaflet-tooltip')].filter(e=>e.style.display!=='none'&&e.offsetWidth);const cl=[...document.querySelectorAll('.marker-cluster')];const bad=[];ls.forEach(l=>{const a=l.getBoundingClientRect();cl.forEach(c=>{const b=c.getBoundingClientRect();const w=Math.min(a.right,b.right)-Math.max(a.left,b.left),h=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);if(w>0&&h>0&&(w*h)/(b.width*b.height)>0.35)bad.push(l.textContent+'/'+c.textContent.trim());});});return {n:ls.length,bad};}")
        check("76 no landmark label hides a cluster count", lc['n']>0 and len(lc['bad'])==0, lc)
        await pg76t4.close()
        pg76k=await b.new_page(viewport={'width':640,'height':900}, has_touch=True)
        await pg76k.goto(URL+'?lang=ko'); await pg76k.wait_for_timeout(1000)
        kl=await pg76k.evaluate("()=>{const h=document.querySelector('h1');const t=h.firstChild;const rg=document.createRange();const txt=h.textContent;const lines=[];let last=null,start=0;for(let i=0;i<txt.length;i++){rg.setStart(t,i);rg.setEnd(t,i+1);const y=rg.getBoundingClientRect().top;if(last!==null&&y>last+2){lines.push(txt.slice(start,i));start=i;}last=y;}lines.push(txt.slice(start));return lines;}")
        check("76 640px Korean title never breaks inside a word", all(not l.startswith(('드','ド')) for l in kl), kl)
        await pg76k.close()

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
