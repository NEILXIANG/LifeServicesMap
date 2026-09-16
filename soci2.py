import asyncio, os, sys
from playwright.async_api import async_playwright
URL='file://'+os.path.abspath('kamloops.html')
OK=[];BAD=[]
def chk(n,c,d=None):
    (OK if c else BAD).append(n); print("  %s %s%s"%('PASS' if c else 'FAIL',n,('  — %r'%(d,)) if d is not None else ''))
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(); pg=await b.new_page(viewport={'width':1280,'height':950})
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1400)

        # 1. the two new cards exist, in the right buckets, in all six languages
        cards=await pg.evaluate("""()=>{const o={};
          ['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);renderTaskList();
            const c=[...document.querySelectorAll('.task-card')];
            o[l]=c.filter(e=>['connect','hardship'].indexOf(e.dataset.task)>=0)
                  .map(e=>({id:e.dataset.task,txt:e.textContent.trim()}));});
          setLang('en');renderTaskList();
          return {perLang:o,n:TASKS.length,
                  buckets:TASKS.filter(t=>['connect','hardship'].indexOf(t.id)>=0)
                              .map(t=>t.id+':'+t.when)};}""")
        allsix=all(len(v)==2 and all(x['txt'] for x in v) for v in cards['perLang'].values())
        uniq={}
        for l,v in cards['perLang'].items():
            for x in v: uniq.setdefault(x['id'],set()).add(x['txt'])
        chk("connect + hardship render in all six languages with distinct copy",
            allsix and cards['n']==14 and all(len(s)==6 for s in uniq.values()),  # 14 tasks since 'legal' was added after this script was written
            {'buckets':cards['buckets'],'n':cards['n'],
             'distinct':{k:len(v) for k,v in uniq.items()}})
        chk("they sit in the buckets a reader would look in",
            cards['buckets']==['connect:ongoing','hardship:problem'], cards['buckets'])

        # 2. each opens with the full detail contract
        for tid,want in [('connect',{'place':True,'steps':3}),('hardship',{'place':True,'steps':3})]:
            det=await pg.evaluate("""(tid)=>{renderTaskList();
                document.querySelector('.task-card[data-task='+tid+']').click();
                const h=document.getElementById('guideTasks');
                return {title:(h.querySelector('h4')||{}).textContent,
                        steps:h.querySelectorAll('.task-steps li').length,
                        place:(h.querySelector('.task-place b')||{}).textContent||null,
                        tel:!!h.querySelector('.task-place a[href^=tel]'),
                        map:!!h.querySelector('.task-map'),
                        src:(h.querySelector('.task-src a')||{}).textContent||null,
                        href:(h.querySelector('.task-src a')||{}).href||null,
                        back:!!document.getElementById('taskBack')};}""", tid)
            chk("%s opens with steps, a real office and a citable source"%tid,
                det['steps']>=want['steps'] and det['place'] and det['map']
                and det['src'] and (det['href'] or '').startswith('http') and det['back'], det)

        # 3. hardship carries the "this will not be reported" reassurance in every language
        cf=await pg.evaluate("""()=>{const o={};
          ['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);renderTaskList();
            document.querySelector('.task-card[data-task=hardship]').click();
            const row=[...document.querySelectorAll('#guideTasks .task-row')]
              .find(r=>r.querySelector('.task-lb').textContent===UI[l].taskConfid);
            o[l]=row?row.querySelector('.task-bd').textContent.trim():null;});
          setLang('en');renderTaskList();return o;}""")
        chk("hardship reassures, in every language, that asking is safe",
            all(cf.values()) and len(set(cf.values()))==6, {k:(v or '')[:40] for k,v in cf.items()})

        # 4. "where do I go" hands both cards off to a marker that really exists
        for tid,want in [('connect','Volunteer'),('hardship','Food Bank')]:
            await pg.evaluate("()=>{resetAll();if(!document.getElementById('guideBackdrop').classList.contains('open'))document.getElementById('guideToggle').click();}")
            await pg.wait_for_timeout(350)
            ev=await pg.evaluate("""(tid)=>{renderTaskList();
                document.querySelector('.task-card[data-task='+tid+']').click();
                const n0=_evBuf.length;document.querySelector('.task-map').click();
                return {closed:!document.getElementById('guideBackdrop').classList.contains('open'),
                        ev:_evBuf.slice(n0).map(e=>e.t)};}""", tid)
            await pg.wait_for_timeout(1300)
            pop=await pg.evaluate("()=>{const t=document.querySelector('.leaflet-popup .pt');return t?t.textContent:null;}")
            chk("%s's office opens on the map"%tid,
                ev['closed'] and pop and want in pop, {'popup':pop,'ev':ev['ev']})

        # 5. the support category is a real, six-language, filterable category
        await pg.evaluate("()=>{resetAll();setLang('en');}")
        sup=await pg.evaluate("""()=>{
          const labels={};['zh','en','fr','es','ko','ja'].forEach(l=>{setLang(l);labels[l]=CI.support[l];});
          setLang('en');
          aC=new Set(['support']);renderCats();apply();
          const shown=M.filter(m=>markerHome().hasLayer(m)).map(m=>m.data.n);
          const chips=[...document.querySelectorAll('.af-chip')].map(e=>e.textContent);
          resetAll();
          return {labels,shown,icon:IC.support,colour:CD.support,
                  inGroup:GRP.some(g=>g.cats.indexOf('support')>=0),
                  chipShown:chips.some(c=>c.indexOf(CI.support.en)>=0)};}""")
        chk("the support category is labelled in six languages and filters to real places",
            len(set(sup['labels'].values()))==6 and len(sup['shown'])>=1
            and sup['inGroup'] and sup['icon'] and sup['colour'], sup)

        # 5b. and it behaves like every other category through the real UI:
        #     (it was first filed under Faith & Community — the provider's label,
        #      not the reader's; a person out of food does not look under 🙏)
        #     tap it, it filters and shows a chip; clear the chip, it un-filters
        # reach it the way a reader does: open the panel, expand the group it
        # was filed under, then tap the button by the label they can read
        await pg.evaluate("()=>{resetAll();setLang('en');}")
        await pg.click('#catBtn'); await pg.wait_for_timeout(500)
        await pg.evaluate("""()=>{const g=GRP.find(g=>g.cats.indexOf('support')>=0);
            expandedGroups.add(g.k);renderCats();}""")
        await pg.wait_for_timeout(400)
        ui=await pg.evaluate("""()=>{
          const grp=GRP.find(g=>g.cats.indexOf('support')>=0);
          const btn=[...document.querySelectorAll('.cat-btn')]
            .find(b=>b.textContent.indexOf(CI.support.en)>=0);
          if(!btn)return {no:'no button',group:grp.k};
          // measure before the click: renderCats() rebuilds the grid, so after
          // the click this node is detached and every box is zero
          const size=btn.getBoundingClientRect().height, label=btn.textContent.trim();
          btn.click();
          const chip=[...document.querySelectorAll('.af-chip .x')]
            .find(x=>x.dataset.kind==='cat');
          const on=M.filter(m=>markerHome().hasLayer(m)).length;
          if(chip)chip.click();
          const off=M.filter(m=>markerHome().hasLayer(m)).length;
          const r={label:label,group:grp.k,filtered:on,chip:!!chip,cleared:off,size:size};
          resetAll();closeModal(document.getElementById('backdrop'));return r;}""")
        # (tap-target size is a touch-viewport property — regress.py checks it
        #  under pointer:coarse; here the question is only that it behaves)
        chk("support filters and clears like any other category, filed where a reader would look",
            ui.get('chip') and ui['filtered']>=1 and ui['cleared']>ui['filtered']
            and ui['group']=='services', ui)

        # 6. the new places are searchable by the words a reader would actually type
        srch=await pg.evaluate("""()=>{const o={};
          const probe=(lang,q,want)=>{setLang(lang);
            searchInputEl.value=q;searchRaw=q;searchTerm=q.toLowerCase();apply();
            const hits=M.filter(m=>m.score>0).sort((a,b)=>b.score-a.score).map(m=>m.data.n);
            o[lang+':'+q]={top:hits[0]||null,found:hits.some(h=>h.indexOf(want)>=0)};};
          probe('en','volunteer','Volunteer');
          probe('zh','志愿','Volunteer');
          probe('en','mustard','Mustard');
          probe('zh','无家可归','Mustard');
          probe('ko','자원봉사','Volunteer');
          resetAll();setLang('en');return o;}""")
        for k,v in srch.items(): print("      %-18s -> %s"%(k,v['top']))
        chk("the new places are findable in the reader's own words",
            all(v['found'] for v in srch.values()), {k:v['found'] for k,v in srch.items()})

        # 7. done-state still works for the new cards and survives a reload
        done=await pg.evaluate("""()=>{if(!document.getElementById('guideBackdrop').classList.contains('open'))
                document.getElementById('guideToggle').click();
            renderTaskList();
            document.querySelector('.task-card[data-task=connect]').click();
            const tick=document.getElementById('taskTick');
            if(!tick)return {no:'no tick'};
            tick.click();
            renderTaskList();
            return {stored:localStorage.getItem('kamloopsTasksDone'),
                    marked:document.querySelector('.task-card[data-task=connect]').classList.contains('is-done'),
                    progress:!!document.querySelector('.task-progress')};}""")
        await pg.reload(); await pg.wait_for_timeout(1400)
        after=await pg.evaluate("""()=>{document.getElementById('guideToggle').click();
            return document.querySelector('.task-card[data-task=connect]').classList.contains('is-done');}""")
        chk("marking a new card done persists across a reload",
            done.get('marked') and after, {'before':done,'after':after})

        chk("no page errors anywhere in this pass", not errs, errs[:3])
        await b.close()
    print("\n  %d pass, %d fail"%(len(OK),len(BAD)))
    if BAD: print("  FAILED: "+", ".join(BAD)); sys.exit(1)
asyncio.run(main())
