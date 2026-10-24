// access.js — 只让登记过的工作人员使用（说明 F1）。
//
// 线上靠 Cloudflare Access：它在请求到达 Worker 之前要求邮箱验证码登录，
// 并在请求头 Cf-Access-Jwt-Assertion 里带一个签名令牌。这里再验证一次签名，
// 防止有人绕过 Access 直接打到 Worker。
//
// 两种方式：ctx.access（首选，不用配置），或自己验证令牌签名（需配置 ACCESS_TEAM 和 ACCESS_AUD）。
// 都不成立时：本机（localhost）放行，线上一律拒绝（宁可用不了，也不能开着）。

const keyCache = new Map();

function b64url(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  return Uint8Array.from(atob(s), c => c.charCodeAt(0));
}

async function teamKeys(team) {
  const hit = keyCache.get(team);
  if (hit && hit.until > Date.now()) return hit.keys;
  const r = await fetch(`https://${team}.cloudflareaccess.com/cdn-cgi/access/certs`);
  if (!r.ok) throw new Error('certs ' + r.status);
  const { keys } = await r.json();
  keyCache.set(team, { keys, until: Date.now() + 3600_000 });
  return keys;
}

export async function verifyAccess(request, env, ctx) {
  const host = new URL(request.url).hostname;
  // 首选：Worker 的 Access 标签页里开启"Protect this Worker behind Access"后，
  // 通过认证的请求带 ctx.access（Cloudflare 已验证过令牌）；没通过认证时它是 undefined。
  if (ctx && ctx.access) {
    try {
      const who = await ctx.access.getIdentity();
      if (who && who.email) return { ok: true, via: 'ctx.access' };
    } catch (e) { /* 落到下面的令牌校验 */ }
  }
  if (!env.ACCESS_TEAM || !env.ACCESS_AUD) {
    return /^(localhost|127\.0\.0\.1|\[::1\])$/.test(host) ? { ok: true, local: true } : { ok: false, why: 'access_not_configured' };
  }
  const jwt = request.headers.get('Cf-Access-Jwt-Assertion');
  if (!jwt) return { ok: false, why: 'no_token' };
  const [h, p, s] = jwt.split('.');
  if (!h || !p || !s) return { ok: false, why: 'bad_token' };
  try {
    const header = JSON.parse(new TextDecoder().decode(b64url(h)));
    const payload = JSON.parse(new TextDecoder().decode(b64url(p)));
    const jwk = (await teamKeys(env.ACCESS_TEAM)).find(k => k.kid === header.kid);
    if (!jwk || header.alg !== 'RS256') return { ok: false, why: 'unknown_key' };
    const key = await crypto.subtle.importKey('jwk', jwk, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
    const good = await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, b64url(s), new TextEncoder().encode(h + '.' + p));
    const aud = [].concat(payload.aud || []);
    const now = Date.now() / 1000;
    if (!good) return { ok: false, why: 'bad_signature' };
    if (!aud.includes(env.ACCESS_AUD)) return { ok: false, why: 'wrong_audience' };
    if (payload.exp && payload.exp < now) return { ok: false, why: 'expired' };
    if (payload.iss && payload.iss !== `https://${env.ACCESS_TEAM}.cloudflareaccess.com`) return { ok: false, why: 'wrong_issuer' };
    return { ok: true };
  } catch (e) {
    return { ok: false, why: 'verify_failed' };
  }
}
