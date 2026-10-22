// worker.js — Life Guide edge worker (one per city, same code; the city is in each event's blob5)
//
// Two responsibilities:
//   1. POST /api/event   →  validate payload, write a row to Analytics Engine
//   2. anything else     →  fall through to the bundled static asset (index.html)
//
// The static index.html contains the same trackEvent() helper it always has; the
// only thing that changed between Phase B and Phase A is that the helper's
// internals now hit this /api/event endpoint via navigator.sendBeacon. We never
// persist anything except the event payload itself — no IP, no User-Agent, no
// cookies, no fingerprinting. A session ID is generated client-side and reused
// across reloads in the same browser, which is the only way to link events that
// belong to one user without ever knowing who they are.
//
// Free tier: Workers 100K req/day, Analytics Engine 100K writes/day — this
// project's expected usage (~5K events/day at 100 DAU) is 20× under both caps.

// 2026-09-11: the event endpoint used to answer any origin (CORS *) with no
// rate limit — anyone could pour rows into the analytics or burn the daily
// quota from a script. It now accepts browser posts from this site only
// (Origin / Sec-Fetch-Site / Referer must match the request host) and caps
// each client IP at RATE_LIMIT events per minute via the edge cache — a soft,
// per-datacentre limit that needs no extra binding and fails open.
// Every asset response also carries a baseline of security headers. The CSP
// keeps 'unsafe-inline' for script/style because the app is one file with
// inline handlers; what it does lock down is where the page may load from and
// talk to, that it cannot be framed, and that plugins/base tags are refused.
const RATE_LIMIT = 300;            // events per IP per minute (a library's NAT is one IP)
// 瓦片服务商。这份名单必须同时出现在 img-src 和 connect-src 里：
// 瓦片本身是 <img>（img-src），但 引擎（app/engine/）的 probeTiles() 还会对主底图和每个备用底图用
// fetch() 真正取一张瓦片、读它的 HTTP 状态码——因为"key 失效 / 配额用尽"这类
// 响应会正常返回一张写着错误的图片，tileerror 永远不触发，只能看状态码。
// 少了 connect-src，那次 fetch 被 CSP 挡下、被 .catch(()=>{}) 吞掉，
// **Esri 自动降级就静默失效了**：地图今天照常显示，但 MapTiler 的 key 一旦过期，
// 页面会一直显示"invalid key"的瓦片而不会切到备用源。
// 2026-09-16 首次真正启用 CSP 时就是这么发现的。
const TILE_HOSTS =
  'https://server.arcgisonline.com https://*.arcgisonline.com https://api.maptiler.com ' +
  'https://tiles.stadiamaps.com https://*.basemaps.cartocdn.com https://*.tile.openstreetmap.org';
const SECURITY_HEADERS = {
  'Content-Security-Policy':
    "default-src 'self'; script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com; " +
    "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: " + TILE_HOSTS + "; " +
    "font-src 'self' data:; connect-src 'self' https://cloudflareinsights.com https://static.cloudflareinsights.com " + TILE_HOSTS + "; " +
    "worker-src 'self'; manifest-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self' mailto:",
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'X-Frame-Options': 'DENY',
  'Permissions-Policy': 'geolocation=(self), camera=(), microphone=(), payment=()',
  'Cross-Origin-Opener-Policy': 'same-origin',
};

function sameSite(request, url) {
  const origin = request.headers.get('Origin');
  if (origin) {
    try { return new URL(origin).host === url.host; } catch (e) { return false; }
  }
  const sfs = request.headers.get('Sec-Fetch-Site');
  if (sfs) return sfs === 'same-origin';
  const ref = request.headers.get('Referer');
  if (ref) {
    try { return new URL(ref).host === url.host; } catch (e) { return false; }
  }
  return false;   // a bare POST with none of the three is not a browser on this site
}

async function overLimit(request) {
  try {
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    const minute = Math.floor(Date.now() / 60000);
    const key = new Request('https://ratelimit.internal/' + encodeURIComponent(ip) + '/' + minute);
    const cache = caches.default;
    const hit = await cache.match(key);
    const n = hit ? parseInt(await hit.text(), 10) || 0 : 0;
    if (n >= RATE_LIMIT) return true;
    await cache.put(key, new Response(String(n + 1), { headers: { 'Cache-Control': 'max-age=120' } }));
    return false;
  } catch (e) {
    return false;   // the cache is a convenience; never block real traffic on its failure
  }
}

function withSecurityHeaders(resp) {
  const h = new Headers(resp.headers);
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) h.set(k, v);
  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: h });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS preflight — same-site only; there is no legitimate cross-site caller.
    if (request.method === 'OPTIONS' && url.pathname === '/api/event') {
      if (!sameSite(request, url)) return new Response(null, { status: 403 });
      return new Response(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': url.origin,
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Max-Age': '86400',
          'Vary': 'Origin',
        },
      });
    }

    if (url.pathname === '/api/event' && request.method === 'POST') {
      if (!sameSite(request, url)) return new Response('forbidden', { status: 403 });
      if (await overLimit(request)) return new Response('too many events', { status: 429, headers: { 'Retry-After': '60' } });
      return handleEvent(request, env, url);
    }

    // Everything else (the index.html and anything else build.py produces) is
    // served by the static asset binding. If a path is not found in assets,
    // env.ASSETS.fetch falls back to a 404 — no separate SPA rewrite rule
    // needed because the app is a single file.
    return withSecurityHeaders(await env.ASSETS.fetch(request));
  },
};

async function handleEvent(request, env, url) {
  // --- 1. Parse + validate payload ----------------------------------------
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return badRequest('bad json');
  }

  // The client contract is {sid, t, p, d}; t is the only required field and
  // is constrained to a lowercase snake_case token (with optional digits, so
  // dev/smoke probes like "verify_double2" still pass) so we can index by it
  // in Analytics Engine queries without surprises.
  const t = String(body.t || '').slice(0, 64);
  if (!t || !/^[a-z0-9_]+$/.test(t)) return badRequest('bad type');

  // sid is a client-generated random string (see getSid() in the engine (app/engine/)), which
  // emits and re-validates /^[a-z0-9]{12,32}$/ — plus the literal 'anon' when
  // storage is unavailable. 2026-09-08 audit: this used to accept any string up
  // to 64 chars, so a junk or hand-crafted POST landed in the same session
  // column as real traffic and could not be told apart afterwards. Anything that
  // does not look like one of our own ids is bucketed rather than trusted.
  const rawSid = String(body.sid || 'anon');
  const sid = /^[a-z0-9]{12,32}$/.test(rawSid) || rawSid === 'anon' ? rawSid : 'invalid';

  // Stringify props with a hard cap — Analytics Engine blobs total 4 KB per
  // row, and this 2 KB ceiling leaves room for the other columns. The client
  // already strips PII for search queries, so this is a belt-and-braces limit.
  let propsStr = '{}';
  try {
    propsStr = JSON.stringify(body.p || {});
    if (propsStr.length > 2048) propsStr = propsStr.slice(0, 2048);
  } catch (e) {}

  // d is the client's Date.now() at click time; we trust it (no clock skew
  // adjustment) because the report card we read from Analytics Engine is already
  // good enough at day-resolution and we don't want to introduce server-side
  // latency just to canonicalise timestamps.
  const ts = Number.isFinite(body.d) ? body.d : Date.now();

  // env: maintainer traffic (?debug=1 pages, deploy.sh smoke tests) tags its
  // events with p.env === 'dev'. It has to land in its own numeric column,
  // not just inside the props JSON — Analytics Engine has no JSON functions,
  // so a value buried in blob3 cannot be filtered on. double2 = 1 means dev,
  // 0 means real user. Every analysis query should add `AND double2 = 0`.
  const isDev = body.p && body.p.env === 'dev' ? 1 : 0;

  // --- 2. Write to Analytics Engine ---------------------------------------
  // 2026-09-11: the questions a maintainer actually asks — which language,
  // which flyer, which card, which category, which deployment — used to be
  // buried inside the props JSON, and Analytics Engine cannot GROUP BY into
  // JSON. They now get their own blob columns. Column map:
  //   blob1 sid · blob2 type · blob3 props JSON · blob4 lang · blob5 city
  //   blob6 host · blob7 src · blob8 id (or task) · blob9 cat · blob10 kind/target/to
  //   blob11 client version
  const p = (body.p && typeof body.p === 'object') ? body.p : {};
  const col = (v) => (v === undefined || v === null) ? '' : String(v).slice(0, 64);
  const lang = /^[a-z]{2}$/.test(String(body.l || '')) ? body.l : '';
  const city = col(body.c).replace(/[^a-z0-9_-]/gi, '');
  const ver = col(body.v);
  const host = url ? url.host : '';
  try {
    env.ANALYTICS.writeDataPoint({
      // blobs[0..2] are string columns we can SELECT: session id, event type,
      // and the JSON-stringified props payload.
      blobs: [sid, t, propsStr, lang, city, host, col(p.src), col(p.id || p.task), col(p.cat), col(p.kind || p.target || p.to || p.mode), ver],
      // doubles[0] is the event timestamp in ms.
      // doubles[1] is the dev-traffic flag (1 = maintainer, 0 = real user).
      doubles: [ts, isDev],
      // indexes[0] is the column we filter on most often. Analytics Engine
      // indexes one blob per row by default; indexing t means event-type
      // queries scan a tight range instead of the whole dataset.
      indexes: [t],
    });
  } catch (e) {
    // If writeDataPoint fails for any reason (quota, transient backend issue),
    // log server-side but still return 200 to the client. The client keeps a
    // local copy in ?debug=1 mode, and a 500 here would just cause noisy
    // console errors without giving the user any benefit.
    console.error('ANALYTICS.writeDataPoint failed', e);
  }

  return new Response('ok', {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': url ? url.origin : 'null',
      'Cache-Control': 'no-store',
      'Vary': 'Origin',
    },
  });
}

function badRequest(reason) {
  return new Response(reason, { status: 400, headers: { 'Cache-Control': 'no-store' } });
}