#!/usr/bin/env python3
"""2026-09-24 — the icon audit: one wrong icon, one unreadable on older phones,
two that looked alike, two headings that stayed emoji, and four weak choices.

1. "Free & low-cost" was a dollar sign. In a row where everything else is a
   pictogram, "$" is the universal sign for *costs money* — the opposite of the
   82 places behind that chip. It now carries a struck-through dollar: no charge.
2. Parks used 🛝 (playground slide), which is Emoji 14.0 — released in 2021 and
   missing on Android 11 and iOS 15.3 and older, where the city's 22 parks would
   all show an empty box. 🌳 is Emoji 1.0 and renders everywhere.
3. "Just moved" (suitcase) and "Lost your job" (briefcase) were the same drawing
   with a slightly different handle. The suitcase now has wheels and a trolley
   handle, which is what tells the two apart at 20 px.
4. The licence and privacy headings were the only section titles left as colour
   emoji; every other title in the app is a line icon. 📜 maps to the document
   icon, 🔒 to a new lock, and both headings now go through iconify.
5. Weak category icons: a bus-stop sign for the school bus (🚸, the children's
   crossing, is what a school bus means), a recycling symbol for thrift stores
   (👕), a balloon for the indoor play centre (🎠), and a laundry basket that was
   the same picture as the "daily life" theme (🧼).

Left alone on purpose:
- 🪶 for Indigenous services: Emoji 13.0 (2020), supported on anything still
  getting security updates, and no other emoji carries the meaning.
- ⚠️ in the error toast and 📲 on the system-share button: both sit among emoji,
  not line icons — the share grid is a row of channel logos.
- The unused 'school' line icon (it draws an open book). No string starts with
  🏫 today, so it renders nowhere; worth redrawing before anything uses it.
"""
import re, sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:110], n))
    return src.replace(old, new)

# ---- 1. "free" is no longer a plain dollar sign
s = rep(s, """<path d="M12 5v14"/><path d="M15.5 8.5a3 3 0 00-3-1.5h-1a2.5 2.5 0 000 5h1a2.5 2.5 0 010 5h-1a3 3 0 01-3-1.5"/>""",
           """<path d="M12 5v14"/><path d="M15.5 8.5a3 3 0 00-3-1.5h-1a2.5 2.5 0 000 5h1a2.5 2.5 0 010 5h-1a3 3 0 01-3-1.5"/><path d="M5 19.5L19 4.5"/>""")

# ---- 3. a suitcase you can tell from a briefcase: wheels and a trolley handle
s = rep(s, """<rect x="4" y="8" width="16" height="11" rx="2"/><path d="M9 8V6a2 2 0 012-2h2a2 2 0 012 2v2"/><path d="M4 13h16"/>""",
           """<rect x="5" y="7.5" width="14" height="11" rx="2"/><path d="M10 7.5V5.6a1.6 1.6 0 011.6-1.6h.8A1.6 1.6 0 0114 5.6v1.9"/><path d="M8.5 18.5v1.6M15.5 18.5v1.6"/><path d="M8.5 21.4h.01M15.5 21.4h.01"/>""")

# ---- 4. a lock for the privacy heading, and the two headings become line icons
s = rep(s, "  key:'", "  lock:'<rect x=\"5\" y=\"10.5\" width=\"14\" height=\"9.5\" rx=\"2\"/><path d=\"M8.5 10.5V8a3.5 3.5 0 017 0v2.5\"/>',\n  key:'")
s = rep(s, "'🔑':'key',", "'🔑':'key','📜':'doc','🔒':'lock',")
s = rep(s, """let pv='<div class="privacy-note"><div class="pv-h">'+esc(u.legalTitle)+'</div><ul class="pv-sum">';""",
           """let pv='<div class="privacy-note"><div class="pv-h">'+iconify(u.legalTitle)+'</div><ul class="pv-sum">';""")
s = rep(s, """pv+='<div class="privacy-note"><div class="pv-h">'+esc(u.privacyTitle)+'</div><ul class="pv-sum">';""",
           """pv+='<div class="privacy-note"><div class="pv-h">'+iconify(u.privacyTitle)+'</div><ul class="pv-sum">';""")

# ---- 2 & 5. category icons
for cat, old, new, why in [
    ('park',       '🛝', '🌳', 'Emoji 14.0 shows as an empty box on older phones'),
    ('schoolbus',  '🚏', '🚸', 'a bus-stop sign is not a school bus'),
    ('secondhand', '♻️', '👕', 'the recycling symbol reads as a depot, not a thrift store'),
    ('playcenter', '🎈', '🎠', 'a balloon says nothing about an indoor play centre'),
    ('laundry',    '🧺', '🧼', 'the basket was also the "daily life" theme icon'),
]:
    pat = '"%s":"%s"' % (cat, old)
    if s.count(pat) != 1: sys.exit('IC entry %s (%s) appears %d times' % (cat, old, s.count(pat)))
    s = s.replace(pat, '"%s":"%s"' % (cat, new))

open(E, 'w', encoding='utf-8').write(s)
print('p26 applied')
