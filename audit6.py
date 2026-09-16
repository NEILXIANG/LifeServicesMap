#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit pass 6 (2026-09-10): the data layer, mechanically.

validate.py enforces invariants — things that must never be false. This pass
looks for things that are merely *suspicious*: gaps, outliers, drift, thinness.
It prints findings; it changes nothing.
"""
import re, json, math, collections, sys
d = open('src/data-kamloops.js', encoding='utf-8').read()
e = open('src/engine.html', encoding='utf-8').read()
P  = json.loads(re.search(r'const P=(\[.*?\]);', d, re.S).group(1))
RI = json.loads(re.search(r'const RI=(\{.*?\});', d, re.S).group(1))
CI = json.loads(re.search(r'const CI=(\{.*?\});\n', e, re.S).group(1))
TASKS = json.loads(re.search(r'const TASKS=(\[.*?\]);\n', d, re.S).group(1))  # moved to data-kamloops.js since this script was written
L = ['zh','en','fr','es','ko','ja']
F = []
def find(sev, area, msg): F.append((sev, area, msg))

# ---- 1. completeness ------------------------------------------------------
miss = collections.Counter()
for p in P:
    for k in ('p','w','h'):
        if not p.get(k): miss[k]+=1
    if not p.get('note'): miss['note']+=1
    elif isinstance(p['note'], dict):
        for l in L:
            if not p['note'].get(l): find('P0','data', "%r has no %s note" % (p['n'], l))
n=len(P)
find('info','data', "places=%d · no phone %d · no website %d · no hours %d · no note %d"
     % (n, miss['p'], miss['w'], miss['h'], miss['note']))
# categories where hours matter and are missing
for c in ('gov','hospital','legal','foodbank','support','library','pharmacy','bank'):
    rows=[p for p in P if p['c']==c and not p.get('h')]
    if rows: find('P1','data', "%d %s entries have no hours: %s" % (len(rows), c, ', '.join(p['n'] for p in rows)[:160]))

# ---- 2. hours sanity -------------------------------------------------------
for p in P:
    h=p.get('h')
    if not isinstance(h, dict): continue
    for r in h.get('r', []):
        d1,d2,o,c,ap = r
        if not (1<=d1<=7 and 1<=d2<=7 and d1<=d2): find('P1','data', "%r has a bad day range %s" % (p['n'], r))
        if o is not None and c is not None and c<=o and c!=0: find('P1','data', "%r closes before it opens: %s" % (p['n'], r))
        if o is not None and (o<0 or o>1440): find('P1','data', "%r opening minute out of range: %s" % (p['n'], r))

# ---- 3. coordinates: region outliers ---------------------------------------
cent={}
for g in RI:
    rows=[p for p in P if p['g']==g]
    if rows: cent[g]=(sum(p['lat'] for p in rows)/len(rows), sum(p['lng'] for p in rows)/len(rows))
for p in P:
    if p['g'] not in cent: continue
    la,lo=cent[p['g']]
    dist=math.hypot((p['lat']-la)*111000,(p['lng']-lo)*111000*0.635)
    lim = 6000 if p['g']=='ot' else 3200
    if dist>lim: find('P2','data', "%r is %.1f km from the centre of its area %s — mis-tagged?" % (p['n'], dist/1000, p['g']))
# river test: North Shore / Brocklehurst / Westsyde should be north of ~50.681 near downtown
for p in P:
    if p['g'] in ('ns','br') and p['lat']<50.679 and p['lng']>-120.40:
        find('P2','data', "%r is tagged %s but sits south of the river (%.4f)" % (p['n'], p['g'], p['lat']))
    if p['g'] in ('sk','sa') and p['lat']>50.6835 and p['lng']>-120.36:
        find('P2','data', "%r is tagged %s but sits north of the river (%.4f)" % (p['n'], p['g'], p['lat']))

# ---- 4. duplicates & near-duplicates ---------------------------------------
seen=collections.defaultdict(list)
for p in P: seen[re.sub(r'[^a-z]','',p['n'].lower())].append(p)
for k,v in seen.items():
    if len(v)>1: find('P1','data', "duplicate name: %s" % [x['n'] for x in v])
for i in range(n):
    for j in range(i+1,n):
        a,b=P[i],P[j]
        if a['c']==b['c'] and math.hypot((a['lat']-b['lat'])*111000,(a['lng']-b['lng'])*111000*0.635)<8 and a['n']!=b['n']:
            find('P2','data', "same category, same spot: %r / %r" % (a['n'], b['n']))

# ---- 5. staleness ----------------------------------------------------------
vs=collections.Counter(p.get('v','?') for p in P)
find('info','data', "verification stamps: %s" % dict(sorted(vs.items())))
old=[p['n'] for p in P if (p.get('v') or '0000')<'2026-06']
if old: find('P2','data', "%d entries verified before 2026-06: %s" % (len(old), ', '.join(old[:8])+('…' if len(old)>8 else '')))

# ---- 6. richness: thin categories, thin regions, alias coverage -------------
cc=collections.Counter(p['c'] for p in P)
thin=[c for c in CI if cc[c]<=1]
find('info','data', "categories with ≤1 entry: %s" % thin)
gc=collections.Counter(p['g'] for p in P)
find('info','data', "per area: %s" % dict(gc))
al=sum(1 for p in P if p.get('alias'))
find('info','data', "%d/%d places have search aliases; key services without one:" % (al,n))
for p in P:
    if p['c'] in ('gov','hospital','legal','foodbank','support','library','transit','bank','pharmacy') and not p.get('alias'):
        find('P2','data', "no alias: %r [%s]" % (p['n'], p['c']))

# ---- 7. copy: leaks across languages ---------------------------------------
lat=re.compile(r'[A-Za-z]{4,}')
for p in P:
    nt=p.get('note')
    if not isinstance(nt, dict): continue
    for l in ('zh','ko','ja'):
        t=nt.get(l,'')
        words=[w for w in lat.findall(t) if w not in ('Kamloops','TRU','ICBC','BC','MSP','SIN','RCMP','Tranquille','Victoria','Street','Road','Ave','Avenue','Umo','LINC','KUU','CVITP','Fortune','Lansdowne','Seymour','Columbia','Notre','Dame','Lorne','Poplar','Laburnum','Paul','Better','Home','Meals','Wheels','House','Harbour','Women','Mount','Rise','Renew','Lizzy','Closet','Interior','Pathways','Wellness','Emerald','Merit','Place','KAFS','Mini','Storage','Elizabeth','Fry','Society','Colombo','Lodge','Francophone','Association','Royal','Inland','Hospital','North','South','Shore','Blue','River','Vernon','Lombard','Yellowhead','Immigrant','Services','Sahali','Aberdeen','Valleyview','Brocklehurst','Westsyde','Downtown','Google','Places','Family','Justice','Centre','Community','Food','Bank','Legal','Clinic','Employment','Assistance','Salvation','Army','Mustard','Seed','West','End','Shelter','Auxiliary','Thrift','Shop','Hospice','Volunteer','Canadian','Mental','Health','Fourth','Cherry','Ord','Batchelor','Heights','Juniper','Ridge','Dallas','Pineview','Pacific','Way','Parkcrest','Gleneagles','Tournament','Capital','Canada','Games','Aquatic','Costco','Walmart','Safeway','Superstore','Save','Foods','FreshCo','Shoppers','Drug','Mart','Thompson','Rivers','University','Secwepemc','Secwépemc','Tk','emlúps','Freemasons','Cultural','Museum','Archives','Gallery','Library','Wildlife','Park','Sandman','Riverside','McArthur','Island','Kenna','Cartwright','Peterson','Creek','Cinnamon','Ridge','Kinsmen','Overlanders','Moose','McDonald','Prince','Charles','Dominion','Albert','McGowan','Hills','Sherbrooke','Centennial','Hall','Convenience','Gas','Secondary','Elementary','School','Japanese','Chinese','Sikh','Punjabi','Italian','French','Immersion','Fraser','AP','IB','MYP','DP','Rent','Courtwork','Duty','Counsel','LawLINE','Dial','Law','Access','Pro','Bono','myselfserve','gov','bc','ca','ASK','STREETS','SHOP','Housing','First','Starfish','Backpacks','Baby','Youth','Necessity','Nook','BGC','John','Tod','Wood','Gleaning','Abundance','Policy','Council','Okanagan','Rents','Sun','Peaks','Kamloops','DayPASS','Tap','Pay','Uber','Kami','Cabs','Yellow','Taxi')]
        if len(words)>=6:
            find('P2','copy', "%s note for %r carries %d Latin words — untranslated fragment? %s" % (l, p['n'], len(words), ' '.join(words[:6])))

# ---- 8. tasks: every task's place exists; every task has 6 langs ------------
ids={p['id'] for p in P}
for t in TASKS:
    if t.get('place') and t['place'] not in ids: find('P0','guide', "task %s points at missing place %s" % (t['id'], t['place']))
    for k in ('q','t','why'):
        for l in L:
            if not t[k].get(l): find('P0','guide', "task %s.%s lacks %s" % (t['id'],k,l))
    for i,st in enumerate(t['steps']):
        for l in L:
            if not st.get(l): find('P0','guide', "task %s step %d lacks %s" % (t['id'],i,l))
find('info','guide', "tasks=%d (%s)" % (len(TASKS), ', '.join(t['id'] for t in TASKS)))
# tasks that could name a place but do not
for t in TASKS:
    if not t.get('place'): find('P2','guide', "task %s has no 'where do I go' place" % t['id'])

# ---- report ----------------------------------------------------------------
order={'P0':0,'P1':1,'P2':2,'info':3}
F.sort(key=lambda x:(order[x[0]],x[1]))
for sev,area,msg in F: print("  %-4s %-6s %s" % (sev,area,msg))
print("\n  %d findings: %s" % (len(F), dict(collections.Counter(f[0] for f in F))))
