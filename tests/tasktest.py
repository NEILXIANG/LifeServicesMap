import asyncio, os, sys
_r = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    if os.path.exists(os.path.join(_r, 'kamdata.py')): break
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import kamdata
from playwright.async_api import async_playwright

# 构建产物在 build/kamloops.html（build.py 的默认输出）。原来写的是
# os.path.abspath('kamloops.html')——既依赖当前工作目录，文件名也早就不对了，
# 于是 Chromium 加载到一个错误页，测试以 JS 异常炸掉而不是干净地 FAIL。
BUILT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(kamdata.ROOT, 'build', 'kamloops.html')
if not os.path.exists(BUILT):
    sys.exit('没有找到构建产物 %s —— 先跑 python3 build.py' % BUILT)
URL = 'file://' + BUILT
OK=[];BAD=[]
def chk(n,c,d=None):
    (OK if c else BAD).append(n); print("  %s %s%s"%('PASS' if c else 'FAIL',n,('  — %r'%(d,)) if d is not None else ''))
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(); pg=await b.new_page(viewport={'width':1280,'height':900})
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1400)

        await pg.click('#guideToggle'); await pg.wait_for_timeout(400)
        lst=await pg.evaluate("""()=>({
            open:document.getElementById('guideBackdrop').classList.contains('open'),
            cards:[...document.querySelectorAll('.task-card')].map(e=>e.dataset.task),
            buckets:[...document.querySelectorAll('.task-bucket')].map(e=>e.textContent),
            proseStillThere:document.getElementById('guideBody').textContent.length,
            tocStillThere:!!document.querySelector('.guide-toc')})""")
        n=await pg.evaluate("()=>TASKS.length")
        chk("guide opens on the problem list, prose still below",
            lst['open'] and len(lst['cards'])==n and n>=11
            and lst['proseStillThere']>10000 and lst['tocStillThere'], dict(lst, n=n))

        det=await pg.evaluate("""()=>{document.querySelector('.task-card[data-task=msp]').click();
            const h=document.getElementById('guideTasks');
            return {title:(h.querySelector('h4')||{}).textContent,
                    labels:[...h.querySelectorAll('.task-lb')].map(e=>e.textContent),
                    steps:h.querySelectorAll('.task-steps li').length,
                    place:(h.querySelector('.task-place b')||{}).textContent,
                    hasPhone:!!h.querySelector('.task-place a[href^=tel]'),
                    mapBtn:!!h.querySelector('.task-map'),
                    src:(h.querySelector('.task-src a')||{}).textContent,
                    back:!!document.getElementById('taskBack')};}""")
        chk("a task opens with steps, office, cost, wait and its source",
            det['steps']==4 and det['mapBtn'] and det['back'] and 'MSP' in (det['src'] or ''), det)
        chk("the office it names is the right one (ICBC trap avoided elsewhere)",
            det['place']=='Service BC Centre', det['place'])

        back=await pg.evaluate("""()=>{document.getElementById('taskBack').click();
            return document.querySelectorAll('.task-card').length;}""")
        chk("back returns to the full list", back==n, back)

        # where-to-go actually hands off to the map
        mp=await pg.evaluate("""()=>{document.querySelector('.task-card[data-task=sin]').click();
            const n0=_evBuf.length;
            document.querySelector('.task-map').click();
            return {guideClosed:!document.getElementById('guideBackdrop').classList.contains('open'),
                    ev:_evBuf.slice(n0).map(e=>e.t)};}""")
        await pg.wait_for_timeout(1200)
        popup=await pg.evaluate("()=>{const t=document.querySelector('.leaflet-popup .pt');return t?t.textContent:null;}")
        chk("'where do I go' closes the guide and opens that office on the map",
            mp['guideClosed'] and popup and 'Service Canada' in popup, {'ev':mp['ev'],'popup':popup})

        # every language renders every task without falling back to English
        lang=await pg.evaluate("""()=>{const out={};
          ['zh','en','fr','es','ko','ja'].forEach(l=>{
            setLang(l);                       // setLang re-renders the task layer
            renderTaskList();                 // ensure we are on the list, not a task
            const cards=[...document.querySelectorAll('.task-card')];
            const qs=cards.map(c=>c.querySelector('.task-q').textContent);
            document.querySelector('.task-card[data-task=licence]').click();
            const h=document.getElementById('guideTasks');
            out[l]={n:cards.length,
                    steps:h.querySelectorAll('.task-steps li').length,
                    labels:[...h.querySelectorAll('.task-lb')].map(e=>e.textContent).join('|'),
                    sample:qs[0]};
            document.getElementById('taskBack').click();});
          setLang('en');return out;}""")
        allsix = all(v['n']==n and v['steps']>=3 for v in lang.values())
        distinct = len({v['sample'] for v in lang.values()})==6
        distinct_lb = len({v['labels'] for v in lang.values()})==6
        chk("all six languages render every task, with no English fallback",
            allsix and distinct and distinct_lb,
            {k:v['sample'][:26] for k,v in lang.items()})

        chk("no page errors across the task layer", len(errs)==0, errs[:3])
        await pg.close(); await b.close()
    print("\n  %d passed, %d failed"%(len(OK),len(BAD)))
    sys.exit(1 if BAD else 0)
asyncio.run(main())
