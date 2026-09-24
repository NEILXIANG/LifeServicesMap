#!/usr/bin/env python3
"""2026-09-24 — "Open now" no longer hangs the crisis lines under the filter row.

Turning on "Open now" used to add a "📞 24-hour lines" block under the filter
chips — 911, two suicide lines including 9-8-8, the mental-health line, 8-1-1,
VictimLink and the Indigenous crisis line — at any hour and whatever the result.
Almost everyone who taps "Open now" wants an open pharmacy or grocery; at two in
the afternoon a row of suicide lines is beside the point, reads as alarming, and
takes a band of the phone screen above the map.

The lines are not lost anywhere they are needed:
  - the Help button in the header, on every screen;
  - a crisis word in the search box, in any of the six languages;
  - "Open now" with nothing open — the empty state still says everything is
    closed and lists the lines that answer around the clock.

On a statutory holiday the chip row still says that listed hours may not apply.
That sentence used to end "these lines answer around the clock", pointing at the
block that is now gone, so the chip row gets its own copy without that clause
(holidayChipNote); the empty state keeps the full sentence, where the lines are.
"""
import re, sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    s = s.replace(old, new)

rep("""  // With "open now" on, the reader may be asking at an hour when the answer is
  // a phone, not a door. The 24-hour lines ride along with the chip row — no
  // extra tap, no need for the result to be empty first.
  if(openNow){
    const hl=document.createElement('div');hl.className='af-hotlines';
    hl.innerHTML=(isHolidayToday()?'<p class="af-holiday">'+esc(u.holidayOpenNote)+'</p>':'')+hotlineHtml(true);
    root.appendChild(hl);
  }""",
"""  // 2026-09-24: the 24-hour lines used to ride along here whenever "open now"
  // was on — a row of crisis lines under a search for an open pharmacy at 2 pm.
  // They stay where they answer a real need: the Help button, a crisis search,
  // and the empty state when nothing at all is open. On a statutory holiday the
  // row still says listed hours may not hold.
  if(openNow&&isHolidayToday()){
    const hn=document.createElement('div');hn.className='af-note';
    hn.innerHTML='<p class="af-holiday">'+esc(u.holidayChipNote)+'</p>';
    root.appendChild(hn);
  }""")
rep("  .af-hotlines{flex:0 0 100%;}\n", "  .af-note{flex:0 0 100%;}\n")
rep("  .af-hotlines .hotlines{margin:4px 0 0;}\n", "")

# the chip-row holiday sentence, without the clause that pointed at the lines
m = re.search(r"^UI\.zh\.holidayOpenNote=.*$", s, re.M)
line = m.group(0)
vals = dict(re.findall(r"UI\.(\w\w)\.holidayOpenNote='((?:[^'\\]|\\.)*)'", line))
TAIL = {'zh': '下面这些电话 24 小时有人接。', 'en': ' These lines answer around the clock.',
        'fr': ' Ces lignes répondent jour et nuit.', 'es': ' Estas líneas atienden a toda hora.',
        'ko': ' 아래 전화는 24시간 받습니다.', 'ja': '以下の電話は24時間つながります。'}
new = []
for l in ('zh', 'en', 'fr', 'es', 'ko', 'ja'):
    v = vals[l]
    if not v.endswith(TAIL[l]): sys.exit('%s holidayOpenNote does not end as expected: %r' % (l, v[-40:]))
    new.append("UI.%s.holidayChipNote='%s';" % (l, v[:-len(TAIL[l])].rstrip()))
s = s.replace(line, line + '\n' + ''.join(new), 1)

open(E, 'w', encoding='utf-8').write(s)
print('p33 applied')
