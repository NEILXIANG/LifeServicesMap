#!/usr/bin/env python3
"""Phase 7 — a page for people who live here, not only for people arriving;
and the Nation's own spelling and names (2026-09-21 outreach-site check)."""
import sys, re
sys.path.insert(0, '.')
import kamdata

E, D = 'src/engine.html', 'src/data-kamloops.js'
d = open(D, encoding='utf-8').read()
s = open(E, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:90], n))
    return src.replace(old, new)

# ---------------------------------------------------------------- Kamloopa Powwow is in June (tkemlups.ca: 26–28 June 2026)
for old, new in (("每年 8 月在 Tk'emlúps 举行的", "每年 6 月在 Tk'emlúps 举行的"), ('Each August the <b>Kamloopa', 'Each June the <b>Kamloopa'),
                 ('Chaque août, le <b>Kamloopa', 'Chaque année en juin, le <b>Kamloopa'), ('Cada agosto el <b>Kamloopa', 'Cada junio el <b>Kamloopa'),
                 ("매년 8월 Tk'emlúps에서", "매년 6월 Tk'emlúps에서"), ("毎年 8 月に Tk'emlúps で", "毎年 6 月に Tk'emlúps で")):
    d = rep(d, old, new)

# ---------------------------------------------------------------- the Nation's spelling: Tk̓emlúps (comma above the k)
# FAV_MIGRATE keys are old names people may have saved, so that line keeps them.
K = "Tk̓emlúps"
out = []
for line in d.split('\n'):
    out.append(line if line.startswith('const FAV_MIGRATE=') else line.replace("Tk'emlúps", K))
d = '\n'.join(out)
assert d.count(K) >= 30, d.count(K)

# ---------------------------------------------------------------- the land section: the Nation's own words, and two more 24-hour lines
IND = {
 'zh': ('24 小时服务：<b>1-800-588-8717</b>。</p><h3>🧳',
        '24 小时服务：<b>1-800-588-8717</b>。寄宿学校幸存者及家属危机热线 <b>1-866-925-4419</b> 和原住民心理支持热线 Hope for Wellness <b>1-855-242-3310</b> 也都 24 小时有人接。</p>\n'
        '<p>该民族称那些没能回家的孩子为 <i>Le Estcwicwéy̓</i>——“失踪的人”。在悼念场合，请尊重该民族自己的礼仪。</p>'),
 'en': ('Indigenous people across BC: <b>1-800-588-8717</b>.</p><h3>🧳',
        'Indigenous people across BC: <b>1-800-588-8717</b>. The Indian Residential School Survivors and Family Crisis Line (<b>1-866-925-4419</b>) and Hope for Wellness (<b>1-855-242-3310</b>) also answer 24 hours.</p>\n'
        '<p>The Nation calls the children who did not come home <i>Le Estcwicwéy̓</i> — “the missing”. At memorials, follow the Nation’s own protocols.</p>'),
 'fr': ('aux Autochtones de la C.-B. : <b>1-800-588-8717</b>.</p><h3>🧳',
        'aux Autochtones de la C.-B. : <b>1-800-588-8717</b>. La ligne de crise pour les survivants des pensionnats indiens et leurs familles (<b>1-866-925-4419</b>) et Espoir pour le mieux-être (<b>1-855-242-3310</b>) répondent aussi 24 h sur 24.</p>\n'
        '<p>La Nation appelle les enfants qui ne sont pas rentrés <i>Le Estcwicwéy̓</i> — « les disparus ». Lors des commémorations, respectez les protocoles de la Nation.</p>'),
 'es': ('a personas indígenas de BC: <b>1-800-588-8717</b>.</p><h3>🧳',
        'a personas indígenas de BC: <b>1-800-588-8717</b>. La línea de crisis para sobrevivientes de las escuelas residenciales y sus familias (<b>1-866-925-4419</b>) y Hope for Wellness (<b>1-855-242-3310</b>) también atienden las 24 horas.</p>\n'
        '<p>La Nación llama a los niños que no volvieron a casa <i>Le Estcwicwéy̓</i>, “los desaparecidos”. En los actos de memoria, siga los protocolos de la Nación.</p>'),
 'ko': ('BC주 원주민을 대상으로 24시간 운영됩니다: <b>1-800-588-8717</b>.</p><h3>🧳',
        'BC주 원주민을 대상으로 24시간 운영됩니다: <b>1-800-588-8717</b>. 기숙학교 생존자·가족 위기 전화(<b>1-866-925-4419</b>)와 Hope for Wellness(<b>1-855-242-3310</b>)도 24시간 받습니다.</p>\n'
        '<p>이 부족은 집에 돌아오지 못한 아이들을 <i>Le Estcwicwéy̓</i> — “실종된 이들”이라고 부릅니다. 추모 행사에서는 부족의 의례를 따르세요.</p>'),
 'ja': ('24時間対応しています: <b>1-800-588-8717</b>。</p><h3>🧳',
        '24時間対応しています: <b>1-800-588-8717</b>。寄宿学校のサバイバーと家族のための危機ライン（<b>1-866-925-4419</b>）と Hope for Wellness（<b>1-855-242-3310</b>）も24時間つながります。</p>\n'
        '<p>この民族は、家に帰れなかった子どもたちを <i>Le Estcwicwéy̓</i>（「行方不明の子どもたち」）と呼びます。追悼の場では民族の作法に従ってください。</p>'),
}
# ---------------------------------------------------------------- living here for years (report §4; each item checked on the City / TNRL page)
RES = {
 'zh': '<h3>🏡 在这里住了很多年的人，也用得上这些</h3>\n<p><b>ARCH</b> 是市政府的康乐补贴：收入符合条件的居民，每年最多有 400 加元的额度用于游泳、健身和课程，自己付 15%，通过推荐机构申请。办了 ARCH 还可以买 <b>KamPASS</b> 低价公交月票（在 {CITY} 博物馆买）。有图书证的话，图书馆的<b>社区通行证</b>可以免费借一周：泳池、TCC、野生动物园、科学中心、Paramount 影院。下雪天，<b>Snow Angels</b> 志愿者会帮老人和行动不便的人铲雪——可以求助，也可以报名帮忙。<b>2026 年 10 月 17 日</b>是市政选举；投票要有加拿大公民身份。父母年纪大了，看“照顾年长的家人”那张卡。</p>',
 'en': '<h3>🏡 If you have lived here for years</h3>\n<p><b>ARCH</b> is the City’s recreation subsidy: income-qualified residents get up to $400 a year towards swimming, gym and programmes, paying 15% themselves, and apply through a referring agency. ARCH members can also buy <b>KamPASS</b>, a low-cost transit pass (sold at the {CITY} Museum). With a library card, the library’s <b>Community Pass</b> lends a free family pass for a week — pools, the TCC, the BC Wildlife Park, the science centre and the Paramount. When it snows, <b>Snow Angels</b> volunteers clear walks for seniors and people with limited mobility — ask for help, or sign up to give it. The municipal election is on <b>October 17, 2026</b>; voting needs Canadian citizenship. For a parent who is getting older, see the card on caring for an older relative.</p>',
 'fr': '<h3>🏡 Si vous vivez ici depuis des années</h3>\n<p><b>ARCH</b> est la subvention de loisirs de la Ville : les résidents admissibles selon le revenu ont jusqu’à 400 $ par an pour la natation, la salle de sport et les cours, en payant 15 % eux-mêmes, et font la demande par un organisme de référence. Les membres ARCH peuvent aussi acheter <b>KamPASS</b>, un laissez-passer de transport à bas prix (vendu au {CITY} Museum). Avec une carte de bibliothèque, le <b>Community Pass</b> prête gratuitement un laissez-passer familial pour une semaine — piscines, TCC, BC Wildlife Park, centre des sciences et Paramount. Quand il neige, les bénévoles <b>Snow Angels</b> déneigent pour les aînés et les personnes à mobilité réduite — demandez de l’aide ou inscrivez-vous pour en donner. L’élection municipale a lieu le <b>17 octobre 2026</b> ; il faut la citoyenneté canadienne pour voter. Pour un parent vieillissant, voir la fiche sur l’aide à un proche âgé.</p>',
 'es': '<h3>🏡 Si lleva años viviendo aquí</h3>\n<p><b>ARCH</b> es la subvención recreativa de la Ciudad: los residentes que califican por ingresos reciben hasta 400 $ al año para natación, gimnasio y programas, pagando ellos el 15 %, y lo solicitan a través de una agencia de referencia. Los miembros de ARCH también pueden comprar <b>KamPASS</b>, un pase de transporte de bajo costo (se vende en el {CITY} Museum). Con tarjeta de biblioteca, el <b>Community Pass</b> presta gratis un pase familiar por una semana: piscinas, TCC, BC Wildlife Park, centro de ciencias y Paramount. Cuando nieva, los voluntarios de <b>Snow Angels</b> quitan la nieve para personas mayores o con movilidad reducida; pida ayuda o inscríbase para darla. Las elecciones municipales son el <b>17 de octubre de 2026</b>; para votar se necesita la ciudadanía canadiense. Para un padre o madre que envejece, vea la ficha sobre el cuidado de un familiar mayor.</p>',
 'ko': '<h3>🏡 이곳에 오래 살아온 분께</h3>\n<p><b>ARCH</b>는 시의 여가 지원금입니다: 소득 요건이 맞는 주민은 수영, 헬스, 강좌에 연 최대 400달러를 받고 15%만 본인이 내며, 추천 기관을 통해 신청합니다. ARCH 회원은 저가 교통 패스 <b>KamPASS</b>도 살 수 있습니다({CITY} 박물관에서 판매). 도서관 카드가 있으면 도서관의 <b>Community Pass</b>로 가족 이용권을 일주일간 무료로 빌릴 수 있습니다 — 수영장, TCC, BC Wildlife Park, 과학관, Paramount. 눈이 오면 <b>Snow Angels</b> 자원봉사자가 노인과 거동이 불편한 분의 눈을 치워 줍니다 — 도움을 요청하거나 봉사자로 등록하세요. 시 선거는 <b>2026년 10월 17일</b>이며, 투표하려면 캐나다 시민권이 필요합니다. 나이 드신 부모님이 있다면 ‘나이 든 가족 돌보기’ 카드를 보세요.</p>',
 'ja': '<h3>🏡 長くここに住んでいる人へ</h3>\n<p><b>ARCH</b>は市のレクリエーション補助です。収入の条件を満たす住民は、水泳・ジム・講座に年最大400ドル分が使え、自己負担は15%。紹介機関を通じて申し込みます。ARCHの会員は低料金の交通パス<b>KamPASS</b>も買えます（{CITY}博物館で販売）。図書館カードがあれば、図書館の<b>Community Pass</b>で家族用の入場パスを1週間無料で借りられます — プール、TCC、BC Wildlife Park、科学館、Paramount。雪の日は<b>Snow Angels</b>のボランティアが高齢者や体の不自由な人の雪かきをします — 頼むことも、手伝いに登録することもできます。市の選挙は<b>2026年10月17日</b>で、投票にはカナダ国籍が必要です。親が年を取ってきたら、「年老いた家族の世話」のカードを見てください。</p>',
}
for l, (anchor, repl) in IND.items():
    d = rep(d, anchor, repl + '\n' + RES[l] + '<h3>🧳')

# ---------------------------------------------------------------- Help sheet: the two Indigenous 24-hour lines
d = rep(d, "   {n:'1-888-353-2273',note:{",
  "   {n:'1-866-925-4419',note:{en:'Residential school survivors and families, 24 hours:',fr:'Survivants des pensionnats et leurs familles, 24 h sur 24 :',es:'Sobrevivientes de las escuelas residenciales y sus familias, 24 horas:',zh:'寄宿学校幸存者及家属，24 小时：',ko:'기숙학교 생존자와 가족, 24시간:',ja:'寄宿学校のサバイバーと家族、24時間：'}},\n"
  "   {n:'1-855-242-3310',note:{en:'Hope for Wellness (Indigenous peoples), 24 hours:',fr:'Espoir pour le mieux-être (Autochtones), 24 h sur 24 :',es:'Hope for Wellness (pueblos indígenas), 24 horas:',zh:'Hope for Wellness（原住民心理支持），24 小时：',ko:'Hope for Wellness(원주민 대상), 24시간:',ja:'Hope for Wellness（先住民向け）、24時間：'}},\n"
  "   {n:'1-888-353-2273',note:{")
open(D, 'w', encoding='utf-8').write(d)

# the admin office: still found by the spelling people type
P = kamdata.load('P')
for p in P:
    if p['id'] == '718a712f':
        p['alias'] = sorted(set((p.get('alias') or []) + ["Tk'emlúps", 'Tkemlups', 'TteS']))
kamdata.save('P', P)

# ---------------------------------------------------------------- the page speaks to residents too
SUB = {
 'zh': ('给刚到的人，也给住了很久、想帮人的人', '刚到的人和住了很多年的人，都用得上'),
 'en': ('for people who just arrived, and for anyone who wants to help them', 'for people who just arrived, and for people who have lived here for years'),
 'fr': ('pour qui arrive, et pour qui veut aider', 'pour qui arrive, et pour qui vit ici depuis des années'),
 'es': ('para quien llega, y para quien quiere ayudar', 'para quien llega, y para quien lleva años aquí'),
 'ko': ('막 도착한 분에게, 그리고 돕고 싶은 분에게', '막 도착한 분에게도, 오래 살아온 분에게도'),
 'ja': ('来たばかりの人に、そして助けたい人に', '来たばかりの人にも、長く住んでいる人にも'),
}
for l, (a, b) in SUB.items():
    s = rep(s, a, b)
PRE = {'"newcomer":"🧳 居民必备"': '"newcomer":"🧳 刚搬来"', '"newcomer":"🧳 Resident Essentials"': '"newcomer":"🧳 Just moved"',
       '"newcomer":"🧳 Essentiels résidents"': '"newcomer":"🧳 Nouvelle installation"', '"newcomer":"🧳 Esenciales para residentes"': '"newcomer":"🧳 Recién mudado"',
       '"newcomer":"🧳 주민 필수"': '"newcomer":"🧳 막 이사 옴"', '"newcomer": "🧳 住民の手続き先"': '"newcomer": "🧳 引っ越してきたら"'}
for a, b in PRE.items():
    s = rep(s, a, b)
m = re.search(r'"ja":\{"title".*?"newcomer": ?"([^"]*)"', s, re.S)
print('ja preset label:', m.group(1) if m else None)
open(E, 'w', encoding='utf-8').write(s)
print('phase 7 applied')
