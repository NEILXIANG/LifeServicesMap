#!/usr/bin/env python3
"""Phase 5 — the task cards' missing conditions (2026-09-21 card check).
Steps are rewritten in place, never added or removed, so a reader's ticks
(stored by step position) still point at the same step."""
import sys
sys.path.insert(0, '.')
import kamdata

T = kamdata.load('TASKS')
P = kamdata.load('P')
by = {t['id']: t for t in T}
L6 = ('en', 'fr', 'es', 'zh', 'ko', 'ja')
def tx(**kw):
    assert set(kw) == set(L6), set(L6) - set(kw)
    return {l: kw[l] for l in ('en', 'fr', 'es', 'zh', 'ko', 'ja')}
def step(tid, i, starts, new):
    t = by[tid]; assert t['steps'][i]['en'].startswith(starts), (tid, i, t['steps'][i]['en'][:60])
    t['steps'][i] = new

# ---------------------------------------------------------------- deposit (RTB returning-deposits page; Policy Guideline 17)
step('deposit', 0, 'Give your landlord your forwarding address', tx(
  en='Give your landlord your forwarding address in writing — within one year of moving out, or you lose the right to get the deposit back.',
  fr='Donnez par écrit votre nouvelle adresse au propriétaire — dans l’année qui suit votre départ, sinon vous perdez le droit de récupérer le dépôt.',
  es='Dé por escrito su nueva dirección al arrendador — dentro del año siguiente a la mudanza, o pierde el derecho a recuperar el depósito.',
  zh='书面把新地址交给房东——必须在搬走后一年内交，否则就失去拿回押金的权利。',
  ko='새 주소를 서면으로 집주인에게 주세요 — 이사 후 1년 안에 주지 않으면 보증금을 돌려받을 권리를 잃습니다.',
  ja='転居先の住所を書面で大家に渡しましょう — 退去から1年以内に渡さないと、敷金を返してもらう権利がなくなります。'))
step('deposit', 1, 'They then have 15 days', tx(
  en='From the later of the day you move out and the day they receive your address, they have 15 days to return it (with any interest owed) or to file a claim against it.',
  fr='À compter de la date la plus tardive entre votre départ et la réception de votre adresse, le propriétaire a 15 jours pour le rendre (avec les intérêts dus) ou présenter une demande pour le garder.',
  es='Desde la fecha más tardía entre su mudanza y el día en que reciben su dirección, tienen 15 días para devolverlo (con los intereses que correspondan) o presentar una reclamación sobre él.',
  zh='从“你搬走那天”和“房东收到地址那天”中较晚的一天算起，房东有 15 天把押金（连同应付的利息）还给你，或者就押金提出申请。',
  ko='이사한 날과 집주인이 주소를 받은 날 중 늦은 날부터 15일 안에, 집주인은 보증금을(발생한 이자와 함께) 돌려주거나 보증금에 대한 청구를 제기해야 합니다.',
  ja='退去日と大家が住所を受け取った日のうち遅いほうから15日以内に、大家は敷金を（発生した利息とともに）返すか、敷金について申し立てをしなければなりません。'))
by['deposit']['note'] = tx(
  en='Caps: security deposit at most half a month’s rent; pet damage deposit at most another half. Landlords may not charge application fees, monthly pet fees, or a fee to return your deposit. They may keep part of it only if you agree in writing, or if the Residential Tenancy Branch orders it.',
  fr='Plafonds : dépôt de garantie d’au plus un demi-mois de loyer ; dépôt pour dommages causés par un animal d’au plus un autre demi-mois. Le propriétaire ne peut pas facturer de frais de demande, de frais mensuels pour animal ni de frais pour rendre le dépôt. Il ne peut en garder une partie que si vous l’acceptez par écrit ou si la Residential Tenancy Branch l’ordonne.',
  es='Topes: depósito de garantía de medio mes de alquiler como máximo; depósito por daños de mascota de otra media mensualidad como máximo. No se pueden cobrar tarifas de solicitud, cuotas mensuales por mascota ni una tarifa por devolver el depósito. Solo pueden quedarse con una parte si usted lo acepta por escrito o si la Residential Tenancy Branch lo ordena.',
  zh='上限：押金最多半个月房租；宠物押金最多再加半个月。房东不能收申请费、每月宠物费，也不能收“退押金手续费”。只有你书面同意、或者 Residential Tenancy Branch 裁定，房东才能扣下一部分。',
  ko='상한: 보증금은 최대 월세의 절반, 반려동물 손해 보증금은 최대 절반 더. 집주인은 신청비, 월 반려동물 요금, 보증금 반환 수수료를 받을 수 없습니다. 일부를 가져갈 수 있는 경우는 세입자가 서면으로 동의했거나 Residential Tenancy Branch가 명령한 때뿐입니다.',
  ja='上限：敷金は家賃の半月分まで、ペット損害の敷金はさらに半月分まで。大家は申込手数料、毎月のペット料金、敷金返還の手数料を取れません。一部を差し引けるのは、あなたが書面で同意したか、Residential Tenancy Branchが命じた場合だけです。')

# ---------------------------------------------------------------- eldercare (gov.bc.ca eligibility; home-support and adult-day cost pages; ICS Better at Home)
by['eldercare']['why'] = tx(
  en='This one is for people who have lived here for years as much as for anyone new. Much of the help is subsidised, and almost nobody knows it exists until they need it. Subsidised care is for citizens, permanent residents and some permit holders who have lived in BC for at least three months — a parent here on a visitor visa or super visa does not qualify.',
  fr='Cette fiche s’adresse autant aux personnes installées depuis des années qu’aux nouveaux arrivants. Une grande partie de l’aide est subventionnée, et presque personne ne le sait avant d’en avoir besoin. Les soins subventionnés sont réservés aux citoyens, aux résidents permanents et à certains titulaires de permis qui vivent en C.-B. depuis au moins trois mois — un parent venu avec un visa de visiteur ou un super visa n’y a pas droit.',
  es='Esta ficha es tanto para quienes llevan años aquí como para quien acaba de llegar. Buena parte de la ayuda está subvencionada, y casi nadie lo sabe hasta que la necesita. La atención subvencionada es para ciudadanos, residentes permanentes y algunos titulares de permisos que llevan al menos tres meses viviendo en BC; un padre o madre con visa de visitante o súper visa no reúne los requisitos.',
  zh='这张卡既写给住了很多年的人，也写给新来的人。很多帮助有政府补贴，但大多数人要到用得上时才知道。有补贴的照护只给公民、永久居民和部分持许可的人，而且要在 BC 住满三个月——用访客签证或超级签证来的父母不符合条件。',
  ko='이 카드는 새로 온 사람만큼이나 이곳에 오래 산 사람을 위한 것입니다. 많은 지원이 보조금으로 제공되지만, 필요해지기 전까지는 거의 아무도 모릅니다. 보조 돌봄은 시민, 영주권자, 일부 허가 소지자로서 BC에 최소 3개월 거주한 사람만 받을 수 있습니다 — 방문 비자나 슈퍼 비자로 온 부모는 해당되지 않습니다.',
  ja='このカードは、新しく来た人だけでなく、長く住んでいる人のためのものでもあります。支援の多くには補助がありますが、必要になるまでほとんど誰も知りません。補助付きのケアは、市民、永住者、一部の許可保持者で、BCに3か月以上住んでいる人が対象です — 訪問者ビザやスーパービザで来ている親は対象外です。')
step('eldercare', 1, "Ask Interior Health's Home and Community Care", tx(
  en="Ask Interior Health's Home and Community Care for an assessment. It is free, and it is the door to subsidised home support, adult day programmes and, later, assisted living.",
  fr="Demandez une évaluation aux services Home and Community Care d’Interior Health. Elle est gratuite, et c’est la porte d’entrée vers l’aide à domicile subventionnée, les programmes de jour et, plus tard, le logement avec services.",
  es="Pida una evaluación a Home and Community Care de Interior Health. Es gratuita y es la puerta a la ayuda a domicilio subvencionada, los programas de día para adultos y, más adelante, la vivienda asistida.",
  zh='向 Interior Health 的 Home and Community Care 申请评估。评估免费，是获得补贴居家支援、成人日间项目，以及以后辅助生活住所的入口。',
  ko='Interior Health의 Home and Community Care에 평가를 요청하세요. 평가는 무료이며, 보조 재가 지원, 성인 주간 프로그램, 나중에는 지원 주택으로 가는 관문입니다.',
  ja='Interior HealthのHome and Community Careに評価を依頼しましょう。評価は無料で、補助付きの在宅支援、成人デイプログラム、将来のアシステッドリビングへの入口です。'))
step('eldercare', 2, 'For the everyday things', tx(
  en='For people 65 and over, Better at Home (through Interior Community Services) helps with groceries, light housekeeping, yard work, friendly visits and meals. Some of it is charged on a sliding scale by income.',
  fr='Pour les 65 ans et plus, Better at Home (par Interior Community Services) aide pour l’épicerie, le ménage léger, l’entretien du terrain, les visites amicales et les repas. Certains services sont facturés selon une échelle liée au revenu.',
  es='Para mayores de 65 años, Better at Home (a través de Interior Community Services) ayuda con la compra, limpieza ligera, jardín, visitas amistosas y comidas. Algunos servicios se cobran según una escala de ingresos.',
  zh='65 岁以上的人可以通过 Interior Community Services 的 Better at Home 获得帮助：买菜、简单家务、院子活、上门探访和送餐。部分服务按收入分档收费。',
  ko='65세 이상이라면 Interior Community Services의 Better at Home이 장보기, 가벼운 집안일, 마당 일, 방문 말벗, 식사를 도와줍니다. 일부는 소득에 따라 차등 요금이 있습니다.',
  ja='65歳以上なら、Interior Community ServicesのBetter at Homeが買い物、軽い家事、庭仕事、訪問、食事を手伝います。一部は収入に応じたスライド制の料金です。'))
by['eldercare']['cost'] = tx(
  en='Assessment free. Home support is charged at a daily rate based on income — free for people receiving GIS or income assistance. Adult day programmes can charge up to $10 a day, which can be waived in hardship.',
  fr='Évaluation gratuite. L’aide à domicile est facturée à un tarif journalier selon le revenu — gratuite pour les bénéficiaires du SRG ou de l’aide sociale. Les programmes de jour peuvent coûter jusqu’à 10 $ par jour, somme qui peut être annulée en cas de difficulté.',
  es='Evaluación gratuita. La ayuda a domicilio se cobra por día según los ingresos; es gratuita para quien recibe el GIS o asistencia social. Los programas de día pueden costar hasta 10 $ al día, cantidad que puede eximirse en casos de dificultad.',
  zh='评估免费。居家支援按收入计日费——领取 GIS 或社会救助的人免费。成人日间项目每天最多收 10 加元，经济困难可以免收。',
  ko='평가는 무료입니다. 재가 지원은 소득에 따른 일일 요금이며, GIS나 소득 지원을 받는 사람은 무료입니다. 성인 주간 프로그램은 하루 최대 10달러이며, 형편이 어려우면 면제될 수 있습니다.',
  ja='評価は無料。在宅支援は収入に応じた日額料金で、GISや生活扶助を受けている人は無料です。成人デイプログラムは1日最大10ドルで、困窮時は免除されることがあります。')
by['eldercare']['help'] = tx(
  en='Stuck between offices? Call 2-1-1, or a settlement worker if language is part of the difficulty.',
  fr='Perdu entre les services ? Le 2-1-1, ou un intervenant en établissement si la langue fait partie du problème.',
  es='¿Perdido entre oficinas? Llame al 2-1-1, o a un trabajador de asentamiento si el idioma es parte de la dificultad.',
  zh='在几个机构之间转不出来？打 2-1-1；如果语言也是障碍，找定居服务专员。',
  ko='기관 사이에서 헤매고 있다면 2-1-1, 언어가 어려움의 일부라면 정착 지원 담당자에게.',
  ja='窓口の間で行き詰まったら2-1-1へ。言葉も壁になっているなら定住支援ワーカーへ。')

# ---------------------------------------------------------------- msp (gov.bc.ca apply-for-msp: accepted documents, upload format)
step('msp', 1, 'Upload a document showing', tx(
  en='Upload a document showing your name, date of birth and status: a PR card, record of landing, or a work, study or visitor permit (a Canadian passport for citizens). A foreign passport or a COPR is not accepted. JPG or PNG, at least 1000 × 1500 pixels.',
  fr='Téléversez un document indiquant votre nom, votre date de naissance et votre statut : carte de RP, fiche relative au droit d’établissement, ou permis de travail, d’études ou de visiteur (passeport canadien pour les citoyens). Un passeport étranger ou une CRP n’est pas accepté. JPG ou PNG, au moins 1000 × 1500 pixels.',
  es='Suba un documento con su nombre, fecha de nacimiento y estatus: tarjeta de RP, constancia de llegada (record of landing) o permiso de trabajo, estudio o visitante (pasaporte canadiense para ciudadanos). No se acepta un pasaporte extranjero ni la COPR. JPG o PNG, al menos 1000 × 1500 píxeles.',
  zh='上传一份写有姓名、出生日期和身份的文件：PR 卡、落地纸（record of landing），或工签、学签、访客许可（公民用加拿大护照）。外国护照和 COPR 不被接受。格式为 JPG 或 PNG，至少 1000 × 1500 像素。',
  ko='이름, 생년월일, 체류 신분이 나온 서류를 올리세요: 영주권 카드, 랜딩 기록(record of landing), 또는 취업·학생·방문 허가서(시민은 캐나다 여권). 외국 여권이나 COPR은 인정되지 않습니다. JPG 또는 PNG, 최소 1000 × 1500 픽셀.',
  ja='氏名、生年月日、在留資格が分かる書類をアップロード：PRカード、ランディング記録（record of landing）、または就労・学生・訪問者許可（市民はカナダのパスポート）。外国のパスポートやCOPRは不可。JPGかPNGで、1000 × 1500ピクセル以上。'))
by['msp']['bring'] = tx(
  en='A document showing your name, date of birth and immigration status — a PR card, record of landing, or a work, study or visitor permit. Not a foreign passport, not a COPR. You upload a photo of it (JPG or PNG).',
  fr='Un document indiquant votre nom, votre date de naissance et votre statut d’immigration — carte de RP, fiche relative au droit d’établissement, ou permis de travail, d’études ou de visiteur. Pas de passeport étranger ni de CRP. Vous en téléversez une photo (JPG ou PNG).',
  es='Un documento con su nombre, fecha de nacimiento y estatus migratorio: tarjeta de RP, constancia de llegada, o permiso de trabajo, estudio o visitante. No sirve el pasaporte extranjero ni la COPR. Se sube una foto (JPG o PNG).',
  zh='一份写有姓名、出生日期和移民身份的文件——PR 卡、落地纸，或工签、学签、访客许可。外国护照和 COPR 不行。上传它的照片（JPG 或 PNG）。',
  ko='이름, 생년월일, 이민 신분이 나온 서류 — 영주권 카드, 랜딩 기록, 또는 취업·학생·방문 허가서. 외국 여권과 COPR은 안 됩니다. 사진(JPG 또는 PNG)으로 올립니다.',
  ja='氏名、生年月日、在留資格が分かる書類 — PRカード、ランディング記録、または就労・学生・訪問者許可。外国のパスポートやCOPRは不可。写真（JPGかPNG）でアップロードします。')

# ---------------------------------------------------------------- licence (icbc.com visit-dl-office)
step('licence', 0, 'Go to an ICBC driver licensing office', tx(
  en='Go to an ICBC driver licensing office. Knowledge and road tests need an appointment; for other services you can walk in, but you might not be served that day.',
  fr='Rendez-vous dans un bureau de permis de conduire d’ICBC. Les examens théorique et pratique se font sur rendez-vous ; pour le reste, on peut se présenter sans rendez-vous, mais sans garantie d’être servi le jour même.',
  es='Vaya a una oficina de licencias de ICBC. Los exámenes teórico y práctico requieren cita; para otros trámites puede ir sin cita, pero quizá no le atiendan ese día.',
  zh='去 ICBC 驾照办公室。笔试和路考要预约；其他业务可以直接去，但当天不一定排得上。',
  ko='ICBC 운전면허 사무소로 가세요. 필기시험과 도로주행 시험은 예약이 필요하고, 다른 업무는 방문 접수가 되지만 그날 처리되지 않을 수도 있습니다.',
  ja='ICBCの運転免許事務所へ。学科試験と実技試験は予約が必要です。そのほかの手続きは予約なしでも行けますが、その日に対応してもらえないこともあります。'))
by['licence']['why'] = tx(
  en='If you have moved here to live, you have 90 days from arriving before you need a BC licence. Visitors and students with an exemption follow different rules.',
  fr='Si vous vous installez ici, vous avez 90 jours après votre arrivée pour obtenir un permis de la C.-B. Les visiteurs et les étudiants bénéficiant d’une exemption suivent d’autres règles.',
  es='Si se ha mudado aquí para vivir, tiene 90 días desde su llegada antes de necesitar una licencia de BC. Los visitantes y estudiantes con exención siguen otras reglas.',
  zh='如果是搬来这里生活，到达后 90 天内要换成 BC 驾照。访客和有豁免的学生适用不同规定。',
  ko='이곳에 살려고 이주했다면, 도착 후 90일 안에 BC 면허가 필요합니다. 방문자와 면제 대상 학생은 규정이 다릅니다.',
  ja='住むために移ってきた場合、到着から90日以内にBCの免許が必要です。訪問者や免除のある学生は別のルールです。')

# ---------------------------------------------------------------- sin (canada.ca SIN required documents)
step('sin', 0, 'Apply online (fastest)', tx(
  en='Apply online (fastest), by mail, or in person at Service Canada — request an in-person appointment online first.',
  fr='Faites la demande en ligne (le plus rapide), par la poste ou en personne à Service Canada — demandez d’abord un rendez-vous en ligne.',
  es='Solicítelo en línea (lo más rápido), por correo o en persona en Service Canada; pida primero una cita en línea.',
  zh='网上申请（最快）、邮寄，或到 Service Canada 当面办——当面办要先在网上申请预约。',
  ko='온라인(가장 빠름), 우편, 또는 Service Canada 방문으로 신청하세요 — 방문하려면 먼저 온라인으로 예약을 요청하세요.',
  ja='オンライン（最速）、郵送、またはService Canadaの窓口で申請 — 窓口の場合は先にオンラインで予約を申し込みます。'))
by['sin']['bring'] = tx(
  en='One primary document — your work or study permit (it must say you may work), PR card, or a COPR less than a year old — plus one secondary ID, such as your passport or a driver’s licence.',
  fr='Un document principal — votre permis de travail ou d’études (il doit indiquer que vous pouvez travailler), votre carte de RP ou une CRP de moins d’un an — et une pièce secondaire, comme votre passeport ou un permis de conduire.',
  es='Un documento principal — su permiso de trabajo o de estudio (debe decir que puede trabajar), la tarjeta de RP o una COPR de menos de un año — más una identificación secundaria, como su pasaporte o una licencia de conducir.',
  zh='一份主要文件——工签或学签（上面要写明可以工作）、PR 卡，或签发不到一年的 COPR——再加一份辅助证件，比如护照或驾照。',
  ko='기본 서류 1개 — 취업·학생 허가서(근로 가능하다고 적혀 있어야 함), 영주권 카드, 또는 발급 1년 이내의 COPR — 와 여권이나 운전면허증 같은 보조 신분증 1개.',
  ja='主要書類1つ — 就労・学生許可（就労可と書かれているもの）、PRカード、または発行から1年以内のCOPR — と、パスポートや運転免許証などの補助的な身分証1つ。')

# ---------------------------------------------------------------- hardship shelters (bc211 listings: 24/7 confirmed for Mustard Seed and Merit Place)
by['hardship']['note'] = tx(
  en='Need a bed tonight? Kamloops has four shelters: The Mustard Seed West End Shelter 250-372-9890 (20 beds, walk-ins any time), Merit Place Shelter 236-425-0341 (49 pods, walk-ins any time; one pet at a time; beds are given out at the 9:30 pm curfew), Pathways Shelter and Access Hub 250-299-7936 (44 beds, North Shore, low-barrier — call the intake line), and Emerald Centre 250-372-3031 (42 beds — call before you go). If one is full, try another — no single call is the end of the road.',
  fr='Besoin d’un lit ce soir ? Kamloops compte quatre refuges : The Mustard Seed West End Shelter 250-372-9890 (20 lits, accueil sans rendez-vous à toute heure), Merit Place Shelter 236-425-0341 (49 capsules, accueil à toute heure ; un animal à la fois ; les lits sont attribués au couvre-feu de 21 h 30), Pathways Shelter and Access Hub 250-299-7936 (44 lits, rive nord, bas seuil — appelez la ligne d’accueil) et Emerald Centre 250-372-3031 (42 lits — appelez avant d’y aller). Si l’un est plein, essayez-en un autre — un seul appel n’est jamais la fin.',
  es='¿Necesita una cama esta noche? Kamloops tiene cuatro albergues: The Mustard Seed West End Shelter 250-372-9890 (20 camas, sin cita a cualquier hora), Merit Place Shelter 236-425-0341 (49 cápsulas, sin cita a cualquier hora; una mascota a la vez; las camas se asignan en el toque de queda de las 21:30), Pathways Shelter and Access Hub 250-299-7936 (44 camas, ribera norte, bajo umbral — llame a la línea de ingreso) y Emerald Centre 250-372-3031 (42 camas — llame antes de ir). Si uno está lleno, pruebe otro: ninguna llamada es el final del camino.',
  zh='今晚需要床位？Kamloops 有四家庇护所：The Mustard Seed West End Shelter 250-372-9890（20 张床位，随时可直接去），Merit Place Shelter 236-425-0341（49 个独立床舱，随时可直接去；每次可带一只宠物；床位在晚上 9:30 门禁时分配），Pathways Shelter and Access Hub 250-299-7936（44 张床位，北岸，低门槛——打入住电话），Emerald Centre 250-372-3031（42 张床位——去之前先打电话）。一家满了就试另一家——一个电话打不通不是走投无路。',
  ko='오늘 밤 잘 곳이 필요하세요? Kamloops에는 쉼터가 네 곳 있습니다: The Mustard Seed West End Shelter 250-372-9890(20병상, 언제든 방문 가능), Merit Place Shelter 236-425-0341(개별 포드 49개, 언제든 방문 가능, 반려동물 한 마리까지, 침상은 밤 9시 30분 통금 때 배정), Pathways Shelter and Access Hub 250-299-7936(44병상, 노스쇼어, 저문턱 — 입소 전화로 연락), Emerald Centre 250-372-3031(42병상 — 가기 전에 전화). 한 곳이 꽉 찼으면 다른 곳을 시도하세요 — 전화 한 통으로 끝나는 게 아닙니다.',
  ja='今夜寝る場所が必要ですか？Kamloopsには4つのシェルターがあります：The Mustard Seed West End Shelter 250-372-9890（20床、いつでも直接行ける）、Merit Place Shelter 236-425-0341（個室ポッド49、いつでも直接行ける、ペットは1匹まで、ベッドは21時30分の門限時に割り当て）、Pathways Shelter and Access Hub 250-299-7936（44床、ノースショア、ローバリア — 入所の電話へ）、Emerald Centre 250-372-3031（42床 — 行く前に電話を）。1か所が満員でも別の所を試してください — 電話1本で終わりではありません。')

# ---------------------------------------------------------------- school (sd73.bc.ca/register-for-school)
by['school']['why'] = tx(
  en='Your home address decides your catchment school. SD73 also runs Schools of Choice (French Immersion, Montessori and others), which have their own registration.',
  fr='Votre adresse détermine votre école de secteur. Le SD73 offre aussi des écoles de choix (immersion française, Montessori et autres), avec leur propre inscription.',
  es='Su dirección determina la escuela de su zona. El SD73 también tiene escuelas de elección (inmersión en francés, Montessori y otras), con su propia inscripción.',
  zh='你的住址决定孩子的片区学校。SD73 还有“择校项目”（法语沉浸、蒙特梭利等），要另外报名。',
  ko='집 주소가 배정 학교를 정합니다. SD73에는 선택 학교(프랑스어 몰입, 몬테소리 등)도 있으며, 등록은 따로 합니다.',
  ja='住所で学区の学校が決まります。SD73には選択制の学校（フレンチイマージョン、モンテッソーリなど）もあり、登録は別です。')
by['school']['note'] = tx(
  en='If your child is still learning English, say so when you register — the district has language support, and asking early is what gets it started. Kindergarten catchment registration for the coming September is in early February; Schools of Choice register earlier, in January. Late registrations are accepted. A child still in the MSP wait may not have a BC Services Card yet — say so when you register.',
  fr='Si votre enfant apprend encore l’anglais, dites-le à l’inscription — le district offre du soutien linguistique, et le demander tôt permet de le mettre en place. L’inscription à la maternelle de secteur pour septembre a lieu début février ; les écoles de choix inscrivent plus tôt, en janvier. Les inscriptions tardives sont acceptées. Un enfant encore dans le délai d’attente du MSP n’a peut-être pas de carte BC Services — dites-le à l’inscription.',
  es='Si su hijo todavía está aprendiendo inglés, dígalo al inscribirlo: el distrito ofrece apoyo lingüístico y pedirlo pronto es lo que lo pone en marcha. La inscripción de kínder por zona para septiembre es a principios de febrero; las escuelas de elección inscriben antes, en enero. Se aceptan inscripciones tardías. Si el niño aún está en la espera del MSP, quizá no tenga BC Services Card: dígalo al inscribirlo.',
  zh='孩子英语还在学的话，登记时要说出来——学区有语言支持，早提早开始。下一年 9 月入学的幼儿园片区登记在 2 月初；择校项目更早，在 1 月。晚登记也接受。孩子还在 MSP 等待期、还没有 BC Services Card 的话，登记时说明一下。',
  ko='자녀가 아직 영어를 배우는 중이라면 등록할 때 말하세요 — 교육청에 언어 지원이 있고, 일찍 요청해야 시작됩니다. 다음 9월 유치원의 학군 등록은 2월 초이며, 선택 학교는 더 이른 1월입니다. 늦은 등록도 받습니다. 아이가 아직 MSP 대기 기간이라 BC Services Card가 없다면 등록할 때 말하세요.',
  ja='お子さんがまだ英語を学習中なら、登録時に伝えましょう — 学区には言語支援があり、早く頼むほど早く始まります。翌9月の幼稚園の学区登録は2月初め、選択制の学校はそれより早い1月です。遅れての登録も受け付けます。MSPの待機期間中でBC Services Cardがまだない場合も、登録時に伝えてください。')
by['school']['src'] = 'https://www.sd73.bc.ca/register-for-school'

# ---------------------------------------------------------------- connect (immigrantservices.ca conversation-circle page)
by['connect']['also'] = tx(
  en='Kamloops Immigrant Services runs free Conversation Circles and social events — register first by calling 778-470-6101 ext. 116.',
  fr='Kamloops Immigrant Services organise des cercles de conversation et des activités sociales gratuits — inscrivez-vous d’abord au 778-470-6101, poste 116.',
  es='Kamloops Immigrant Services organiza círculos de conversación y actividades sociales gratuitos; inscríbase antes llamando al 778-470-6101, ext. 116.',
  zh='Kamloops Immigrant Services 有免费的英语角和社交活动——先打 778-470-6101 转 116 报名。',
  ko='Kamloops Immigrant Services는 무료 대화 모임과 사교 행사를 엽니다 — 먼저 778-470-6101 내선 116으로 전화해 등록하세요.',
  ja='Kamloops Immigrant Servicesは無料の会話サークルや交流イベントを開いています — まず778-470-6101（内線116）に電話して登録を。')

# ---------------------------------------------------------------- settle (immigrantservices.ca/get-settled/)
by['settle']['why'] = tx(
  en='Free and one-to-one — for permanent residents and refugees in particular; some services are also open to temporary residents. This is the shortcut for everything else on this list.',
  fr='Gratuit et en tête-à-tête — surtout pour les résidents permanents et les réfugiés ; certains services sont aussi ouverts aux résidents temporaires. Le raccourci pour tout le reste de cette liste.',
  es='Gratis y uno a uno — sobre todo para residentes permanentes y refugiados; algunos servicios también están abiertos a residentes temporales. El atajo para todo lo demás de esta lista.',
  zh='免费、一对一——主要面向永久居民和难民；部分服务也对临时居民开放。这份清单上其他所有事，走这条路最快。',
  ko='무료 일대일 상담 — 주로 영주권자와 난민 대상이며, 일부 서비스는 임시 거주자도 이용할 수 있습니다. 이 목록의 나머지 모든 일에 대한 지름길입니다.',
  ja='無料の個別相談 — 主に永住者と難民が対象で、一部のサービスは一時滞在者も利用できます。このリストの他のすべてへの近道です。')
step('settle', 0, 'Call or walk in', tx(
  en='Call to book an appointment, and say you have just arrived and want help getting set up.',
  fr='Appelez pour prendre rendez-vous, et dites que vous venez d’arriver et que vous voulez de l’aide pour vous installer.',
  es='Llame para pedir una cita y diga que acaba de llegar y quiere ayuda para instalarse.',
  zh='打电话预约，说你刚到、想找人帮你安顿下来。',
  ko='전화로 예약하고, 막 도착해서 정착 도움을 받고 싶다고 말하세요.',
  ja='電話で予約し、来たばかりで生活の立ち上げを手伝ってほしいと伝えましょう。'))
step('settle', 1, 'Ask for an interpreter', tx(
  en='Ask whether an interpreter can be booked in your language.',
  fr='Demandez si un interprète peut être réservé dans votre langue.',
  es='Pregunte si pueden reservar un intérprete en su idioma.',
  zh='问一下能不能安排你母语的翻译。',
  ko='모국어 통역을 예약할 수 있는지 물어보세요.',
  ja='母語の通訳を予約できるか聞いてみましょう。'))
by['settle']['src'] = 'https://immigrantservices.ca/get-settled/'
by['settle']['srcName'] = 'Kamloops Immigrant Services'
by['settle']['cost'] = tx(
  en='Free; what is offered depends on your status.', fr='Gratuit ; l’offre dépend de votre statut.', es='Gratis; lo que se ofrece depende de su estatus.',
  zh='免费；能用哪些服务取决于你的身份。', ko='무료이며, 이용 가능한 서비스는 신분에 따라 다릅니다.', ja='無料。受けられるサービスは在留資格によって異なります。') if isinstance(by['settle'].get('cost'), dict) else by['settle'].get('cost')

# ---------------------------------------------------------------- rights (BCHRT time limit page; SPOKE page)
by['rights']['note'] = tx(
  en='The one-year clock runs from the incident — or, for discrimination that keeps happening, from the last incident — not from the day you arrived. A late complaint can still be accepted, but only if the Tribunal finds it is in the public interest and no one would be substantially prejudiced — do not rely on it.',
  fr='Le délai d’un an court à partir de l’incident — ou, pour une discrimination qui se répète, du dernier incident — et non de votre arrivée. Une plainte tardive peut encore être acceptée, mais seulement si le Tribunal juge que c’est dans l’intérêt public et que personne n’en subirait un préjudice important — n’y comptez pas.',
  es='El plazo de un año cuenta desde el incidente —o, si la discriminación continúa, desde el último incidente—, no desde su llegada. Una queja tardía aún puede aceptarse, pero solo si el Tribunal considera que es de interés público y que nadie sufriría un perjuicio sustancial; no cuente con ello.',
  zh='一年的期限从事件发生之日算起——如果歧视一直在持续，从最后一次算起——不是从你到加拿大那天算。超期投诉也可能被受理，但前提是审裁处认为符合公共利益、且不会让任何一方受到实质性损害——别指望这一点。',
  ko='1년 기한은 사건일부터 — 차별이 계속되는 경우에는 마지막 사건일부터 — 계산되며, 도착일부터가 아닙니다. 기한이 지난 진정도 받아들여질 수 있지만, 재판소가 공익에 부합하고 누구도 실질적 불이익을 받지 않는다고 판단할 때뿐입니다 — 기대하지 마세요.',
  ja='1年の期限は出来事の日から — 差別が続いている場合は最後の出来事の日から — 数え、到着日からではありません。期限後の申立ても受理されることはありますが、審判所が公益にかない、誰にも実質的な不利益がないと判断した場合だけです — 当てにしないでください。')
by['rights']['also'] = tx(
  en="Kamloops Immigrant Services' SPOKE program offers free short-term counselling and legal referrals, especially for women, girls and gender-diverse newcomers — you do not have to do this alone.",
  fr="Le programme SPOKE de Kamloops Immigrant Services offre du counseling gratuit à court terme et des orientations juridiques, en particulier pour les femmes, les filles et les personnes de diversité de genre nouvellement arrivées — vous n'avez pas à traverser cela seul(e).",
  es='El programa SPOKE de Kamloops Immigrant Services ofrece asesoría gratuita a corto plazo y derivaciones legales, especialmente para mujeres, niñas y personas de diversidad de género recién llegadas — no tiene que enfrentarlo solo.',
  zh='Kamloops Immigrant Services 的 SPOKE 项目提供免费的短期心理辅导和法律转介，尤其面向女性、女孩和性别多元新移民——你不用一个人面对这件事。',
  ko='Kamloops Immigrant Services의 SPOKE 프로그램은 무료 단기 상담과 법률 연계를 제공합니다. 특히 여성, 소녀, 성 다양성을 지닌 신규 이민자를 위한 것입니다 — 혼자 감당하지 않아도 됩니다.',
  ja='Kamloops Immigrant ServicesのSPOKEプログラムは、無料の短期カウンセリングと法律相談先の紹介を提供しています。特に女性、少女、性の多様な新規移住者向けです——一人で抱え込む必要はありません。')

# ---------------------------------------------------------------- bank (FCAC opening-a-bank-account page)
step('bank', 0, 'Walk into any branch', tx(
  en='Walk into any bank branch and say you want to open a personal chequing account.',
  fr='Entrez dans n’importe quelle succursale bancaire et dites que vous voulez ouvrir un compte-chèques personnel.',
  es='Entre en cualquier sucursal bancaria y diga que quiere abrir una cuenta de cheques personal.',
  zh='走进任何一家银行的分行，说你想开个人支票账户。',
  ko='아무 은행 지점에 들어가 개인 체킹 계좌를 열고 싶다고 말하세요.',
  ja='どの銀行の支店でもいいので入って、個人のチェッキング口座を開きたいと伝えましょう。'))
by['bank']['note'] = tx(
  en='A bank can still refuse for a few reasons — for example false information, fraud in the past seven years, or harassing staff — but not for being new or broke. These rights apply to banks; credit unions follow provincial rules.',
  fr='Une banque peut encore refuser pour quelques raisons — par exemple de fausses informations, une fraude au cours des sept dernières années ou du harcèlement envers le personnel — mais pas parce que vous êtes nouveau ou sans argent. Ces droits s’appliquent aux banques ; les coopératives de crédit suivent les règles provinciales.',
  es='Un banco todavía puede negarse por algunos motivos —por ejemplo información falsa, fraude en los últimos siete años o acoso al personal—, pero no por ser nuevo o no tener dinero. Estos derechos se aplican a los bancos; las cooperativas de crédito siguen normas provinciales.',
  zh='银行仍可以因少数原因拒绝——比如提供虚假信息、过去七年内有欺诈记录、骚扰员工——但不能因为你刚来或没钱就拒绝。这些权利适用于银行；信用合作社按省里的规定。',
  ko='은행은 몇 가지 이유 — 예를 들어 허위 정보, 최근 7년 내 사기 이력, 직원 괴롭힘 — 로는 거절할 수 있지만, 새로 왔거나 돈이 없다는 이유로는 거절할 수 없습니다. 이 권리는 은행에 적용되며, 신용협동조합은 주 규정을 따릅니다.',
  ja='銀行は、虚偽の情報、過去7年以内の詐欺、職員への嫌がらせなど、いくつかの理由では断れますが、来たばかりだから、お金がないからという理由では断れません。この権利は銀行に適用され、信用組合は州のルールに従います。')

# ---------------------------------------------------------------- legal (legalaid.bc.ca/services)
by['legal']['why'] = tx(
  en='Legal Aid BC covers family, child protection, criminal, immigration and refugee, mental health and prison law. Full representation depends on your income. It does not cover most tenancy, employment or debt problems — ask them where to go for those.',
  fr='Legal Aid BC couvre le droit de la famille, la protection de l’enfance, le droit criminel, l’immigration et les réfugiés, la santé mentale et le droit carcéral. La représentation complète dépend de votre revenu. La plupart des problèmes de logement, d’emploi ou de dettes ne sont pas couverts — demandez-leur où vous adresser.',
  es='Legal Aid BC cubre derecho de familia, protección de menores, penal, inmigración y refugio, salud mental y derecho penitenciario. La representación completa depende de sus ingresos. No cubre la mayoría de los problemas de alquiler, empleo o deudas: pregúnteles adónde acudir.',
  zh='Legal Aid BC 涵盖家庭、儿童保护、刑事、移民与难民、精神健康和监狱方面的法律问题。能否获得全程代理取决于你的收入。大多数租房、工作或债务问题不在范围内——可以问他们该去哪里。',
  ko='Legal Aid BC는 가족, 아동 보호, 형사, 이민·난민, 정신건강, 교정 관련 법률을 다룹니다. 전면 대리 여부는 소득에 따라 다릅니다. 대부분의 임대차, 고용, 채무 문제는 다루지 않으니 어디로 가야 하는지 물어보세요.',
  ja='Legal Aid BCは家族、児童保護、刑事、移民・難民、精神保健、刑務所に関する法律を扱います。全面的な代理は収入によります。賃貸、雇用、借金の問題の多くは対象外なので、どこに相談すればよいか聞いてみましょう。')

kamdata.save('TASKS', T)

# ---------------------------------------------------------------- elementary notes (SD73: no immunization records asked)
by_p = {p['id']: p for p in P}
ELEM = {
 'zh': 'SD73 学区小学；登记入学要带孩子的出生证明、BC Services Card、住址证明（有监护协议的也要带）',
 'en': 'SD73 elementary; to register, bring your child’s birth certificate, BC Services Card and proof of address (and a custody agreement if one applies)',
 'fr': 'École primaire du SD73 ; pour l’inscription, apportez l’acte de naissance de l’enfant, sa carte BC Services et une preuve d’adresse (et l’entente de garde, le cas échéant)',
 'es': 'Primaria del SD73; para inscribir, traiga la partida de nacimiento del niño, su BC Services Card y un comprobante de domicilio (y el acuerdo de custodia, si corresponde)',
 'ko': 'SD73 초등학교. 등록 시 아이의 출생증명서, BC Services Card, 주소 증빙(해당 시 양육권 합의서)을 가져오세요',
 'ja': 'SD73の小学校。登録には子どもの出生証明書、BC Services Card、住所の証明（該当する場合は親権の取り決め）を持参'}
for i in ('fb43944b', '7162c470', 'beee7266', '43a22995', 'b7096197', '4e13201f'):
    p = by_p[i]
    assert 'immuni' in p['note']['en'].lower(), i
    p['note'] = dict(ELEM); p['v'] = '2026-09'
kamdata.save('P', P)
print('phase 5 task edits applied')
