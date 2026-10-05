#!/usr/bin/env python3
"""Licensed GROUP child care for any BC city, from the Province's Child Care Map data.

    python3 scripts/importers/bc_childcare.py --city kelowna
    python3 scripts/importers/bc_childcare.py --city kamloops --enrich --localities KAMLOOPS
        # 2026-10-04: refresh records already on the map (imported before this script existed) from the current
        # data: website if missing, and the languages / ages / fee-reduction note. Never adds a record, never
        # changes an id (favourites and task ticks are stored by id, L-105); only touches records whose note is
        # still the plain generated one, so a hand-written note is never overwritten.

Source: "Child Care Map Data", Province of British Columbia (catalogue.data.gov.bc.ca,
dataset child-care-map-data), updated daily, Open Government Licence – British Columbia.
Tier 1 (government open data) → src:'opendata'.

Settings live in cities/<city>/import/config.json under "bc_childcare":
    {"localities": {"KELOWNA": null, "WEST KELOWNA": "wk", "WESTBANK": "wk"}}
(the value forces an area key for that locality; null = nearest hand-assigned records decide).

Rules carried over from Kamloops (p25, 2026-09-24) and extended for Kelowna (2026-10-03):
- Licensed GROUP facilities only. "Licensed family" providers run out of private homes; a
  home address does not go on a public map (methodology §5.3).
- Rows the Province flags IS_DUPLICATE are dropped; several licences in one building become one
  place; one operator in several buildings gets the street in brackets.
- NEW for Kelowna: the note says, in all six languages, which languages staff speak (the
  dataset's LANG_* flags), which ages the centre takes, and whether it is in the fee-reduction
  programme (CCFRI). For a newcomer parent those three facts decide whether to call at all.
- No hours and no website are invented: the dataset has a WEBSITE column, used only when it
  is an http(s) URL.
"""
import argparse, csv, io, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CityImport, tidy, norm
import bc_geocode

URL = ('https://catalogue.data.gov.bc.ca/dataset/4cc207cc-ff03-44f8-8c5f-415af5224646/resource/'
       '9a9f14e1-03ea-4a11-936a-6e77b15eeb39/download/childcare_locations.csv')
L6 = ['zh', 'en', 'fr', 'es', 'ko', 'ja']

BASE = {
 'zh': '持牌托儿机构（BC 省政府开放数据）。托儿位普遍紧张，去之前先打电话问有没有空位、收什么年龄段。',
 'en': 'Licensed child care (BC government open data). Spaces are scarce — call first to ask about openings and the ages they take.',
 'fr': 'Garderie autorisée (données ouvertes du gouvernement de la C.-B.). Les places sont rares — téléphonez d’abord pour demander s’il y a de la place et quels âges sont acceptés.',
 'es': 'Guardería con licencia (datos abiertos del gobierno de BC). Hay pocas plazas: llame antes para preguntar por vacantes y las edades que aceptan.',
 'ko': '허가받은 보육시설(BC주 정부 공개 데이터). 자리가 부족하니 먼저 전화해 빈자리와 받는 연령을 물어보세요.',
 'ja': '認可保育施設（BC州政府のオープンデータ）。空きが少ないので、まず電話で空き状況と受け入れ年齢を確認してください。'}
LANG_NAMES = {
 'LANG_MANDARIN_YN': {'zh': '普通话', 'en': 'Mandarin', 'fr': 'mandarin', 'es': 'mandarín', 'ko': '중국어(표준어)', 'ja': '北京語'},
 'LANG_CANTONESE_YN': {'zh': '粤语', 'en': 'Cantonese', 'fr': 'cantonais', 'es': 'cantonés', 'ko': '광둥어', 'ja': '広東語'},
 'LANG_PUNJABI_YN': {'zh': '旁遮普语', 'en': 'Punjabi', 'fr': 'pendjabi', 'es': 'panyabí', 'ko': '펀자브어', 'ja': 'パンジャーブ語'},
 'LANG_FRENCH_YN': {'zh': '法语', 'en': 'French', 'fr': 'français', 'es': 'francés', 'ko': '프랑스어', 'ja': 'フランス語'},
 'LANG_SPANISH_YN': {'zh': '西班牙语', 'en': 'Spanish', 'fr': 'espagnol', 'es': 'español', 'ko': '스페인어', 'ja': 'スペイン語'}}
LANG_LEAD = {'zh': '可用语言（除英语外）：', 'en': 'Languages besides English: ', 'fr': 'Langues en plus de l’anglais : ',
             'es': 'Idiomas además del inglés: ', 'ko': '영어 외 가능 언어: ', 'ja': '英語以外の対応言語：'}
SEP = {'zh': '、', 'en': ', ', 'fr': ', ', 'es': ', ', 'ko': ', ', 'ja': '、'}
END = {'zh': '。', 'en': '.', 'fr': '.', 'es': '.', 'ko': '.', 'ja': '。'}
AGES = {  # flag -> label
 'SRVC_UNDER36_YN': {'zh': '3 岁以下', 'en': 'under 3', 'fr': 'moins de 3 ans', 'es': 'menores de 3 años', 'ko': '3세 미만', 'ja': '3歳未満'},
 'SRVC_30MOS_5YRS_YN': {'zh': '2 岁半到 5 岁', 'en': '2½ to 5', 'fr': '2 ans et demi à 5 ans', 'es': 'de 2 años y medio a 5', 'ko': '2세 반~5세', 'ja': '2歳半〜5歳'},
 'SRVC_LICPRE_YN': {'zh': '学前班', 'en': 'preschool', 'fr': 'prématernelle', 'es': 'preescolar', 'ko': '유치원 전 과정', 'ja': 'プリスクール'},
 'SRVC_OOS_GR1_AGE12_YN': {'zh': '课后托管（1 年级到 12 岁）', 'en': 'before/after school (grade 1 to age 12)', 'fr': 'avant et après l’école (1re année à 12 ans)', 'es': 'antes y después de la escuela (de 1.º grado a 12 años)', 'ko': '방과 전후 돌봄(1학년~12세)', 'ja': '学童保育（1年生〜12歳）'}}
AGE_LEAD = {'zh': '年龄：', 'en': 'Ages: ', 'fr': 'Âges : ', 'es': 'Edades: ', 'ko': '연령: ', 'ja': '年齢：'}
CCFRI = {'zh': '参加省政府的托儿费减免计划（CCFRI）。', 'en': 'In the provincial fee-reduction programme (CCFRI).',
         'fr': 'Participe au programme provincial de réduction des frais (CCFRI).', 'es': 'Participa en el programa provincial de reducción de cuotas (CCFRI).',
         'ko': '주 정부 보육료 감면 프로그램(CCFRI) 참여.', 'ja': '州の保育料軽減プログラム（CCFRI）に参加。'}

def yes(v):
    return str(v).strip().upper() in ('Y', 'YES', 'TRUE', '1')

def note_for(r):
    out = {}
    for l in L6:
        parts = [BASE[l]]
        langs = [LANG_NAMES[k][l] for k in LANG_NAMES if yes(r.get(k))]
        if langs: parts.append(LANG_LEAD[l] + SEP[l].join(langs) + END[l])
        ages = [AGES[k][l] for k in AGES if yes(r.get(k))]
        if ages: parts.append(AGE_LEAD[l] + SEP[l].join(ages) + END[l])
        if yes(r.get('IS_CCFRI_AUTH')): parts.append(CCFRI[l])
        out[l] = (' ' if l not in ('zh', 'ja') else '').join(parts)
    return out

def base_name(n):
    return re.sub(r'[\s\-–]*(?:\(\d+\)|\d+)$', '', n).strip(' -–')

def building(a):
    m = re.search(r'(\d{1,6})\s+(.*)$', re.sub(r'^\s*[#\w]+\s*-\s*(?=\d)', '', a))
    return (m.group(1), norm(m.group(2))[:14]) if m else (a.lower(), '')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--city', required=True)
    ap.add_argument('--csv', help='use a downloaded copy instead of fetching')
    ap.add_argument('--enrich', action='store_true', help='update matching records already on the map; add nothing')
    ap.add_argument('--localities', help='comma-separated CSV CITY values (needed with --enrich when the city has no import/config.json)')
    a = ap.parse_args()
    if a.enrich:
        return enrich(a)
    imp = CityImport(a.city, 'bc-childcare-map')
    imp.name_suffix = 'child care'
    cfg = json.load(open(os.path.join(imp.dir, 'import', 'config.json'), encoding='utf-8'))['bc_childcare']
    locs = {k.upper(): v for k, v in cfg['localities'].items()}
    imp.area_by_locality = {k.lower(): v for k, v in locs.items() if v}
    if a.csv:
        text = open(a.csv, encoding='utf-8-sig').read()
    else:
        with urllib.request.urlopen(URL, timeout=120, context=bc_geocode.SSL_CTX) as r:
            text = r.read().decode('utf-8-sig')
    rows = [r for r in csv.DictReader(io.StringIO(text))
            if r['CITY'].strip().upper() in locs and r['SERVICE_TYPE_CD'] == 'Licensed Group'
            and not yes(r.get('IS_DUPLICATE'))]
    print('%d licensed group rows for %s' % (len(rows), ', '.join(locs)))
    # one place per building per operator
    seen = {}
    for r in rows:
        k = (norm(base_name(tidy(r['NAME']))), building(tidy(r['ADDRESS_1'])))
        seen.setdefault(k, r)
    rows = list(seen.values())
    by_op = {}
    for r in rows:
        by_op.setdefault(norm(base_name(tidy(r['NAME']))), []).append(r)
    for r in rows:
        n, addr, loc = base_name(tidy(r['NAME'])), tidy(r['ADDRESS_1']), r['CITY'].strip().title()
        if len(by_op[norm(n)]) > 1:
            street = re.sub(r'^\s*[#\w]+\s*-\s*(?=\d)', '', addr)
            n = '%s (%s)' % (n, street)
        try:
            dlat, dlng = float(r['LATITUDE']), float(r['LONGITUDE'])
        except ValueError:
            dlat = dlng = None
        lat, lng, approx = imp.locate(addr, loc, dlat, dlng)
        if lat is None:
            imp.skipped.append((n, 'no usable coordinates')); continue
        rec = {'n': n, 'c': 'daycare', 'lat': lat, 'lng': lng, 'a': addr, 'note': note_for(r), 't': ['family']}
        ph = re.sub(r'\D', '', r.get('PHONE', ''))
        if len(ph) == 10: rec['p'] = '%s-%s-%s' % (ph[:3], ph[3:6], ph[6:])
        w = (r.get('WEBSITE') or '').strip()
        if re.match(r'^https?://\S+\.\S+$', w): rec['w'] = w
        elif re.match(r'^www\.\S+\.\S+$', w): rec['w'] = 'https://' + w
        if approx: rec['precision'] = 'low'
        imp.add(rec, r['FAC_PARTY_ID'], loc)
    imp.save()

def _fetch(a):
    if a.csv:
        return open(a.csv, encoding='utf-8-sig').read()
    with urllib.request.urlopen(URL, timeout=120, context=bc_geocode.SSL_CTX) as r:
        return r.read().decode('utf-8-sig')

def enrich(a):
    import math
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import kamdata
    kamdata.use(a.city)
    locs = {x.strip().upper() for x in (a.localities or a.city).split(',')}
    rows = [r for r in csv.DictReader(io.StringIO(_fetch(a)))
            if r['CITY'].strip().upper() in locs and r['SERVICE_TYPE_CD'] == 'Licensed Group' and not yes(r.get('IS_DUPLICATE'))]
    P = kamdata.load('P')
    def dist(p, r):
        try: la, ln = float(r['LATITUDE']), float(r['LONGITUDE'])
        except ValueError: return 1e9
        return math.hypot((p['lat'] - la) * 111000, (p['lng'] - ln) * 111000 * math.cos(math.radians(la)))
    def digits(x): return re.sub(r'\D', '', x or '')[-10:]
    month = kamdata.month(a.city)
    stats = {'matched': 0, 'note': 0, 'web': 0, 'unmatched': []}
    for p in P:
        if p['c'] != 'daycare' or p.get('src') != 'opendata': continue
        cand = [r for r in rows if dist(p, r) < 250 and (
                (digits(p.get('p')) and digits(p.get('p')) == digits(r.get('PHONE'))) or
                norm(base_name(tidy(r['NAME']))) == norm(re.sub(r'\s*\(.*\)$', '', p['n'])))]
        if not cand:
            stats['unmatched'].append(p['n']); continue
        r = min(cand, key=lambda r: dist(p, r)); stats['matched'] += 1
        changed = False
        # the generated note, possibly followed by a city's own sentence (Kamloops adds the local Child Care
        # Resource & Referral line): put the languages / ages / CCFRI after the generated part, keep the rest
        if all((p['note'].get(l) or '').startswith(BASE[l]) for l in L6):
            gen = note_for(r)
            new = {l: gen[l] + p['note'][l][len(BASE[l]):] for l in L6}
            if any(gen[l] != BASE[l] for l in L6) and not any(LANG_LEAD[l] in p['note'][l] or AGE_LEAD[l] in p['note'][l] for l in L6):
                p['note'] = new; stats['note'] += 1; changed = True
        w = (r.get('WEBSITE') or '').strip()
        w = w if re.match(r'^https?://\S+\.\S+$', w) else ('https://' + w if re.match(r'^www\.\S+\.\S+$', w) else '')
        if w and not p.get('w'): p['w'] = w; stats['web'] += 1; changed = True
        if changed: p['v'] = month          # re-checked against today's provincial data
    kamdata.save('P', P)
    print('%s: %d licensed group rows; %d of our records matched; %d notes now give languages/ages/CCFRI; %d websites added'
          % (a.city, len(rows), stats['matched'], stats['note'], stats['web']))
    if stats['unmatched']:
        print('not matched (left as they are — closed, renamed or moved? check by phone): %d' % len(stats['unmatched']))
        for n in stats['unmatched']: print('   ', n)

if __name__ == '__main__':
    main()
