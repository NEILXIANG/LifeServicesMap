#!/usr/bin/env python3
"""Phase 6 — coverage the 2026-09-21 gap check found missing. Every fact is
from the page named beside it; coordinates are OpenStreetMap address matches
(house-number level) unless marked precision:'low'."""
import sys, hashlib
sys.path.insert(0, '.')
import kamdata

P = kamdata.load('P')
T = kamdata.load('TASKS')
by = {p['id']: p for p in P}
E, D = 'src/engine.html', 'src/data-kamloops.js'
V = '2026-09'
def pid(n): return hashlib.sha1(n.encode('utf-8')).hexdigest()[:8]
def L(**kw):
    assert set(kw) == {'zh', 'en', 'fr', 'es', 'ko', 'ja'}
    return {l: kw[l] for l in ('zh', 'en', 'fr', 'es', 'ko', 'ja')}
TORDER = ["life","family","fun","scenic","history","culture","free","multi","student","indoor"]
def tsort(t): return sorted(set(t), key=TORDER.index)
def add(rec):
    rec['id'] = pid(rec['n']); rec['v'] = V
    if 't' in rec: rec['t'] = tsort(rec['t'])
    assert rec['id'] not in by, rec['n']
    P.append(rec); by[rec['id']] = rec
    return rec['id']

# ---------------------------------------------------------------- Legal Aid BC office (legalaid.bc.ca/location-map/00141)
la = add({'n': 'Legal Aid BC (Kamloops)', 'c': 'legal', 'g': 'sk',
  'lat': by['85cdbdb6']['lat'], 'lng': by['85cdbdb6']['lng'], 'a': '455 Columbia St, 2nd Floor', 'p': '250-314-1900',
  'w': 'https://legalaid.bc.ca/location-map/00141', 'h': {'k': 'hCallDay'}, 'src': 'official', 't': ['free'],
  'alias': ['legal aid', '法律援助', '律师', '법률 구조', '法律扶助', 'aide juridique', 'asistencia legal'],
  'note': L(
    zh='Legal Aid BC 的本地办公室。免费法律咨询；收入符合条件的，还可以安排律师——涵盖家庭、儿童保护、刑事、移民与难民问题。可以要翻译。先打电话。',
    en='Legal Aid BC’s local office. Free legal advice and, if your income qualifies, a lawyer — for family, child protection, criminal, and immigration and refugee matters. Interpreters available. Call first.',
    fr='Le bureau local de Legal Aid BC. Conseils juridiques gratuits et, si votre revenu y donne droit, un avocat — droit de la famille, protection de l’enfance, criminel, immigration et réfugiés. Interprètes disponibles. Appelez d’abord.',
    es='La oficina local de Legal Aid BC. Asesoría legal gratuita y, si sus ingresos califican, un abogado: familia, protección de menores, penal, inmigración y refugio. Hay intérpretes. Llame primero.',
    ko='Legal Aid BC의 지역 사무소. 무료 법률 상담, 소득 요건이 맞으면 변호사 선임까지 — 가족, 아동 보호, 형사, 이민·난민 문제. 통역 가능. 먼저 전화하세요.',
    ja='Legal Aid BCの地域事務所。無料の法律相談と、収入の条件を満たせば弁護士も — 家族、児童保護、刑事、移民・難民の問題。通訳あり。まず電話を。')})
by[la]['sameComplex'] = ['85cdbdb6']
by['85cdbdb6'].setdefault('sameComplex', []).append(la)

# ---------------------------------------------------------------- Interior Health MHSU (interiorhealth.ca/locations/kamloops-mental-health-substance-use)
add({'n': 'Kamloops Mental Health & Substance Use (Interior Health)', 'c': 'hospital', 'g': 'sk',
  'lat': 50.6770, 'lng': -120.3358, 'precision': 'low', 'a': '235 Lansdowne St #100', 'p': '310-6478',
  'w': 'https://www.interiorhealth.ca/locations/kamloops-mental-health-substance-use',
  'h': {'r': [[1, 5, 510, 1020, 0]]}, 'src': 'official', 't': ['free'],
  'alias': ['mental health', 'counselling', 'addiction', '心理', '精神健康', '戒瘾', '정신건강', '상담', '中毒', 'こころ', 'santé mentale', 'salud mental'],
  'note': L(
    zh='Interior Health 的心理健康与成瘾服务办公室。工作日 8:30–17:00 可以直接去或自己申请，也可以打 310-6478。任何时间出现危机：1-888-353-2273。',
    en='Interior Health’s mental health and substance use office. Walk in or refer yourself on weekdays, 8:30–5, or call 310-6478. In crisis at any hour: 1-888-353-2273.',
    fr='Le bureau santé mentale et usage de substances d’Interior Health. Présentez-vous ou adressez-vous vous-même en semaine, 8 h 30–17 h, ou appelez le 310-6478. En crise, à toute heure : 1-888-353-2273.',
    es='La oficina de salud mental y consumo de sustancias de Interior Health. Vaya sin cita o derívese usted mismo entre semana, 8:30–17:00, o llame al 310-6478. En crisis, a cualquier hora: 1-888-353-2273.',
    ko='Interior Health의 정신건강·약물 사용 사무소. 평일 8:30–17:00에 직접 방문하거나 스스로 의뢰할 수 있고, 310-6478로 전화해도 됩니다. 위기 시 언제든: 1-888-353-2273.',
    ja='Interior Healthの精神保健・薬物使用の窓口。平日8:30–17:00に直接行くか自分で申し込めます。310-6478に電話も可。危機のときはいつでも：1-888-353-2273。')})

# ---------------------------------------------------------------- KSACC (ksacc.ca)
add({'n': 'Kamloops Sexual Assault Counselling Centre', 'c': 'support', 'g': 'sk',
  'lat': 50.6751197, 'lng': -120.3245204, 'a': '694 Seymour St', 'p': '250-372-0179',
  'w': 'https://www.ksacc.ca/', 'h': {'k': 'hCallDay'}, 'src': 'official', 't': ['free'],
  'alias': ['sexual assault', 'abuse', '性侵', '性暴力', '성폭력', '性暴力被害', 'agression sexuelle', 'agresión sexual'],
  'note': L(
    zh='性侵或虐待之后的免费咨询和支持。24 小时危机热线 1-888-974-7278；办公室 250-372-0179。',
    en='Free counselling and support after sexual assault or abuse. 24-hour crisis line 1-888-974-7278; office 250-372-0179.',
    fr='Counseling et soutien gratuits après une agression sexuelle ou des abus. Ligne de crise 24 h : 1-888-974-7278 ; bureau : 250-372-0179.',
    es='Asesoría y apoyo gratuitos tras una agresión sexual o abuso. Línea de crisis 24 horas: 1-888-974-7278; oficina: 250-372-0179.',
    ko='성폭력이나 학대 이후의 무료 상담과 지원. 24시간 위기 전화 1-888-974-7278, 사무실 250-372-0179.',
    ja='性暴力や虐待の後の無料カウンセリングと支援。24時間の危機ライン 1-888-974-7278、事務所 250-372-0179。')})

# ---------------------------------------------------------------- South Asian community
add({'n': 'Gurdwara Sahib Society', 'c': 'religious', 'g': 'br',
  'lat': 50.710196, 'lng': -120.375573, 'a': '1345 Ord Rd', 'src': 'places', 't': ['multi', 'culture'],
  'alias': ['gurdwara', 'Sikh', '锡克', '시크', 'シク', 'Punjabi'],
  'note': L(
    zh='Brocklehurst 的锡克教谒师所（Gurdwara），是本市第二座，另一座是 Cambridge Cres 的 Sikh Cultural Society。',
    en='A Sikh gurdwara in Brocklehurst — the city’s second, alongside the Sikh Cultural Society on Cambridge Cres.',
    fr='Un gurdwara sikh à Brocklehurst — le deuxième de la ville, avec la Sikh Cultural Society sur Cambridge Cres.',
    es='Un gurdwara sij en Brocklehurst, el segundo de la ciudad junto a la Sikh Cultural Society en Cambridge Cres.',
    ko='Brocklehurst의 시크교 구르드와라 — Cambridge Cres의 Sikh Cultural Society와 함께 시의 두 번째 구르드와라입니다.',
    ja='Brocklehurstのシク教のグルドワラ。Cambridge CresのSikh Cultural Societyに続く、市内2つ目です。')})
add({'n': 'FraserCart Indian Store', 'c': 'asian', 'g': 'sa',
  'lat': 50.6679695, 'lng': -120.3604096, 'a': '795 McGill Rd #103', 'src': 'places', 't': ['life', 'multi'],
  'alias': ['Indian', 'Punjabi', 'halal', '印度', '인도', 'インド', 'épicerie indienne', 'tienda india'],
  'note': L(
    zh='印度食品和香料杂货店，靠近 TRU。',
    en='Indian groceries and spices, near TRU.',
    fr='Épicerie indienne et épices, près de TRU.',
    es='Comestibles y especias de la India, cerca de TRU.',
    ko='인도 식료품과 향신료, TRU 근처.',
    ja='インドの食料品とスパイス。TRUの近く。')})

# ---------------------------------------------------------------- StrongStart (sd73.bc.ca strongstart page)
SS = L(
  zh='这里有 StrongStart：0–5 岁孩子和家长一起参加的免费早教活动，不用排队。',
  en='Has a StrongStart centre: free drop-in early learning for children up to age 5 with their parent or caregiver — no waitlist.',
  fr='Accueille un centre StrongStart : éveil gratuit sans inscription pour les enfants jusqu’à 5 ans avec leur parent — pas de liste d’attente.',
  es='Tiene un centro StrongStart: aprendizaje temprano gratuito y sin cita para niños de hasta 5 años con su padre, madre o cuidador; sin lista de espera.',
  ko='StrongStart 센터가 있습니다: 5세 이하 아이가 부모와 함께 참여하는 무료 조기 학습, 대기자 명단 없음.',
  ja='StrongStartがあります：5歳までの子どもが親と一緒に参加できる無料の幼児教育。順番待ちなし。')
for i in ('fb43944b', 'e7a06546', 'b7096197', '1fb066c7'):
    p = by[i]
    p['note'] = {l: (p['note'][l].rstrip('。.') + ('。' if l in ('zh', 'ja') else '. ') + SS[l]) for l in p['note']}
    p['alias'] = sorted(set((p.get('alias') or []) + ['StrongStart', '早教', '幼儿']))
    p['t'] = tsort((p.get('t') or []) + ['family', 'free'])
    p['v'] = V

# ---------------------------------------------------------------- CDCP (the clinics' own sites; canada.ca eligibility)
CD = L(
  zh='接受加拿大牙科护理计划（CDCP）。申请条件：报过加拿大税、家庭收入在限额以内、没有私人牙科保险。',
  en='Accepts the Canadian Dental Care Plan (CDCP). To qualify you must have filed a Canadian tax return, be under the family income limit and have no private dental insurance.',
  fr='Accepte le Régime canadien de soins dentaires (RCSD). Pour y avoir droit, il faut avoir produit une déclaration de revenus au Canada, respecter le plafond de revenu familial et ne pas avoir d’assurance dentaire privée.',
  es='Acepta el Canadian Dental Care Plan (CDCP). Para calificar, debe haber presentado la declaración de impuestos en Canadá, estar por debajo del límite de ingresos familiares y no tener seguro dental privado.',
  ko='캐나다 치과 치료 계획(CDCP)을 받습니다. 자격: 캐나다 세금 신고를 했고, 가구 소득이 기준 이하이며, 민간 치과 보험이 없어야 합니다.',
  ja='カナダ歯科ケアプラン（CDCP）が使えます。対象は、カナダで確定申告をし、世帯収入が上限以下で、民間の歯科保険がない人です。')
by['9b1e48e3']['note'] = dict(CD)
by['de3a3b49']['note'] = {l: by['de3a3b49']['note'][l].rstrip('。.') + ('。' if l in ('zh', 'ja') else '. ') + CD[l] for l in CD}
for i in ('9b1e48e3', 'de3a3b49'): by[i]['v'] = V

# ---------------------------------------------------------------- exact coordinates for two phase-2 moves (OSM house-number match)
by['b240c0e9'].update(lat=50.6772215, lng=-120.3422852); by['b240c0e9'].pop('precision', None)

kamdata.save('P', P)

# ---------------------------------------------------------------- women leaving violence (ymcabc.ca womens-emergency-shelter)
h = next(t for t in T if t['id'] == 'hardship')
W = {
 'en': ' Women leaving violence, with or without children: Y Women’s Emergency Shelter, call 250-374-6162 or text 250-682-7931, 24 hours, free, no referral.',
 'fr': ' Femmes qui fuient la violence, avec ou sans enfants : Y Women’s Emergency Shelter, appel au 250-374-6162 ou texto au 250-682-7931, 24 h sur 24, gratuit, sans référence.',
 'es': ' Mujeres que huyen de la violencia, con o sin hijos: Y Women’s Emergency Shelter, llame al 250-374-6162 o envíe un texto al 250-682-7931, 24 horas, gratis, sin derivación.',
 'zh': '逃离暴力的女性（带不带孩子都可以）：Y Women’s Emergency Shelter，打 250-374-6162 或发短信 250-682-7931，24 小时，免费，不需要转介。',
 'ko': ' 폭력을 피해 나온 여성(자녀 동반 여부 무관): Y Women’s Emergency Shelter, 전화 250-374-6162 또는 문자 250-682-7931, 24시간, 무료, 의뢰 불필요.',
 'ja': '暴力から逃れる女性（子連れでも一人でも）：Y Women’s Emergency Shelter、電話 250-374-6162、SMS 250-682-7931、24時間・無料・紹介不要。'}
for l, v in W.items():
    assert 'Y Women' not in h['note'][l]
    h['note'][l] = h['note'][l] + v
kamdata.save('TASKS', T)

# ---------------------------------------------------------------- the Help sheet: local lines, not one
d = open(D, encoding='utf-8').read()
o = "  localCrisis:{n:'778-470-2725',src:'https://kafs.ca/crcl-program',"
assert d.count(o) == 1
d = d.replace(o, "  // 2026-09-21: every local line the Help sheet and a crisis search show.\n"
  "  // ymcabc.ca womens-emergency-shelter; interiorhealth.ca (Interior Crisis Line).\n"
  "  localLines:[\n"
  "   {n:'250-374-6162',note:{en:'Y Women’s Emergency Shelter — women, with or without children, leaving violence. 24 hours, free, no referral; the address is kept private. Call, or text 250-682-7931:',\n"
  "      fr:'Y Women’s Emergency Shelter — femmes, avec ou sans enfants, qui fuient la violence. 24 h sur 24, gratuit, sans référence ; l’adresse reste confidentielle. Appelez, ou textez le 250-682-7931 :',\n"
  "      es:'Y Women’s Emergency Shelter — mujeres, con o sin hijos, que huyen de la violencia. 24 horas, gratis, sin derivación; la dirección es confidencial. Llame, o envíe un texto al 250-682-7931:',\n"
  "      zh:'Y Women’s Emergency Shelter——逃离暴力的女性（带不带孩子都行）。24 小时，免费，不需要转介；地址保密。打电话，或发短信到 250-682-7931：',\n"
  "      ko:'Y Women’s Emergency Shelter — 폭력을 피해 나온 여성(자녀 동반 무관). 24시간, 무료, 의뢰 불필요, 주소는 비공개. 전화하거나 250-682-7931로 문자:',\n"
  "      ja:'Y Women’s Emergency Shelter — 暴力から逃れる女性（子連れでも一人でも）。24時間・無料・紹介不要、住所は非公開。電話、またはSMS 250-682-7931：'}},\n"
  "   {n:'1-888-353-2273',note:{en:'Interior Crisis Line, 24 hours:',fr:'Interior Crisis Line, 24 h sur 24 :',es:'Interior Crisis Line, 24 horas:',zh:'Interior 危机热线，24 小时：',ko:'Interior 위기 전화, 24시간:',ja:'Interior危機ライン、24時間：'}},\n"
  "  ],\n" + o)
open(D, 'w', encoding='utf-8').write(d)
s = open(E, encoding='utf-8').read()
o = ("function localCrisisHtml(){\n"
     "  const c=CITY.localCrisis;if(!c)return '';\n"
     "  return '<p class=\"help-local\">'+esc(c.note[L_]||c.note.en)+' <a href=\"tel:'+esc(c.n.replace(/[^\\d]/g,''))+'\"><b>'+esc(c.n)+'</b></a></p>';\n"
     "}")
assert s.count(o) == 1, 'localCrisisHtml'
s = s.replace(o, "function localCrisisHtml(){\n"
     "  const line=c=>'<p class=\"help-local\">'+esc(c.note[L_]||c.note.en)+' <a href=\"tel:'+esc(c.n.replace(/[^\\d]/g,''))+'\"><b>'+esc(c.n)+'</b></a></p>';\n"
     "  return (CITY.localLines||[]).map(line).join('')+(CITY.localCrisis?line(CITY.localCrisis):'');\n"
     "}")
open(E, 'w', encoding='utf-8').write(s)
print('phase 6 applied')
