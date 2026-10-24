// claude.js — 调用 Claude API（官方 SDK），返回按 schema 解析好的对象。
//
// 失败时抛出带 reason 的错误，由 assistant.js 显示兜底内容。
// 不记录提问和回答原文（说明 §9）。

import Anthropic from '@anthropic-ai/sdk';

export function makeCallModel(apiKey, { onUsage } = {}) {
  const client = new Anthropic({ apiKey, maxRetries: 1, timeout: 60_000 });
  return async function callModel(req) {
    let res;
    try {
      // 被安全分类器拒答时由服务器自动换模型重试（server-side fallback）
      res = await client.beta.messages.create({ ...req, betas: ['server-side-fallback-2026-07-01'], fallbacks: 'default' });
    } catch (e) {
      const err = new Error('claude_api');
      err.reason = e instanceof Anthropic.RateLimitError ? 'rate_limited'
        : e instanceof Anthropic.AuthenticationError || e instanceof Anthropic.PermissionDeniedError ? 'ai_key'
        : 'ai_unavailable';
      err.status = e && e.status;
      throw err;
    }
    if (onUsage) onUsage(res.usage, res.model);
    if (res.stop_reason === 'refusal' || res.stop_reason === 'max_tokens') {
      const err = new Error('claude_stop');
      err.reason = res.stop_reason === 'refusal' ? 'ai_refused' : 'ai_unavailable';
      throw err;
    }
    const text = res.content.filter(b => b.type === 'text').map(b => b.text).join('');
    try {
      return JSON.parse(text);
    } catch {
      const err = new Error('claude_json');
      err.reason = 'ai_unavailable';
      throw err;
    }
  };
}
