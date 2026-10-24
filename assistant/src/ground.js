// ground.js — AI 回答的程序校验（说明 §8.1.2，不靠 AI 自觉）。
//
// 1. 引用的来源编号必须属于本次交给 AI 的内容，否则丢掉这条引用；
// 2. 每一步里出现的电话、网址必须在它引用的来源里原样存在，否则整步删掉；
// 3. 来源的名称、链接、核实日期由程序从数据里取，AI 不生成；
// 4. 删完没有有效步骤的"有据回答"改成"不知道"。

import { LANGS } from './retrieve.js';

const PHONE = /(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}|\b\d-\d-\d\b|\b(?:911|811|211|988)\b|\b310-\d{4}\b/g;
const URL_RE = /\bhttps?:\/\/[^\s<>"')\]]+|\b(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:ca|com|org|net|gov|bc\.ca)(?:\/[^\s<>"')\]]*)?/gi;

export const digits = s => String(s).replace(/\D/g, '').replace(/^1(?=\d{10}$)/, '');
const host = u => String(u).toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/[/?#].*$/, '').replace(/\.$/, '');

export function phonesIn(text) { return (String(text).match(PHONE) || []).map(digits).filter(Boolean); }
export function urlsIn(text) { return (String(text).match(URL_RE) || []).map(u => u.replace(/[.,;:]+$/, '')); }

// 一条来源（办事卡 / 地点 / 热线）里所有可以出现的文字，用来核对电话和网址
export function sourceText(d) {
  if (!d) return '';
  const vals = [];
  const walk = v => {
    if (v == null) return;
    if (typeof v === 'string') vals.push(v);
    else if (Array.isArray(v)) v.forEach(walk);
    else if (typeof v === 'object') Object.values(v).forEach(walk);
  };
  walk(d);
  return vals.join('\n');
}

function supported(text, srcText) {
  const okPhones = new Set(phonesIn(srcText));
  for (const p of phonesIn(text)) if (!okPhones.has(p)) return false;
  const okHosts = new Set(urlsIn(srcText).map(host));
  for (const u of urlsIn(text)) if (!okHosts.has(host(u))) return false;
  return true;
}

function monthsBetween(ym, today) {
  const [y, m] = String(ym).split('-').map(Number);
  const [ty, tm] = String(today).split('-').map(Number);
  if (!y || !m || !ty || !tm) return Infinity;
  return (ty - y) * 12 + (tm - m);
}

// 程序生成的来源卡片：名称、链接、核实日期全部取自数据
export function sourceCard(d, lang) {
  const L = LANGS.includes(lang) ? lang : 'en';
  if (d.kind === 'task') {
    return { source_id: d.id, type: 'task', title: (d.t && (d.t[L] || d.t.en)) || d.id,
      url: (d.srcL && d.srcL[L]) || d.src || null, urlName: (d.srcNameL && d.srcNameL[L]) || d.srcName || null,
      guide: d.guide ? d.guide[L] || d.guide.en : null, checked: d.checked || null, official: true };
  }
  if (d.kind === 'place') {
    return { source_id: d.id, type: 'place', title: d.n, url: d.w || null, phone: d.p || null, address: d.a || null,
      category: (d.cat && (d.cat[L] || d.cat.en)) || d.c, checked: d.checked || null,
      map: d.map ? d.map[L] || d.map.en : null,
      // 来源分级：official / opendata 是官方，own 是本人核实，places 是第三方商业资料
      tier: d.srcTier || null, official: d.srcTier === 'official' || d.srcTier === 'opendata' };
  }
  return { source_id: d.id, type: 'line', title: d.title || d.n, phone: d.n, checked: null, official: true };
}

// raw：AI 按 schema 返回的对象；allowed：Map(id → 记录)；返回给界面的回答
export function ground(raw, allowed, { lang, today, staleMonths = 6 } = {}) {
  const dropped = { sources: 0, steps: 0 };
  const status = raw && raw.status;
  const keepIds = ids => (Array.isArray(ids) ? ids : []).filter(id => {
    if (allowed.has(id)) return true;
    dropped.sources++;
    return false;
  });
  const used = new Set();
  const check = (text, ids) => {
    const good = keepIds(ids);
    if (!good.length) return null;
    const src = good.map(id => sourceText(allowed.get(id))).join('\n');
    if (!supported(text, src)) return null;
    good.forEach(id => used.add(id));
    return good;
  };

  const steps = [];
  for (const s of (raw && Array.isArray(raw.steps) ? raw.steps : []).slice(0, 8)) {
    const ids = check(s && s.text, s && s.source_ids);
    if (ids && s.text) steps.push({ text: String(s.text), source_ids: ids });
    else dropped.steps++;
  }

  // 一句话结论和转介没有电话/网址时才保留；有电话/网址的必须出自它引用的来源
  let summary = raw && typeof raw.summary === 'string' ? raw.summary : '';
  if (summary && (phonesIn(summary).length || urlsIn(summary).length)) {
    const src = [...used].map(id => sourceText(allowed.get(id))).join('\n');
    if (!supported(summary, src)) summary = '';
  }
  let referral = null;
  if (raw && raw.referral && raw.referral.text) {
    const ids = check(raw.referral.text, raw.referral.source_ids);
    if (ids) referral = { text: String(raw.referral.text), source_ids: ids };
    else if (!phonesIn(raw.referral.text).length && !urlsIn(raw.referral.text).length) referral = { text: String(raw.referral.text), source_ids: [] };
  }

  let outStatus = ['grounded_answer', 'not_found', 'out_of_scope'].includes(status) ? status : 'not_found';
  if (outStatus === 'grounded_answer' && !steps.length) outStatus = 'not_found';
  if (outStatus === 'out_of_scope' && !steps.length && !referral) outStatus = 'not_found';

  const sources = [...used].map(id => sourceCard(allowed.get(id), lang));
  const stale = sources.some(s => s.checked && today && monthsBetween(s.checked, today) > staleMonths);
  return { status: outStatus, language: (raw && raw.language) || lang, summary, steps, referral, sources, stale, dropped };
}

// 客户语言版本的核对：翻译后的电话、网址必须和原文一样（说明 §8.2 翻译出错）
export function sameFacts(original, translated) {
  const bag = o => {
    const t = [o.summary, ...(o.steps || []).map(s => s.text), o.referral && o.referral.text].filter(Boolean).join('\n');
    return { p: phonesIn(t).sort().join(','), u: urlsIn(t).map(host).sort().join(',') };
  };
  const a = bag(original), b = bag(translated);
  return a.p === b.p && a.u === b.u;
}
