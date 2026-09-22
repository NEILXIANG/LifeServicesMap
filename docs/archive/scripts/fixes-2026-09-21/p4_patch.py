#!/usr/bin/env python3
"""Phase 4 — systemic cleanup from the 2026-09-21 full check.
  * ⭐ out of names (an editor's pick is a field, not part of the name)
  * City park hours: Parks Bylaw 35-104, 05:00–23:00
  * water parks: the season ends on a City notice, not a calendar month
  * chain homepages → the location's own page (URLs the check opened)
  * banks: the late closings that were flagged but never stored
  * the smaller facts the check confirmed on an operator or City page"""
import sys, json, re
sys.path.insert(0, '.')
import kamdata

P = kamdata.load('P')
by = {p['id']: p for p in P}
V = '2026-09'
L6 = ('zh', 'en', 'fr', 'es', 'ko', 'ja')
touched = set()
def rec(i): assert i in by, i; touched.add(i); return by[i]
def note(i, **kw):
    assert set(kw) == set(L6), i
    rec(i)['note'] = {l: kw[l] for l in L6}

# ---------------------------------------------------------------- ⭐ in names
for p in P:
    m = re.match(r'^([⭐\s]+)', p['n'])
    if m:
        stars = m.group(1).count('⭐')
        p['n'] = p['n'][m.end():]
        p['pick'] = stars          # not a check of the record, so v is left alone

# ---------------------------------------------------------------- City park hours
NOT_CITY = {'dd440908', '600d0f4c', '5308dd0d', '7e4469ca'}   # private park, provincial park, informal access, unclear owner
parks = []
for p in P:
    if p['c'] in ('park', 'dogpark', 'trail', 'beach') and p['id'] not in NOT_CITY:
        city = (p.get('p') or '').startswith('250-828-') or p.get('pq') == 'pCity' or 'kamloops.ca/' in (p.get('w') or '')
        if city:
            p['h'] = {'r': [[1, 7, 300, 1380, 0]]}
            parks.append(p['id']); touched.add(p['id'])
for i in ('600d0f4c', '5308dd0d'):          # no phone left, so no phone qualifier either
    by[i].pop('pq', None)
for i in ('ce9ce292', '7e4469ca'):          # the switchboard, labelled as such like the rest
    rec(i)['pq'] = 'pCity'

# ---------------------------------------------------------------- water parks
# kamloops.ca/recreation-culture/parks-sports-fields/water-parks: all closed for
# the season on 15 Sep 2026. A month-based season kept them "open" till October.
for i in ('dd819a8a', '8839dee9', '61d1c228', '35a610c9'):
    p = rec(i)
    p['h']['q'] = 'qSeasonSite'
    p['w'] = p.get('w') or 'https://www.kamloops.ca/recreation-culture/parks-sports-fields/water-parks'
rec('dd819a8a')['h']['r'] = [[1, 7, 600, 1260, 0]]      # 10–9 on the City page

# ---------------------------------------------------------------- location pages
LINKS = {
 '51c509c6': 'https://branches.bmo.com/bc/kamloops/b0720/', 'e7ae063e': 'https://branches.bmo.com/bc/kamloops/b0806/',
 'd0715e84': 'https://branches.bmo.com/bc/kamloops/abm0720-1/',
 '21d9050d': 'https://locations.cibc.com/bc/kamloops/07050', 'd31dbd56': 'https://locations.cibc.com/bc/kamloops/07150',
 '61f2ca0d': 'https://locations.cibc.com/bc/kamloops/02950', '13af4289': 'https://locations.cibc.com/bc/kamloops/00050',
 '43418df3': 'https://maps.rbcroyalbank.com/BC-KAMLOOPS-branch-3520', '34c74ae9': 'https://maps.rbcroyalbank.com/BC-KAMLOOPS-branch-2360',
 '3644cc5b': 'https://maps.rbcroyalbank.com/BC-KAMLOOPS-branch-2320',
 '1b1b6bf2': 'https://locator.scotiabank.com/branch/81620', 'e7514fcc': 'https://locator.scotiabank.com/branch/10140',
 '9e0a9b54': 'https://citycentreautoservice.com/',
 '935659ad': 'https://www.costco.ca/w/-/bc/kamloops/161',
 '0624bb6f': 'https://find.shell.com/ca/fuel/13054771-848-8th-st', 'da6014c5': 'https://find.shell.com/ca/fuel/10052959',
 'd2b51035': 'https://find.shell.com/ca/fuel/10053468-transcanada-hwy-e-comazetto',
 '18523a8a': 'https://www.esso.ca/en-ca/find-station/esso-kamloops-bc-esso-200303929',
 '814cc8b6': 'https://www.freshco.com/stores/freshco-columbia-summit', '9a37f240': 'https://www.freshco.com/stores/freshco-valleyview-east-kamloops',
 '90fb1610': 'https://www.realcanadiansuperstore.ca/en/store-locator/details/1522', 'aa911974': 'https://www.safeway.ca/stores/safeway-fortune',
 '3fe222fe': 'https://www.yourindependentgrocer.ca/en/store-locator/details/5488', 'bdb6ff9c': 'https://www.walmart.ca/en/store/3040',
 '29917426': 'https://www.saveonfoods.com/store-information/lansdowne/2211',
 '0cb7122b': 'https://www.anytimefitness.com/en-ca/locations/kamloops-british-columbia-3807',
 '099ea2fb': 'https://www.goldsgym.com/locations/bc/kamloops/',
 '0a856b7a': 'https://www.canadiantire.ca/en/store-details/bc/kamloops-south-bc-355.html',
 'deffcefb': 'https://stores.homedepot.ca/bc/kamloops/home-improvement-kamloops-bc-7144.html',
 '6c036ec5': 'https://www.homehardware.ca/en/store/55461', '5bbda2fd': 'https://www.rona.ca/en/store/british-columbia/kamloops/rona-kamloops-61310',
 '61154281': 'https://www.planetfitness.ca/gyms/kamloops-bc',
 '6cf9171d': 'https://rcmp.ca/en/bc/kamloops', '50c8f348': 'https://offices.service.canada.ca/en/Office/5986',
 'a014ca8f': 'https://kafs.ca/programs-services/mini-storage-units/', '4e467f97': 'https://www.kelsongroup.com/residential/cities/kamloops',
 '070b0c64': 'https://www.bctransit.com/kamloops/contact',
 # empty `w` although the operator has a site (the check opened each one)
 'b29c9af7': 'https://www.interiorhealth.ca/locations/kamloops-north-shore-urgent-and-primary-care-centre-upcc',
 '78386973': 'https://www.interiorhealth.ca/locations/kamloops-south-shore-urgent-primary-care-learning-centre',
 '7f3150f8': 'https://www.interiorhealth.ca/locations/kamloops-primary-care-clinic',
 '172f9aae': 'https://www.riversidedentalclinic.ca/', '9b1e48e3': 'https://www.kamloopsdentalcentre.ca/', 'de3a3b49': 'https://rivieradentalclinic.com/',
 '316d05b2': 'https://totemfitness.ca/', 'b0a1cfe8': 'https://eastuffgrocery.com/', '4b2bef1d': 'https://nolimitsfitness.ca/',
 '0976dd56': 'https://thelaundryguys.ca/', 'ef414ca5': 'https://thelaundryguys.ca/', '3a28ab47': 'https://thompsoncleaners.ca/',
 'c8eaba85': 'https://sundenmanagement.com/', 'f98091ac': 'https://kbtemple.ca/kamloops/',
 '472010d4': 'https://himalayankitchenandbar.com/', '8457405d': 'https://mittzkitchen.com/', '92f6d936': 'https://moxies.ca/restaurants/kamloops/',
 'dba1a245': 'https://swpublichouse.ca/', '96f6a732': 'https://chookeatery.ca/', '4757f870': 'https://wasabimodernkitchen.com/',
 'ea43f8fb': 'https://yewstreetfoodhall.com/', '564ef9cb': 'https://consignorsports.com/', 'd30d0e25': 'https://flutterbuysthriftstore.com/',
 '029a48b5': 'https://shopstation10.com/', 'd860b505': 'https://valuefurnitures.ca/', '08c3204e': 'https://kamloopsveterinaryclinic.com/',
 '0dbc2ac6': 'https://hastymartesso.com/', '7e5b1086': 'https://cleancutzbarbershop.com/', '4304512a': 'https://sahalicentremall.com/',
 '88a72602': 'https://www.kamloops.ca/recreation-culture/facilities/valleyview-arena',
 'bf216456': 'https://www.kamloops.ca/recreation-culture/parks-sports-fields/dallas-barnhartvale-nature-park',
 '87f4ff34': 'https://www.kamloops.ca/recreation-culture/parks-sports-fields/peterson-creek-nature-park',
 '6d8ff33f': 'https://www.kamloops.ca/recreation-culture/parks-sports-fields/batchelor-nature-park',
 '76537f5f': 'https://www.kamloops.ca/recreation-culture/parks-sports-fields/valleyview-nature-park',
 '752036cd': 'https://www.kamloops.ca/recreation-culture/parks-sports-fields/westsyde-centennial-park',
 '9ce4c55a': 'https://www.kamloops.ca/recreation-culture/parks-sports-fields/prince-charles-park',
 '8b5beceb': 'https://www.kamloops.ca/recreation-culture/parks-sports-fields/river-street-dog-park',
 '3ee66c48': 'https://www.kamloops.ca/recreation-culture/parks-sports-fields/ord-road-dog-park',
}
for i, u in LINKS.items():
    p = rec(i)
    p['w'] = u
    if p.get('src') == 'places': p['src'] = 'official'

# ---------------------------------------------------------------- hours the check confirmed
H = {
 '51c509c6': [[1, 3, 540, 1020, 0], [4, 5, 540, 1080, 0], [6, 6, 540, 960, 0]],      # BMO Columbia: Thu–Fri to 6
 '34c74ae9': [[1, 2, 570, 1020, 0], [3, 5, 570, 1080, 0], [6, 6, 540, 960, 0]],      # RBC Summit: Wed–Fri to 6
 '1b1b6bf2': [[1, 3, 570, 1020, 0], [4, 5, 570, 1080, 0], [6, 6, 570, 960, 0]],      # Scotiabank Sahali: Thu–Fri to 6
 'e7514fcc': [[1, 5, 570, 1020, 0]],                                                 # Scotiabank Victoria: to 5
 '3baa3f69': [[1, 3, 540, 1050, 0], [4, 5, 540, 1080, 0], [6, 6, 540, 960, 0]],      # TD North Shore
 '8d4da008': [[1, 5, 330, 1260, 0], [6, 7, 420, 1140, 0]],                           # ymcabc.ca
 '0dbc2ac6': [[1, 5, 360, 1320, 0], [6, 7, 420, 1320, 0]],                           # hastymartesso.com
 'ea43f8fb': [[1, 6, 660, 1260, 0], [7, 7, 660, 1200, 0]],                           # yewstreetfoodhall.com
 '564ef9cb': [[1, 5, 570, 1050, 0], [6, 6, 570, 1020, 0]],                           # consignorsports.com/contact
 '775d4cc1': [[1, 5, 540, 930, 0]],                                                  # secwepemcmuseum.ca/visit-overview
 '0624bb6f': [[1, 6, 360, 1320, 0], [7, 7, 420, 1320, 0]],                           # find.shell.com
}
for i, r in H.items():
    rec(i)['h'] = {'r': r}
rec('ce9ce292')['h'] = {'r': [[1, 4, 600, 1260, 1], [5, 6, 600, 1320, 1], [7, 7, 600, 1260, 1]], 'se': 'winter'}   # City page: Fri–Sat to 10
rec('0e24eb77')['h'] = {'k': 'hSite'}                                  # showtimes, not opening hours
rec('718a712f').update(p='250-828-9700', h={'r': [[1, 5, 480, 960, 0]], 'q': 'qOffice'})   # tkemlups.ca/contact
rec('1b1b6bf2')['n'] = 'Scotiabank (Sahali)'

# ---------------------------------------------------------------- notes the check found wrong
note('f449c4d5',
  zh='沙滩，有洗手间，可带宠物，比 Riverside 安静。这里禁止游泳。',
  en='Sandy beach with washrooms; pet friendly and quieter than Riverside. Swimming is not allowed here.',
  fr='Plage de sable avec toilettes ; animaux acceptés, plus calme que Riverside. La baignade y est interdite.',
  es='Playa de arena con baños; se admiten mascotas y es más tranquila que Riverside. Aquí no se permite nadar.',
  ko='화장실이 있는 모래 해변으로, 반려동물 동반 가능하고 Riverside보다 조용합니다. 이곳은 수영 금지입니다.',
  ja='トイレのある砂浜。ペット可で、Riversideより静か。ここは遊泳禁止です。')
note('050b5d80',
  zh='市中心河滩：夏天可以游泳，7 月起公园里有音乐会。Scoopz 冰淇淋在街对面。位于 Riverside Park 内。',
  en='Downtown river beach: summer swimming, and concerts in the park from July. Scoopz ice cream is across the street. Inside Riverside Park.',
  fr='Plage de rivière au centre-ville : baignade l’été et concerts dans le parc à partir de juillet. Le glacier Scoopz est de l’autre côté de la rue. Dans le parc Riverside.',
  es='Playa de río en el centro: baño en verano y conciertos en el parque desde julio. La heladería Scoopz está al otro lado de la calle. Dentro de Riverside Park.',
  ko='시내 강변 해변: 여름 수영, 7월부터 공원 음악회. Scoopz 아이스크림은 길 건너편에 있습니다. Riverside Park 안.',
  ja='ダウンタウンの川辺のビーチ：夏は泳げて、7月から公園でコンサート。Scoopzのアイスは通りの向かい。Riverside Park内。')
note('ce9ce292',
  zh='免费户外滑冰环道，有灯光；可租冰鞋（少量费用）。',
  en='Free outdoor skating loop with lights; skate rental available (small fee).',
  fr='Anneau de patinage extérieur gratuit, éclairé ; location de patins (petits frais).',
  es='Circuito de patinaje al aire libre gratuito, con iluminación; alquiler de patines (tarifa pequeña).',
  ko='조명이 있는 무료 야외 스케이트 순환로. 스케이트 대여 가능(소액).',
  ja='照明のある無料の屋外スケートループ。スケート靴のレンタルあり（少額）。')
rec('ce9ce292')['pick'] = 1                                            # its ⭐ lived in the note
note('61f2ca0d',
  zh='客户咨询中心：只有 ATM 取现和咨询，没有柜台服务。',
  en='A client advice centre: cash from the ATM only, no teller service.',
  fr='Centre de conseil : retrait au guichet automatique seulement, pas de service au comptoir.',
  es='Centro de asesoría: solo efectivo en el cajero automático, sin servicio de ventanilla.',
  ko='고객 상담 센터: ATM 현금 인출만 가능하고 창구 업무는 없습니다.',
  ja='相談センター：ATMでの現金引き出しのみで、窓口業務はありません。')
note('e7514fcc',
  zh='有面向新来居民的 StartRight 项目（开户优惠）。',
  en='Offers StartRight, Scotiabank’s banking package for newcomers.',
  fr='Offre StartRight, le forfait bancaire de la Banque Scotia pour les nouveaux arrivants.',
  es='Ofrece StartRight, el paquete bancario de Scotiabank para recién llegados.',
  ko='신규 이민자를 위한 Scotiabank 금융 패키지 StartRight를 제공합니다.',
  ja='新しく来た人向けのScotiabankの口座パッケージ StartRight があります。')
# BC Transit route pages: TRU is 4/5/7/9/10/16; Lansdowne is 1/2/3/6/7/9/17/18
for i, old, new in (('4ff9ad95', '4/5/7/10', '4/5/7/9/10/16'), ('2c8f9d3b', '1/2/3/6/7/9/16/17/18', '1/2/3/6/7/9/17/18')):
    p = rec(i)
    for l in L6:
        assert p['note'][l].count(old) == 1, (i, l)
        p['note'][l] = p['note'][l].replace(old, new).replace('⭐', '').strip()

for i in touched:
    by[i]['v'] = V
kamdata.save('P', P)
print('phase 4: %d records touched; %d City parks on bylaw hours; %d links' % (len(touched), len(parks), len(LINKS)))

# the popup's "editor's pick" tag reads the new field
_E = 'src/engine.html'
_s = open(_E, encoding='utf-8').read()
_o = "const pick=/^⭐/.test(p.n), nm=p.n.replace(/^[⭐\\s]+/,'');"
assert _s.count(_o) == 1
_s = _s.replace(_o, "const pick=!!p.pick||/^⭐/.test(p.n), nm=p.n.replace(/^[⭐\\s]+/,'');")
open(_E, 'w', encoding='utf-8').write(_s)

# the same site, now that both rows carry the operator's page: say so, both ways
P = kamdata.load('P'); by = {p['id']: p for p in P}
for a, b in (('dd819a8a', 'f4c1c1d7'), ('78386973', '1e3e329a')):
    for x, y in ((a, b), (b, a)):
        sc = by[x].setdefault('sameComplex', [])
        if y not in sc: sc.append(y)
kamdata.save('P', P)
