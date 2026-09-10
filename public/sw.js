// sw.js — minimal offline shell for Kamloops Life Map (PWA)
//
// Strategy: network-first for navigations and the index HTML so updates
// land promptly (bumping DATA_VERSION invalidates the cached copy on the
// next reload); cache-first for static assets (manifest, icon, Leaflet
// bundles) so repeat visits open instantly. Tiles are NOT cached —
// they're large and OSM tiles already have their own CDN cache layer.
//
// Bumping: bump CACHE below to flush old caches; pair with a DATA_VERSION
// bump in src/engine.html so the network-fetch hits return the new HTML.

// v1.1.0 (2026-09-07): the icon and the manifest both changed. Static assets are
// served cache-first, so without this bump every reader who had already visited
// would have kept the old icon and the old manifest for good — the change would
// have shipped and reached nobody. Bump this line whenever a file in
// STATIC_ASSETS changes, not only when the strategy changes.
// v1.2.0 (2026-09-08): manifest.json's description changed (the newcomer ->
// resident rename had missed this file), and this is also the first release in
// which the page actually registers this worker — nothing ever called
// serviceWorker.register() before, so every version above shipped to nobody.
// STATIC_ASSETS are served cache-first, so this bump is what lets the corrected
// manifest reach readers who already have a cache.
// v1.3.0 (2026-09-10): manifest.json renamed the app (Living Services Map ->
// Life Guide) and icon.svg is a new mark. Both are STATIC_ASSETS, served
// cache-first, so without this bump every existing reader would keep the old
// name on their home screen and the old icon for good.
// v1.4.0 (2026-09-10): icon-180.png / icon-512.png were listed here (and in
// manifest.json) but never copied into public/, so addAll() rejected and no
// version of this worker ever installed. The icons now ship; the pre-cache
// tolerates a missing file; the HTML is stored once under '/' regardless of
// query string (share links and ?src= tags were each caching a 1.3 MB copy);
// the offline fallback finds it from any URL; static assets revalidate in the
// background so a manifest change no longer waits for a manual bump here.
const CACHE = 'kamloops-lifemap-v1.4.0';
const STATIC_ASSETS = [
  '/manifest.json',
  '/icon.svg',
  '/icon-180.png',
  '/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) =>
      Promise.allSettled(STATIC_ASSETS.map((a) => c.add(a)))
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // tiles, fonts: browser handles them

  // Network-first for HTML navigations (always try fresh, fall back to cache)
  const isHTML = req.mode === 'navigate' ||
    (req.headers.get('accept') || '').includes('text/html');
  if (isHTML) {
    event.respondWith(
      fetch(req)
        .then((resp) => {
          // only a response that actually succeeded becomes the offline shell
          if (resp && resp.ok) {
            const clone = resp.clone();
            event.waitUntil(caches.open(CACHE).then((c) => c.put('/', clone)));
          }
          return resp;
        })
        .catch(() => caches.match('/').then((c) => c || caches.match(req, { ignoreSearch: true })))
    );
    return;
  }

  // Stale-while-revalidate for same-origin static assets (manifest, icons)
  event.respondWith(
    caches.match(req).then((cached) => {
      const refresh = fetch(req).then((resp) => {
        if (resp && resp.ok) {
          const clone = resp.clone();
          event.waitUntil(caches.open(CACHE).then((c) => c.put(req, clone)));
        }
        return resp;
      }).catch(() => cached || Response.error());
      return cached || refresh;
    })
  );
});
