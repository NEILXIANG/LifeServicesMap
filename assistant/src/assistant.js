// assistant.js — 一次提问的完整流程，和 Worker、网络无关，测试可以直接调用。
//
//   危机识别（命中就不调用 AI）→ 检索 → 调用 Claude → 程序校验 → 回答 + 来源
//
// callModel(request) 由调用方提供：Worker 里是 Claude API，测试里是假的模型。

import { buildIndex, retrieve, LANGS } from './retrieve.js';
import { ground, sameFacts, sourceCard } from './ground.js';
import { SYSTEM, TRANSLATE_SYSTEM, ANSWER_SCHEMA, TRANSLATION_SCHEMA, guessLang, taskBlock, placeBlock, lineBlocks, lineDocs } from './prompt.js';

export const MAX_QUESTION = 1000;

export function createAssistant(know, { isCrisis, callModel, model = 'claude-opus-5-5', today }) {
  const index = buildIndex(know.docs);
  const todayYM = (today || know.builtFrom.today || '').slice(0, 7);
  const allTasks = know.docs.filter(d => d.kind === 'task');
  const cardCache = new Map();   // 每种语言的办事卡文字只生成一次，字节完全相同，缓存才能命中
  const cardsText = lang => {
    if (!cardCache.has(lang)) cardCache.set(lang, JSON.stringify(allTasks.map(t => taskBlock(t, lang))));
    return cardCache.get(lang);
  };

  // 失败兜底（原则 8）：AI 不可用时也给出指南链接和 KIS、211
  function fallback(q, uiLang) {
    const L = LANGS.includes(uiLang) ? uiLang : 'en';
    const r = retrieve(know, index, q || '', { placeLimit: 0 });
    return { guide: know.city.siteUrl, tasks: r.topTasks.map(t => sourceCard(t, L)),
      lines: lineBlocks(know, L).slice(0, 2).map(l => ({ title: l.name, phone: l.phone })) };
  }

  function crisis(uiLang) {
    const L = LANGS.includes(uiLang) ? uiLang : 'en';
    const lines = know.hotlines.map(h => ({ phone: h.n, title: (h.label[L] || h.label.en || h.t) }));
    const local = [...(know.localLines || []), ...(know.localCrisis ? [know.localCrisis] : [])]
      .map(l => ({ phone: l.n, sms: l.sms || null, title: (l.note && (l.note[L] || l.note.en)) || '' }));
    return { status: 'crisis', lines, local };
  }

  async function ask(q, { uiLang = 'en' } = {}) {
    q = String(q || '').trim();
    if (!q) return { status: 'error', reason: 'empty' };
    if (q.length > MAX_QUESTION) return { status: 'error', reason: 'too_long' };
    if (isCrisis(q)) return crisis(uiLang);           // 危机：不调用 AI（说明 F3）

    const lang = guessLang(q);
    const r = retrieve(know, index, q);
    const lines = lineDocs(know, lang);
    const allowed = new Map([...r.tasks, ...r.places, ...lines].map(d => [d.id, d]));
    // 办事卡每次都一样（同一语言），放在系统规则后面并标记缓存：第二次起这部分按缓存价计费。
    // 地点和电话随问题变化，放在用户消息里，不影响缓存。
    const cards = cardsText(lang);
    const perQuestion = JSON.stringify({ places: r.places.map(p => placeBlock(p, lang)), phone_lines: lineBlocks(know, lang) });

    let raw;
    try {
      raw = await callModel({
        model, max_tokens: 16000,
        system: [{ type: 'text', text: SYSTEM },
          { type: 'text', text: '<guide_content part="task_cards">\n' + cards + '\n</guide_content>', cache_control: { type: 'ephemeral' } }],
        messages: [{ role: 'user', content: [
          { type: 'text', text: '<guide_content part="places_and_lines">\n' + perQuestion + '\n</guide_content>' },
          { type: 'text', text: '<staff_question>\n' + q + '\n</staff_question>' },
        ] }],
        output_config: { effort: 'medium', format: { type: 'json_schema', schema: ANSWER_SCHEMA } },
      });
    } catch (e) {
      return { status: 'error', reason: e && e.reason || 'ai_unavailable', fallback: fallback(q, uiLang) };
    }
    const out = ground(raw, allowed, { lang: LANGS.includes(raw && raw.language) ? raw.language : (LANGS.includes(lang) ? lang : uiLang), today: todayYM });
    if (out.status === 'not_found') out.fallback = fallback(q, uiLang);
    return out;
  }

  // 客户语言版本（F8）：翻译后电话、网址必须和原文一致，否则不给
  async function translate(answer, target) {
    const src = { summary: answer.summary || '', steps: (answer.steps || []).map(s => s.text || ''), referral: (answer.referral && answer.referral.text) || '' };
    let raw;
    try {
      raw = await callModel({
        model, max_tokens: 16000,
        system: [{ type: 'text', text: TRANSLATE_SYSTEM }],
        messages: [{ role: 'user', content: 'Target language: ' + target + '\n<answer>\n' + JSON.stringify(src) + '\n</answer>' }],
        output_config: { effort: 'low', format: { type: 'json_schema', schema: TRANSLATION_SCHEMA } },
      });
    } catch (e) {
      return { status: 'error', reason: 'ai_unavailable' };
    }
    const tr = { summary: raw.summary, steps: (raw.steps || []).map(text => ({ text })), referral: { text: raw.referral } };
    const orig = { summary: src.summary, steps: src.steps.map(text => ({ text })), referral: { text: src.referral } };
    if (!raw || (raw.steps || []).length !== src.steps.length || !sameFacts(orig, tr)) return { status: 'error', reason: 'translation_mismatch' };
    return { status: 'ok', target, summary: tr.summary, steps: tr.steps.map(s => s.text), referral: raw.referral };
  }

  return { ask, translate, index };
}
