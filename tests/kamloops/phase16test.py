#!/usr/bin/env python3
"""2026-09-24 — the icon audit (p26): the "free" theme is no longer a dollar
sign, parks use an emoji old phones can draw, the suitcase and the briefcase are
telling apart, the last two emoji headings became line icons, and four weak
category icons were replaced."""
import asyncio, os, sys
from playwright.async_api import async_playwright
_r = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tests/ (files live in tests/kamloops/)
URL = 'file://' + os.path.join(os.path.dirname(_r), 'build', 'kamloops.html')
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

# Emoji 13.0 (2020) and later: a phone that predates them draws an empty box.
# 🪶 (13.0) is a deliberate exception — nothing older carries the meaning.
TOO_NEW = ['🛝', '🫧', '🛜', '🪇', '🩻', '🪭', '🪮', '🫆', '🩼', '🛟', '🪫', '🫙']

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 430, 'height': 930}, is_mobile=True, has_touch=True)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)

        # ---- the wrong icon
        free = await pg.evaluate("()=>ICONS.free")
        check('"free & low-cost" is a struck-through dollar, not a plain dollar sign',
              free.count('<path') >= 3 and 'M5 19.5L19 4.5' in free, free[:80])
        svg = await pg.evaluate("""()=>{setLang('en');const el=[...document.querySelectorAll('#themeRow button')]
            .find(b=>/free/i.test(b.textContent));return el?el.innerHTML.slice(0,200):null}""")
        check('  …and the chip on screen draws it as an icon, not a character', svg and '<svg' in svg, svg)

        # ---- the two cases
        suit, brief = await pg.evaluate("()=>[ICONS.suitcase,ICONS.briefcase]")
        check('the suitcase and the briefcase are different drawings', suit != brief)
        check('  …the suitcase is the one with wheels', 'M8.5 21.4h.01' in suit and 'M8.5 21.4h.01' not in brief, suit[:90])

        # ---- headings that were emoji
        check('a lock icon exists and 📜 / 🔒 map to line icons',
              await pg.evaluate("()=>!!ICONS.lock&&EMOJI_ICON['🔒']==='lock'&&EMOJI_ICON['📜']==='doc'"))
        await pg.evaluate("()=>{trackEvent('note_open',{});openModal(noteBackdropEl);}")
        await pg.wait_for_timeout(1200)
        heads = await pg.evaluate("()=>[...document.querySelectorAll('.pv-h')].map(e=>e.innerHTML)")
        check('both headings in the data panel render an icon', len(heads) >= 2 and all('<svg' in h for h in heads), len(heads))
        check('  …and no colour emoji is left in them',
              all(not any(ch in h for ch in '📜🔒') for h in heads), heads[0][:60] if heads else None)
        await pg.evaluate("()=>closeModal(noteBackdropEl)"); await pg.wait_for_timeout(400)

        # ---- category icons
        ic = await pg.evaluate("()=>IC")
        for cat, want in (('park', '🌳'), ('schoolbus', '🚸'), ('secondhand', '👕'), ('playcenter', '🎠'), ('laundry', '🧼')):
            check('%s now uses %s' % (cat, want), ic.get(cat) == want, ic.get(cat))
        bad = [c for c, e in ic.items() if e in TOO_NEW]
        check('no category depends on an emoji older phones cannot draw', not bad, bad)
        dupes = [e for e in set(ic.values()) if list(ic.values()).count(e) > 1]
        check('no two categories share an icon', not dupes, dupes)
        cats = await pg.evaluate("()=>Object.keys(CI)")
        check('every category has an icon', all(c in ic and ic[c] for c in cats), [c for c in cats if not ic.get(c)])
        check('the laundry basket no longer doubles as the "daily life" theme',
              await pg.evaluate("()=>IC.laundry!==TIC.life"))

        # ---- nothing that used to be an icon stopped being one
        miss = await pg.evaluate("""()=>{const out=[];
            Object.entries(TIC).forEach(([k,v])=>{if(!EMOJI_ICON[v])out.push('theme:'+k);});
            (typeof TASKS!=='undefined'?TASKS:[]).forEach(t=>{if(!EMOJI_ICON[t.icon])out.push('task:'+t.id);});
            return out}""")
        check('every theme and task card still resolves to a line icon', not miss, miss)

        # ---- the map still draws the changed categories
        shown = await pg.evaluate("""()=>{aC=new Set(['park','laundry','secondhand','playcenter','schoolbus']);renderCats();apply();
            const pins=[...document.querySelectorAll('.kpin')].map(e=>e.textContent).join('');
            const v=lastVisible;aC=new Set();renderCats();apply();
            return {v,hasTree:pins.includes('🌳'),hasSoap:pins.includes('🧼'),old:/🛝|♻️|🎈|🚏/.test(pins)}}""")
        check('the map draws the new icons and none of the old ones', shown['v'] > 0 and shown['hasTree'] and not shown['old'], shown)
        check('no page errors', not errs, errs[:3])
        await b.close()
    print('\n%d passed, %d failed' % (P, F)); sys.exit(1 if F else 0)
asyncio.run(main())
