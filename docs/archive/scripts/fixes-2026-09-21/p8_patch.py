#!/usr/bin/env python3
"""2026-09-22 — three new cards (family doctor, renting safely, lost my job)
and a seasonal reminder on the first screen (winter driving, wildfire season).

Sources, each opened on 2026-09-22:
  healthlinkbc.ca/find-care/health-connect-registry
  www2.gov.bc.ca …/residential-tenancies/starting-a-tenancy/tenancy-agreements
  www2.gov.bc.ca …/starting-a-tenancy/move-in-condition-inspection
  www2.gov.bc.ca …/starting-a-tenancy/deposits-fees (deposit caps, already on the deposit card)
  bchousing.org/housing-assistance/rental-housing/subsidized-housing
  canada.ca/en/services/benefits/ei/ei-regular-benefit/apply.html
  www2.gov.bc.ca …/employment-standards/termination/quit-fired
  www2.gov.bc.ca …/income-assistance/apply-for-assistance
  www2.gov.bc.ca …/winter-driving/winter-tire-and-chain-up-routes and …/about-winter-tires
  kamloops.ca …/emergency-alert-notifications (Voyent Alert!), …/wildfire-interface-fires
  env.gov.bc.ca/epd/bcairquality/data/aqhi-table.html ; www2.gov.bc.ca/gov/content/safety/wildfire-status
New cards are appended; no existing card gains or loses a step."""
import sys, json
sys.path.insert(0, '.')
import kamdata

E, D, VAL = 'src/engine.html', 'src/data-kamloops.js', 'scripts/validate.py'
s = open(E, encoding='utf-8').read()
d = open(D, encoding='utf-8').read()
v = open(VAL, encoding='utf-8').read()
def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count: sys.exit('expected %d of %r, found %d' % (count, old[:90], n))
    return src.replace(old, new)
L6 = ('en', 'fr', 'es', 'zh', 'ko', 'ja')
def tx(**kw):
    assert set(kw) == set(L6), set(L6) ^ set(kw)
    return {l: kw[l] for l in L6}
def gl(**kw):
    assert set(kw) == {'zh', 'fr', 'es', 'ko', 'ja'}
    return {l: kw[l] for l in ('zh', 'fr', 'es', 'ko', 'ja')}

# ======================================================================== cards
DOCTOR = {
 'id': 'doctor', 'due': 'month3', 'icon': '📋', 'when': 'first', 'place': 'b29c9af7',
 'q': tx(en='I don’t have a family doctor', fr='Je n’ai pas de médecin de famille', es='No tengo médico de familia',
         zh='我没有家庭医生', ko='주치의가 없어요', ja='かかりつけ医がいません'),
 't': tx(en='Get on the list for a family doctor', fr='S’inscrire pour avoir un médecin de famille', es='Apuntarse para conseguir médico de familia',
         zh='登记排队找家庭医生', ko='주치의 대기 명단에 등록하기', ja='かかりつけ医の登録リストに入る'),
 'why': tx(
   en='Family doctors and nurse practitioners are matched from one provincial list, the Health Connect Registry. Clinic waitlists have moved into it, so this one registration is the way in.',
   fr='Les médecins de famille et les infirmières praticiennes sont attribués à partir d’une seule liste provinciale, le Health Connect Registry. Les listes d’attente des cliniques y ont été transférées : cette inscription est la porte d’entrée.',
   es='Los médicos de familia y enfermeras practicantes se asignan desde una sola lista provincial, el Health Connect Registry. Las listas de espera de las clínicas se trasladaron a ella, así que esta inscripción es la puerta de entrada.',
   zh='家庭医生和执业护士都从全省统一的一份名单里分配，叫 Health Connect Registry。各诊所原来的轮候名单已经并了进去，所以登记这一份就行。',
   ko='주치의와 전문 간호사는 주 전체의 명단 하나, Health Connect Registry에서 배정됩니다. 각 클리닉의 대기 명단도 여기로 옮겨졌으니, 여기에 등록하는 것이 입구입니다.',
   ja='かかりつけ医やナースプラクティショナーは、州で一つの名簿「Health Connect Registry」から紹介されます。各クリニックの順番待ちもここに移ったので、この登録が入口です。'),
 'steps': [
   tx(en='Once you have your Personal Health Number (on your BC Services Card), register online at HealthLink BC. It takes about five minutes: your PHN, home address, email and phone.',
      fr='Dès que vous avez votre numéro d’assurance maladie personnel (PHN, sur votre carte BC Services), inscrivez-vous en ligne sur HealthLink BC. Cela prend environ cinq minutes : votre PHN, votre adresse, votre courriel et votre téléphone.',
      es='En cuanto tenga su Personal Health Number (PHN, en su BC Services Card), inscríbase en línea en HealthLink BC. Tarda unos cinco minutos: su PHN, dirección, correo y teléfono.',
      zh='拿到个人健康号（PHN，印在 BC Services Card 上）后，就上 HealthLink BC 网站登记。大约五分钟：填 PHN、住址、邮箱和电话。',
      ko='개인 건강 번호(PHN, BC Services Card에 있음)가 나오면 HealthLink BC에서 온라인으로 등록하세요. 약 5분 걸립니다: PHN, 집 주소, 이메일, 전화번호.',
      ja='個人健康番号（PHN、BC Services Cardに記載）が届いたら、HealthLink BCでオンライン登録を。約5分：PHN、住所、メール、電話番号。'),
   tx(en='Rather use your own language? Call 8-1-1 and say the language you want — an interpreter joins the call (130+ languages). You can register your family members at the same time.',
      fr='Vous préférez votre langue ? Appelez le 8-1-1 et dites la langue voulue — un interprète se joint à l’appel (plus de 130 langues). Vous pouvez inscrire les membres de votre famille en même temps.',
      es='¿Prefiere su idioma? Llame al 8-1-1 y diga el idioma que quiere: un intérprete se une a la llamada (más de 130 idiomas). Puede inscribir a su familia al mismo tiempo.',
      zh='想用母语？打 8-1-1，说出你要的语言，翻译会加入通话（130 多种语言）。可以同时给家人一起登记。',
      ko='모국어가 편하세요? 8-1-1에 전화해 원하는 언어를 말하면 통역사가 통화에 들어옵니다(130개 이상 언어). 가족도 함께 등록할 수 있습니다.',
      ja='母語のほうが楽なら、8-1-1に電話して希望の言語を伝えると通訳が加わります（130以上の言語）。家族もまとめて登録できます。'),
   tx(en='While you wait: 8-1-1 any time; a pharmacist can renew prescriptions, prescribe birth control and treat 21 minor ailments; an urgent and primary care centre for same-day care.',
      fr='En attendant : le 8-1-1 à toute heure ; un pharmacien peut renouveler une ordonnance, prescrire une contraception et traiter 21 affections mineures ; un centre de soins urgents et primaires pour le jour même.',
      es='Mientras espera: el 8-1-1 a cualquier hora; un farmacéutico puede renovar recetas, recetar anticonceptivos y tratar 21 dolencias menores; un centro de atención urgente y primaria para el mismo día.',
      zh='轮候期间：8-1-1 随时可打；药剂师可以续开处方、开避孕药，处理 21 种轻症；当天要看就去紧急与基层医疗中心（UPCC）。',
      ko='기다리는 동안: 8-1-1은 언제든 가능, 약사는 처방 연장·피임약 처방과 21가지 경증 치료를 할 수 있고, 당일 진료는 긴급·1차 진료 센터(UPCC)로.',
      ja='待っている間：8-1-1はいつでも。薬剤師は処方の更新、避妊薬の処方、21の軽い症状の対応ができます。当日の受診は緊急・プライマリケアセンター（UPCC）へ。'),
 ],
 'note': tx(
   en='Registry emails come from healthconnectregistrydonotreply@hlth.gov.bc.ca. If you are not sure a message is real, call 8-1-1 before you click anything.',
   fr='Les courriels du registre viennent de healthconnectregistrydonotreply@hlth.gov.bc.ca. Si vous doutez qu’un message soit authentique, appelez le 8-1-1 avant de cliquer.',
   es='Los correos del registro llegan desde healthconnectregistrydonotreply@hlth.gov.bc.ca. Si duda de que un mensaje sea real, llame al 8-1-1 antes de hacer clic.',
   zh='登记处的邮件来自 healthconnectregistrydonotreply@hlth.gov.bc.ca。拿不准一封邮件是不是真的，先打 8-1-1 问，别急着点链接。',
   ko='등록처 이메일은 healthconnectregistrydonotreply@hlth.gov.bc.ca에서 옵니다. 진짜인지 확실하지 않으면 링크를 누르기 전에 8-1-1에 전화하세요.',
   ja='登録からのメールは healthconnectregistrydonotreply@hlth.gov.bc.ca から届きます。本物か分からないときは、リンクを押す前に8-1-1へ電話を。'),
 'help': tx(en='HealthLink BC · 8-1-1 · 24 hours · 130+ languages', fr='HealthLink BC · 8-1-1 · 24 h sur 24 · plus de 130 langues', es='HealthLink BC · 8-1-1 · 24 horas · más de 130 idiomas',
            zh='HealthLink BC · 8-1-1 · 24 小时 · 130 多种语言', ko='HealthLink BC · 8-1-1 · 24시간 · 130개 이상 언어', ja='HealthLink BC · 8-1-1 · 24時間 · 130以上の言語'),
 'src': 'https://www.healthlinkbc.ca/find-care/health-connect-registry', 'srcName': 'HealthLink BC',
 'say': 'Hi, I’d like to register for the Health Connect Registry. Could I have an interpreter in my language, please?',
 'sayGloss': gl(zh='（意思：您好，我想登记 Health Connect Registry。可以帮我安排一位说我母语的翻译吗？）',
                fr='(Sens : Bonjour, j’aimerais m’inscrire au Health Connect Registry. Puis-je avoir un interprète dans ma langue ?)',
                es='(Significado: Hola, quisiera inscribirme en el Health Connect Registry. ¿Podría tener un intérprete en mi idioma?)',
                ko='(뜻: 안녕하세요, Health Connect Registry에 등록하고 싶습니다. 제 언어 통역을 부탁드려도 될까요?)',
                ja='（意味：こんにちは、Health Connect Registryに登録したいです。私の言語の通訳をお願いできますか？）'),
 'alias': ['family doctor', 'doctor', 'GP', 'Health Connect', 'médecin', 'médico', '家庭医生', '家庭医', '医生', '주치의', '의사', 'かかりつけ医', '医者'],
}

HOUSING = {
 'id': 'housing', 'due': 'week1', 'icon': '🔑', 'when': 'first', 'place': 'd4b9d5c8',
 'q': tx(en='I need a place to rent and I’m worried about scams', fr='Je cherche un logement et je crains les arnaques', es='Busco un lugar para alquilar y temo las estafas',
         zh='我要租房，怕被骗', ko='집을 구해야 하는데 사기가 걱정돼요', ja='部屋を借りたいけど、詐欺が心配'),
 't': tx(en='Rent a place safely', fr='Louer un logement en sécurité', es='Alquilar con seguridad',
         zh='安全地租房', ko='안전하게 집 구하기', ja='安全に部屋を借りる'),
 'why': tx(
   en='Rental scams go after people who cannot view a place in person. BC law gives every tenant a written agreement, a capped deposit and a move-in inspection — insist on all three.',
   fr='Les arnaques au logement visent les personnes qui ne peuvent pas visiter sur place. En C.-B., la loi garantit à chaque locataire un bail écrit, un dépôt plafonné et une inspection d’entrée — exigez les trois.',
   es='Las estafas de alquiler apuntan a quien no puede ver el lugar en persona. La ley de BC da a cada inquilino un contrato escrito, un depósito con tope y una inspección de entrada: exija las tres cosas.',
   zh='租房骗局专找没法实地看房的人。BC 法律给每个租客三样保障：书面租约、有上限的押金、入住检查——三样都要坚持。',
   ko='임대 사기는 직접 집을 볼 수 없는 사람을 노립니다. BC주 법은 모든 세입자에게 서면 계약, 상한이 있는 보증금, 입주 점검을 보장합니다 — 세 가지 모두 요구하세요.',
   ja='賃貸詐欺は、現地で物件を見られない人を狙います。BC州の法律はすべての借り手に、書面の契約、上限のある敷金、入居時の点検を保障しています — 3つとも求めましょう。'),
 'steps': [
   tx(en='See the place in person, or on a live video call with someone you trust there, and meet the landlord or property manager before you pay anything. A listing that wants a deposit first “because the owner is away” is almost always a scam.',
      fr='Visitez sur place, ou en appel vidéo en direct avec une personne de confiance sur les lieux, et rencontrez le propriétaire ou le gestionnaire avant de payer quoi que ce soit. Une annonce qui exige un dépôt d’abord « parce que le propriétaire est absent » est presque toujours une arnaque.',
      es='Vea el lugar en persona, o por videollamada en vivo con alguien de confianza allí, y conozca al arrendador o administrador antes de pagar nada. Un anuncio que pide un depósito primero “porque el dueño está fuera” casi siempre es una estafa.',
      zh='付任何钱之前，先实地看房（或者请你信得过的人到现场、跟你视频直播），并见到房东或物业管理人。以“房东在外地”为由要你先转押金的房源，几乎都是骗局。',
      ko='돈을 내기 전에 직접 집을 보거나(또는 믿을 만한 사람이 현장에서 실시간 영상 통화), 집주인이나 관리인을 만나세요. “집주인이 멀리 있어서” 먼저 보증금을 보내라는 매물은 거의 다 사기입니다.',
      ja='お金を払う前に、現地で物件を見る（または信頼できる人に現地からライブ映像通話してもらう）こと、そして大家か管理会社に会うこと。「オーナーが不在なので」先に敷金をという物件は、ほぼ詐欺です。'),
   tx(en='Get a written tenancy agreement with the standard terms (the RTB-1 form has them all) and read it before you sign. The landlord must give you a signed copy within 21 days.',
      fr='Exigez un bail écrit avec les clauses standard (le formulaire RTB-1 les contient toutes) et lisez-le avant de signer. Le propriétaire doit vous remettre une copie signée dans les 21 jours.',
      es='Pida un contrato de arrendamiento escrito con las cláusulas estándar (el formulario RTB-1 las tiene todas) y léalo antes de firmar. El arrendador debe darle una copia firmada en un plazo de 21 días.',
      zh='拿到一份写有标准条款的书面租约（RTB-1 表格里全都有），签之前读一遍。房东必须在 21 天内给你一份双方签字的副本。',
      ko='표준 조항이 들어간 서면 임대 계약서(RTB-1 양식에 모두 있음)를 받아 서명 전에 읽으세요. 집주인은 21일 안에 서명된 사본을 줘야 합니다.',
      ja='標準条項の入った書面の賃貸契約（RTB-1の書式にすべてあります）をもらい、署名前に読みましょう。大家は21日以内に署名済みの控えを渡す義務があります。'),
   tx(en='Pay no more than half a month’s rent as a security deposit (and no more than another half for a pet). Pay in a way that leaves a record, and keep the receipt.',
      fr='Ne payez pas plus d’un demi-mois de loyer en dépôt de garantie (et pas plus d’un autre demi-mois pour un animal). Payez d’une façon qui laisse une trace, et gardez le reçu.',
      es='No pague más de medio mes de alquiler como depósito de garantía (ni más de otro medio mes por una mascota). Pague de una forma que deje constancia y guarde el recibo.',
      zh='押金最多半个月房租（养宠物的话，宠物押金最多再加半个月）。用能留下记录的方式付款，收据留好。',
      ko='보증금은 월세의 절반을 넘지 않게(반려동물 보증금도 최대 절반 더). 기록이 남는 방법으로 내고 영수증을 보관하세요.',
      ja='敷金は家賃の半月分まで（ペットの敷金もさらに半月分まで）。記録が残る方法で払い、領収書を保管しましょう。'),
   tx(en='Do the move-in inspection with the landlord on the day you get the keys, take photos, and get your copy of the report within 7 days — it is what gets your deposit back.',
      fr='Faites l’inspection d’entrée avec le propriétaire le jour de la remise des clés, prenez des photos et obtenez votre copie du rapport dans les 7 jours — c’est ce qui vous permettra de récupérer votre dépôt.',
      es='Haga la inspección de entrada con el arrendador el día que reciba las llaves, tome fotos y reciba su copia del informe en 7 días: es lo que le devuelve el depósito.',
      zh='拿钥匙那天和房东一起做入住检查，多拍照片，7 天内拿到检查报告的副本——以后能不能拿回押金就靠它。',
      ko='열쇠를 받는 날 집주인과 함께 입주 점검을 하고 사진을 찍어 두고, 7일 안에 보고서 사본을 받으세요 — 보증금을 돌려받는 근거가 됩니다.',
      ja='鍵を受け取る日に大家と一緒に入居時の点検をし、写真を撮り、7日以内に報告書の控えをもらいましょう — 敷金を取り戻す決め手になります。'),
 ],
 'note': tx(
   en='Rent can be raised only once every 12 months, with three full months’ written notice on the official form. For subsidised housing, apply through BC Housing’s Housing Registry (1-800-257-7756); each household member must be a citizen or permanent resident not under sponsorship, a government-assisted refugee, or a refugee claimant.',
   fr='Le loyer ne peut augmenter qu’une fois tous les 12 mois, avec trois mois complets de préavis écrit sur le formulaire officiel. Pour un logement subventionné, faites la demande au Housing Registry de BC Housing (1-800-257-7756) ; chaque membre du ménage doit être citoyen ou résident permanent non parrainé, réfugié parrainé par le gouvernement ou demandeur d’asile.',
   es='El alquiler solo puede subir una vez cada 12 meses, con tres meses completos de aviso por escrito en el formulario oficial. Para vivienda subvencionada, solicítela en el Housing Registry de BC Housing (1-800-257-7756); cada miembro del hogar debe ser ciudadano o residente permanente no patrocinado, refugiado patrocinado por el gobierno o solicitante de refugio.',
   zh='房租 12 个月内只能涨一次，而且要用官方表格提前整整三个月书面通知。申请政府补贴住房，走 BC Housing 的 Housing Registry（1-800-257-7756）；家里每个成员都必须是不在担保期内的公民或永久居民、政府资助的难民，或难民申请人。',
   ko='월세는 12개월에 한 번만 올릴 수 있고, 공식 양식으로 꼬박 3개월 전에 서면 통지해야 합니다. 보조 주택은 BC Housing의 Housing Registry(1-800-257-7756)로 신청하며, 가구원 모두가 스폰서 기간이 아닌 시민·영주권자, 정부 지원 난민, 또는 난민 신청자여야 합니다.',
   ja='家賃の値上げは12か月に1回だけで、公式の書式で丸3か月前に書面の通知が必要です。補助付き住宅はBC HousingのHousing Registry（1-800-257-7756）で申請します。世帯全員が、スポンサー期間中でない市民か永住者、政府支援の難民、または難民申請者であることが条件です。'),
 'help': tx(en='Residential Tenancy Branch · 1-800-665-8779', fr='Residential Tenancy Branch · 1-800-665-8779', es='Residential Tenancy Branch · 1-800-665-8779',
            zh='Residential Tenancy Branch（租房纠纷处）· 1-800-665-8779', ko='Residential Tenancy Branch · 1-800-665-8779', ja='Residential Tenancy Branch · 1-800-665-8779'),
 'src': 'https://www2.gov.bc.ca/gov/content/housing-tenancy/residential-tenancies/starting-a-tenancy', 'srcName': 'BC Residential Tenancy Branch',
 'say': 'Hi, could I see the place in person before I pay anything? And will we sign the standard tenancy agreement?',
 'sayGloss': gl(zh='（意思：您好，付钱之前我能先实地看房吗？我们会签标准租约吗？）',
                fr='(Sens : Bonjour, puis-je visiter le logement avant de payer quoi que ce soit ? Et signerons-nous le bail standard ?)',
                es='(Significado: Hola, ¿puedo ver el lugar en persona antes de pagar nada? ¿Y firmaremos el contrato estándar?)',
                ko='(뜻: 안녕하세요, 돈을 내기 전에 직접 집을 볼 수 있을까요? 그리고 표준 임대 계약서에 서명하나요?)',
                ja='（意味：こんにちは、お金を払う前に物件を直接見られますか？それと、標準の賃貸契約に署名しますか？）'),
 'alias': ['rent', 'rental', 'apartment', 'scam', 'lease', 'landlord', 'loyer', 'alquiler', '租房', '房东', '骗局', '租约', '월세', '집주인', '사기', '家賃', '大家', '詐欺'],
}

JOBLOSS = {
 'id': 'jobloss', 'due': 'need', 'icon': '💼', 'when': 'problem', 'place': 'd72e1296',
 'q': tx(en='I lost my job', fr='J’ai perdu mon emploi', es='Perdí mi trabajo', zh='我失业了', ko='일자리를 잃었어요', ja='仕事を失いました'),
 't': tx(en='After a job loss: money, your rights, the next job', fr='Après une perte d’emploi : argent, droits, prochain emploi', es='Tras perder el empleo: dinero, derechos, próximo trabajo',
         zh='失业之后：钱、权利、下一份工作', ko='실직 후: 돈, 권리, 다음 일자리', ja='失業したら：お金、権利、次の仕事'),
 'why': tx(
   en='Apply for Employment Insurance right away — applying more than four weeks after your last day can cost you benefits. This is what these programs are for; using them says nothing about you.',
   fr='Demandez l’assurance-emploi tout de suite — une demande faite plus de quatre semaines après votre dernier jour peut vous faire perdre des prestations. Ces programmes existent pour cela ; les utiliser ne dit rien de vous.',
   es='Solicite el seguro de empleo enseguida: pedirlo más de cuatro semanas después de su último día puede costarle prestaciones. Para eso existen estos programas; usarlos no dice nada de usted.',
   zh='马上申请失业保险（EI）——最后一天工作后超过四周才申请，可能会少拿钱。这些项目本来就是为这种时候设的，用它不说明你有什么问题。',
   ko='고용보험(EI)은 바로 신청하세요 — 마지막 근무일로부터 4주가 지나서 신청하면 받을 금액을 잃을 수 있습니다. 이런 제도는 바로 이럴 때 쓰라고 있는 것이고, 이용한다고 해서 당신에 대해 달라지는 것은 없습니다.',
   ja='雇用保険（EI）はすぐに申請を — 最終勤務日から4週間を過ぎて申請すると、受け取れる額が減ることがあります。こうした制度はこういう時のためにあり、使うことはあなたの評価とは関係ありません。'),
 'steps': [
   tx(en='Apply for EI online now — you do not need your Record of Employment first; documents can follow. Have your SIN, bank details for direct deposit, and your employers from the past 52 weeks. (A SIN starting with 9 also needs your immigration papers and work permit.) There is a one-week unpaid waiting period.',
      fr='Demandez l’assurance-emploi en ligne dès maintenant — pas besoin d’attendre votre relevé d’emploi ; les documents peuvent suivre. Préparez votre NAS, vos coordonnées bancaires pour le dépôt direct et vos employeurs des 52 dernières semaines. (Un NAS commençant par 9 exige aussi vos papiers d’immigration et votre permis de travail.) Il y a un délai de carence d’une semaine non payée.',
      es='Solicite el EI en línea ya: no necesita antes su Record of Employment; los documentos pueden llegar después. Tenga a mano su SIN, datos bancarios para depósito directo y sus empleadores de las últimas 52 semanas. (Un SIN que empieza por 9 requiere además sus documentos migratorios y permiso de trabajo.) Hay una semana de espera sin pago.',
      zh='现在就上网申请 EI——不用等雇主的离职证明（Record of Employment），文件可以之后补。准备好 SIN、用于直接入账的银行信息、过去 52 周所有雇主的信息。（SIN 以 9 开头的，还要提供移民身份文件和工签。）有一周不发钱的等待期。',
      ko='지금 온라인으로 EI를 신청하세요 — 고용 기록(ROE)을 먼저 받을 필요는 없고 서류는 나중에 내도 됩니다. SIN, 자동 입금용 은행 정보, 지난 52주 동안의 고용주 정보를 준비하세요. (9로 시작하는 SIN이면 이민 서류와 취업 허가서도 필요합니다.) 1주일의 무급 대기 기간이 있습니다.',
      ja='今すぐオンラインでEIを申請 — 離職票（Record of Employment）を待つ必要はなく、書類は後から出せます。SIN、振込用の口座情報、過去52週の雇用主の情報を用意。（9で始まるSINの人は在留書類と就労許可も必要。）1週間の無給の待機期間があります。'),
   tx(en='Check your final pay. If your employer ended your job, everything owed is due within 48 hours (within 6 days if you quit). After more than 3 months in the job you are owed written notice or pay instead: 1 week, 2 weeks after a year, 3 weeks after three years, then one more week for each further year — unless it was for just cause.',
      fr='Vérifiez votre dernière paie. Si l’employeur a mis fin à l’emploi, tout ce qui vous est dû doit être payé dans les 48 heures (6 jours si vous avez démissionné). Après plus de 3 mois, vous avez droit à un préavis écrit ou à une indemnité : 1 semaine, 2 semaines après un an, 3 semaines après trois ans, puis une semaine de plus par année supplémentaire — sauf congédiement pour motif valable.',
      es='Revise su último pago. Si el empleador terminó el empleo, todo lo que le deben vence en 48 horas (6 días si usted renunció). Con más de 3 meses en el puesto, le corresponde aviso por escrito o pago en su lugar: 1 semana, 2 semanas tras un año, 3 semanas tras tres años y una semana más por cada año adicional, salvo despido con causa justa.',
      zh='核对最后一笔工资。如果是雇主解雇你，欠你的钱必须在 48 小时内付清（你自己辞职的是 6 天内）。工作超过 3 个月，你有权得到书面提前通知或相应的补偿：1 周；满 1 年 2 周；满 3 年 3 周，之后每多 1 年再加 1 周——因正当理由（just cause）被解雇的除外。',
      ko='마지막 급여를 확인하세요. 고용주가 해고했다면 밀린 돈은 48시간 안에(스스로 그만뒀다면 6일 안에) 모두 지급해야 합니다. 3개월 넘게 일했다면 서면 예고나 그만큼의 수당을 받을 권리가 있습니다: 1주, 1년 넘으면 2주, 3년 넘으면 3주, 이후 1년마다 1주씩 추가 — 정당한 사유에 의한 해고는 제외.',
      ja='最後の給与を確認。雇用主から解雇された場合、未払い分はすべて48時間以内（自分で辞めた場合は6日以内）に支払われる決まりです。3か月を超えて働いていれば、書面の予告か代わりの手当を受け取れます：1週間、1年を超えると2週間、3年を超えると3週間、その後は1年ごとに1週間追加 — 正当な理由による解雇を除く。'),
   tx(en='If you have no other money coming, apply for BC income assistance through My Self Serve or at 1-866-866-0800. In most cases you first show a three-week work search.',
      fr='Si aucun autre revenu n’arrive, demandez l’aide au revenu de la C.-B. par My Self Serve ou au 1-866-866-0800. Dans la plupart des cas, il faut d’abord montrer trois semaines de recherche d’emploi.',
      es='Si no le llega otro dinero, solicite la asistencia de ingresos de BC por My Self Serve o al 1-866-866-0800. En la mayoría de los casos primero debe mostrar tres semanas de búsqueda de empleo.',
      zh='如果没有别的收入来源，通过 My Self Serve 或打 1-866-866-0800 申请 BC 省的社会救助（income assistance）。多数情况下要先做满三周的求职记录。',
      ko='다른 수입이 없다면 My Self Serve나 1-866-866-0800으로 BC주 소득 지원을 신청하세요. 대부분 먼저 3주간의 구직 활동 기록이 필요합니다.',
      ja='ほかに入ってくるお金がなければ、My Self Serve か 1-866-866-0800 でBC州の生活扶助を申請。多くの場合、先に3週間の求職活動の記録が必要です。'),
   tx(en='For the next job, a WorkBC centre helps free: job search, résumés, and training you may qualify for.',
      fr='Pour le prochain emploi, un centre WorkBC aide gratuitement : recherche d’emploi, CV et formations auxquelles vous pourriez avoir droit.',
      es='Para el próximo trabajo, un centro WorkBC ayuda gratis: búsqueda de empleo, currículum y formación a la que podría tener derecho.',
      zh='找下一份工作，WorkBC 中心免费帮忙：求职、改简历，以及你可能符合条件的培训。',
      ko='다음 일자리는 WorkBC 센터가 무료로 도와줍니다: 구직, 이력서, 받을 수 있는 교육.',
      ja='次の仕事探しは、WorkBCセンターが無料で手伝います：求職、履歴書、対象になりうる職業訓練。'),
 ],
 'note': tx(
   en='If a family member sponsored you into Canada, the income assistance application asks about it — ask a settlement worker or Legal Aid (free) how it affects you before you apply.',
   fr='Si un membre de votre famille vous a parrainé au Canada, la demande d’aide au revenu vous le demande — renseignez-vous auprès d’un intervenant en établissement ou de l’aide juridique (gratuit) avant de faire la demande.',
   es='Si un familiar le patrocinó para venir a Canadá, la solicitud de asistencia de ingresos lo pregunta: consulte a un trabajador de asentamiento o a Legal Aid (gratis) cómo le afecta antes de solicitar.',
   zh='如果你是家人担保来加拿大的，社会救助申请表会问到这一点——申请前先问定居服务专员或法律援助（免费），了解对你有什么影响。',
   ko='가족의 초청(스폰서)으로 캐나다에 왔다면 소득 지원 신청서에서 그것을 묻습니다 — 신청 전에 정착 지원 담당자나 Legal Aid(무료)에 어떤 영향이 있는지 물어보세요.',
   ja='家族のスポンサーでカナダに来た場合、生活扶助の申請でそのことを聞かれます — 申請前に定住支援ワーカーか法律扶助（無料）に、どう影響するか相談を。'),
 'help': tx(en='Employment Standards Branch · 1-833-236-3700 · income assistance 1-866-866-0800', fr='Employment Standards Branch · 1-833-236-3700 · aide au revenu 1-866-866-0800',
            es='Employment Standards Branch · 1-833-236-3700 · asistencia de ingresos 1-866-866-0800', zh='劳工标准处 · 1-833-236-3700 · 社会救助 1-866-866-0800',
            ko='Employment Standards Branch · 1-833-236-3700 · 소득 지원 1-866-866-0800', ja='Employment Standards Branch · 1-833-236-3700 · 生活扶助 1-866-866-0800'),
 'confid': tx(
   en='Feeling low after losing a job is common. The 24-hour mental health line is 310-6789 — no area code.',
   fr='Se sentir abattu après une perte d’emploi est courant. La ligne de santé mentale 24 h sur 24 est le 310-6789 — sans indicatif régional.',
   es='Sentirse decaído tras perder el empleo es común. La línea de salud mental de 24 horas es el 310-6789, sin código de área.',
   zh='失业后情绪低落很常见。24 小时心理支持热线 310-6789，不用加区号。',
   ko='실직 후 기분이 가라앉는 것은 흔한 일입니다. 24시간 정신건강 전화는 310-6789 — 지역번호 없이.',
   ja='失業後に気分が落ち込むのはよくあることです。24時間のこころの相談は310-6789（市外局番なし）。'),
 'src': 'https://www.canada.ca/en/services/benefits/ei/ei-regular-benefit/apply.html', 'srcName': 'Service Canada',
 'say': 'Hi, could you please send my Record of Employment, and tell me when my final pay will be deposited?',
 'sayGloss': gl(zh='（意思：您好，能帮我开离职证明（Record of Employment）吗？最后一笔工资什么时候到账？）',
                fr='(Sens : Bonjour, pourriez-vous envoyer mon relevé d’emploi et me dire quand ma dernière paie sera versée ?)',
                es='(Significado: Hola, ¿podría enviar mi Record of Employment y decirme cuándo me depositarán el último pago?)',
                ko='(뜻: 안녕하세요, 고용 기록(ROE)을 보내 주시고, 마지막 급여가 언제 입금되는지 알려 주시겠어요?)',
                ja='（意味：こんにちは、離職票（Record of Employment）を送っていただけますか？最後の給与はいつ振り込まれますか？）'),
 'alias': ['EI', 'unemployment', 'laid off', 'fired', 'job loss', 'chômage', 'desempleo', '失业', '被解雇', '失业保险', '실직', '해고', '고용보험', '失業', '解雇', '雇用保険'],
}

T = kamdata.load('TASKS')
ids = {t['id'] for t in T}
for c in (DOCTOR, HOUSING, JOBLOSS):
    assert c['id'] not in ids
    T.append(c)
kamdata.save('TASKS', T)
d = open(D, encoding='utf-8').read()

# ======================================================================== seasonal reminder (city data)
SEASON = """  // 2026-09-22: a one-line reminder on the map while a season is on. Dates are
  // MM-DD, inclusive; a range may wrap the new year. Each can be dismissed for
  // that season (the dismissal is keyed by season and year, on this device only).
  // Winter tires: www2.gov.bc.ca winter-tire-and-chain-up-routes (Oct 1–Apr 30 on
  // most routes). Wildfire: BC Wildfire Service, BC AQHI, the City's Voyent Alert!
  seasons:[
   {id:'winter',from:'10-01',to:'04-30',icon:'❄️',
    text:{en:'Winter driving: winter tires or chains are required on most BC highways from October 1 to April 30. Check the roads before you go.',
          fr:'Conduite d’hiver : pneus d’hiver ou chaînes obligatoires sur la plupart des routes de la C.-B. du 1er octobre au 30 avril. Vérifiez les routes avant de partir.',
          es:'Conducción en invierno: neumáticos de invierno o cadenas obligatorios en la mayoría de las carreteras de BC del 1 de octubre al 30 de abril. Revise las carreteras antes de salir.',
          zh:'冬季出行：10 月 1 日至 4 月 30 日，BC 大部分公路要求冬胎或防滑链。出门前先看路况。',
          ko:'겨울 운전: 10월 1일부터 4월 30일까지 BC주 대부분의 고속도로에서 겨울 타이어나 체인이 필수입니다. 출발 전에 도로 상황을 확인하세요.',
          ja:'冬の運転：10月1日から4月30日まで、BC州のほとんどの幹線道路で冬用タイヤかチェーンが必要です。出かける前に道路状況を確認を。'},
    links:[{u:'https://www.drivebc.ca/',t:{en:'Road conditions (DriveBC)',fr:'État des routes (DriveBC)',es:'Estado de las carreteras (DriveBC)',zh:'路况（DriveBC）',ko:'도로 상황(DriveBC)',ja:'道路状況（DriveBC）'}},
           {u:'https://www2.gov.bc.ca/gov/content/transportation/driving-and-cycling/traveller-information/seasonal/winter-driving/winter-tire-and-chain-up-routes',t:{en:'Which routes',fr:'Quelles routes',es:'Qué rutas',zh:'哪些路段',ko:'해당 도로',ja:'対象の道路'}}]},
   {id:'wildfire',from:'07-01',to:'09-30',icon:'🔥',
    text:{en:'Wildfire season: check the air quality before outdoor plans, and sign up for the City’s emergency alerts.',
          fr:'Saison des feux de forêt : vérifiez la qualité de l’air avant de sortir, et inscrivez-vous aux alertes d’urgence de la Ville.',
          es:'Temporada de incendios forestales: revise la calidad del aire antes de planes al aire libre y regístrese en las alertas de emergencia de la Ciudad.',
          zh:'山火季：户外活动前先看空气质量，并登记市政府的紧急警报。',
          ko:'산불 시즌: 야외 활동 전에 대기 질을 확인하고, 시의 긴급 경보에 등록하세요.',
          ja:'山火事シーズン：屋外の予定の前に大気の状態を確認し、市の緊急警報に登録しましょう。'},
    links:[{u:'https://www.env.gov.bc.ca/epd/bcairquality/data/aqhi-table.html',t:{en:'Air quality',fr:'Qualité de l’air',es:'Calidad del aire',zh:'空气质量',ko:'대기 질',ja:'大気の状態'}},
           {u:'https://www.kamloops.ca/public-safety/emergency-preparedness/emergency-alerts-orders/emergency-alert-notifications',t:{en:'Emergency alerts',fr:'Alertes d’urgence',es:'Alertas de emergencia',zh:'紧急警报',ko:'긴급 경보',ja:'緊急警報'}},
           {u:'https://www2.gov.bc.ca/gov/content/safety/wildfire-status',t:{en:'Wildfires now',fr:'Feux en cours',es:'Incendios activos',zh:'当前山火',ko:'현재 산불',ja:'現在の山火事'}}]}
  ],
"""
d = rep(d, "  help:{settle:'778-470-6101', info:'211'},", SEASON + "  help:{settle:'778-470-6101', info:'211'},")
open(D, 'w', encoding='utf-8').write(d)

# ======================================================================== engine: icons, season note, winter-tire wording
s = rep(s, "  receipt:'<path d=\"M6 3h12v18l-2-1.5-2 1.5-2-1.5-2 1.5-2-1.5L6 21z\"/><path d=\"M9 8h6M9 12h6M9 16h3\"/>',",
        "  receipt:'<path d=\"M6 3h12v18l-2-1.5-2 1.5-2-1.5-2 1.5-2-1.5L6 21z\"/><path d=\"M9 8h6M9 12h6M9 16h3\"/>',\n"
        "  briefcase:'<rect x=\"3\" y=\"7\" width=\"18\" height=\"13\" rx=\"2\"/><path d=\"M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2\"/><path d=\"M3 12h18\"/>',\n"
        "  flame:'<path d=\"M12 3c1 3 5 5.5 5 10a5 5 0 01-10 0c0-2.2 1.2-3.8 2.5-5 .3 1.6 1.2 2.6 2.2 3C11.5 8.5 11 5.5 12 3z\"/>',\n"
        "  clipboard:'<rect x=\"5\" y=\"4\" width=\"14\" height=\"17\" rx=\"2\"/><path d=\"M9 4V3h6v1\"/><path d=\"M9 10h6M9 14h6M9 18h3\"/>',")
s = rep(s, "'👨‍👩‍👧':'family'};", "'👨‍👩‍👧':'family','💼':'briefcase','🔥':'flame','📋':'clipboard'};")

s = rep(s, '<div class="firstuse" id="firstUse" hidden></div>',
        '<div class="firstuse" id="firstUse" hidden></div><div class="season-note" id="seasonNote" role="note" hidden></div>')
s = rep(s, "  .firstuse[hidden]{display:none;}",
        "  .firstuse[hidden]{display:none;}\n"
        "  /* 2026-09-22: the seasonal reminder sits where the first-use card sits, and\n"
        "     only when that card is gone — never two cards stacked over the map */\n"
        "  .season-note{position:absolute;z-index:840;left:12px;right:12px;top:10px;padding:8px 44px 8px 12px;border-radius:12px;background:rgba(255,255,255,.92);-webkit-backdrop-filter:saturate(180%) blur(14px);backdrop-filter:saturate(180%) blur(14px);border:1px solid rgba(0,0,0,.08);box-shadow:0 4px 16px rgba(0,0,0,.08);font-size:12.5px;line-height:1.45;color:var(--ink);}\n"
        "  .season-note[hidden]{display:none;}\n"
        "  .season-note .sn-ic .ic{width:15px;height:15px;vertical-align:-3px;margin-right:4px;}\n"
        "  .season-note .sn-links{display:flex;flex-wrap:wrap;gap:2px 12px;margin-top:3px;}\n"
        "  .season-note .sn-links a{color:var(--accent-text);font-weight:600;text-decoration:none;}\n"
        "  .season-note .sn-x{position:absolute;top:0;right:0;background:none;border:none;font-size:15px;line-height:1;padding:6px;cursor:pointer;color:var(--sub-ink);min-width:44px;min-height:44px;}\n"
        "  @media(min-width:700px){.season-note{left:auto;right:16px;top:16px;width:min(380px,calc(100% - 32px));}}")

SEASON_JS = r"""// --- 2026-09-22: the seasonal reminder ------------------------------------
// One line on the map while a season from CITY.seasons is on. It waits for the
// first-use card, steps aside for a place card or a drawn route, and once
// closed stays closed for that season on this device.
function activeSeason(){
  const iso=cityISODate();if(!iso||!CITY.seasons)return null;
  const md=iso.slice(5);
  return CITY.seasons.find(x=>x.from<=x.to?(md>=x.from&&md<=x.to):(md>=x.from||md<=x.to))||null;
}
function seasonKey(x){
  const iso=cityISODate(),y=parseInt(iso.slice(0,4),10),md=iso.slice(5);
  // a season that wraps the new year belongs to the year it started in
  return 'kamloopsSeason_'+x.id+'_'+(x.from>x.to&&md<=x.to?y-1:y);
}
let _seasonClosedMem={};
function renderSeason(){
  const el=document.getElementById('seasonNote');if(!el)return;
  const x=activeSeason(),fu=document.getElementById('firstUse');
  let closed=false;
  if(x){closed=!!_seasonClosedMem[x.id];try{closed=closed||localStorage.getItem(seasonKey(x))==='1';}catch(e){}}
  const busy=(fu&&!fu.hidden)||!!selectedRoute||!!(typeof map!=='undefined'&&map._popup&&map._popup.isOpen&&map._popup.isOpen());
  if(!x||closed||busy){el.hidden=true;return;}
  const u=UI[L_];
  el.innerHTML='<span class="sn-ic">'+emojiIcon(x.icon)+'</span>'+esc(x.text[L_]||x.text.en)
    +'<span class="sn-links">'+x.links.map(k=>'<a href="'+esc(k.u)+'" target="_blank" rel="noopener" data-season-link="'+esc(x.id)+'">'+esc(k.t[L_]||k.t.en)+' ›</a>').join('')+'</span>'
    +'<button type="button" class="sn-x" id="seasonClose" aria-label="'+esc(u.aClose)+'">✕</button>';
  el.hidden=false;
  document.getElementById('seasonClose').onclick=()=>{
    _seasonClosedMem[x.id]=true;try{localStorage.setItem(seasonKey(x),'1');}catch(e){}
    el.hidden=true;trackEvent('season_close',{id:x.id});
  };
  el.querySelectorAll('[data-season-link]').forEach(a=>a.onclick=()=>trackEvent('season_link',{id:x.id,to:a.getAttribute('href').split('/')[2]}));
}
"""
s = rep(s, "function dismissFirstUse(src){\n  const el=document.getElementById('firstUse');\n  if(!el||el.hidden)return;\n  _fuDismissed=true;   // storage may be blocked (private mode); remember in memory for this sitting\n  try{localStorage.setItem(_FU_KEY,'1');}catch(e){}\n  el.hidden=true;\n",
        SEASON_JS + "function dismissFirstUse(src){\n  const el=document.getElementById('firstUse');\n  if(!el||el.hidden)return;\n  _fuDismissed=true;   // storage may be blocked (private mode); remember in memory for this sitting\n  try{localStorage.setItem(_FU_KEY,'1');}catch(e){}\n  el.hidden=true;\n  try{renderSeason();}catch(e){}\n")
open(E, 'w', encoding='utf-8').write(s)


s = open(E, encoding='utf-8').read()
s = rep(s, "  setHL('noteToggle',u.noteToggleLabel);\n  renderFirstUse();\n", "  setHL('noteToggle',u.noteToggleLabel);\n  renderFirstUse();\n  try{renderSeason();}catch(e){}\n")
s = rep(s, "map.on('popupopen',e=>{\n", "map.on('popupopen',e=>{\n  try{document.getElementById('seasonNote').hidden=true;}catch(_){}\n")
s = rep(s, "map.on('popupclose',()=>{\n", "map.on('popupclose',()=>{\n  setTimeout(()=>{try{renderSeason();}catch(_){}},0);\n")
s = rep(s, "  renderRoute(key,!(opts&&opts.keepView));\n  closePanel();\n", "  renderRoute(key,!(opts&&opts.keepView));\n  closePanel();\n  try{renderSeason();}catch(e){}\n")
open(E, 'w', encoding='utf-8').write(s)

# the long guide had the emphasis the wrong way round (gov.bc.ca: most routes Oct 1–Apr 30; select ones end Mar 31)
TIRE = {
 'most BC mountain highways require them from October 1 to March 31, with some routes extended to April 30.':
 'most BC highways require them from October 1 to April 30, and a few routes outside the mountain passes end on March 31.',
 'la plupart des routes de montagne de la C.-B. les exigent du 1er octobre au 31 mars, certaines jusqu\'au 30 avril.':
 'la plupart des routes de la C.-B. les exigent du 1er octobre au 30 avril, et quelques routes hors des cols de montagne s\'arrêtent au 31 mars.',
 'la mayoría de las carreteras de montaña de BC los exigen del 1 de octubre al 31 de marzo, y algunas rutas hasta el 30 de abril.':
 'la mayoría de las carreteras de BC los exigen del 1 de octubre al 30 de abril, y algunas rutas fuera de los pasos de montaña terminan el 31 de marzo.',
 'BC주의 산악 고속도로 대부분은 매년 10월 1일부터 3월 31일까지(일부 구간은 4월 30일까지) 겨울용 타이어를 의무화합니다.':
 'BC주의 고속도로 대부분은 매년 10월 1일부터 4월 30일까지 겨울용 타이어를 의무화하며, 산악 고개가 아닌 일부 구간은 3월 31일에 끝납니다.',
 '本省大量山区公路在每年10月1日至次年3月31日（部分路段延长至4月30日）强制要求冬季轮胎':
 '本省大部分公路在每年10月1日至次年4月30日强制要求冬季轮胎（少数不经过山口的路段到3月31日为止）',
 'BC州のほとんどの山岳道路では10月1日から3月31日まで（一部は4月30日まで延長）冬用タイヤの装着が義務付けられています。':
 'BC州のほとんどの道路では10月1日から4月30日まで冬用タイヤの装着が義務付けられています（山岳の峠を通らない一部の道路は3月31日まで）。',
}
s = open(E, encoding='utf-8').read()
for a, b in TIRE.items():
    s = rep(s, a, b)
open(E, 'w', encoding='utf-8').write(s)

# ======================================================================== validate: the new cards' places
v = rep(v, "  'legal': {'legal'}, 'eldercare': {'commctr','hospital','support'},",
        "  'legal': {'legal'}, 'eldercare': {'commctr','hospital','support'}, 'jobloss': {'gov'}, 'doctor': {'hospital'}, 'housing': {'legal'},")
open(VAL, 'w', encoding='utf-8').write(v)
print('p8 applied: 3 cards, seasonal note, tire wording')
