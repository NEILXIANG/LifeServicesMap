#!/usr/bin/env python3
"""2026-09-24 — design tokens: fewer type sizes, fewer radii, one palette.

The audit counted 19 different font-size values (9px through 26px) and 15
different border-radius values (3px through 999px) in one stylesheet. Hierarchy
was being expressed by half-pixel differences that nobody can see, which is the
same as no hierarchy — weight and colour do that work, size should come from a
scale.

Type: seven steps — 10 / 11.5 / 12.5 / 14 / 17 / 22 / 26. Every existing value
snaps to the nearest, and the scale deliberately keeps the three most-used sizes
(11.5, 12.5, 14) where they are, so the great majority of declarations move by
0.5px or not at all. Nothing moves by more than 1.5px, and the largest single
move is downward.

Radius: four tokens — 6 (inline badges, inputs, thin bars, map tooltips),
10 (small controls), 14 (cards, panels, sheets, the map itself) and 999 (pills).
The 18px / 20px / 99px values were all already on pill-shaped controls where a
stadium and a 20px corner render identically; they become 999 so the intent is
stated rather than implied. (The audit proposed three tokens; four is what the
markup actually has roles for — collapsing the small-control step into the card
step would put a 14px corner on a 24px close button.)

Palette: the popup's state chips were Material greys and pastels sitting inside
an otherwise Apple-derived palette. "Closed now" now uses the page's own
--paper / --sub-ink tokens instead of two hardcoded Material greys, and the
"open" and "holiday" tints move to the Apple green/orange family. Contrast was
checked for each pair: 5.55:1, 4.54:1 and 6.22:1, all above AA.

Left alone: the offline notice and the footer's emergency band keep their amber
and red. They are page-level alerts rather than chips, their colour is the
signal, and both already clear AA.
"""
import re, sys

E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
cut = s.index('</style>')
css, rest = s[:cut], s[cut:]

# ---------------------------------------------------------------- type scale
FONT = {'9': '10', '9.5': '10', '10': '10', '10.5': '10',
        '11': '11.5', '11.5': '11.5', '12': '11.5',
        '12.5': '12.5', '13': '12.5',
        '13.5': '14', '14': '14', '14.5': '14', '15': '14', '15.5': '14',
        '16': '17', '17': '17', '18': '17',
        '22': '22', '26': '26'}
seen_f = {}
def _font(m):
    v = m.group(1)
    if v not in FONT: sys.exit('unmapped font-size %s' % v)
    seen_f[v] = seen_f.get(v, 0) + 1
    return 'font-size:' + FONT[v] + 'px'
css = re.sub(r'font-size:([\d.]+)px', _font, css)

# ------------------------------------------------------------------- radii
RAD = {'3': '6', '4': '6', '5': '6', '6': '6', '7': '6',
       '8': '10', '9': '10', '10': '10',
       '12': '14', '14': '14', '16': '14',
       '18': '999', '20': '999', '99': '999', '999': '999'}
seen_r = {}
def _rad(m):
    v = m.group(1)
    if v not in RAD: sys.exit('unmapped border-radius %s' % v)
    seen_r[v] = seen_r.get(v, 0) + 1
    return 'border-radius:' + RAD[v] + 'px'
css = re.sub(r'border-radius:([\d.]+)px', _rad, css)

s = css + rest

# --------------------------------------------------------------- state chips
def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:110], n))
    s = s.replace(old, new)

rep("""  .pv-open.on{background:#e6f4ea;color:#137333;}
  .pv-open.off{background:#f1f3f4;color:#5f6368;}""",
    """  /* 2026-09-24: "closed" was two hardcoded Material greys inside an Apple
     palette — it uses the page's own tokens now. "Open" and the holiday pill
     move to the Apple green/orange family. Contrast 5.55:1, 4.54:1, 6.22:1. */
  .pv-open.on{background:#e6f7ec;color:#12703a;}
  .pv-open.off{background:var(--paper);color:var(--sub-ink);}""")
rep("""  .pv-open.hol{background:#fff3e0;color:#8a4b00;}""",
    """  .pv-open.hol{background:#fff2e0;color:#8a4a00;}""")

open(E, 'w', encoding='utf-8').write(s)
print('p28 applied')
print('  font-size values folded:', {k: seen_f[k] for k in sorted(seen_f, key=float)})
print('  radius values folded  :', {k: seen_r[k] for k in sorted(seen_r, key=float)})
print('  scale now             :', sorted(set(FONT[k] for k in seen_f), key=float),
      sorted(set(RAD[k] for k in seen_r), key=float))
