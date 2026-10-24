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
