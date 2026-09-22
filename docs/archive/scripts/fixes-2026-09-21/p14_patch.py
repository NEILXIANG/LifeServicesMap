#!/usr/bin/env python3
"""2026-09-22 — the maintainer's rule: a phone number that cannot be confirmed on
an official source is not shown. Every place phone was checked on 2026-09-22 against
the organisation's own site, then (where that failed) against another official
source: City of Kamloops Contact Database / facility pages, BC Transit's Kamloops
contact page, HealthLink BC's clinic and pharmacy directory, canada.ca, icbc.com,
Canada Post's customer guide, bc211, and the chains' own store pages.

Removed (no official source found, or the number belongs to another office):
- City lines that are not the park's: 250-828-3461 is Capital Projects, 250-828-3335
  is Arena Booking, 250-828-3551 is the McDonald Park spray-park line, 250-828-3500
  is the Tournament Capital Centre — dropped from the parks, dog parks and beach that
  borrowed them (the City main line 250-828-3311, which is in the directory, stays).
- Store phones the brand's site does not publish or would not show: Superstore,
  Independent Grocer, London Drugs, Beem Valleyview, four TD branches, two local
  Canada Post counters, four Petro-Canada and four Chevron / On The Run stations.
- Sites that refuse to load or list no phone: The Chook Eatery, Himalayan Kitchen,
  The View Apartments, Kamloops United Church, Yellow Cabs (web booker only).
- Places with no official site at all (the number came from a map listing).
- The Mustard Seed winter shelter line (bc211's Yacht Club listing is now empty):
  the place note and the "money runs out" card point to 2-1-1 instead.

Also, now that their own store pages were found and read (address and phone match),
three Shoppers Drug Mart, three 7-Eleven and two Esso links go to the store page
instead of the brand homepage."""
import sys, json, re
sys.path.insert(0, '.')
import kamdata
D = 'src/data-kamloops.js'
d = open(D, encoding='utf-8').read()
J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)
P0 = {p['id']: p for p in kamdata.load('P')}
byname = {}
for p in P0.values(): byname.setdefault(p['n'], []).append(p['id'])
def pid(n):
    assert len(byname.get(n, [])) == 1, n
    return byname[n][0]

def edit_place(i, fn):
    global d
    lines = d.split('\n')
    hit = [k for k, l in enumerate(lines) if ('"id":"%s"' % i) in l]
    assert len(hit) == 1, (i, len(hit))
    mm = re.match(r'^(\s*(?:const P=\[)?)(\{.*\})(,|\];)?\s*$', lines[hit[0]])
    o = json.loads(mm.group(2)); assert J(o) == mm.group(2), i
    fn(o)
    lines[hit[0]] = mm.group(1) + J(o) + (mm.group(3) or '')
    d = '\n'.join(lines)

REMOVE = {  # name: phone on file (asserted)
 'Prince Charles Park': '250-828-3551', 'Riverside Park': '250-828-3551', 'McDonald Park': '250-828-3551',
 'Brocklehurst Park': '250-828-3551', 'McArthur Island Park': '250-828-3461', 'Albert McGowan Park': '250-828-3461',
 'Valleyview Nature Park': '250-828-3461', 'River Street Dog Park': '250-828-3335', 'Juniper Dog Park': '250-828-3335',
 'Riverside Park Beach': '250-828-3500',
 'Real Canadian Superstore': '250-371-6418', "Sarah's Your Independent Grocer": '250-312-3323',
 'London Drugs (Lansdowne Village)': '250-372-0028', 'Beem Credit Union (Valleyview)': '250-374-9151',
 'TD Bank (Notre Dame Dr)': '250-314-3000', 'TD Bank (Aberdeen)': '250-314-5077', 'TD Bank (North Shore)': '250-376-7774',
 'TD Canada Trust (Victoria St)': '250-314-5035', 'Canada Post (North Shore)': '250-554-2398',
 'Canada Post (Brocklehurst)': '250-376-5611',
 'Petro-Canada (Sydney Ave)': '250-376-1131', 'Petro-Canada (Powwow Trail)': '250-377-8684',
 'Petro-Canada Truck Stop': '250-374-6263', 'Petro-Canada (10th Ave)': '250-372-1734',
 'Chevron (8th St)': '250-376-4111', 'On The Run (Chevron)': '250-376-4111', 'Chevron (Frontage Rd)': '250-374-1338',
 'Chevron (Westsyde)': '250-579-5885',
 'The Chook Eatery': '250-372-8514', 'Himalayan Kitchen & Bar': '236-425-3568', 'The View Apartments': '250-572-4043',
 'Kamloops United Church': '250-372-3020', 'Yellow Cabs Kamloops': '250-374-3333',
 'Cheng Kwong 長江超市': '250-554-2272', 'Day to Day Grocery': '250-205-0257', "D'Cruz Filipino Mart": '250-682-5196',
 'Victoria Oriental': '250-377-6886', 'Oriental Express': '778-470-2060', 'Columbia Place': '250-372-5878',
 'Tranquille Market': '236-421-1949', 'North Shore Community Centre': '250-376-4777',
 'Canco Gas + One Stop': '250-376-1710', 'Co-op Valleyview Gas Bar': '250-372-8911',
 'Sagebrush Manor Apartments': '250-299-2057', 'The Success Formula Tutoring': '778-921-0098',
 'Church of Jesus Christ of Latter-day Saints (Kamloops)': '250-600-3032',
 'The Mustard Seed Winter Shelter': '250-571-0469',
}
for n, ph in REMOVE.items():
    def f(o, ph=ph, n=n):
        assert o.get('p') == ph, (n, o.get('p'))
        del o['p']
        if n == 'The Mustard Seed Winter Shelter':
            for l in ('en', 'fr', 'es', 'zh', 'ko', 'ja'):
                assert o['note'][l].count('250-571-0469') == 1, l
                o['note'][l] = o['note'][l].replace('250-571-0469', '2-1-1')
    edit_place(pid(n), f)

STORE = {  # name: (old w, verified store page)
 'Shoppers Drug Mart (Summit)': ('https://www.shoppersdrugmart.ca', 'https://www.shoppersdrugmart.ca/en/stores/277-shoppers-drug-mart-columbia-place/'),
 'Shoppers Drug Mart (Tranquille)': ('https://www.shoppersdrugmart.ca', 'https://www.shoppersdrugmart.ca/en/stores/286-shoppers-drug-mart-north-hills-shopping-centre/'),
 'Shoppers Drug Mart (Valleyview)': ('https://www.shoppersdrugmart.ca', 'https://www.shoppersdrugmart.ca/en/stores/261-shoppers-drug-mart-valleyview-square-s-c/'),
 '7-Eleven (8th St)': ('https://www.7-eleven.ca', 'https://www.7-eleven.ca/locations/bc/kamloops/964-8th-street-27024'),
 '7-Eleven (Tranquille Rd)': ('https://www.7-eleven.ca', 'https://www.7-eleven.ca/locations/bc/kamloops/1790-tranquille-rd-29991'),
 '7-Eleven (Rogers Way)': ('https://www.7-eleven.ca', 'https://www.7-eleven.ca/locations/bc/kamloops/1120-rogers-way-37774'),
 'Esso (Columbia St)': ('https://www.esso.ca', 'https://www.esso.ca/en-ca/find-station/kamloops-bc-esso-200302440'),
 'Esso (8th St)': ('https://www.esso.ca', 'https://www.esso.ca/en-ca/find-station/kamloops-bc-esso-200327266'),
}
for n, (old, new) in STORE.items():
    def g(o, old=old, new=new, n=n):
        assert o.get('w') == old, (n, o.get('w'))
        o['w'] = new
    edit_place(pid(n), g)
open(D, 'w', encoding='utf-8').write(d)

# the winter-shelter sentence on the "money runs out" card
T = kamdata.load('TASKS')
t = [x for x in T if x['id'] == 'hardship'][0]
CUT = {'en': ' — 250-571-0469.', 'fr': ' — 250-571-0469.', 'ko': ' — 250-571-0469.', 'ja': ' — 250-571-0469。',
       'es': ': 250-571-0469.', 'zh': '——250-571-0469。'}
END = {'en': '.', 'fr': '.', 'ko': '.', 'ja': '。', 'es': '.', 'zh': '。'}
for l, a in CUT.items():
    assert t['note'][l].count(a) == 1, (l, a)
    t['note'][l] = t['note'][l].replace(a, END[l])
kamdata.save('TASKS', T)

# ---------------------------------------------------------------- self-check
P1 = {p['id']: p for p in kamdata.load('P')}
assert set(P1) == set(P0)
changed = {i for i in P0 if P0[i] != P1[i]}
expect = {pid(n) for n in REMOVE} | {pid(n) for n in STORE}
assert changed == expect, changed ^ expect
for i in changed:
    diff = {k for k in set(P0[i]) | set(P1[i]) if P0[i].get(k) != P1[i].get(k)}
    assert diff <= {'p', 'w', 'note'}, (i, diff)
blob = open(D, encoding='utf-8').read() + open('src/engine.html', encoding='utf-8').read()
assert '571-0469' not in blob
print('p14 applied: %d phones removed, %d store links' % (len(REMOVE), len(STORE)))
