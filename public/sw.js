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
const CACHE = 'kamloops-lifemap-v1.1.0';
const STATIC_ASSETS = [
  '/manifest.json',
  '/icon.svg',
  '/icon-180.png',
  '/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  // Network-first for HTML navigations (always try fresh, fall back to cache)
  const isHTML = req.mode === 'navigate' ||
    (req.headers.get('accept') || '').includes('text/html');
  if (isHTML) {
    event.respondWith(
      fetch(req)
        .then((resp) => {
          const clone = resp.clone();
          caches.open(CACHE).then((c) => c.put(req, clone));
          return resp;
        })
        .catch(() => caches.match(req).then((c) => c || caches.match('/')))
    );
    return;
  }

  // Cache-first for everything else (manifest, icon, same-origin static)
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(req).then((cached) => cached || fetch(req).then((resp) => {
        const clone = resp.clone();
        caches.open(CACHE).then((c) => c.put(req, clone));
        return resp;
      }))
    );
  }
});