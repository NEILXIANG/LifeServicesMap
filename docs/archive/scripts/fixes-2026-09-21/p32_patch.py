#!/usr/bin/env python3
"""2026-09-24 — two labels that ran off the screen in some languages.

Found by opening every panel, modal and popup in all six languages at 320, 390
and 430 px and measuring every text box against the viewport:

1. The Area panel. Each area button carries its name and a plain-language
   description ("Sahali/Aberdeen (hillside south of Downtown, home to TRU) · 85")
   and was white-space:nowrap, so on a 390 px phone — the most common size —
   the English, French, Spanish and Japanese labels ran up to 70 px past the
   right edge, cutting off the description and the count. A button may now wrap
   onto a second line inside its own pill; nothing else about it changes.

2. The crisis-line list. Each line (number + who it is for) was nowrap as a
   whole; on a 320 px phone the longer ones in French, Japanese and Chinese ran
   past the box. The line may wrap now, but the number itself never breaks.
"""
import sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    s = s.replace(old, new)
rep("  .reg-row{display:flex;flex-wrap:wrap;gap:6px;padding:0 0 12px;}",
    "  .reg-row{display:flex;flex-wrap:wrap;gap:6px;padding:0 0 12px;}\n"
    "  /* 2026-09-24: an area's name plus its description is wider than a phone in four\n"
    "     of the six languages — let the label wrap inside its pill instead of running\n"
    "     off the screen (the rule below keeps nowrap for everything that fits). */\n"
    "  .reg-row .reg-btn{white-space:normal;max-width:100%;text-align:left;line-height:1.35;}")
rep("  .hotlines .hl-line{white-space:nowrap;color:var(--ink);text-decoration:none;}",
    "  .hotlines .hl-line{white-space:normal;color:var(--ink);text-decoration:none;}\n"
    "  .hotlines .hl-line b{white-space:nowrap;}   /* the line may wrap, the number never does */")
open(E, 'w', encoding='utf-8').write(s)
print('p32 applied')
