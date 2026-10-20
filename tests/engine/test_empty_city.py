#!/usr/bin/env python3
"""A brand-new city straight out of scripts/new-city.py — no places, no task cards,
no bus routes, no landmarks, no local crisis line — must still load and work.

That is the state every new city starts in, and the state a half-finished one is
reviewed in. Creates cities/_empty_test/, builds it, drives the page, removes it.
Also checks validate.py refuses the skeleton because of its TODOs.
"""
import asyncio, os, shutil, subprocess, sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CID = '_empty_test'
DIRS = [os.path.join(ROOT, 'cities', CID), os.path.join(ROOT, 'deploy', CID)]
P = F = 0
def check(name, ok, info=None):
    global P, F
    if ok: P += 1; print('  PASS', name)
    else: F += 1; print('  FAIL', name, ' —', info)

def cleanup():
    for d in DIRS:
        shutil.rmtree(d, ignore_errors=True)
    try: os.remove(os.path.join(ROOT, 'build', CID + '.html'))
    except FileNotFoundError: pass

async def main():
    cleanup()
    subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'new-city.py'), CID,
                    '--name', 'Emptyville', '--centre', '49.888,-119.496'], check=True, capture_output=True)
    subprocess.run([sys.executable, os.path.join(ROOT, 'build.py'), '--city', CID], check=True, capture_output=True)
    v = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'validate.py'), '--city', CID],
                       capture_output=True, text=True)
    check('validate.py refuses a skeleton that still has TODOs', v.returncode != 0 and 'TODO' in v.stdout, v.stdout[-300:])

    url = 'file://' + os.path.join(ROOT, 'build', CID + '.html')
    errors = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': 1280, 'height': 900})
        pg.on('pageerror', lambda e: errors.append(str(e)[:200]))
        await pg.goto(url + '?lang=en'); await pg.wait_for_timeout(1500)
        check('the empty city loads under its own name', (await pg.title()) == 'Emptyville Life Guide', await pg.title())
        steps = ["()=>{searchInputEl.value='doctor';runSearch();}",
                 "()=>{searchInputEl.value='suicide';runSearch();}",   # crisis path with no local line
                 "()=>{searchInputEl.value='';runSearch();}",
                 "()=>openGuide('test')",
                 "()=>{['zh','ja','ko','es','fr','en'].forEach(setLang)}",
                 "()=>openPanel('bus')", "()=>openPanel('fav')",
                 "()=>document.getElementById('helpBtn').click()"]
        for js in steps:
            await pg.evaluate(js); await pg.wait_for_timeout(250)
        await pg.goto(url + '?lang=en&task=msp'); await pg.wait_for_timeout(800)   # a task id the city lacks
        check('search, guide, languages, panels, help and a missing task raise no page error', not errors, errors[:3])
        await b.close()
    cleanup()
    print('\n%d passed, %d failed' % (P, F))
    sys.exit(1 if F else 0)

try:
    asyncio.run(main())
finally:
    cleanup()
