// worker.js — kamloops-assistant 的 Cloudflare Worker。
//
//   GET  /…               界面（public/），先过 Access 校验，再加安全头
//   POST /api/ask         { q, uiLang } → 回答（见 assistant.js）
//   POST /api/translate   { answer, target } → 客户语言版本（只在工作人员版）
//   POST /api/feedback    { verdict, status, lang, note } → 匿名反馈（写 Analytics Engine，若已绑定）
//   GET  /api/health      AI 是否可用（不含任何密钥）
//
// 隐私（说明 §9）：不保存、不记录提问和回答原文；反馈只记"有用/有错"和一句去掉数字与邮箱的说明。

import know from '../build/knowledge.json';
import { isCrisis } from './crisis.js';
import { createAssistant, MAX_QUESTION } from './assistant.js';
import { makeCallModel } from './claude.js';
import { verifyAccess } from './access.js';
import { checkLimits } from './limits.js';

const SECURITY_HEADERS = {
  'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; " +
    "connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'",
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'X-Frame-Options': 'DENY',
  'Permissions-Policy': 'geolocation=(), camera=(), microphone=(), payment=()',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cache-Control': 'no-store',
  'X-Robots-Tag': 'noindex, nofollow',
};

function withHeaders(resp) {
  const h = new Headers(resp.headers);
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) h.set(k, v);
  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: h });
}
const json = (obj, status = 200) => withHeaders(new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json; charset=utf-8' } }));

function sameSite(request, url) {
  const origin = request.headers.get('Origin');
  if (origin) { try { return new URL(origin).host === url.host; } catch { return false; } }
  return request.headers.get('Sec-Fetch-Site') === 'same-origin';
}

// 公开（PUBLIC=1，2026-10-24 Neil 决定）：像生活指南一样任何人都能打开，回答直接面向新移民；
// 否则只给登录的 KIS 工作人员（Cloudflare Access），回答面向工作人员，并有"客户语言版本"。
const isPublic = env => env.PUBLIC === '1';
const audience = env => (isPublic(env) ? 'public' : 'staff');

let _assistant = null, _key = null;
function assistant(env) {
  if (!_assistant || _key !== env.ANTHROPIC_API_KEY) {
    _key = env.ANTHROPIC_API_KEY;
    const callModel = _key ? makeCallModel(_key) : async () => { const e = new Error('no key'); e.reason = 'ai_not_configured'; throw e; };
    _assistant = createAssistant(know, { isCrisis, callModel, model: env.MODEL || 'claude-opus-5-5', audience: audience(env) });
  }
  return _assistant;
}

async function body(request) {
  if (Number(request.headers.get('Content-Length') || 0) > 20000) return null;
  try { return await request.json(); } catch { return null; }
}

const clean = s => String(s || '').slice(0, 200).replace(/\S+@\S+/g, '[email]').replace(/\d[\d\s-]{4,}\d/g, '[number]');

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (!isPublic(env)) {
      const gate = await verifyAccess(request, env, ctx);
      if (!gate.ok) return json({ status: 'forbidden', reason: gate.why }, 403);
    }

    if (!url.pathname.startsWith('/api/')) return withHeaders(await env.ASSETS.fetch(request));

    if (url.pathname === '/api/health' && request.method === 'GET') {
      return json({ ai: !!env.ANTHROPIC_API_KEY, model: env.MODEL || 'claude-opus-5-5', audience: audience(env), built: know.builtFrom });
    }
    if (request.method !== 'POST' || !sameSite(request, url)) return json({ status: 'error', reason: 'bad_request' }, 400);
    const b = await body(request);
    if (!b) return json({ status: 'error', reason: 'bad_request' }, 400);

    if (url.pathname === '/api/ask') {
      const a = assistant(env);
      // 危机提问不计入上限，也不调用 AI
      // 空问题、过长的问题不调用 AI，也不计次数；危机提问同样不计次数
      const q = String(b.q || '').trim();
      if (q && q.length <= MAX_QUESTION && !isCrisis(q)) {
        const why = await checkLimits(request, env);
        if (why) return json({ status: 'error', reason: why });
      }
      return json(await a.ask(b.q, { uiLang: b.uiLang }));
    }
    if (url.pathname === '/api/translate' && !isPublic(env)) {
      if (!b.answer || !b.target || String(b.target).length > 40) return json({ status: 'error', reason: 'bad_request' }, 400);
      const why = await checkLimits(request, env);
      if (why) return json({ status: 'error', reason: why });
      return json(await assistant(env).translate(b.answer, String(b.target)));
    }
    if (url.pathname === '/api/feedback') {
      if (env.ANALYTICS) {
        env.ANALYTICS.writeDataPoint({ blobs: ['feedback', String(b.verdict || '').slice(0, 10), String(b.status || '').slice(0, 20),
          String(b.lang || '').slice(0, 10), clean(b.note)], doubles: [1], indexes: ['assistant'] });
      }
      return json({ status: 'ok' });
    }
    return json({ status: 'error', reason: 'not_found' }, 404);
  },
};
