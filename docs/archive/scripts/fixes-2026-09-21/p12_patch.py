#!/usr/bin/env python3
"""2026-09-22 — Aberdeen Tiny Library Saturday hours, per the branch page
tnrl.ca/using-the-library/locations/aberdeen-tiny-library/ (Sat 10:00-4:00; the
record said 12:00-4:00). The other two Kamloops branches were checked against
their TNRL pages the same day and match (hours, phone, address)."""
import sys, json, re
D = 'src/data-kamloops.js'
d = open(D, encoding='utf-8').read()
J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)
lines = d.split('\n')
hit = [i for i, l in enumerate(lines) if '"id":"c597c849"' in l]
assert len(hit) == 1
mm = re.match(r'^(\s*)(\{.*\})(,?)\s*$', lines[hit[0]])
o = json.loads(mm.group(2)); assert J(o) == mm.group(2)
assert o['n'] == 'Aberdeen Tiny Library'
assert o['h'] == {"r": [[2, 3, 720, 960, 0], [4, 5, 600, 1020, 0], [6, 6, 720, 960, 0], [7, 7, 720, 960, 0]]}, o['h']
o['h']['r'][2] = [6, 6, 600, 960, 0]
lines[hit[0]] = mm.group(1) + J(o) + mm.group(3)
open(D, 'w', encoding='utf-8').write('\n'.join(lines))
print('p12 applied')
