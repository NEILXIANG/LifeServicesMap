// app.js — 助手界面。界面文字六种语言（zh/en/fr/es/ko/ja，与指南一致）；回答默认用提问的语言。
// 不在浏览器里保存提问和回答；只记住界面语言。

const T = {
  zh: {
    intro: 'AI 根据 Kamloops 生活指南中已核实的内容回答，可能出错。重要信息请以官方来源为准。',
    privacy: '请勿输入姓名、证件号码、病历等个人信息。', qLabel: '问题', placeholder: '用任何语言提问……', ask: '提问',
    quickLabel: '常见：', quick1t: '新到第一周', quick2t: '孩子入学', quick3t: '找家庭医生', quick4t: '食物银行',
    quick1: '刚到 Kamloops 第一周要办哪些事？', quick2: '孩子刚到 Kamloops，怎么报名上学？', quick3: '怎么找家庭医生？', quick4: '食物银行在哪里，怎么用？',
    privacyLink: '隐私说明', guideLink: 'Kamloops 生活指南',
    loading: '正在查找指南里的相关内容……', announce: '新回答已生成',
    sources: '来源', checked: '核实', official: '官方页面', inGuide: '在指南中打开', notChecked: '未标核实日期',
    tierOfficial: '官方', tierOwn: '本人核实', tierPlaces: '第三方资料',
    footer: 'AI 根据指南整理，以官方信息为准。',
    stale: '部分依据超过 6 个月未核实，此信息需向机构再次确认。',
    referral: '转给真人：', copy: '复制', copied: '已复制',
    client: '生成客户语言版本', clientPick: '选择语言…', clientNote: 'AI 翻译，供参考；以链接中的官方信息为准。', translating: '正在翻译……',
    trFail: '翻译未通过核对（电话或网址与原文不一致），请直接使用原文。',
    fbQ: '这个回答：', useful: '有用', wrong: '有错', fbPh: '错在哪里（一句话，不含个人信息）', fbSend: '提交', fbThanks: '谢谢，已记录。',
    notFound: '指南里没有已核实的相关信息', outScope: '这个问题需要按个人情况判断',
    tryThese: '可以试试：', relatedCards: '指南里相关的办事卡：',
    crisisTitle: '紧急求助', crisisLead: '这个问题可能涉及安全或危机。助手不会用 AI 回答，请直接使用下面的求助电话。有生命危险请立即拨 911。',
    crisisLocal: '本地专线', sms: '短信',
    errTitle: '暂时无法回答', errLead: '请稍后再试，或直接查看生活指南。', retry: '重试',
    reasons: { daily_limit: '今天的提问次数已用完。', ai_not_configured: 'AI 服务尚未配置。', ai_key: 'AI 服务的密钥无效或余额不足。', rate_limited: 'AI 服务繁忙。', too_long: '问题太长了（最多 1000 字）。', empty: '请输入问题。', forbidden: '没有访问权限，请重新登录。' },
  },
  en: {
    intro: 'Answers are drawn from verified content in the Kamloops Life Guide and may contain errors. Please confirm important details with official sources.',
    privacy: 'Please do not enter names, ID numbers, medical records or other personal information.', qLabel: 'Question', placeholder: 'Ask in any language…', ask: 'Ask',
    quickLabel: 'Common:', quick1t: 'First week', quick2t: 'School enrolment', quick3t: 'Family doctor', quick4t: 'Food bank',
    quick1: 'What should a newcomer do in their first week in Kamloops?', quick2: 'How do I enrol a child who just arrived in Kamloops in school?', quick3: 'How do I find a family doctor?', quick4: 'Where is the food bank and how does it work?',
    privacyLink: 'Privacy', guideLink: 'Kamloops Life Guide',
    loading: 'Looking up the guide…', announce: 'New answer ready',
    sources: 'Sources', checked: 'checked', official: 'Official page', inGuide: 'Open in the guide', notChecked: 'no check date',
    tierOfficial: 'official', tierOwn: 'checked by the author', tierPlaces: 'third-party listing',
    footer: 'Compiled by AI from the guide. Official sources take precedence.',
    stale: 'Some of this has not been checked for over 6 months — confirm with the organisation.',
    referral: 'Refer to a person:', copy: 'Copy', copied: 'Copied',
    client: 'Client-language version', clientPick: 'Choose a language…', clientNote: 'AI translation for reference; the official information at the link takes precedence.', translating: 'Translating…',
    trFail: 'The translation failed the check (a phone number or web address changed). Please use the original.',
    fbQ: 'This answer:', useful: 'Useful', wrong: 'Wrong', fbPh: 'What is wrong (one sentence, no personal details)', fbSend: 'Send', fbThanks: 'Thank you — noted.',
    notFound: 'The guide has no verified information on this', outScope: 'This depends on the person’s situation',
    tryThese: 'You could try:', relatedCards: 'Related task cards in the guide:',
    crisisTitle: 'Urgent help', crisisLead: 'This question may involve safety or a crisis. The assistant does not answer it with AI — please use the lines below. If a life is in danger, call 911 now.',
    crisisLocal: 'Local lines', sms: 'text',
    errTitle: 'Can’t answer right now', errLead: 'Please try again later, or use the Life Guide directly.', retry: 'Try again',
    reasons: { daily_limit: 'Today’s question limit has been reached.', ai_not_configured: 'The AI service is not configured yet.', ai_key: 'The AI service key is invalid or out of credit.', rate_limited: 'The AI service is busy.', too_long: 'The question is too long (1,000 characters at most).', empty: 'Please type a question.', forbidden: 'No access — please sign in again.' },
  },
  fr: {
    intro: 'Les réponses s’appuient sur le contenu vérifié du Guide de vie à Kamloops et peuvent contenir des erreurs. Vérifiez les informations importantes auprès des sources officielles.',
    privacy: 'N’entrez pas de noms, de numéros de pièce d’identité, de dossiers médicaux ni d’autres renseignements personnels.', qLabel: 'Question', placeholder: 'Posez votre question dans n’importe quelle langue…', ask: 'Demander',
    quickLabel: 'Fréquent :', quick1t: 'Première semaine', quick2t: 'Inscription scolaire', quick3t: 'Médecin de famille', quick4t: 'Banque alimentaire',
    quick1: 'Que doit faire un nouvel arrivant pendant sa première semaine à Kamloops ?', quick2: 'Comment inscrire à l’école un enfant qui vient d’arriver à Kamloops ?', quick3: 'Comment trouver un médecin de famille ?', quick4: 'Où se trouve la banque alimentaire et comment fonctionne-t-elle ?',
    privacyLink: 'Confidentialité', guideLink: 'Guide de vie à Kamloops',
    loading: 'Recherche dans le guide…', announce: 'Nouvelle réponse prête',
    sources: 'Sources', checked: 'vérifié', official: 'Page officielle', inGuide: 'Ouvrir dans le guide', notChecked: 'sans date de vérification',
    tierOfficial: 'officiel', tierOwn: 'vérifié par l’auteur', tierPlaces: 'fiche d’un tiers',
    footer: 'Rédigé par l’IA à partir du guide. Les sources officielles font foi.',
    stale: 'Une partie de ces informations n’a pas été vérifiée depuis plus de 6 mois — confirmez auprès de l’organisme.',
    referral: 'Orienter vers une personne :', copy: 'Copier', copied: 'Copié',
    client: 'Version dans la langue du client', clientPick: 'Choisir une langue…', clientNote: 'Traduction par IA, à titre indicatif ; l’information officielle du lien fait foi.', translating: 'Traduction…',
    trFail: 'La traduction n’a pas passé la vérification (un numéro de téléphone ou une adresse web a changé). Utilisez l’original.',
    fbQ: 'Cette réponse :', useful: 'Utile', wrong: 'Erronée', fbPh: 'Qu’est-ce qui est faux (une phrase, sans renseignements personnels)', fbSend: 'Envoyer', fbThanks: 'Merci, c’est noté.',
    notFound: 'Le guide n’a pas d’information vérifiée à ce sujet', outScope: 'Cela dépend de la situation de la personne',
    tryThese: 'Vous pouvez essayer :', relatedCards: 'Fiches pratiques du guide sur ce sujet :',
    crisisTitle: 'Aide urgente', crisisLead: 'Cette question peut concerner la sécurité ou une crise. L’assistant n’y répond pas avec l’IA — utilisez les lignes ci-dessous. Si une vie est en danger, appelez le 911 maintenant.',
    crisisLocal: 'Lignes locales', sms: 'texto',
    errTitle: 'Impossible de répondre pour le moment', errLead: 'Réessayez plus tard, ou consultez directement le guide.', retry: 'Réessayer',
    reasons: { daily_limit: 'La limite de questions du jour est atteinte.', ai_not_configured: 'Le service d’IA n’est pas encore configuré.', ai_key: 'La clé du service d’IA est invalide ou sans crédit.', rate_limited: 'Le service d’IA est occupé.', too_long: 'La question est trop longue (1 000 caractères au plus).', empty: 'Tapez une question.', forbidden: 'Accès refusé — reconnectez-vous.' },
  },
  es: {
    intro: 'Las respuestas se basan en el contenido verificado de la Guía de vida en Kamloops y pueden contener errores. Confirme la información importante con las fuentes oficiales.',
    privacy: 'No escriba nombres, números de identificación, historiales médicos ni otros datos personales.', qLabel: 'Pregunta', placeholder: 'Pregunte en cualquier idioma…', ask: 'Preguntar',
    quickLabel: 'Frecuentes:', quick1t: 'Primera semana', quick2t: 'Inscripción escolar', quick3t: 'Médico de familia', quick4t: 'Banco de alimentos',
    quick1: '¿Qué debe hacer una persona recién llegada en su primera semana en Kamloops?', quick2: '¿Cómo inscribo en la escuela a un niño que acaba de llegar a Kamloops?', quick3: '¿Cómo encuentro un médico de familia?', quick4: '¿Dónde está el banco de alimentos y cómo funciona?',
    privacyLink: 'Privacidad', guideLink: 'Guía de vida en Kamloops',
    loading: 'Buscando en la guía…', announce: 'Nueva respuesta lista',
    sources: 'Fuentes', checked: 'verificado', official: 'Página oficial', inGuide: 'Abrir en la guía', notChecked: 'sin fecha de verificación',
    tierOfficial: 'oficial', tierOwn: 'verificado por el autor', tierPlaces: 'ficha de terceros',
    footer: 'Redactado por IA a partir de la guía. Prevalecen las fuentes oficiales.',
    stale: 'Parte de esta información no se ha verificado en más de 6 meses — confírmela con la organización.',
    referral: 'Derivar a una persona:', copy: 'Copiar', copied: 'Copiado',
    client: 'Versión en el idioma del cliente', clientPick: 'Elija un idioma…', clientNote: 'Traducción por IA, solo de referencia; prevalece la información oficial del enlace.', translating: 'Traduciendo…',
    trFail: 'La traducción no pasó la verificación (cambió un teléfono o una dirección web). Use el original.',
    fbQ: 'Esta respuesta:', useful: 'Útil', wrong: 'Incorrecta', fbPh: 'Qué está mal (una frase, sin datos personales)', fbSend: 'Enviar', fbThanks: 'Gracias, queda anotado.',
    notFound: 'La guía no tiene información verificada sobre esto', outScope: 'Depende de la situación de la persona',
    tryThese: 'Puede intentar:', relatedCards: 'Fichas prácticas de la guía sobre este tema:',
    crisisTitle: 'Ayuda urgente', crisisLead: 'Esta pregunta puede tener que ver con la seguridad o una crisis. El asistente no la responde con IA; use las líneas de abajo. Si hay una vida en peligro, llame al 911 ahora.',
    crisisLocal: 'Líneas locales', sms: 'texto',
    errTitle: 'No se puede responder en este momento', errLead: 'Inténtelo más tarde o consulte directamente la guía.', retry: 'Reintentar',
    reasons: { daily_limit: 'Se alcanzó el límite de preguntas de hoy.', ai_not_configured: 'El servicio de IA aún no está configurado.', ai_key: 'La clave del servicio de IA no es válida o no tiene saldo.', rate_limited: 'El servicio de IA está ocupado.', too_long: 'La pregunta es demasiado larga (máximo 1000 caracteres).', empty: 'Escriba una pregunta.', forbidden: 'Sin acceso; vuelva a iniciar sesión.' },
  },
  ko: {
    intro: 'Kamloops 생활 가이드에서 확인된 내용을 바탕으로 AI가 답하며, 틀릴 수 있습니다. 중요한 정보는 공식 출처에서 확인하세요.',
    privacy: '이름, 신분증 번호, 진료 기록 등 개인정보를 입력하지 마세요.', qLabel: '질문', placeholder: '어떤 언어로든 질문하세요…', ask: '질문하기',
    quickLabel: '자주 묻는 질문:', quick1t: '도착 첫 주', quick2t: '자녀 입학', quick3t: '가정의 찾기', quick4t: '푸드뱅크',
    quick1: 'Kamloops에 도착한 첫 주에 무엇을 해야 하나요?', quick2: 'Kamloops에 막 도착한 아이를 학교에 어떻게 등록하나요?', quick3: '가정의는 어떻게 찾나요?', quick4: '푸드뱅크는 어디에 있고 어떻게 이용하나요?',
    privacyLink: '개인정보 안내', guideLink: 'Kamloops 생활 가이드',
    loading: '가이드에서 관련 내용을 찾는 중…', announce: '새 답변이 준비되었습니다',
    sources: '출처', checked: '확인', official: '공식 페이지', inGuide: '가이드에서 열기', notChecked: '확인 날짜 없음',
    tierOfficial: '공식', tierOwn: '작성자 확인', tierPlaces: '제3자 정보',
    footer: 'AI가 가이드를 바탕으로 정리했습니다. 공식 정보가 우선입니다.',
    stale: '일부 내용은 6개월 넘게 확인되지 않았습니다 — 해당 기관에 다시 확인하세요.',
    referral: '담당자 연결:', copy: '복사', copied: '복사됨',
    client: '고객 언어 버전 만들기', clientPick: '언어 선택…', clientNote: 'AI 번역이며 참고용입니다. 링크의 공식 정보가 우선입니다.', translating: '번역 중…',
    trFail: '번역이 확인을 통과하지 못했습니다(전화번호나 웹 주소가 바뀜). 원문을 사용하세요.',
    fbQ: '이 답변:', useful: '도움 됨', wrong: '틀림', fbPh: '무엇이 틀렸나요(한 문장, 개인정보 제외)', fbSend: '보내기', fbThanks: '감사합니다. 기록했습니다.',
    notFound: '가이드에 이에 관한 확인된 정보가 없습니다', outScope: '개인 상황에 따라 판단해야 하는 질문입니다',
    tryThese: '이렇게 해 보세요:', relatedCards: '가이드의 관련 안내 카드:',
    crisisTitle: '긴급 도움', crisisLead: '안전이나 위기와 관련된 질문일 수 있습니다. 도우미는 AI로 답하지 않습니다 — 아래 전화번호를 바로 이용하세요. 생명이 위험하면 지금 911에 전화하세요.',
    crisisLocal: '지역 전화', sms: '문자',
    errTitle: '지금은 답할 수 없습니다', errLead: '잠시 후 다시 시도하거나 생활 가이드를 직접 보세요.', retry: '다시 시도',
    reasons: { daily_limit: '오늘 질문 횟수를 모두 사용했습니다.', ai_not_configured: 'AI 서비스가 아직 설정되지 않았습니다.', ai_key: 'AI 서비스 키가 잘못되었거나 잔액이 없습니다.', rate_limited: 'AI 서비스가 바쁩니다.', too_long: '질문이 너무 깁니다(최대 1,000자).', empty: '질문을 입력하세요.', forbidden: '접근 권한이 없습니다. 다시 로그인하세요.' },
  },
  ja: {
    intro: 'Kamloops 生活ガイドの確認済みの内容をもとに AI が回答します。誤りがある場合があります。重要な情報は公式の情報源で確認してください。',
    privacy: '氏名、身分証の番号、診療記録などの個人情報は入力しないでください。', qLabel: '質問', placeholder: 'どの言語でも質問できます…', ask: '質問する',
    quickLabel: 'よくある質問：', quick1t: '到着後1週間', quick2t: '子どもの入学', quick3t: 'かかりつけ医', quick4t: 'フードバンク',
    quick1: 'Kamloops に着いて最初の1週間に何をすればいいですか？', quick2: 'Kamloops に来たばかりの子どもを学校に登録するには？', quick3: 'かかりつけ医（ファミリードクター）はどう探せばいいですか？', quick4: 'フードバンクはどこにあり、どう利用しますか？',
    privacyLink: 'プライバシー', guideLink: 'Kamloops 生活ガイド',
    loading: 'ガイドから関連する内容を探しています…', announce: '新しい回答ができました',
    sources: '出典', checked: '確認', official: '公式ページ', inGuide: 'ガイドで開く', notChecked: '確認日なし',
    tierOfficial: '公式', tierOwn: '作成者が確認', tierPlaces: '第三者の情報',
    footer: 'AI がガイドをもとにまとめました。公式の情報が優先です。',
    stale: '一部の情報は6か月以上確認されていません — 機関に改めて確認してください。',
    referral: '担当者につなぐ：', copy: 'コピー', copied: 'コピーしました',
    client: 'お客様の言語版を作る', clientPick: '言語を選ぶ…', clientNote: 'AI による翻訳で参考用です。リンク先の公式情報が優先です。', translating: '翻訳しています…',
    trFail: '翻訳が確認を通りませんでした（電話番号またはウェブアドレスが変わっています）。原文を使ってください。',
    fbQ: 'この回答：', useful: '役に立った', wrong: '誤りがある', fbPh: 'どこが誤りか（一文で、個人情報は含めずに）', fbSend: '送信', fbThanks: 'ありがとうございます。記録しました。',
    notFound: 'ガイドにはこの件の確認済みの情報がありません', outScope: '個人の状況によって判断が必要な質問です',
    tryThese: '次を試してください：', relatedCards: 'ガイドの関連する手続きカード：',
    crisisTitle: '緊急の支援', crisisLead: '安全や危機に関わる質問の可能性があります。このアシスタントは AI では回答しません — 下の電話番号を直接使ってください。命に危険がある場合は、今すぐ 911 に電話してください。',
    crisisLocal: '地域の窓口', sms: 'SMS',
    errTitle: '今は回答できません', errLead: 'しばらくしてからもう一度試すか、生活ガイドを直接ご覧ください。', retry: 'もう一度試す',
    reasons: { daily_limit: '今日の質問回数の上限に達しました。', ai_not_configured: 'AI サービスがまだ設定されていません。', ai_key: 'AI サービスのキーが無効か、残高がありません。', rate_limited: 'AI サービスが混み合っています。', too_long: '質問が長すぎます（1,000文字まで）。', empty: '質問を入力してください。', forbidden: 'アクセス権がありません。もう一度ログインしてください。' },
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

const $ = s => document.querySelector(s);
const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) e.append(c.nodeType ? c : document.createTextNode(String(c)));
  return e;
};
const telHref = p => 'tel:' + String(p).replace(/[^\d+]/g, '');
// 回答文字里的电话：可点击拨号，且不在中间折行（这些号码已由服务器核对过出自指南）
const PHONE_RE = /((?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}|\b\d-\d-\d\b|\b(?:911|811|211)\b)/g;
const rich = text => String(text).split(PHONE_RE).map((part, i) => i % 2 ? el('a', { class: 'tel-inline', href: telHref(part) }, part) : part);

function applyLang() {
  document.documentElement.lang = L === 'zh' ? 'zh-Hans' : L;
  document.querySelectorAll('[data-t]').forEach(n => { n.textContent = t(n.dataset.t); });
  document.querySelectorAll('[data-ph]').forEach(n => { n.placeholder = t(n.dataset.ph); });
  document.querySelectorAll('[data-al]').forEach(n => { n.setAttribute('aria-label', t(n.dataset.al)); });
  document.querySelectorAll('.langs button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lang === L)));
  const pl = document.querySelector('a[href^="privacy.html"]');
  if (pl) pl.setAttribute('href', 'privacy.html#' + L);
}

const out = $('#out');
let lastQ = '', lastAnswer = null, lastRes = null;

async function post(path, payload) {
  const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (r.status === 403) return { status: 'error', reason: 'forbidden' };
  try { return await r.json(); } catch { return { status: 'error', reason: 'ai_unavailable' }; }
}

function announce() { const a = $('#announce'); a.textContent = ''; setTimeout(() => { a.textContent = t('announce'); }, 50); }

async function ask(q) {
  q = q.trim();
  if (!q) return;
  lastQ = q;
  $('#go').disabled = true;
  out.replaceChildren(el('div', { class: 'card loading', role: 'status' }, t('loading')));
  const res = await post('/api/ask', { q, uiLang: L });
  $('#go').disabled = false;
  render(res);
  announce();
}

function render(res) {
  lastRes = res;
  if (res.status === 'crisis') return out.replaceChildren(crisisCard(res));
  if (res.status === 'error') return out.replaceChildren(errorCard(res));
  out.replaceChildren(answerCard(res));
}

function crisisCard(res) {
  const line = l => el('li', {}, el('a', { class: 'tel', href: telHref(l.phone) }, l.phone), ' ', l.title);
  // 本地专线的说明来自指南，写法是"……或打电话："，号码接在说明后面
  const local = l => el('li', {}, l.title, ' ', el('a', { class: 'tel', href: telHref(l.phone) }, l.phone),
    l.sms ? el('span', {}, ' · ', t('sms'), ' ', el('a', { href: 'sms:' + l.sms.replace(/[^\d+]/g, '') }, l.sms)) : null);
  return el('div', { class: 'card crisis', role: 'alert' },
    el('h2', {}, '⚠ ', t('crisisTitle')), el('p', {}, t('crisisLead')),
    el('ul', {}, res.lines.map(line)),
    res.local && res.local.length ? [el('h3', {}, t('crisisLocal')), el('ul', {}, res.local.map(local))] : null);
}

function fallbackBlock(fb) {
  if (!fb) return null;
  return el('div', {},
    fb.tasks && fb.tasks.length ? [el('p', {}, t('relatedCards')), el('ul', {}, fb.tasks.map(c => el('li', {}, el('a', { href: c.guide, target: '_blank', rel: 'noopener' }, c.title))))] : null,
    el('p', {}, t('tryThese')),
    el('ul', {}, (fb.lines || []).map(l => el('li', {}, l.title, ' ', el('a', { class: 'tel', href: telHref(l.phone) }, l.phone))),
      el('li', {}, el('a', { href: fb.guide, target: '_blank', rel: 'noopener' }, t('guideLink')))));
}

function errorCard(res) {
  const why = (t('reasons')[res.reason]) || '';
  return el('div', { class: 'card error', role: 'alert' },
    el('h2', {}, t('errTitle')), el('p', {}, [why, t('errLead')].filter(Boolean).join(' ')),
    lastQ && res.reason !== 'daily_limit' && res.reason !== 'too_long' ? el('button', { type: 'button', class: 'primary', onclick: () => ask(lastQ) }, t('retry')) : null,
    fallbackBlock(res.fallback));
}

function answerText(res) {
  const num = new Map(res.sources.map((s, i) => [s.source_id, i + 1]));
  const lines = [];
  if (res.summary) lines.push(res.summary);
  res.steps.forEach((s, i) => lines.push(`${i + 1}. ${s.text} [${s.source_ids.map(id => num.get(id)).join(',')}]`));
  if (res.referral) lines.push(t('referral') + ' ' + res.referral.text);
  lines.push('', t('sources') + ':');
  res.sources.forEach((s, i) => lines.push(`[${i + 1}] ${s.title}${s.phone ? ' ' + s.phone : ''}${s.url ? ' ' + s.url : ''}${s.checked ? ' (' + t('checked') + ' ' + s.checked + ')' : ''}`));
  lines.push('', t('footer'));
  return lines.join('\n');
}

function answerCard(res) {
  lastAnswer = res;
  const num = new Map(res.sources.map((s, i) => [s.source_id, i + 1]));
  const cites = ids => ids.map(id => el('a', { class: 'cite', href: '#src-' + num.get(id), 'aria-label': t('sources') + ' ' + num.get(id) }, '[' + num.get(id) + ']'));
  const heading = res.status === 'not_found' ? t('notFound') : res.status === 'out_of_scope' ? t('outScope') : null;
  const lang = res.language && /^[a-z]{2}$/.test(res.language) ? res.language : null;

  const card = el('article', { class: 'card answer' },
    heading ? el('h2', {}, heading) : null,
    el('div', { lang },
      res.summary ? el('p', {}, el('strong', {}, rich(res.summary))) : null,
      res.steps.length ? el('ol', {}, res.steps.map(s => el('li', {}, rich(s.text), cites(s.source_ids)))) : null,
      res.referral ? el('p', { class: 'referral' }, el('strong', {}, t('referral') + ' '), rich(res.referral.text), cites(res.referral.source_ids)) : null),
    res.stale ? el('p', { class: 'stale' }, t('stale')) : null,
    res.status === 'not_found' ? fallbackBlock(res.fallback) : null,
    res.sources.length ? el('div', { class: 'sources' }, el('h3', {}, t('sources')), el('ol', {}, res.sources.map((s, i) => sourceItem(s, i + 1)))) : null,
    el('p', { class: 'note' }, t('footer')),
    actions(res));
  return card;
}

function sourceItem(s, n) {
  const tier = s.type === 'place' && s.tier ? (s.official ? t('tierOfficial') : s.tier === 'own' ? t('tierOwn') : s.tier === 'places' ? t('tierPlaces') : null) : null;
  return el('li', { id: 'src-' + n },
    el('strong', {}, s.title), tier ? el('span', { class: 'tier' }, tier) : null,
    s.category ? el('span', { class: 'meta' }, ' · ' + s.category) : null,
    s.address ? el('span', { class: 'meta' }, ' · ' + s.address) : null,
    s.phone ? el('span', {}, ' · ', el('a', { href: telHref(s.phone) }, s.phone)) : null,
    // 热线不是办事卡或地点，没有核实月份这一项，不显示
    s.type === 'line' ? null : el('span', { class: 'meta' }, ' · ' + (s.checked ? t('checked') + ' ' + s.checked : t('notChecked'))),
    el('br'),
    s.url ? el('a', { href: s.url, target: '_blank', rel: 'noopener' }, (s.type === 'task' ? t('official') : s.url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')) + ' ↗') : null,
    s.url && s.guide ? ' · ' : null,
    s.guide ? el('a', { href: s.guide, target: '_blank', rel: 'noopener' }, t('inGuide') + ' ↗') : null);
}

function actions(res) {
  const box = el('div', {});
  const copyBtn = el('button', { type: 'button', onclick: async () => {
    try { await navigator.clipboard.writeText(answerText(res)); copyBtn.textContent = t('copied'); setTimeout(() => { copyBtn.textContent = t('copy'); }, 1500); } catch {}
  } }, t('copy'));
  const sel = el('select', { 'aria-label': t('client') },
    el('option', { value: '' }, t('client') + ' ▾'),
    CLIENT_LANGS.map(([native, en]) => el('option', { value: en }, native + (native === en ? '' : ' — ' + en))));
  const clientBox = el('div', {});
  sel.addEventListener('change', async () => {
    if (!sel.value) return;
    clientBox.replaceChildren(el('div', { class: 'client loading', role: 'status' }, t('translating')));
    const tr = await post('/api/translate', { answer: res, target: sel.value });
    if (tr.status !== 'ok') return clientBox.replaceChildren(el('div', { class: 'client', role: 'alert' }, tr.reason === 'translation_mismatch' ? t('trFail') : (t('reasons')[tr.reason] || t('errTitle'))));
    const bcp = CLIENT_BCP[sel.value] || null;
    const text = [tr.summary, ...tr.steps.map((s, i) => `${i + 1}. ${s}`), tr.referral].filter(Boolean).join('\n');
    const c = el('button', { type: 'button', onclick: async () => { try { await navigator.clipboard.writeText(text + '\n\n' + t('clientNote')); c.textContent = t('copied'); } catch {} } }, t('copy'));
    clientBox.replaceChildren(el('div', { class: 'client' },
      el('p', { class: 'note' }, t('clientNote')),
      el('div', { lang: bcp, dir: bcp && RTL.has(bcp) ? 'rtl' : null },
        tr.summary ? el('p', {}, el('strong', {}, rich(tr.summary))) : null,
        el('ol', {}, tr.steps.map(s => el('li', {}, rich(s)))),
        tr.referral ? el('p', {}, rich(tr.referral)) : null),
      c));
    announce();
  });

  const fbNote = el('div', {});
  const fbBtn = (k, v) => el('button', { type: 'button', 'aria-pressed': 'false', onclick: e => {
    fb.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === e.currentTarget)));
    if (v === 'useful') { send(v, ''); fbNote.replaceChildren(el('p', { class: 'note', role: 'status' }, t('fbThanks'))); return; }
    const inp = el('input', { type: 'text', maxlength: '200', placeholder: t('fbPh'), 'aria-label': t('fbPh') });
    fbNote.replaceChildren(el('div', { class: 'fbnote' }, inp, el('button', { type: 'button', onclick: () => { send(v, inp.value); fbNote.replaceChildren(el('p', { class: 'note', role: 'status' }, t('fbThanks'))); } }, t('fbSend'))));
    inp.focus();
  } }, t(k));
  const send = (verdict, note) => post('/api/feedback', { verdict, note, status: res.status, lang: res.language });
  const fb = el('div', { class: 'fb', role: 'group', 'aria-label': t('fbQ') }, el('span', {}, t('fbQ')), fbBtn('useful', 'useful'), fbBtn('wrong', 'wrong'));

  box.append(el('div', { class: 'actions' }, sel, copyBtn, fb), fbNote, clientBox);
  return box;
}

// 事件
$('#ask').addEventListener('submit', e => { e.preventDefault(); ask($('#q').value); });
$('#q').addEventListener('input', e => { $('#count').textContent = e.target.value.length + ' / 1000'; });
$('#q').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); ask(e.target.value); } });
document.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => { const q = t(b.dataset.q); $('#q').value = q; $('#count').textContent = q.length + ' / 1000'; ask(q); }));
document.querySelectorAll('.langs button').forEach(b => b.addEventListener('click', () => {
  L = b.dataset.lang; try { localStorage.setItem('kia-lang', L); } catch {}
  applyLang();
  // 危机卡片的热线名称来自服务器、按界面语言给出：重新取一次（不调用 AI，不计次数）
  if (lastRes && lastRes.status === 'crisis' && lastQ) ask(lastQ);
  else if (lastRes && !out.querySelector('.loading')) render(lastRes);
}));
applyLang();
