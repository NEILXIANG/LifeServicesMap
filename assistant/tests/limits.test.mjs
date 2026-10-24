// 公开后的费用保护（src/limits.js）：防刷、每位访客每天、全站每天。用内存计数，不联网。
import test from 'node:test';
import assert from 'node:assert/strict';
import { checkLimits, _resetForTests } from '../src/limits.js';

const req = ip => new Request('https://kamloops-assistant.neilxiang.workers.dev/api/ask', { headers: { 'CF-Connecting-IP': ip } });
const day = new Date('2026-10-24T12:00:00Z');

test('每位访客每天上限：第 21 次被拒，换一个访客照常', async () => {
  _resetForTests();
  const env = { IP_DAILY_LIMIT: '20', DAILY_LIMIT: '200' };
  for (let i = 0; i < 20; i++) assert.equal(await checkLimits(req('1.2.3.4'), env, day), null);
  assert.equal(await checkLimits(req('1.2.3.4'), env, day), 'visitor_limit');
  assert.equal(await checkLimits(req('5.6.7.8'), env, day), null);
});

test('第二天重新计数', async () => {
  _resetForTests();
  const env = { IP_DAILY_LIMIT: '1', DAILY_LIMIT: '200' };
  assert.equal(await checkLimits(req('1.2.3.4'), env, day), null);
  assert.equal(await checkLimits(req('1.2.3.4'), env, day), 'visitor_limit');
  assert.equal(await checkLimits(req('1.2.3.4'), env, new Date('2026-10-25T12:00:00Z')), null);
});

test('全站每天上限：到了以后谁都不能再问', async () => {
  _resetForTests();
  const env = { IP_DAILY_LIMIT: '20', DAILY_LIMIT: '3' };
  for (const ip of ['1.1.1.1', '2.2.2.2', '3.3.3.3']) assert.equal(await checkLimits(req(ip), env, day), null);
  assert.equal(await checkLimits(req('4.4.4.4'), env, day), 'daily_limit');
});

test('短时防刷：绑定说不行就拒绝', async () => {
  _resetForTests();
  const env = { BURST: { limit: async () => ({ success: false }) } };
  assert.equal(await checkLimits(req('1.2.3.4'), env, day), 'too_fast');
});

test('KV 里只存编码，不存 IP 本身', async () => {
  _resetForTests();
  const keys = [];
  const env = { USAGE: { get: async () => null, put: async k => { keys.push(k); } } };
  await checkLimits(req('203.0.113.77'), env, day);
  assert.ok(keys.length === 2);
  assert.ok(keys.every(k => !k.includes('203.0.113.77')));
});
