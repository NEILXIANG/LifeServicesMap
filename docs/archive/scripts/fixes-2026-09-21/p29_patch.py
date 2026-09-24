#!/usr/bin/env python3
"""2026-09-24 — the map pin becomes a flat circle, in the cluster's language.

The audit's finding: at any zoom where both are on screen, the map drew two
unrelated visual languages at once — place pins as skeuomorphic teardrops with a
drop-shadowed point, and cluster bubbles as flat geometric circles with a white
ring and a soft shadow. Same map, same layer, same tap target, two idioms.

The pin is now the same object as a cluster bubble: a 30px circle, a 2.5px white
ring and the cluster's own shadow, with the category colour as the fill and the
category's glyph on a white face inside it. It keeps the glyph the pin has always
carried (the user chose to keep the emoji rather than redraw 51 line icons), and
that glyph is the same one the identity chip in the popup and the category filter
print, so the three surfaces finally agree.

Two consequences worth stating:

- The anchor moves from the teardrop's point to the circle's centre, which is
  what a cluster does and what a place's coordinates actually mean. A pin now
  sits *on* its address instead of 21px above it.
- The route-focus rule dimmed the pin by killing an SVG filter; a circle carries
  a box-shadow, so that rule targets the element rather than the drawing, and
  scales from the centre rather than from the vanished point.
"""
import sys
E = 'src/engine.html'
s = open(E, encoding='utf-8').read()
def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:110], n))
    s = s.replace(old, new)

# ---- the marker itself
rep("""// Google-style pin: a crisp vector teardrop drawn directly in its final orientation
// (no CSS rotate transform on the shape — rotating a div was what made the old
// diamond-icon markers look soft/blurry, especially once dozens overlap on screen).
function mkIcon(k){
  const c=CD[k];
  const svg='<svg width="28" height="38" viewBox="0 0 28 38" xmlns="http://www.w3.org/2000/svg" style="display:block;filter:drop-shadow(0 2px 3px rgba(0,0,0,.35))">'
    +'<path d="M14 0C6.268 0 0 6.268 0 14c0 10.5 14 24 14 24s14-13.5 14-24C28 6.268 21.732 0 14 0z" fill="'+c+'" stroke="#fff" stroke-width="1.5"/>'
    +'<circle cx="14" cy="14" r="9.5" fill="#fff"/>'
    +'<text x="14" y="19" font-size="13.5" text-anchor="middle">'+IC[k]+'</text>'
    +'</svg>';
  // The class is what lets a selected bus route push these into the background
  // (see .route-focus below) and what lets a label know a pin is in its way.
  return L.divIcon({html:svg,className:'kpin',iconSize:[28,38],iconAnchor:[14,36],popupAnchor:[0,-34]});
}""",
    """// 2026-09-24 — the pin is a flat circle built from the same parts as a cluster
// bubble (see .kcluster): one ring width, one shadow, one shape language on the
// map. The category colour is the fill, the glyph sits on a white face so a
// colour emoji stays legible on every one of the 51 fills, and the anchor is the
// circle's centre — a place now sits on its coordinates rather than 21px above
// them, which is also how the cluster it collapses into behaves.
// (No CSS rotate on the shape: rotating a div was what made the original
// diamond markers look soft once dozens overlapped.)
function mkIcon(k){
  const html='<div class="kpin-dot" style="background:'+catColour(k)+'"><span>'+(IC[k]||'')+'</span></div>';
  // The class is what lets a selected bus route push these into the background
  // (see .route-focus below) and what lets a label know a pin is in its way.
  return L.divIcon({html:html,className:'kpin',iconSize:[30,30],iconAnchor:[15,15],popupAnchor:[0,-16]});
}""")

# ---- the pin's own rule, next to the cluster's so the two stay in step
rep("""  .kcluster{background:var(--accent);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;""",
    """  /* the place pin: the cluster bubble's ring and shadow at 30px, with the
     category colour outside and the glyph on a white face inside */
  .kpin-dot{width:30px;height:30px;border-radius:999px;border:2.5px solid #fff;
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 1px 3px rgba(60,64,67,.4),0 3px 8px rgba(60,64,67,.25);}
  .kpin-dot>span{width:20px;height:20px;border-radius:999px;background:#fff;
    display:flex;align-items:center;justify-content:center;font-size:14px;line-height:1;}
  .kcluster{background:var(--accent);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;""")

# ---- route focus: the drawing is a box now, not an SVG
rep("""  .route-focus .kpin svg{filter:none;transform:scale(.86);transform-origin:50% 100%;}""",
    """  .route-focus .kpin .kpin-dot{box-shadow:none;transform:scale(.86);}""")

open(E, 'w', encoding='utf-8').write(s)
print('p29 applied')
