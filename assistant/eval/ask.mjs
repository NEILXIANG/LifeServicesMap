// 本机直接问一个问题（不经过 Worker）：node eval/ask.mjs "问题"
// 密钥从 ~/.anthropic_key 读取（或环境变量 ANTHROPIC_API_KEY），不打印。
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createAssistant } from '../src/assistant.js';
import { makeCallModel } from '../src/claude.js';

const here = path.dirname(fileURLToPath(import.meta.url));
export function loadKey() {
  if (process.env.ANTHROPIC_API_KEY) return process.env.ANTHROPIC_API_KEY;
  const f = path.join(os.homedir(), '.anthropic_key');
  return fs.existsSync(f) ? fs.readFileSync(f, 'utf8').trim() : '';
}
export async function load(opts = {}) {
  const know = JSON.parse(fs.readFileSync(path.join(here, '..', 'build', 'knowledge.json'), 'utf8'));
  const { isCrisis } = await import('../src/crisis.js');
  return createAssistant(know, { isCrisis, callModel: opts.callModel || makeCallModel(loadKey()), model: process.env.MODEL || 'claude-opus-5-5',
    // 2026-10-24 起线上是公开版；AUDIENCE=staff 可测工作人员版
    audience: process.env.AUDIENCE || 'public' });
}
if (import.meta.url === `file://${process.argv[1]}`) {
  const a = await load();
  const t0 = Date.now();
  const out = await a.ask(process.argv[2] || '怎么办 SIN', { uiLang: 'zh' });
  console.log(JSON.stringify(out, null, 1));
  console.error(`(${((Date.now() - t0) / 1000).toFixed(1)} s)`);
}
