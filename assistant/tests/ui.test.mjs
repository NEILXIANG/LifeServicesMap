// 界面文字：六种语言（zh/en/fr/es/ko/ja）要么全译、要么不译（与指南的规则一致）。不联网。
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const pub = f => fs.readFileSync(path.join(here, '..', 'public', f), 'utf8');
const T = new Function(pub('app.js').match(/const T = (\{[\s\S]*?\n\});\n/)[0] + 'return T;')();
const SIX = ['zh', 'en', 'fr', 'es', 'ko', 'ja'];

test('六种语言都有，而且每种语言的文字条目完全一样', () => {
  assert.deepEqual(Object.keys(T).sort(), [...SIX].sort());
  const keys = o => Object.keys(o).sort().join(',');
  for (const l of SIX) {
    assert.equal(keys(T[l]), keys(T.zh), l + ' 的条目和中文不一致');
    assert.equal(keys(T[l].reasons), keys(T.zh.reasons), l + ' 的出错原因条目不一致');
    for (const [k, v] of Object.entries(T[l])) if (typeof v === 'string') assert.ok(v.trim(), `${l}.${k} 是空的`);
  }
});

test('界面上每种语言都有切换按钮，隐私说明每种语言都有一节', () => {
  const html = pub('index.html'), privacy = pub('privacy.html');
  for (const l of SIX) {
    assert.ok(html.includes(`data-lang="${l}"`), l + ' 没有切换按钮');
    assert.ok(privacy.includes(`id="${l}"`), l + ' 没有隐私说明');
  }
});

test('界面里的 data-t 都有对应的文字', () => {
  for (const k of pub('index.html').matchAll(/data-(?:t|ph)="(\w+)"/g)) assert.ok(T.zh[k[1]], '缺少 ' + k[1]);
});

test('不再显示"KIS 内部"标签（Neil 2026-10-24）', () => {
  assert.ok(!/KIS 内部|KIS internal|class="badge"/.test(pub('index.html') + pub('app.js')));
});

test('语言顺序：英、法、西、中、韩、日（Neil 2026-10-24）', () => {
  const order = ['en', 'fr', 'es', 'zh', 'ko', 'ja'];
  assert.deepEqual([...pub('index.html').matchAll(/data-lang="(\w+)"/g)].map(m => m[1]), order);
  assert.deepEqual([...pub('privacy.html').matchAll(/<article class="card" id="(\w+)"/g)].map(m => m[1]), order);
  assert.deepEqual([...pub('privacy.html').matchAll(/<a href="#(\w+)"/g)].map(m => m[1]), order);
});

test('默认英文：页面初始文字、按钮状态、脚本默认值都是英文（Neil 2026-10-24）', () => {
  const html = pub('index.html');
  assert.match(html, /<html lang="en">/);
  assert.match(html, /data-lang="en" aria-pressed="true"/);
  assert.match(pub('app.js'), /let L = 'en';/);
  for (const m of html.matchAll(/data-t="(\w+)">([^<]*)</g)) assert.equal(m[2], T.en[m[1]], m[1] + ' 初始文字不是英文');
});

test('超过每日次数：六种语言都说明"测试版、控制预算、每人每天 10 题"（Neil 2026-10-24）', () => {
  for (const l of Object.keys(T)) {
    const m = T[l].reasons.visitor_limit;
    assert.match(m, /10/, l);
    assert.match(m, /测试版|test version|version d’essai|versión de prueba|시험 버전|テスト版/, l);
    assert.match(m, /2-1-1/, l);
    assert.match(T[l].reasons.daily_limit, /测试版|test version|version d’essai|versión de prueba|시험 버전|テスト版/, l);
  }
});

// 2026-10-24 界面与交互优化（17 项）的不变量
const app = pub('app.js');
const PII_RE = new Function(app.match(/const PII_RE = (\[[\s\S]*?\n\]);/)[0] + 'return PII_RE;')();
const looksPersonal = q => PII_RE.some(re => re.test(q));

test('发送前的个人信息检查：电话、邮箱、SIN、证件号要提醒', () => {
  for (const q of ['My phone is 250-555-1234', 'email me at li@example.com', 'SIN 123 456 789', 'passport E12345678', 'PHN 9876543210'])
    assert.ok(looksPersonal(q), q);
});

test('普通问题不误报个人信息', () => {
  for (const q of ['How do I get a SIN?', '孩子 9 岁怎么上学', 'Is 811 free?', 'Where is the food bank on 171 Wilson St?', 'What does 9-8-8 do?', '2026 年的税怎么报'])
    assert.ok(!looksPersonal(q), q);
});

test('每种语言都有新增的文字，次数说明里有 {n} 和 {m}，示例有 3 个', () => {
  const keys = ['loading', 'loading2', 'loading3', 'quotaLeft', 'limitTitle', 'youAsked', 'piiTitle', 'piiLead', 'piiEdit', 'piiSend',
    'share', 'mapLink', 'askAnother', 'call911', 'backToAsk', 'offtopic', 'fbPhOff', 'offline', 'earlier'];
  for (const l of Object.keys(T)) {
    for (const k of keys) assert.ok(T[l][k] && T[l][k].trim(), `${l}.${k}`);
    assert.match(T[l].quotaLeft, /\{n\}/); assert.match(T[l].quotaLeft, /\{m\}/);
    assert.equal(T[l].examples.length, 3, l);
    assert.equal(T[l].placeholder, T[l].examples[0], l + ' 初始示例和第一个示例一致');
  }
});

test('el() 彻底展开嵌套数组；回答卡片不用会把 null 显示成文字的原生 append', () => {
  assert.match(app, /kids\.flat\(Infinity\)/);
  assert.equal((app.match(/\.append\(/g) || []).length, 1, '只有 el() 里那一处 append');
});

test('回答里的网址可以点，句末标点不算进网址', () => {
  const re = new Function(app.match(/const URL_IN_TEXT = (\/.*\/g);/)[0] + 'return URL_IN_TEXT;')();
  const split = s => s.split(re).filter((_, i) => i % 2);
  assert.deepEqual(split('Website https://kamloopsfoodbank.org/clients/. Call first.'), ['https://kamloopsfoodbank.org/clients/']);
  assert.deepEqual(split('详见 https://www.canada.ca/sin。'), ['https://www.canada.ca/sin']);
  assert.deepEqual(split('(see https://a.ca/x)'), ['https://a.ca/x']);
  assert.deepEqual(split('no link here'), []);
});
