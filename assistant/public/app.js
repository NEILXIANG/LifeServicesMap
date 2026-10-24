// app.js — 助手界面。界面文字六种语言（zh/en/fr/es/ko/ja，与指南一致）；回答默认用提问的语言。
// 不在浏览器里保存提问和回答；只记住界面语言。

const T = {
  zh: {
    intro: 'AI 根据 Kamloops 生活指南中已核实的内容回答，可能出错，重要信息请以官方来源为准。本工具是独立制作的，不是 Kamloops Immigrant Services 或政府的服务。',
    privacy: '请勿输入姓名、证件号码、病情等个人信息。你的问题会发给 AI 服务来生成回答。', qLabel: '问题', placeholder: '用任何语言提问——例如：怎么办 SIN？', ask: '提问',
    quickLabel: '常见问题', quick1t: '新到第一周', quick2t: '孩子入学', quick3t: '找家庭医生', quick4t: '食物银行',
    quick1: '刚到 Kamloops 第一周要办哪些事？', quick2: '孩子刚到 Kamloops，怎么报名上学？', quick3: '怎么找家庭医生？', quick4: '食物银行在哪里，怎么用？',
    privacyLink: '隐私说明', guideLink: 'Kamloops 生活指南',
    loading: '正在查找指南里的相关内容……', announce: '新回答已生成',
    sources: '来源', checked: '核实', official: '官方页面', inGuide: '在指南中打开', notChecked: '未标核实日期',
    tierOfficial: '官方', tierOwn: '本人核实', tierPlaces: '第三方资料',
    footer: 'AI 根据指南整理，以官方信息为准。',
    stale: '部分依据超过 6 个月未核实，此信息需向机构再次确认。',
    referral: '可以找谁帮忙：', copy: '复制', copied: '已复制',
    client: '生成客户语言版本', clientPick: '选择语言…', clientNote: 'AI 翻译，供参考；以链接中的官方信息为准。', translating: '正在翻译……',
    trFail: '翻译未通过核对（电话或网址与原文不一致），请直接使用原文。',
    fbQ: '这个回答：', useful: '有用', wrong: '有错', fbPh: '错在哪里（一句话，不含个人信息）', fbSend: '提交', fbThanks: '谢谢，已记录。',
    notFound: '指南里没有已核实的相关信息', outScope: '这要看你的具体情况',
    tryThese: '可以试试：', relatedCards: '指南里相关的办事卡：',
    crisisTitle: '紧急求助', crisisLead: '这个问题可能涉及安全或危机。助手不会用 AI 回答，请直接使用下面的求助电话。有生命危险请立即拨 911。',
    crisisLocal: '本地专线', sms: '短信',
    errTitle: '暂时无法回答', errLead: '请稍后再试，或直接查看生活指南。', retry: '重试',
    reasons: { too_fast: '提问太快了，请等一分钟再试。', visitor_limit: '这是测试版，为了控制预算，每人每天最多可以问 10 个问题。你今天的次数已用完，请明天再试；需要帮助可以拨打 2-1-1，或查看生活指南。', daily_limit: '这是测试版，为了控制预算，全站每天的提问次数有限，今天已经用完了。请明天再试；需要帮助可以拨打 2-1-1，或查看生活指南。', ai_not_configured: 'AI 服务尚未配置。', ai_key: 'AI 服务的密钥无效或余额不足。', rate_limited: 'AI 服务繁忙。', too_long: '问题太长了（最多 1000 字）。', empty: '请输入问题。', forbidden: '没有访问权限，请重新登录。' },
    loading2: '正在整理回答……', loading3: '快好了——回答通常需要 5–15 秒。', quotaLeft: '测试版：今天还可以问 {n} 题（每天 {m} 题）。', limitTitle: '今天的提问次数已用完', youAsked: '你的问题：', piiTitle: '这里好像有个人信息', piiLead: '你的问题里好像有电话号码、邮箱或证件号码。回答不需要这些，而且问题会发给 AI 服务，请先删掉。', piiEdit: '修改问题', piiSend: '仍然发送', share: '分享', mapLink: '在指南地图上找', askAnother: '再问一个问题', call911: '拨打 911', backToAsk: '返回提问', offtopic: '没回答我的问题', fbPhOff: '你想找的是什么？（一句话，不含个人信息）', offline: '你现在没有联网。提问需要网络；生活指南可以离线使用。', earlier: '之前的回答',
    examples: ['用任何语言提问——例如：怎么办 SIN？', '用任何语言提问——例如：哪里有免费的法律咨询？', '用任何语言提问——例如：房东不退押金怎么办？'],
  },
  en: {
    intro: 'Answers come from verified content in the Kamloops Life Guide, written by AI, and may contain errors. Check important details with the official source. This is an independent tool — not a service of Kamloops Immigrant Services or the government.',
    privacy: 'Do not enter your name, ID numbers, health details or other personal information. Your question is sent to an AI service to write the answer.', qLabel: 'Question', placeholder: 'Ask in any language — e.g. How do I get a SIN?', ask: 'Ask',
    quickLabel: 'Common questions', quick1t: 'First week', quick2t: 'School enrolment', quick3t: 'Family doctor', quick4t: 'Food bank',
    quick1: 'What should a newcomer do in their first week in Kamloops?', quick2: 'How do I enrol a child who just arrived in Kamloops in school?', quick3: 'How do I find a family doctor?', quick4: 'Where is the food bank and how does it work?',
    privacyLink: 'Privacy', guideLink: 'Kamloops Life Guide',
    loading: 'Looking up the guide…', announce: 'New answer ready',
    sources: 'Sources', checked: 'checked', official: 'Official page', inGuide: 'Open in the guide', notChecked: 'no check date',
    tierOfficial: 'official', tierOwn: 'checked by the author', tierPlaces: 'third-party listing',
    footer: 'Compiled by AI from the guide. Official sources take precedence.',
    stale: 'Some of this has not been checked for over 6 months — confirm with the organisation.',
    referral: 'Who can help:', copy: 'Copy', copied: 'Copied',
    client: 'Client-language version', clientPick: 'Choose a language…', clientNote: 'AI translation for reference; the official information at the link takes precedence.', translating: 'Translating…',
    trFail: 'The translation failed the check (a phone number or web address changed). Please use the original.',
    fbQ: 'This answer:', useful: 'Useful', wrong: 'Wrong', fbPh: 'What is wrong (one sentence, no personal details)', fbSend: 'Send', fbThanks: 'Thank you — noted.',
    notFound: 'The guide has no verified information on this', outScope: 'This depends on your own situation',
    tryThese: 'You could try:', relatedCards: 'Related task cards in the guide:',
    crisisTitle: 'Urgent help', crisisLead: 'This question may involve safety or a crisis. The assistant does not answer it with AI — please use the lines below. If a life is in danger, call 911 now.',
    crisisLocal: 'Local lines', sms: 'text',
    errTitle: 'Can’t answer right now', errLead: 'Please try again later, or use the Life Guide directly.', retry: 'Try again',
    reasons: { too_fast: 'Too many questions in a short time. Please wait a minute.', visitor_limit: 'This is a test version. To keep within budget, each person can ask up to 10 questions a day, and you have reached today’s limit. Please try again tomorrow — for help now, call 2-1-1 or use the Life Guide.', daily_limit: 'This is a test version. To keep within budget, the number of questions for the whole site is limited each day, and today’s have been used up. Please try again tomorrow — for help now, call 2-1-1 or use the Life Guide.', ai_not_configured: 'The AI service is not configured yet.', ai_key: 'The AI service key is invalid or out of credit.', rate_limited: 'The AI service is busy.', too_long: 'The question is too long (1,000 characters at most).', empty: 'Please type a question.', forbidden: 'No access — please sign in again.' },
    loading2: 'Writing the answer…', loading3: 'Almost done — answers usually take 5–15 seconds.', quotaLeft: 'Test version: {n} of {m} questions left today.', limitTitle: 'Today’s questions are used up', youAsked: 'Your question:', piiTitle: 'This looks like personal information', piiLead: 'Your question seems to include a phone number, email address or ID number. You don’t need it to get an answer, and the question is sent to an AI service — please remove it.', piiEdit: 'Edit my question', piiSend: 'Send anyway', share: 'Share', mapLink: 'Find on the guide map', askAnother: 'Ask another question', call911: 'Call 911', backToAsk: 'Back to asking', offtopic: 'Didn’t answer my question', fbPhOff: 'What were you looking for? (one sentence, no personal details)', offline: 'You are offline. Asking needs an internet connection — the Life Guide works offline.', earlier: 'Earlier answers',
    examples: ['Ask in any language — e.g. How do I get a SIN?', 'Ask in any language — e.g. Where can I get free legal advice?', 'Ask in any language — e.g. My landlord won’t return my deposit. What can I do?'],
  },
  fr: {
    intro: 'Les réponses, rédigées par l’IA, s’appuient sur le contenu vérifié du Guide de vie à Kamloops et peuvent contenir des erreurs. Vérifiez les informations importantes auprès de la source officielle. Outil indépendant — ce n’est pas un service de Kamloops Immigrant Services ni du gouvernement.',
    privacy: 'N’entrez pas votre nom, vos numéros de pièce d’identité, des détails de santé ni d’autres renseignements personnels. Votre question est envoyée à un service d’IA pour rédiger la réponse.', qLabel: 'Question', placeholder: 'Posez votre question dans n’importe quelle langue — p. ex. Comment obtenir un NAS ?', ask: 'Demander',
    quickLabel: 'Questions fréquentes', quick1t: 'Première semaine', quick2t: 'Inscription scolaire', quick3t: 'Médecin de famille', quick4t: 'Banque alimentaire',
    quick1: 'Que doit faire un nouvel arrivant pendant sa première semaine à Kamloops ?', quick2: 'Comment inscrire à l’école un enfant qui vient d’arriver à Kamloops ?', quick3: 'Comment trouver un médecin de famille ?', quick4: 'Où se trouve la banque alimentaire et comment fonctionne-t-elle ?',
    privacyLink: 'Confidentialité', guideLink: 'Guide de vie à Kamloops',
    loading: 'Recherche dans le guide…', announce: 'Nouvelle réponse prête',
    sources: 'Sources', checked: 'vérifié', official: 'Page officielle', inGuide: 'Ouvrir dans le guide', notChecked: 'sans date de vérification',
    tierOfficial: 'officiel', tierOwn: 'vérifié par l’auteur', tierPlaces: 'fiche d’un tiers',
    footer: 'Rédigé par l’IA à partir du guide. Les sources officielles font foi.',
    stale: 'Une partie de ces informations n’a pas été vérifiée depuis plus de 6 mois — confirmez auprès de l’organisme.',
    referral: 'Qui peut vous aider :', copy: 'Copier', copied: 'Copié',
    client: 'Version dans la langue du client', clientPick: 'Choisir une langue…', clientNote: 'Traduction par IA, à titre indicatif ; l’information officielle du lien fait foi.', translating: 'Traduction…',
    trFail: 'La traduction n’a pas passé la vérification (un numéro de téléphone ou une adresse web a changé). Utilisez l’original.',
    fbQ: 'Cette réponse :', useful: 'Utile', wrong: 'Erronée', fbPh: 'Qu’est-ce qui est faux (une phrase, sans renseignements personnels)', fbSend: 'Envoyer', fbThanks: 'Merci, c’est noté.',
    notFound: 'Le guide n’a pas d’information vérifiée à ce sujet', outScope: 'Cela dépend de votre situation',
    tryThese: 'Vous pouvez essayer :', relatedCards: 'Fiches pratiques du guide sur ce sujet :',
    crisisTitle: 'Aide urgente', crisisLead: 'Cette question peut concerner la sécurité ou une crise. L’assistant n’y répond pas avec l’IA — utilisez les lignes ci-dessous. Si une vie est en danger, appelez le 911 maintenant.',
    crisisLocal: 'Lignes locales', sms: 'texto',
    errTitle: 'Impossible de répondre pour le moment', errLead: 'Réessayez plus tard, ou consultez directement le guide.', retry: 'Réessayer',
    reasons: { too_fast: 'Trop de questions en peu de temps. Attendez une minute.', visitor_limit: 'Ceci est une version d’essai. Pour respecter le budget, chaque personne peut poser jusqu’à 10 questions par jour, et vous avez atteint la limite d’aujourd’hui. Réessayez demain — pour de l’aide dès maintenant, appelez le 2-1-1 ou consultez le guide.', daily_limit: 'Ceci est une version d’essai. Pour respecter le budget, le nombre de questions pour tout le site est limité chaque jour, et celles d’aujourd’hui sont épuisées. Réessayez demain — pour de l’aide dès maintenant, appelez le 2-1-1 ou consultez le guide.', ai_not_configured: 'Le service d’IA n’est pas encore configuré.', ai_key: 'La clé du service d’IA est invalide ou sans crédit.', rate_limited: 'Le service d’IA est occupé.', too_long: 'La question est trop longue (1 000 caractères au plus).', empty: 'Tapez une question.', forbidden: 'Accès refusé — reconnectez-vous.' },
    loading2: 'Rédaction de la réponse…', loading3: 'Presque terminé — une réponse prend en général 5 à 15 secondes.', quotaLeft: 'Version d’essai : il vous reste {n} questions sur {m} aujourd’hui.', limitTitle: 'Les questions d’aujourd’hui sont épuisées', youAsked: 'Votre question :', piiTitle: 'Ceci ressemble à des renseignements personnels', piiLead: 'Votre question semble contenir un numéro de téléphone, une adresse courriel ou un numéro de pièce d’identité. Ce n’est pas nécessaire pour obtenir une réponse, et la question est envoyée à un service d’IA — retirez-le.', piiEdit: 'Modifier ma question', piiSend: 'Envoyer quand même', share: 'Partager', mapLink: 'Voir sur la carte du guide', askAnother: 'Poser une autre question', call911: 'Appeler le 911', backToAsk: 'Revenir aux questions', offtopic: 'Ne répond pas à ma question', fbPhOff: 'Que cherchiez-vous ? (une phrase, sans renseignements personnels)', offline: 'Vous êtes hors ligne. Poser une question demande une connexion internet — le guide fonctionne hors ligne.', earlier: 'Réponses précédentes',
    examples: ['Posez votre question dans n’importe quelle langue — p. ex. Comment obtenir un NAS ?', 'Posez votre question dans n’importe quelle langue — p. ex. Où trouver des conseils juridiques gratuits ?', 'Posez votre question dans n’importe quelle langue — p. ex. Mon propriétaire ne rend pas mon dépôt. Que faire ?'],
  },
  es: {
    intro: 'Las respuestas, redactadas por IA, se basan en el contenido verificado de la Guía de vida en Kamloops y pueden contener errores. Confirme la información importante con la fuente oficial. Es una herramienta independiente, no un servicio de Kamloops Immigrant Services ni del gobierno.',
    privacy: 'No escriba su nombre, números de identificación, datos de salud ni otros datos personales. Su pregunta se envía a un servicio de IA para redactar la respuesta.', qLabel: 'Pregunta', placeholder: 'Pregunte en cualquier idioma; p. ej.: ¿Cómo obtengo el número de seguro social (SIN)?', ask: 'Preguntar',
    quickLabel: 'Preguntas frecuentes', quick1t: 'Primera semana', quick2t: 'Inscripción escolar', quick3t: 'Médico de familia', quick4t: 'Banco de alimentos',
    quick1: '¿Qué debe hacer una persona recién llegada en su primera semana en Kamloops?', quick2: '¿Cómo inscribo en la escuela a un niño que acaba de llegar a Kamloops?', quick3: '¿Cómo encuentro un médico de familia?', quick4: '¿Dónde está el banco de alimentos y cómo funciona?',
    privacyLink: 'Privacidad', guideLink: 'Guía de vida en Kamloops',
    loading: 'Buscando en la guía…', announce: 'Nueva respuesta lista',
    sources: 'Fuentes', checked: 'verificado', official: 'Página oficial', inGuide: 'Abrir en la guía', notChecked: 'sin fecha de verificación',
    tierOfficial: 'oficial', tierOwn: 'verificado por el autor', tierPlaces: 'ficha de terceros',
    footer: 'Redactado por IA a partir de la guía. Prevalecen las fuentes oficiales.',
    stale: 'Parte de esta información no se ha verificado en más de 6 meses — confírmela con la organización.',
    referral: 'Quién puede ayudarle:', copy: 'Copiar', copied: 'Copiado',
    client: 'Versión en el idioma del cliente', clientPick: 'Elija un idioma…', clientNote: 'Traducción por IA, solo de referencia; prevalece la información oficial del enlace.', translating: 'Traduciendo…',
    trFail: 'La traducción no pasó la verificación (cambió un teléfono o una dirección web). Use el original.',
    fbQ: 'Esta respuesta:', useful: 'Útil', wrong: 'Incorrecta', fbPh: 'Qué está mal (una frase, sin datos personales)', fbSend: 'Enviar', fbThanks: 'Gracias, queda anotado.',
    notFound: 'La guía no tiene información verificada sobre esto', outScope: 'Depende de su situación',
    tryThese: 'Puede intentar:', relatedCards: 'Fichas prácticas de la guía sobre este tema:',
    crisisTitle: 'Ayuda urgente', crisisLead: 'Esta pregunta puede tener que ver con la seguridad o una crisis. El asistente no la responde con IA; use las líneas de abajo. Si hay una vida en peligro, llame al 911 ahora.',
    crisisLocal: 'Líneas locales', sms: 'texto',
    errTitle: 'No se puede responder en este momento', errLead: 'Inténtelo más tarde o consulte directamente la guía.', retry: 'Reintentar',
    reasons: { too_fast: 'Demasiadas preguntas en poco tiempo. Espere un minuto.', visitor_limit: 'Esta es una versión de prueba. Para no salirnos del presupuesto, cada persona puede hacer hasta 10 preguntas al día, y usted ya alcanzó el límite de hoy. Inténtelo mañana; si necesita ayuda ahora, llame al 2-1-1 o consulte la guía.', daily_limit: 'Esta es una versión de prueba. Para no salirnos del presupuesto, el número de preguntas de todo el sitio es limitado cada día y las de hoy ya se agotaron. Inténtelo mañana; si necesita ayuda ahora, llame al 2-1-1 o consulte la guía.', ai_not_configured: 'El servicio de IA aún no está configurado.', ai_key: 'La clave del servicio de IA no es válida o no tiene saldo.', rate_limited: 'El servicio de IA está ocupado.', too_long: 'La pregunta es demasiado larga (máximo 1000 caracteres).', empty: 'Escriba una pregunta.', forbidden: 'Sin acceso; vuelva a iniciar sesión.' },
    loading2: 'Redactando la respuesta…', loading3: 'Casi listo: las respuestas suelen tardar de 5 a 15 segundos.', quotaLeft: 'Versión de prueba: le quedan {n} de {m} preguntas hoy.', limitTitle: 'Se agotaron las preguntas de hoy', youAsked: 'Su pregunta:', piiTitle: 'Esto parece información personal', piiLead: 'Su pregunta parece incluir un número de teléfono, un correo electrónico o un número de identificación. No hace falta para obtener una respuesta y la pregunta se envía a un servicio de IA; por favor, quítelo.', piiEdit: 'Editar mi pregunta', piiSend: 'Enviar de todos modos', share: 'Compartir', mapLink: 'Ver en el mapa de la guía', askAnother: 'Hacer otra pregunta', call911: 'Llamar al 911', backToAsk: 'Volver a preguntar', offtopic: 'No respondió mi pregunta', fbPhOff: '¿Qué buscaba? (una frase, sin datos personales)', offline: 'No tiene conexión. Para preguntar se necesita internet; la guía funciona sin conexión.', earlier: 'Respuestas anteriores',
    examples: ['Pregunte en cualquier idioma; p. ej.: ¿Cómo obtengo el número de seguro social (SIN)?', 'Pregunte en cualquier idioma; p. ej.: ¿Dónde consigo asesoría legal gratuita?', 'Pregunte en cualquier idioma; p. ej.: Mi arrendador no me devuelve el depósito. ¿Qué hago?'],
  },
  ko: {
    intro: 'Kamloops 생활 가이드에서 확인된 내용을 바탕으로 AI가 답하며, 틀릴 수 있습니다. 중요한 정보는 공식 출처에서 확인하세요. 이 도구는 독립적으로 만든 것으로, Kamloops Immigrant Services나 정부의 서비스가 아닙니다.',
    privacy: '이름, 신분증 번호, 건강 정보 등 개인정보를 입력하지 마세요. 질문은 답변 작성을 위해 AI 서비스로 전송됩니다.', qLabel: '질문', placeholder: '어떤 언어로든 질문하세요 — 예: SIN은 어떻게 받나요?', ask: '질문하기',
    quickLabel: '자주 묻는 질문', quick1t: '도착 첫 주', quick2t: '자녀 입학', quick3t: '가정의 찾기', quick4t: '푸드뱅크',
    quick1: 'Kamloops에 도착한 첫 주에 무엇을 해야 하나요?', quick2: 'Kamloops에 막 도착한 아이를 학교에 어떻게 등록하나요?', quick3: '가정의는 어떻게 찾나요?', quick4: '푸드뱅크는 어디에 있고 어떻게 이용하나요?',
    privacyLink: '개인정보 안내', guideLink: 'Kamloops 생활 가이드',
    loading: '가이드에서 관련 내용을 찾는 중…', announce: '새 답변이 준비되었습니다',
    sources: '출처', checked: '확인', official: '공식 페이지', inGuide: '가이드에서 열기', notChecked: '확인 날짜 없음',
    tierOfficial: '공식', tierOwn: '작성자 확인', tierPlaces: '제3자 정보',
    footer: 'AI가 가이드를 바탕으로 정리했습니다. 공식 정보가 우선입니다.',
    stale: '일부 내용은 6개월 넘게 확인되지 않았습니다 — 해당 기관에 다시 확인하세요.',
    referral: '도움을 받을 수 있는 곳:', copy: '복사', copied: '복사됨',
    client: '고객 언어 버전 만들기', clientPick: '언어 선택…', clientNote: 'AI 번역이며 참고용입니다. 링크의 공식 정보가 우선입니다.', translating: '번역 중…',
    trFail: '번역이 확인을 통과하지 못했습니다(전화번호나 웹 주소가 바뀜). 원문을 사용하세요.',
    fbQ: '이 답변:', useful: '도움 됨', wrong: '틀림', fbPh: '무엇이 틀렸나요(한 문장, 개인정보 제외)', fbSend: '보내기', fbThanks: '감사합니다. 기록했습니다.',
    notFound: '가이드에 이에 관한 확인된 정보가 없습니다', outScope: '개인 상황에 따라 달라집니다',
    tryThese: '이렇게 해 보세요:', relatedCards: '가이드의 관련 안내 카드:',
    crisisTitle: '긴급 도움', crisisLead: '안전이나 위기와 관련된 질문일 수 있습니다. 도우미는 AI로 답하지 않습니다 — 아래 전화번호를 바로 이용하세요. 생명이 위험하면 지금 911에 전화하세요.',
    crisisLocal: '지역 전화', sms: '문자',
    errTitle: '지금은 답할 수 없습니다', errLead: '잠시 후 다시 시도하거나 생활 가이드를 직접 보세요.', retry: '다시 시도',
    reasons: { too_fast: '짧은 시간에 질문이 너무 많습니다. 1분 후에 다시 시도하세요.', visitor_limit: '시험 버전이라 예산 관리를 위해 한 사람당 하루 최대 10개까지 질문할 수 있으며, 오늘 횟수를 모두 사용했습니다. 내일 다시 시도해 주세요. 지금 도움이 필요하면 2-1-1에 전화하거나 생활 가이드를 보세요.', daily_limit: '시험 버전이라 예산 관리를 위해 사이트 전체의 하루 질문 수가 정해져 있으며, 오늘 분량을 모두 사용했습니다. 내일 다시 시도해 주세요. 지금 도움이 필요하면 2-1-1에 전화하거나 생활 가이드를 보세요.', ai_not_configured: 'AI 서비스가 아직 설정되지 않았습니다.', ai_key: 'AI 서비스 키가 잘못되었거나 잔액이 없습니다.', rate_limited: 'AI 서비스가 바쁩니다.', too_long: '질문이 너무 깁니다(최대 1,000자).', empty: '질문을 입력하세요.', forbidden: '접근 권한이 없습니다. 다시 로그인하세요.' },
    loading2: '답변을 작성하는 중…', loading3: '거의 다 됐습니다 — 답변에는 보통 5~15초가 걸립니다.', quotaLeft: '시험 버전: 오늘 {m}개 중 {n}개 질문이 남았습니다.', limitTitle: '오늘 질문 횟수를 모두 사용했습니다', youAsked: '질문:', piiTitle: '개인정보로 보이는 내용이 있습니다', piiLead: '질문에 전화번호, 이메일 주소 또는 신분증 번호로 보이는 내용이 있습니다. 답변을 받는 데 필요하지 않고 질문은 AI 서비스로 전송되니 지워 주세요.', piiEdit: '질문 고치기', piiSend: '그대로 보내기', share: '공유', mapLink: '가이드 지도에서 보기', askAnother: '다른 질문하기', call911: '911에 전화하기', backToAsk: '질문으로 돌아가기', offtopic: '질문에 대한 답이 아님', fbPhOff: '무엇을 찾고 있었나요? (한 문장, 개인정보 제외)', offline: '오프라인 상태입니다. 질문하려면 인터넷이 필요합니다 — 생활 가이드는 오프라인에서도 쓸 수 있습니다.', earlier: '이전 답변',
    examples: ['어떤 언어로든 질문하세요 — 예: SIN은 어떻게 받나요?', '어떤 언어로든 질문하세요 — 예: 무료 법률 상담은 어디서 받나요?', '어떤 언어로든 질문하세요 — 예: 집주인이 보증금을 돌려주지 않아요. 어떻게 하나요?'],
  },
  ja: {
    intro: 'Kamloops 生活ガイドの確認済みの内容をもとに AI が回答します。誤りがある場合があるので、重要な情報は公式の情報源で確認してください。これは独立したツールで、Kamloops Immigrant Services や政府のサービスではありません。',
    privacy: '氏名、身分証の番号、健康状態などの個人情報は入力しないでください。質問は回答を作るために AI サービスに送られます。', qLabel: '質問', placeholder: 'どの言語でも質問できます — 例：SIN はどう取得しますか？', ask: '質問する',
    quickLabel: 'よくある質問', quick1t: '到着後1週間', quick2t: '子どもの入学', quick3t: 'かかりつけ医', quick4t: 'フードバンク',
    quick1: 'Kamloops に着いて最初の1週間に何をすればいいですか？', quick2: 'Kamloops に来たばかりの子どもを学校に登録するには？', quick3: 'かかりつけ医（ファミリードクター）はどう探せばいいですか？', quick4: 'フードバンクはどこにあり、どう利用しますか？',
    privacyLink: 'プライバシー', guideLink: 'Kamloops 生活ガイド',
    loading: 'ガイドから関連する内容を探しています…', announce: '新しい回答ができました',
    sources: '出典', checked: '確認', official: '公式ページ', inGuide: 'ガイドで開く', notChecked: '確認日なし',
    tierOfficial: '公式', tierOwn: '作成者が確認', tierPlaces: '第三者の情報',
    footer: 'AI がガイドをもとにまとめました。公式の情報が優先です。',
    stale: '一部の情報は6か月以上確認されていません — 機関に改めて確認してください。',
    referral: '相談できる窓口：', copy: 'コピー', copied: 'コピーしました',
    client: 'お客様の言語版を作る', clientPick: '言語を選ぶ…', clientNote: 'AI による翻訳で参考用です。リンク先の公式情報が優先です。', translating: '翻訳しています…',
    trFail: '翻訳が確認を通りませんでした（電話番号またはウェブアドレスが変わっています）。原文を使ってください。',
    fbQ: 'この回答：', useful: '役に立った', wrong: '誤りがある', fbPh: 'どこが誤りか（一文で、個人情報は含めずに）', fbSend: '送信', fbThanks: 'ありがとうございます。記録しました。',
    notFound: 'ガイドにはこの件の確認済みの情報がありません', outScope: 'あなたの状況によって異なります',
    tryThese: '次を試してください：', relatedCards: 'ガイドの関連する手続きカード：',
    crisisTitle: '緊急の支援', crisisLead: '安全や危機に関わる質問の可能性があります。このアシスタントは AI では回答しません — 下の電話番号を直接使ってください。命に危険がある場合は、今すぐ 911 に電話してください。',
    crisisLocal: '地域の窓口', sms: 'SMS',
    errTitle: '今は回答できません', errLead: 'しばらくしてからもう一度試すか、生活ガイドを直接ご覧ください。', retry: 'もう一度試す',
    reasons: { too_fast: '短時間に質問が多すぎます。1分ほど待ってください。', visitor_limit: 'これはテスト版のため、予算を抑えるために1人1日10問までとしています。今日の上限に達しました。明日もう一度お試しください。今すぐ助けが必要なときは 2-1-1 に電話するか、生活ガイドをご覧ください。', daily_limit: 'これはテスト版のため、予算を抑えるためにサイト全体の1日の質問数を限っており、今日の分は終わりました。明日もう一度お試しください。今すぐ助けが必要なときは 2-1-1 に電話するか、生活ガイドをご覧ください。', ai_not_configured: 'AI サービスがまだ設定されていません。', ai_key: 'AI サービスのキーが無効か、残高がありません。', rate_limited: 'AI サービスが混み合っています。', too_long: '質問が長すぎます（1,000文字まで）。', empty: '質問を入力してください。', forbidden: 'アクセス権がありません。もう一度ログインしてください。' },
    loading2: '回答をまとめています…', loading3: 'もうすぐです — 回答には通常 5〜15 秒かかります。', quotaLeft: 'テスト版：今日はあと {n} 問質問できます（1日 {m} 問まで）。', limitTitle: '今日の質問回数を使い切りました', youAsked: 'あなたの質問：', piiTitle: '個人情報のようなものが含まれています', piiLead: '質問に電話番号、メールアドレス、または身分証などの番号らしきものが含まれています。回答には必要なく、質問は AI サービスに送られるので、削除してください。', piiEdit: '質問を直す', piiSend: 'このまま送る', share: '共有', mapLink: 'ガイドの地図で見る', askAnother: '別の質問をする', call911: '911 に電話する', backToAsk: '質問に戻る', offtopic: '質問の答えになっていない', fbPhOff: '何を知りたかったですか？（一文で、個人情報は含めずに）', offline: 'オフラインです。質問にはインターネット接続が必要です（生活ガイドはオフラインでも使えます）。', earlier: 'これまでの回答',
    examples: ['どの言語でも質問できます — 例：SIN はどう取得しますか？', 'どの言語でも質問できます — 例：無料の法律相談はどこで受けられますか？', 'どの言語でも質問できます — 例：大家が敷金を返してくれません。どうすれば？'],
  },
};

// 客户语言版本的常用语言（KIS 提供客户语言清单后再调整，说明 §15 第 2 条）
const CLIENT_LANGS = [['English', 'English'], ['简体中文', 'Simplified Chinese'], ['繁體中文', 'Traditional Chinese'], ['Français', 'French'], ['Español', 'Spanish'],
  ['한국어', 'Korean'], ['日本語', 'Japanese'], ['العربية', 'Arabic'], ['فارسی', 'Persian (Farsi)'], ['دری', 'Dari'], ['Українська', 'Ukrainian'],
  ['Русский', 'Russian'], ['ਪੰਜਾਬੀ', 'Punjabi'], ['हिन्दी', 'Hindi'], ['Tagalog', 'Tagalog'], ['Tiếng Việt', 'Vietnamese'], ['ትግርኛ', 'Tigrinya'],
  ['Soomaali', 'Somali'], ['Kiswahili', 'Swahili'], ['Português', 'Portuguese'], ['Türkçe', 'Turkish']];
const CLIENT_BCP = { 'Simplified Chinese': 'zh-Hans', 'Traditional Chinese': 'zh-Hant', French: 'fr', Spanish: 'es', Korean: 'ko', Japanese: 'ja', Arabic: 'ar',
  'Persian (Farsi)': 'fa', Dari: 'prs', Ukrainian: 'uk', Russian: 'ru', Punjabi: 'pa', Hindi: 'hi', Tagalog: 'tl', Vietnamese: 'vi', Tigrinya: 'ti',
  Somali: 'so', Swahili: 'sw', Portuguese: 'pt', Turkish: 'tr', English: 'en' };
const RTL = new Set(['ar', 'fa', 'prs']);


let L = 'en';   // 默认英文（Neil 2026-10-24）；选过的语言记在本机，下次沿用
try { const s = localStorage.getItem('kia-lang'); if (T[s]) L = s; } catch {}
const t = k => T[L][k];
const fill = (s, o) => String(s).replace(/\{(\w+)\}/g, (_, k) => (o[k] != null ? o[k] : ''));

const $ = s => document.querySelector(s);
const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat(Infinity)) if (c != null && c !== false) e.append(c.nodeType ? c : document.createTextNode(String(c)));
  return e;
};
const telHref = p => 'tel:' + String(p).replace(/[^\d+]/g, '');
// 回答文字里的电话：可点击拨号，且不在中间折行（这些号码已由服务器核对过出自指南）
const PHONE_RE = /((?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}|\b\d-\d-\d\b|\b(?:911|811|211)\b)/g;
const rich = text => String(text).split(PHONE_RE).map((part, i) => i % 2 ? el('a', { class: 'tel-inline', href: telHref(part) }, part) : part);

// 发送前的个人信息检查（只在浏览器里，不发出去）：电话、邮箱、9 位号码（SIN 等）、证件号、7 位以上的长数字
const PII_RE = [
  /[^\s@]+@[^\s@]+\.[a-z]{2,}/i,
  /(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b/,
  /\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b/,
  /\b[A-Z]{1,2}\d{6,9}\b/,
  /\d{7,}/,
];
export const looksPersonal = q => PII_RE.some(re => re.test(q));

const out = $('#out'), form = $('#ask'), qBox = $('#q'), go = $('#go');
let current = null;            // { q, res }：当前显示的回答
const earlier = [];            // 这次打开页面期间之前的回答（只在本页，关掉就没了，不保存）
let exampleIdx = 0;
let busy = false;

// 公开版没有"客户语言版本"（读者本人就用自己的语言提问）；只在工作人员版（Access 登录）显示。
// 取不到设置时按公开版处理（少一个按钮，不会多一个能被滥用的接口）。
let STAFF = false;
fetch('/api/health').then(r => r.json()).then(j => {
  STAFF = j.audience === 'staff';
  if (j.guide) { GUIDE = j.guide; applyGuideLinks(); }
}).catch(() => {});
let GUIDE = document.querySelector('.guide-href') ? document.querySelector('.guide-href').getAttribute('href') : '';
function applyGuideLinks() {
  if (!GUIDE) return;
  const u = GUIDE + (L === 'en' ? '' : (GUIDE.includes('?') ? '&' : '?') + 'lang=' + L);
  document.querySelectorAll('.guide-href').forEach(a => a.setAttribute('href', u));
}

// 今天还剩几题（测试版每人每天的上限）
let quota = null;
function showQuota(q) {
  if (q && q.left != null) quota = q;
  const p = $('#quota');
  if (!quota) { p.hidden = true; return; }
  p.hidden = false;
  p.textContent = fill(t('quotaLeft'), { n: quota.left, m: quota.limit });
  p.classList.toggle('low', quota.left <= 2);
}
fetch('/api/quota').then(r => r.json()).then(showQuota).catch(() => {});

function applyLang() {
  document.documentElement.lang = L === 'zh' ? 'zh-Hans' : L;
  document.querySelectorAll('[data-t]').forEach(n => { n.textContent = t(n.dataset.t); });
  document.querySelectorAll('[data-al]').forEach(n => { n.setAttribute('aria-label', t(n.dataset.al)); });
  document.querySelectorAll('.langs button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lang === L)));
  const pl = document.querySelector('a[href^="privacy.html"]');
  if (pl) pl.setAttribute('href', 'privacy.html#' + L);
  qBox.placeholder = t('examples')[exampleIdx % t('examples').length];
  applyGuideLinks();
  showQuota();
}

async function post(path, payload) {
  try {
    const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (r.status === 403) return { status: 'error', reason: 'forbidden' };
    return await r.json();
  } catch {
    return { status: 'error', reason: navigator.onLine === false ? 'offline' : 'ai_unavailable' };
  }
}

function announce(msg) { const a = $('#announce'); a.textContent = ''; setTimeout(() => { a.textContent = msg || t('announce'); }, 50); }

// ---------- 发送 ----------

function hidePii() { const b = $('#pii'); b.hidden = true; b.replaceChildren(); }

function showPii(q) {
  const b = $('#pii');
  b.replaceChildren(
    el('p', {}, el('strong', {}, t('piiTitle'))),
    el('p', {}, t('piiLead')),
    el('div', { class: 'pii-actions' },
      el('button', { type: 'button', class: 'primary', onclick: () => { hidePii(); qBox.focus(); } }, t('piiEdit')),
      el('button', { type: 'button', onclick: () => { hidePii(); ask(q, { force: true }); } }, t('piiSend'))));
  b.hidden = false;
}

function setBusy(on) {
  busy = on;
  go.disabled = on;
  qBox.readOnly = on;
  form.setAttribute('aria-busy', String(on));
  document.querySelectorAll('.chip').forEach(c => { c.disabled = on; });
}

function loadingCard() {
  const msg = el('span', {}, t('loading'));
  const card = el('div', { class: 'card loading', role: 'status' }, el('span', { class: 'spinner', 'aria-hidden': 'true' }), msg);
  // 分阶段的进度文字：用户知道还在处理，不会以为卡住而反复点（每点一次都会用掉一次额度）
  const timers = [setTimeout(() => { msg.textContent = t('loading2'); }, 3000), setTimeout(() => { msg.textContent = t('loading3'); }, 9000)];
  card.stop = () => timers.forEach(clearTimeout);
  return card;
}

async function ask(q, { force = false } = {}) {
  q = String(q || '').trim();
  if (!q || busy) return;
  hidePii();
  if (navigator.onLine === false) { $('#offline').hidden = false; return; }
  if (!force && looksPersonal(q)) { showPii(q); return; }
  setBusy(true);
  const loading = loadingCard();
  out.replaceChildren(loading);
  const res = await post('/api/ask', { q, uiLang: L });
  loading.stop();
  setBusy(false);
  if (res.quota) showQuota(res.quota);
  // 上一个回答（不是出错提示的）移到"之前的回答"，不会因为这次出错而丢掉
  if (current && current.res.status !== 'error') earlier.unshift(current);
  current = { q, res };
  // 有回答（含危机卡片）时：清空输入框，换一个示例，收起常见问题；出错时保留输入，方便重试
  if (res.status !== 'error') {
    qBox.value = '';
    updateCount();
    exampleIdx++;
    qBox.placeholder = t('examples')[exampleIdx % t('examples').length];
    $('#quick').open = false;
  }
  renderAll();
  focusNew();
}

// ---------- 显示 ----------

function renderAll() {
  out.replaceChildren(current ? card(current, true) : '');
  const box = $('#earlier');
  box.hidden = !earlier.length;
  $('#earlierList').replaceChildren(...earlier.map(e => el('details', { class: 'past' },
    el('summary', {}, e.q), card(e, false))));
}

function focusNew() {
  const h = out.querySelector('h2');
  if (h) {
    h.setAttribute('tabindex', '-1');
    h.focus({ preventScroll: true });
    // 新回答滚到屏幕顶部（手机上回答在提问框下面，否则只露出一半）
    const reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    out.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  }
  announce();
}

function card(entry, isCurrent) {
  const { q, res } = entry;
  if (res.status === 'crisis') return crisisCard(res, isCurrent);
  if (res.status === 'error') return errorCard(res, q);
  return answerCard(res, q, isCurrent);
}

function askedLine(q) {
  return el('h2', { class: 'asked' }, el('span', { class: 'asked-label' }, t('youAsked') + ' '), q);
}

function backButton(label) {
  return el('button', { type: 'button', class: 'secondary', onclick: () => { window.scrollTo({ top: 0, behavior: 'smooth' }); qBox.focus(); } }, label);
}

function crisisCard(res, isCurrent) {
  const nine = (res.lines || []).find(l => l.phone === '911');
  const others = (res.lines || []).filter(l => l !== nine);
  const line = l => el('li', {}, el('a', { class: 'tel', href: telHref(l.phone) }, l.phone), ' ', l.title);
  // 本地专线的说明来自指南，写法是"……或打电话："，号码接在说明后面
  const local = l => el('li', {}, l.title, ' ', el('a', { class: 'tel', href: telHref(l.phone) }, l.phone),
    l.sms ? el('span', {}, ' · ', t('sms'), ' ', el('a', { href: 'sms:' + l.sms.replace(/[^\d+]/g, '') }, l.sms)) : null);
  return el('div', { class: 'card crisis', role: isCurrent ? 'alert' : null },
    el('h2', {}, '⚠ ', t('crisisTitle')), el('p', {}, t('crisisLead')),
    nine ? el('a', { class: 'call911', href: telHref('911') }, t('call911')) : null,
    el('ul', {}, others.map(line)),
    res.local && res.local.length ? [el('h3', {}, t('crisisLocal')), el('ul', {}, res.local.map(local))] : null,
    isCurrent ? el('div', { class: 'actions' }, backButton(t('backToAsk'))) : null);
}

function fallbackBlock(fb) {
  if (!fb) return null;
  return el('div', { class: 'fallback' },
    fb.tasks && fb.tasks.length ? [el('p', {}, t('relatedCards')), el('ul', {}, fb.tasks.map(c => el('li', {}, el('a', { href: c.guide, target: '_blank', rel: 'noopener' }, c.title))))] : null,
    el('p', {}, t('tryThese')),
    el('ul', {}, (fb.lines || []).map(l => el('li', {}, l.title, ' ', el('a', { class: 'tel', href: telHref(l.phone) }, l.phone))),
      el('li', {}, el('a', { href: fb.guide, target: '_blank', rel: 'noopener' }, t('guideLink')))));
}

const LIMIT_REASONS = ['visitor_limit', 'daily_limit'];

function errorCard(res, q) {
  const limit = LIMIT_REASONS.includes(res.reason);
  const why = res.reason === 'offline' ? t('offline') : (t('reasons')[res.reason] || '');
  return el('div', { class: 'card error', role: 'alert' },
    // 次数用完不是故障：标题直接说"今天的提问次数已用完"
    el('h2', {}, limit ? t('limitTitle') : t('errTitle')),
    // 超过次数：说明本身已写明原因和"明天再试"，不再接通用的"请稍后再试"
    el('p', {}, limit ? why : [why, t('errLead')].filter(Boolean).join(' ')),
    q && !limit && res.reason !== 'too_long' ? el('button', { type: 'button', class: 'primary', onclick: () => ask(q, { force: true }) }, t('retry')) : null,
    fallbackBlock(res.fallback));
}

function answerText(res, q) {
  const num = new Map(res.sources.map((s, i) => [s.source_id, i + 1]));
  const lines = [t('youAsked') + ' ' + q, ''];
  if (res.summary) lines.push(res.summary);
  res.steps.forEach((s, i) => lines.push(`${i + 1}. ${s.text} [${s.source_ids.map(id => num.get(id)).join(',')}]`));
  if (res.referral) lines.push(t('referral') + ' ' + res.referral.text);
  lines.push('', t('sources') + ':');
  res.sources.forEach((s, i) => lines.push(`[${i + 1}] ${s.title}${s.phone ? ' ' + s.phone : ''}${s.url ? ' ' + s.url : (s.guide ? ' ' + s.guide : '')}${s.checked ? ' (' + t('checked') + ' ' + s.checked + ')' : ''}`));
  lines.push('', t('footer'), location.origin + '/');
  return lines.join('\n');
}

function answerCard(res, q, isCurrent) {
  const num = new Map(res.sources.map((s, i) => [s.source_id, i + 1]));
  const uid = Math.random().toString(36).slice(2, 8);
  const srcId = n => `src-${uid}-${n}`;
  // 点引用号：就地显示来源（不跳到页面底部），同时高亮下面对应的来源
  const cites = ids => ids.flatMap(id => {
    const n = num.get(id), s = res.sources[n - 1];
    const pop = el('span', { class: 'cite-pop', hidden: true },
      el('strong', {}, s.title), s.checked ? ' · ' + t('checked') + ' ' + s.checked : '',
      s.url ? [' · ', el('a', { href: s.url, target: '_blank', rel: 'noopener' }, (s.type === 'task' ? t('official') : t('sources')) + ' ↗')] : '',
      s.guide ? [' · ', el('a', { href: s.guide, target: '_blank', rel: 'noopener' }, t('inGuide') + ' ↗')] : '');
    const btn = el('button', { type: 'button', class: 'cite', 'aria-expanded': 'false', 'aria-label': t('sources') + ' ' + n, onclick: () => {
      const open = pop.hidden;
      pop.hidden = !open;
      btn.setAttribute('aria-expanded', String(open));
      const li = document.getElementById(srcId(n));
      if (li) { li.classList.remove('flash'); void li.offsetWidth; li.classList.add('flash'); }
    } }, '[' + n + ']');
    return [btn, pop];
  });
  const heading = res.status === 'not_found' ? t('notFound') : res.status === 'out_of_scope' ? t('outScope') : null;
  const lang = res.language && /^[a-z]{2}$/.test(res.language) ? res.language : null;

  return el('article', { class: 'card answer' },
    askedLine(q),
    heading ? el('p', { class: 'status-head' }, heading) : null,
    el('div', { lang },
      res.summary ? el('p', { class: 'summary' }, rich(res.summary)) : null,
      res.steps.length ? el('ol', {}, res.steps.map(s => el('li', {}, rich(s.text), cites(s.source_ids)))) : null,
      res.referral ? el('p', { class: 'referral' }, el('strong', {}, t('referral') + ' '), rich(res.referral.text), cites(res.referral.source_ids)) : null),
    res.stale ? el('p', { class: 'stale' }, t('stale')) : null,
    res.status === 'not_found' ? fallbackBlock(res.fallback) : null,
    res.sources.length ? el('div', { class: 'sources' }, el('h3', {}, t('sources')), el('ol', {}, res.sources.map((s, i) => sourceItem(s, i + 1, srcId(i + 1))))) : null,
    el('p', { class: 'note' }, t('footer')),
    actions(res, q, isCurrent));
}

function sourceItem(s, n, id) {
  const tier = s.type === 'place' && s.tier ? (s.official ? t('tierOfficial') : s.tier === 'own' ? t('tierOwn') : s.tier === 'places' ? t('tierPlaces') : null) : null;
  const links = [
    s.url ? el('a', { href: s.url, target: '_blank', rel: 'noopener' }, (s.type === 'task' ? t('official') : s.url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')) + ' ↗') : null,
    s.guide ? el('a', { href: s.guide, target: '_blank', rel: 'noopener' }, t('inGuide') + ' ↗') : null,
    s.map ? el('a', { href: s.map, target: '_blank', rel: 'noopener' }, t('mapLink') + ' ↗') : null,
  ].filter(Boolean);
  return el('li', { id },
    el('strong', {}, s.title), tier ? el('span', { class: 'tier' }, tier) : null,
    s.category ? el('span', { class: 'meta' }, ' · ' + s.category) : null,
    s.address ? el('span', { class: 'meta' }, ' · ' + s.address) : null,
    s.phone ? el('span', {}, ' · ', el('a', { class: 'tel-inline', href: telHref(s.phone) }, s.phone)) : null,
    // 热线不是办事卡或地点，没有核实月份这一项，不显示
    s.type === 'line' ? null : el('span', { class: 'meta' }, ' · ' + (s.checked ? t('checked') + ' ' + s.checked : t('notChecked'))),
    links.length ? el('span', { class: 'links' }, links.flatMap((a, i) => (i ? [' · ', a] : [a]))) : null);
}

function actions(res, q, isCurrent) {
  const text = () => answerText(res, q);
  const copyBtn = el('button', { type: 'button', onclick: async () => {
    try { await navigator.clipboard.writeText(text()); copyBtn.textContent = t('copied'); setTimeout(() => { copyBtn.textContent = t('copy'); }, 1500); } catch {}
  } }, t('copy'));
  // 分享：手机上用系统自带的分享（WhatsApp、微信、短信等）；不支持的浏览器只显示"复制"
  const shareBtn = navigator.share ? el('button', { type: 'button', onclick: async () => {
    try { await navigator.share({ title: q, text: text() }); } catch {}
  } }, t('share')) : null;

  const sel = STAFF ? clientLangSelect(res) : null;

  const fbNote = el('div', {});
  const send = (verdict, note) => post('/api/feedback', { verdict, note, status: res.status, lang: res.language });
  const thanks = () => fbNote.replaceChildren(el('p', { class: 'note', role: 'status' }, t('fbThanks')));
  const fbBtn = (label, v) => el('button', { type: 'button', 'aria-pressed': 'false', onclick: e => {
    fb.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === e.currentTarget)));
    if (v === 'useful') { send(v, ''); thanks(); return; }
    const ph = v === 'offtopic' ? t('fbPhOff') : t('fbPh');
    const inp = el('input', { type: 'text', maxlength: '200', placeholder: ph, 'aria-label': ph });
    fbNote.replaceChildren(el('div', { class: 'fbnote' }, inp, el('button', { type: 'button', onclick: () => { send(v, inp.value); thanks(); } }, t('fbSend'))));
    inp.focus();
  } }, label);
  const fb = el('div', { class: 'fb', role: 'group', 'aria-label': t('fbQ') }, el('span', {}, t('fbQ')),
    fbBtn(t('useful'), 'useful'), fbBtn(t('wrong'), 'wrong'), fbBtn(t('offtopic'), 'offtopic'));

  // 用 el() 组装（它会跳过空值）；浏览器自带的 append 会把 null 显示成文字"null"
  return el('div', {}, el('div', { class: 'actions' }, sel && sel.select, shareBtn, copyBtn), el('div', { class: 'actions' }, fb), fbNote, sel && sel.box,
    isCurrent ? el('div', { class: 'actions' }, backButton(t('askAnother'))) : null);
}

// 工作人员版才有：把回答翻成客户的语言（公开版不显示，接口也关闭）
function clientLangSelect(res) {
  const select = el('select', { 'aria-label': t('client') },
    el('option', { value: '' }, t('client') + ' ▾'),
    CLIENT_LANGS.map(([native, en]) => el('option', { value: en }, native + (native === en ? '' : ' — ' + en))));
  const box = el('div', {});
  select.addEventListener('change', async () => {
    if (!select.value) return;
    box.replaceChildren(el('div', { class: 'client loading', role: 'status' }, t('translating')));
    const tr = await post('/api/translate', { answer: res, target: select.value });
    if (tr.status !== 'ok') return box.replaceChildren(el('div', { class: 'client', role: 'alert' }, tr.reason === 'translation_mismatch' ? t('trFail') : (t('reasons')[tr.reason] || t('errTitle'))));
    const bcp = CLIENT_BCP[select.value] || null;
    const text = [tr.summary, ...tr.steps.map((s, i) => `${i + 1}. ${s}`), tr.referral].filter(Boolean).join('\n');
    const c = el('button', { type: 'button', onclick: async () => { try { await navigator.clipboard.writeText(text + '\n\n' + t('clientNote')); c.textContent = t('copied'); } catch {} } }, t('copy'));
    box.replaceChildren(el('div', { class: 'client' },
      el('p', { class: 'note' }, t('clientNote')),
      el('div', { lang: bcp, dir: bcp && RTL.has(bcp) ? 'rtl' : null },
        tr.summary ? el('p', {}, el('strong', {}, rich(tr.summary))) : null,
        el('ol', {}, tr.steps.map(s => el('li', {}, rich(s)))),
        tr.referral ? el('p', {}, rich(tr.referral)) : null),
      c));
    announce();
  });
  return { select, box };
}

// ---------- 事件 ----------

// 字数：快到上限（800 字以上）才显示，平时不打扰
function updateCount() {
  const n = qBox.value.length, c = $('#count');
  c.hidden = n < 800;
  c.textContent = n + ' / 1000';
}

form.addEventListener('submit', e => { e.preventDefault(); ask(qBox.value); });
qBox.addEventListener('input', () => { updateCount(); hidePii(); });
qBox.addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); ask(qBox.value); } });
document.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => { const q = t(b.dataset.q); qBox.value = q; updateCount(); ask(q); }));
document.querySelectorAll('.langs button').forEach(b => b.addEventListener('click', () => {
  L = b.dataset.lang; try { localStorage.setItem('kia-lang', L); } catch {}
  applyLang();
  // 危机卡片的热线名称来自服务器、按界面语言给出：重新取一次（不调用 AI，不计次数）
  if (current && current.res.status === 'crisis' && !busy) { const q = current.q; current = null; ask(q, { force: true }); }
  else if (!busy) renderAll();
}));
const online = () => { $('#offline').hidden = navigator.onLine !== false; };
window.addEventListener('online', online);
window.addEventListener('offline', online);
online();
applyLang();
