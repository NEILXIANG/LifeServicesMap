#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write the verified hardship and community places into src/data-kamloops.js.

Every row here came out of a sourced research pass (2026-09-09) and a separate
geocoding pass (2026-09-10); nothing is estimated. Where a coordinate is only
good to the block rather than the doorstep it carries precision:'low', which is
what the popup reads to warn the reader before they walk somewhere.

Two corrections travel with the additions:
  · The Mustard Seed at 181 Victoria St W was 250 m north-east of the building.
  · Lizzy's Closet closed in May 2026 and became Rise & Renew — it was never in
    this dataset, so there is nothing to remove, but the replacement is added.
"""
import io, json, re, hashlib

SRC = 'src/data-kamloops.js'
s = io.open(SRC, encoding='utf-8').read()
P = json.loads(re.search(r'const P=(\[.*?\]);', s, re.S).group(1))
by_addr = {}
for p in P:
    by_addr.setdefault((p.get('a') or '').lower(), []).append(p)

def pid(name, addr):
    """Same shape of id as every other row: a short stable hash."""
    return hashlib.sha1((name + '|' + addr).encode('utf-8')).hexdigest()[:8]

def hrs(*ranges):
    return {'r': [list(r) for r in ranges]}

M = lambda h, m=0: h * 60 + m

NEW = [
 # ---------------------------------------------------------------- food ----
 dict(n='Mount Paul Community Food Centre', c='foodbank', g='ns',
      lat=50.68876, lng=-120.35554, a='140 Laburnum St', p='236-421-1011',
      w='https://www.mountpaulcommunityfoodcentre.com', t=['free'],
      h=hrs((1,5,M(8,30),M(16),0)),
      alias=['免费吃饭','社区厨房','食物','무료 식사','무료급식','食事','repas gratuit','comida gratis'],
      note=dict(
       en='Free community meals, Mondays and Thursdays 12-1pm, and everyone is eligible — you are not asked to prove anything. Also an affordable produce market (Tue and Thu 10-2), a free sharing table of surplus vegetables during market hours, and discounted produce boxes.',
       fr='Repas communautaires gratuits, les lundis et jeudis de 12h a 13h, ouverts a tous — on ne vous demande rien a prouver. Aussi un marche de fruits et legumes abordables (mar. et jeu. 10h-14h), une table de partage gratuite pendant le marche, et des paniers de fruits et legumes a prix reduit.',
       es='Comidas comunitarias gratuitas, lunes y jueves de 12 a 13h, y todo el mundo puede participar — no le piden demostrar nada. Ademas un mercado de verduras asequible (mar. y jue. 10-14h), una mesa gratuita de excedentes durante el mercado, y cajas de fruta y verdura a precio reducido.',
       zh='免费社区午餐，周一和周四 12:00–13:00，任何人都可以来吃，不需要证明什么。另有平价果蔬市集（周二、周四 10:00–14:00）、市集时段免费取用的富余蔬菜台，以及低于成本价的果蔬箱。',
       ko='무료 커뮤니티 식사, 월요일과 목요일 12-13시. 누구나 참여할 수 있고 무엇을 증명할 필요도 없습니다. 저렴한 농산물 마켓(화·목 10-14시), 마켓 시간 중 무료로 가져갈 수 있는 나눔 테이블, 값보다 훨씬 싼 농산물 박스도 있습니다.',
       ja='無料のコミュニティ食事、月曜と木曜の12〜13時。誰でも参加でき、何かを証明する必要はありません。手頃な価格の青果マーケット（火・木10〜14時）、マーケット時間中に無料で持ち帰れるシェアテーブル、値段より価値のある割安な青果ボックスもあります。')),

 dict(n='The Salvation Army Community Services', c='foodbank', g='ns',
      lat=50.69341, lng=-120.36352, a='344 Poplar St', p='250-554-1611',
      w='https://www.kamloopssalvationarmy.ca/community-services/', t=['free'],
      h=hrs((2,5,M(10),M(13),0)),
      alias=['救世军','食物','紧急','구세군','救世軍','urgence','emergencia'],
      note=dict(
       en='Emergency food hampers, Tuesday to Friday 10am-1pm — hamper applications close at 12:30, so arrive before noon. Bring current proof of income. Also thrift store vouchers for clothing and household goods, bus tickets, diapers and formula, and hot meals from the mobile kitchen at St Paul St and 4th Ave, Tuesdays and Thursdays 6-7pm.',
       fr='Paniers alimentaires d\'urgence, du mardi au vendredi de 10h a 13h — les demandes ferment a 12h30, arrivez donc avant midi. Apportez une preuve de revenu a jour. Aussi des bons pour la friperie, des billets d\'autobus, des couches et du lait maternise, et des repas chauds de la cuisine mobile a St Paul St et 4th Ave, mardi et jeudi 18h-19h.',
       es='Despensas de emergencia, de martes a viernes de 10 a 13h — las solicitudes cierran a las 12:30, llegue antes del mediodia. Traiga comprobante de ingresos actual. Ademas vales para la tienda de segunda mano, boletos de autobus, panales y formula, y comidas calientes de la cocina movil en St Paul St y 4th Ave, martes y jueves de 18 a 19h.',
       zh='紧急食物包，周二至周五 10:00–13:00——申请 12:30 截止，请在中午前到。需带当前收入证明。另提供二手店代金券（衣物与家居用品）、公交票、尿布与奶粉，以及流动厨房的热食（St Paul St 与 4th Ave 路口，周二、周四 18:00–19:00）。',
       ko='긴급 식료품 꾸러미, 화요일부터 금요일 10-13시 — 신청은 12시 30분에 마감되니 정오 전에 도착하세요. 최신 소득 증빙을 가져오세요. 중고매장 바우처(의류·생활용품), 버스 티켓, 기저귀와 분유, 그리고 St Paul St와 4th Ave 교차로의 이동식 주방 따뜻한 식사(화·목 18-19시)도 있습니다.',
       ja='緊急食料パック、火曜から金曜の10〜13時 — 申請は12時30分締切なので正午前に到着してください。最新の収入証明をお持ちください。古着店のバウチャー（衣類・生活用品）、バス券、おむつと粉ミルク、St Paul StとFourth Aveの移動式キッチンの温かい食事（火・木18〜19時）もあります。')),

 # --------------------------------------------------------------- legal ----
 dict(n='TRU Community Legal Clinic', c='legal', g='sk',
      lat=50.67452, lng=-120.33676, a='235 1st Ave #601', p='778-471-8490',
      w='https://www.tru.ca/law/students/outreach/legal-clinic.html', t=['free'],
      h=hrs((1,5,M(9),M(16),0)),
      alias=['免费律师','法律','法律援助','무료 법률','법률상담','法律相談','aide juridique','ayuda legal'],
      note=dict(
       en='Free legal help for people who cannot afford a lawyer: tenancy, employment standards, small claims up to the provincial limit, human rights, wills and powers of attorney. Appointment only, no drop-ins. Open weekdays 9-4 but only while TRU classes are running, so it can be closed over the winter break and in summer — phone first.',
       fr='Aide juridique gratuite pour les personnes sans moyens : logement, normes du travail, petites creances jusqu\'au plafond provincial, droits de la personne, testaments et procurations. Sur rendez-vous seulement. Ouvert en semaine 9h-16h, mais uniquement pendant les cours a TRU — donc parfois ferme l\'hiver et l\'ete. Telephonez d\'abord.',
       es='Ayuda legal gratuita para quien no puede pagar un abogado: arrendamiento, normas laborales, demandas menores hasta el limite provincial, derechos humanos, testamentos y poderes. Solo con cita previa. Abierto entre semana de 9 a 16h, pero solo mientras hay clases en TRU — puede estar cerrado en invierno y verano. Llame primero.',
       zh='为请不起律师的人提供免费法律帮助：租房、劳动标准、省定限额以内的小额索赔、人权、遗嘱与授权书。**只接受预约，不接待临时来访**。工作日 9:00–16:00，但仅在 TRU 上课期间开放，寒暑假可能关闭——请先打电话。',
       ko='변호사를 선임할 여력이 없는 사람을 위한 무료 법률 지원: 임대차, 근로기준, 주 기준 한도 이내의 소액청구, 인권, 유언장과 위임장. 예약제이며 방문 접수는 받지 않습니다. 평일 9-16시이지만 TRU 학기 중에만 운영되어 겨울방학과 여름에는 닫힐 수 있으니 먼저 전화하세요.',
       ja='弁護士を雇う余裕がない人のための無料法律支援: 賃貸、労働基準、州の上限までの少額請求、人権、遺言と委任状。予約制で、飛び込みは受け付けていません。平日9〜16時ですが、TRUの授業期間中のみの運営で、冬休みや夏は閉まることがあります。まず電話してください。')),

 dict(n='Kamloops Family Justice Centre', c='legal', g='sk',
      lat=50.67633, lng=-120.33779, a='150 Victoria St #205', p='250-828-4688',
      w='https://www2.gov.bc.ca/gov/content/life-events/divorce/family-justice/who-can-help/family-justice-services-division/family-justice-centres', t=['free'], precision='low',
      h=hrs((2,4,M(8,30),M(16,50),0)),
      alias=['家庭','抚养','离婚','监护','가족','양육비','이혼','家族','養育費','famille','familia'],
      note=dict(
       en='Free provincial service for family matters: parenting arrangements, guardianship, child and spousal support, contact with a child. Legal information and help reaching an agreement without going to court. In person Tuesday to Thursday 8:30-4:50; by phone or video Monday to Friday. Everything here is free of charge.',
       fr='Service provincial gratuit pour les questions familiales : arrangements parentaux, tutelle, pension alimentaire pour enfants et epoux, contact avec un enfant. Information juridique et aide pour s\'entendre sans aller au tribunal. Sur place du mardi au jeudi 8h30-16h50; par telephone ou video du lundi au vendredi. Tout y est gratuit.',
       es='Servicio provincial gratuito para asuntos familiares: acuerdos de crianza, tutela, manutencion de hijos y conyuge, contacto con un hijo. Informacion legal y ayuda para llegar a un acuerdo sin ir a juicio. Presencial de martes a jueves de 8:30 a 16:50; por telefono o video de lunes a viernes. Todo es gratuito.',
       zh='省政府提供的免费家事服务：抚养安排、监护权、子女与配偶抚养费、探视。提供法律信息，并帮助双方在不上法庭的情况下达成协议。周二至周四 8:30–16:50 现场办理；周一至周五可电话或视频。全部免费。',
       ko='가족 문제를 위한 주정부 무료 서비스: 양육 계획, 후견, 자녀·배우자 부양비, 자녀 면접교섭. 법률 정보를 제공하고 법정에 가지 않고 합의에 이르도록 돕습니다. 대면은 화-목 8:30-16:50, 전화나 화상은 월-금. 모두 무료입니다.',
       ja='家族の問題のための州の無料サービス: 養育の取り決め、後見、子と配偶者の扶養、子との面会。法的情報を提供し、裁判に行かずに合意に至る手助けをします。対面は火〜木の8時30分〜16時50分、電話やビデオは月〜金。すべて無料です。')),

 dict(n='Kamloops & District Elizabeth Fry Society', c='support', g='sk',
      lat=50.67473, lng=-120.32066, a='827 Seymour St', p='250-374-2119',
      w='https://kamloopsefry.com/', t=['free'],
      h=hrs((1,5,M(9),M(16),0)),
      alias=['房租','押金','法庭','无息贷款','월세','보증금','법정','家賃','敷金','loyer','alquiler'],
      note=dict(
       en='Two things worth knowing here. The Kamloops Rent Bank gives interest-free loans for rent, a damage deposit or a utility bill when an unexpected emergency threatens your housing — for anyone on a low or moderate income across the region, not just the city. And the Courtwork programme connects you with duty counsel if you have a court date, explains the procedure, helps with the paperwork, and can even lend you clothes for court. Weekdays 9-4, closed 12-12:30.',
       fr='Deux choses a savoir. La banque de loyer offre des prets sans interet pour le loyer, un depot de garantie ou une facture de services publics quand une urgence imprevue menace votre logement — pour tout revenu faible ou modeste de la region. Et le programme Courtwork vous met en lien avec un avocat de service si vous avez une date de cour, explique la procedure, aide avec les papiers, et peut meme vous preter des vetements. En semaine 9h-16h, ferme 12h-12h30.',
       es='Dos cosas que conviene saber. El banco de alquiler da prestamos sin intereses para el alquiler, un deposito o una factura de servicios cuando una emergencia imprevista amenaza su vivienda — para cualquier ingreso bajo o moderado de la region. Y el programa Courtwork le conecta con un abogado de guardia si tiene una fecha judicial, le explica el procedimiento, ayuda con los papeles e incluso puede prestarle ropa. Entre semana 9-16h, cerrado 12-12:30.',
       zh='这里有两件事值得知道。**租金银行**为遇到突发状况、住房受到威胁的人提供**无息贷款**，可用于房租、押金或水电费——面向本地区所有中低收入者，不限于市内。**法庭陪同项目**则会在你有开庭日期时帮你联系值班律师、讲清流程、协助文件，甚至可以借给你上庭穿的衣服。工作日 9:00–16:00，12:00–12:30 午休。',
       ko='여기서 알아둘 것이 두 가지입니다. 렌트뱅크는 예기치 못한 위기로 주거가 위태로울 때 월세, 보증금, 공과금에 쓸 수 있는 무이자 대출을 제공합니다 — 시내뿐 아니라 지역 전체의 중·저소득층이 대상입니다. 그리고 법정 동행 프로그램은 재판 날짜가 있을 때 당직 변호사를 연결하고 절차를 설명하며 서류를 돕고, 법정에 입고 갈 옷까지 빌려줍니다. 평일 9-16시, 12-12시 30분 휴게.',
       ja='ここで知っておくとよいことが二つあります。レントバンクは、予期せぬ出来事で住まいが危うくなったときに、家賃・敷金・光熱費に使える無利子の融資を行います — 市内に限らず地域全体の中低所得者が対象です。そして法廷同行プログラムは、出廷日がある場合に当番弁護士につなぎ、手続きを説明し、書類を手伝い、法廷で着る服まで貸してくれます。平日9〜16時、12時〜12時30分は休憩。')),

 # --------------------------------------------------------------- money ----
 dict(n='BC Employment and Assistance (Income Assistance)', c='gov', g='sk',
      lat=50.67464, lng=-120.32581, a='631 Seymour St', p='1-866-866-0800',
      w='https://www.myselfserve.gov.bc.ca', precision='low',
      h=hrs((1,5,M(9),M(12),0),(1,5,M(13),M(16),0)),
      alias=['低保','救济金','失业','残疾补助','생활보호','기초생활','실업','生活保護','失業','aide sociale','asistencia'],
      note=dict(
       en='Where to apply for income assistance or disability assistance if you are out of work, underemployed, waiting on other income, or unable to work. Open weekdays 9-12 and 1-4 — closed over lunch. Most of the application is done online at myselfserve.gov.bc.ca; this office is for the parts that need a person. The street address here comes from a directory rather than a government page, so phone before making a special trip.',
       fr='Ou demander l\'aide au revenu ou l\'aide aux personnes handicapees si vous etes sans emploi, sous-employe, en attente d\'un autre revenu ou inapte au travail. Ouvert en semaine 9h-12h et 13h-16h — ferme le midi. L\'essentiel de la demande se fait en ligne; ce bureau sert aux etapes qui exigent une personne. L\'adresse vient d\'un annuaire et non d\'une page gouvernementale : telephonez avant de vous deplacer.',
       es='Donde solicitar asistencia de ingresos o por discapacidad si esta sin trabajo, subempleado, esperando otro ingreso o no puede trabajar. Abierto entre semana de 9 a 12 y de 13 a 16 — cerrado al mediodia. La mayor parte se hace en linea; esta oficina es para lo que requiere una persona. La direccion proviene de un directorio y no de una pagina oficial: llame antes de ir.',
       zh='申请低保（income assistance）或残疾补助的地方，适用于失业、就业不足、等待其他收入或无法工作的人。工作日 9:00–12:00、13:00–16:00 开放，**中午休息**。大部分申请在 myselfserve.gov.bc.ca 线上完成，这个办公室处理必须当面办的部分。此处地址来自第三方目录而非政府页面，**专程前往前请先致电确认**。',
       ko='실직·불완전 취업·다른 소득 대기·근로 불가 상태일 때 생계급여나 장애급여를 신청하는 곳입니다. 평일 9-12시, 13-16시 — 점심시간에는 닫습니다. 신청의 대부분은 온라인으로 하며, 이 사무실은 사람이 필요한 절차를 위한 곳입니다. 주소가 정부 페이지가 아닌 디렉터리에서 온 것이므로 일부러 가기 전에 전화하세요.',
       ja='失業中、就業が不十分、他の収入を待っている、または働けない場合に、所得支援や障害者支援を申請する場所です。平日9〜12時と13〜16時 — 昼は閉まります。申請の大部分はオンラインででき、この事務所は人が必要な手続きのためのものです。住所が政府ページではなくディレクトリ由来なので、わざわざ出向く前に電話してください。')),

 # ------------------------------------------------------------- shelter ----
 dict(n='The Mustard Seed West End Shelter', c='support', g='sk',
      lat=50.67698, lng=-120.34365, a='181 Victoria St W', p='250-372-9890',
      w='https://theseed.ca/emergency-shelter', t=['free'],
      h={'a': True},
      alias=['庇护所','收容','没地方住','쉼터','노숙','シェルター','refuge','albergue'],
      note=dict(
       en='Emergency shelter, 20 beds, men and women, open 24 hours a day. Food, clothing, hot showers, hygiene supplies, and help getting to counselling, health care and advocacy. There is also a separate 12-bed wellness space for women, Women\'s Harbour House, at the same address — call 825-401-2870 for that one.',
       fr='Refuge d\'urgence, 20 lits, hommes et femmes, ouvert 24 heures sur 24. Nourriture, vetements, douches chaudes, produits d\'hygiene, et aide pour acceder au counseling, aux soins et a la defense des droits. Il y a aussi un espace distinct de 12 lits pour les femmes, Women\'s Harbour House, a la meme adresse — appelez le 825-401-2870.',
       es='Albergue de emergencia, 20 camas, hombres y mujeres, abierto las 24 horas. Comida, ropa, duchas calientes, articulos de higiene y ayuda para acceder a consejeria, atencion medica y defensa. Tambien hay un espacio aparte de 12 camas para mujeres, Women\'s Harbour House, en la misma direccion — llame al 825-401-2870.',
       zh='紧急庇护所，20 张床位，男女皆可，24 小时开放。提供食物、衣物、热水淋浴、卫生用品，并协助你接上心理咨询、医疗与权益倡导。同一地址还有面向女性的 12 床位空间 Women\'s Harbour House，电话 825-401-2870。',
       ko='24시간 운영하는 응급 쉼터로 남녀 20병상. 음식, 의류, 따뜻한 샤워, 위생용품을 제공하고 상담·의료·권익 옹호로 연결해 줍니다. 같은 주소에 여성을 위한 12병상 공간 Women\'s Harbour House도 있습니다 — 825-401-2870으로 전화하세요.',
       ja='24時間開いている緊急シェルター、男女20床。食事、衣類、温かいシャワー、衛生用品を提供し、カウンセリング・医療・権利擁護につなぎます。同じ住所に女性のための12床のWomen\'s Harbour Houseもあります — 825-401-2870へ。')),

 dict(n='Pathways Shelter and Access Hub', c='support', g='ns',
      lat=50.68481, lng=-120.35349, a='142 Tranquille Rd', p='250-376-7558',
      w='https://askwellness.ca/streets/', t=['free'],
      h={'a': True},
      alias=['庇护所','收容','洗澡','没地方住','쉼터','샤워','シェルター','シャワー','refuge','albergue'],
      note=dict(
       en='A 44-bed low-barrier emergency shelter on the North Shore, open 24 hours. Meals, washrooms and showers, somewhere to store your belongings, cultural programming, help setting goals, and access to a mobile health clinic. Low-barrier means you are not turned away for being intoxicated or having nothing with you.',
       fr='Refuge d\'urgence a bas seuil de 44 lits sur la rive nord, ouvert 24 heures. Repas, toilettes et douches, un endroit ou ranger vos affaires, programmes culturels, aide a se fixer des objectifs, et acces a une clinique mobile. Bas seuil veut dire qu\'on ne vous refuse pas parce que vous avez bu ou que vous n\'avez rien sur vous.',
       es='Albergue de emergencia de bajo umbral con 44 camas en la ribera norte, abierto 24 horas. Comidas, banos y duchas, un lugar para guardar sus cosas, programacion cultural, ayuda para fijar metas y acceso a una clinica movil. Bajo umbral significa que no se le rechaza por estar intoxicado o no llevar nada.',
       zh='北岸的 44 床位低门槛紧急庇护所，24 小时开放。提供餐食、洗手间与淋浴、存放随身物品的地方、文化活动、目标规划协助，以及流动医疗诊所。"低门槛"的意思是：不会因为你喝了酒或身上什么都没有就把你拒之门外。',
       ko='노스쇼어에 있는 44병상 저문턱 응급 쉼터로 24시간 운영합니다. 식사, 화장실과 샤워, 소지품 보관, 문화 프로그램, 목표 설정 지원, 이동 진료소 이용이 가능합니다. 저문턱이란 술을 마셨거나 아무것도 없이 왔다고 해서 돌려보내지 않는다는 뜻입니다.',
       ja='ノースショアにある44床のローバリア緊急シェルターで、24時間開いています。食事、トイレとシャワー、荷物を置く場所、文化プログラム、目標設定の支援、移動診療所の利用ができます。ローバリアとは、酔っていても何も持っていなくても追い返さない、という意味です。')),

 dict(n='Emerald Centre', c='support', g='sk',
      lat=50.67767, lng=-120.34588, a='271 Victoria St W', p='250-372-3031',
      w='https://kamloops.cmha.bc.ca/programs/homeless-shelter/', t=['free'],
      h={'a': True}, precision='low',
      alias=['庇护所','收容','没地方住','쉼터','노숙','シェルター','refuge','albergue'],
      note=dict(
       en='A 42-bed low-barrier shelter for women and men, open every day of the year. Shelter and meals, support workers, case management, and mental health and housing services brought in on site. Please phone before you set out: the operator\'s own website prints its head-office address on this page, and the address here is the one two other sources give.',
       fr='Refuge a bas seuil de 42 lits pour femmes et hommes, ouvert tous les jours de l\'annee. Hebergement et repas, intervenants, gestion de cas, et services de sante mentale et de logement offerts sur place. Telephonez avant de partir : le site de l\'organisme affiche l\'adresse de son siege sur cette page, et l\'adresse indiquee ici est celle que donnent deux autres sources.',
       es='Albergue de bajo umbral con 42 camas para mujeres y hombres, abierto todos los dias del ano. Alojamiento y comidas, trabajadores de apoyo, gestion de casos y servicios de salud mental y vivienda en el lugar. Llame antes de salir: el sitio del operador publica la direccion de su sede en esa pagina, y la direccion de aqui es la que dan otras dos fuentes.',
       zh='42 床位低门槛庇护所，男女皆可，全年无休。提供住宿与餐食、支持人员、个案管理，以及上门提供的心理健康与住房服务。**出发前请先打电话**：运营方自己的网页在这一页上印的是总部地址，此处采用的是另外两个来源一致给出的地址。',
       ko='여성과 남성을 위한 42병상 저문턱 쉼터로 연중무휴입니다. 숙소와 식사, 지원 인력, 사례관리, 현장에서 제공되는 정신건강·주거 서비스가 있습니다. 출발 전에 전화하세요: 운영기관 웹사이트가 이 페이지에 본부 주소를 표시하고 있어, 여기 주소는 다른 두 출처가 일치하게 제시한 것입니다.',
       ja='女性と男性のための42床のローバリアシェルターで、年中無休です。宿泊と食事、支援員、ケースマネジメント、現地で提供される精神保健・住居サービスがあります。出かける前に電話してください: 運営団体のサイトはこのページに本部の住所を載せており、ここの住所は他の二つの情報源が一致して示すものです。')),

 dict(n='Merit Place Shelter', c='support', g='sa',
      lat=50.66321, lng=-120.35651, a='725 Notre Dame Dr', p='236-425-0341',
      w='https://kamloops.cmha.bc.ca/', t=['free'],
      h={'a': True}, precision='low',
      alias=['庇护所','收容','宠物','没地方住','쉼터','반려동물','シェルター','ペット','refuge','albergue'],
      note=dict(
       en='Year-round low-barrier shelter, 49 adults of any gender, in individual pods rather than an open dormitory. Meals, laundry, nursing and wound care, medication management, case management, an overdose prevention site, and bicycle storage. One pet is allowed, which is the reason some people can come here and nowhere else. No maximum length of stay.',
       fr='Refuge a bas seuil toute l\'annee, 49 adultes de tout genre, en modules individuels plutot qu\'en dortoir. Repas, buanderie, soins infirmiers et soins des plaies, gestion des medicaments, gestion de cas, site de prevention des surdoses, rangement pour velos. Un animal de compagnie est admis — c\'est la raison pour laquelle certaines personnes ne peuvent aller que la. Aucune duree maximale de sejour.',
       es='Albergue de bajo umbral todo el ano, 49 adultos de cualquier genero, en modulos individuales en vez de un dormitorio abierto. Comidas, lavanderia, enfermeria y curacion de heridas, manejo de medicamentos, gestion de casos, sitio de prevencion de sobredosis y guarda de bicicletas. Se admite una mascota, que es la razon por la que algunas personas solo pueden venir aqui. Sin estancia maxima.',
       zh='全年开放的低门槛庇护所，49 名成年人（不限性别），住的是**独立隔间**而非通铺。提供餐食、洗衣、护理与伤口处理、药物管理、个案管理、防过量站点，以及自行车存放。**允许带一只宠物**——这正是有些人只能来这里的原因。没有最长入住期限。',
       ko='연중 운영하는 저문턱 쉼터로 성별 무관 성인 49명, 개방형 숙소가 아닌 개별 포드입니다. 식사, 세탁, 간호와 상처 치료, 약물 관리, 사례관리, 과다복용 예방 시설, 자전거 보관이 있습니다. 반려동물 한 마리를 데려올 수 있는데, 그래서 여기밖에 갈 수 없는 사람들이 있습니다. 최대 체류 기간은 없습니다.',
       ja='通年のローバリアシェルター、性別を問わない成人49名、大部屋ではなく個別のポッドです。食事、洗濯、看護と創傷ケア、服薬管理、ケースマネジメント、過量摂取予防拠点、自転車置き場があります。ペット1匹を connect できるため、ここにしか来られない人がいます。滞在期間の上限はありません。')),

 # ----------------------------------------------------------- practical ----
 dict(n='KAFS Mini Storage (showers, laundry, mail)', c='support', g='sk',
      lat=50.67678, lng=-120.33989, a='48 Victoria St W', p='778-220-8059',
      w='https://kafs.ca/programs-services/mini-storage-units/', t=['free'],
      h=hrs((1,6,M(10),M(17),0)),
      alias=['洗澡','淋浴','洗衣','收信','地址','샤워','세탁','우편','シャワー','洗濯','郵便','douche','ducha'],
      note=dict(
       en='Showers, public washrooms and laundry, six days a week — and, quietly the most important part, you can receive mail here using this address. Almost every application for ID, income assistance or housing needs somewhere to send the letter, and this is that somewhere. Also safe storage for your belongings (up to 50 lb in clear bags, checked weekly), meals and referrals. Monday to Saturday 10-5.',
       fr='Douches, toilettes publiques et buanderie, six jours par semaine — et, discretement le plus important, vous pouvez recevoir votre courrier ici en utilisant cette adresse. Presque toute demande de piece d\'identite, d\'aide au revenu ou de logement exige une adresse ou envoyer la lettre, et c\'est celle-la. Aussi rangement sur pour vos affaires (jusqu\'a 50 lb en sacs transparents, verifies chaque semaine), repas et references. Du lundi au samedi 10h-17h.',
       es='Duchas, banos publicos y lavanderia, seis dias a la semana — y, sin hacer ruido, lo mas importante: puede recibir correo aqui usando esta direccion. Casi toda solicitud de identificacion, asistencia o vivienda necesita un lugar al que enviar la carta, y este es ese lugar. Ademas guarda segura de sus pertenencias (hasta 50 lb en bolsas transparentes, revisadas semanalmente), comidas y derivaciones. De lunes a sabado de 10 a 17h.',
       zh='淋浴、公共洗手间与洗衣，每周六天——还有一件低调但最要紧的事：**你可以用这个地址收信**。办身份证件、申请低保或住房，几乎每一项都需要一个能收信的地址，而这里就是那个地址。另提供随身物品的安全寄存（透明袋装、不超过 50 磅、每周需查看一次）、餐食与转介。周一至周六 10:00–17:00。',
       ko='샤워, 공중화장실, 세탁을 주 6일 이용할 수 있고 — 조용하지만 가장 중요한 것은, 이 주소로 우편을 받을 수 있다는 점입니다. 신분증, 생계급여, 주거 신청은 거의 모두 편지를 보낼 주소를 요구하는데, 여기가 바로 그 주소입니다. 소지품 안전 보관(투명 봉투에 50파운드까지, 주 1회 확인), 식사와 연계도 있습니다. 월-토 10-17시.',
       ja='シャワー、公衆トイレ、洗濯が週6日利用でき — そして目立たないながら最も重要なのは、この住所で郵便を受け取れることです。身分証、生活支援、住居の申請はほぼすべて手紙の送り先を必要とし、ここがその送り先になります。持ち物の安全な保管（透明の袋で50ポンドまで、週1回の確認が必要）、食事、紹介もあります。月〜土10〜17時。')),

 dict(n='Rise & Renew Thrift Store', c='secondhand', g='ns',
      lat=50.68507, lng=-120.35467, a='178 Tranquille Rd', p='250-374-2119',
      w='https://kamloopsefry.com/rise-renew-thrift-store-kamloops/', t=['free'],
      h=hrs((2,6,M(10),M(16),0)),
      alias=['二手','衣服','免费衣服','중고','옷','무료 옷','古着','服','friperie','ropa'],
      note=dict(
       en='A thrift store, and also a place where a woman in financial hardship can take clothing and essentials free, with no paperwork — a small basket of items at a time, generally four times a year, more at staff discretion. Just ask at the counter. Tuesday to Saturday 10-4. (This replaced Lizzy\'s Closet, which closed in May 2026.)',
       fr='Une friperie, et aussi un endroit ou une femme en difficulte financiere peut prendre des vetements et des articles essentiels gratuitement, sans paperasse — un petit panier a la fois, generalement quatre fois par an, davantage a la discretion du personnel. Il suffit de demander au comptoir. Du mardi au samedi 10h-16h. (Remplace Lizzy\'s Closet, ferme en mai 2026.)',
       es='Una tienda de segunda mano, y tambien un lugar donde una mujer en dificultad economica puede llevarse ropa y articulos esenciales gratis, sin papeleo — una pequena cesta de articulos por vez, en general cuatro veces al ano, mas a criterio del personal. Solo pregunte en el mostrador. De martes a sabado de 10 a 16h. (Sustituyo a Lizzy\'s Closet, cerrada en mayo de 2026.)',
       zh='一家二手店，同时也是**处于经济困难中的女性可以免费拿走衣物与生活必需品**的地方，不需要任何证明——每次可拿一小篮，通常一年四次，工作人员可酌情放宽。到柜台说一声即可。周二至周六 10:00–16:00。（它取代了 2026 年 5 月关闭的 Lizzy\'s Closet。）',
       ko='중고매장이자, 경제적으로 어려운 여성이 서류 없이 의류와 생필품을 무료로 가져갈 수 있는 곳입니다 — 한 번에 작은 바구니 하나 정도, 보통 연 4회이며 직원 재량으로 더 받을 수도 있습니다. 카운터에서 말씀하시면 됩니다. 화-토 10-16시. (2026년 5월 문을 닫은 Lizzy\'s Closet을 대신합니다.)',
       ja='古着店であり、経済的に困っている女性が書類なしで衣類や生活必需品を無料で持ち帰れる場所でもあります — 一度に小さなかご一杯まで、通常は年4回、スタッフの判断でそれ以上も。カウンターで声をかけるだけです。火〜土10〜16時。（2026年5月に閉店したLizzy\'s Closetの後継です。）')),

 dict(n='ASK Wellness Society', c='support', g='ns',
      lat=50.69080, lng=-120.35920, a='433 Tranquille Rd', p='250-376-7558',
      w='https://askwellness.ca/', t=['free'],
      h=hrs((1,5,M(8,30),M(16,30),0)),
      alias=['找房','住房','帮助','주거','도움','住まい','支援','logement','vivienda'],
      note=dict(
       en='Housing-first support for people who are homeless or close to it: help finding a place, securing it, and keeping it. Also street outreach, harm reduction, health navigation, mental health and disability support, and employment services. Weekdays 8:30-4:30, closed weekends — for a bed tonight, go to the Pathways shelter on Tranquille Rd instead, which is open around the clock.',
       fr='Soutien logement d\'abord pour les personnes sans domicile ou pres de l\'etre : aide a trouver un logement, a l\'obtenir et a le garder. Aussi travail de rue, reduction des mefaits, navigation en sante, soutien en sante mentale et en situation de handicap, et services d\'emploi. En semaine 8h30-16h30, ferme la fin de semaine — pour un lit ce soir, allez plutot au refuge Pathways sur Tranquille Rd, ouvert jour et nuit.',
       es='Apoyo de vivienda primero para personas sin hogar o a punto de estarlo: ayuda para encontrar un lugar, conseguirlo y conservarlo. Ademas trabajo de calle, reduccion de danos, navegacion en salud, apoyo en salud mental y discapacidad, y servicios de empleo. Entre semana de 8:30 a 16:30, cerrado los fines de semana — para una cama esta noche, vaya al albergue Pathways en Tranquille Rd, abierto las 24 horas.',
       zh='"住房优先"支持，面向无家可归或濒临无家可归的人：帮你找房、拿到房、并住得下去。另有街头外展、减害服务、就医导航、心理健康与残障支持，以及就业服务。工作日 8:30–16:30，周末不开——**今晚就需要床位的话**，请去 Tranquille Rd 上 24 小时开放的 Pathways 庇护所。',
       ko='노숙 상태이거나 그에 가까운 사람을 위한 주거우선 지원: 집을 찾고, 계약하고, 유지하도록 돕습니다. 거리 아웃리치, 해악 감소, 의료 안내, 정신건강·장애 지원, 취업 서비스도 있습니다. 평일 8:30-16:30, 주말 휴무 — 오늘 밤 잘 곳이 필요하면 24시간 운영하는 Tranquille Rd의 Pathways 쉼터로 가세요.',
       ja='ホームレス状態、またはそれに近い人のためのハウジングファースト支援: 住まいを見つけ、確保し、住み続けられるよう手伝います。街頭アウトリーチ、ハームリダクション、受診の付き添い、精神保健・障害支援、就労支援もあります。平日8時30分〜16時30分、週末休み — 今夜の寝る場所が必要なら、24時間開いているTranquille RdのPathwaysシェルターへ。')),

 dict(n='Canadian Mental Health Association Kamloops', c='support', g='sk',
      lat=50.67571, lng=-120.32585, a='651 Victoria St', p='250-374-0440',
      w='https://kamloops.cmha.bc.ca/', t=['free'],
      h=hrs((1,5,M(9),M(16),0)),
      alias=['心理健康','抑郁','焦虑','志愿','정신건강','우울','자원봉사','メンタルヘルス','ボランティア','sante mentale','salud mental'],
      note=dict(
       en='Mental health support, a clubhouse programme, information and referral, and one of the easier places in town to start volunteering — displays, presentations, events. Weekdays 9-4. This is the head office; the shelters it runs are at other addresses. If you need to talk to someone right now instead, the BC mental health support line is 310-6789, no area code, day or night.',
       fr='Soutien en sante mentale, programme de club, information et references, et l\'un des endroits les plus faciles en ville pour commencer a faire du benevolat. En semaine 9h-16h. Ceci est le siege; les refuges qu\'elle exploite sont a d\'autres adresses. Si vous avez besoin de parler a quelqu\'un tout de suite, la ligne de soutien en sante mentale de la C.-B. est le 310-6789, sans indicatif, jour et nuit.',
       es='Apoyo en salud mental, un programa de club, informacion y derivacion, y uno de los lugares mas faciles de la ciudad para empezar a ser voluntario. Entre semana de 9 a 16h. Esta es la sede; los albergues que opera estan en otras direcciones. Si necesita hablar con alguien ahora mismo, la linea de apoyo de salud mental de BC es el 310-6789, sin prefijo, de dia o de noche.',
       zh='心理健康支持、会所项目、信息与转介，也是本市最容易开始做义工的地方之一。工作日 9:00–16:00。这里是总部，它运营的庇护所在别的地址。**如果你现在就需要有人说话**，BC 省心理健康支持热线是 **310-6789**（不需要区号，24 小时）。',
       ko='정신건강 지원, 클럽하우스 프로그램, 정보와 연계를 제공하며, 이 도시에서 자원봉사를 시작하기 가장 수월한 곳 중 하나입니다. 평일 9-16시. 여기는 본부이고 운영하는 쉼터는 다른 주소에 있습니다. 지금 당장 누군가와 이야기해야 한다면 BC주 정신건강 지원 전화는 310-6789입니다 — 지역번호 없이, 밤낮 없이.',
       ja='メンタルヘルス支援、クラブハウス・プログラム、情報提供と紹介を行い、この街でボランティアを始めるのに最も入りやすい場所の一つです。平日9〜16時。ここは本部で、運営するシェルターは別の住所にあります。今すぐ誰かと話す必要があるなら、BC州のメンタルヘルス支援電話は310-6789です（市外局番不要、昼夜問わず）。')),

 # ----------------------------------------------------------- community ----
 dict(n='Association Francophone de Kamloops', c='commctr', g='ns',
      lat=50.68955, lng=-120.35158, a='348 Fortune Dr', p='250-376-6060',
      w='https://francokamloops.org/', t=['family','free'],
      h=hrs((1,4,M(9),M(15),0)),
      alias=['法语','法文','francophone','프랑스어','フランス語','frances'],
      note=dict(
       en='The francophone hub of the city: adult French conversation clubs, French classes, a daycare and schooling, community events through the year, and newcomer and job support. Useful whether French is your first language or a language you are trying to keep up. Office Monday to Thursday 9-3.',
       fr='Le point de rencontre francophone de la ville : clubs de conversation pour adultes, cours de francais, garderie et scolarisation, evenements communautaires toute l\'annee, et soutien aux nouveaux arrivants et a l\'emploi. Utile que le francais soit votre langue maternelle ou une langue que vous cherchez a entretenir. Bureau du lundi au jeudi 9h-15h.',
       es='El centro francofono de la ciudad: clubes de conversacion en frances para adultos, clases, guarderia y escolarizacion, eventos comunitarios durante todo el ano, y apoyo a recien llegados y al empleo. Util tanto si el frances es su lengua materna como si intenta mantenerlo. Oficina de lunes a jueves de 9 a 15h.',
       zh='本市的法语社区中心：成人法语会话俱乐部、法语课程、日托与就学、全年的社区活动，以及新到居民与就业支持。无论法语是你的母语，还是你想保持的一门语言，这里都用得上。办公室周一至周四 9:00–15:00。',
       ko='이 도시의 프랑스어 커뮤니티 거점입니다: 성인 프랑스어 회화 모임, 프랑스어 수업, 어린이집과 학교, 연중 커뮤니티 행사, 신규 이민자와 취업 지원. 프랑스어가 모국어이든, 유지하고 싶은 언어이든 유용합니다. 사무실은 월-목 9-15시.',
       ja='この街のフランス語コミュニティの拠点です: 大人のフランス語会話クラブ、フランス語教室、保育と就学、一年を通じた地域イベント、新規移住者と就労の支援。フランス語が母語の方にも、維持したい方にも役立ちます。事務所は月〜木9〜15時。')),

 dict(n='Interior Community Services', c='commctr', g='ns',
      lat=50.69877, lng=-120.36376, a='765 Tranquille Rd', p='250-376-3660',
      w='https://interiorcommunityservices.bc.ca/', t=['free'],
      h=hrs((1,5,M(8,30),M(16,30),0)),
      alias=['志愿','义工','送餐','자원봉사','도시락','ボランティア','配食','benevolat','voluntario'],
      note=dict(
       en='A large local social-services agency, and a good first stop if you want to volunteer somewhere that puts you with the same people week after week: Meals on Wheels delivery routes, the Better at Home programme (driving seniors, grocery help), and the Mount Paul food centre. It also runs a youth shelter for ages 13-18 — phone this number to ask about that.',
       fr='Un grand organisme local de services sociaux, et un bon premier arret si vous voulez faire du benevolat la ou vous retrouvez les memes personnes chaque semaine : livraison de la popote roulante, programme Mieux chez soi (conduire des aines, aide a l\'epicerie), et le centre alimentaire Mount Paul. Il gere aussi un refuge pour les 13-18 ans — telephonez a ce numero.',
       es='Una gran agencia local de servicios sociales, y un buen primer paso si quiere ser voluntario en un lugar donde vera a las mismas personas cada semana: rutas de reparto de comida a domicilio, el programa Better at Home (llevar a mayores, ayuda con las compras) y el centro alimentario Mount Paul. Tambien gestiona un albergue juvenil de 13 a 18 anos — llame a este numero.',
       zh='本地规模较大的社会服务机构，如果你想做义工、并且希望**每周见到同一批人**，这里是个好起点：送餐上门路线、Better at Home 项目（接送长者、代买杂货）、以及 Mount Paul 食物中心。它同时运营 13–18 岁青少年庇护所——相关事宜请打这个电话。',
       ko='규모가 큰 지역 사회서비스 기관으로, 매주 같은 사람들을 만나는 방식의 자원봉사를 원한다면 좋은 출발점입니다: 도시락 배달 노선, Better at Home 프로그램(어르신 차량 지원, 장보기 도움), Mount Paul 푸드센터. 13-18세 청소년 쉼터도 운영하니 이 번호로 문의하세요.',
       ja='地域の大きな社会サービス団体で、毎週同じ人たちと顔を合わせる形のボランティアを探しているなら良い出発点です: 配食の配達ルート、Better at Homeプログラム（高齢者の送迎、買い物の手伝い）、Mount Paulフードセンター。13〜18歳の青少年シェルターも運営しているので、この番号へお問い合わせください。')),

 dict(n='Colombo Lodge Italian Cultural Centre', c='commctr', g='sk',
      lat=50.67711, lng=-120.31960, a='814 Lorne St', p='250-374-4914',
      w='https://www.colombolodge.com/', t=['culture'],
      h=hrs((1,5,M(9),M(13),0)),
      alias=['意大利','意大利语','이탈리아','イタリア','italien','italiano'],
      note=dict(
       en='The Italian cultural centre and hall, going back to the city\'s early Italian community. It takes new members who want to keep that culture going locally; members are asked for a minimum of ten volunteer hours a year. Office weekdays 9-1.',
       fr='Le centre culturel et la salle italiens, issus de la premiere communaute italienne de la ville. Il accueille de nouveaux membres qui veulent faire vivre cette culture ici; on demande aux membres un minimum de dix heures de benevolat par an. Bureau en semaine 9h-13h.',
       es='El centro cultural y salon italiano, heredero de la primera comunidad italiana de la ciudad. Admite nuevos miembros que quieran mantener viva esa cultura aqui; se pide un minimo de diez horas de voluntariado al ano. Oficina entre semana de 9 a 13h.',
       zh='意大利文化中心与礼堂，可追溯到这座城市早期的意大利社群。欢迎希望把这份文化在本地延续下去的人加入；会员每年需承担至少十小时的志愿服务。办公室工作日 9:00–13:00。',
       ko='이 도시 초기 이탈리아 커뮤니티에서 이어져 온 이탈리아 문화센터이자 홀입니다. 그 문화를 지역에서 이어가고 싶은 신규 회원을 받으며, 회원에게는 연간 최소 열 시간의 자원봉사를 요청합니다. 사무실은 평일 9-13시.',
       ja='この街の初期のイタリア人コミュニティに遡るイタリア文化センターとホールです。その文化を地元で続けたい新しい会員を受け入れており、会員には年間最低10時間のボランティアが求められます。事務所は平日9〜13時。')),

 dict(n='Kamloops Hospice Association', c='hospital', g='sa',
      lat=50.65881, lng=-120.33750, a='72 Whiteshield Cres S', p='250-372-1336',
      w='https://kamloopshospice.com/', precision='low',
      h=hrs((1,5,M(9),M(16),0)),
      alias=['临终关怀','安宁疗护','호스피스','ホスピス','soins palliatifs','cuidados paliativos'],
      note=dict(
       en='Hospice House — end-of-life care for people and their families, at no cost to the family. Also one of the places in town that takes trained volunteers, though expect an application and a wait rather than a walk-in. The coordinate here is good to the block, not the door.',
       fr='Maison de soins palliatifs — accompagnement de fin de vie pour les personnes et leurs familles, sans frais pour la famille. Aussi l\'un des endroits qui accueille des benevoles formes, mais attendez-vous a une candidature et a un delai. La coordonnee ici est bonne a l\'ilot pres, pas a la porte.',
       es='Casa de cuidados paliativos — atencion al final de la vida para las personas y sus familias, sin costo para la familia. Tambien uno de los lugares que acepta voluntarios formados, aunque conlleva una solicitud y una espera. La coordenada aqui es buena a nivel de manzana, no de puerta.',
       zh='临终关怀之家——为患者与家属提供生命末期照护，**家属不需付费**。这里也接收经过培训的志愿者，但需要提交申请并等待，不能直接上门。此处坐标精确到街区，不到门牌。',
       ko='호스피스 하우스 — 환자와 가족을 위한 임종 돌봄으로, 가족에게 비용을 청구하지 않습니다. 교육을 받은 자원봉사자를 받는 곳이기도 하지만, 지원서와 대기가 필요하며 바로 방문하는 방식은 아닙니다. 여기 좌표는 구역 단위이며 출입구 단위는 아닙니다.',
       ja='ホスピスハウス — 本人とご家族のための終末期ケアで、ご家族に費用はかかりません。訓練を受けたボランティアを受け入れている場所でもありますが、申込と待機が必要で、飛び込みではありません。ここの座標は街区単位で、玄関の精度ではありません。')),

 dict(n='RIH Auxiliary Thrift Shop', c='secondhand', g='sk',
      lat=50.67644, lng=-120.33795, a='146 Victoria St', p='250-374-0487',
      w='https://rih-auxiliary.com/', t=['free'],
      h=hrs((1,6,M(10),M(16),0)),
      alias=['二手','旧货','衣服','중고','옷','古着','friperie','ropa usada'],
      note=dict(
       en='The hospital auxiliary\'s thrift shop downtown — cheap clothes and household goods, and the money goes back into Royal Inland Hospital. It is also the practical way into hospital volunteering in Kamloops: you can apply for the thrift shop in person, right here.',
       fr='La friperie de l\'auxiliaire de l\'hopital, au centre-ville — vetements et articles menagers bon marche, et l\'argent retourne a l\'hopital Royal Inland. C\'est aussi la voie concrete vers le benevolat hospitalier a Kamloops : on peut postuler sur place pour la friperie.',
       es='La tienda de segunda mano del auxiliar del hospital, en el centro — ropa y articulos del hogar baratos, y el dinero vuelve al Royal Inland Hospital. Es tambien la via practica al voluntariado hospitalario en Kamloops: puede solicitarlo en persona aqui mismo.',
       zh='医院志愿者协会在市中心开的二手店——便宜的衣物与家居用品，收入回流到 Royal Inland 医院。这里也是在 Kamloops 进入医院志愿服务的实际入口：二手店的志愿岗位可以直接来店里申请。',
       ko='시내에 있는 병원 후원회의 중고매장입니다 — 저렴한 옷과 생활용품을 팔고, 수익은 Royal Inland 병원으로 돌아갑니다. 캄루프스에서 병원 자원봉사를 시작하는 현실적인 통로이기도 해서, 매장 봉사는 이곳에서 직접 신청할 수 있습니다.',
       ja='病院後援会がダウンタウンで運営する古着店です — 安い衣類や生活用品を扱い、売上はRoyal Inland病院に戻ります。カムループスで病院ボランティアを始める現実的な入口でもあり、店舗の募集はここで直接申し込めます。')),
]

# ---------------------------------------------------------------------------
existing_ids = {p['id'] for p in P}
existing_names = {p['n'] for p in P}
rows = []
for r in NEW:
    if r['n'] in existing_names:
        print('  skip (already present):', r['n']); continue
    r = dict(r)
    r['id'] = pid(r['n'], r['a'])
    assert r['id'] not in existing_ids, 'id collision on ' + r['n']
    existing_ids.add(r['id'])
    r['src'] = 'official'
    r['v'] = '2026-09'
    rows.append(r)

# key order matches the rest of the file so a diff stays readable
ORDER = ['n','c','g','lat','lng','a','p','w','h','note','src','v','alias','t','precision','id']
def dump(r):
    d = {k: r[k] for k in ORDER if k in r}
    return json.dumps(d, ensure_ascii=False, separators=(',', ':'))

blob = ',\n'.join(dump(r) for r in rows)
marker = '];\n'
i = s.index('const P=[')
j = s.index(marker, i)
s = s[:j] + ',\n' + blob + s[j:]

# --- correction: the Mustard Seed pin was 250 m north-east of the building ---
s = s.replace('"lat":50.6789,"lng":-120.3421', '"lat":50.67698,"lng":-120.34365')

io.open(SRC, 'w', encoding='utf-8').write(s)
print('added %d places' % len(rows))
for r in rows: print('   %-46s %-10s %s' % (r['n'][:46], r['c'], r['id']))
