#!/usr/bin/env python3
"""2026-09-22 — follow-ups from the 5-day analytics review.

1. DATA_VERSION 2026.09.13f → 2026.09.22. The 22 Sept release went live still
   reporting 2026.09.13f, so old- and new-version events could not be told apart.
2. "walk in clinic" returned no places (a real visitor searched it). The North
   Shore UPCC — the one walk-in door in the city — gains the terms people type
   for it, in six languages. (South Shore UPCLC is appointment-only, so it does
   not get "walk-in clinic".)
3. Maintainer device flag. Opening the site once with ?maintainer=1 marks that
   browser as the maintainer's; from then on every event it sends carries
   env:'dev' (double2 = 1), exactly like ?debug=1, and is left out of real-user
   queries. ?maintainer=0 clears it. The key sits outside the kamloops* prefix
   on purpose, so the Help sheet's "clear this device" does not silently drop it.
"""
import sys, json, re
sys.path.insert(0, '.')
import kamdata
E, D = 'src/engine.html', 'src/data-kamloops.js'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    return src.replace(old, new)

s = rep(s, "const DATA_VERSION='2026.09.13f';", "const DATA_VERSION='2026.09.22';")

s = rep(s, "const _IS_DEBUG=/[?&]debug=1\\b/.test(location.search);\n",
"""const _IS_DEBUG=/[?&]debug=1\\b/.test(location.search);
// 2026-09-22: the maintainer's own phone and laptop were 57% of five days of
// "user" events. ?maintainer=1 marks this browser once, for good; ?maintainer=0
// unmarks it. Tagged exactly like ?debug=1 (env:'dev'), without the debug panel.
const _OWNER_KEY='lifemapMaintainer';
const _IS_OWNER=(function(){try{
  const m=/[?&]maintainer=([01])\\b/.exec(location.search);
  if(m){if(m[1]==='1')localStorage.setItem(_OWNER_KEY,'1');else localStorage.removeItem(_OWNER_KEY);}
  return localStorage.getItem(_OWNER_KEY)==='1';
}catch(e){return false;}})();
""")
s = rep(s, "    if(_IS_DEBUG)safeProps=Object.assign({env:'dev'},safeProps||{});",
           "    if(_IS_DEBUG||_IS_OWNER)safeProps=Object.assign({env:'dev'},safeProps||{});")
open(E, 'w', encoding='utf-8').write(s)

# ---- UPCC aliases
d = open(D, encoding='utf-8').read()
J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)
lines = d.split('\n')
hit = [k for k, l in enumerate(lines) if '"id":"b29c9af7"' in l]; assert len(hit) == 1
mm = re.match(r'^(\s*(?:const P=\[)?)(\{.*\})(,|\];)?\s*$', lines[hit[0]])
o = json.loads(mm.group(2)); assert J(o) == mm.group(2)
assert o['n'] == 'North Shore Urgent Care (UPCC)'
assert o['alias'] == ['急诊', 'walk in', 'walkin', '급한', '急患'], o['alias']
o['alias'] += ['walk in clinic', 'walk-in clinic', 'walk-in', 'clinique sans rendez-vous',
               'clínica sin cita', '无需预约的诊所', '免预约诊所', '워크인 클리닉', 'ウォークインクリニック']
lines[hit[0]] = mm.group(1) + J(o) + (mm.group(3) or '')
open(D, 'w', encoding='utf-8').write('\n'.join(lines))
print('p16 applied')
