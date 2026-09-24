#!/usr/bin/env python3
"""2026-09-24 — the 15 Kamloops elementary schools that were missing.

Newcomers ask about schools before almost anything else, and the map had 10 of
the city's 25 elementary schools. This adds the other 15: 14 SD73 public
elementary schools and the francophone École Collines-d'or (CSF / SD 93).

Every field is verified:
- name, street address and coordinates: the province's own K-12 school dataset
  (BC Data Catalogue, 2025/2026 school year, updated by DataBC);
- phone and website: each school's own page on sd73.bc.ca (collinesdor.csf.bc.ca
  for the francophone school), fetched one by one;
- area: assigned from the coordinates, checked against the neighbourhood the
  street actually sits in (Bert Edwards and Westmount are North Shore, not
  Brocklehurst; Rayleigh is its own community north of Westsyde, so it is
  "other", like Dallas and Barnhartvale).

Deliberately not written:
- opening hours. The province's dataset has none, and the school pages do not
  publish office hours, so these records say "hours unknown" rather than
  guessing. (The 10 schools already on the map carry Mon–Fri 8:30–15:30, which
  is not verified either — worth revisiting.)
- StrongStart. SD73 lists exactly four StrongStart centres in Kamloops — AE
  Perry, Arthur Hatton, Marion Schilling and Beattie — and all four are already
  on the map with that note. None of the new schools may claim it.
"""
import json, re, sys, uuid

D = 'src/data-kamloops.js'
J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)

NOTE = {   # identical wording to the elementary schools already on the map
 "zh": "SD73 学区小学；登记入学要带孩子的出生证明、BC Services Card、住址证明（有监护协议的也要带）",
 "en": "SD73 elementary; to register, bring your child’s birth certificate, BC Services Card and proof of address (and a custody agreement if one applies)",
 "fr": "École primaire du SD73 ; pour l’inscription, apportez l’acte de naissance de l’enfant, sa carte BC Services et une preuve d’adresse (et l’entente de garde, le cas échéant)",
 "es": "Primaria del SD73; para inscribir, traiga la partida de nacimiento del niño, su BC Services Card y un comprobante de domicilio (y el acuerdo de custodia, si corresponde)",
 "ko": "SD73 초등학교. 등록 시 아이의 출생증명서, BC Services Card, 주소 증빙(해당 시 양육권 합의서)을 가져오세요",
 "ja": "SD73の小学校。登録には子どもの出生証明書、BC Services Card、住所の証明（該当する場合は親権の取り決め）を持参",
}
NOTE_CSF = {
 "zh": "法语公立学校（CSF 第 93 学区），幼儿园到 8 年级，不属于 SD73。入学资格有规定，先看学校网站或打电话问。",
 "en": "French-language public school (Conseil scolaire francophone, district 93), Kindergarten to Grade 8 — not part of SD73. Eligibility rules apply: check the school’s site or call first.",
 "fr": "École publique francophone (Conseil scolaire francophone, district 93), de la maternelle à la 8e année — ne fait pas partie du SD73. Des critères d’admissibilité s’appliquent : consultez le site de l’école ou téléphonez d’abord.",
 "es": "Escuela pública de lengua francesa (Conseil scolaire francophone, distrito 93), de kínder a 8.º grado; no pertenece al SD73. Hay requisitos de admisión: consulte el sitio de la escuela o llame antes.",
 "ko": "프랑스어 공립학교(CSF 93학군), 유치원부터 8학년까지이며 SD73 소속이 아닙니다. 입학 자격 요건이 있으니 학교 홈페이지를 보거나 먼저 전화하세요.",
 "ja": "フランス語の公立学校（CSF 第93学区）。幼稚園から8年生まで。SD73には属しません。入学資格の条件があるので、学校のサイトを見るか、まず電話を。",
}

# name, area, lat, lng, address, phone, website, alias
NEW = [
 ("Bert Edwards Science & Technology School", "ns", 50.7085691, -120.3612095, "711 Windsor Ave", "250-376-2205", "https://best.sd73.bc.ca/en/index.aspx", ["BEST"]),
 ("Dallas Elementary",            "ot", 50.6673263, -120.1729595, "296 Harper Rd",      "250-573-3261", "https://www.sd73.bc.ca/dallas", None),
 ("Dufferin Elementary",          "sa", 50.6619608, -120.3966740, "1880 Hillside Dr",   "250-374-4425", "https://www.sd73.bc.ca/dufferin", None),
 ("George Hilliard Elementary",   "br", 50.7071645, -120.3883613, "985 Holt St",        "250-376-7253", "https://www.sd73.bc.ca/ghilliard", None),
 ("Juniper Ridge Elementary",     "vv", 50.6599202, -120.2449337, "2540 Qu’Appelle Blvd", "250-374-2305", "https://www.sd73.bc.ca/juniper-ridge", None),
 ("Kay Bingham Elementary",       "br", 50.7044512, -120.3980096, "950 Southill St",    "250-376-5586", "https://www.sd73.bc.ca/kay-bingham", None),
 ("McGowan Park Elementary",      "sa", 50.6446041, -120.3419866, "2080 Tremerton Dr",  "250-374-4545", "https://www.sd73.bc.ca/mcgowan", None),
 ("Pacific Way Elementary",       "sa", 50.6371745, -120.3708647, "2330 Pacific Way",   "250-851-0632", "https://www.sd73.bc.ca/pacificway", None),
 ("Ralph Bell Elementary",        "vv", 50.6754661, -120.2879247, "1764 Valleyview Dr", "778-765-0999", "https://www.sd73.bc.ca/ralph-bell", None),
 ("Rayleigh Elementary",          "ot", 50.7975104, -120.3162216, "306 Puett Ranch Rd", "250-578-7229", "https://www.sd73.bc.ca/rayleigh", None),
 ("RL Clemitson Elementary",      "ot", 50.6491537, -120.1658797, "5990 Todd Rd",       "250-573-3227", "https://www.sd73.bc.ca/rl-clemitson", ["Robert L Clemitson", "Barnhartvale"]),
 ("Summit Elementary",            "sa", 50.6529215, -120.3487164, "425 Monarch Crt",    "250-372-1224", "https://www.sd73.bc.ca/summit", None),
 ("Westmount Elementary",         "ns", 50.7185832, -120.3585978, "745 Walkem Rd",      "250-376-8879", "https://www.sd73.bc.ca/westmount", None),
 ("Westsyde Elementary",          "ws", 50.7738893, -120.3413155, "3550 Westsyde Rd",   "778-696-2265", "https://www.sd73.bc.ca/westsyde", None),
 ("École Collines-d’or",          "ws", 50.7456436, -120.3550583, "2450 Partridge Dr",  "250-579-9223", "https://collinesdor.csf.bc.ca/contactez-nous/",
     ["French school", "ecole francaise", "école française", "法语学校", "프랑스어 학교", "フランス語学校"]),
]

d = open(D, encoding='utf-8').read()
lines = d.split('\n')

# the P array runs from `const P=[` to the last record before `const QUARANTINE=`
start = [k for k, l in enumerate(lines) if l.startswith('const P=[')]
nextconst = [k for k, l in enumerate(lines) if l.startswith('const QUARANTINE=')]
if len(start) != 1 or len(nextconst) != 1:
    sys.exit('could not locate the P array (P starts %d, QUARANTINE starts %d)' % (len(start), len(nextconst)))
k = max(j for j in range(start[0], nextconst[0]) if lines[j].rstrip().endswith('}];'))
m = re.match(r'^(\s*)(\{.*\})\];\s*$', lines[k])
if not m:
    sys.exit('the closing line is not shaped like a record: %r' % lines[k][:80])

existing_ids = set(re.findall(r'"id":"([0-9a-f]{8})"', d))
existing_names = set(re.findall(r'\{"n":"([^"]+)"', d))

out = []
for n, g, lat, lng, a, p, w, alias in NEW:
    if n in existing_names:
        sys.exit('already present: %s' % n)
    i = uuid.uuid4().hex[:8]
    while i in existing_ids:
        i = uuid.uuid4().hex[:8]
    existing_ids.add(i)
    o = {"n": n, "c": "elem", "g": g, "lat": lat, "lng": lng, "a": a, "p": p, "w": w,
         "note": NOTE_CSF if "Collines" in n else NOTE,
         "src": "official", "v": "2026-09", "t": ["family"], "id": i}
    if alias:
        o["alias"] = alias
    s = J(o)
    assert json.loads(s) == o
    out.append(m.group(1) + s)

# keep the old last record, append the new ones, close the array on the last line
lines[k] = m.group(1) + m.group(2) + ','
lines[k+1:k+1] = [x + ',' for x in out[:-1]] + [out[-1] + '];']
open(D, 'w', encoding='utf-8').write('\n'.join(lines))
print('p21 applied: +%d elementary schools' % len(NEW))
