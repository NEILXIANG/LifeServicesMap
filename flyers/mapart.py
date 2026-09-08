#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Draw a stylised, Google-Maps-light illustration of Kamloops.

Geographic precision is deliberately relaxed (the flyer asks for recognition,
not survey accuracy) but nothing is invented: every label sits on the real
coordinate of the place it names, taken from the project's own verified records,
and the water is drawn through control points on the real river courses — the
North Thompson down from Westsyde, the South Thompson in from Valleyview, their
confluence at Riverside Park, and the Thompson running west past McArthur Island
into Kamloops Lake.
"""
import re, json, math

d = open('src/data-kamloops.js', encoding='utf-8').read()
BR = json.loads(re.search(r'const BR=(\{.*?\});\s*\n', d, re.S).group(1))
P = json.loads(re.search(r'const P=(\[.*?\]);\s*\n', d, re.S).group(1))

K = math.cos(math.radians(50.70))

# --- the frame: the city plus enough west to reach the lake ------------------
LAT0, LAT1 = 50.6430, 50.7300        # Aberdeen bench -> above Brocklehurst
LNG0, LNG1 = -120.5150, -120.2530    # head of Kamloops Lake -> Valleyview

def make(W, H, bounds=None):
    la0, la1, lo0, lo1 = bounds or (LAT0, LAT1, LNG0, LNG1)
    spanx = (lo1 - lo0) * K
    spany = (la1 - la0)
    sx, sy = W / spanx, H / spany
    s = max(sx, sy)
    offx = (W - spanx * s) / 2
    offy = (H - spany * s) / 2
    def xy(la, lo):
        return ((lo - lo0) * K * s + offx, (la1 - la) * s + offy)
    return xy

def smooth(pts):
    """Catmull-Rom through the points, emitted as cubic beziers, so a river
    drawn from a handful of control points reads as a river and not a hinge."""
    if len(pts) < 2:
        return ''
    d = ['M%.1f,%.1f' % pts[0]]
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append('C%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (c1[0], c1[1], c2[0], c2[1], p2[0], p2[1]))
    return ' '.join(d)

# --- real courses, as control points on the actual rivers -------------------
NORTH_THOMPSON = [(50.790,-120.332),(50.766,-120.338),(50.742,-120.336),(50.718,-120.329),
                  (50.700,-120.327),(50.690,-120.330),(50.6830,-120.3345)]
SOUTH_THOMPSON = [(50.6735,-120.238),(50.6768,-120.262),(50.6800,-120.288),(50.6815,-120.310),
                  (50.6830,-120.3345)]
THOMPSON_WEST  = [(50.6830,-120.3345),(50.6885,-120.356),(50.6940,-120.378),(50.6985,-120.404),
                  (50.7035,-120.436),(50.7080,-120.470),(50.7115,-120.500)]
# Kamloops Lake, entered from the east — only its head is inside this frame.
LAKE = [(50.7115,-120.500),(50.7180,-120.520),(50.7250,-120.548),(50.7290,-120.585),
        (50.7300,-120.625),(50.7270,-120.660),
        (50.7060,-120.660),(50.7040,-120.620),(50.7010,-120.580),(50.6990,-120.545),
        (50.7040,-120.516),(50.7080,-120.503)]

# --- hills: the benchland and the hills that box this valley in -------------
HILLS = [
  # south bench rising to Aberdeen / Kenna Cartwright
  [(50.6180,-120.470),(50.6300,-120.430),(50.6400,-120.395),(50.6480,-120.372),
   (50.6540,-120.345),(50.6520,-120.305),(50.6420,-120.270),(50.6300,-120.245),
   (50.6180,-120.240)],
  # Mount Paul and the east side, across the river from downtown
  [(50.6830,-120.250),(50.6900,-120.262),(50.6960,-120.280),(50.6980,-120.300),
   (50.6930,-120.310),(50.6870,-120.300),(50.6845,-120.275)],
  # the north-shore benches behind Brocklehurst and Westsyde
  [(50.7300,-120.430),(50.7450,-120.400),(50.7600,-120.385),(50.7750,-120.380),
   (50.7900,-120.390),(50.7900,-120.470),(50.7600,-120.470),(50.7400,-120.455)],
]
GREEN = [   # the two parks a resident would name first
  ('Kenna Cartwright Park', 50.6640, -120.3830, 0.0072, 0.018),
  ('McArthur Island',       50.6964, -120.3772, 0.0042, 0.011),
]

# (kind, text, lat, lng, dx, dy) — dx/dy in px at the reference width, so a name
# can clear its own marker and its neighbours without moving off its location.
LABELS = [
  ('city',  'DOWNTOWN',             50.6742, -120.3230,   0,  26),
  ('city',  'NORTH SHORE',          50.7010, -120.3540,   0, -10),
  ('city',  'SAHALI',               50.6600, -120.3480,   0,  16),
  ('city',  'ABERDEEN',             50.6505, -120.3760,   0,  14),
  ('city',  'VALLEYVIEW',           50.6790, -120.2660,   0,  30),
  ('city',  'BROCKLEHURST',         50.7060, -120.3960,   0, -12),
  ('water', 'Kamloops Lake',        50.7020, -120.5480,  10,   0),
  ('water', 'North Thompson River', 50.7080, -120.3300,  78,   2),
  ('water', 'South Thompson River', 50.6818, -120.2900,   0, -14),
  ('water', 'Thompson River',       50.7000, -120.4230,   0, -16),
  ('poi',   'TRU',                  50.6708, -120.3660,   0,   0),
  ('poi',   'Riverside Park',       50.6784, -120.3369,   0, -12),
  ('poi',   'Kenna Cartwright Park',50.6635, -120.3775,   0,   0),
]

def build(W, H, *, tone='colour', labels=True, roads=True, bounds=None):
    xy = make(W, H, bounds)
    out = []
    if tone == 'colour':
        land, water, green, hill = '#f3f4f5', '#a9d4ef', '#cfe8d0', '#eceeed'
        road_case, road_fill = '#e3e5e7', '#ffffff'
    else:                                   # the pale wash used behind body text
        land, water, green, hill = '#f7f9fb', '#d8e9f6', '#e3eee2', '#f1f3f4'
        road_case, road_fill = '#e8ebee', '#ffffff'
    out.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, land))
    for h in HILLS:
        out.append('<path d="%s Z" fill="%s"/>' % (smooth([xy(a, b) for a, b in h]), hill))
    out.append('<path d="%s Z" fill="%s"/>' % (smooth([xy(a, b) for a, b in LAKE]), water))
    for pts, w in ((NORTH_THOMPSON, 13), (SOUTH_THOMPSON, 13), (THOMPSON_WEST, 17)):
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="%d" '
                   'stroke-linecap="round" stroke-linejoin="round"/>'
                   % (smooth([xy(a, b) for a, b in pts]), water, w * (W / 1240.0)))
    for _, la, lo, rla, rlo in GREEN:
        cx, cy = xy(la, lo)
        rx = abs(xy(la, lo + rlo)[0] - cx)
        ry = abs(xy(la + rla, lo)[1] - cy)
        out.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s"/>' % (cx, cy, rx, ry, green))
    if roads:
        segs = []
        for r in BR.values():
            p = r.get('p') or []
            if len(p) > 1:
                segs.append(smooth([xy(a, b) for a, b in p][::3] or [xy(*p[0])]))
        sw = W / 1240.0
        out.append('<g fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" '
                   'stroke-linejoin="round">%s</g>'
                   % (road_case, 6.5 * sw, ''.join('<path d="%s"/>' % s for s in segs)))
        out.append('<g fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" '
                   'stroke-linejoin="round">%s</g>'
                   % (road_fill, 3.6 * sw, ''.join('<path d="%s"/>' % s for s in segs)))
    if labels:
        sw = W / 1240.0
        for kind, text, la, lo, dx, dy in LABELS:
            x, y = xy(la, lo)
            x += dx * sw; y += dy * sw
            if kind == 'city':
                out.append('<text x="%.1f" y="%.1f" class="lb-city">%s</text>' % (x, y, text))
            elif kind == 'water':
                out.append('<text x="%.1f" y="%.1f" class="lb-water">%s</text>' % (x, y, text))
            else:
                out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" class="lb-dot"/>' % (x, y, 4.2 * sw))
                out.append('<text x="%.1f" y="%.1f" class="lb-poi">%s</text>' % (x + 7 * sw, y + 4 * sw, text))
    return '\n'.join(out)

if __name__ == '__main__':
    W, H = 1240, 500
    css = '''<style>
      .lb-city{font:700 %.0fpx "Roboto",Arial,sans-serif;fill:#5f6368;letter-spacing:.12em;text-anchor:middle}
      .lb-water{font:italic 500 %.0fpx "Roboto",Arial,sans-serif;fill:#5b93bf;text-anchor:middle}
      .lb-poi{font:600 %.0fpx "Roboto",Arial,sans-serif;fill:#3c4043}
      .lb-dot{fill:#188038}
    </style>''' % (15, 14, 13)
    open('/tmp/shots/mapart.svg', 'w').write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">%s%s</svg>'
        % (W, H, W, H, css, build(W, H)))
    print('wrote /tmp/shots/mapart.svg')
