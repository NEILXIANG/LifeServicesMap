// 登录校验（说明 F1）：没配 Access 时线上一律拒绝；配了 Access 只认 Cloudflare 签名的令牌。不联网。
import test from 'node:test';
import assert from 'node:assert/strict';
import { verifyAccess } from '../src/access.js';

const req = (url, headers = {}) => new Request(url, { headers });

test('没配 Access：本机放行', async () => {
  assert.equal((await verifyAccess(req('http://localhost:8787/'), {})).ok, true);
  assert.equal((await verifyAccess(req('http://127.0.0.1:8787/api/ask'), {})).ok, true);
});

test('没配 Access：线上地址一律拒绝', async () => {
  const r = await verifyAccess(req('https://kamloops-assistant.neilxiang.workers.dev/'), {});
  assert.equal(r.ok, false);
  assert.equal(r.why, 'access_not_configured');
});

test('配了 Access：没有令牌、令牌格式不对都拒绝', async () => {
  const env = { ACCESS_TEAM: 'example', ACCESS_AUD: 'aud123' };
  assert.equal((await verifyAccess(req('https://kamloops-assistant.neilxiang.workers.dev/'), env)).why, 'no_token');
  assert.equal((await verifyAccess(req('https://kamloops-assistant.neilxiang.workers.dev/', { 'Cf-Access-Jwt-Assertion': 'abc' }), env)).why, 'bad_token');
});

test('配了 Access：伪造的令牌（自己签名）拒绝', async () => {
  const { privateKey, publicKey } = await crypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
  const b64 = o => Buffer.from(JSON.stringify(o)).toString('base64url');
  const h = b64({ alg: 'RS256', kid: 'k1' }), p = b64({ aud: ['aud123'], exp: Date.now() / 1000 + 600 });
  const sig = Buffer.from(await crypto.subtle.sign('RSASSA-PKCS1-v1_5', privateKey, new TextEncoder().encode(h + '.' + p))).toString('base64url');
  // Cloudflare 的公钥里没有攻击者的 k1：用假的 fetch 返回另一把公钥
  const other = await crypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
  const jwk = { ...(await crypto.subtle.exportKey('jwk', other.publicKey)), kid: 'k1' };
  const realFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ keys: [jwk] }));
  try {
    const r = await verifyAccess(req('https://kamloops-assistant.neilxiang.workers.dev/', { 'Cf-Access-Jwt-Assertion': [h, p, sig].join('.') }), { ACCESS_TEAM: 'forgetest', ACCESS_AUD: 'aud123' });
    assert.equal(r.ok, false);
    assert.equal(r.why, 'bad_signature');
    // 同一把钥匙签的、受众对的令牌：通过（证明校验本身是对的）
    const good = { ...(await crypto.subtle.exportKey('jwk', publicKey)), kid: 'k2' };
    globalThis.fetch = async () => new Response(JSON.stringify({ keys: [good] }));
    const h2 = b64({ alg: 'RS256', kid: 'k2' });
    const sig2 = Buffer.from(await crypto.subtle.sign('RSASSA-PKCS1-v1_5', privateKey, new TextEncoder().encode(h2 + '.' + p))).toString('base64url');
    const ok = await verifyAccess(req('https://x.workers.dev/', { 'Cf-Access-Jwt-Assertion': [h2, p, sig2].join('.') }), { ACCESS_TEAM: 'goodtest', ACCESS_AUD: 'aud123' });
    assert.equal(ok.ok, true);
    const wrongAud = await verifyAccess(req('https://x.workers.dev/', { 'Cf-Access-Jwt-Assertion': [h2, p, sig2].join('.') }), { ACCESS_TEAM: 'goodtest', ACCESS_AUD: 'other' });
    assert.equal(wrongAud.why, 'wrong_audience');
  } finally {
    globalThis.fetch = realFetch;
  }
});

test('ctx.access 有已登录的身份：放行；没有身份或取身份出错：不放行', async () => {
  const url = 'https://kamloops-assistant.neilxiang.workers.dev/';
  assert.equal((await verifyAccess(req(url), {}, { access: { getIdentity: async () => ({ email: 'staff@example.org' }) } })).ok, true);
  assert.equal((await verifyAccess(req(url), {}, { access: { getIdentity: async () => null } })).ok, false);
  assert.equal((await verifyAccess(req(url), {}, { access: { getIdentity: async () => { throw new Error('x'); } } })).ok, false);
  assert.equal((await verifyAccess(req(url), {}, {})).ok, false);
});
