#!/usr/bin/env python3
"""2026-09-22 — fixes from the independent re-audit. Each change is backed by at
least two independent sources, checked on 2026-09-22:

A. Bus "last trip" times (12 routes). BC Transit's current GTFS feed (valid from
   2026-09-19, operatorIds=46) shows the old values came from a one-day New Year's
   Eve service (service_id active on 2026-12-31 only). Replaced by the latest trip
   of regular service (services running on 4+ dates). First trips were already right.
B. Map positions of 20 places. BC Address Geocoder (civic number, score 95-100),
   OpenStreetMap and the Google Maps pin agree with each other (within ~130 m) and
   disagree with the stored point by 0.3-4.8 km. Where the corrected point lies in
   another area, the area moves with it (Windsor Plywood → Sahali/Aberdeen,
   Columbia Manor → South Kamloops, Airport Shuttle and DriveHub → Brocklehurst,
   Secwepemc Museum and TteS Administration → Valleyview, next to Powwow Trail).
C. Brocklehurst Outdoor Pool phone: the City facility page lists 250 554 1747.
D. Mustard Seed West End Shelter: its link opened the Mustard Seed's Calgary shelter
   page; now bc211's listing, which describes the Kamloops shelter (30 beds,
   250-372-9890, 181 Victoria St W). Bed count 20 → 30 in the place note and in the
   "money runs out" card, six languages.
E. Kamloops Family Justice Centre: link to the Kamloops page (hours, phone, address)
   instead of the province-wide page.
F. Seven-digit "310-" lines (310-6478 Interior Health MHSU, 310-6789) are now
   tappable wherever phone numbers are linked, like every other number.
No step is added to or removed from any card."""
import sys, json, re
sys.path.insert(0, '.')
import kamdata
E, D = 'src/engine.html', 'src/data-kamloops.js'
s = open(E, encoding='utf-8').read()
d = open(D, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:100], n))
    return src.replace(old, new)
J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)

# ---------------------------------------------------------------- A. bus last trips
m = re.search(r'^const BR=(.*);\s*$', d, re.M)
assert J(json.loads(m.group(1))) == m.group(1), 'BR does not round-trip'
BR = json.loads(m.group(1))
LAST = {'1': ('26:09', '25:14'), '2': ('25:34', '22:33'), '3': ('25:14', '24:16'), '4': ('25:31', '24:07'),
        '5': ('24:51', '23:21'), '6': ('24:41', '22:03'), '7': ('26:25', '25:50'), '13': ('25:43', '20:46'),
        '14': ('24:50', '20:56'), '16': ('25:24', '20:22'), '17': ('25:49', '24:04')}
for k, (old, new) in LAST.items():
    assert BR[k]['l'] == old, (k, BR[k]['l'])
    BR[k]['l'] = new
for k in ('9', '10', '18'):
    assert BR[k]['l'] in ('26:16', '21:32', '22:39'), (k, BR[k]['l'])   # already regular service — unchanged
d = d[:m.start(1)] + J(BR) + d[m.end(1):]

# ---------------------------------------------------------------- B-E. place records
def edit_place(pid, fn):
    global d
    lines = d.split('\n')
    hit = [i for i, l in enumerate(lines) if ('"id":"%s"' % pid) in l]
    assert len(hit) == 1, (pid, len(hit))
    i = hit[0]; line = lines[i]
    mm = re.match(r'^(\s*)(\{.*\})(,?)\s*$', line)
    assert mm, pid
    o = json.loads(mm.group(2))
    assert J(o) == mm.group(2), 'record does not round-trip: ' + pid
    fn(o)
    lines[i] = mm.group(1) + J(o) + mm.group(3)
    d = '\n'.join(lines)

MOVE = {  # id: (lat, lng, new area or None, drop 'precision: low')
 '42b06f2f': (50.662069, -120.357339, 'sa'),      # Windsor Plywood, 735 Laval Cres
 'bfd3954a': (50.697292, -120.356781, None),      # Central Apartments, 209 Nelson Ave
 'c8e62dff': (50.671986, -120.308858, 'sk'),      # Columbia Manor, 1336 Columbia St
 'b4d3cd9d': (50.673948, -120.355155, None),      # Dufferin Terrace, 525 Dalgleish Dr
 '8244ba59': (50.677511, -120.27276, None),       # Valleyview Manor, 174 Oriole Rd
 '54085508': (50.679311, -120.362198, None),      # The View Apartments, 955 Victoria St W
 'ffdd8aff': (50.672074, -120.335076, None),      # Sacred Heart Cathedral, 255 Nicola St
}
def by_name(n):
    ids = [p['id'] for p in kamdata.load('P') if p['n'] == n]
    assert len(ids) == 1, n
    return ids[0]
NAMED = {
 'Kamloops Buddhist Temple': (50.692979, -120.363694, None),
 'Kamloops Sikh Cultural Society': (50.699207, -120.382327, None),
 'Kamloops Airport Shuttle': (50.717673, -120.368786, 'br'),
 'DriveHub Autosales': (50.708948, -120.370805, 'br'),
 'All Aboard Child Care': (50.637545, -120.376287, None),
 'Colour My World Childcare': (50.712897, -120.364001, None),
 'Kamloops Kidz Early Learning Center': (50.670869, -120.226663, None),
 'Apex Adventure Plex Kamloops': (50.668372, -120.35191, None),
 'Kamloops Aboriginal Friendship Society': (50.685622, -120.356446, None),
 'Child Care Resource & Referral (YMCA BC)': (50.689905, -120.355183, None),
 'Kamloops Japanese Canadian Cultural Centre': (50.695422, -120.357749, None),
 'Secwepemc Museum & Heritage Park': (50.678306, -120.294779, 'vv'),
 'Tk̓emlúps te Secwépemc Administration': (50.679533, -120.294305, 'vv'),
 'Chevron (Westsyde)': None,
}
P0 = {p['id']: p for p in kamdata.load('P')}
for n, v in NAMED.items():
    MOVE[by_name(n)] = v
# Chevron Westsyde: BC geocoder and the OSM "Chevron" node at 2711 Westsyde Rd (19 m apart)
MOVE[by_name('Chevron (Westsyde)')] = (50.751562, -120.353873, None)
KEEP_LOW = {by_name('Tk̓emlúps te Secwépemc Administration')}   # block-level geocode only
assert len(MOVE) == 21, len(MOVE)
for pid, (lat, lng, g) in MOVE.items():
    def f(o, lat=lat, lng=lng, g=g, pid=pid):
        o['lat'], o['lng'] = lat, lng
        if g: o['g'] = g
        if o.get('precision') == 'low' and pid not in KEEP_LOW: del o['precision']
    edit_place(pid, f)

def pool(o):
    assert o['p'] == '250-828-3654'; o['p'] = '250-554-1747'
edit_place('a5d0f9dc', pool)

BEDS = {'en': ('20 beds', '30 beds'), 'fr': ('20 lits', '30 lits'), 'es': ('20 camas', '30 camas'),
        'zh': ('20 张床位', '30 张床位'), 'ko': ('남녀 20병상', '남녀 30병상'), 'ja': ('男女20床', '男女30床')}
def seed(o):
    assert o['w'] == 'https://theseed.ca/emergency-shelter'
    o['w'] = 'https://bc.211.ca/agency-details/the-mustard-seed-9490188/'
    for l, (a, b2) in BEDS.items():
        assert o['note'][l].count(a) == 1, (l, a)
        o['note'][l] = o['note'][l].replace(a, b2)
edit_place('25cf033e', seed)

def fjc(o):
    assert o['w'].endswith('/family-justice-centres')
    o['w'] = o['w'] + '/locations/kamloops'
edit_place('c92d454d', fjc)

# the shelter paragraph on the "money runs out" card
open(D, 'w', encoding='utf-8').write(d)
T = kamdata.load('TASKS')
t = [x for x in T if x['id'] == 'hardship'][0]
CARD = {'en': '250-372-9890 (20 beds', 'fr': '250-372-9890 (20 lits', 'es': '250-372-9890 (20 camas',
        'zh': '250-372-9890（20 张床位', 'ko': '250-372-9890(20병상', 'ja': '250-372-9890（20床'}
for l, a in CARD.items():
    assert t['note'][l].count(a) == 1, (l, a)
    t['note'][l] = t['note'][l].replace(a, a.replace('20', '30'))
kamdata.save('TASKS', T)

# ---------------------------------------------------------------- F. 310- numbers are tappable
s = rep(s, r"return str.replace(/(\d{3}[-\s]?\d{3}[-\s]?\d{4}|\b\d-\d-\d\b)/g,",
           r"return str.replace(/(\d{3}[-\s]?\d{3}[-\s]?\d{4}|\b310-\d{4}\b|\b\d-\d-\d\b)/g,")
open(E, 'w', encoding='utf-8').write(s)

# ---------------------------------------------------------------- self-check
P1 = {p['id']: p for p in kamdata.load('P')}
assert len(P1) == len(P0)
changed = {i for i in P0 if P0[i] != P1[i]}
assert changed == set(MOVE) | {'a5d0f9dc', '25cf033e', 'c92d454d'}, changed ^ (set(MOVE) | {'a5d0f9dc', '25cf033e', 'c92d454d'})
for i in changed:
    diff = {k for k in set(P0[i]) | set(P1[i]) if P0[i].get(k) != P1[i].get(k)}
    assert diff <= {'lat', 'lng', 'g', 'precision', 'p', 'w', 'note'}, (i, diff)
print('p11 applied: %d places, %d routes' % (len(changed), len(LAST)))
