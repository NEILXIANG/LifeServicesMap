#!/usr/bin/env python3
"""2026-09-24 — licensed child care, from the province's own Child Care Map.

The map had 4 child care records; Kamloops has 128 licensed facilities. Parents
searching "daycare" were seeing 3% of what exists, which is worse than useless
when every centre has a waitlist.

This adds the 82 licensed GROUP facilities that are not already on the map,
from the Child Care Map dataset published by the Province of British Columbia
(updated daily, Open Government Licence – British Columbia; the licence panel
now carries the attribution).

Deliberately left out:
- the 38 "licensed family" providers. Those operate out of private homes, and
  putting 38 residential addresses on a public map is a different decision from
  listing a centre. The note sends parents to Child Care Resource & Referral,
  which knows the family providers and is already on the map.
- 8 facilities that are already listed (matched by name, or within 40 m of an
  existing record): the four child care records, the francophone centre, and
  three school-based programs at schools already on the map.
- opening hours and websites: the dataset has neither, so these records say
  "hours unknown" rather than inventing them.

Every record keeps the provincial source label (src: opendata), which tells the
reader in their own language that this came from government data and was not
confirmed by phone one by one.
"""
import csv, json, math, re, sys, uuid

D = 'src/data-kamloops.js'
CSV = '/tmp/a7/cc.csv'
J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)

NOTE = {
 "zh": "持牌托儿机构（BC 省政府开放数据）。托儿位普遍紧张，去之前先打电话问有没有空位、收什么年龄段。找不到位子可以打 Child Care Resource & Referral 250-376-4771，他们帮你找并且免费。",
 "en": "Licensed child care (BC government open data). Spaces are scarce — call first to ask about openings and the ages they take. If you cannot find a space, Child Care Resource & Referral (250-376-4771) will help you search, free.",
 "fr": "Garderie autorisée (données ouvertes du gouvernement de la C.-B.). Les places sont rares — téléphonez d’abord pour demander s’il y a de la place et quels âges sont acceptés. Si vous ne trouvez rien, Child Care Resource & Referral (250-376-4771) vous aide gratuitement.",
 "es": "Guardería con licencia (datos abiertos del gobierno de BC). Hay pocas plazas: llame antes para preguntar por vacantes y las edades que aceptan. Si no encuentra plaza, Child Care Resource & Referral (250-376-4771) le ayuda a buscar, gratis.",
 "ko": "허가받은 보육시설(BC주 정부 공개 데이터). 자리가 부족하니 먼저 전화해 빈자리와 받는 연령을 물어보세요. 자리를 찾기 어려우면 Child Care Resource & Referral(250-376-4771)이 무료로 도와줍니다.",
 "ja": "認可保育施設（BC州政府のオープンデータ）。空きが少ないので、まず電話で空き状況と受け入れ年齢を確認してください。見つからない場合は Child Care Resource & Referral（250-376-4771）が無料で探すのを手伝ってくれます。",
}
# The province's child care dataset shares one coordinate between neighbouring
# centres (350 and 352 Seymour St came out 5 m apart with the same point), so
# every address was re-resolved against the BC Address Geocoder on 2026-09-24.
# Its answer is used when it scores 95+ and lands within 150 m of the province's
# own point; otherwise the province's point is kept and the record is marked
# "approximate location", which the map shows plainly.
GEO = {
"520 6Th Ave": [
50.6729366,
-120.3274604,
100
],
"559 Battle St": [
50.6729739,
-120.3278391,
100
],
"1565 Summit Dr": [
50.6579226,
-120.3386023,
100
],
"492 mcgill Rd": [
50.6700872,
-120.3524174,
100
],
"480 Kenora Rd": [
50.6975313,
-120.3694193,
100
],
"950 Southill St": [
50.7044512,
-120.3980096,
100
],
"2250 Park Dr": [
50.677788,
-120.2577279,
100
],
"348 Fortune Dr": [
50.6895517,
-120.3493957,
100
],
"920 Greystone Cres": [
50.6428589,
-120.3640629,
100
],
"120 West Shuswap Rd": [
50.700996,
-120.3401551,
95
],
"350 Seymour St": [
50.6751231,
-120.332879,
100
],
"201-3200 Valleyview Dr": [
50.6710606,
-120.2266329,
100
],
"352 Seymour St": [
50.6751589,
-120.3328745,
100
],
"1579 Collingwood Dr": [
50.7129708,
-120.3639672,
100
],
"3550 Westsyde Rd": [
50.7738893,
-120.3413155,
100
],
"3255 Overlander Dr": [
50.7709541,
-120.3413596,
100
],
"1136 6Th Ave": [
50.6675491,
-120.3274889,
100
],
"750 Cottonwood Ave": [
50.6968191,
-120.3686989,
100
],
"30-945 Columbia St W": [
50.6685119,
-120.3536951,
100
],
"3125 Serle Ct": [
50.7630551,
-120.3510252,
100
],
"810 Sicamore Dr": [
50.7727778,
-120.3421394,
100
],
"629 Battle St": [
50.6729815,
-120.3262191,
100
],
"779 Franklin Rd": [
50.7510182,
-120.3535409,
100
],
"110-206 Seymour St": [
50.6751296,
-120.3363721,
100
],
"40-945 Columbia St W": [
50.6685119,
-120.3536951,
100
],
"767 Seymour St": [
50.6747285,
-120.3223052,
100
],
"101-2049 Highland Pl": [
50.6618812,
-120.2624491,
100
],
"1351 Dunbar Dr": [
50.6387717,
-120.3782137,
100
],
"259 Seymour St": [
50.67444,
-120.335039,
100
],
"163 Oriole Rd": [
50.678053,
-120.2719699,
100
],
"315 Chestnut Ave": [
50.6949344,
-120.351587,
100
],
"2632 Young Pl": [
50.7048942,
-120.4239035,
100
],
"1500 9 Ave": [
50.6633372,
-120.3203542,
100
],
"2481 Sunset Dr": [
50.6747897,
-120.2476579,
100
],
"604 Tranquille Rd": [
50.6944877,
-120.3598417,
100
],
"101-5170 Dallas Dr": [
50.6688563,
-120.1858419,
100
],
"759 Seymour St": [
50.6747303,
-120.322518,
100
],
"5201 Dallas Dr": [
50.6677816,
-120.1842485,
100
],
"1205 Rogers Way": [
50.6510504,
-120.3704715,
100
],
"1550 Tranquille Rd": [
50.7024684,
-120.3817164,
100
],
"628 Sun Valley Dr": [
50.7738549,
-120.3338897,
100
],
"886 Morven Pl": [
50.7534001,
-120.3555593,
100
],
"1780 Valleyview Dr": [
50.6754661,
-120.2879247,
100
],
"2200 Park Dr": [
50.6761336,
-120.2564058,
100
],
"1640A & 1640B Happyvale Ave": [
50.6995284,
-120.3861349,
97
],
"2060 Pala Mesa Pl": [
50.6998581,
-120.4030742,
100
],
"1800 Tranquille Rd": [
50.7006368,
-120.3949057,
100
],
"249 Seymour Street": [
50.6744436,
-120.3354646,
100
],
"715 Uplands Crt": [
50.6620827,
-120.1914494,
100
],
"753 Seymour St": [
50.6747329,
-120.3227449,
100
],
"1380 Sherbrooke Ave": [
50.7043101,
-120.3764261,
100
],
"2170 Parkcrest Ave": [
50.7080316,
-120.4070413,
100
],
"1051 Pine Spring Road": [
50.6693773,
-120.3151013,
91
],
"444 Seymour St": [
50.6751084,
-120.3304664,
100
],
"101-2079 Falcon Rd": [
50.6784735,
-120.2684075,
100
],
"2-510 Lorne Street": [
50.6785177,
-120.3299925,
100
],
"203-1020 Talasa Way": [
50.686198,
-120.2982817,
94
],
"1799 Springview Pl": [
50.6558639,
-120.3576868,
100
],
"1152 Nicola St": [
50.6724486,
-120.3125956,
100
],
"1099 Fraser St": [
50.6661025,
-120.3146787,
100
],
"3214 Hargraves Pl": [
50.7659262,
-120.3520288,
100
],
"24-750 Fortune Dr": [
50.6998073,
-120.3600814,
100
],
"107-910 Columbia Street W.": [
50.6684033,
-120.35493,
99
],
"110-945 Columbia St W": [
50.6685119,
-120.3536951,
100
],
"2191 Van Horne Dr": [
50.6416305,
-120.3595624,
100
],
"235 Poplar St": [
50.6947894,
-120.3617077,
100
],
"2090 Pacific Way": [
50.6440256,
-120.3680606,
100
],
"720 Robson Dr": [
50.6457006,
-120.3531036,
100
],
"1642 Springhaven Plc": [
50.6593836,
-120.3586779,
100
],
"5990 Todd Rd": [
50.649153,
-120.1658656,
100
],
"8205 Dallas Dr": [
50.6553065,
-120.1074846,
100
],
"2990 Westsyde Rd": [
50.7593585,
-120.3492011,
100
],
"C - 1440 Hugh Allan Drive": [
50.6518568,
-120.3778652,
99
],
"700 Hugh Allan Dr": [
50.6462587,
-120.3571778,
100
],
"1585 Summit Dr": [
50.6567575,
-120.3392605,
100
],
"1711 Copperhead Dr": [
50.6536334,
-120.3980836,
100
],
"360 Chief Alex Thomas Way": [
50.6794698,
-120.2954146,
95
],
"645 Clearwater Ave": [
50.7078925,
-120.3581678,
100
],
"702 1801 Princeton Kamloops Hwy": [
50.6525583,
-120.3644764,
100
],
"2955 Westsyde Rd": [
50.7579597,
-120.3486237,
100
],
"2826 Bank Rd": [
50.754364,
-120.3477263,
100
],
"306 Puett Ranch Rd": [
50.7975104,
-120.3162216,
100
],
"150 Wood St": [
50.6900587,
-120.3551284,
100
],
"3-1325 Aberdeen Dr": [
50.6375089,
-120.3762293,
100
],
"205 Columbia St": [
50.6711748,
-120.3376387,
100
],
"2049 Highland Pl": [
50.6617813,
-120.2624335,
100
]
}

SMALL = {'of', 'and', 'the', 'for', 'at', 'in', 'on', 'de', 'du', 'la'}
ACRONYM = {'ymca': 'YMCA', 'ywca': 'YWCA', 'bc': 'BC'}

def tidy(s):
    s = re.sub(r'\s+', ' ', s).strip(' -–—')
    out = []
    for i, t in enumerate(s.split(' ')):
        low = t.lower()
        if low in ACRONYM: out.append(ACRONYM[low])
        elif low in SMALL and i > 0: out.append(low)
        elif re.match(r'^\d+(st|nd|rd|th)$', low): out.append(low)
        elif low.startswith('mc') and len(low) > 2: out.append('Mc' + low[2].upper() + low[3:])
        else: out.append(t[:1].upper() + t[1:] if t[:1].islower() else t)
    return ' '.join(out)

# ---- existing records: for de-duplication and for the area of each new one
d = open(D, encoding='utf-8').read()
lines = d.split('\n')
existing = []
for line in lines:
    m = re.match(r'^(\s*(?:const P=\[)?)(\{.*\})(,|\];)?\s*$', line)
    if not m: continue
    try: o = json.loads(m.group(2))
    except Exception: continue
    if isinstance(o, dict) and 'lat' in o: existing.append(o)
if len(existing) < 300: sys.exit('only %d existing places parsed — aborting' % len(existing))
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())

rows = list(csv.reader(open(CSV, encoding='utf-8-sig')))
hdr, rows = rows[0], rows[1:]
I = {k: hdr.index(k) for k in ('NAME', 'ADDRESS_1', 'CITY', 'LATITUDE', 'LONGITUDE', 'PHONE', 'SERVICE_TYPE_CD')}
group = [r for r in rows if r[I['CITY']].strip().lower() == 'kamloops' and r[I['SERVICE_TYPE_CD']] == 'Licensed Group']
if not 80 <= len(group) <= 110: sys.exit('unexpected number of group facilities: %d' % len(group))

ids = set(re.findall(r'"id":"([0-9a-f]{8})"', d))
new, skipped, odd_area = [], [], []
for r in group:
    n, a = tidy(r[I['NAME']]), tidy(r[I['ADDRESS_1']])
    lat, lng = round(float(r[I['LATITUDE']]), 6), round(float(r[I['LONGITUDE']]), 6)
    phone = r[I['PHONE']].strip()
    approx = False
    g = GEO.get(re.sub(r'\s+', ' ', r[I['ADDRESS_1']]).strip())
    if g and g[2] >= 95 and math.hypot((g[0] - lat) * 111000, (g[1] - lng) * 70000) <= 150:
        lat, lng = round(g[0], 6), round(g[1], 6)      # the address's own point, not the shared one
    else:
        approx = True                                   # keep the province's point, say it is approximate
    if not (50.5 < lat < 50.9 and -120.7 < lng < -120.0): sys.exit('out of bounds: %s' % n)
    if not re.match(r'^\d{3}-\d{3}-\d{4}$', phone): sys.exit('odd phone for %s: %r' % (n, phone))
    if not phone.startswith(('250', '778', '236')): odd_area.append((n, phone))
    dupe = None
    for p in existing:
        dist = math.hypot((p['lat'] - lat) * 111000, (p['lng'] - lng) * 70000)
        na, nb = norm(p['n']), norm(n)
        if (na in nb or nb in na) and dist < 400: dupe = p['n']
        elif dist < 40 and p['c'] in ('daycare', 'commctr'): dupe = p['n']
        if dupe: break
    if dupe:
        skipped.append((n, dupe)); continue
    near = sorted(existing, key=lambda p: (p['lat'] - lat) ** 2 + (p['lng'] - lng) ** 2)[:5]
    area = max(set(p['g'] for p in near), key=lambda x: sum(1 for p in near if p['g'] == x))
    i = uuid.uuid4().hex[:8]
    while i in ids: i = uuid.uuid4().hex[:8]
    ids.add(i)
    o = {"n": n, "c": "daycare", "g": area, "lat": lat, "lng": lng, "a": a, "p": phone,
         "note": NOTE, "src": "opendata", "v": "2026-09", "t": ["family"], "id": i}
    if approx: o["precision"] = "low"
    assert json.loads(J(o)) == o
    new.append(J(o))

# The province licenses each program separately, so one centre can appear three
# times (River City holds units 30, 40 and 110 at 945 Columbia St W) and one
# operator runs several sites under near-identical names (seven Parasol
# locations). Same building = one place on the map; different buildings keep
# their own record, with the street in brackets so a reader can tell them apart
# — the way the pharmacies and the 7-Elevens already do.
def base_name(n):
    return re.sub(r'[\s\-–]*(?:\(\d+\)|\d+)$', '', n).strip(' -–')
def building(a):
    m = re.search(r'(\d{2,5})\s+(.*)$', re.sub(r'^\s*[\d]+\s*-\s*', '', a))   # drop a unit prefix
    return (m.group(1), re.sub(r'[^a-z]', '', m.group(2).lower())[:14]) if m else (a.lower(), '')
def street_of(a):
    m = re.search(r'\d{2,5}\s+(.*)$', re.sub(r'^\s*[\d]+\s*-\s*', '', a))
    return m.group(1).strip() if m else a.strip()

records = [json.loads(x) for x in new]
groups = {}
for o in records:
    groups.setdefault(norm(base_name(o['n'])), []).append(o)
merged = []
collapsed = []
for key, items in groups.items():
    by_building = {}
    for o in items:
        by_building.setdefault(building(o['a']), []).append(o)
    kept = []
    for bld, same in by_building.items():
        kept.append(same[0])
        for extra in same[1:]:
            collapsed.append((extra['n'], same[0]['n']))
    if len(kept) > 1:                       # same operator, different buildings
        streets = [street_of(o['a']) for o in kept]
        for o, st in zip(kept, streets):
            label = st if streets.count(st) == 1 else '%s %s' % (building(o['a'])[0], st)
            if norm(label) not in norm(o['n']):
                o['n'] = '%s (%s)' % (base_name(o['n']), label)
    merged.extend(kept)
new = [J(o) for o in merged]

if len(skipped) < 5: sys.exit('de-duplication found only %d overlaps — check the matcher' % len(skipped))
start = [k for k, l in enumerate(lines) if l.startswith('const P=[')]
nextconst = [k for k, l in enumerate(lines) if l.startswith('const QUARANTINE=')]
if len(start) != 1 or len(nextconst) != 1: sys.exit('could not locate the P array')
k = max(j for j in range(start[0], nextconst[0]) if lines[j].rstrip().endswith('}];'))
m = re.match(r'^(\s*)(\{.*\})\];\s*$', lines[k])
if not m: sys.exit('closing line is not a record: %r' % lines[k][:80])
lines[k] = m.group(1) + m.group(2) + ','
lines[k+1:k+1] = [m.group(1) + x + ',' for x in new[:-1]] + [m.group(1) + new[-1] + '];']
open(D, 'w', encoding='utf-8').write('\n'.join(lines))
print('p25 applied: +%d licensed group child care centres (%d already listed, skipped)' % (len(new), len(skipped)))
for a_, b_ in collapsed: print('   merged  %-46s into %s (same building, separate licence)' % (a_[:46], b_))
for n, why in skipped: print('   skipped %-46s (already on the map as %s)' % (n[:46], why))
for n, phone in odd_area: print('   note: %s lists a non-local area code (%s) — that is what the province has' % (n, phone))
