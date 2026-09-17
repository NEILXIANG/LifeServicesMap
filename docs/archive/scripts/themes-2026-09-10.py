# -*- coding: utf-8 -*-
"""Assigns the overlapping `t` (theme) field to every place.

Themes are a second, deliberately overlapping axis on top of the single-valued
category: a library is one `library` record but is at once a family outing, a
free resource, a cultural venue, an indoor winter option and a student's desk.
Categories answer "what kind of place is this"; themes answer "what am I in the
mood to do / what am I short of".

Assignment is rule-driven from the category, plus a small table of per-record
additions. Both are auditable: nothing here asserts a fact that the record's own
verified note does not already support. Scenic and History in particular are
assigned only where the note states the reason (a view, a waterfall, a landmark,
a heritage site), never merely because the category sounds like it might.
"""
import json, re, collections
import os, sys
_r = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    if os.path.exists(os.path.join(_r, 'kamdata.py')): break
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import kamdata


BY_CAT = {
  'grocery':['life'], 'asian':['life','multi'], 'conv':['life'], 'pharmacy':['life'],
  'bank':['life'], 'post':['life'], 'laundry':['life'], 'barber':['life'],
  'gas':['life'], 'hardware':['life'], 'liquor':['life'], 'gov':['life'],
  'mall':['life','fun','indoor'], 'restaurant':['life','fun'],
  'cafe':['life','fun','indoor','student'], 'secondhand':['life','free'],
  'transit':['life','student'],
  'park':['family','free'], 'splash':['family','free','fun'],
  'playcenter':['family','fun','indoor'], 'daycare':['family'],
  'elem':['family'], 'school':['family'], 'schoolbus':['family'],
  'tutor':['family','student'],
  'library':['family','free','culture','indoor','student','multi'],
  'museum':['culture','indoor'],
  'cinema':['fun','indoor'],
  'pool':['fun','family','indoor'], 'rink':['fun','family','indoor'],
  'gym':['fun','indoor','student'],
  'trail':['scenic','free'], 'beach':['scenic','free','family','fun'],
  'dogpark':['free'],
  'religious':['multi'], 'commctr':['multi','free','indoor'],
  'legal':['free'],
  'foodbank':['free','multi'],
  'heritage':['history','culture','scenic'],
}

# Per-record additions. The right-hand comment is the evidence in that record's
# own note; if a note is ever rewritten so the evidence disappears, the theme
# should go with it.
ADD = {
  # scenic — the note names a view, a waterfall, a river frontage or an island
  'Riverside Park':                       ['scenic','fun'],       # beach + summer concerts
  'McArthur Island Park':                 ['scenic','fun'],       # island, 3 km loop, wild deer
  'Overlanders Park':                     ['scenic'],             # riverside beach, good views
  'Juniper Ridge Park':                   ['scenic'],             # valley-view trail
  'Aberdeen Hills Park':                  ['scenic'],             # open hill views
  'Pineview Valley Park':                 ['scenic'],             # pond, creek, trails
  # history — the note names a heritage site or a landmark building
  'Kamloops Museum & Archives':           ['history','family'],   # city museum + children's area
  'Secwepemc Museum & Heritage Park':     ['history','multi'],    # outdoor heritage site
  'Sacred Heart Cathedral':               ['history','culture'],  # downtown landmark
  "St. Paul's Anglican Cathedral":        ['history','culture'],  # downtown landmark
  # culture
  'Kamloops Art Gallery':                 ['culture','family'],
  'The Paramount Theatre':                ['culture'],            # independent film + live concerts
  'Kamloops Japanese Canadian Cultural Centre': ['culture'],      # exhibitions, language classes
  'Kamloops Sikh Cultural Society':       ['culture','free'],     # community gatherings, free Langar meal
  'Kamloops Buddhist Temple':             ['culture'],
  'Ayesha Mosque':                        ['culture'],
  # fun / family attractions
  'BC Wildlife Park':                     ['fun'],                # miniature train, animals, water play
  'Sandman Centre':                       ['fun'],                # main arena and concert venue
  'Riverside Park Outdoor Skating and Multi-Use Loop': ['free'],  # note says "Free!"
  'Todd Hill Park':                       ['fun'],                # winter sledding hill
  'Westsyde Centennial Park':             ['fun'],                # mini farm, water play, skating
  'McDonald Park':                        ['fun'],                # Sunday art market
  # newcomer-facing
  '⭐⭐ Kamloops Immigrant Services':      ['multi','free'],       # free LINC classes and childcare
  'Okanagan Thompson Legal Clinic':       ['multi'],              # serves immigrants and refugees
  'Thompson Rivers University (TRU)':     ['student','culture'],
  'TRU Exchange':                         ['student'],
  'YMCA-YWCA of Kamloops(Downtown Y)':    ['family'],             # pool, gym and childcare
}

ORDER = ['life','family','fun','scenic','history','culture','free','multi','student','indoor']

def build(P):
    for p in P:
        t = set(BY_CAT.get(p['c'], []))
        t |= set(ADD.get(p['n'], []))
        if t:
            p['t'] = [k for k in ORDER if k in t]
        else:
            p.pop('t', None)
    return P

if __name__ == '__main__':
    P = kamdata.load('P')
    known = {p['n'] for p in P}
    missing = [k for k in ADD if k not in known]
    assert not missing, 'ADD names not in data: %s' % missing
    build(P)
    kamdata.save('P', P)
    c = collections.Counter()
    for p in P:
        for k in p.get('t', []): c[k] += 1
    print('records with a theme: %d / %d' % (sum(1 for p in P if p.get('t')), len(P)))
    for k in ORDER: print('  %-8s %3d' % (k, c[k]))
