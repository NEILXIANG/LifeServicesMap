// worker.js — Kamloops Life Map edge worker
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS preflight — sendBeacon never triggers this because Content-Type
    // stays as text/plain (or we use a Blob with no custom header), but if a
    // future tool switches to fetch-with-headers, this keeps the request alive.
    if (request.method === 'OPTIONS' && url.pathname === '/api/event') {
      return new Response(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Max-Age': '86400',
        },
      });
    }

    if (url.pathname === '/api/event' && request.method === 'POST') {
      return handleEvent(request, env);
    }

    // Everything else (the index.html and anything else build.py produces) is
    // served by the static asset binding. If a path is not found in assets,
    // env.ASSETS.fetch falls back to a 404 — no separate SPA rewrite rule
    // needed because the app is a single file.
    return env.ASSETS.fetch(request);
  },
};

async function handleEvent(request, env) {
  // --- 1. Parse + validate payload ----------------------------------------
  // A well-formed event is a few hundred bytes; the client's own props cap is
  // 2 KB. Refusing anything larger before parsing keeps a hostile or broken
  // client from making the Worker do the work of parsing megabytes.
  const declared = Number(request.headers.get('content-length') || 0);
  if (declared > 8192) return badRequest('too large');

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return badRequest('bad json');
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return badRequest('bad shape');
  }

  // The client contract is {sid, t, p, d}; t is the only required field and
  // is constrained to a lowercase snake_case token (with optional digits, so
  // dev/smoke probes like "verify_double2" still pass) so we can index by it
  // in Analytics Engine queries without surprises.
  const t = String(body.t || '').slice(0, 64);
  if (!t || !/^[a-z0-9_]+$/.test(t)) return badRequest('bad type');

  // sid is a client-generated random string (see getSid() in engine.html).
  // We slice to 64 chars defensively; the helper always emits <32.
  const sid = String(body.sid || 'anon').slice(0, 64);

  // Stringify props with a hard cap — Analytics Engine blobs total 4 KB per
  // row, and this 2 KB ceiling leaves room for the other columns. The client
  // already strips PII for search queries, so this is a belt-and-braces limit.
  let propsStr = '{}';
  try {
    propsStr = JSON.stringify(body.p || {});
    if (propsStr.length > 2048) propsStr = propsStr.slice(0, 2048);
  } catch (e) {}

  // d is the client's Date.now() at click time. Trusting it unconditionally was
  // a mistake: a device with a wrong clock — common enough, and near-certain on
  // a cheap phone that has just crossed several time zones, which describes a
  // fair share of this map's audience — writes a timestamp days or years out,
  // and every time-bucketed report is then quietly wrong with nothing to show
  // that it is. Anything outside a day either side of server time is replaced
  // with server time, and the row says it was corrected so the rate of bad
  // clocks is itself measurable rather than hidden.
  const now = Date.now();
  const DAY = 86400000;
  const claimed = Number.isFinite(body.d) ? body.d : now;
  const skewed = Math.abs(claimed - now) > DAY;
  const ts = skewed ? now : claimed;

  // env: maintainer traffic (?debug=1 pages, deploy.sh smoke tests) tags its
  // events with p.env === 'dev'. It has to land in its own numeric column,
  // not just inside the props JSON — Analytics Engine has no JSON functions,
  // so a value buried in blob3 cannot be filtered on. double2 = 1 means dev,
  // 0 means real user. Every analysis query should add `AND double2 = 0`.
  const isDev = body.p && body.p.env === 'dev' ? 1 : 0;

  // doubles[2] carries the clock-skew flag rather than the props JSON, for the
  // same reason isDev does: Analytics Engine has no JSON functions, so anything
  // buried in a blob cannot be filtered or counted.

  // --- 2. Write to Analytics Engine ---------------------------------------
  try {
    env.ANALYTICS.writeDataPoint({
      // blobs[0..2] are string columns we can SELECT: session id, event type,
      // and the JSON-stringified props payload.
      blobs: [sid, t, propsStr],
      // doubles[0] is the event timestamp in ms (server-corrected when the
      //           client's clock was more than a day out).
      // doubles[1] is the dev-traffic flag (1 = maintainer, 0 = real user).
      // doubles[2] is 1 when doubles[0] had to be corrected.
      doubles: [ts, isDev, skewed ? 1 : 0],
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
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-store',
    },
  });
}

function badRequest(reason) {
  return new Response(reason, {
    status: 400,
    headers: { 'Access-Control-Allow-Origin': '*' },
  });
}