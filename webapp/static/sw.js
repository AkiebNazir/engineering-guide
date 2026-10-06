/* ============================================================================
   Service worker for the static site: repeat visits load from the device, not
   the network, and pages already read keep working offline.

   Only the static build registers it (app.js boot, when EG_STATIC). build_static.py
   fills in VERSION and SHELL below; this source copy is never served as is.

   Every file the app asks for carries its content hash in the URL (?v=…, see
   assetUrl in lazy.js and the build's index.html), so a cached response is
   always the right one: those are served from the cache first. The page itself
   (index.html) is fetched from the network first, so a deploy shows up on the
   next visit, and comes from the cache when offline. A new VERSION gets a new
   cache; the old one is deleted when the new worker takes over.
   ========================================================================= */
const VERSION = 'dev';
const SHELL = [];

const CACHE = `eg-${VERSION}`;

self.addEventListener('install', event => {
  // Every file index.html loads, so the next visit and offline use need no network.
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k.startsWith('eg-') && k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

const fromCacheFirst = async req => {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok) cache.put(req, res.clone());
  return res;
};

const fromNetworkFirst = async (req, fallbackUrl) => {
  const cache = await caches.open(CACHE);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (e) {
    return (await cache.match(req, { ignoreSearch: true })) ||
      (fallbackUrl && await cache.match(fallbackUrl)) || Response.error();
  }
};

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // Pyodide's CDN and the Go Playground keep their own caching.
  if (url.origin !== self.location.origin) return;
  if (req.mode === 'navigate') {
    event.respondWith(fromNetworkFirst(req, new URL('./index.html', self.registration.scope).href));
    return;
  }
  // Content-hashed (?v=) and version-pathed (vendor/<lib>/<version>/) files never change.
  if (url.searchParams.has('v') || url.pathname.includes('/vendor/')) {
    event.respondWith(fromCacheFirst(req));
    return;
  }
  event.respondWith(fromNetworkFirst(req));
});
