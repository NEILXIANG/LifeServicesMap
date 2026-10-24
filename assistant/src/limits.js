// limits.js — 公开后的费用保护（说明 F10；2026-10-24 改为公开）。
//
// 三层，任何一层到了就不调用 AI：
//   1. 短时防刷：同一访客每分钟最多 BURST 次（Cloudflare Rate Limiting 绑定 BURST；没绑定就跳过）；
//   2. 每位访客每天最多 IP_DAILY_LIMIT 次（线上设为 10）；
//   3. 全站每天最多 DAILY_LIMIT 次。
// 访客只用"IP + 当天日期"的散列计数，不保存 IP 本身；计数第二天自动过期。
// 计数存在 KV（USAGE）里；没绑定 KV 时按实例计数（本机开发、测试）。最后一道是 Anthropic Console 的预充值余额。

const mem = new Map();

async function sha(text) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(d)].slice(0, 12).map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function visitorKey(request, day) {
  const ip = request.headers.get('CF-Connecting-IP') || request.headers.get('X-Forwarded-For') || 'local';
  return sha('kia|' + day + '|' + ip);
}

async function get(env, k) { return env.USAGE ? Number(await env.USAGE.get(k) || 0) : (mem.get(k) || 0); }
async function put(env, k, n) {
  if (env.USAGE) await env.USAGE.put(k, String(n), { expirationTtl: 2 * 86400 });
  else mem.set(k, n);
}

// 今天还剩几题（不计数），给界面显示"测试版：今天还可以问 n 题"
export async function peekQuota(request, env, now = new Date()) {
  const day = now.toISOString().slice(0, 10);
  const who = await visitorKey(request, day);
  const limit = Number(env.IP_DAILY_LIMIT || 20);
  const used = await get(env, 'ip:' + day + ':' + who);
  return { left: Math.max(0, limit - used), limit };
}

// 返回 null 表示放行（并已计数）；否则返回拒绝的原因
export async function checkLimits(request, env, now = new Date()) {
  const day = now.toISOString().slice(0, 10);
  const who = await visitorKey(request, day);
  if (env.BURST) {
    const { success } = await env.BURST.limit({ key: who });
    if (!success) return 'too_fast';
  }
  const ipLimit = Number(env.IP_DAILY_LIMIT || 20);
  const allLimit = Number(env.DAILY_LIMIT || 200);
  const kIp = 'ip:' + day + ':' + who, kAll = 'all:' + day;
  const [nIp, nAll] = await Promise.all([get(env, kIp), get(env, kAll)]);
  if (nIp >= ipLimit) return 'visitor_limit';
  if (nAll >= allLimit) return 'daily_limit';
  await Promise.all([put(env, kIp, nIp + 1), put(env, kAll, nAll + 1)]);
  return null;
}

export function _resetForTests() { mem.clear(); }
