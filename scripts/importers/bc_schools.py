#!/usr/bin/env python3
"""K-12 schools for any BC city, from the Province's school dataset, with each school's
own website and phone from the district's site.

    python3 scripts/importers/bc_schools.py --city kelowna

Sources
- Name, street address, coordinates, public/independent, level, French programmes:
  "BC Schools - K-12 with Francophone Indicators", Province of BC (BC Data Catalogue,
  bc-schools-k-12-with-francophone-indicators), Open Government Licence – BC. Tier 1.
- Website: the district's school list (for SD23, www.sd23.bc.ca/schools), saved as
  cities/<city>/import/<district>-sites.json with its date. Phone: the school's own home page.
  Tier 2. Independent and francophone schools keep only what the province publishes.

Settings: cities/<city>/import/config.json "bc_schools":
    {"cities": ["Kelowna", "West Kelowna", "Westbank"], "district": "023", "districtShort": "SD23",
     "sites": "sd23-sites.json"}

Rules (Kamloops p21, 2026-09-24, generalised 2026-10-03):
- Standard schools only (no online-learning, continuing-education or alternate-programme rows).
- Elementary -> category `elem`; middle and secondary -> `school`.
- No hours are written: neither the province nor the school pages publish office hours.
- French programmes come from the province's own flags (early / late immersion, francophone).
- Phones are taken only from the school's own page, and only when exactly one local number
  appears in its header/footer; otherwise the record has no phone rather than a guess.
"""
import argparse, csv, io, json, os, re, sys, time, urllib.request, html as H
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CityImport, tidy
import bc_geocode

PKG = 'https://catalogue.data.gov.bc.ca/api/3/action/package_show?id=bc-schools-k-12-with-francophone-indicators'
L6 = ['zh', 'en', 'fr', 'es', 'ko', 'ja']
J = {'zh': '', 'ja': ''}

def T(**k): return k

def note(kind, sd, early, late):
    if kind == 'elem':
        base = T(zh='{sd} 学区公立小学。孩子上哪所学校由家庭住址决定，先在学区网站查学区划分（catchment）。',
                 en='{sd} public elementary school. Which school your child attends depends on your home address — check the district’s catchment map first.',
                 fr='École primaire publique du {sd}. L’école de votre enfant dépend de votre adresse — consultez d’abord la carte des secteurs du district.',
                 es='Escuela primaria pública del {sd}. La escuela de su hijo depende de su dirección: consulte primero el mapa de zonas del distrito.',
                 ko='{sd} 공립 초등학교. 어느 학교에 다니는지는 집 주소로 정해지니, 먼저 학군의 학구(catchment) 지도를 확인하세요.',
                 ja='{sd} の公立小学校。通う学校は住所で決まるので、まず学区の通学区域（catchment）を確認してください。')
    elif kind == 'middle':
        base = T(zh='{sd} 学区公立初中（middle school）。入学按家庭住址划分，先查学区划分。',
                 en='{sd} public middle school. Attendance is by home address — check the catchment map first.',
                 fr='École intermédiaire publique du {sd}. L’inscription dépend de l’adresse — consultez la carte des secteurs.',
                 es='Escuela intermedia pública del {sd}. La asignación depende de la dirección: consulte el mapa de zonas.',
                 ko='{sd} 공립 중학교(middle school). 집 주소에 따라 배정되니 학구 지도를 먼저 확인하세요.',
                 ja='{sd} の公立ミドルスクール。住所で通学区域が決まるので、まず学区地図を確認してください。')
    elif kind == 'secondary':
        base = T(zh='{sd} 学区公立高中。入学按家庭住址划分，先查学区划分。',
                 en='{sd} public secondary school. Attendance is by home address — check the catchment map first.',
                 fr='École secondaire publique du {sd}. L’inscription dépend de l’adresse — consultez la carte des secteurs.',
                 es='Escuela secundaria pública del {sd}. La asignación depende de la dirección: consulte el mapa de zonas.',
                 ko='{sd} 공립 고등학교. 집 주소에 따라 배정되니 학구 지도를 먼저 확인하세요.',
                 ja='{sd} の公立高校。住所で通学区域が決まるので、まず学区地図を確認してください。')
    elif kind == 'independent':
        base = T(zh='独立学校（私立），收学费，有自己的招生流程；直接联系学校。',
                 en='Independent (private) school — tuition fees and its own admissions; contact the school directly.',
                 fr='École indépendante (privée) — frais de scolarité et admission propre ; contactez l’école.',
                 es='Escuela independiente (privada): cobra matrícula y tiene su propio proceso de admisión; contacte a la escuela.',
                 ko='독립(사립)학교 — 수업료가 있고 자체 입학 절차가 있습니다. 학교에 직접 문의하세요.',
                 ja='独立（私立）学校。授業料がかかり、独自の入学手続きがあります。学校に直接問い合わせてください。')
    else:  # francophone
        base = T(zh='法语公立学校（CSF 第 93 学区），不属于 {sd}。入学资格有规定，先看学校网站或打电话问。',
                 en='French-language public school (Conseil scolaire francophone, district 93) — not part of {sd}. Eligibility rules apply: check the school’s site or call first.',
                 fr='École publique francophone (Conseil scolaire francophone, district 93) — ne fait pas partie du {sd}. Des critères d’admissibilité s’appliquent : consultez le site de l’école ou appelez.',
                 es='Escuela pública de lengua francesa (Conseil scolaire francophone, distrito 93); no pertenece al {sd}. Hay requisitos de admisión: consulte el sitio de la escuela o llame.',
                 ko='프랑스어 공립학교(CSF 93학군)로 {sd} 소속이 아닙니다. 입학 자격 요건이 있으니 학교 홈페이지를 보거나 먼저 전화하세요.',
                 ja='フランス語の公立学校（CSF 第93学区）。{sd} には属しません。入学資格の条件があるので、学校のサイトを見るか、まず電話で確認してください。')
    extra = {}
    if early:
        extra = T(zh='设有早期法语沉浸课程（French Immersion）。', en='Offers early French immersion.',
                  fr='Offre l’immersion française précoce.', es='Ofrece inmersión temprana en francés.',
                  ko='초기 프랑스어 몰입 과정 운영.', ja='早期フレンチ・イマージョンあり。')
    if late:
        late_t = T(zh='设有后期法语沉浸课程。', en='Offers late French immersion.', fr='Offre l’immersion française tardive.',
                   es='Ofrece inmersión tardía en francés.', ko='후기 프랑스어 몰입 과정 운영.', ja='後期フレンチ・イマージョンあり。')
        extra = {l: (extra.get(l, '') + (' ' if extra.get(l) and l not in J else '') + late_t[l]) for l in L6}
    return {l: base[l].format(sd=sd) + ((' ' if l not in J else '') + extra[l] if extra else '') for l in L6}

PHONE = re.compile(r'\(?(250|778|236)\)?[-. ]?(\d{3})[-. ](\d{4})')

def site_phone(url, cache):
    if url in cache: return cache[url]
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (lifeguide-data-import)'})
        with urllib.request.urlopen(req, timeout=25, context=bc_geocode.SSL_CTX) as r:
            t = r.read().decode('utf-8', 'ignore')
        t = H.unescape(re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S))
        flat = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t))
        # SD23 school pages print "P (250) 870-5112 F (250) 870-5012": take the one labelled P/Phone
        lab = {'%s-%s-%s' % m.groups()[1:] for m in re.finditer(
            r'\b(P|Ph|Phone|Tel|Telephone)\b\.?:?\s*\(?(250|778|236)\)?[-. ]?(\d{3})[-. ](\d{4})', flat)}
        nums = {'%s-%s-%s' % m.groups() for m in PHONE.finditer(flat)}
        cache[url] = lab.pop() if len(lab) == 1 else (nums.pop() if len(nums) == 1 else None)
    except Exception:
        cache[url] = None
    time.sleep(1)
    return cache[url]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--city', required=True); ap.add_argument('--csv')
    a = ap.parse_args()
    imp = CityImport(a.city, 'bc-k12-schools')
    imp.word_radius = 400      # school names are unique; a campus is big
    cfgall = json.load(open(os.path.join(imp.dir, 'import', 'config.json'), encoding='utf-8'))
    cfg = cfgall['bc_schools']
    cities = {c.lower() for c in cfg['cities']}
    imp.area_by_locality = {k.lower(): v for k, v in cfgall.get('bc_childcare', {}).get('localities', {}).items() if v}
    sites = json.load(open(os.path.join(imp.dir, 'import', cfg['sites']), encoding='utf-8'))['sites'] if cfg.get('sites') else {}
    norm_site = {re.sub(r'[^a-z]', '', re.sub(r'^(école|ecole)\s+', '', k.lower())): v for k, v in sites.items()}
    if a.csv:
        text = open(a.csv, encoding='utf-8-sig').read()
    else:
        with urllib.request.urlopen(PKG, timeout=60, context=bc_geocode.SSL_CTX) as r:
            url = [x['url'] for x in json.load(r)['result']['resources'] if x.get('format') == 'csv'][0]
        with urllib.request.urlopen(url, timeout=120, context=bc_geocode.SSL_CTX) as r:
            text = r.read().decode('utf-8-sig')
    rows = [r for r in csv.DictReader(io.StringIO(text))
            if r['PHYSICAL_ADDRESS_CITY'].strip().lower() in cities and r['FACILITY_TYPE'] == 'Standard School']
    phone_cache_path = os.path.join(imp.dir, 'import', 'school-phones-cache.json')
    try: pcache = json.load(open(phone_cache_path, encoding='utf-8'))
    except FileNotFoundError: pcache = {}
    sd = cfg['districtShort']
    overrides = []
    for r in rows:
        n = r['SCHOOL_NAME'].strip()
        level = r['SCHOOL_EDUCATION_LEVEL']
        # 2026-10-03: the provincial dataset itself mislabels some schools (Rutland Senior
        # Secondary, Okanagan Mission Secondary and Springvalley Middle were "Elementary").
        # A school's own name is the stronger signal; every override is reported so it can
        # be sent back to DataBC.
        named = 'Secondary' if re.search(r'\bsecondary\b|\bhigh school\b', n, re.I) else \
                'Middle School' if re.search(r'\bmiddle\b', n, re.I) else None
        if named and level != named and not (named == 'Secondary' and 'Secondary' in level):
            overrides.append('%s: dataset says %r, name says %r' % (n, level, named))
            level = named
        public = r['PUBLIC_OR_INDEPENDENT'] == 'Public School'
        franco = r['HAS_PROG_FRANCOPHONE'] == 'YES' or r['DISTRICT_NUMBER'] == '093'
        if franco:
            kind = 'franco'; n = n if n.lower().startswith('école') else 'École ' + n
        elif not public: kind = 'independent'
        elif level == 'Elementary': kind = 'elem'
        elif level == 'Middle School': kind = 'middle'
        else: kind = 'secondary'
        cat = 'elem' if level == 'Elementary' else 'school'
        addr, loc = r['STREET_ADDRESS'].strip(), r['PHYSICAL_ADDRESS_CITY'].strip()
        try: dlat, dlng = float(r['LATITUDE']), float(r['LONGITUDE'])
        except ValueError: dlat = dlng = None
        lat, lng, approx = imp.locate(addr, loc, dlat, dlng)
        if lat is None:
            imp.skipped.append((n, 'no usable coordinates')); continue
        rec = {'n': n, 'c': cat, 'lat': lat, 'lng': lng, 'a': addr,
               'note': note(kind, sd, r['HAS_EARLY_FRENCH_IMMERSION'] == 'YES', r['HAS_LATE_FRENCH_IMMERSION'] == 'YES'),
               't': ['family']}
        key = re.sub(r'[^a-z]', '', re.sub(r'^(école|ecole)\s+', '', n.lower()))
        w = norm_site.get(key) or next((v for k, v in norm_site.items() if key and (key in k or k in key)), None)
        if w and public and not franco:
            rec['w'] = w
            ph = site_phone(w, pcache)
            if ph: rec['p'] = ph
            rec['src'] = 'official'
        if approx: rec['precision'] = 'low'
        imp.add(rec, r['MINCODE'], loc)
    json.dump(pcache, open(phone_cache_path, 'w', encoding='utf-8'), indent=1, sort_keys=True)
    imp.save()
    for o in overrides:
        print('   level override (report to DataBC): ' + o)

if __name__ == '__main__':
    main()
