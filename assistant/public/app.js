// app.js — 助手界面。界面文字先做中文和英文（说明 §10.5）；回答默认用提问的语言。
// 不在浏览器里保存提问和回答；只记住界面语言。

const T = {
  zh: {
    badge: 'KIS 内部', intro: 'AI 根据 Kamloops 生活指南中已核实的内容回答，可能出错。重要信息请以官方来源为准。',
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
    badge: 'KIS internal', intro: 'Answers are drawn from verified content in the Kamloops Life Guide and may contain errors. Please confirm important details with official sources.',
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

let L = 'zh';
try { const s = localStorage.getItem('kia-lang'); if (s === 'en' || s === 'zh') L = s; } catch {}
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
  document.documentElement.lang = L === 'zh' ? 'zh-Hans' : 'en';
  document.querySelectorAll('[data-t]').forEach(n => { n.textContent = t(n.dataset.t); });
  document.querySelectorAll('[data-ph]').forEach(n => { n.placeholder = t(n.dataset.ph); });
  document.querySelectorAll('[data-al]').forEach(n => { n.setAttribute('aria-label', t(n.dataset.al)); });
  document.querySelectorAll('.langs button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lang === L)));
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
