// 隔离检查（Neil 2026-10-24："不能污染 kamloops-lifemap""只能是 kamloops-assistant"）。
// 助手的一切改动和部署只针对 kamloops-assistant；生活指南的文件、Worker、数据一个都不能动。不联网。

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, '..', '..');
// 只看配置本身，不看注释（注释里会提到指南的 Worker 名字）
const toml = fs.readFileSync(path.join(here, '..', 'wrangler.toml'), 'utf8').split('\n').filter(l => !/^\s*#/.test(l)).join('\n');

test('部署目标只能是 kamloops-assistant', () => {
  assert.match(toml, /^name = "kamloops-assistant"$/m);
  assert.doesNotMatch(toml, /kamloops-lifemap/);
  assert.doesNotMatch(toml, /^\s*(routes?|route)\s*=/m, '不绑定任何路由（只用 workers.dev 地址）');
});

test('不和指南共用任何数据：反馈数据集、KV、限流命名空间都是助手自己的', () => {
  assert.doesNotMatch(toml, /dataset = "kamloops_events"/);
  for (const m of toml.matchAll(/dataset = "([^"]+)"/g)) assert.match(m[1], /assistant/);
});

// 允许改动的路径：助手自己的目录、助手的文档、经验库（记录本轮经验）、.gitignore
const ALLOWED = [/^assistant\//, /^docs\/assistant\//, /^docs\/knowledge\//, /^\.gitignore$/];

test('和 main 比，生活指南的文件一个都没有改', t => {
  let base;
  try { base = execFileSync('git', ['merge-base', 'HEAD', 'main'], { cwd: root, encoding: 'utf8' }).trim(); }
  catch { return t.skip('没有 main 分支可比'); }
  const changed = [
    ...execFileSync('git', ['-c', 'core.quotepath=false', 'diff', '--name-only', base], { cwd: root, encoding: 'utf8' }).split('\n'),
    ...execFileSync('git', ['-c', 'core.quotepath=false', 'ls-files', '--others', '--exclude-standard'], { cwd: root, encoding: 'utf8' }).split('\n'),
  ].filter(Boolean);
  const bad = changed.filter(f => !ALLOWED.some(re => re.test(f)));
  assert.deepEqual(bad, [], '这些指南文件被改了：' + bad.join(', '));
});

test('线上上限：每位用户（IP）每天 10 题，全站每天 200 题（Neil 2026-10-24）', () => {
  assert.match(toml, /^IP_DAILY_LIMIT = "10"/m);
  assert.match(toml, /^DAILY_LIMIT = "200"/m);
});
