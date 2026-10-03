#!/usr/bin/env python3
"""2026-09-24 — the popup rebuild (p27), the token convergence (p28) and the flat
map pin (p29): one chip vocabulary, one type scale, one radius set, one shape
language on the map, and an action row that is actually on screen."""
import asyncio, os, re, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_r)
URL = 'file://' + os.path.join(ROOT, 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

TYPE_SCALE = {'10', '11.5', '12.5', '14', '17', '22', '26'}
RADII = {'6', '10', '14', '999'}

def static_checks():
    # the app's own stylesheet, not the vendor CSS (Leaflet and markercluster are
    # inlined into the build and carry their own sizes and radii)
    sys.path.insert(0, ROOT); import kamdata; src = kamdata.engine_text()
    css = src[:src.index('</style>')]
    sizes = sorted(set(re.findall(r'font-size:([\d.]+)px', css)), key=float)
    check('every font-size in the stylesheet is on the 7-step scale',
          set(sizes) <= TYPE_SCALE, [x for x in sizes if x not in TYPE_SCALE])
    rad = sorted(set(re.findall(r'border-radius:([\d.]+)px', css)), key=float)
    check('every border-radius is one of the four tokens',
          set(rad) <= RADII, [x for x in rad if x not in RADII])
    check('  …and the scale is actually used, not collapsed to one size', len(sizes) >= 5, sizes)
    for dead in ('.tag2{', '.tag3{', '.tag.tag-pick{'):
        check('the superseded chip rule %s is gone' % dead.rstrip('{'), dead not in css)

async def main():
    static_checks()
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 430, 'height': 930}, is_mobile=True, has_touch=True)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)

        # ---------------------------------------------------------- chips
        html = await pg.evaluate("()=>{const p=P.find(x=>x.p&&x.h&&x.t&&x.t.length);return popup(p,P.indexOf(p));}")
        check('the place popup uses the new chip classes only',
              'pchip' in html and 'class="tag' not in html, html[:120])

        ink = await pg.evaluate("""()=>{const srgb=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);};
            const lum=c=>0.2126*srgb(c[0])+0.7152*srgb(c[1])+0.0722*srgb(c[2]);
            const rgb=h=>{h=h.replace('#','');return [0,2,4].map(i=>parseInt(h.slice(i,i+2),16));};
            const ratio=(a,b)=>{const x=lum(rgb(a)),y=lum(rgb(b));return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);};
            const bad=[];
            Object.keys(CI).forEach(c=>{const col=catColour(c),t=catInk(c);
              const bg=rgb(col).map(v=>Math.round(v*0.11+255*0.89));
              const hex='#'+bg.map(v=>('0'+v.toString(16)).slice(-2)).join('');
              if(ratio(t,hex)<4.5)bad.push([c,col,t,+ratio(t,hex).toFixed(2)]);});
            return {n:Object.keys(CI).length,bad};}""")
        check('every one of the %d category chips clears 4.5:1 on its own tint' % ink['n'],
              not ink['bad'], ink['bad'][:4])

        chip = await pg.evaluate("""()=>{const p=P.find(x=>x.g&&/[（(]/.test(regLabel(x.g)));
            const d=document.createElement('div');d.innerHTML=popup(p,P.indexOf(p));
            const id=d.querySelector('.pchip-id'), rg=d.querySelector('.pchip-meta.pv-cut');
            return {glyph:id&&id.textContent.slice(0,2).trim(), want:IC[p.c],
                    short:rg&&rg.textContent.trim(), full:rg&&rg.getAttribute('title')};}""")
        check('the identity chip carries the same glyph as the map pin',
              chip['glyph'] and chip['glyph'].startswith(chip['want'][0]), chip)
        check('the area chip shows the short name and keeps the explanation in its tooltip',
              chip['short'] and '(' not in chip['short'] and '(' in (chip['full'] or ''), chip)

        # ------------------------------------------------- label/value grid
        grid = await pg.evaluate("""()=>{const p=P.find(x=>x.p&&x.e&&x.h);if(!p)return {skip:1};
            const d=document.createElement('div');d.style.cssText='position:fixed;left:0;top:0;width:305px';
            d.innerHTML=popup(p,P.indexOf(p));document.body.appendChild(d);
            const vals=[...d.querySelectorAll('.pkv .pval')].map(e=>Math.round(e.getBoundingClientRect().left));
            const kv=d.querySelector('.pkv'), task=d.querySelector('.pv-task');
            const order=!task||(kv.compareDocumentPosition(task)&Node.DOCUMENT_POSITION_FOLLOWING)>0;
            d.remove();return {vals,order};}""")
        if grid.get('skip'):
            check('label/value grid', False, 'no place with phone+email+hours')
        else:
            check('phone / email / hours values share one left edge',
                  len(set(grid['vals'])) == 1 and len(grid['vals']) >= 2, grid['vals'])
        check('the task card follows the facts instead of splitting them', grid.get('order', True), grid)

        # ------------------------------------------------- provenance line
        prov = await pg.evaluate("""()=>{const p=P.find(x=>x.src==='official'&&x.v);
            const d=document.createElement('div');d.innerHTML=popup(p,P.indexOf(p));document.body.appendChild(d);
            const s=d.querySelector('.pv-src'),cs=getComputedStyle(s);
            const kinds=['src-official','src-own','src-opendata','src-stub'].map(k=>{
              const e=document.createElement('span');e.className='pv-src '+k;d.appendChild(e);
              const c=getComputedStyle(e,'::before').backgroundColor;e.remove();return c;});
            const out={bg:cs.backgroundColor,cls:s.className,kinds:new Set(kinds).size};d.remove();return out;}""")
        check('the source badge is no longer a filled block',
              prov['bg'] in ('rgba(0, 0, 0, 0)', 'transparent'), prov['bg'])
        check('  …and the four source kinds are still told apart by colour', prov['kinds'] == 4, prov)

        # ------------------------------------------------- the star
        star = await pg.evaluate("""()=>{const p=P[0];const d=document.createElement('div');
            d.innerHTML=popup(p,0);const s=d.querySelector('.fav-star');
            return {svg:!!s.querySelector('svg.ic'), glyph:/[★☆]/.test(s.textContent)};}""")
        check('the favourite control draws the icon set\'s star, not a character',
              star['svg'] and not star['glyph'], star)

        # ------------------------------------------------- state chips
        st = await pg.evaluate("""()=>{const srgb=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);};
            const px=s=>s.match(/\\d+/g).slice(0,3).map(Number);
            const lum=c=>0.2126*srgb(c[0])+0.7152*srgb(c[1])+0.0722*srgb(c[2]);
            const ratio=(a,b)=>{const x=lum(a),y=lum(b);return +((Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)).toFixed(2);};
            const out={};['on','off','hol'].forEach(k=>{const e=document.createElement('span');
              e.className='pv-open '+k;e.textContent='x';document.body.appendChild(e);
              const c=getComputedStyle(e);out[k]=ratio(px(c.color),px(c.backgroundColor));e.remove();});
            const sub=getComputedStyle(document.documentElement).getPropertyValue('--sub-ink').trim();
            const e=document.createElement('span');e.className='pv-open off';document.body.appendChild(e);
            const usesToken=getComputedStyle(e).color===(()=>{const t=document.createElement('i');
              t.style.color=sub;document.body.appendChild(t);const v=getComputedStyle(t).color;t.remove();return v;})();
            e.remove();out.usesToken=usesToken;return out;}""")
        check('open / closed / holiday chips all clear AA (%s)' % {k: st[k] for k in ('on', 'off', 'hol')},
              all(st[k] >= 4.5 for k in ('on', 'off', 'hol')), st)
        check('  …and "closed" uses the page\'s own grey token, not a second palette', st['usesToken'], st)

        # ------------------------------------------------- the sticky action row
        tall = await pg.evaluate("""async()=>{const i=P.map((p,k)=>[k,(noteText(p)||'').length]).sort((a,b)=>b[1]-a[1])[0][0];
            const m=M.find(x=>x.data.id===P[i].id);map.setView([P[i].lat,P[i].lng],17);m.openPopup();
            for(let t=0;t<40;t++){if(document.querySelector('.pact'))break;await new Promise(r=>setTimeout(r,120));}
            await new Promise(r=>setTimeout(r,700));
            const box=document.querySelector('.leaflet-popup-content'),a=document.querySelector('.pact');
            if(!box||!a)return {none:true};
            box.scrollTop=0;await new Promise(r=>setTimeout(r,120));
            const b1=a.getBoundingClientRect(),c1=box.getBoundingClientRect();
            const scrollable=box.scrollHeight>box.clientHeight+2;
            return {scrollable,sticky:getComputedStyle(a).position==='sticky',
                    insideAtTop:b1.bottom<=c1.bottom+2&&b1.top>=c1.top-2,
                    ctas:document.querySelectorAll('.pact .pact-btn').length};}""")
        check('the tallest popup really does scroll', tall.get('scrollable'), tall)
        check('the action row is sticky and on screen before any scrolling',
              tall.get('sticky') and tall.get('insideAtTop'), tall)
        check('  …with all its buttons', tall.get('ctas', 0) >= 1, tall)
        await pg.evaluate("()=>map.closePopup()"); await pg.wait_for_timeout(300)

        # ------------------------------------------------- the pin
        pin = await pg.evaluate("""()=>{const d=document.querySelector('.kpin .kpin-dot');
            if(!d)return {none:true};const r=d.getBoundingClientRect();const cs=getComputedStyle(d);
            const ic=mkIcon('park');
            const k=document.createElement('div');k.className='kcluster s';document.body.appendChild(k);
            const kr=getComputedStyle(k).borderTopWidth;k.remove();
            return {w:Math.round(r.width),h:Math.round(r.height),radius:cs.borderRadius,
                    ring:cs.borderTopWidth,clusterRing:kr,shadow:cs.boxShadow!=='none',
                    size:ic.options.iconSize,anchor:ic.options.iconAnchor,
                    svg:!!document.querySelector('.kpin svg')};}""")
        check('the pin is a circle, not a teardrop',
              pin.get('w') == 30 and pin.get('h') == 30 and not pin.get('svg'), pin)
        # computed border-width is rounded to whole device pixels, so compare the pin
        # with the cluster rather than with the literal 2.5px in the stylesheet
        check('  …with the cluster bubble\'s ring and shadow',
              pin.get('ring') == pin.get('clusterRing') and pin.get('shadow'), pin)
        check('  …anchored at its centre, like the cluster it collapses into',
              pin.get('anchor') == [pin['size'][0] / 2, pin['size'][1] / 2], pin)
        glyphs = await pg.evaluate("()=>[...document.querySelectorAll('.kpin')].map(e=>e.textContent).join('')")
        check('the pins still carry their category glyphs', len(glyphs.strip()) > 0, glyphs[:12])

        # ------------------------------------------------- nothing broke
        await pg.evaluate("()=>{searchInputEl.value='pharmacy';runSearch();}"); await pg.wait_for_timeout(700)
        n = await pg.evaluate("()=>lastVisible")
        check('search still returns results after the restyle (%s)' % n, n > 0, n)
        await pg.evaluate("()=>{searchInputEl.value='';runSearch();}"); await pg.wait_for_timeout(400)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
