// eval/run.mjs — 用真实的 Claude 跑测试题（花钱！说明 §12.1）。
//
//   node eval/run.mjs              # 默认只跑 smoke 的 5 道（Neil 2026-10-23）
//   node eval/run.mjs q10 q18      # 只跑指定的题
//   node eval/run.mjs --all        # 全部 30 道——先问 Neil
//   node eval/run.mjs --dry        # 只列出要跑哪些题和预计费用，不调用
//
// 危机题不调用 AI，免费。每次跑完打印实际用量和费用，结果写到 eval/results/（不入仓）。
// 评分全部由程序判定（状态、引用、必须/禁止的说法、电话出自指南、不泄露规则），人工评分另记。

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { load, loadKey } from './ask.mjs';
import { makeCallModel } from '../src/claude.js';
import { phonesIn, sourceText } from '../src/ground.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const bank = JSON.parse(fs.readFileSync(path.join(here, 'questions.json'), 'utf8')).items;
const know = JSON.parse(fs.readFileSync(path.join(here, '..', 'build', 'knowledge.json'), 'utf8'));

// Claude Opus 5.5 价格（美元 / 百万 token）：输入 4、输出 20、写缓存 5（1.25 倍）、读缓存 0.20
const PRICE = { in: 4, out: 20, cacheWrite: 5, cacheRead: 0.2 };
const EST_PER_Q = 0.08;

const args = process.argv.slice(2);
const ids = args.filter((a, i) => !a.startsWith('--') && args[i - 1] !== '--regrade');
const pick = args.includes('--all') ? bank : ids.length ? bank.filter(q => ids.includes(q.id)) : bank.filter(q => q.smoke);
const paid = pick.filter(q => q.type !== 'crisis').length;
console.log(`要跑 ${pick.length} 道（其中 ${paid} 道调用 AI，预计约 $${(paid * EST_PER_Q).toFixed(2)}）：${pick.map(q => q.id).join(' ')}`);
if (args.includes('--dry')) process.exit(0);
if (paid && !args.includes('--regrade') && !loadKey()) { console.error('没有密钥（~/.anthropic_key 或 ANTHROPIC_API_KEY）'); process.exit(2); }

const usage = { in: 0, out: 0, cacheWrite: 0, cacheRead: 0, calls: 0 };
const callModel = makeCallModel(loadKey(), { onUsage: u => {
  usage.calls++; usage.in += u.input_tokens || 0; usage.out += u.output_tokens || 0;
  usage.cacheWrite += u.cache_creation_input_tokens || 0; usage.cacheRead += u.cache_read_input_tokens || 0;
} });
const a = await load({ callModel });

const allPhones = new Set(phonesIn(know.docs.map(sourceText).join('\n') + '\n' + JSON.stringify(know.hotlines) + JSON.stringify(know.help)));
const textOf = o => [o.summary, ...(o.steps || []).map(s => s.text), o.referral && o.referral.text].filter(Boolean).join('\n');

function grade(item, out) {
  const fails = [];
  if (!item.expect.includes(out.status)) fails.push(`状态 ${out.status}，期望 ${item.expect.join('/')}`);
  if (out.status === 'crisis' || out.status === 'error') return fails;
  const text = textOf(out);
  const cited = new Set((out.sources || []).map(s => s.source_id));
  if (item.cite && !item.cite.some(id => cited.has(id))) fails.push('没有引用 ' + item.cite.join(' 或 '));
  if (item.citePlace && !(out.sources || []).some(s => s.type === 'place')) fails.push('没有引用具体地点');
  if (item.referral && !out.referral) fails.push('没有转介');
  for (const m of item.must || []) if (!new RegExp(m, 'i').test(text)) fails.push('缺少：' + m);
  for (const m of item.mustNot || []) if (new RegExp(m, 'im').test(text)) fails.push('出现了禁止的说法：' + m);
  for (const p of phonesIn(text)) if (!allPhones.has(p)) fails.push('电话不在指南里：' + p);
  if ((out.sources || []).some(s => !s.source_id)) fails.push('来源编号缺失');
  return fails;
}

// --regrade <结果文件>：用保存的回答重新评分（改了评分规则时用），不调用 AI
const regradeAt = args.indexOf('--regrade');
if (regradeAt >= 0) {
  const saved = JSON.parse(fs.readFileSync(args[regradeAt + 1], 'utf8'));
  let n = 0;
  for (const r of saved.results) {
    const item = bank.find(q => q.id === r.id);
    const fails = grade(item, r.out);
    if (!fails.length) n++;
    console.log(`${fails.length ? '✗' : '✓'} ${r.id} [${r.type}] ${r.out.status}`);
    for (const f of fails) console.log('    - ' + f);
  }
  console.log(`\n重新评分：通过 ${n} / ${saved.results.length}（不调用 AI；原费用 $${(saved.cost || 0).toFixed(3)}）`);
  process.exit(n === saved.results.length ? 0 : 1);
}

const results = [];
for (const item of pick) {
  const t0 = Date.now();
  let out;
  try { out = await a.ask(item.q, { uiLang: item.lang === 'en' ? 'en' : 'zh' }); } catch (e) { out = { status: 'error', reason: String(e && e.message) }; }
  const fails = grade(item, out);
  results.push({ id: item.id, type: item.type, q: item.q, pass: !fails.length, fails, secs: (Date.now() - t0) / 1000, out });
  console.log(`${fails.length ? '✗' : '✓'} ${item.id} [${item.type}] ${out.status}${out.dropped && (out.dropped.steps || out.dropped.sources) ? ` (程序删掉 ${out.dropped.steps} 步、${out.dropped.sources} 个无效引用)` : ''} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  for (const f of fails) console.log('    - ' + f);
}

const cost = (usage.in * PRICE.in + usage.out * PRICE.out + usage.cacheWrite * PRICE.cacheWrite + usage.cacheRead * PRICE.cacheRead) / 1e6;
const passed = results.filter(r => r.pass).length;
console.log(`\n通过 ${passed} / ${results.length}`);
console.log(`AI 调用 ${usage.calls} 次；输入 ${usage.in}、写缓存 ${usage.cacheWrite}、读缓存 ${usage.cacheRead}、输出 ${usage.out} token；费用约 $${cost.toFixed(3)}`);

const dir = path.join(here, 'results');
fs.mkdirSync(dir, { recursive: true });
const file = path.join(dir, new Date().toISOString().replace(/[:.]/g, '-') + '.json');
fs.writeFileSync(file, JSON.stringify({ model: process.env.MODEL || 'claude-opus-5-5', usage, cost, passed, total: results.length, results }, null, 1));
console.log('结果：' + path.relative(process.cwd(), file));
process.exit(passed === results.length ? 0 : 1);
