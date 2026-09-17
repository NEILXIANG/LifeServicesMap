# -*- coding: utf-8 -*-
"""Repairs coordinates that disagree with their own street's geometry.

Downtown streets here are straight, so position is very nearly linear in the
civic number. Fitting that line through a street's surveyed rows predicts where
every other row on the street belongs. A plain least-squares fit is useless for
this, though: the bad rows are in the sample and drag the line toward themselves,
which is exactly how a 231 m error hid behind an inflated tolerance. So the fit
is iterated — fit, drop anything past 3x the median residual, refit — until it
settles on the rows that agree with each other, and only then are the rest
measured against it.

Repaired rows keep their address (which was always right, and is what the
Directions button uses) and are marked precision='low', because a fitted
position is derived from this project's own surveyed rows, not surveyed itself.
"""
import json, re, math, sys

MOVE_OVER = 200          # metres: repair anything further off than this
MIN_ANCHORS = 8

def dp(x): return len(str(x).split('.')[-1]) if '.' in str(x) else 0
def civic(a):
    m = re.search(r'(\d{2,5})\s+([A-Za-z].*)$', (a or '').replace('#', ' '))
    if not m: return None
    st = re.sub(r'\b(unit|suite|ste)\b.*', '', m.group(2), flags=re.I)
    return int(m.group(1)), re.sub(r'[^a-z]', '', st.lower())[:14]

def linfit(xs, vals):
    mx = sum(xs) / len(xs); my = sum(vals) / len(vals)
    den = sum((x - mx) ** 2 for x in xs)
    if not den: return None
    return (sum((x - mx) * (v - my) for x, v in zip(xs, vals)) / den, my, mx)

def robust(rows):
    """rows = [(civic, lat, lng)] -> (predict, rms, kept) or None."""
    keep = list(rows)
    for _ in range(6):
        if len(keep) < MIN_ANCHORS: return None
        xs = [r[0] for r in keep]
        if len(set(xs)) < 5: return None
        fa = linfit(xs, [r[1] for r in keep]); fo = linfit(xs, [r[2] for r in keep])
        if not fa or not fo: return None
        pred = lambda n: (fa[1] + fa[0] * (n - fa[2]), fo[1] + fo[0] * (n - fo[2]))
        res = []
        for n, la, ln in keep:
            pla, pln = pred(n)
            res.append(math.hypot((la - pla) * 111000, (ln - pln) * 111000 * 0.635))
        med = sorted(res)[len(res) // 2]
        cut = max(3 * med, 60)
        nxt = [r for r, d in zip(keep, res) if d <= cut]
        if len(nxt) == len(keep):
            rms = (sum(d * d for d in res) / len(res)) ** 0.5
            return pred, rms, len(keep)
        keep = nxt
    return None

path = 'src/data-kamloops.js'
s = open(path, encoding='utf-8').read()
m = re.search(r"const P=(\[.*?\]);\n", s, re.S)
P = json.loads(m.group(1))

streets = {}
for p in P:
    c = civic(p['a'])
    if c: streets.setdefault(c[1], []).append((c[0], p))

moved = 0
for st, items in sorted(streets.items()):
    if len(items) < 8: continue
    anchors = [(n, p['lat'], p['lng']) for n, p in items
               if min(dp(p['lat']), dp(p['lng'])) >= 5 and p.get('precision') != 'low']
    r = robust(anchors)
    if not r: continue
    pred, rms, kept = r
    if rms > 60: continue
    print('%-16s %2d rows, ruler from %2d of %2d surveyed, rms %.0f m'
          % (st, len(items), kept, len(anchors), rms))
    for n, p in sorted(items, key=lambda t: t[0]):
        la, ln = pred(n)
        d = math.hypot((p['lat'] - la) * 111000, (p['lng'] - ln) * 111000 * 0.635)
        if d > MOVE_OVER:
            print('    MOVE %-36s %6.0f m -> %.6f,%.6f' % (p['n'][:36], d, la, ln))
            p['lat'] = round(la, 6); p['lng'] = round(ln, 6); p['precision'] = 'low'
            moved += 1
        elif d > 120:
            print('    keep %-36s %6.0f m (within tolerance)' % (p['n'][:36], d))

open(path, 'w', encoding='utf-8').write(
    s[:m.start(1)] + json.dumps(P, ensure_ascii=False, separators=(',', ':')) + s[m.end(1):])
print('\n%d coordinate(s) repaired' % moved)
