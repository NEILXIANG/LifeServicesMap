#!/usr/bin/env python3
"""Phase 2 — the 47 serious data problems from the 2026-09-21 full check,
plus the tax card. Every fact below comes from the operator's own page or
a government page named in the comment; nothing is guessed. Where two
official sources disagree, the record says so instead of picking one."""
import sys, json, copy
sys.path.insert(0, '.')
import kamdata

P = kamdata.load('P')
Q = kamdata.load('QUARANTINE')
T = kamdata.load('TASKS')
by = {p['id']: p for p in P}
L6 = ('en', 'fr', 'es', 'zh', 'ko', 'ja')
V = '2026-09'
done = []

def rec(i):
    assert i in by, i
    return by[i]

def note(i, **kw):
    assert set(kw) == set(L6), (i, set(L6) - set(kw))
    rec(i)['note'] = {l: kw[l] for l in ('zh', 'en', 'fr', 'es', 'ko', 'ja')}

def setf(i, **kw):
    p = rec(i)
    for k, v in kw.items():
        if v is None: p.pop(k, None)
        else: p[k] = v
    p['v'] = V
    done.append(i)

def quarantine(i, why):
    global P
    p = rec(i)
    for o in P:
        sc = o.get('sameComplex')
        if sc and i in sc:
            sc.remove(i)
            if not sc: o.pop('sameComplex')
    p.pop('sameComplex', None)
    p['quarantined'] = '2026-09-21: ' + why
    Q.append(p)
    P = [x for x in P if x['id'] != i]
    done.append(i)

# ---------------------------------------------------------------- harm first
# Pathways: the number was ASK Wellness's weekday office. bc211 listing gives
# the shelter's own intake and inquiry lines; askwellness.ca/streets/pathways/
setf('b08eb3fe', p='250-299-7936', w='https://askwellness.ca/streets/pathways/')
note('b08eb3fe',
  en='A 44-bed low-barrier emergency shelter on the North Shore, open 24 hours. Intake line 250-299-7936; general inquiries 250-312-3881 (the ASK Wellness office number is weekdays only). Meals, washrooms and showers, somewhere to store your belongings, cultural programming, help setting goals, and access to a mobile health clinic. Low-barrier means you are not turned away for having nothing with you; people who have been drinking or using are accepted as long as they are not disruptive.',
  fr='Refuge d’urgence à bas seuil de 44 lits sur la rive nord, ouvert 24 heures. Ligne d’accueil 250-299-7936 ; renseignements 250-312-3881 (le numéro du bureau d’ASK Wellness ne répond qu’en semaine). Repas, toilettes et douches, un endroit où ranger vos affaires, programmes culturels, aide à se fixer des objectifs et accès à une clinique mobile. Bas seuil veut dire qu’on ne vous refuse pas parce que vous n’avez rien sur vous ; les personnes qui ont bu ou consommé sont acceptées tant qu’elles ne perturbent pas les lieux.',
  es='Albergue de emergencia de bajo umbral con 44 camas en la ribera norte, abierto 24 horas. Línea de ingreso 250-299-7936; consultas 250-312-3881 (el número de la oficina de ASK Wellness solo atiende entre semana). Comidas, baños y duchas, un lugar para guardar sus cosas, programación cultural, ayuda para fijar metas y acceso a una clínica móvil. Bajo umbral significa que no se le rechaza por no llevar nada; se acepta a quien haya bebido o consumido mientras no cause disturbios.',
  zh='北岸的 44 床位低门槛紧急庇护所，24 小时开放。入住电话 250-299-7936；一般咨询 250-312-3881（ASK Wellness 办公室的号码只在工作日接听）。提供餐食、洗手间与淋浴、存放随身物品的地方、文化活动、目标规划协助，以及流动医疗诊所。“低门槛”的意思是：身上什么都没有也不会被拒；喝了酒或用了药的人，只要不扰乱秩序也会接收。',
  ko='노스쇼어에 있는 44병상 저문턱 응급 쉼터로 24시간 운영합니다. 입소 전화 250-299-7936, 일반 문의 250-312-3881 (ASK Wellness 사무실 번호는 평일에만 받습니다). 식사, 화장실과 샤워, 소지품 보관, 문화 프로그램, 목표 설정 지원, 이동 진료소 이용이 가능합니다. 저문턱이란 아무것도 없이 왔다고 돌려보내지 않는다는 뜻이며, 술이나 약물을 한 사람도 소란을 일으키지 않으면 받아 줍니다.',
  ja='ノースショアにある44床のローバリア緊急シェルターで、24時間開いています。入所の電話 250-299-7936、一般の問い合わせ 250-312-3881（ASK Wellness事務所の番号は平日のみ）。食事、トイレとシャワー、荷物を置く場所、文化プログラム、目標設定の支援、移動診療所の利用ができます。ローバリアとは、何も持っていなくても追い返さないという意味で、飲酒や薬物使用のある人も、周りに迷惑をかけなければ受け入れます。')

# Overlanders: kamloops.ca page says no swimming (drowning risk, strong currents)
setf('80e697e8')
note('80e697e8',
  en='Riverside park with good views. Swimming is not allowed here — the river has strong currents.',
  fr='Parc au bord de la rivière avec de belles vues. La baignade y est interdite — le courant est fort.',
  es='Parque junto al río con buenas vistas. Aquí no se permite nadar: la corriente es fuerte.',
  zh='河边公园，景色好。这里禁止游泳——河水流急。',
  ko='전망이 좋은 강변 공원입니다. 이곳은 수영 금지입니다 — 물살이 셉니다.',
  ja='眺めのよい川沿いの公園。ここは遊泳禁止です — 流れが速いです。')

# ---------------------------------------------------------------- closed
quarantine('878135f5', 'closed — the last post on its own Facebook page (6 Feb 2023) says "Final week of play"; the website no longer loads')
quarantine('a634fe38', 'the Mt Paul Way site is closed; its own site says it is moving downtown (380 Victoria St) — restore at the new address once it reopens')
quarantine('645ae374', 'closing for good on 30 Sep 2026 (its own Facebook post of 7 Sep 2026); no longer taking donations')
quarantine('97daa003', '344 Poplar St is the Salvation Army church and resource centre, not a thrift store (kamloopssalvationarmy.ca); the food program there is its own row, df64d05e')

# Columbia Square: Toys R Us closed 2025 (Castanet); owner lists Dolson's, TD,
# Boston Pizza, McDonald's (nwproperties.ca). The phone is Columbia Place's in
# one directory and Columbia Square's in another — dropped rather than guessed.
setf('ef7c19b3', p=None)
note('ef7c19b3',
  en='Strip mall with Dolson’s, TD, Boston Pizza and McDonald’s; Save-On-Foods is next door in Columbia Place.',
  fr='Centre commercial avec Dolson’s, TD, Boston Pizza et McDonald’s ; Save-On-Foods est juste à côté, dans Columbia Place.',
  es='Centro comercial con Dolson’s, TD, Boston Pizza y McDonald’s; Save-On-Foods está al lado, en Columbia Place.',
  zh='小型购物中心，有 Dolson’s、TD 银行、Boston Pizza 和麦当劳；Save-On-Foods 在隔壁的 Columbia Place。',
  ko='Dolson’s, TD, Boston Pizza, 맥도날드가 있는 상가입니다. Save-On-Foods는 바로 옆 Columbia Place에 있습니다.',
  ja='Dolson’s、TD、Boston Pizza、マクドナルドが入るショッピングプラザ。Save-On-Foodsは隣のColumbia Placeにあります。')

# Service BC: the photo BC Services Card is issued at ICBC (gov.bc.ca "Get a card")
setf('85cdbdb6')
note('85cdbdb6',
  en='The province’s front counter: help with MSP enrolment, birth certificates and other provincial programmes. The photo BC Services Card itself is issued at an ICBC driver licensing office, not here. Bring your passport or immigration papers and one letter showing your local address. Weekdays 9–4:30.',
  fr='Le guichet de la province : aide à l’inscription au MSP, certificats de naissance et autres programmes provinciaux. La carte BC Services avec photo, elle, se fait dans un bureau de permis de conduire d’ICBC, pas ici. Apportez votre passeport ou vos papiers d’immigration et une lettre montrant votre adresse locale. En semaine, 9 h–16 h 30.',
  es='La ventanilla de la provincia: ayuda con la inscripción al MSP, partidas de nacimiento y otros programas provinciales. La BC Services Card con foto se tramita en una oficina de licencias de ICBC, no aquí. Traiga su pasaporte o documentos de inmigración y una carta con su dirección local. Días laborables, 9–16:30.',
  zh='省政府的一站式窗口：协助办理 MSP 医保登记、出生证明及其他省级项目。带照片的 BC Services Card 本身要去 ICBC 驾照办公室办，不在这里。带护照或移民文件、以及一份写有本地地址的信件。周一至周五 9:00–16:30。',
  ko='주 정부 민원 창구: MSP 등록, 출생증명서, 기타 주 정부 프로그램을 도와줍니다. 사진이 있는 BC Services Card 자체는 여기가 아니라 ICBC 운전면허 사무소에서 발급합니다. 여권이나 이민 서류, 그리고 현지 주소가 적힌 우편물 하나를 가져오세요. 평일 9:00–16:30.',
  ja='州の総合窓口：MSP加入の手続き、出生証明書、その他の州のプログラムを扱います。写真付きのBC Services Card自体は、ここではなくICBCの運転免許事務所で発行されます。パスポートか移民書類と、現住所の分かる郵便物を1通持参してください。平日 9:00–16:30。')

# Salvation Army food program: its own site shows two schedules — say so.
setf('df64d05e', h=None)
note('df64d05e',
  en='Emergency food hampers. The Salvation Army’s own website currently shows two different schedules (Tuesday to Friday 10am–1pm on one page; Monday and Wednesday 9–11:45am, once every 60 days, on another), so call 250-554-1611 before you go. Bring ID for everyone in your household and current proof of income.',
  fr='Paniers alimentaires d’urgence. Le site de l’Armée du Salut affiche actuellement deux horaires différents (du mardi au vendredi 10 h–13 h sur une page ; lundi et mercredi 9 h–11 h 45, une fois tous les 60 jours, sur une autre) : appelez le 250-554-1611 avant d’y aller. Apportez une pièce d’identité pour chaque membre du ménage et une preuve de revenu à jour.',
  es='Despensas de emergencia. El sitio web del Ejército de Salvación muestra ahora dos horarios distintos (de martes a viernes 10–13 h en una página; lunes y miércoles 9–11:45, una vez cada 60 días, en otra), así que llame al 250-554-1611 antes de ir. Traiga identificación de cada persona del hogar y un comprobante de ingresos actual.',
  zh='紧急食物包。救世军自己的网站目前写着两套不同的时间（一页写周二至周五 10:00–13:00；另一页写周一、周三 9:00–11:45，每 60 天可领一次），去之前请先打 250-554-1611 确认。带上家里每个人的证件和当前的收入证明。',
  ko='긴급 식료품 꾸러미. 구세군 웹사이트에 현재 서로 다른 두 일정이 올라와 있습니다(한 페이지는 화–금 10:00–13:00, 다른 페이지는 월·수 9:00–11:45, 60일에 한 번). 가기 전에 250-554-1611로 전화해 확인하세요. 가구원 모두의 신분증과 최신 소득 증빙을 가져오세요.',
  ja='緊急食料パック。救世軍のウェブサイトには現在2つの異なる日程が載っています（あるページでは火〜金 10:00–13:00、別のページでは月・水 9:00–11:45、60日に1回）。行く前に250-554-1611に電話して確認してください。世帯全員の身分証と最新の収入証明を持参してください。')
h = next(t for t in T if t['id'] == 'hardship')
old_sa = {
 'en': 'and The Salvation Army (emergency hampers Tuesday to Friday mornings, apply before 12:30).',
 'fr': 'et The Salvation Army (paniers d’urgence du mardi au vendredi matin, demande avant 12h30).',
 'es': 'y The Salvation Army (despensas de emergencia de martes a viernes por la mañana, solicitud antes de las 12:30).',
 'zh': 'The Salvation Army（周二至周五上午发放紧急食物包，12:30前申请）。',
 'ko': 'The Salvation Army(화-금 오전 긴급 식료품 꾸러미, 12시 30분 전 신청).',
 'ja': 'The Salvation Army（火～金の午前中の緊急食料パック、12時30分までに申請）。'}
new_sa = {
 'en': 'and The Salvation Army (emergency hampers — its website shows two different schedules, so call 250-554-1611 first).',
 'fr': 'et The Salvation Army (paniers d’urgence — son site affiche deux horaires différents, appelez d’abord le 250-554-1611).',
 'es': 'y The Salvation Army (despensas de emergencia — su sitio muestra dos horarios distintos, llame antes al 250-554-1611).',
 'zh': 'The Salvation Army（紧急食物包——它的网站上有两套不同的时间，先打 250-554-1611 确认）。',
 'ko': 'The Salvation Army(긴급 식료품 꾸러미 — 웹사이트에 일정이 두 가지로 나와 있으니 먼저 250-554-1611로 전화).',
 'ja': 'The Salvation Army（緊急食料パック — サイトに2つの異なる日程があるので、先に250-554-1611へ電話を）。'}
for l in L6:
    assert h['also'][l].count(old_sa[l]) == 1, (l, h['also'][l][-120:])
    h['also'][l] = h['also'][l].replace(old_sa[l], new_sa[l])

# ---------------------------------------------------------------- hours missing whole days
# aberdeenmall.ca/about
setf('9db87af4', h={'r': [[1, 4, 600, 1080, 0], [5, 5, 600, 1200, 0], [6, 6, 600, 1080, 0], [7, 7, 660, 1020, 0]]})
# homehardware.ca/en/store/55461 ; rona.ca …/rona-kamloops-61310
setf('6c036ec5', h={'r': [[1, 5, 420, 1080, 0], [6, 6, 480, 1080, 0], [7, 7, 540, 1020, 0]]})
setf('5bbda2fd', h={'r': [[1, 5, 420, 1080, 0], [6, 6, 480, 1080, 0], [7, 7, 540, 1020, 0]]})
# planetfitness.ca/gyms/kamloops-bc
setf('61154281', h={'r': [[1, 4, 300, 1380, 0], [5, 5, 300, 1260, 0], [6, 7, 420, 1140, 0]]})
# Canada Post North Shore (in McGoo's): Saturday 9–5:30
setf('12093f3a', h={'r': [[1, 3, 540, 1050, 0], [4, 5, 540, 1140, 0], [6, 6, 540, 1050, 0], [7, 7, 720, 960, 0]]})
# tnrl.ca …/aberdeen-tiny-library/ — Saturday 12–4 (the 10–4 was a misread)
setf('c597c849', h={'r': [[2, 3, 720, 960, 0], [4, 5, 600, 1020, 0], [6, 6, 720, 960, 0], [7, 7, 720, 960, 0]]})

# ---------------------------------------------------------------- wrong phones
setf('42b06f2f', p='250-372-7797', h={'r': [[1, 5, 450, 1050, 0], [6, 6, 510, 1020, 0]]})   # windsorplywood.ca/pages/kamloops
setf('88a72602', p='250-314-0429')          # kamloops.ca …/valleyview-arena
setf('600d0f4c', p=None)                    # BC Parks lists no phone; 3311 is the City switchboard
setf('046b81d1', p='250-372-8911')          # YellowPages and GasBuddy agree
setf('e252ea96', p='250-828-3600')          # kamloops.ca event-centre page
note('e252ea96',
  en='Three ice sheets (mini, Olympic and NHL size), plus curling and family skating.',
  fr='Trois patinoires (mini, olympique et LNH), plus curling et patinage familial.',
  es='Tres pistas de hielo (mini, olímpica y de tamaño NHL), además de curling y patinaje familiar.',
  zh='三块冰场（迷你、奥运尺寸和 NHL 尺寸），另有冰壶和家庭滑冰。',
  ko='아이스링크 3면(미니, 올림픽, NHL 규격)과 컬링, 가족 스케이팅.',
  ja='リンクが3面（ミニ、オリンピック、NHLサイズ）、カーリングと家族向けスケートも。')
# theviewapartments.ca/contactus
setf('54085508', p='250-572-4043', a='955 Victoria St W')
note('54085508',
  en='A new building overlooking the Thompson River, within a five-minute drive of TRU. Quartz counters, full-size washer and dryer, rooftop patio, gym and heated garage. Studio, 1BR, 2BR and 3BR units — check the website or call for current rents.',
  fr='Immeuble neuf donnant sur la rivière Thompson, à moins de cinq minutes en voiture de TRU. Comptoirs en quartz, laveuse et sécheuse pleine grandeur, terrasse sur le toit, salle de sport et garage chauffé. Studios, 1, 2 et 3 chambres — loyers actuels sur le site ou par téléphone.',
  es='Edificio nuevo con vista al río Thompson, a menos de cinco minutos en coche de TRU. Encimeras de cuarzo, lavadora y secadora de tamaño completo, terraza en la azotea, gimnasio y garaje climatizado. Estudios y unidades de 1, 2 y 3 dormitorios — consulte el sitio o llame para saber los alquileres actuales.',
  zh='新楼，俯瞰 Thompson River，距 TRU 车程 5 分钟内。石英台面、全尺寸洗衣机和烘干机、屋顶露台、健身房、恒温车库。Studio、1BR、2BR、3BR 户型——当前租金以官网或电话为准。',
  ko='Thompson River가 내려다보이는 신축 건물로, TRU까지 차로 5분 이내입니다. 쿼츠 조리대, 풀사이즈 세탁기·건조기, 옥상 테라스, 헬스장, 난방 차고. 스튜디오, 1·2·3베드룸 — 현재 임대료는 웹사이트나 전화로 확인하세요.',
  ja='トンプソン川を見下ろす新しい建物で、TRUまで車で5分以内。クォーツのカウンター、フルサイズの洗濯機と乾燥機、屋上テラス、ジム、暖房付き車庫。スタジオ、1・2・3ベッドルーム — 現在の家賃はサイトか電話で確認を。')

# ---------------------------------------------------------------- facts
# find.shell.com station page lists Scene+; Shell Canada left Air Miles in 2026
setf('d2b51035')
note('d2b51035', en='Collects Scene+ points.', fr='Accumule des points Scène+.', es='Acumula puntos Scene+.', zh='可以攒 Scene+ 积分。', ko='Scene+ 포인트 적립.', ja='Scene+ポイントが貯まります。')
# saveonfoods.com/store-information/westsyde/2210 — no seniors hour listed
setf('04d4f0da')
note('04d4f0da',
  en='Westsyde’s only full-size supermarket, open 8 am to 9 pm daily. Pharmacy inside, and the BC Liquor store is in the same plaza, so residents up the road need not drive downtown for groceries. The More Rewards card is free — get one before your first checkout.',
  fr='Le seul grand supermarché de Westsyde, ouvert tous les jours de 8 h à 21 h. Pharmacie sur place, et le BC Liquor est dans la même plaza : pas besoin d’aller en ville pour l’épicerie. La carte More Rewards est gratuite — prenez-la avant votre premier passage en caisse.',
  es='El único supermercado grande de Westsyde, abierto todos los días de 8 a 21 h. Tiene farmacia, y la tienda BC Liquor está en la misma plaza, así que no hace falta ir al centro para hacer la compra. La tarjeta More Rewards es gratuita: sáquela antes de su primera compra.',
  zh='Westsyde 唯一的全尺寸超市，每天 8:00–21:00。店内有药房，同一小商场里有 BC Liquor，住北边的居民不必进城采购。More Rewards 会员卡免费，第一次结账前先办一张。',
  ko='Westsyde 유일의 대형 슈퍼마켓으로 매일 8:00–21:00 영업합니다. 약국이 있고 같은 상가에 BC Liquor가 있어 시내까지 장 보러 갈 필요가 없습니다. More Rewards 카드는 무료이니 첫 계산 전에 만드세요.',
  ja='Westsyde唯一の大型スーパーで、毎日8:00–21:00。店内に薬局があり、同じプラザにBC Liquorもあるので、買い物に街まで出る必要がありません。More Rewardsカードは無料なので、最初の会計の前に作りましょう。')
# cineplex.com/theatre/cineplex-cinemas-aberdeen-mall — UltraAVX, 3D, Dolby Atmos
setf('36785c07', w='https://www.cineplex.com/theatre/cineplex-cinemas-aberdeen-mall')
note('36785c07', en='UltraAVX, 3D and Dolby Atmos screens.', fr='Salles UltraAVX, 3D et Dolby Atmos.', es='Salas UltraAVX, 3D y Dolby Atmos.', zh='有 UltraAVX、3D 和杜比全景声影厅。', ko='UltraAVX, 3D, 돌비 애트모스 상영관.', ja='UltraAVX、3D、ドルビーアトモスのスクリーンあり。')
# beemcreditunion.ca — Interior Savings merged into Beem in 2024
setf('e3a1f254', n='Beem Credit Union (Valleyview)', w='https://www.beemcreditunion.ca/')
rec('e3a1f254')['alias'] = sorted(set((rec('e3a1f254').get('alias') or []) + ['Interior Savings']))
note('e3a1f254',
  en='Formerly Interior Savings — it merged into Beem Credit Union in 2024. A member-owned credit union; call to confirm current branch hours.',
  fr='Anciennement Interior Savings — fusionnée dans Beem Credit Union en 2024. Coopérative de crédit appartenant à ses membres ; appelez pour confirmer les heures de la succursale.',
  es='Antes Interior Savings — se fusionó en Beem Credit Union en 2024. Cooperativa de crédito propiedad de sus socios; llame para confirmar el horario de la sucursal.',
  zh='原 Interior Savings——2024 年并入 Beem Credit Union。会员所有的信用合作社；分行营业时间请先电话确认。',
  ko='예전 Interior Savings — 2024년 Beem Credit Union으로 합병되었습니다. 조합원 소유 신용협동조합이며, 지점 영업시간은 전화로 확인하세요.',
  ja='旧Interior Savings — 2024年にBeem Credit Unionに合併。組合員が所有する信用組合です。支店の営業時間は電話で確認を。')
# esso.ca station page: no car wash
setf('18523a8a')
note('18523a8a', en='In the Halston area.', fr='Dans le secteur Halston.', es='En la zona de Halston.', zh='在 Halston 区。', ko='Halston 지역.', ja='Halstonエリア。')
# kamloopsairport.com; Pacific Coastal flies non-stop to Victoria
setf('bad51e3f', a='101 – 3035 Airport Rd')
note('bad51e3f',
  en='The city’s airport, about 15 minutes north-west of downtown. Direct flights to Vancouver, Calgary and Victoria; most other places connect through those. The terminal is open 3 am to 12:30 am daily, with paid parking, car rental and taxis. There is no regular city bus to the terminal — plan a taxi, a lift, or the airport shuttle.',
  fr='L’aéroport de la ville, à environ 15 minutes au nord-ouest du centre. Vols directs vers Vancouver, Calgary et Victoria ; la plupart des autres destinations passent par l’une d’elles. Aérogare ouverte de 3 h à 0 h 30 tous les jours, avec stationnement payant, location de voitures et taxis. Aucun autobus urbain régulier ne dessert l’aérogare — prévoyez un taxi, quelqu’un pour vous conduire ou la navette.',
  es='El aeropuerto de la ciudad, a unos 15 minutos al noroeste del centro. Vuelos directos a Vancouver, Calgary y Victoria; casi todo lo demás conecta por ellos. La terminal abre todos los días de 3:00 a 0:30, con estacionamiento de pago, alquiler de coches y taxis. No hay autobús urbano regular a la terminal: prevea un taxi, que alguien le lleve o el servicio de enlace.',
  zh='本市机场，市中心西北约 15 分钟车程。有直飞温哥华、卡尔加里和维多利亚的航班，去其他地方大多经这几处转机。航站楼每天凌晨 3:00 开到次日 0:30；有付费停车、租车和出租车。没有常规公交到航站楼——提前安排出租车、朋友接送或机场接驳车。',
  ko='시내에서 북서쪽으로 약 15분 거리의 공항입니다. 밴쿠버, 캘거리, 빅토리아 직항이 있고, 다른 곳은 대부분 이곳들을 경유합니다. 터미널은 매일 새벽 3시부터 밤 12시 30분까지 열며 유료 주차, 렌터카, 택시가 있습니다. 터미널까지 가는 정기 시내버스는 없으니 택시, 지인 차량, 공항 셔틀을 준비하세요.',
  ja='市の空港で、ダウンタウンから北西へ車で約15分。バンクーバー、カルガリー、ビクトリアへの直行便があり、ほかの行き先はたいていそこで乗り継ぎます。ターミナルは毎日午前3時から翌0時30分まで。有料駐車場、レンタカー、タクシーあり。ターミナルへの定期市バスはないので、タクシーか送迎、空港シャトルを手配してください。')
# countryautokamloops.ca: 154 Victoria St W. Coordinates placed between the
# known 48 and 181 Victoria St W rows and marked approximate.
setf('b240c0e9', a='154 Victoria St W', g='sk', lat=50.67694, lng=-120.3429, precision='low')
# volunteerkamloops.org/contact: #7-231 Victoria St — beside 227 Victoria St
setf('507845f0', a='#7-231 Victoria St', lat=50.67565, lng=-120.3358, precision='low')
# francokamloops.org/contactez-nous: Monday to Friday 8:30–14:00
setf('04e9b0f0', h={'r': [[1, 5, 510, 840, 0]]})
note('04e9b0f0',
  en='The francophone hub of the city: adult French conversation clubs, French classes, a daycare and schooling, community events through the year, and newcomer and job support. Useful whether French is your first language or a language you are trying to keep up. Office Monday to Friday 8:30–2.',
  fr='Le carrefour francophone de la ville : clubs de conversation pour adultes, cours de français, garderie et scolarité, activités communautaires toute l’année, et soutien aux nouveaux arrivants et à l’emploi. Utile que le français soit votre langue première ou une langue que vous voulez garder. Bureau du lundi au vendredi, 8 h 30–14 h.',
  es='El centro francófono de la ciudad: clubes de conversación en francés para adultos, clases de francés, guardería y escolarización, actividades comunitarias durante todo el año, y apoyo a recién llegados y para el empleo. Útil tanto si el francés es su primera lengua como si quiere mantenerlo. Oficina de lunes a viernes, 8:30–14:00.',
  zh='本市的法语社区中心：成人法语会话俱乐部、法语课程、日托与就学、全年的社区活动，以及新到居民与就业支持。无论法语是你的母语，还是你想保持的一门语言，这里都用得上。办公室周一至周五 8:30–14:00。',
  ko='시의 프랑스어권 중심지: 성인 프랑스어 회화 모임, 프랑스어 수업, 어린이집과 학교, 연중 지역 행사, 신규 이민자·취업 지원. 프랑스어가 모국어이든 유지하고 싶은 언어이든 도움이 됩니다. 사무실 월–금 8:30–14:00.',
  ja='市のフランス語コミュニティの拠点：大人のフランス語会話クラブ、フランス語講座、保育と就学、年間を通じた地域行事、新しく来た人と就職の支援。フランス語が母語でも、維持したい言語でも役立ちます。事務所は月〜金 8:30–14:00。')
# kelsongroup.com Bonnie Lee: water + garbage included (not heat, not power)
setf('17b01a14')
note('17b01a14',
  en='Accessible entry. Studio, 1BR and 2BR units (rent via the website or by phone); water and garbage included. Near Valleyview Shopping Centre.',
  fr='Entrée accessible. Studios, 1 et 2 chambres (loyer sur le site ou par téléphone) ; eau et ordures incluses. Près du Valleyview Shopping Centre.',
  es='Entrada accesible. Estudios y unidades de 1 y 2 dormitorios (alquiler en el sitio o por teléfono); agua y basura incluidas. Cerca de Valleyview Shopping Centre.',
  zh='无障碍入口。Studio、1BR、2BR 户型（租金以官网或电话为准）；包水费和垃圾清运。靠近 Valleyview Shopping Centre。',
  ko='무장애 출입구. 스튜디오, 1·2베드룸(임대료는 웹사이트나 전화로 확인); 수도와 쓰레기 수거 포함. Valleyview Shopping Centre 근처.',
  ja='バリアフリーの入口。スタジオ、1・2ベッドルーム（家賃はサイトか電話で）。水道とゴミ収集込み。Valleyview Shopping Centreの近く。')
# kelsongroup.com Jason Adam Manor: 1, 2, 3BR; heat + water included; 55+
setf('8114d27f')
note('8114d27f',
  en='Residents must be 55+. 1BR, 2BR and 3BR units (rent via the website or by phone); heat and water included.',
  fr='Réservé aux 55 ans et plus. Logements de 1, 2 et 3 chambres (loyer sur le site ou par téléphone) ; chauffage et eau inclus.',
  es='Solo para mayores de 55 años. Unidades de 1, 2 y 3 dormitorios (alquiler en el sitio o por teléfono); calefacción y agua incluidas.',
  zh='仅限 55 岁以上入住。1BR、2BR、3BR 户型（租金以官网或电话为准）；包暖气和水费。',
  ko='55세 이상만 입주 가능. 1·2·3베드룸(임대료는 웹사이트나 전화로 확인); 난방과 수도 포함.',
  ja='入居は55歳以上のみ。1・2・3ベッドルーム（家賃はサイトか電話で）。暖房と水道込み。')

# ---------------------------------------------------------------- hours wrong on most days
# straight8barbershop.ca/north-shore-kamloops/
setf('b91cf687', w='https://straight8barbershop.ca/north-shore-kamloops/', src='official', note=None,
     h={'r': [[1, 1, 540, 1020, 0], [2, 5, 540, 1140, 0], [6, 6, 540, 1080, 0], [7, 7, 600, 1020, 0]]})
# manhandlerbarbers.com — Friday 8:30–4 was missing; its Sunday line contradicts
# its own "Monday to Friday", so Sunday is left out rather than asserted
setf('89c4efee', w='https://manhandlerbarbers.com/', src='official',
     h={'r': [[1, 4, 510, 1080, 0], [5, 5, 510, 960, 0]]})
# cuttingedgestudio.ca
setf('872c0058', p='236-313-0824', w='https://cuttingedgestudio.ca/', src='official', note=None,
     h={'r': [[1, 5, 540, 1080, 0], [6, 7, 600, 1080, 0]]})
# k-spoon.ca — Mon–Sat 11:30–20:00, closed Sunday
setf('ef8db6fb', w='https://k-spoon.ca/', src='official', h={'r': [[1, 6, 690, 1200, 0]]})
# manilasocial.ca
setf('75440a0f', w='https://manilasocial.ca/', src='official',
     h={'r': [[1, 1, 960, 1260, 0], [3, 3, 960, 1260, 0], [4, 4, 690, 1260, 0], [5, 6, 690, 1380, 0], [7, 7, 690, 1260, 0]]})
# stores.savers.com …/valuevillage-thrift-store-2051.html
setf('ca7e5fe2', w='https://stores.savers.com/bc/kamloops/valuevillage-thrift-store-2051.html',
     h={'r': [[1, 6, 540, 1260, 0], [7, 7, 600, 1140, 0]]})
# the auxiliary's own Facebook page: weekdays 10–3, Saturday 10–2
setf('8172374d', h={'r': [[1, 5, 600, 900, 0], [6, 6, 600, 840, 0]]})
# bcliquorstores.com/store/locator/147 — Friday closes at 8 pm
setf('ws00007', h={'r': [[1, 4, 570, 1140, 0], [5, 5, 570, 1200, 0], [6, 6, 570, 1140, 0], [7, 7, 660, 1080, 0]]})
note('ws00007',
  en='The BC Liquor branch in Westsyde, in the same plaza as Save-On-Foods, so residents up the road need not drive downtown. Call before a holiday.',
  fr='La succursale BC Liquor de Westsyde, dans la même plaza que Save-On-Foods : pas besoin d’aller en ville. Appelez avant un jour férié.',
  es='La sucursal de BC Liquor en Westsyde, en la misma plaza que Save-On-Foods, así que no hace falta ir al centro. Llame antes de un día festivo.',
  zh='BC Liquor 在 Westsyde 的分店，与 Save-On-Foods 同在一个小商场，北边居民买酒不必进城。节假日前请先打电话确认。',
  ko='Westsyde의 BC Liquor 지점으로 Save-On-Foods와 같은 상가에 있어 시내까지 갈 필요가 없습니다. 공휴일 전에는 전화로 확인하세요.',
  ja='WestsydeのBC Liquor店舗。Save-On-Foodsと同じプラザにあり、街まで出る必要がありません。祝日の前は電話で確認を。')
# bcwildlife.org — 9:30–4, last admission 3:30; admission is charged, so not "free"
setf('dd440908', h={'r': [[1, 7, 570, 960, 0]]}, t=[x for x in rec('dd440908')['t'] if x != 'free'])
note('dd440908',
  en='Animals, a miniature train and summer water play; a 20-minute drive. Last admission 3:30.',
  fr='Animaux, petit train et jeux d’eau en été ; à 20 minutes en voiture. Dernière entrée à 15 h 30.',
  es='Animales, un tren en miniatura y juegos de agua en verano; a 20 minutos en coche. Última entrada a las 15:30.',
  zh='动物、小火车和夏季戏水；车程 20 分钟。最晚 15:30 入园。',
  ko='동물, 미니 기차, 여름 물놀이; 차로 20분. 마지막 입장 15:30.',
  ja='動物、ミニ列車、夏の水遊び。車で20分。最終入園は15:30。')

# ---------------------------------------------------------------- unconfirmable location
# Two listings give two other addresses; the phone matches. Keep the number,
# say plainly that the address needs a call, and mark the pin approximate.
setf('362f2221', precision='low')
note('362f2221',
  en='A local tutoring centre. Listings give different addresses — call before you go.',
  fr='Centre de tutorat local. Les annuaires donnent des adresses différentes — appelez avant d’y aller.',
  es='Centro de tutorías local. Los directorios dan direcciones distintas: llame antes de ir.',
  zh='本地补习机构。不同目录上的地址不一样——去之前先打电话。',
  ko='지역 과외 센터. 목록마다 주소가 다르니 가기 전에 전화하세요.',
  ja='地元の個別指導塾。掲載によって住所が違うので、行く前に電話を。')
# Dallas dog park: the City and the listings put it in two different places
quarantine('8606c30e', 'location conflicts — the City lists the off-leash area in Dallas-Barnhartvale Nature Park (1210 Eliza Rd), listings put a separate park at 5998 Todd Hill Cres; restore after a site check')

# ---------------------------------------------------------------- unsourced claims
# Cooney Bay: no City page (the old URL 404s); access is informal; hours in no source
setf('5308dd0d', p=None, h=None)
note('5308dd0d',
  en='Pebble beach on Kamloops Lake, reached informally from the Tranquille on the Lake road-end parking. The road in can be rough at times.',
  fr='Plage de galets sur le lac Kamloops, accessible de façon informelle depuis le stationnement au bout de la route de Tranquille on the Lake. La route peut être difficile par moments.',
  es='Playa de guijarros en el lago Kamloops, a la que se llega de forma informal desde el estacionamiento al final de la carretera de Tranquille on the Lake. El camino a veces está en mal estado.',
  zh='Kamloops 湖边的卵石滩，从 Tranquille on the Lake 路尽头的停车处走非正式小路进去。进场的路有时不好走。',
  ko='Kamloops 호숫가의 자갈 해변으로, Tranquille on the Lake 도로 끝 주차장에서 비공식 길로 들어갑니다. 진입로가 험할 때가 있습니다.',
  ja='Kamloops湖の小石の浜。Tranquille on the Lakeの道路終点の駐車場から、正式ではない道で行きます。道が悪いことがあります。')
# Tranquille Market (now One Stop #502): two directories disagree on hours
setf('d7aa2f6d', h=None)
note('d7aa2f6d',
  en='Convenience store with bubble tea (Boba Boo) and ice cream. Directories disagree on hours — call if you are going late.',
  fr='Dépanneur avec bubble tea (Boba Boo) et crème glacée. Les annuaires ne s’accordent pas sur les heures — appelez si vous y allez tard.',
  es='Tienda de conveniencia con bubble tea (Boba Boo) y helado. Los directorios no coinciden en el horario: llame si va tarde.',
  zh='便利店，有珍珠奶茶（Boba Boo）和冰淇淋。各目录上的营业时间不一致——晚上去之前先打电话。',
  ko='버블티(Boba Boo)와 아이스크림이 있는 편의점. 목록마다 영업시간이 달라 늦게 갈 때는 전화하세요.',
  ja='タピオカドリンク（Boba Boo）とアイスがあるコンビニ。掲載ごとに営業時間が違うので、遅い時間は電話で確認を。')
# Ord Road: no lighting (City page lists none; residents petition for it)
setf('3ee66c48')
note('3ee66c48',
  en='A large off-leash area. No lighting — go in daylight.',
  fr='Grande aire sans laisse. Pas d’éclairage — allez-y de jour.',
  es='Zona amplia para perros sin correa. Sin iluminación: vaya de día.',
  zh='面积大的无绳遛狗区。没有照明——白天去。',
  ko='넓은 오프리시 구역. 조명이 없으니 낮에 가세요.',
  ja='広いノーリードエリア。照明はないので明るいうちに。')
# Canada Post (London Drugs): hours stored are right; the note was not
setf('0379415c')
note('0379415c',
  en='Open until 9 pm on weekdays; shorter hours at the weekend.',
  fr='Ouvert jusqu’à 21 h en semaine ; horaires plus courts le week-end.',
  es='Abierto hasta las 21 h entre semana; horario más corto el fin de semana.',
  zh='工作日开到晚上 9 点；周末营业时间较短。',
  ko='평일 21시까지 영업, 주말은 영업시간이 짧습니다.',
  ja='平日は21時まで。週末は短めの営業時間。')

# ---------------------------------------------------------------- tax card
tax = next(t for t in T if t['id'] == 'tax')
# canada.ca newcomers page: newcomers "could qualify to get these payments as
# soon as you arrive in Canada, even before you file"; CCB = RC66 + RC66SCH,
# CGEB = RC151; both need world income; temporary residents from month 19.
assert tax['why']['en'].startswith('Filing is how the benefit payments start')
tax['why'] = {
 'en': 'Newcomers can apply for the child and grocery benefits as soon as they arrive — no need to wait until you file. After that, filing every year is what keeps the payments coming, even if you owe no tax.',
 'fr': 'Les nouveaux arrivants peuvent demander les prestations pour enfants et pour l’épicerie dès leur arrivée — inutile d’attendre la déclaration. Ensuite, c’est la déclaration annuelle qui maintient les versements, même si vous ne devez aucun impôt.',
 'es': 'Los recién llegados pueden solicitar las prestaciones por hijos y para alimentos en cuanto llegan, sin esperar a declarar. Después, declarar cada año es lo que mantiene los pagos, aunque no deba impuestos.',
 'zh': '新移民一到加拿大就可以申请牛奶金和食品补助，不必等到报税。之后，每年报税才能让这些钱持续到账——即使你不欠税。',
 'ko': '신규 이민자는 도착하자마자 자녀 수당과 식료품 수당을 신청할 수 있습니다 — 세금 신고를 기다릴 필요가 없습니다. 그 후에는 내야 할 세금이 없어도 매년 신고해야 지급이 계속됩니다.',
 'ja': '新しく来た人は、到着後すぐに児童手当と食料品手当を申請できます — 確定申告を待つ必要はありません。その後は、納める税金がなくても毎年申告することで支給が続きます。'}
tax['note'] = {
 'en': 'Just arrived? Apply now: the Canada Child Benefit with form RC66 (plus schedule RC66SCH), and the Canada Groceries and Essentials Benefit with form RC151. Both ask for your income from outside Canada. Temporary residents qualify for the Canada Child Benefit from their 19th month in Canada.',
 'fr': 'Vous venez d’arriver ? Faites la demande maintenant : l’Allocation canadienne pour enfants avec le formulaire RC66 (et l’annexe RC66SCH), et la prestation canadienne pour l’épicerie et les produits essentiels avec le formulaire RC151. Les deux demandent vos revenus hors du Canada. Les résidents temporaires ont droit à l’Allocation canadienne pour enfants à partir de leur 19e mois au Canada.',
 'es': '¿Acaba de llegar? Solicítelas ya: la Canada Child Benefit con el formulario RC66 (más el anexo RC66SCH) y la Canada Groceries and Essentials Benefit con el formulario RC151. Ambas piden sus ingresos fuera de Canadá. Los residentes temporales tienen derecho a la Canada Child Benefit a partir de su mes 19 en Canadá.',
 'zh': '刚到？现在就申请：牛奶金（Canada Child Benefit）用 RC66 表（附 RC66SCH），食品与生活必需品补助（Canada Groceries and Essentials Benefit）用 RC151 表。两份表都要填你在加拿大境外的收入。临时居民从在加拿大的第 19 个月起才能领牛奶金。',
 'ko': '막 도착했나요? 지금 신청하세요: 캐나다 자녀 수당(Canada Child Benefit)은 RC66 양식(RC66SCH 첨부), 식료품·생활필수품 수당(Canada Groceries and Essentials Benefit)은 RC151 양식입니다. 두 양식 모두 캐나다 밖에서 번 소득을 적어야 합니다. 임시 거주자는 캐나다 체류 19개월째부터 자녀 수당을 받을 수 있습니다.',
 'ja': '来たばかりですか？今すぐ申請を：カナダ児童手当（Canada Child Benefit）はRC66（RC66SCH添付）、食料品・生活必需品手当（Canada Groceries and Essentials Benefit）はRC151で申請します。どちらもカナダ国外での収入を記入します。一時滞在者はカナダ滞在19か月目から児童手当の対象になります。'}

kamdata.save('P', P)
kamdata.save('QUARANTINE', Q)
kamdata.save('TASKS', T)
print('phase 2 place fixes: %d records touched' % len(set(done)))

# (applied after the first run) the hardship card listed Pathways with the
# ASK Wellness office number too — all six languages
_s = open('src/data-kamloops.js', encoding='utf-8').read()
if 'Pathways Shelter and Access Hub 250-376-7558' in _s:
    _s = _s.replace('Pathways Shelter and Access Hub 250-376-7558', 'Pathways Shelter and Access Hub 250-299-7936')
    open('src/data-kamloops.js', 'w', encoding='utf-8').write(_s)

# (second pass) "no hours" read as missing data; these two have hours that
# the sources disagree on, which is what hCall says: call ahead to confirm.
_P = kamdata.load('P')
for _p in _P:
    if _p['id'] in ('df64d05e', 'd7aa2f6d') and 'h' not in _p:
        _p['h'] = {'k': 'hCall'}
kamdata.save('P', _P)
